from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ApplicationBatch, Candidate, InterviewFeedback, InterviewSlot, JobRole, ScreeningResult, User


@admin.register(User)
class PortalUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("Recruitment access", {"fields": ("role",)}),)


@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "min_experience_months", "max_salary", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "required_skills")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("candidate_name", "email", "job_role", "experience_months", "expected_salary", "is_valid")
    list_filter = ("job_role", "is_valid", "historical_selection_status")
    search_fields = ("candidate_name", "email", "phone", "college", "skills")
    fieldsets = (
        ("Identity", {"fields": ("candidate_name", "email", "phone", "college", "profile_image")}),
        ("Application", {"fields": ("batch", "job_role", "skills", "experience_months", "notice_period_days", "expected_salary")}),
        ("Resume", {"fields": ("resume_text", "resume_file", "portfolio_url", "historical_selection_status", "is_valid")}),
    )


@admin.register(ApplicationBatch)
class ApplicationBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "uploaded_by", "status", "processed_rows", "total_rows", "accepted_rows", "rejected_rows", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "completed_at")


@admin.register(ScreeningResult)
class ScreeningResultAdmin(admin.ModelAdmin):
    list_display = ("candidate", "status", "rule_score", "ml_probability", "nlp_skill_score", "updated_at")
    list_filter = ("status", "candidate__job_role")
    search_fields = ("candidate__candidate_name", "candidate__email")


@admin.register(InterviewSlot)
class InterviewSlotAdmin(admin.ModelAdmin):
    list_display = ("job_role", "interviewer", "starts_at", "duration_minutes", "is_booked")
    list_filter = ("job_role", "is_booked", "starts_at")


@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):
    list_display = ("candidate", "interviewer", "technical_score", "communication_score", "recommendation")
    list_filter = ("recommendation", "interviewer")


admin.site.site_header = "Recruitment Intelligence Administration"
