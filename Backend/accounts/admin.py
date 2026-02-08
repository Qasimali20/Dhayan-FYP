from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from accounts.models import User, Role, UserRole, PasswordResetToken


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User

    ordering = ("email",)
    list_display = ("id", "email", "full_name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "full_name")

    fieldsets = (
        (None, {"fields": ("email", "password", "full_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_staff", "is_active")}),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "created_at")
    search_fields = ("slug", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "assigned_at")
    search_fields = ("user__email", "role__slug")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at", "used")
    list_filter = ("used",)
    readonly_fields = ("token", "created_at")
