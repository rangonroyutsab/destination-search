# Architecture

## Overview

destination-search is composed of three runtime tiers that share no in-process state, each managed as a Docker Compose service:

```
Browser
  |
  |  HTTP (React SPA served by Django; /api/* proxied in dev by Vite)
  v
Django (DRF)  :8000
  |
  +-- PostgreSQL / PostGIS  :5432   <- canonical store, migrations, admin
  |
  +-- Elasticsearch 9       :9200   <- all search & geo queries
```

Postgres is the **system of record** (data survives ES re-indexing). Elasticsearch is the **query engine** — every read path hits ES, never Postgres directly (except the health check and admin).

---

## System Diagram

```
+---------------------------+
|   Browser                 |
|   React 19 + Leaflet      |
+---------------------------+
            |
      HTTP GET /api/v1/...
            |
            v
+------------------------------------------+
|   Django (DRF)  :8000                    |
|                                          |
|  +------------------+                   |
|  | Views            |                   |
|  | SearchView       |                   |
|  | AutocompleteView |                   |
|  | NearbyView       |                   |
|  | WithinBoundsView |                   |
|  | HealthCheckView  |                   |
|  +--------+---------+                   |
|           |                             |
|  +--------v---------+                   |
|  | Services         |                   |
|  | search_service   |                   |
|  | autocomplete_svc |                   |
|  | geo_service      |                   |
|  +--------+---------+                   |
|           |                             |
|  +--------v---------+                   |
|  | ES Layer         |                   |
|  | client.py        |                   |
|  | documents.py     |                   |
|  | queries.py       |                   |
|  +--------+---------+                   |
|           |              |              |
+-----------+--------------+--------------+
            |              |
     ES search/geo    SELECT 1
     queries          (health only)
            |              |
            v              v
  +-----------------+  +-------------------+
  | Elasticsearch 9 |  | PostgreSQL        |
  | :9200           |  | + PostGIS  :5432  |
  +-----------------+  +-------------------+
            ^                    ^
            |                    |
       bulk index           bulk insert
            |                    |
  +-----------------------------+
  |  seed_destinations          |
  |  (management command)       |
  |  reads worldcitiespop.csv   |
  +-----------------------------+
```

---

## Component Breakdown

### `core/`

The Django project package — wiring only, no business logic.

| File | Responsibility |
|---|---|
| `settings.py` | All configuration via environment variables; registers `apps.destinations`, `rest_framework`, `django.contrib.gis` |
| `urls.py` | Mounts `/api/v1/health/` and delegates `/api/v1/destinations/` to the app |
| `views.py` | `HealthCheckView` — pings Postgres (`SELECT 1`) and ES (`.ping()`) to report real dependency health |
| `utils/responses.py` | `success_response()` / `error_response()` — all endpoints share one envelope shape |
| `utils/exceptions.py` | DRF exception handler; maps `ServiceUnavailableError` → 503 and wraps DRF validation errors in the standard envelope |

**Response envelope (all endpoints):**

```json
// Success
{ "success": true,  "data": [...], "error": null, "meta": {...} }

// Failure
{ "success": false, "data": null, "error": { "code": "...", "message": "...", "details": {...} } }
```

---

### `apps/destinations/`

The single Django application. Organised into four clear layers.

#### Layer 1 — Models (`models.py`)

```python
class Destination(models.Model):
    city       = CharField
    country    = CharField
    population = IntegerField
    location   = PointField(geography=True, srid=4326)   # WGS-84
```

Two database indexes:
- `destination_location_gist` — GiST spatial index on `location`
- `destination_country_city_idx` — B-tree compound index on `(country, city)`

#### Layer 2 — Serializers (`serializers.py`)

Query-parameter validators only; no model serialisation. Four classes:

| Serializer | Params |
|---|---|
| `SearchQuerySerializer` | `q` (required), `country` (optional) |
| `AutocompleteQuerySerializer` | `q` (required) |
| `NearbyQuerySerializer` | `lat`, `lon`, `radius` (all required, range-validated) |
| `WithinBoundsQuerySerializer` | `north`, `south`, `east`, `west` (all required; validates `north > south`) |

