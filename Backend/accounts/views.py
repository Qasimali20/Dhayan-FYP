from __future__ import annotations

import random
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes as perm_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from accounts.models import Role, UserRole, PasswordResetToken
from accounts.serializers import (
    MeSerializer,
    AdminCreateUserSerializer,
    ReplaceRolesSerializer,
    RoleSerializer,
    SignupSerializer,
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
)
from accounts.permissions import IsAdminUser

User = get_user_model()
logger = logging.getLogger(__name__)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        user = request.user
        full_name = request.data.get("full_name")
        phone = request.data.get("phone")
        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        user.save()
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Client-side token removal is the primary mechanism
        # This endpoint exists for API completeness
        return Response({"message": "Logged out successfully."})


class AdminListUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        role_filter = request.query_params.get("role")
        qs = User.objects.prefetch_related("user_roles__role").order_by("-created_at")
        if role_filter:
            qs = qs.filter(user_roles__role__slug=role_filter)
        users = []
        for u in qs:
            users.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "roles": list(u.user_roles.values_list("role__slug", flat=True)),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            })
        return Response(users)


class AdminCreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        ser = AdminCreateUserSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(
            {"id": user.id, "email": user.email, "roles": list(user.user_roles.values_list("role__slug", flat=True))},
            status=status.HTTP_201_CREATED
        )


class AdminReplaceUserRolesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id: int):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        ser = ReplaceRolesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        roles = ser.validated_data["roles"]

        UserRole.objects.filter(user=user).delete()
        for slug in roles:
            role = Role.objects.get(slug=slug)
            UserRole.objects.create(user=user, role=role)

        return Response({"status": "ok", "user_id": user.id, "roles": roles})


class AdminListRolesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        roles = Role.objects.order_by("slug")
        return Response(RoleSerializer(roles, many=True).data)


# ─────────────────────────────────────────────────────────────────────────────
# Signup
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@perm_classes([AllowAny])
def signup(request):
    ser = SignupSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()
    return Response(
        {
            "message": "Account created successfully.",
            "user": MeSerializer(user).data,
        },
        status=status.HTTP_201_CREATED,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Forgot Password – request OTP
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@perm_classes([AllowAny])
def forgot_password(request):
    ser = ForgotPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    email = ser.validated_data["email"]
    user = User.objects.get(email=email)

    # Invalidate previous tokens
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    PasswordResetToken.objects.create(
        user=user,
        token=otp,
        expires_at=timezone.now() + timedelta(minutes=15),
    )

    # Try email; falls back to console in development
    try:
        send_mail(
            subject="DHYAN - Password Reset OTP",
            message=f"Your password reset OTP is: {otp}\n\nThis code expires in 15 minutes.",
            from_email=getattr(django_settings, "DEFAULT_FROM_EMAIL", "noreply@dhyan.com"),
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        logger.warning("Email send failed: %s", e)
        print(f"\n{'='*50}")
        print(f"  OTP for {email}: {otp}")
        print(f"{'='*50}\n")

    return Response({"message": "If an account with that email exists, an OTP has been sent."})


# ─────────────────────────────────────────────────────────────────────────────
# Verify OTP
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@perm_classes([AllowAny])
def verify_otp(request):
    ser = VerifyOTPSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    email = ser.validated_data["email"].lower()
    otp = ser.validated_data["otp"]

    try:
        user = User.objects.get(email=email)
        token = PasswordResetToken.objects.filter(
            user=user, token=otp, used=False
        ).latest("created_at")
    except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    if not token.is_valid():
        return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "OTP verified. You may now reset your password."})


# ─────────────────────────────────────────────────────────────────────────────
# Reset Password
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@perm_classes([AllowAny])
def reset_password(request):
    ser = ResetPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    email = ser.validated_data["email"].lower()
    otp = ser.validated_data["otp"]

    try:
        user = User.objects.get(email=email)
        token = PasswordResetToken.objects.filter(
            user=user, token=otp, used=False
        ).latest("created_at")
    except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    if not token.is_valid():
        return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(ser.validated_data["new_password"])
    user.save()

    token.used = True
    token.save()

    return Response({"message": "Password reset successfully. You may now log in."})
