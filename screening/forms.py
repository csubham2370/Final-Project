from pathlib import Path
from django import forms
from .models import ApplicationBatch, Candidate, ScreeningResult


class BatchUploadForm(forms.ModelForm):
    class Meta:
        model = ApplicationBatch
        fields = ("source_file",)

    def clean_source_file(self):
        file = self.cleaned_data["source_file"]
        if Path(file.name).suffix.lower() not in {".csv", ".xlsx"}:
            raise forms.ValidationError("Upload a CSV or XLSX file.")
        if file.size == 0:
            raise forms.ValidationError("The uploaded file is empty.")
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("The file must not exceed 10 MB.")
        return file


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        exclude = ("batch", "is_valid", "created_at")
        widgets = {"resume_text": forms.Textarea(attrs={"rows": 5})}


class ScreeningStatusForm(forms.ModelForm):
    class Meta:
        model = ScreeningResult
        fields = ("status", "notes")
