"""
Service-layer unit tests.

Elasticsearch is MOCKED here.
"""

from unittest.mock import MagicMock

import pytest
from elasticsearch import ConnectionError as ESConnectionError

from apps.destinations.services import autocomplete_service, geo_service, search_service
from core.utils.exceptions import ServiceUnavailableError


@pytest.fixture
def fake_hit():
    """Factory fixture - call fake_hit(city, country, ...) to build one ES hit dict."""

    def _make(city, country, population=1000, lat=1.0, lon=2.0, score=5.0):
        return {
            "_score": score,
            "_source": {
                "city": city,
                "country": country,
                "population": population,
                "location": {"lat": lat, "lon": lon},
            },
        }

    return _make


@pytest.fixture
def mock_es(mocker):
    """Patches the ES client in all three services to a MagicMock, and returns it."""
    es = MagicMock()
    mocker.patch(
        "apps.destinations.services.search_service.get_es_client", return_value=es
    )
    mocker.patch(
        "apps.destinations.services.autocomplete_service.get_es_client", return_value=es
    )
    mocker.patch(
        "apps.destinations.services.geo_service.get_es_client", return_value=es
    )
    return es


class TestSearchService:
    def test_shapes_hits_into_result_dicts(self, mock_es, fake_hit):
        mock_es.search.return_value = {
            "hits": {
                "hits": [fake_hit("paris", "france", population=2000000, score=12.3)]
            }
        }

        results = search_service.search("paris")

        assert results == [
            {
                "city": "paris",
                "country": "france",
                "population": 2000000,
                "location": {"lat": 1.0, "lon": 2.0},
                "score": 12.3,
            }
        ]

    def test_defaults_missing_population_to_zero(self, mock_es, fake_hit):
        hit = fake_hit("nowhere", "nocountry")
        del hit["_source"]["population"]
        mock_es.search.return_value = {"hits": {"hits": [hit]}}

        results = search_service.search("nowhere")

        assert results[0]["population"] == 0

    def test_raises_service_unavailable_on_connection_error(self, mock_es):
        mock_es.search.side_effect = ESConnectionError("boom")

        with pytest.raises(ServiceUnavailableError):
            search_service.search("paris")

    def test_passes_params_through_to_query_builder(self, mock_es, mocker):
        mock_es.search.return_value = {"hits": {"hits": []}}
        mock_build_query = mocker.patch(
            "apps.destinations.services.search_service.build_search_query",
            return_value={"query": "stub"},
        )

        search_service.search("paris", country="france", size=7)

        mock_build_query.assert_called_once_with("paris", country="france", size=7)


class TestAutocompleteService:
    def test_shapes_hits_without_score_or_population(self, mock_es, fake_hit):
        mock_es.search.return_value = {
            "hits": {"hits": [fake_hit("san antonio", "united states")]}
        }

        results = autocomplete_service.autocomplete("san")

        assert results == [
            {
                "city": "san antonio",
                "country": "united states",
                "location": {"lat": 1.0, "lon": 2.0},
            }
        ]
        assert "population" not in results[0]
        assert "score" not in results[0]

    def test_raises_service_unavailable_on_connection_error(self, mock_es):
        mock_es.search.side_effect = ESConnectionError("boom")

        with pytest.raises(ServiceUnavailableError):
            autocomplete_service.autocomplete("san")

    def test_always_requests_max_five(self, mock_es, mocker):
        mock_es.search.return_value = {"hits": {"hits": []}}
        mock_build_query = mocker.patch(
            "apps.destinations.services.autocomplete_service.build_autocomplete_query",
            return_value={},
        )

        autocomplete_service.autocomplete("san")

        mock_build_query.assert_called_once_with(
            "san", size=autocomplete_service.MAX_RESULTS
        )


class TestGeoServiceNearby:
    def test_shapes_hits_with_distance_from_sort_value(self, mock_es, fake_hit):
        hit = fake_hit(
            "miami", "united states", population=400000, lat=25.76, lon=-80.19
        )
        hit["sort"] = [3.14159]
        mock_es.search.return_value = {"hits": {"hits": [hit]}}

        results = geo_service.nearby(25.7617, -80.1918, 25)

        assert results[0]["city"] == "miami"
        assert results[0]["distance_km"] == 3.142  # rounded to 3dp

    def test_raises_service_unavailable_on_connection_error(self, mock_es):
        mock_es.search.side_effect = ESConnectionError("boom")

        with pytest.raises(ServiceUnavailableError):
            geo_service.nearby(0, 0, 10)

    def test_passes_params_through_to_query_builder(self, mock_es, mocker):
        mock_es.search.return_value = {"hits": {"hits": []}}
        mock_build_query = mocker.patch(
            "apps.destinations.services.geo_service.build_nearby_query",
            return_value={},
        )

        geo_service.nearby(25.7617, -80.1918, 25, size=10)

        mock_build_query.assert_called_once_with(25.7617, -80.1918, 25, size=10)


class TestGeoServiceWithinBounds:
    def test_shapes_hits_without_distance(self, mock_es, fake_hit):
        mock_es.search.return_value = {
            "hits": {"hits": [fake_hit("tokyo", "japan", population=13000000)]}
        }

        results = geo_service.within_bounds(36, 35, 140, 139)

        assert results[0]["city"] == "tokyo"
        assert "distance_km" not in results[0]

    def test_raises_service_unavailable_on_connection_error(self, mock_es):
        mock_es.search.side_effect = ESConnectionError("boom")

        with pytest.raises(ServiceUnavailableError):
            geo_service.within_bounds(1, 0, 1, 0)
