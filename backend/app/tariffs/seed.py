"""Resolve curated tariff seed data (operator names) into `msp_tariffs` rows.

Operator name -> ocm_operator_id resolution happens at seed time against
whatever has actually been ingested (see Phase 2 ETL) — this makes the seed
data portable across environments/regions without hardcoding OCM's internal
operator IDs.
"""
import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import MspTariff, Operator
from app.tariffs.seed_data import TARIFF_SEED_DATA

logger = logging.getLogger("app.tariffs.seed")


def seed_tariffs(db: Session) -> dict:
    """Upsert all curated tariffs, resolving covered_operator_names against
    the operators table. Returns a summary dict."""
    all_names = {
        name for entry in TARIFF_SEED_DATA for name in entry["covered_operator_names"]
    }
    rows = (
        db.query(Operator.name, Operator.ocm_operator_id)
        .filter(Operator.name.in_(all_names))
        .all()
    )
    name_to_ocm_id = {name: ocm_id for name, ocm_id in rows}

    unmatched: dict[str, list[str]] = {}
    values = []

    for entry in TARIFF_SEED_DATA:
        covered_ids = []
        entry_unmatched = []
        for name in entry["covered_operator_names"]:
            ocm_id = name_to_ocm_id.get(name)
            if ocm_id is not None:
                covered_ids.append(ocm_id)
            else:
                entry_unmatched.append(name)

        if entry_unmatched:
            unmatched[entry["name"]] = entry_unmatched

        values.append(
            {
                "name": entry["name"],
                "provider": entry["provider"],
                "base_fee_monthly": entry["base_fee_monthly"],
                "price_per_kwh_ac": entry["price_per_kwh_ac"],
                "price_per_kwh_dc": entry["price_per_kwh_dc"],
                "roaming_price_per_kwh": entry["roaming_price_per_kwh"],
                "covered_operator_ids": covered_ids,
                "notes": entry["notes"],
            }
        )

    stmt = insert(MspTariff).values(values)
    update_cols = {
        col: stmt.excluded[col]
        for col in (
            "provider",
            "base_fee_monthly",
            "price_per_kwh_ac",
            "price_per_kwh_dc",
            "roaming_price_per_kwh",
            "covered_operator_ids",
            "notes",
        )
    }
    stmt = stmt.on_conflict_do_update(index_elements=[MspTariff.name], set_=update_cols)
    db.execute(stmt)
    db.commit()

    if unmatched:
        logger.warning(
            "[Tariffs] Some covered_operator_names had no matching operator "
            "in the DB (likely not yet ingested for the configured regions): %s",
            unmatched,
        )

    logger.info("[Tariffs] Seeded/updated %d tariffs", len(values))
    return {
        "tariffs_seeded": len(values),
        "unmatched_operator_names": unmatched,
    }
