"""
Real Elasticsearch connectivity checks.
"""

import pytest

from apps.destinations.search.client import get_es_client, index_name

pytestmark = pytest.mark.integration


def test_client_is_singleton():
    assert get_es_client() is get_es_client()


def test_client_connects():
    assert get_es_client().ping() is True


def test_index_exists_and_has_docs():
    es = get_es_client()
    assert es.indices.exists(index=index_name())
    assert es.count(index=index_name())["count"] > 0
