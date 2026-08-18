# destination-search

A full-stack city and destination search engine with text search, autocomplete, geo-radius, and map bounding-box modes. Powered by **Django + Elasticsearch** on the backend and a **React + Leaflet** SPA on the frontend.

---

## Table of Contents

- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Frontend Development](#frontend-development)
- [Running Tests](#running-tests)
- [Load Testing](#load-testing)
- [Further Reading](#further-reading)

---

## Key Features

- **Text search** — exact, prefix, fuzzy, and cross-field queries (e.g. `"paris france"`) powered by Elasticsearch. Typo tolerance via `fuzziness: AUTO`.
- **Autocomplete** — edge-ngram prefix matching optimised for sub-100 ms response. Returns the top 5 matching cities as you type.
- **Nearby search** — geo-radius query around a lat/lon point. Results sorted nearest-first; click anywhere on the map to set the centre.
- **Within bounds** — bounding-box query that mirrors the current map viewport. Results sorted by population so the most prominent cities appear first.
- **Interactive map** — React-Leaflet map with pin markers, radius circle overlay, and live sync between the results list and the map (hover/select highlighting).
- **Population-aware ranking** — population is applied as a log-dampened secondary boost so that larger cities rank higher when text relevance is equal.
- **Standard response envelope** — every endpoint returns `{ success, data, error, meta }` making error handling uniform across all callers.
- **Real health checks** — `/api/v1/health/` actively pings both Postgres and Elasticsearch, not just the Django process.
- **Developer panel** — the frontend exposes the last request URL, HTTP status, and response time for easy debugging.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 6 + Django REST Framework |
| Search engine | Elasticsearch 9 |
| Geospatial database | PostgreSQL 18 + PostGIS 3.6 |
| Frontend | React 19 + Vite 8 |
| Map | React-Leaflet + Leaflet 1.9 |
| Containerisation | Docker Compose |
| Python runtime | Python 3.14 |
| Node runtime | Node 20+ |

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- Git

### 1. Clone and configure

```bash
git clone https://github.com/rangonroyutsab/destination-search.git
cd destination-search
cp .env.example .env
```

### 2. Start the stack

```bash
docker compose up -d
```
- for macos:
```bash
docker compose -f compose.yaml -f compose.mac.yaml up -d --build  
```

This starts three services: `db` (PostGIS), `elasticsearch`, and `web` (Django). Both `db` and `elasticsearch` have health checks — `web` will not start until they pass.

### 3. Run database migrations

```bash
docker compose exec web python manage.py migrate
```

### 4. Seed destination data

```bash
docker compose --profile seed run --rm seed
```
or
```bash
docker compose exec web python manage.py seed_destinations data/worldcitiespop.csv  
```

This ingests `data/worldcitiespop.csv` into both PostgreSQL and Elasticsearch. May take a few minutes depending on dataset size.

### 5. Open the app

| Service | URL |
|---|---|
| Web app | http://localhost:8000 |
| Elasticsearch | http://localhost:9200 |
| API health | http://localhost:8000/api/v1/health/ |

---

## Environment Variables

All variables are read from `.env` (copied from `.env.example`). Docker Compose also accepts them directly from the host environment.

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `1` | Set to `0` in production |
| `SECRET_KEY` | `dev-secret-key-change-me` | Django secret key — **change in production** |
| `DJANGO_SETTINGS_MODULE` | `core.settings` | Django settings module path |
| `POSTGRES_DB` | `destination_search` | PostgreSQL database name |
| `POSTGRES_USER` | `destsearch` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `destsearch` | PostgreSQL password |
| `POSTGRES_PORT` | `5432` | Host-side port for PostgreSQL |
| `ES_PORT` | `9200` | Host-side port for Elasticsearch |
| `WEB_PORT` | `8000` | Host-side port for Django |
| `SEARCH_DEFAULT_SIZE` | `24` | Max results for text search queries |
| `NEARBY_DEFAULT_SIZE` | `48` | Max results for geo-radius nearby search |
| `BOUNDS_DEFAULT_SIZE` | `48` | Max results for map bounding-box search |
| `AUTOCOMPLETE_DEFAULT_SIZE` | `5` | Max suggestions returned for autocomplete |

---

## Project Structure

```
destination-search/
├── apps/
│   └── destinations/
│       ├── management/commands/
│       │   └── seed_destinations.py    # CSV -> Postgres + ES ingest
│       ├── search/
│       │   ├── client.py               # ES singleton client
│       │   ├── documents.py            # Index definition & analyzers
│       │   └── queries.py              # Query builders
│       ├── services/
│       │   ├── autocomplete_service.py
│       │   ├── geo_service.py
│       │   └── search_service.py
│       ├── tests/
│       ├── models.py
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
├── core/
│   ├── utils/
│   │   ├── exceptions.py               # Custom exception handler
│   │   └── responses.py                # Standard response envelope
│   ├── settings.py
│   ├── urls.py
│   └── views.py                        # HealthCheckView
├── frontend/src/
│   ├── api/destinations.js
│   ├── components/
│   └── App.jsx
├── data/                               # worldcitiespop.csv
├── scripts/
│   └── country_code_replace.py         # ISO code -> country name converter
├── docs/
│   ├── README.md
│   ├── api.md
│   └── architecture.md
├── compose.yaml
├── Dockerfile
├── locustfile.py
├── requirements.txt
└── .env.example
```

---

## Frontend Development

The frontend is a Vite-powered React SPA. For live development with hot-module replacement:

```bash
cd frontend
npm install
npm run dev      
```

The Django backend must be running (via Docker) on port `8000` for API calls to work.

```bash
npm run lint      
```

---

## Running Tests

The backend runs inside Docker. All `pytest` commands are executed via `docker compose exec`:

```bash
# All tests
docker compose exec web pytest

# With coverage report
docker compose exec web pytest --cov=apps --cov=core --cov-report=term-missing

# A specific test module
docker compose exec web pytest apps/destinations/tests/test_views.py

# Unit tests only (fast, no live ES required)
docker compose exec web pytest -m "not integration"

# Integration / search accuracy tests (requires seeded ES)
docker compose exec web pytest -m integration
```

Configuration: `pytest.ini` and `.coveragerc`.

---

## Load Testing

Locust runs **outside** Docker, pointing at the containerised backend:

```bash
# Install locust locally (already in requirements.txt)
pip install locust

# Open the Locust web UI at http://localhost:8089
locust -f locustfile.py --host=http://localhost:8000

# Headless: 10 users, spawn 2/s, run for 60 s
locust -f locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
```

---

## Further Reading

- [API Reference](docs/api.md) — endpoint documentation, query parameters, response schemas
- [Architecture](docs/architecture.md) — system design, data flow, Elasticsearch index design
