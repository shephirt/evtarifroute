"""One-time data bootstrap on app startup.

Fixes the "empty app on first boot" problem: without this, a fresh
deployment has zero stations and zero tariffs until someone manually calls
POST /api/etl/run and POST /api/tariffs/seed — so radius/route analysis
would silently return empty results with no indication why.

Runs in a background thread on startup (non-blocking — the app becomes
healthy immediately, data fills in a few seconds later) and only actually
does anything if the relevant tables are empty, so it's a no-op on every
subsequent restart once data exists.
"""
import logging

from app.database import SessionLocal
from app.etl.ocm_fetch import run_etl
from app.models import MspTariff, Station
from app.tariffs.seed import seed_tariffs

logger = logging.getLogger("app.bootstrap")


def bootstrap_data() -> None:
    db = SessionLocal()
    try:
        station_count = db.query(Station).count()
    finally:
        db.close()

    if station_count == 0:
        logger.info("[Bootstrap] No stations in DB — running initial OCM ingestion...")
        try:
            run_etl()
        except Exception:
            logger.exception("[Bootstrap] Initial ETL run failed")
    else:
        logger.info("[Bootstrap] %d stations already present, skipping initial ETL", station_count)

    db = SessionLocal()
    try:
        tariff_count = db.query(MspTariff).count()
        if tariff_count == 0:
            logger.info("[Bootstrap] No tariffs in DB — seeding curated tariff data...")
            seed_tariffs(db)
        else:
            logger.info("[Bootstrap] %d tariffs already present, skipping seed", tariff_count)
    except Exception:
        logger.exception("[Bootstrap] Initial tariff seed failed")
    finally:
        db.close()
