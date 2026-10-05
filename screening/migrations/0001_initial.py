from django.conf import settings
from django.contrib.auth.models import UserManager
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(name="User", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("password", models.CharField(max_length=128, verbose_name="password")), ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
            ("is_superuser", models.BooleanField(default=False)), ("username", models.CharField(max_length=150, unique=True)),
            ("first_name", models.CharField(blank=True, max_length=150)), ("last_name", models.CharField(blank=True, max_length=150)),
            ("email", models.EmailField(blank=True, max_length=254)), ("is_staff", models.BooleanField(default=False)),
            ("is_active", models.BooleanField(default=True)), ("date_joined", models.DateTimeField(auto_now_add=True)),
            ("role", models.CharField(choices=[("HR", "HR"), ("INTERVIEWER", "Interviewer"), ("ADMIN", "Admin")], default="HR", max_length=20)),
            ("is_email_verified", models.BooleanField(default=False)),
            ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group")),
            ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission")),
        ], managers=[("objects", UserManager())]),
        migrations.CreateModel(name="JobRole", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=120, unique=True)),
            ("code", models.CharField(max_length=20, unique=True)), ("required_skills", models.CharField(max_length=500)),
            ("min_experience_months", models.PositiveIntegerField(default=0)), ("max_salary", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ("is_active", models.BooleanField(default=True)),
        ]),
        migrations.CreateModel(name="ApplicationBatch", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("source_file", models.FileField(upload_to="batches/%Y/%m/")),
            ("status", models.CharField(choices=[("PENDING", "Pending"), ("PROCESSING", "Processing"), ("COMPLETED", "Completed"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
            ("total_rows", models.PositiveIntegerField(default=0)), ("processed_rows", models.PositiveIntegerField(default=0)), ("accepted_rows", models.PositiveIntegerField(default=0)), ("rejected_rows", models.PositiveIntegerField(default=0)),
            ("error_message", models.TextField(blank=True)), ("accepted_file", models.FileField(blank=True, upload_to="results/")), ("rejected_file", models.FileField(blank=True, upload_to="results/")),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("completed_at", models.DateTimeField(blank=True, null=True)),
            ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="batches", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="Candidate", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("candidate_name", models.CharField(max_length=150)),
            ("email", models.EmailField(max_length=254, unique=True)), ("phone", models.CharField(max_length=20)), ("college", models.CharField(max_length=180)), ("skills", models.CharField(max_length=800)),
            ("experience_months", models.PositiveIntegerField(default=0)), ("notice_period_days", models.PositiveIntegerField(default=0)), ("expected_salary", models.DecimalField(decimal_places=2, max_digits=12)),
            ("resume_text", models.TextField(blank=True)), ("resume_file", models.FileField(blank=True, upload_to="resumes/")), ("profile_image", models.ImageField(blank=True, upload_to="candidate_images/")),
            ("portfolio_url", models.URLField(blank=True)), ("historical_selection_status", models.CharField(blank=True, max_length=40)), ("is_valid", models.BooleanField(default=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="candidates", to="screening.applicationbatch")),
            ("job_role", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="candidates", to="screening.jobrole")),
        ], options={"ordering": ["candidate_name"]}),
        migrations.CreateModel(name="ScreeningResult", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("status", models.CharField(choices=[("PENDING", "Pending"), ("SELECTED", "Selected"), ("REJECTED", "Rejected"), ("WAITLISTED", "Waitlisted")], default="PENDING", max_length=20)),
            ("rule_score", models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
            ("ml_probability", models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
            ("nlp_skill_score", models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])), ("notes", models.TextField(blank=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("candidate", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="screening_result", to="screening.candidate")),
            ("screened_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="InterviewSlot", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("starts_at", models.DateTimeField()), ("duration_minutes", models.PositiveIntegerField(default=30)), ("is_booked", models.BooleanField(default=False)),
            ("interviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="interview_slots", to=settings.AUTH_USER_MODEL)),
            ("job_role", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interview_slots", to="screening.jobrole")),
        ], options={"ordering": ["starts_at"]}),
        migrations.CreateModel(name="InterviewFeedback", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("technical_score", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
            ("communication_score", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])), ("recommendation", models.CharField(choices=[("HIRE", "Hire"), ("HOLD", "Hold"), ("NO_HIRE", "No hire")], max_length=30)),
            ("comments", models.TextField(blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to="screening.candidate")),
            ("interviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="feedback", to=settings.AUTH_USER_MODEL)), ("slot", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="feedback", to="screening.interviewslot")),
        ]),
        migrations.CreateModel(name="EmailOTP", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("code", models.CharField(max_length=6)), ("created_at", models.DateTimeField(auto_now_add=True)), ("used", models.BooleanField(default=False)),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="email_otps", to=settings.AUTH_USER_MODEL)),
        ]),
    ]
