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


def build_search_query(q: str, country: str | None = None, size: int = 20) -> dict:
    """
    Full destination search - broader than autocomplete: adds fuzzy
    matching for typo tolerance and an optional country filter.
    """
    q_norm = q.strip().lower()

    should = [
        {"term": {"city.raw": {"value": q_norm, "boost": 25}}},
        {"match": {"city": {"query": q_norm, "boost": 10}}},
        {"match": {"city": {"query": q_norm, "fuzziness": "AUTO", "boost": 4}}},
        {"match": {"country": {"query": q_norm, "boost": 3}}},
        {"term": {"country.raw": {"value": q_norm, "boost": 3}}},
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
