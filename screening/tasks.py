import tempfile
from pathlib import Path
from celery import shared_task
from django.core.files import File
from django.utils import timezone
import pandas as pd
from .models import ApplicationBatch, Candidate, JobRole, ScreeningResult
from .services.ingestion import REQUIRED_COLUMNS, ingest_file
from .services.scoring import nlp_score, rule_score


@shared_task(bind=True)
def process_candidate_batch(self, batch_id):
    batch = ApplicationBatch.objects.get(pk=batch_id)
    batch.status = ApplicationBatch.Status.PROCESSING
    batch.save(update_fields=["status"])
    try:
        with tempfile.TemporaryDirectory() as folder:
            accepted_path, rejected_path = Path(folder) / "accepted_rows.csv", Path(folder) / "rejected_rows.csv"

            def report(processed, total, accepted, rejected):
                ApplicationBatch.objects.filter(pk=batch_id).update(total_rows=total, processed_rows=processed, accepted_rows=accepted, rejected_rows=rejected)
                self.update_state(state="PROGRESS", meta={"processed": processed, "total": total})

            accepted, rejected = ingest_file(batch.source_file.path, accepted_path, rejected_path, report)
            persisted = []
            for data in accepted:
                role = JobRole.objects.filter(code__iexact=data["applied_role"]).first()
                if not role:
                    rejected.append({**data, "error_reason": "unknown applied_role"})
                    continue
                persisted.append(data)
                candidate, _ = Candidate.objects.update_or_create(email=data["email"], defaults={
                    "batch": batch, "job_role": role, "candidate_name": data["candidate_name"], "phone": data["phone"],
                    "college": data["college"], "skills": data["skills"], "experience_months": data["experience_months"],
                    "notice_period_days": data["notice_period_days"], "expected_salary": data["expected_salary"],
                    "resume_text": data["resume_text"], "portfolio_url": data["portfolio_url"],
                    "historical_selection_status": data["historical_selection_status"],
                })
                result, _ = ScreeningResult.objects.get_or_create(candidate=candidate)
                result.rule_score = rule_score(candidate)
                result.nlp_skill_score = nlp_score(candidate)
                result.save()
            pd.DataFrame(persisted, columns=REQUIRED_COLUMNS).to_csv(accepted_path, index=False)
            pd.DataFrame(rejected, columns=(*REQUIRED_COLUMNS, "error_reason")).to_csv(rejected_path, index=False)
            with accepted_path.open("rb") as fh:
                batch.accepted_file.save(f"batch_{batch.id}_accepted_rows.csv", File(fh), save=False)
            with rejected_path.open("rb") as fh:
                batch.rejected_file.save(f"batch_{batch.id}_rejected_rows.csv", File(fh), save=False)
        # Progress is updated through queryset.update() inside report(). Saving
        # the original in-memory instance without update_fields would overwrite
        # those counters with the zero values loaded before processing began.
        batch.refresh_from_db(fields=["total_rows", "processed_rows"])
        batch.status = ApplicationBatch.Status.COMPLETED
        batch.completed_at = timezone.now()
        batch.accepted_rows = len(persisted)
        batch.rejected_rows = len(rejected)
        batch.save(update_fields=[
            "status", "completed_at", "accepted_rows", "rejected_rows",
            "accepted_file", "rejected_file",
        ])
        return {"accepted": len(persisted), "rejected": len(rejected)}
    except Exception as exc:
        batch.status = ApplicationBatch.Status.FAILED
        batch.error_message = str(exc)
        batch.completed_at = timezone.now()
        batch.save(update_fields=["status", "error_message", "completed_at"])
        raise
