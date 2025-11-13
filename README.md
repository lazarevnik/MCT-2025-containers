# Docker environments and monitoring

This repository provides two Docker Compose environments (development and production)
and a monitoring stack (Prometheus + Grafana) that can be run together with the
production services. This document explains what is included, how to run each
environment, how to access metrics and dashboards, and what files to look at.

## Contents added for monitoring

- `prometheus/prometheus.yml` - Prometheus scrape configuration. Prometheus will
 scrape the web service metrics at `/metrics`.
- `grafana/provisioning/` - Grafana provisioning for datasources and dashboards.
 A sample dashboard `fastapi-dashboard.json` is provided.

## Environments

The repo supports two compose configurations:

- Production: `docker-compose.yml` — full stack with PostgreSQL, Redis, `db-init`,
 the `web` service, and monitoring (`prometheus`, `grafana`).
- Development: `docker-compose.dev.yml` — lightweight, runs only the `web`
 service with `DEV_MODE=true` (the `/visits` endpoint returns `-1` and the
 app doesn't require DB/Redis).

### Production (full stack)

Start the full stack (includes monitoring):

```powershell
docker compose -f docker-compose.yml up -d --build
```

Useful commands:

```powershell
docker compose ps
docker compose logs -f web
docker compose down
```

Endpoints:

- Web app: <http://localhost:8000>
  - `/health` — health check
  - `/ping` — records a visit (writes to DB) and returns `pong`
  - `/visits` — returns the visit count (from cache/DB)
  - `/metrics` — Prometheus metrics exposed by the app
- Prometheus UI: <http://localhost:9090>
- Grafana UI: <http://localhost:3000> (default credentials: admin/admin)

### Development (fast local authoring)

Start dev environment (only web, DEV_MODE=true):

```powershell
docker compose -f docker-compose.dev.yml up -d --build
```

Behavior differences in dev mode:

- `/visits` always returns `{"visits": -1}`
- `/ping` returns `pong` but does not persist to the database
- No Redis or PostgreSQL required

## Monitoring (Prometheus + Grafana)

What was added:

- Prometheus service (`prom/prometheus`) configured to scrape the `web` service
 metrics endpoint at `/metrics` (see `prometheus/prometheus.yml`).
- Grafana service with a provisioning folder to auto-add Prometheus as a
 datasource and a preconfigured dashboard (`grafana/provisioning`).

How to access:

- Prometheus UI: <http://localhost:9090>
- Grafana UI: <http://localhost:3000>
  - Default login: admin / admin (see `docker-compose.yml` env for grafana)

Quick checks:

```powershell
# App metrics endpoint (should show Prometheus text format)
curl http://localhost:8000/metrics

# Prometheus health endpoint
curl http://localhost:9090/-/healthy

# Grafana health
curl http://localhost:3000/api/health
```

## CI notes (GitHub Actions)

The repository workflow `.github/workflows/test.yml` is configured to:

- Run unit tests with coverage (coverage threshold is enforced).
- Start the production compose stack (`docker compose -f docker-compose.yml up -d`).
- Verify services are healthy (Postgres, Redis, db-init exit code).
- Verify monitoring is up:
  - Prometheus reachable on port 9090 and scraping the app metrics
  - Grafana reachable on port 3000
- Run a few integration requests to ensure `/ping` and `/visits` behave as
  expected, then tear down the stack.

When running the CI locally (or debugging), you can emulate the workflow steps
manually in this order to reproduce the checks.

## Files of interest (quick map)

Below is a compact tree view of the repository files relevant to running
environments and monitoring. Each line includes a short purpose comment.

```powershell
.
├─ docker-compose.yml # Production compose
├─ docker-compose.dev.yml # Development compose (web only, DEV_MODE=true)
├─ README.md # This README
├─ prometheus/
│  └─ prometheus.yml # Prometheus scrape configuration
├─ grafana/
│  └─ provisioning/
│     ├─ datasources/
│     │  └─ prometheus.yml # Grafana datasource provisioning
│     └─ dashboards/
│        └─ fastapi-dashboard.json # Example Grafana dashboard
└─ app/
  ├─ main.py # FastAPI application
  ├─ init_db.py # DB initialization script run by `db-init`
  └─ test_main.py # Unit tests (pytest)

```
