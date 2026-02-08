from __future__ import annotations

from rest_framework.permissions import BasePermission
from accounts.models import UserRole
from patients.models import TherapistChildAssignment
from therapy.models import TherapySession


def is_admin(user) -> bool:
    if not (user and user.is_authenticated):
        return False
    if getattr(user, "is_staff", False):
        return True
    return UserRole.objects.filter(user=user, role__slug="admin").exists()


def is_therapist(user) -> bool:
    if not (user and user.is_authenticated):
        return False
    return UserRole.objects.filter(user=user, role__slug="therapist").exists()


class IsAdminOrTherapist(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user) or is_therapist(request.user)


class CanAccessSession(BasePermission):
    """
    Object-level: admin can access all;
    therapist can access sessions only if child is assigned to therapist.
    """
    def has_object_permission(self, request, view, obj: TherapySession):
        if is_admin(request.user):
            return True
        if is_therapist(request.user):
            return TherapistChildAssignment.objects.filter(
                therapist=request.user,
                child_user=obj.child.user
            ).exists()
        return False
