"""Transform raw OpenChargeMap POI JSON into rows for our schema.

OCM POI shape (relevant fields, compact=false):
    {
      "ID": 12345,
      "AddressInfo": {"Title": "...", "Latitude": 52.5, "Longitude": 13.4},
      "OperatorID": 3,
      "OperatorInfo": {"ID": 3, "Title": "EnBW", "WebsiteURL": "https://..."},
      "UsageType": {"ID": 1, "Title": "Public"},
      "GeneralComments": "...",
      "Connections": [
        {
          "PowerKW": 150.0,
          "Level": {"ID": 3, "Title": "Level 3 : Rapid AC/DC", "IsFastChargeCapable": true},
          "ConnectionType": {"Title": "Type 2 (Socket Only)"}
        }
      ]
    }

DC fast-charging vs AC is derived from the connection's Level.ID, following
OCM's convention: Level 1/2 = slow/fast AC, Level 3 = rapid DC.

Trailer/caravan/HGV accessibility (SRS 2.4) is NOT a structured field in the
OCM schema — as a best-effort heuristic we scan GeneralComments for relevant
keywords. This is inherently approximate; consider a manually curated
override list if data quality here matters for launch.

Note: verified against the real dataset (DACH + NL, 35k+ stations) that
GeneralComments is frequently populated but predominantly in German/Dutch
(e.g. "Öffentlich 320-kW-HPC-Ladestation..."), not English — an English-only
keyword match against real data returned **zero** matches across the entire
dataset. Keywords below include German/Dutch equivalents to reduce (not
eliminate) this gap.
"""
import re
from typing import Any, TypedDict

_CARAVAN_KEYWORDS = re.compile(r"caravan|wohnwagen|wohnmobil", re.IGNORECASE)
_TRAILER_KEYWORDS = re.compile(r"trailer|anh[aä]nger|aanhangwagen", re.IGNORECASE)
_HGV_KEYWORDS = re.compile(r"\bhgv\b|heavy goods|\blkw\b|schwerlastverkehr|vrachtwagen", re.IGNORECASE)
_DRIVE_THROUGH_KEYWORDS = re.compile(r"drive[\s-]?through|durchfahrt|doorrijden", re.IGNORECASE)

DC_LEVEL_IDS = {3}
AC_LEVEL_IDS = {1, 2}


class OperatorRow(TypedDict):
    ocm_operator_id: int
    name: str
    website: str | None


class StationRow(TypedDict):
    ocm_id: int
    ocm_operator_id: int | None
    name: str | None
    longitude: float
    latitude: float
    max_power_kw: float | None
    usage_type: str | None
    connector_types: list[str]
    number_of_points: int | None
    is_ac: bool
    is_dc: bool
    drive_through: bool
    caravan_friendly: bool
    trailer_friendly: bool
    hgv_friendly: bool


def extract_operator(poi: dict[str, Any]) -> OperatorRow | None:
    operator_info = poi.get("OperatorInfo")
    if not operator_info or not operator_info.get("ID"):
        return None
    return OperatorRow(
        ocm_operator_id=operator_info["ID"],
        name=operator_info.get("Title") or f"Operator {operator_info['ID']}",
        website=operator_info.get("WebsiteURL"),
    )


def extract_station(poi: dict[str, Any]) -> StationRow | None:
    address = poi.get("AddressInfo") or {}
    lat = address.get("Latitude")
    lon = address.get("Longitude")
    if lat is None or lon is None:
        return None

    connections = poi.get("Connections") or []
    power_values = [c["PowerKW"] for c in connections if c.get("PowerKW")]
    max_power_kw = max(power_values) if power_values else None

    level_ids = {
        c["Level"]["ID"]
        for c in connections
        if c.get("Level") and c["Level"].get("ID") is not None
    }
    is_dc = bool(level_ids & DC_LEVEL_IDS)
    is_ac = bool(level_ids & AC_LEVEL_IDS) or not is_dc

    connector_types = sorted(
        {
            c["ConnectionType"]["Title"]
            for c in connections
            if c.get("ConnectionType") and c["ConnectionType"].get("Title")
        }
    )

    comments = poi.get("GeneralComments") or ""
    operator_info = poi.get("OperatorInfo") or {}

    return StationRow(
        ocm_id=poi["ID"],
        ocm_operator_id=operator_info.get("ID"),
        name=address.get("Title"),
        longitude=lon,
        latitude=lat,
        max_power_kw=max_power_kw,
        usage_type=(poi.get("UsageType") or {}).get("Title"),
        connector_types=connector_types,
        number_of_points=poi.get("NumberOfPoints"),
        is_ac=is_ac,
        is_dc=is_dc,
        drive_through=bool(_DRIVE_THROUGH_KEYWORDS.search(comments)),
        caravan_friendly=bool(_CARAVAN_KEYWORDS.search(comments)),
        trailer_friendly=bool(_TRAILER_KEYWORDS.search(comments)),
        hgv_friendly=bool(_HGV_KEYWORDS.search(comments)),
    )
