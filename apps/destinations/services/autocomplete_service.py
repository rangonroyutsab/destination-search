"""
Autocomplete service - same orchestration pattern as search_service.py
but optimized for speed and top-N results, so no fuzzy matching or country filter.
"""

from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import TransportError

from apps.destinations.search.client import get_es_client, index_name
from apps.destinations.search.queries import build_autocomplete_query
from core.utils.exceptions import ServiceUnavailableError

MAX_RESULTS = 5


def autocomplete(q: str) -> list[dict]:
    """
    Returns up to 5 suggestion dicts:
        {"city": ..., "country": ..., "location": {"lat":.., "lon":..}}
    """
    es = get_es_client()
    query_body = build_autocomplete_query(q, size=MAX_RESULTS)

    try:
        response = es.search(index=index_name(), body=query_body)
    except (ESConnectionError, TransportError) as exc:
        raise ServiceUnavailableError(str(exc)) from exc

    return [_hit_to_suggestion(hit) for hit in response["hits"]["hits"]]


def _hit_to_suggestion(hit: dict) -> dict:
    source = hit["_source"]
    return {
        "city": source["city"],
        "country": source["country"],
        "location": source["location"],
    }
