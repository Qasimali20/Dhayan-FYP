from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import (
    MeView,
    LogoutView,
    AdminCreateUserView,
    AdminReplaceUserRolesView,
    AdminListRolesView,
    AdminListUsersView,
    signup,
    forgot_password,
    verify_otp,
    reset_password,
)

urlpatterns = [
    path("login", TokenObtainPairView.as_view(), name="auth-login"),
    path("refresh", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me", MeView.as_view(), name="auth-me"),
    path("logout", LogoutView.as_view(), name="auth-logout"),

    # Signup
    path("signup", signup, name="auth-signup"),

    # Forgot / Reset Password
    path("forgot-password", forgot_password, name="forgot-password"),
    path("verify-otp", verify_otp, name="verify-otp"),
    path("reset-password", reset_password, name="reset-password"),

    # RBAC admin endpoints
    path("admin/roles", AdminListRolesView.as_view(), name="admin-list-roles"),
    path("admin/users", AdminCreateUserView.as_view(), name="admin-create-user"),
    path("admin/users/list", AdminListUsersView.as_view(), name="admin-list-users"),
    path("admin/users/<int:user_id>/roles", AdminReplaceUserRolesView.as_view(), name="admin-replace-user-roles"),
]
