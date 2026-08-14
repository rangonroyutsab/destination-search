"""
Destinations API views.
"""

from rest_framework.views import APIView

from apps.destinations.serializers import (
    AutocompleteQuerySerializer,
    SearchQuerySerializer,
)
from apps.destinations.services import autocomplete_service, search_service
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