#### Layer 3 — Views (`views.py`)

Four `APIView` subclasses. Each view follows the same three steps:
1. Validate query params via the serializer (`raise_exception=True` hands errors to the global handler)
2. Delegate to the appropriate service
3. Return `success_response(results, meta={...})`

Views contain no search logic — they are thin HTTP adapters.

#### Layer 4 — Services (`services/`)

Orchestrators between the view and the Elasticsearch layer.

| Module | Function | ES Query | Result shape |
|---|---|---|---|
| `search_service` | `search(q, country, size=20)` | `build_search_query` | `{city, country, population, location, score}` |
| `autocomplete_service` | `autocomplete(q)` | `build_autocomplete_query` | `{city, country, location}` |
| `geo_service` | `nearby(lat, lon, radius_km, size=50)` | `build_nearby_query` | `{city, country, population, location, distance_km}` |
| `geo_service` | `within_bounds(north, south, east, west, size=100)` | `build_within_bounds_query` | `{city, country, population, location}` |

All services catch `elasticsearch.ConnectionError` and `TransportError`, re-raising them as `ServiceUnavailableError` (→ 503).

---

### `apps/destinations/search/` — Elasticsearch Layer

#### `client.py`

Returns a lazily-created, module-level `Elasticsearch` singleton. The index name is read from `settings.ELASTICSEARCH_DSL` at call time.

#### `documents.py` — Index Definition

The index is named `destinations`. Key design decisions:

**Analyzers:**

| Analyzer | Used when | What it does |
|---|---|---|
| `autocomplete_index_analyzer` | Indexing `city` / `country` | standard tokeniser → lowercase → asciifolding → edge_ngram (2–20 chars) |
| `autocomplete_search_analyzer` | Searching `city` / `country` | standard tokeniser → lowercase → asciifolding (no ngram — avoids double-ngram expansion) |
| `standard_text_analyzer` | Subfields `city.standard` / `country.standard` | standard tokeniser → lowercase → asciifolding |

The split index/search analyzer is the core trick for prefix-matching: at index time each token is expanded into all its leading substrings (e.g. `"dha"` becomes `"dh"`, `"dha"`). At search time the raw query term is looked up against those pre-expanded tokens, so `"dha"` matches `"dhaka"` without fuzzy overhead.

**Mappings:**

| Field | Type | Notes |
|---|---|---|
| `city` | `text` | ngram index analyzer, standard search analyzer |
| `city.raw` | `keyword` | lowercased; exact-match boosting and sorting |
| `city.standard` | `text` | standard analyzer; used for fuzzy full-search |
| `country` | `text` | same structure as `city` |
| `country.raw` | `keyword` | lowercased; used for country filter |
| `country.standard` | `text` | standard analyzer |
| `population` | `integer` | secondary scoring factor |
| `location` | `geo_point` | WGS-84; used by geo_distance and geo_bounding_box filters |

#### `queries.py` — Query Builders

Four pure functions that return Elasticsearch query dicts. No I/O.

**`build_autocomplete_query(q, size=5)`**

`function_score` wrapping a `bool.should`:
1. `term` on `city.raw` — exact match, boost 20
2. `match` on `city` (ngram field) — prefix match, boost 8
3. `match` on `country` — country match, boost 2

Population `field_value_factor` (log1p, factor 0.1) added via `boost_mode: sum` so text relevance always dominates.

**`build_search_query(q, country=None, size=20)`**

`function_score` with a richer `bool.should`:
1. `term` on `city.raw` — exact, boost 25
2. `match` on `city` (ngram) — prefix, boost 10
3. `match` on `city.standard` with `fuzziness: AUTO` — typo tolerance, boost 4
4. `match` on `country.standard` — boost 3
5. `term` on `country.raw` — boost 3
6. `multi_match` cross-fields on `city.standard` + `country.standard` — handles "paris france" style queries, boost 15

