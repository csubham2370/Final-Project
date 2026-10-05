from django.db import transaction
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from screening.models import ApplicationBatch, Candidate, InterviewFeedback, JobRole, ScreeningResult
from screening.ml.predict import predict_shortlist
from .permissions import IsHRorAdmin, IsInterviewerOrAdmin
from .serializers import BatchSerializer, CandidateSerializer, InterviewFeedbackSerializer, JobRoleSerializer, RegistrationSerializer, ScreeningResultSerializer


class RegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegistrationSerializer

@extend_schema(
    request=inline_serializer(name="LogoutRequest", fields={"refresh": serializers.CharField()}),
    responses={205: None},
)
@api_view(["POST"])
def logout(request):
    token = request.data.get("refresh")
    if not token:
        return Response({"detail": "refresh token is required"}, status=400)
    try:
        RefreshToken(token).blacklist()
    except Exception:
        return Response({"detail": "Invalid or expired token."}, status=400)
    return Response(status=status.HTTP_205_RESET_CONTENT)


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related("job_role").all()
    serializer_class = CandidateSerializer
    permission_classes = [IsHRorAdmin]


class JobRoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobRole.objects.filter(is_active=True)
    serializer_class = JobRoleSerializer
    permission_classes = [permissions.IsAuthenticated]


class BatchDetailView(generics.RetrieveAPIView):
    queryset = ApplicationBatch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsHRorAdmin]


class ScreeningResultListView(generics.ListAPIView):
    serializer_class = ScreeningResultSerializer
    permission_classes = [IsHRorAdmin]

    def get_queryset(self):
        return ScreeningResult.objects.select_related("candidate", "candidate__job_role").order_by("-rule_score")


class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = InterviewFeedbackSerializer
    permission_classes = [IsInterviewerOrAdmin]


@extend_schema(
    request=inline_serializer(name="MLPredictionRequest", fields={
        "experience_months": serializers.FloatField(), "notice_period_days": serializers.FloatField(),
        "expected_salary": serializers.FloatField(), "skill_match_score": serializers.FloatField(),
    }),
    responses=inline_serializer(name="MLPredictionResponse", fields={
        "prediction": serializers.CharField(), "confidence": serializers.FloatField(), "algorithm": serializers.CharField(),
    }),
)
@api_view(["POST"])
@permission_classes([IsHRorAdmin])
def ml_predict(request):
    try:
        prediction = predict_shortlist(request.data)
    except (KeyError, TypeError, ValueError) as exc:
        return Response({"detail": str(exc)}, status=400)
    return Response(prediction)
