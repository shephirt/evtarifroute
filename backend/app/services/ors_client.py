"""Thin HTTP client for OpenRouteService (ORS): geocoding + directions.

Docs: https://openrouteservice.org/dev/#/api-docs

Used exclusively to:
  - geocode a free-text address into coordinates (geocode/search)
  - generate the route LineString geometry between two points (directions)
No battery/consumption simulation or dynamic waypointing — see SRS 3.2.
"""
import logging
import os

import httpx

logger = logging.getLogger("app.services.ors_client")

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
ORS_AUTOCOMPLETE_URL = "https://api.openrouteservice.org/geocode/autocomplete"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


class OrsError(Exception):
    """Raised when ORS cannot fulfil a request (geocode miss, routing failure,
    quota/auth errors, network issues, etc.) — the single exception type API
    routes need to catch to turn any ORS failure into a clean HTTP error
    response instead of an unhandled 500."""


def _api_key() -> str:
    api_key = os.environ.get("ORS_API_KEY")
    if not api_key:
        raise OrsError("ORS_API_KEY is not configured")
    return api_key


def _request(client: httpx.Client, method: str, url: str, **kwargs) -> dict:
    """Perform an HTTP request against ORS, translating any failure (HTTP
    error status, timeout, connection error, invalid JSON) into OrsError so
    callers only ever need to catch one exception type."""
    try:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:200] if e.response is not None else str(e)
        if e.response is not None and e.response.status_code == 429:
            raise OrsError(
                "OpenRouteService rate limit exceeded — please try again shortly."
            ) from e
        if e.response is not None and e.response.status_code == 403:
            raise OrsError(
                "OpenRouteService rejected the request (403) — the API key's "
                "quota may be exhausted or the key is invalid. "
                f"Response: {detail}"
            ) from e
        raise OrsError(
            f"OpenRouteService request failed ({e.response.status_code if e.response is not None else '?'}): {detail}"
        ) from e
    except httpx.RequestError as e:
        raise OrsError(f"Could not reach OpenRouteService: {e}") from e


def geocode(address: str, timeout: float = 15.0) -> tuple[float, float]:
    """Geocode a free-text address. Returns (longitude, latitude)."""
    params = {"api_key": _api_key(), "text": address, "size": 1}
    with httpx.Client(timeout=timeout) as client:
        data = _request(client, "GET", ORS_GEOCODE_URL, params=params)

    features = data.get("features") or []
    if not features:
        raise OrsError(f"No geocoding result found for address: {address!r}")

    lon, lat = features[0]["geometry"]["coordinates"]
    return lon, lat


def autocomplete(text: str, size: int = 5, timeout: float = 10.0) -> list[dict]:
    """Address autocomplete suggestions. Returns a list of
    {"label": str, "latitude": float, "longitude": float}."""
    if not text or len(text) < 2:
        return []

    params = {"api_key": _api_key(), "text": text, "size": size}
    with httpx.Client(timeout=timeout) as client:
        data = _request(client, "GET", ORS_AUTOCOMPLETE_URL, params=params)

    suggestions = []
    for feature in data.get("features") or []:
        lon, lat = feature["geometry"]["coordinates"]
        label = feature.get("properties", {}).get("label")
        if label:
            suggestions.append({"label": label, "latitude": lat, "longitude": lon})
    return suggestions


def get_route_geometry(
    start_lonlat: tuple[float, float],
    end_lonlat: tuple[float, float],
    timeout: float = 30.0,
) -> dict:
    """Fetch the route LineString GeoJSON geometry between two points."""
    headers = {
        "Authorization": _api_key(),
        "Content-Type": "application/json",
    }
    body = {"coordinates": [list(start_lonlat), list(end_lonlat)]}

    with httpx.Client(timeout=timeout) as client:
        data = _request(client, "POST", ORS_DIRECTIONS_URL, headers=headers, json=body)

    features = data.get("features") or []
    if not features:
        raise OrsError("ORS returned no route for the given coordinates")

    return features[0]["geometry"]
