"""
Health check endpoint tests.
"""

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db

URL = "/api/v1/health/"


def test_all_healthy_returns_200(api_client, mocker):
    mock_es = mocker.MagicMock()
    mock_es.ping.return_value = True
    mocker.patch("core.views.get_es_client", return_value=mock_es)

    response = api_client.get(URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] is True
    assert response.data["data"]["checks"]["database"] is True
    assert response.data["data"]["checks"]["elasticsearch"] is True


def test_elasticsearch_down_returns_503(api_client, mocker):
    mock_es = mocker.MagicMock()
    mock_es.ping.return_value = False
    mocker.patch("core.views.get_es_client", return_value=mock_es)

    response = api_client.get(URL)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.data["success"] is False
    assert response.data["error"]["details"]["elasticsearch"] is False
    assert response.data["error"]["details"]["database"] is True


def test_elasticsearch_exception_counts_as_down(api_client, mocker):
    mocker.patch(
        "core.views.get_es_client", side_effect=Exception("connection refused")
    )

    response = api_client.get(URL)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
