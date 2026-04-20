import os
import dotenv
from celery import Celery
from celery.schedules import crontab


dotenv.read_dotenv()   

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("bank_system")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send_daily_report": {
        "task": "accounts.tasks.send_daily_report",
        "schedule": crontab(minute=0, hour=9),
    },
}