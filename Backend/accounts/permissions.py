from __future__ import annotations

from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class IsAdminUser(BasePermission):
    """
    Django staff OR has admin role.
    """
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if getattr(u, "is_staff", False):
            return True
        return UserRole.objects.filter(user=u, role__slug="admin").exists()


class HasRole(BasePermission):
    """
    View must declare: required_roles = ["therapist", "supervisor"]
    """
    def has_permission(self, request, view):
        required = getattr(view, "required_roles", None)
        if not required:
            return True
        u = request.user
        if not (u and u.is_authenticated):
            return False
        return UserRole.objects.filter(user=u, role__slug__in=required).exists()
