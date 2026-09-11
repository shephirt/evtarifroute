"""OpenChargeMap ETL orchestration.

Fetches charging station data for configured regions and upserts into the
local PostGIS database. Region list is config-driven via TARGET_REGIONS env
var (comma-separated ISO country codes) to allow future extension beyond
the initial DACH + NL scope.

Runs entirely inside the `app` process (see app.etl.scheduler for the
periodic in-process trigger, and POST /api/etl/run for the manual one).
There is no separate ETL container/service.
"""
import logging
import os

from app.database import SessionLocal
from app.etl.ocm_client import fetch_pois_for_region
from app.etl.transform import extract_operator, extract_station
from app.etl.upsert import upsert_operators, upsert_stations

logger = logging.getLogger("app.etl")


def _target_regions() -> list[str]:
    return [r.strip() for r in os.environ.get("TARGET_REGIONS", "DE,AT,CH,NL").split(",") if r.strip()]


def run_etl() -> dict:
    """Run one OCM ingestion pass across all configured regions.

    Returns a summary dict: {"regions": [...], "stations_upserted": N, ...}
    """
    regions = _target_regions()
    api_key = os.environ.get("OCM_API_KEY")

    if not api_key:
        logger.warning(
            "[ETL] OCM_API_KEY not set — skipping fetch. "
            "Set it in .env to enable real ingestion."
        )
        return {"regions": regions, "status": "skipped", "reason": "missing OCM_API_KEY"}

    total_stations = 0
    per_region_counts: dict[str, int] = {}

    db = SessionLocal()
    try:
        for region in regions:
            try:
                pois = fetch_pois_for_region(region, api_key)
            except Exception:
                logger.exception("[ETL] Failed to fetch POIs for region %s", region)
                continue

            operators = [op for op in (extract_operator(p) for p in pois) if op]
            stations = [s for s in (extract_station(p) for p in pois) if s]

            operator_id_map = upsert_operators(db, operators)
            count = upsert_stations(db, stations, operator_id_map)

            per_region_counts[region] = count
            total_stations += count
    finally:
        db.close()

    logger.info(
        "[ETL] Ingestion complete. Regions: %s, total stations upserted: %d",
        regions,
        total_stations,
    )
    return {
        "regions": regions,
        "status": "ok",
        "stations_upserted": total_stations,
        "per_region": per_region_counts,
    }


if __name__ == "__main__":
    # Still runnable standalone for local debugging:
    #   python -m app.etl.ocm_fetch
    logging.basicConfig(level=logging.INFO)
    run_etl()
