import logging
import time
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger("screening.requests")


class RequestAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/dashboard/") and not request.user.is_authenticated:
            if request.headers.get("Accept") == "application/json":
                return JsonResponse({"detail": "Authentication required."}, status=401)
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        started = time.perf_counter()
        response = self.get_response(request)
        role = getattr(request.user, "role", "anonymous") if request.user.is_authenticated else "anonymous"
        logger.info("path=%s method=%s duration_ms=%.2f role=%s", request.path, request.method, (time.perf_counter() - started) * 1000, role)
        response["X-Process-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
        return response
