"""
Destinations API views.
"""

from rest_framework.views import APIView

from apps.destinations.serializers import (
    AutocompleteQuerySerializer,
    NearbyQuerySerializer,
    SearchQuerySerializer,
)
from apps.destinations.services import autocomplete_service, geo_service, search_service
from core.utils.responses import success_response


class SearchView(APIView):
    """GET /api/v1/destinations/search?q=<query>&country=<optional>"""

    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        q = serializer.validated_data["q"]
        country = serializer.validated_data.get("country")

        results = search_service.search(q, country=country)

        return success_response(
            results, meta={"query": q, "country": country, "count": len(results)}
        )


class AutocompleteView(APIView):
    """GET /api/v1/destinations/autocomplete?q=<query>"""

    def get(self, request):
        serializer = AutocompleteQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        q = serializer.validated_data["q"]

        results = autocomplete_service.autocomplete(q)

        return success_response(results, meta={"query": q, "count": len(results)})


class NearbyView(APIView):
    """GET /api/v1/destinations/nearby?lat=<lat>&lon=<lon>&radius=<km>"""

    def get(self, request):
        serializer = NearbyQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        results = geo_service.nearby(data["lat"], data["lon"], data["radius"])

        return success_response(
            results,
            meta={
                "lat": data["lat"],
                "lon": data["lon"],
                "radius_km": data["radius"],
                "count": len(results),
            },
        )
