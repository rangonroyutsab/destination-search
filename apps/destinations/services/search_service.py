"""
Search service - orchestrates the search + query builder + ES client,
and shapes raw ES hits into plain dicts the API layer can hand
straight to success_response().
"""

from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import TransportError

from apps.destinations.search.client import get_es_client, index_name
from apps.destinations.search.queries import build_search_query


class SearchUnavailableError(Exception):
    """Raised when Elasticsearch can't be reached — lets the view
    return a proper 503 instead of a raw 500."""


def search(q: str, country: str | None = None, size: int = 20) -> list[dict]:
    """
    Runs a destination search and returns a list of plain result dicts:
        {"city": ..., "country": ..., "population": ..., "location": {"lat":.., "lon":..}, "score": ...}
    """
    es = get_es_client()
    query_body = build_search_query(q, country=country, size=size)

    try:
        response = es.search(index=index_name(), body=query_body)
    except (ESConnectionError, TransportError) as exc:
        raise SearchUnavailableError(str(exc)) from exc

    return [_hit_to_result(hit) for hit in response["hits"]["hits"]]


def _hit_to_result(hit: dict) -> dict:
    source = hit["_source"]
    return {
        "city": source["city"],
        "country": source["country"],
        "population": source.get("population", 0),
        "location": source["location"],
        "score": hit["_score"],
    }
