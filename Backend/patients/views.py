from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts.models import Role, UserRole
from accounts.permissions import IsAdminUser, HasRole
from patients.models import ChildProfile, TherapistChildAssignment
from patients.serializers import (
    ChildProfileSerializer,
    ChildCreateSerializer,
    ChildUpdateSerializer,
    AssignTherapistSerializer,
)
from patients.permissions import IsAdminOrTherapist, CanAccessChild, user_has_role

User = get_user_model()


class ChildListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrTherapist]

    def get(self, request):
        if user_has_role(request.user, "admin"):
            qs = ChildProfile.objects.select_related("user").prefetch_related("guardians").order_by("-created_at")
        else:
            # therapist: only assigned children
            child_ids = TherapistChildAssignment.objects.filter(
                therapist=request.user
            ).values_list("child_user_id", flat=True)
            qs = ChildProfile.objects.select_related("user").prefetch_related("guardians").filter(
                user_id__in=child_ids
            ).order_by("-created_at")

        return Response(ChildProfileSerializer(qs, many=True).data)

    def post(self, request):
        ser = ChildCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        profile = ser.save()

        # If creator is therapist, auto-assign to them
        if user_has_role(request.user, "therapist"):
            TherapistChildAssignment.objects.get_or_create(
                therapist=request.user,
                child_user=profile.user,
                defaults={"is_primary": True},
            )

        return Response(ChildProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class ChildDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrTherapist, CanAccessChild]

    def get_object(self, child_id: int) -> ChildProfile:
        return ChildProfile.objects.select_related("user").prefetch_related("guardians").get(id=child_id)

    def get(self, request, child_id: int):
        profile = self.get_object(child_id)
        self.check_object_permissions(request, profile)
        return Response(ChildProfileSerializer(profile).data)

    def patch(self, request, child_id: int):
        profile = self.get_object(child_id)
        self.check_object_permissions(request, profile)

        ser = ChildUpdateSerializer(profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        profile = ser.save()

        return Response(ChildProfileSerializer(profile).data)


class AdminAssignTherapistView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, child_id: int):
        ser = AssignTherapistSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        therapist_id = ser.validated_data["therapist_user_id"]
        is_primary = ser.validated_data["is_primary"]

        try:
            therapist = User.objects.get(id=therapist_id)
        except User.DoesNotExist:
            return Response({"detail": "Therapist not found"}, status=status.HTTP_404_NOT_FOUND)

        # Ensure therapist role exists on user
        if not UserRole.objects.filter(user=therapist, role__slug="therapist").exists() and not therapist.is_staff:
            return Response({"detail": "Target user is not a therapist"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = ChildProfile.objects.select_related("user").get(id=child_id)
        except ChildProfile.DoesNotExist:
            return Response({"detail": "Child not found"}, status=status.HTTP_404_NOT_FOUND)

        TherapistChildAssignment.objects.update_or_create(
            therapist=therapist,
            child_user=profile.user,
            defaults={"is_primary": is_primary},
        )

        return Response({"status": "ok", "child_id": profile.id, "therapist_id": therapist.id})
