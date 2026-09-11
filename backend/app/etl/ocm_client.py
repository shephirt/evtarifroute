"""Thin HTTP client for the OpenChargeMap (OCM) POI API.

Docs: https://openchargemap.org/site/develop/api
Endpoint used: GET /v3/poi/

Note on pagination: OCM's `offset` query parameter does NOT work as
documented — verified empirically that requests with different `offset`
values return identical results (always the first page). The correct
approach is simply requesting a sufficiently large `maxresults` in a single
call; OCM does honor large values (verified up to 100,000 for a single
country with no truncation). DEFAULT_MAX_RESULTS is set generously above
today's real per-country totals (e.g. Germany ~24.6k stations as of writing)
to avoid silently truncating results as the dataset grows.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger("app.etl.ocm_client")

OCM_BASE_URL = "https://api.openchargemap.io/v3/poi/"

# Generous per-country result cap. Verified OCM honors values well above
# any single country's current station count (no observed hard server cap
# up to 100,000). Revisit if a target region's real count approaches this.
DEFAULT_MAX_RESULTS = 100_000


def fetch_pois_for_region(
    country_code: str,
    api_key: str | None,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: float = 120.0,
) -> list[dict[str, Any]]:
    """Fetch all POIs (charging stations) for a given ISO country code."""
    params = {
        "countrycode": country_code,
        "maxresults": max_results,
        "compact": "false",  # we need OperatorInfo/Connections detail
        "includecomments": "false",
    }
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    with httpx.Client(timeout=timeout) as client:
        response = client.get(OCM_BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, list):
        logger.warning(
            "[ETL] Unexpected OCM response shape for %s: %s", country_code, type(data)
        )
        return []

    if len(data) >= max_results:
        logger.warning(
            "[ETL] Region %s returned %d POIs, at or above max_results=%d — "
            "result set may be truncated, consider raising max_results",
            country_code,
            len(data),
            max_results,
        )

    logger.info("[ETL] Fetched %d POIs for region %s", len(data), country_code)
    return data
