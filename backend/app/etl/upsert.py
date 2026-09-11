"""Upsert transformed OCM rows into the database."""
import logging

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.etl.transform import OperatorRow, StationRow
from app.models import Operator, Station

logger = logging.getLogger("app.etl.upsert")

# Postgres/psycopg2 can choke on very large multi-row upserts (both on bind
# parameter counts and on "ON CONFLICT DO UPDATE command cannot affect row a
# second time" if a batch happens to contain a duplicate key). Chunking
# keeps each statement small and lets us de-dupe reliably per batch.
BATCH_SIZE = 500


def _chunk(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def upsert_operators(db: Session, operators: list[OperatorRow]) -> dict[int, int]:
    """Upsert operators, return a mapping of ocm_operator_id -> internal id."""
    if not operators:
        return {}

    # De-dupe by ocm_operator_id (multiple stations share the same operator;
    # also protects against ON CONFLICT hitting the same row twice in one
    # statement).
    unique = list({op["ocm_operator_id"]: op for op in operators}.values())

    for batch in _chunk(unique, BATCH_SIZE):
        stmt = insert(Operator).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Operator.ocm_operator_id],
            set_={"name": stmt.excluded.name, "website": stmt.excluded.website},
        )
        db.execute(stmt)
    db.commit()

    rows = db.query(Operator.ocm_operator_id, Operator.id).all()
    return {ocm_id: internal_id for ocm_id, internal_id in rows}


def upsert_stations(
    db: Session, stations: list[StationRow], operator_id_map: dict[int, int]
) -> int:
    if not stations:
        return 0

    # De-dupe by ocm_id (keep the last occurrence) — OCM responses can
    # occasionally include the same POI twice, and Postgres rejects an
    # ON CONFLICT DO UPDATE that would affect the same row twice within one
    # statement.
    by_ocm_id: dict[int, dict] = {}
    for s in stations:
        operator_id = operator_id_map.get(s["ocm_operator_id"]) if s["ocm_operator_id"] else None
        by_ocm_id[s["ocm_id"]] = {
            "ocm_id": s["ocm_id"],
            "operator_id": operator_id,
            "name": s["name"],
            "geom": WKTElement(f"POINT({s['longitude']} {s['latitude']})", srid=4326),
            "max_power_kw": s["max_power_kw"],
            "usage_type": s["usage_type"],
            "connector_types": s["connector_types"],
            "number_of_points": s["number_of_points"],
            "is_ac": s["is_ac"],
            "is_dc": s["is_dc"],
            "drive_through": s["drive_through"],
            "caravan_friendly": s["caravan_friendly"],
            "trailer_friendly": s["trailer_friendly"],
            "hgv_friendly": s["hgv_friendly"],
        }

    values = list(by_ocm_id.values())
    update_cols_names = (
        "operator_id",
        "name",
        "geom",
        "max_power_kw",
        "usage_type",
        "connector_types",
        "number_of_points",
        "is_ac",
        "is_dc",
        "drive_through",
        "caravan_friendly",
        "trailer_friendly",
        "hgv_friendly",
    )

    for batch in _chunk(values, BATCH_SIZE):
        stmt = insert(Station).values(batch)
        update_cols = {col: stmt.excluded[col] for col in update_cols_names}
        stmt = stmt.on_conflict_do_update(index_elements=[Station.ocm_id], set_=update_cols)
        db.execute(stmt)
    db.commit()

    logger.info("[ETL] Upserted %d stations", len(values))
    return len(values)
