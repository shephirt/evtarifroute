"""Pydantic request/response schemas for the analysis & tariff API."""
from pydantic import BaseModel, Field, model_validator


class LatLon(BaseModel):
    latitude: float
    longitude: float


class AddressSuggestion(BaseModel):
    label: str
    latitude: float
    longitude: float


class AddressSuggestResponse(BaseModel):
    suggestions: list[AddressSuggestion]


class OperatorRanking(BaseModel):
    operator_id: int | None
    operator_name: str
    station_count: int
    # Only populated for route analysis (Mode A): the number of stations
    # remaining after filtering out ones that are "too close" to a
    # previously counted one (closer than target_spacing_km / 2) — see
    # rank_operators_along_route(). Reflects how well spread-out the
    # operator's stations are along the route, not just raw count.
    effective_station_count: int | None = None


class StationPoint(BaseModel):
    station_id: int
    station_name: str | None
    operator_id: int | None
    operator_name: str
    latitude: float
    longitude: float
    max_power_kw: float | None = None
    number_of_points: int | None = None
    connector_types: list[str] = Field(default_factory=list)


# --- Mode B: Local Radius CPO Dominance Analysis (SRS 2.2) ---


class RadiusAnalysisRequest(BaseModel):
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float = Field(default=3.0, gt=0, le=50)

    require_ac: bool = False
    require_dc: bool = False
    trailer_friendly: bool = False
    connector_type: str | None = None
    min_power_kw: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_location_provided(self):
        has_coords = self.latitude is not None and self.longitude is not None
        if not self.address and not has_coords:
            raise ValueError("Provide either 'address' or both 'latitude' and 'longitude'")
        return self


class RadiusAnalysisResponse(BaseModel):
    location: LatLon
    radius_km: float
    total_stations: int
    rankings: list[OperatorRanking]
    stations: list[StationPoint]


# --- Mode A: Route-Based CPO Dominance Analysis (SRS 2.1) ---


class RouteAnalysisRequest(BaseModel):
    start_address: str | None = None
    start: LatLon | None = None
    destination_address: str | None = None
    destination: LatLon | None = None

    buffer_km: float = Field(default=2.0, gt=0, le=20)
    trailer_friendly: bool = False
    connector_type: str | None = None
    min_power_kw: float | None = Field(default=None, ge=0)
    # "I want a charger at least every X km" — used to score how evenly an
    # operator's stations are spread along the route (see
    # rank_operators_along_route). Stations closer than half this distance
    # to a previously counted one don't count as an additional data point.
    target_spacing_km: float = Field(default=100.0, gt=0, le=500)

    @model_validator(mode="after")
    def check_endpoints_provided(self):
        if not self.start_address and not self.start:
            raise ValueError("Provide either 'start_address' or 'start' coordinates")
        if not self.destination_address and not self.destination:
            raise ValueError(
                "Provide either 'destination_address' or 'destination' coordinates"
            )
        return self


class RouteAnalysisResponse(BaseModel):
    total_stations: int
    rankings: list[OperatorRanking]
    stations: list[StationPoint]
    route_geojson: dict


# --- Tariff & MSP Recommendation Engine (SRS 2.3) ---


class TariffRecommendationRequest(BaseModel):
    rankings: list[OperatorRanking]
    monthly_kwh_estimate: float = Field(default=100.0, gt=0)
    prefer_dc: bool = True


class TariffRecommendation(BaseModel):
    tariff_id: int
    name: str
    provider: str
    estimated_monthly_cost: float
    coverage_ratio: float
    covered_station_count: int
    covered_operator_ids: list[int] = Field(default_factory=list)
    notes: str | None = None


class TariffRecommendationResponse(BaseModel):
    recommendations: list[TariffRecommendation]
