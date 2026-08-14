"""
Destinations API views.
"""

from rest_framework.views import APIView

from apps.destinations.serializers import SearchQuerySerializer
from apps.destinations.services import search_service
from core.utils.responses import error_response, success_response


class SearchView(APIView):
    """GET /api/v1/destinations/search?q=<query>&country=<optional>"""

    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        q = serializer.validated_data["q"]
        country = serializer.validated_data.get("country")

        try:
            results = search_service.search(q, country=country)
        except search_service.SearchUnavailableError:
            return error_response(
                "Search is temporarily unavailable.",
                status=503,
                code="service_unavailable",
            )

        return success_response(
            results, meta={"query": q, "country": country, "count": len(results)}
        )
