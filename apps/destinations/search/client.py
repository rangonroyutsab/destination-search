"""
Shared Elasticsearch client.
"""

import os
from functools import lru_cache

from elasticsearch import Elasticsearch

from apps.destinations.search.documents import INDEX_NAME


@lru_cache(maxsize=1)
def get_es_client() -> Elasticsearch:
    """
    Returns a process-wide singleton Elasticsearch client.
    """
    return Elasticsearch(
        os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200"),
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
    )


def index_name() -> str:
    """Small wrapper so callers don't need to import documents.py directly."""
    return INDEX_NAME
