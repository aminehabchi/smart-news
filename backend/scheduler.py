"""Schedules the hourly pipeline run (scrape + clean + NER + topic classification) from within the API process."""

import logging
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bson import ObjectId

from db import PIPELINE_RUNS_COLLECTION, get_collection

logger = logging.getLogger("scheduler")

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
PIPELINE_PYTHON = PIPELINE_DIR / "venv" / "bin" / "python"

# Keep stored output/error reasonably bounded -- tracebacks/logs from a full
# scrape run can be long, and only the tail is useful for debugging failures.
_OUTPUT_TAIL_CHARS = 4000

# Hard ceiling on a single run -- a scrape that hangs (dead site, stuck
# browser) would otherwise leave the "running" record (and therefore every
# future scheduled/manual run, see is_pipeline_running) stuck forever.
# Normal runs take a few minutes; this is generous headroom, not a target.
_RUN_TIMEOUT_SECONDS = 30 * 60


def is_pipeline_running() -> bool:
    return get_collection(PIPELINE_RUNS_COLLECTION).find_one({"status": "running"}) is not None


def _start_run(trigger: str) -> ObjectId | None:
    """Inserts the "running" record and returns its id, or None if a run is
    already in progress. Synchronous and cheap, so callers can rely on the
    record existing immediately, before any subprocess work begins."""
    runs = get_collection(PIPELINE_RUNS_COLLECTION)
    if is_pipeline_running():
        return None
    return runs.insert_one(
        {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "status": "running",
            "trigger": trigger,
            "output": None,
            "error": None,
        }
    ).inserted_id


def _execute_run(run_id: ObjectId) -> None:
    """Runs the scrape subprocess and always closes out the run record --
    on a clean exit, a non-zero exit, a timeout, or any other exception --
    so a crash/hang can never leave the record stuck at "running" and lock
    out every future run."""
    runs = get_collection(PIPELINE_RUNS_COLLECTION)
    logger.info("Starting pipeline run %s", run_id)
    try:
        result = subprocess.run(
            [str(PIPELINE_PYTHON), "orchestrator.py"],
            cwd=PIPELINE_DIR,
            capture_output=True,
            text=True,
            timeout=_RUN_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.exception("Pipeline run %s crashed before completing", run_id)
        runs.update_one(
            {"_id": run_id},
            {
                "$set": {
                    "status": "failed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc)[-_OUTPUT_TAIL_CHARS:],
                }
            },
        )
        return

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


def run_pipeline() -> None:
    """Entry point for the hourly APScheduler job. APScheduler already runs
    jobs off the main thread, so this executes synchronously."""
    run_id = _start_run("scheduled")
    if run_id is None:
        logger.warning("Pipeline run already in progress, skipping scheduled trigger")
        return
    _execute_run(run_id)


def trigger_manual_run() -> bool:
    """Starts a pipeline run in the background. Returns False without
    starting anything if a run is already in progress. The "running" record
    is inserted synchronously before returning, so a caller that immediately
    re-fetches /api/pipeline/runs is guaranteed to see it -- only the
    subprocess itself runs on a background thread."""
    run_id = _start_run("manual")
    if run_id is None:
        return False
    threading.Thread(target=_execute_run, args=(run_id,), daemon=True).start()
    return True


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, IntervalTrigger(hours=1), id="hourly_scrape")
    scheduler.start()
    return scheduler
