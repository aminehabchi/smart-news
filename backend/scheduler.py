"""Schedules the hourly pipeline run (scrape + clean + NER + topic classification) from within the API process."""

import logging
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db import PIPELINE_RUNS_COLLECTION, get_collection

logger = logging.getLogger("scheduler")

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
PIPELINE_PYTHON = PIPELINE_DIR / "venv" / "bin" / "python"

# Keep stored output/error reasonably bounded -- tracebacks/logs from a full
# scrape run can be long, and only the tail is useful for debugging failures.
_OUTPUT_TAIL_CHARS = 4000


def is_pipeline_running() -> bool:
    return get_collection(PIPELINE_RUNS_COLLECTION).find_one({"status": "running"}) is not None


def run_pipeline(trigger: str = "scheduled") -> None:
    runs = get_collection(PIPELINE_RUNS_COLLECTION)
    if is_pipeline_running():
        logger.warning("Pipeline run already in progress, skipping %s trigger", trigger)
        return

    run_id = runs.insert_one(
        {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "status": "running",
            "trigger": trigger,
            "output": None,
            "error": None,
        }
    ).inserted_id

    logger.info("Starting %s pipeline run", trigger)
    result = subprocess.run(
        [str(PIPELINE_PYTHON), "orchestrator.py"],
        cwd=PIPELINE_DIR,
        capture_output=True,
        text=True,
    )
    finished_at = datetime.now(timezone.utc).isoformat()
    if result.returncode != 0:
        logger.error("Pipeline run failed: %s", result.stderr)
        runs.update_one(
            {"_id": run_id},
            {
                "$set": {
                    "status": "failed",
                    "finished_at": finished_at,
                    "output": result.stdout[-_OUTPUT_TAIL_CHARS:],
                    "error": result.stderr[-_OUTPUT_TAIL_CHARS:],
                }
            },
        )
    else:
        logger.info("Pipeline run finished: %s", result.stdout.strip())
        runs.update_one(
            {"_id": run_id},
            {
                "$set": {
                    "status": "success",
                    "finished_at": finished_at,
                    "output": result.stdout[-_OUTPUT_TAIL_CHARS:],
                }
            },
        )


def trigger_manual_run() -> bool:
    """Kicks off a pipeline run in the background. Returns False without
    starting anything if a run is already in progress."""
    if is_pipeline_running():
        return False
    threading.Thread(target=run_pipeline, args=("manual",), daemon=True).start()
    return True


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, IntervalTrigger(hours=1), id="hourly_scrape")
    scheduler.start()
    return scheduler
