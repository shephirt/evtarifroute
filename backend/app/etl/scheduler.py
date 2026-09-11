"""In-process scheduler for periodic ETL runs.

Uses APScheduler's background scheduler so the FastAPI app itself triggers
OCM ingestion on an interval, without needing any separate service/container
or external cron. Interval is configurable via ETL_INTERVAL_HOURS (default:
24h). Set ETL_INTERVAL_HOURS=0 to disable the periodic schedule (manual
trigger via POST /api/etl/run still works).
"""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from app.etl.ocm_fetch import run_etl

logger = logging.getLogger("app.etl.scheduler")

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global _scheduler

    interval_hours = float(os.environ.get("ETL_INTERVAL_HOURS", "24"))
    if interval_hours <= 0:
        logger.info("[ETL] Periodic schedule disabled (ETL_INTERVAL_HOURS<=0)")
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(run_etl, "interval", hours=interval_hours, id="ocm_etl")
    _scheduler.start()
    logger.info("[ETL] Scheduled to run every %s hour(s)", interval_hours)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
