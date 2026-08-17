"""
API/view-layer tests.
"""

import pytest
from rest_framework import status

from core.utils.exceptions import ServiceUnavailableError

pytestmark = pytest.mark.django_db


class TestSearchView:
    url = "/api/v1/destinations/search/"

    def test_missing_query_param_returns_400(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert response.data["data"] is None
        assert response.data["error"] is not None

    def test_valid_query_returns_200_with_envelope(self, api_client, mocker):
        mock_search = mocker.patch(
            "apps.destinations.services.search_service.search",
            return_value=[
                {
                    "city": "paris",
                    "country": "france",
                    "population": 2000000,
                    "location": {"lat": 1, "lon": 2},
                    "score": 9.9,
                }
            ],
        )

        response = api_client.get(self.url, {"q": "paris"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"] == mock_search.return_value
        assert response.data["meta"]["query"] == "paris"
        assert response.data["meta"]["count"] == 1
        mock_search.assert_called_once_with("paris", country=None)

    def test_country_param_passed_through(self, api_client, mocker):
        mock_search = mocker.patch(
            "apps.destinations.services.search_service.search", return_value=[]
        )

        api_client.get(self.url, {"q": "paris", "country": "france"})

        mock_search.assert_called_once_with("paris", country="france")

    def test_service_unavailable_returns_503(self, api_client, mocker):
        mocker.patch(
            "apps.destinations.services.search_service.search",
            side_effect=ServiceUnavailableError("ES down"),
        )

        response = api_client.get(self.url, {"q": "paris"})

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["success"] is False
        assert response.data["error"]["code"] == "service_unavailable"


class TestAutocompleteView:
    url = "/api/v1/destinations/autocomplete/"

    def test_missing_query_param_returns_400(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_query_returns_200(self, api_client, mocker):
        mocker.patch(
            "apps.destinations.services.autocomplete_service.autocomplete",
            return_value=[
                {
                    "city": "san antonio",
                    "country": "united states",
                    "location": {"lat": 1, "lon": 2},
                }
            ],
        )

        response = api_client.get(self.url, {"q": "san"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["meta"]["count"] == 1

    def test_service_unavailable_returns_503(self, api_client, mocker):
        mocker.patch(
            "apps.destinations.services.autocomplete_service.autocomplete",
            side_effect=ServiceUnavailableError("ES down"),
        )

        response = api_client.get(self.url, {"q": "san"})

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestNearbyView:
    url = "/api/v1/destinations/nearby/"

    def test_missing_params_returns_400(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_out_of_range_lat_returns_400(self, api_client):
        response = api_client.get(self.url, {"lat": 200, "lon": 0, "radius": 10})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_zero_radius_returns_400(self, api_client):
        response = api_client.get(self.url, {"lat": 0, "lon": 0, "radius": 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_params_returns_200(self, api_client, mocker):
        mock_nearby = mocker.patch(
            "apps.destinations.services.geo_service.nearby",
            return_value=[
                {
                    "city": "miami",
                    "country": "united states",
                    "population": 400000,
                    "location": {"lat": 25.76, "lon": -80.19},
                    "distance_km": 1.2,
                }
            ],
        )

        response = api_client.get(
            self.url, {"lat": 25.7617, "lon": -80.1918, "radius": 25}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["meta"]["radius_km"] == 25
        mock_nearby.assert_called_once_with(25.7617, -80.1918, 25.0)

    def test_service_unavailable_returns_503(self, api_client, mocker):
        mocker.patch(
            "apps.destinations.services.geo_service.nearby",
            side_effect=ServiceUnavailableError("ES down"),
        )

        response = api_client.get(self.url, {"lat": 0, "lon": 0, "radius": 10})

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestWithinBoundsView:
    url = "/api/v1/destinations/within-bounds/"

    def test_missing_params_returns_400(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_north_not_greater_than_south_returns_400(self, api_client):
        response = api_client.get(
            self.url, {"north": 10, "south": 20, "east": 5, "west": 1}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_params_returns_200(self, api_client, mocker):
        mock_within_bounds = mocker.patch(
            "apps.destinations.services.geo_service.within_bounds",
            return_value=[
                {
                    "city": "miami",
                    "country": "united states",
                    "population": 400000,
                    "location": {"lat": 25.76, "lon": -80.19},
                }
            ],
        )

        response = api_client.get(
            self.url, {"north": 25.90, "south": 25.60, "east": -80.00, "west": -80.40}
        )

        assert response.status_code == status.HTTP_200_OK
        mock_within_bounds.assert_called_once_with(25.90, 25.60, -80.00, -80.40)

    def test_service_unavailable_returns_503(self, api_client, mocker):
        mocker.patch(
            "apps.destinations.services.geo_service.within_bounds",
            side_effect=ServiceUnavailableError("ES down"),
        )

        response = api_client.get(
            self.url, {"north": 10, "south": 5, "east": 5, "west": 1}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
