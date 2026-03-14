from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStaffOrAdmin(BasePermission):
    """Allow STAFF and ADMIN users only."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role in ('STAFF', 'ADMIN'))


class IsAdminRole(BasePermission):
    """Allow ADMIN users only."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role == 'ADMIN')


class IsOwnerOrStaff(BasePermission):
    """Allow item owner, or STAFF/ADMIN, for object-level access."""
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ('STAFF', 'ADMIN'):
            return True
        # Check reporter FK (works for Item objects)
        reporter = getattr(obj, 'reporter', None)
        if reporter is not None:
            return reporter == request.user
        return False
