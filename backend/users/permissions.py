from rest_framework.permissions import BasePermission

from .models import UserRole


class IsAdminUserRole(BasePermission):
    """Allow only admin role or superuser."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or getattr(user, "role", None) == UserRole.ADMIN)
        )


class IsCashierOrAdminRole(BasePermission):
    """Allow cashier or admin (including superuser)."""

    def has_permission(self, request, view):
        user = request.user
        role = getattr(user, "role", None)
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or role in (UserRole.CASHIER, UserRole.ADMIN))
        )
