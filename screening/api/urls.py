from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import BatchDetailView, CandidateViewSet, FeedbackCreateView, JobRoleViewSet, RegistrationView, ScreeningResultListView, logout, ml_predict

router = DefaultRouter()
router.register("candidates", CandidateViewSet)
router.register("roles", JobRoleViewSet)

urlpatterns = [
    path("auth/register/", RegistrationView.as_view(), name="api-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", logout, name="api-logout"),
    path("batches/<int:pk>/", BatchDetailView.as_view(), name="api-batch-detail"),
    path("screening-results/", ScreeningResultListView.as_view(), name="api-screening-results"),
    path("feedback/", FeedbackCreateView.as_view(), name="api-feedback"),
    path("ml/predict/", ml_predict, name="api-ml-predict"),
    path("", include(router.urls)),
]
