import tempfile
import csv
from pathlib import Path
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Candidate, JobRole, ScreeningResult, User
from .services.ingestion import MissingColumnsError, RowValidationError, clean_record, ingest_file


class IngestionTests(TestCase):
    def sample(self):
        return {"candidate_name":"  ana ray ","email":"ANA@example.com","phone":"+91 98765 43210","college":"North College","applied_role":"py-dj","skills":"Python, Django, Python","experience_months":"12","notice_period_days":"30","expected_salary":"500000","resume_text":"Python Django","portfolio_url":"https://example.com","historical_selection_status":"selected"}

    def test_clean_record(self):
        result = clean_record(self.sample())
        self.assertEqual(result["candidate_name"], "Ana Ray")
        self.assertEqual(result["email"], "ana@example.com")
        self.assertEqual(result["skills"], "django, python")

    def test_invalid_email_is_rejected(self):
        row = self.sample(); row["email"] = "bad"
        with self.assertRaises(RowValidationError): clean_record(row)

    def test_ingest_writes_both_output_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, accepted, rejected = Path(tmp)/"in.csv", Path(tmp)/"accepted.csv", Path(tmp)/"rejected.csv"
            with source.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.sample().keys())
                writer.writeheader()
                writer.writerow(self.sample())
            good, bad = ingest_file(source, accepted, rejected)
            self.assertEqual((len(good),len(bad)),(1,0)); self.assertTrue(accepted.exists()); self.assertTrue(rejected.exists())


@override_settings(CACHES={"default":{"BACKEND":"django.core.cache.backends.locmem.LocMemCache"}})
class PortalTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user("hr",password="StrongPass123!",role="HR")
        self.interviewer=User.objects.create_user("interviewer",password="StrongPass123!",role="INTERVIEWER")
        self.admin=User.objects.create_user("admin",password="StrongPass123!",role="ADMIN",is_staff=True,is_superuser=True)
        self.role=JobRole.objects.create(name="Python Developer",code="PY-DJ",required_skills="python,django")
        self.candidate=Candidate.objects.create(job_role=self.role,candidate_name="Ana",email="ana@example.com",phone="+919876543210",college="North",skills="python,django",experience_months=12,expected_salary=500000)
        ScreeningResult.objects.create(candidate=self.candidate)

    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse("dashboard-explicit")).status_code,302)

    def test_candidate_json(self):
        self.client.force_login(self.user)
        response=self.client.get(reverse("candidate-json-detail",args=[self.candidate.pk]))
        self.assertEqual(response.status_code,200); self.assertEqual(response.json()["role"],"PY-DJ")

    def test_interviewer_has_read_only_portal_access(self):
        self.client.force_login(self.interviewer)
        self.assertEqual(self.client.get(reverse("candidate-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("candidate-detail", args=[self.candidate.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("candidate-edit", args=[self.candidate.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("batch-upload")).status_code, 403)

    def test_hr_and_admin_can_access_management_features(self):
        for user in (self.user, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("batch-upload")).status_code, 200)
            self.assertEqual(self.client.get(reverse("candidate-edit", args=[self.candidate.pk])).status_code, 200)

    def test_api_docs_nav_link_is_admin_only(self):
        for user in (self.user, self.interviewer):
            self.client.force_login(user)
            self.assertNotContains(self.client.get(reverse("dashboard")), "API docs")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("dashboard")), "API docs")


class APIPermissionTests(APITestCase):
    def test_hr_can_list_candidates_without_otp(self):
        user=User.objects.create_user("newhr",password="StrongPass123!",role="HR")
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get("/api/candidates/").status_code,200)
