from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard-explicit"),
    path("batches/upload/", views.upload_batch, name="batch-upload"),
    path("batches/<int:pk>/", views.batch_detail, name="batch-detail"),
    path("candidates/", views.CandidateListView.as_view(), name="candidate-list"),
    path("candidates/<int:pk>/", views.CandidateDetailView.as_view(), name="candidate-detail"),
    path("candidates/<int:pk>/edit/", views.CandidateUpdateView.as_view(), name="candidate-edit"),
    path("candidates/<int:pk>/delete/", views.InvalidCandidateDeleteView.as_view(), name="candidate-delete"),
    path("candidates/<int:pk>/screening/", views.edit_screening, name="screening-edit"),
    path("json/candidates/", views.candidate_json, name="candidate-json-list"),
    path("json/candidates/<int:pk>/", views.candidate_json, name="candidate-json-detail"),
    path("ajax/duplicate-email/", views.duplicate_email, name="duplicate-email"),
    path("ajax/slots/", views.available_slots, name="available-slots"),
]
