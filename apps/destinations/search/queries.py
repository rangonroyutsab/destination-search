"""
Query builders for text search (city + country).

Priority order these follow (per the spec):
    1. Exact match
    2. Prefix match
    3. General relevance
    4. Country match
    5. Population as a secondary tie-breaker
"""


def _population_score_function():
    """
    Shared scoring function: population acts as a secondary boost,
    log-dampened so a huge city (10M+) doesn't completely drown out
    an otherwise-better text match from a smaller one.
    """
    return {
        "field_value_factor": {
            "field": "population",
            "modifier": "log1p",
            "factor": 0.1,
            "missing": 0,
        }
    }


def build_autocomplete_query(q: str, size: int = 5) -> dict:
    """
    Top-N autocomplete
        - optimized for speed, so no fuzziness
        - relies on the edge_ngram index-time analyzer to handle prefix matching
    """
    q_norm = q.strip().lower()

    return {
        "size": size,
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "should": [
                            # 1. Exact match - highest priority.
                            {"term": {"city.raw": {"value": q_norm, "boost": 20}}},
                            # 2. Prefix match via the edge_ngram field.
                            {"match": {"city": {"query": q_norm, "boost": 8}}},
                            # 4. Country match - lower priority than city.
                            {"match": {"country": {"query": q_norm, "boost": 2}}},
                        ],
                        "minimum_should_match": 1,
                    }
                },
                # 5. Population - secondary factor, added on top of the
                # text-relevance score rather than replacing it.
                "functions": [_population_score_function()],
                "boost_mode": "sum",
                "score_mode": "sum",
            }
        },
    }


def build_search_query(q: str, country: str | None = None, size: int = 20) -> dict:
    """
    Full destination search - broader than autocomplete: adds fuzzy
    matching for typo tolerance and an optional country filter/boost
    for queries like "paris france".
    """
    q_norm = q.strip().lower()

    should = [
        # 1. Exact match.
        {"term": {"city.raw": {"value": q_norm, "boost": 25}}},
        # 2. Prefix match
        {"match": {"city": {"query": q_norm, "boost": 10}}},
        # 3. General relevance + typo tolerance
        {
            "match": {
                "city.standard": {"query": q_norm, "fuzziness": "AUTO", "boost": 4}
            }
        },
        # 4. Country match - whole-word field, same reasoning.
        {"match": {"country.standard": {"query": q_norm, "boost": 3}}},
        {"term": {"country.raw": {"value": q_norm, "boost": 3}}},
        {
            "multi_match": {
                "query": q_norm,
                "type": "cross_fields",
                "fields": ["city.standard", "country.standard"],
                "operator": "and",
                "boost": 15,
            }
        },
    ]

    bool_query: dict = {"should": should, "minimum_should_match": 1}

    if country:
        bool_query["filter"] = [{"term": {"country.raw": country.strip().lower()}}]

    return {
        "size": size,
        "query": {
            "function_score": {
                "query": {"bool": bool_query},
                "functions": [_population_score_function()],
                "boost_mode": "sum",
                "score_mode": "sum",
            }
        },
    }


def build_nearby_query(
    lat: float, lon: float, radius_km: float, size: int = 50
) -> dict:
    """
    Radius search around a point. Uses a geo_distance FILTER (not a
    scored query) - a result is either in range or it isn't, so
    there's no relevance score to compute; sorting is by actual
    distance instead, which is what "nearby" means to a caller.
    """
    return {
        "size": size,
        "query": {
            "bool": {
                "filter": {
                    "geo_distance": {
                        "distance": f"{radius_km}km",
                        "location": {"lat": lat, "lon": lon},
                    }
                }
            }
        },
        "sort": [
            {
                "_geo_distance": {
                    "location": {"lat": lat, "lon": lon},
                    "order": "asc",
                    "unit": "km",
                }
            }
        ],
    }


def build_within_bounds_query(
    north: float, south: float, east: float, west: float, size: int = 100
) -> dict:
    """
    Map viewport / bounding-box search. Also a filter, not a scored
    query - every result inside the box is equally "in bounds".
    Sorted by population so the most prominent places surface first
    when a zoomed-out viewport returns more than `size` results.
    """
    return {
        "size": size,
        "query": {
            "bool": {
                "filter": {
                    "geo_bounding_box": {
                        "location": {
                            "top_left": {"lat": north, "lon": west},
                            "bottom_right": {"lat": south, "lon": east},
                        }
                    }
                }
            }
        },
        "sort": [{"population": {"order": "desc"}}],
    }
