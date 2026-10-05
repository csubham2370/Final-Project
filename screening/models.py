from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        HR = "HR", "HR"
        INTERVIEWER = "INTERVIEWER", "Interviewer"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.HR)


class JobRole(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    required_skills = models.CharField(max_length=500)
    min_experience_months = models.PositiveIntegerField(default=0)
    max_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class ApplicationBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="batches")
    source_file = models.FileField(upload_to="batches/%Y/%m/")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    accepted_file = models.FileField(upload_to="results/", blank=True)
    rejected_file = models.FileField(upload_to="results/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def progress_percent(self):
        return round((self.processed_rows / self.total_rows) * 100) if self.total_rows else 0


class Candidate(models.Model):
    batch = models.ForeignKey(ApplicationBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="candidates")
    job_role = models.ForeignKey(JobRole, on_delete=models.PROTECT, related_name="candidates")
    candidate_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    college = models.CharField(max_length=180)
    skills = models.CharField(max_length=800)
    experience_months = models.PositiveIntegerField(default=0)
    notice_period_days = models.PositiveIntegerField(default=0)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2)
    resume_text = models.TextField(blank=True)
    resume_file = models.FileField(upload_to="resumes/", blank=True)
    profile_image = models.ImageField(upload_to="candidate_images/", blank=True)
    portfolio_url = models.URLField(blank=True)
    historical_selection_status = models.CharField(max_length=40, blank=True)
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["candidate_name"]

    def __str__(self):
        return f"{self.candidate_name} ({self.email})"


class ScreeningResult(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"
        WAITLISTED = "WAITLISTED", "Waitlisted"

    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name="screening_result")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rule_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    ml_probability = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])
    nlp_skill_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    notes = models.TextField(blank=True)
    screened_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class InterviewSlot(models.Model):
    job_role = models.ForeignKey(JobRole, on_delete=models.CASCADE, related_name="interview_slots")
    interviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="interview_slots")
    starts_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.job_role.code} at {self.starts_at:%Y-%m-%d %H:%M}"


class InterviewFeedback(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="feedback")
    slot = models.OneToOneField(InterviewSlot, on_delete=models.PROTECT, related_name="feedback")
    interviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="feedback")
    technical_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    communication_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    recommendation = models.CharField(max_length=30, choices=[("HIRE", "Hire"), ("HOLD", "Hold"), ("NO_HIRE", "No hire")])
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

