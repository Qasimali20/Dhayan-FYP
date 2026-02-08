from __future__ import annotations

from rest_framework.permissions import BasePermission
from accounts.models import UserRole
from patients.models import TherapistChildAssignment


def user_has_role(user, role_slug: str) -> bool:
    if not (user and user.is_authenticated):
        return False
    if getattr(user, "is_staff", False) and role_slug == "admin":
        return True
    return UserRole.objects.filter(user=user, role__slug=role_slug).exists()


class IsAdminOrTherapist(BasePermission):
    def has_permission(self, request, view):
        return user_has_role(request.user, "admin") or user_has_role(request.user, "therapist")


class CanAccessChild(BasePermission):
    """
    Object-level: admin can access all;
    therapist can only access assigned children.
    """
    def has_object_permission(self, request, view, obj):
        if user_has_role(request.user, "admin"):
            return True
        if user_has_role(request.user, "therapist"):
            return TherapistChildAssignment.objects.filter(therapist=request.user, child_user=obj.user).exists()
        return False
