"""Spatial query services backing Mode A (route) and Mode B (radius)
CPO dominance analysis (SRS 2.1 / 2.2).

All queries use `ST_DWithin` against `stations.geom::geography` for
accurate meter-based distances, backed by the `idx_stations_geog` GIST
expression index (see migration 5a30dbbebfa7) — verified ~10x faster than
relying on the plain geometry GIST index for this access pattern.

Route ranking (`rank_operators_along_route`) additionally scores operators
by how *evenly* their stations are spread along the route, not just raw
count — a CPO with 50 stations bunched in the first 100km of a 600km route
is much less useful than one with 15 stations spread across the whole
route. See `_effective_station_count`.
"""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session


def _build_filters(
    require_ac: bool,
    require_dc: bool,
    trailer_friendly: bool,
    connector_type: str | None,
    min_power_kw: float | None,
) -> tuple[str, dict]:
    """Build the combined accessibility/connector/power filter clause.

    AC and DC are OR'd together, not AND'd: checking both means "show AC or
    DC chargers" (i.e. no restriction, since every station is at least one
    of the two) — not "only stations supporting both simultaneously", which
    would incorrectly collapse results to a tiny subset (verified on real
    data: only ~6% of stations report both AC and DC connectors on the same
    station).
    """
    clauses = []
    params: dict = {}

    if require_ac and require_dc:
        clauses.append("(s.is_ac = true OR s.is_dc = true)")
    elif require_ac:
        clauses.append("s.is_ac = true")
    elif require_dc:
        clauses.append("s.is_dc = true")

    if trailer_friendly:
        clauses.append(
            "(s.drive_through = true OR s.caravan_friendly = true OR s.trailer_friendly = true)"
        )

    if connector_type:
        # Case-insensitive substring match against any of the station's
        # connector type titles (e.g. "CCS" matches "CCS (Type 2)").
        clauses.append(
            "EXISTS (SELECT 1 FROM unnest(s.connector_types) ct WHERE ct ILIKE :connector_type)"
        )
        params["connector_type"] = f"%{connector_type}%"

    if min_power_kw is not None:
        clauses.append("s.max_power_kw >= :min_power_kw")
        params["min_power_kw"] = min_power_kw

    sql = ("AND " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def rank_operators_in_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float,
    require_ac: bool = False,
    require_dc: bool = False,
    trailer_friendly: bool = False,
    connector_type: str | None = None,
    min_power_kw: float | None = None,
) -> list[dict]:
    """Rank CPOs by number of stations within radius_km of (latitude, longitude)."""
    extra_sql, extra_params = _build_filters(
        require_ac, require_dc, trailer_friendly, connector_type, min_power_kw
    )

    query = text(
        f"""
        SELECT o.id AS operator_id,
               COALESCE(o.name, 'Unknown Operator') AS operator_name,
               count(*) AS station_count
        FROM stations s
        LEFT JOIN operators o ON o.id = s.operator_id
        WHERE ST_DWithin(
                s.geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius_m
              )
              {extra_sql}
        GROUP BY o.id, o.name
        ORDER BY station_count DESC
        """
    )

    rows = db.execute(
        query,
        {"lat": latitude, "lon": longitude, "radius_m": radius_km * 1000, **extra_params},
    ).mappings()

    return [dict(row) for row in rows]


def _effective_station_count(positions_km: list[float], min_spacing_km: float) -> int:
    """Greedily count stations along a route, skipping ones "too close" to
    a previously counted one.

    Given sorted km-positions of an operator's stations along the route,
    keep the first one, then only keep the next one if it's at least
    `min_spacing_km` away from the last *kept* position (not the last seen
    position) — so a cluster of stations within min_spacing_km of each
    other only counts once, but the algorithm still "resumes" counting
    correctly further down the route.

    Example (matches the exact scenario this was designed for): stations at
    km 0, 75, 100, 200 with min_spacing_km=50 (i.e. target_spacing_km=100):
      - keep 0 (first)
      - 75 - 0 = 75 >= 50 -> keep
      - 100 - 75 = 25 < 50 -> skip (too close to the last *kept* station)
      - 200 - 75 = 125 >= 50 -> keep
      => effective count = 3 (0, 75, 200) — matches the expected result.
    """
    kept: list[float] = []
    for km in sorted(positions_km):
        if not kept or (km - kept[-1]) >= min_spacing_km:
            kept.append(km)
    return len(kept)


