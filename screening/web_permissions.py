from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """Require authentication and one of the configured portal roles."""
    allowed = set(allowed_roles)

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role not in allowed:
                raise PermissionDenied("Your role does not have access to this feature.")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


class RoleRequiredMixin:
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.role not in set(self.allowed_roles):
            raise PermissionDenied("Your role does not have access to this feature.")
        return super().dispatch(request, *args, **kwargs)