Optional `country` param adds a `filter` clause (`term` on `country.raw`) to hard-filter results.

**`build_nearby_query(lat, lon, radius_km, size=50)`**

`bool.filter` with a single `geo_distance` clause. Sorted by `_geo_distance` ascending (nearest first). No relevance scoring — every in-range result is equally valid.

**`build_within_bounds_query(north, south, east, west, size=100)`**

`bool.filter` with a single `geo_bounding_box` clause. Sorted by `population` descending — the most prominent cities surface first when a large viewport returns many results.

---

### `frontend/`

A React 19 SPA built with Vite 8.

**State architecture (`App.jsx`):**
- `activeMode` — `'search' | 'nearby' | 'bounds'`
- `results` / `loading` / `error` / `hasSearched` — standard async state
- `nearbyCenter` / `nearbyRadius` — pin position + km radius for nearby mode
- `currentBounds` — map viewport coordinates for bounds mode
- `latestRequestId` ref — cancels stale responses when a new request is dispatched before the previous one resolves

**Key components:**

| Component | Purpose |
|---|---|
| `ModeTabs` | Switches between search / nearby / bounds modes |
| `SearchControls` | Text input + optional country filter; drives `handleSearch` |
| `NearbyControls` | Lat/lon inputs (or map click) + radius slider; drives `handleNearbySearch` |
| `BoundsControls` | Triggers `handleBoundsSearch` using the map's current viewport |
| `DestinationMap` | Leaflet map; renders pins, radius circle, handles clicks, reports viewport bounds |
| `DestinationList` / `DestinationCard` | Result list with hover/select highlighting synced to map pins |
| `AutocompleteDropdown` | Debounced autocomplete calling `/api/v1/destinations/autocomplete/` |
| `HealthIndicator` | Polls `/api/v1/health/` and shows dependency status |
| `DeveloperDetails` | Shows last request URL, HTTP status, and response time |

**API client (`api/destinations.js`):**

Five `fetch` wrappers (`getHealth`, `autocomplete`, `searchDestinations`, `searchNearby`, `searchWithinBounds`). Each wrapper records `performance.now()` timing and returns a uniform object:

```js
{ status, duration, data, error, url, method }
```

This object is stored as `developerRequestInfo` in App state and rendered by `DeveloperDetails`.

---

## Data Seeding

`apps/destinations/management/commands/seed_destinations.py` is a Django management command that:

1. Reads `worldcitiespop.csv` (country codes pre-converted to full names by `scripts/country_code_replace.py`)
2. Creates / updates `Destination` rows in Postgres (batch `bulk_create`)
3. Drops and recreates the `destinations` ES index (idempotent on re-runs)
4. Bulk-indexes all destinations into ES

Both stores are populated in a single command run.

---

## Infrastructure

### Docker Compose Services

| Service | Image | Purpose |
|---|---|---|
| `db` | `postgis/postgis:18-3.6` | PostgreSQL with PostGIS extension |
| `elasticsearch` | `elasticsearch:9.5.1` | Single-node ES cluster, security disabled |
| `web` | Project Dockerfile | Django app (dev: `runserver`, prod: `gunicorn`) |
| `seed` | Project Dockerfile | One-off data ingest (profile: `seed`) |

`web` and `seed` both declare `depends_on` with `condition: service_healthy`, so Docker Compose waits for the DB and ES health checks to pass before starting them.

### Dockerfile

Multi-stage build:

- **Stage 1 (`builder`)** — `python:3.14-slim` with build tools (`gcc`, `libgdal-dev`, `libgeos-dev`, `libproj-dev`). Installs all Python deps into `/install`.
- **Stage 2 (`runtime`)** — `python:3.14-slim` with runtime-only shared libs (`gdal-bin`, `libgeos-c1v5`, `libproj25`). Copies `/install` from builder. Drops to unprivileged `appuser`. Exposes port `8000`.

Production command: `gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 60`.