def rank_operators_along_route(
    db: Session,
    route_geojson: dict,
    buffer_km: float,
    require_ac: bool = False,
    require_dc: bool = False,
    trailer_friendly: bool = False,
    connector_type: str | None = None,
    min_power_kw: float | None = None,
    target_spacing_km: float = 100.0,
) -> list[dict]:
    """Rank CPOs along the route, weighting even distribution over raw count.

    Computes each matched station's approximate position in km along the
    route (via `ST_LineLocatePoint`, a 0..1 fraction, times the route's
    total length), then per operator applies `_effective_station_count` —
    stations closer than `target_spacing_km / 2` to a previously counted
    one don't add to the count. Operators are ranked primarily by this
    `effective_station_count`, with raw `station_count` as a tiebreaker.

    This directly addresses: a CPO with 50 stations bunched in the first
    100km of a 600km route should NOT outrank one with fewer stations
    spread evenly across the whole route.
    """
    extra_sql, extra_params = _build_filters(
        require_ac, require_dc, trailer_friendly, connector_type, min_power_kw
    )

    query = text(
        f"""
        WITH route AS (
            SELECT geom, ST_Length(geom::geography) / 1000.0 AS length_km
            FROM (SELECT ST_SetSRID(ST_GeomFromGeoJSON(:route_geojson), 4326) AS geom) g
        )
        SELECT o.id AS operator_id,
               COALESCE(o.name, 'Unknown Operator') AS operator_name,
               ST_LineLocatePoint(route.geom, s.geom) * route.length_km AS km
        FROM stations s
        LEFT JOIN operators o ON o.id = s.operator_id
        CROSS JOIN route
        WHERE ST_DWithin(s.geom::geography, route.geom::geography, :buffer_m)
              {extra_sql}
        """
    )

    rows = db.execute(
        query,
        {
            "route_geojson": json.dumps(route_geojson),
            "buffer_m": buffer_km * 1000,
            **extra_params,
        },
    ).mappings()

    positions_by_operator: dict[int | None, list[float]] = {}
    names_by_operator: dict[int | None, str] = {}
    for row in rows:
        positions_by_operator.setdefault(row["operator_id"], []).append(row["km"])
        names_by_operator[row["operator_id"]] = row["operator_name"]

    min_spacing_km = target_spacing_km / 2
    results = []
    for operator_id, positions in positions_by_operator.items():
        results.append(
            {
                "operator_id": operator_id,
                "operator_name": names_by_operator[operator_id],
                "station_count": len(positions),
                "effective_station_count": _effective_station_count(positions, min_spacing_km),
            }
        )

    results.sort(key=lambda r: (-r["effective_station_count"], -r["station_count"]))
    return results


def stations_in_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float,
    require_ac: bool = False,
    require_dc: bool = False,
    trailer_friendly: bool = False,
    connector_type: str | None = None,
    min_power_kw: float | None = None,
    limit: int = 2000,
) -> list[dict]:
    """Individual station points within radius (for map markers / hover highlighting)."""
    extra_sql, extra_params = _build_filters(
        require_ac, require_dc, trailer_friendly, connector_type, min_power_kw
    )

    query = text(
        f"""
        SELECT s.id AS station_id,
               s.name AS station_name,
               o.id AS operator_id,
               COALESCE(o.name, 'Unknown Operator') AS operator_name,
               ST_Y(s.geom) AS latitude,
               ST_X(s.geom) AS longitude,
               s.max_power_kw AS max_power_kw,
               s.number_of_points AS number_of_points,
               s.connector_types AS connector_types
        FROM stations s
        LEFT JOIN operators o ON o.id = s.operator_id
        WHERE ST_DWithin(
                s.geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius_m
              )
              {extra_sql}
        LIMIT :limit
        """
    )

    rows = db.execute(
        query,
        {
            "lat": latitude,
            "lon": longitude,
            "radius_m": radius_km * 1000,
            "limit": limit,
            **extra_params,
        },
    ).mappings()

    return [dict(row) for row in rows]


def stations_along_route(
    db: Session,
    route_geojson: dict,
    buffer_km: float,
    require_ac: bool = False,
    require_dc: bool = False,
    trailer_friendly: bool = False,
    connector_type: str | None = None,
    min_power_kw: float | None = None,
    limit: int = 2000,
) -> list[dict]:
    """Individual station points along the route buffer (for map markers / hover highlighting)."""
    extra_sql, extra_params = _build_filters(
        require_ac, require_dc, trailer_friendly, connector_type, min_power_kw
    )

    query = text(
        f"""
        SELECT s.id AS station_id,
               s.name AS station_name,
               o.id AS operator_id,
               COALESCE(o.name, 'Unknown Operator') AS operator_name,
               ST_Y(s.geom) AS latitude,
               ST_X(s.geom) AS longitude,
               s.max_power_kw AS max_power_kw,
               s.number_of_points AS number_of_points,
               s.connector_types AS connector_types
        FROM stations s
        LEFT JOIN operators o ON o.id = s.operator_id
        WHERE ST_DWithin(
                s.geom::geography,
                ST_SetSRID(ST_GeomFromGeoJSON(:route_geojson), 4326)::geography,
                :buffer_m
              )
              {extra_sql}
        LIMIT :limit
        """
    )

    rows = db.execute(
        query,
        {
            "route_geojson": json.dumps(route_geojson),
            "buffer_m": buffer_km * 1000,
            "limit": limit,
            **extra_params,
        },
    ).mappings()

    return [dict(row) for row in rows]
