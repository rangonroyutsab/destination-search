"""
Geo service — nearby (radius) and within-bounds (bounding box) search.
"""

from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import TransportError

from django.conf import settings

from apps.destinations.search.client import get_es_client, index_name
from apps.destinations.search.queries import (
    build_nearby_query,
    build_within_bounds_query,
)
from core.utils.exceptions import ServiceUnavailableError


def nearby(lat: float, lon: float, radius_km: float, size: int | None = None) -> list[dict]:
    size = size or settings.NEARBY_DEFAULT_SIZE
    """
    Returns destinations within radius_km of (lat, lon), nearest first:
        {"city": ..., "country": ..., "population": ..., "location": {...}, "distance_km": ...}
    """
    es = get_es_client()
    query_body = build_nearby_query(lat, lon, radius_km, size=size)

    try:
        response = es.search(index=index_name(), body=query_body)
    except (ESConnectionError, TransportError) as exc:
        raise ServiceUnavailableError(str(exc)) from exc

    return [_hit_to_nearby_result(hit) for hit in response["hits"]["hits"]]


def within_bounds(
    north: float, south: float, east: float, west: float, size: int | None = None
) -> list[dict]:
    size = size or settings.BOUNDS_DEFAULT_SIZE
    """
    Returns destinations inside the given map viewport, most populous
    first:
        {"city": ..., "country": ..., "population": ..., "location": {...}}
    """
    es = get_es_client()
    query_body = build_within_bounds_query(north, south, east, west, size=size)

    try:
        response = es.search(index=index_name(), body=query_body)
    except (ESConnectionError, TransportError) as exc:
        raise ServiceUnavailableError(str(exc)) from exc

    return [_hit_to_result(hit) for hit in response["hits"]["hits"]]


def _hit_to_nearby_result(hit: dict) -> dict:
    result = _hit_to_result(hit)
    # build_nearby_query sorts by _geo_distance with unit="km"
    result["distance_km"] = round(hit["sort"][0], 3)
    return result


def _hit_to_result(hit: dict) -> dict:
    source = hit["_source"]
    return {
        "city": source["city"],
        "country": source["country"],
        "population": source.get("population", 0),
        "location": source["location"],
    }
