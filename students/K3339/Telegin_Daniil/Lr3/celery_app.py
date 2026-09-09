"""Celery configuration for background parsing jobs."""

from __future__ import annotations

import os

from celery import Celery


celery_app = Celery(
    "lr3",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)
