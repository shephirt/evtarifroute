"""Analysis & tariff recommendation endpoints (SRS 2.1, 2.2, 2.3)."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.schemas import (
    AddressSuggestResponse,
    LatLon,
    OperatorRanking,
    RadiusAnalysisRequest,
    RadiusAnalysisResponse,
    RouteAnalysisRequest,
    RouteAnalysisResponse,
    StationPoint,
    TariffRecommendationRequest,
    TariffRecommendationResponse,
)
from app.database import get_db
from app.services import ors_client
from app.services.ors_client import OrsError
from app.services.spatial import (
    rank_operators_along_route,
    rank_operators_in_radius,
    stations_along_route,
    stations_in_radius,
)
from app.services.tariff_engine import recommend_tariffs
from app.tariffs.seed import seed_tariffs

logger = logging.getLogger("app.api")

router = APIRouter(prefix="/api")


@router.get("/geocode/suggest", response_model=AddressSuggestResponse)
async def geocode_suggest(q: str):
    """Address autocomplete suggestions, proxied through the backend so the
    ORS API key never reaches the frontend."""
    try:
        suggestions = await run_in_threadpool(ors_client.autocomplete, q)
    except OrsError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return AddressSuggestResponse(suggestions=suggestions)


@router.post("/radius-analysis", response_model=RadiusAnalysisResponse)
async def radius_analysis(req: RadiusAnalysisRequest, db: Session = Depends(get_db)):
    """Mode B: Local Radius CPO Dominance Analysis (SRS 2.2)."""
    if req.latitude is not None and req.longitude is not None:
        lat, lon = req.latitude, req.longitude
    else:
        try:
            lon, lat = await run_in_threadpool(ors_client.geocode, req.address)
        except OrsError as e:
            raise HTTPException(status_code=422, detail=str(e))

    rows = await run_in_threadpool(
        rank_operators_in_radius,
        db,
        lat,
        lon,
        req.radius_km,
        require_ac=req.require_ac,
        require_dc=req.require_dc,
        trailer_friendly=req.trailer_friendly,
        connector_type=req.connector_type,
        min_power_kw=req.min_power_kw,
    )
    station_rows = await run_in_threadpool(
        stations_in_radius,
        db,
        lat,
        lon,
        req.radius_km,
        require_ac=req.require_ac,
        require_dc=req.require_dc,
        trailer_friendly=req.trailer_friendly,
        connector_type=req.connector_type,
        min_power_kw=req.min_power_kw,
    )

    total = sum(r["station_count"] for r in rows)
    return RadiusAnalysisResponse(
        location=LatLon(latitude=lat, longitude=lon),
        radius_km=req.radius_km,
        total_stations=total,
        rankings=[OperatorRanking(**r) for r in rows],
        stations=[StationPoint(**s) for s in station_rows],
    )


@router.post("/route-analysis", response_model=RouteAnalysisResponse)
async def route_analysis(req: RouteAnalysisRequest, db: Session = Depends(get_db)):
    """Mode A: Route-Based CPO Dominance Analysis (SRS 2.1)."""
    try:
        if req.start is not None:
            start_lonlat = (req.start.longitude, req.start.latitude)
        else:
            start_lonlat = await run_in_threadpool(ors_client.geocode, req.start_address)

        if req.destination is not None:
            end_lonlat = (req.destination.longitude, req.destination.latitude)
        else:
            end_lonlat = await run_in_threadpool(ors_client.geocode, req.destination_address)

        route_geometry = await run_in_threadpool(
            ors_client.get_route_geometry, start_lonlat, end_lonlat
        )
    except OrsError as e:
        raise HTTPException(status_code=422, detail=str(e))

    rows = await run_in_threadpool(
        rank_operators_along_route,
        db,
        route_geometry,
        req.buffer_km,
        trailer_friendly=req.trailer_friendly,
        connector_type=req.connector_type,
        min_power_kw=req.min_power_kw,
        target_spacing_km=req.target_spacing_km,
    )
    station_rows = await run_in_threadpool(
        stations_along_route,
        db,
        route_geometry,
        req.buffer_km,
        trailer_friendly=req.trailer_friendly,
        connector_type=req.connector_type,
        min_power_kw=req.min_power_kw,
    )

    total = sum(r["station_count"] for r in rows)
    return RouteAnalysisResponse(
        total_stations=total,
        rankings=[OperatorRanking(**r) for r in rows],
        stations=[StationPoint(**s) for s in station_rows],
        route_geojson=route_geometry,
    )


@router.post("/tariff-recommendation", response_model=TariffRecommendationResponse)
async def tariff_recommendation(
    req: TariffRecommendationRequest, db: Session = Depends(get_db)
):
    """Maps ranked CPOs (from radius/route analysis) to MSP tariffs (SRS 2.3)."""
    rankings = [r.model_dump() for r in req.rankings]
    results = await run_in_threadpool(
        recommend_tariffs, db, rankings, req.monthly_kwh_estimate, req.prefer_dc
    )
    return TariffRecommendationResponse(recommendations=results)


@router.post("/tariffs/seed")
async def trigger_tariff_seed(db: Session = Depends(get_db)):
    """Manually (re-)seed the curated msp_tariffs table (Phase 4).

    Resolves each seed entry's covered_operator_names against whatever
    operators have actually been ingested (run /api/etl/run first). Safe to
    re-run — upserts by tariff name.
    """
    result = await run_in_threadpool(seed_tariffs, db)
    return result
