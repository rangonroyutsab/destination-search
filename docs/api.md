# API Reference

Base URL (local dev): `http://localhost:8000`  
All endpoints are prefixed with `/api/v1/`.

---

## Table of Contents

- [Response Envelope](#response-envelope)
- [Error Codes](#error-codes)
- [GET /api/v1/health/](#get-apiv1health)
- [GET /api/v1/destinations/search/](#get-apiv1destinationssearch)
- [GET /api/v1/destinations/autocomplete/](#get-apiv1destinationsautocomplete)
- [GET /api/v1/destinations/nearby/](#get-apiv1destinationsnearby)
- [GET /api/v1/destinations/within-bounds/](#get-apiv1destinationswithin-bounds)
- [Notes](#notes)

---

## Response Envelope

Every endpoint — success or failure — returns the same top-level shape:

**Success (`2xx`)**

```json
{
  "success": true,
  "data": [ ... ],
  "error": null,
  "meta": { "query": "paris", "count": 3 }
}
```

**Failure (`4xx` / `5xx`)**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "bad_request",
    "message": "Human-readable description.",
    "details": { "q": ["This field is required."] }
  }
}
```

`meta` is only present on success responses. `error.details` for `400` mirrors DRF per-field validation errors; for other status codes it may be omitted or contain diagnostic context.

---

## Error Codes

| HTTP Status | `error.code` | When it occurs |
|---|---|---|
| `400` | `bad_request` | Missing or invalid query parameters |
| `404` | `not_found` | Unknown route |
| `405` | `method_not_allowed` | Wrong HTTP method (all endpoints are `GET` only) |
| `503` | `service_unavailable` | Elasticsearch or another dependency is unreachable |

---

## `GET /api/v1/health/`

Liveness and readiness probe. Checks that the app can actually reach its dependencies — not just that the Django process is up.

### Response — `200` (all healthy)

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "checks": {
      "database": true,
      "elasticsearch": true
    }
  },
  "error": null
}
```

### Response — `503` (a dependency is down)

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "service_unavailable",
    "message": "One or more dependencies are unreachable.",
    "details": {
      "database": true,
      "elasticsearch": false
    }
  }
}
```

`checks.database` — result of `SELECT 1` on the default connection.  
`checks.elasticsearch` — result of `es.ping()`.

---

## `GET /api/v1/destinations/search/`

Full destination search. Handles exact matches, prefix matches, typo-tolerant fuzzy matching, and cross-field queries (e.g. `"paris france"`). Results are ranked by relevance then secondarily by population.

### Query Parameters

| Param | Type | Required | Constraints |
|---|---|---|---|
| `q` | string | Yes | Non-blank. Blank or missing → `400`. |
| `country` | string | No | Filters results to this country (case/accent-insensitive exact match). |

### Example — basic city search

```
GET /api/v1/destinations/search/?q=paris
```

```json
{
  "success": true,
  "data": [
    {
      "city": "paris",
      "country": "France",
      "population": 2138551,
      "location": { "lat": 48.8566, "lon": 2.3522 },
      "score": 35.4
    }
  ],
  "error": null,
  "meta": { "query": "paris", "country": null, "count": 1 }
}
```

### Example — city + country in one query

```
GET /api/v1/destinations/search/?q=paris%20france
```

The `multi_match` cross-fields clause boosts results where both tokens match different fields, surfacing `paris, France` above any unrelated cities named "paris".

### Example — explicit country filter

```
GET /api/v1/destinations/search/?q=barcelona&country=spain
```

The `country` param adds a hard filter — only cities whose `country` matches `"spain"` (case-insensitive) are returned. Without it you may get results from multiple countries.

### Example — typo tolerance

```
GET /api/v1/destinations/search/?q=dhka
```

The full search endpoint uses `fuzziness: AUTO` on the `city.standard` field, so a single-character typo like `dhka` still surfaces `dhaka` (Bangladesh).

### Result Object Fields

| Field | Type | Description |
|---|---|---|
| `city` | string | City name, lowercased (e.g. `"dhaka"`) |
| `country` | string | Country name in Title Case (e.g. `"Bangladesh"`) |
| `population` | integer | Population (0 if unknown in the dataset) |
| `location` | object | `{ "lat": float, "lon": float }` — WGS-84 |
| `score` | float | Elasticsearch relevance score — useful for debugging ranking; not stable across ES upgrades |

Results are capped at **20**. No pagination.

### Errors

| Status | Condition |
|---|---|
| `400` | `q` is missing or blank |
| `503` | Elasticsearch is unreachable |

---

## `GET /api/v1/destinations/autocomplete/`

Top-5 autocomplete suggestions, optimised for sub-100 ms response times. Uses edge-ngram prefix matching — **no fuzzy/typo tolerance**. Designed for a search-as-you-type dropdown.

### Query Parameters

| Param | Type | Required | Constraints |
|---|---|---|---|
| `q` | string | Yes | Non-blank. Blank or missing → `400`. |

### Example — prefix match

```
GET /api/v1/destinations/autocomplete/?q=dha
```

```json
{
  "success": true,
  "data": [
    { "city": "dhaka",    "country": "Bangladesh", "location": { "lat": 23.7231, "lon": 90.4086 } },
    { "city": "dhamtari", "country": "India",      "location": { "lat": 20.7000, "lon": 81.5500 } }
  ],
  "error": null,
  "meta": { "query": "dha", "count": 2 }
}
```

### Example — multi-word city prefix

```
GET /api/v1/destinations/autocomplete/?q=san
```

Returns cities whose name starts with `"san"` — e.g. `san antonio`, `santiago`, `san diego` — ranked by a mix of text relevance and population.

### Note on typo tolerance

Autocomplete intentionally has no fuzziness. A mistyped query like `dhka` returns an empty list — this is by design to keep latency low. Use the full `/search/` endpoint for typo recovery.

### Result Object Fields

| Field | Type | Description |
|---|---|---|
| `city` | string | City name |
| `country` | string | Country name in Title Case |
| `location` | object | `{ "lat": float, "lon": float }` |

Unlike `/search/`, autocomplete results have **no** `population` or `score` field.

Always returns **at most 5** results.

### Errors

| Status | Condition |
|---|---|
| `400` | `q` is missing or blank |
| `503` | Elasticsearch is unreachable |

---

## `GET /api/v1/destinations/nearby/`

Radius search around a geographic point. Returns destinations within `radius` kilometres, sorted nearest-first.

### Query Parameters

| Param | Type | Required | Constraints |
|---|---|---|---|
| `lat` | float | Yes | `-90` to `90` |
| `lon` | float | Yes | `-180` to `180` |
| `radius` | float | Yes | `> 0` (kilometres) |

### Example — cities near Dhaka

```
GET /api/v1/destinations/nearby/?lat=23.7231&lon=90.4086&radius=50
```

```json
{
  "success": true,
  "data": [
    {
      "city": "dhaka",
      "country": "Bangladesh",
      "population": 10356500,
      "location": { "lat": 23.7231, "lon": 90.4086 },
      "distance_km": 0.0
    },
    {
      "city": "narayanganj",
      "country": "Bangladesh",
      "population": 296070,
      "location": { "lat": 23.6236, "lon": 90.5000 },
      "distance_km": 12.5
    }
  ],
  "error": null,
  "meta": {
    "lat": 23.7231,
    "lon": 90.4086,
    "radius_km": 50,
    "count": 2
  }
}
```

### Example — cities near Paris

```
GET /api/v1/destinations/nearby/?lat=48.8566&lon=2.3522&radius=30
```

### Result Object Fields

| Field | Type | Description |
|---|---|---|
| `city` | string | City name |
| `country` | string | Country name in Title Case |
| `population` | integer | Population (0 if unknown) |
| `location` | object | `{ "lat": float, "lon": float }` |
| `distance_km` | float | Great-circle distance from the query point, rounded to 3 decimal places |

Sorted by `distance_km` ascending. Capped at **50**.

### Errors

| Status | Condition |
|---|---|
| `400` | Any param is missing, non-numeric, or out of range (e.g. `lat=200`, `radius=0`) |
| `503` | Elasticsearch is unreachable |

---

## `GET /api/v1/destinations/within-bounds/`

Map viewport / bounding-box search. Returns all destinations inside the specified geographic rectangle, sorted by population descending (most prominent cities first).

### Query Parameters

| Param | Type | Required | Constraints |
|---|---|---|---|
| `north` | float | Yes | `-90` to `90`; must be greater than `south` |
| `south` | float | Yes | `-90` to `90` |
| `east` | float | Yes | `-180` to `180` |
| `west` | float | Yes | `-180` to `180` |

### Example — cities visible in a map of Japan

```
GET /api/v1/destinations/within-bounds/?north=36.0&south=35.0&east=140.0&west=139.0
```

```json
{
  "success": true,
  "data": [
    {
      "city": "tokyo",
      "country": "Japan",
      "population": 13185502,
      "location": { "lat": 35.6895, "lon": 139.6917 }
    },
    {
      "city": "yokohama",
      "country": "Japan",
      "population": 3574443,
      "location": { "lat": 35.4437, "lon": 139.6380 }
    }
  ],
  "error": null,
  "meta": {
    "north": 36.0,
    "south": 35.0,
    "east": 140.0,
    "west": 139.0,
    "count": 2
  }
}
```

### Example — Iberian Peninsula

```
GET /api/v1/destinations/within-bounds/?north=43.8&south=36.0&east=3.4&west=-9.5
```

Returns cities in Spain and Portugal sorted by population — `madrid`, `barcelona`, `lisbon`, etc.

### Result Object Fields

| Field | Type | Description |
|---|---|---|
| `city` | string | City name |
| `country` | string | Country name in Title Case |
| `population` | integer | Population (0 if unknown) |
| `location` | object | `{ "lat": float, "lon": float }` |

No `distance_km` (there is no single reference point) or `score` (this is a filter, not a relevance query). Capped at **100**.

### Errors

| Status | Condition |
|---|---|
| `400` | Any param is missing, non-numeric, or out of range; or `north <= south` |
| `503` | Elasticsearch is unreachable |

---

## Notes

### Country names in the dataset

Country names come from the seeded dataset and follow the mappings in `scripts/country_code_replace.py`. Some common examples:

| Country | Name in dataset |
|---|---|
| Bangladesh | `Bangladesh` |
| France | `France` |
| Germany | `Germany` |
| Japan | `Japan` |
| Spain | `Spain` |
| United Kingdom | `United Kingdom` |
| Brazil | `Brazil` |
| India | `India` |
| China | `China` |

Filtering via the `country` query parameter on `/search/` is **case and accent-insensitive** — `france`, `France`, and `FRANCE` all work.

### Result caps

| Endpoint | Cap |
|---|---|
| `/search/` | 20 |
| `/autocomplete/` | 5 |
| `/nearby/` | 50 |
| `/within-bounds/` | 100 |

No cursor or offset pagination is implemented.

### No authentication

All endpoints are currently unauthenticated. No API keys or session tokens are required.

### No rate limiting

Rate limiting is not yet implemented.

### Coordinates

All coordinates use WGS-84 (EPSG:4326). Longitude: `-180` to `180`, latitude: `-90` to `90`.
