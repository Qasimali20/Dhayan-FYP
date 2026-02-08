from __future__ import annotations

from rest_framework.permissions import BasePermission
from accounts.models import UserRole
from patients.models import TherapistChildAssignment


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


def therapist_has_child(user, child_user_id: int) -> bool:
    return TherapistChildAssignment.objects.filter(therapist=user, child_user_id=child_user_id).exists()


class CanAccessSpeechTrial(BasePermission):
    """
    Therapist can access only assigned child's trials.
    Admin can access all.
    """
    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        if not is_therapist(request.user):
            return False

        # obj is SessionTrial
        child_user_id = obj.session.child.user_id
        return therapist_has_child(request.user, child_user_id)
