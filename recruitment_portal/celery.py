import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recruitment_portal.settings")
app = Celery("recruitment_portal")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
