from dotenv import load_dotenv
from pathlib import Path

# Fix #15: Load .env before importing config
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

from celery import Celery
from backend.core.logging_config import configure_logging
import backend.config as config

# Fix #1: Configure logging for the Celery worker process
configure_logging()

celery_app = Celery(
    "dia",
    broker=config.effective_broker_url,
    backend=config.effective_result_backend,
    include=["backend.jobs.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=False,
    task_eager_propagates=False,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)
