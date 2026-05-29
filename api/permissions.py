from rest_framework.permissions import SAFE_METHODS, AllowAny, BasePermission


class IsAuthenticatedNotBlocked(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and not getattr(request.user, "is_blocked", False)
        )


class IsPanelUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.can_access_panel
            and not request.user.is_blocked
        )


class AllowCreateOrPanelOnly(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return True
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated and not request.user.is_blocked)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.can_access_panel
            and not request.user.is_blocked
        )
