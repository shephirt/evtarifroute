import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.routes import router as api_router
from app.bootstrap import bootstrap_data
from app.etl.ocm_fetch import run_etl
from app.etl.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    # Fire-and-forget: don't block startup/healthcheck on the initial data
    # load, which can take ~20s. Only actually does work if tables are empty.
    import asyncio

    asyncio.create_task(run_in_threadpool(bootstrap_data))
    yield
    stop_scheduler()


app = FastAPI(title="EVTarifRoute API", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/etl/run")
async def trigger_etl():
    """Manually trigger one OCM ingestion pass on demand (no separate container)."""
    result = await run_in_threadpool(run_etl)
    return result


app.include_router(api_router)


# Serve the built frontend (Vue) static assets, if present.
# In the combined "app" container image, the frontend is built at image-build
# time and copied into this directory. Locally (without a build step) this
# directory may not exist, in which case only the API routes are available.
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        # SPA fallback: always serve index.html for non-API routes so
        # client-side routing works on refresh/deep links.
        return FileResponse(STATIC_DIR / "index.html")
