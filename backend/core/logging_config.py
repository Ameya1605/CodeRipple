import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """
    Call this once at application startup (main.py AND celery_app.py startup).
    Emits structured JSON lines so logs are parseable in production.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)r}',
        datefmt="%Y-%m-%dT%H:%M:%S"
    ))
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)
