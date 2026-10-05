from rest_framework.permissions import BasePermission


class IsHRorAdmin(BasePermission):
    message = "HR or Admin access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role in {"ADMIN", "HR"})


class IsInterviewerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role in {"INTERVIEWER", "ADMIN"})
