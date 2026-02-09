from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import Role, UserRole

User = get_user_model()


class MeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "is_staff", "is_active", "roles")

    def get_roles(self, obj):
        return list(obj.user_roles.select_related("role").values_list("role__slug", flat=True))


class AdminCreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(min_length=10, write_only=True)
    is_active = serializers.BooleanField(default=True)
    roles = serializers.ListField(child=serializers.SlugField(), required=False, default=list)

    def validate_roles(self, roles):
        missing = [r for r in roles if not Role.objects.filter(slug=r).exists()]
        if missing:
            raise serializers.ValidationError(f"Unknown roles: {', '.join(missing)}")
        return roles

    def create(self, validated_data):
        roles = validated_data.pop("roles", [])
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        for slug in roles:
            role = Role.objects.get(slug=slug)
            UserRole.objects.get_or_create(user=user, role=role)
        return user


class ReplaceRolesSerializer(serializers.Serializer):
    roles = serializers.ListField(child=serializers.SlugField(), min_length=0)

    def validate_roles(self, roles):
        missing = [r for r in roles if not Role.objects.filter(slug=r).exists()]
        if missing:
            raise serializers.ValidationError(f"Unknown roles: {', '.join(missing)}")
        return roles


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "slug", "name")


# ── Signup ──

class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    password = serializers.CharField(min_length=8, write_only=True)
    password2 = serializers.CharField(write_only=True, label="Confirm password")
    role = serializers.SlugField(
        required=False,
        default="parent",
        help_text="Role slug: e.g. 'therapist' or 'parent'",
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_role(self, value):
        if not Role.objects.filter(slug=value).exists():
            raise serializers.ValidationError(f"Unknown role: {value}")
        return value

    def create(self, validated_data):
        role_slug = validated_data.pop("role")
        validated_data.pop("password2")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        role = Role.objects.get(slug=role_slug)
        UserRole.objects.create(user=user, role=role)

        return user


# ── Forgot / Reset Password ──

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8)
    new_password2 = serializers.CharField(label="Confirm new password")

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        return attrs
