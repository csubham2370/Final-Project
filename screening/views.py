from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from .forms import BatchUploadForm, CandidateForm, ScreeningStatusForm
from .models import ApplicationBatch, Candidate, InterviewSlot, JobRole, ScreeningResult, User
from .tasks import process_candidate_batch
from .web_permissions import RoleRequiredMixin, role_required


@login_required
def dashboard(request):
    role_id = request.GET.get("role") or request.COOKIES.get("last_role_filter", "")
    candidates = Candidate.objects.select_related("job_role")
    if role_id:
        candidates = candidates.filter(job_role_id=role_id)
    metrics = candidates.aggregate(count=Count("id"), salary_sum=Sum("expected_salary"), salary_min=Min("expected_salary"), salary_max=Max("expected_salary"), salary_avg=Avg("expected_salary"))
    status_counts = ScreeningResult.objects.values("status").annotate(total=Count("id")).order_by("status")
    roles_over_five = JobRole.objects.annotate(candidate_count=Count("candidates")).filter(candidate_count__gt=5)
    role_features = {
        User.Role.ADMIN: ["Full portal and Django Admin access", "Manage candidates, batches, roles and screening", "Review all reports and secured APIs"],
        User.Role.HR: ["Upload and monitor candidate batches", "Create and edit candidates", "Update screening decisions and view reports"],
        User.Role.INTERVIEWER: ["View candidate profiles", "Review assigned interview slots", "Submit interview feedback through the secured API"],
    }
    response = render(request, "screening/dashboard.html", {"metrics": metrics, "status_counts": status_counts, "roles": JobRole.objects.filter(is_active=True), "selected_role": str(role_id), "roles_over_five": roles_over_five, "role_features": role_features.get(request.user.role, [])})
    if role_id:
        response.set_cookie("last_role_filter", role_id, max_age=30 * 24 * 3600, samesite="Lax")
    return response


@role_required(User.Role.HR, User.Role.ADMIN)
def upload_batch(request):
    if request.method == "POST":
        form = BatchUploadForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.uploaded_by = request.user
            batch.save()
            request.session["current_batch_id"] = batch.id
            process_candidate_batch.delay(batch.id)
            messages.success(request, f"Batch {batch.id} queued for processing.")
            return redirect("batch-detail", pk=batch.id)
    else:
        form = BatchUploadForm()
    return render(request, "screening/upload.html", {"form": form})


class CandidateListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.HR, User.Role.ADMIN, User.Role.INTERVIEWER)
    model = Candidate
    paginate_by = 20
    template_name = "screening/candidate_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("job_role", "screening_result")
        query = self.request.GET.get("q", "").strip()
        return qs.filter(candidate_name__icontains=query) if query else qs


class CandidateDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = (User.Role.HR, User.Role.ADMIN, User.Role.INTERVIEWER)
    model = Candidate
    template_name = "screening/candidate_detail.html"


class CandidateUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.HR, User.Role.ADMIN)
    model = Candidate
    form_class = CandidateForm
    template_name = "screening/form.html"
    success_url = reverse_lazy("candidate-list")


class InvalidCandidateDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = (User.Role.HR, User.Role.ADMIN)
    model = Candidate
    template_name = "screening/confirm_delete.html"
    success_url = reverse_lazy("candidate-list")

    def form_valid(self, form):
        if self.object.is_valid:
            messages.error(self.request, "Only invalid candidate records may be deleted.")
            return redirect("candidate-detail", pk=self.object.pk)
        return super().form_valid(form)


@role_required(User.Role.HR, User.Role.ADMIN)
def edit_screening(request, pk):
    result = get_object_or_404(ScreeningResult, candidate_id=pk)
    form = ScreeningStatusForm(request.POST or None, instance=result)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.screened_by = request.user
        item.save()
        return redirect("candidate-detail", pk=pk)
    return render(request, "screening/form.html", {"form": form, "title": "Update screening status"})


@role_required(User.Role.HR, User.Role.ADMIN)
def batch_detail(request, pk):
    return render(request, "screening/batch_detail.html", {"batch": get_object_or_404(ApplicationBatch, pk=pk)})


@role_required(User.Role.HR, User.Role.ADMIN)
def duplicate_email(request):
    email = request.GET.get("email", "").strip().lower()
    return JsonResponse({"exists": bool(email and Candidate.objects.filter(email__iexact=email).exists())})


@role_required(User.Role.HR, User.Role.ADMIN, User.Role.INTERVIEWER)
def available_slots(request):
    role_id = request.GET.get("role_id")
    slots = InterviewSlot.objects.filter(job_role_id=role_id, is_booked=False).values("id", "starts_at", "interviewer__username")[:50]
    return JsonResponse({"slots": list(slots)})


@role_required(User.Role.HR, User.Role.ADMIN)
def candidate_json(request, pk=None):
    qs = Candidate.objects.exclude(is_valid=False).order_by("candidate_name")
    if pk:
        candidate = get_object_or_404(qs, pk=pk)
        return JsonResponse({"id": candidate.id, "name": candidate.candidate_name, "email": candidate.email, "role": candidate.job_role.code, "skills": candidate.skills})
    return JsonResponse({"results": list(qs.values("id", "candidate_name", "email", "job_role__code")[:100])})
