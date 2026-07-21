"""Schedules the daily pipeline run (scrape + store) from within the API process."""

import logging
import subprocess
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("scheduler")

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
PIPELINE_PYTHON = PIPELINE_DIR / "venv" / "bin" / "python"


def run_pipeline() -> None:
    logger.info("Starting scheduled pipeline run")
    result = subprocess.run(
        [str(PIPELINE_PYTHON), "orchestrator.py"],
        cwd=PIPELINE_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Pipeline run failed: %s", result.stderr)
    else:
        logger.info("Pipeline run finished: %s", result.stdout.strip())


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, CronTrigger(hour=6, minute=0), id="daily_scrape")
    scheduler.start()
    return scheduler
