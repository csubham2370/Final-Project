from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from screening.models import ApplicationBatch, Candidate, InterviewFeedback, JobRole, ScreeningResult, User


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def create(self, validated_data):
        return User.objects.create_user(role=User.Role.HR, **validated_data)


class JobRoleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = JobRole
        fields = ("url", "id", "code", "name", "required_skills", "min_experience_months", "max_salary", "is_active")


class CandidateSerializer(serializers.ModelSerializer):
    role_code = serializers.SlugRelatedField(source="job_role", slug_field="code", queryset=JobRole.objects.all())

    class Meta:
        model = Candidate
        fields = ("id", "candidate_name", "email", "phone", "college", "role_code", "skills", "experience_months", "notice_period_days", "expected_salary", "resume_text", "resume_file", "profile_image", "portfolio_url", "historical_selection_status", "is_valid")
        read_only_fields = ("is_valid",)

    def validate_phone(self, value):
        from screening.services.ingestion import PHONE_RE
        if not PHONE_RE.fullmatch(value.replace(" ", "")):
            raise serializers.ValidationError("Enter a valid international phone number.")
        return value


class BatchSerializer(serializers.ModelSerializer):
    progress_percent = serializers.IntegerField(read_only=True)
    class Meta:
        model = ApplicationBatch
        fields = ("id", "status", "total_rows", "processed_rows", "accepted_rows", "rejected_rows", "progress_percent", "error_message", "created_at", "completed_at")


class ScreeningResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.candidate_name", read_only=True)
    class Meta:
        model = ScreeningResult
        fields = "__all__"


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = ("id", "candidate", "slot", "technical_score", "communication_score", "recommendation", "comments", "created_at")
        read_only_fields = ("created_at",)

    def create(self, validated_data):
        validated_data["interviewer"] = self.context["request"].user
        feedback = super().create(validated_data)
        feedback.slot.is_booked = True
        feedback.slot.save(update_fields=["is_booked"])
        return feedback
