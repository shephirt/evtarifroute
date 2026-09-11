"""Tariff & MSP Recommendation Engine (SRS 2.3).

Maps a ranked list of dominant CPOs (from Mode A/B analysis) to the curated
`msp_tariffs` table, estimating monthly cost per tariff based on how much of
the user's charging need is covered by that tariff's home network vs.
requiring roaming rates, then ranks tariffs cheapest-first.
"""
from sqlalchemy.orm import Session

from app.models import MspTariff, Operator


def recommend_tariffs(
    db: Session,
    rankings: list[dict],
    monthly_kwh_estimate: float = 100.0,
    prefer_dc: bool = True,
) -> list[dict]:
    """rankings: list of {"operator_id": int|None, "operator_name": str, "station_count": int}"""
    total_stations = sum(r["station_count"] for r in rankings)
    if total_stations == 0:
        return []

    operator_ids = [r["operator_id"] for r in rankings if r["operator_id"] is not None]
    ocm_id_map: dict[int, int] = {}
    if operator_ids:
        rows = (
            db.query(Operator.id, Operator.ocm_operator_id)
            .filter(Operator.id.in_(operator_ids))
            .all()
        )
        ocm_id_map = {internal_id: ocm_id for internal_id, ocm_id in rows}

    # station_count per ocm_operator_id (what msp_tariffs.covered_operator_ids references)
    stations_by_ocm_operator_id: dict[int, int] = {}
    for r in rankings:
        if r["operator_id"] is None:
            continue
        ocm_id = ocm_id_map.get(r["operator_id"])
        if ocm_id is None:
            continue
        stations_by_ocm_operator_id[ocm_id] = (
            stations_by_ocm_operator_id.get(ocm_id, 0) + r["station_count"]
        )

    tariffs = db.query(MspTariff).all()
    results = []

    for tariff in tariffs:
        covered_ids = set(tariff.covered_operator_ids or [])
        covered_station_count = sum(
            count
            for ocm_id, count in stations_by_ocm_operator_id.items()
            if ocm_id in covered_ids
        )

        if covered_station_count == 0:
            # Only recommend tariffs for CPOs actually found in this
            # search — a tariff with zero overlap with the found operators
            # isn't a useful recommendation here.
            continue

        coverage_ratio = covered_station_count / total_stations

        # Internal operator IDs (as used in `rankings`/map markers) covered by
        # this tariff — lets the frontend highlight the right stations on
        # hover (SRS 4.4).
        covered_operator_internal_ids = [
            internal_id
            for internal_id, ocm_id in ocm_id_map.items()
            if ocm_id in covered_ids
        ]

        home_price = tariff.price_per_kwh_dc if prefer_dc else tariff.price_per_kwh_ac
        if home_price is None:
            home_price = tariff.price_per_kwh_ac or tariff.price_per_kwh_dc
        roaming_price = tariff.roaming_price_per_kwh
        if home_price is None and roaming_price is None:
            # No usable pricing data for this tariff — skip cost estimate.
            continue
        home_price = float(home_price) if home_price is not None else float(roaming_price)
        roaming_price = float(roaming_price) if roaming_price is not None else home_price

        energy_cost = monthly_kwh_estimate * (
            coverage_ratio * home_price + (1 - coverage_ratio) * roaming_price
        )
        estimated_monthly_cost = float(tariff.base_fee_monthly) + energy_cost

        results.append(
            {
                "tariff_id": tariff.id,
                "name": tariff.name,
                "provider": tariff.provider,
                "estimated_monthly_cost": round(estimated_monthly_cost, 2),
                "coverage_ratio": round(coverage_ratio, 4),
                "covered_station_count": covered_station_count,
                "covered_operator_ids": covered_operator_internal_ids,
                "notes": tariff.notes,
            }
        )

    results.sort(key=lambda r: r["estimated_monthly_cost"])
    return results
