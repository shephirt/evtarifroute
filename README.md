# EVTarifRoute

A web-based analytical tool that recommends the most cost-effective EV charging subscription (Mobility Service Provider) based on real-world charging infrastructure density — either along a route or within a local radius.

## Stack

- **Database:** PostgreSQL + PostGIS
- **Backend:** Python (FastAPI), serving both the API and the built frontend from a single process
- **Frontend:** Vue 3 + Leaflet
- **Data sources:** [OpenChargeMap](https://openchargemap.org/) (charging station data) and [OpenRouteService](https://openrouteservice.org/) (geocoding + routing)
- **Deployment:** Docker Compose — `compose.yaml` (production: pre-built image) by default, `compose.dev.yaml` for local development (builds from source). No reverse proxy is bundled — put your own in front (Caddy, nginx, Traefik, ...).

## Local Development

Builds the app from source, exposes it directly on :8000, no reverse proxy.

```bash
cp .env.example .env
# Fill in OCM_API_KEY and ORS_API_KEY (both have free tiers)

docker compose -f compose.dev.yaml up -d --build
```

The app is available at **http://localhost:8000**. On first boot, it automatically fetches charging station data and seeds tariff data in the background (takes ~20-30s) — no manual steps needed.

To manually re-trigger data ingestion or tariff seeding:

```bash
curl -X POST http://localhost:8000/api/etl/run
curl -X POST http://localhost:8000/api/tariffs/seed
```

Stop with `docker compose -f compose.dev.yaml down` (add `-v` to also wipe the database volume).

### Frontend-only development

```bash
cd frontend
npm install
npm run dev
```

Vite's dev server proxies `/api/*` to `http://localhost:8000` (see `vite.config.js`), so run the backend via Docker Compose in parallel.

## Production Deployment

`compose.yaml` is the default compose file and is production-oriented: it uses the pre-built image published by CI (see below) instead of building from source. Fully standalone — you only need `compose.yaml` and `.env` on the server (not the full source tree).

```bash
cp .env.example .env
# Fill in DB credentials, OCM_API_KEY, ORS_API_KEY, and optionally IMAGE_TAG
# (defaults to "latest"; pin to a specific version like "0.1.0" for
# reproducible deployments)

docker compose up -d
```

The app is published on `:8000`. There is intentionally no reverse proxy / TLS termination bundled — put your own in front (Caddy, nginx, Traefik, or whatever you already run) pointing at that port.

## CI/CD

`.github/workflows/docker-image.yml` builds the multi-stage Docker image (Vue frontend + FastAPI backend) and publishes it to GitHub Container Registry (`ghcr.io/shephirt/evtarifroute`) on every push to `main` and on version tags (`v*.*.*`). Pull requests build (but don't push) the image to validate it compiles.

The package is public, so `docker compose up -d` can pull it without any registry login.

## Known Limitations

- The trailer/caravan/HGV accessibility filter relies on a best-effort keyword heuristic over free-text OCM data, which has very weak real-world signal.
- The curated MSP tariff data (`backend/app/tariffs/seed_data.py`) is illustrative, not scraped/verified against live provider pricing — review before relying on it for real decisions.
- No automated test suite yet.
