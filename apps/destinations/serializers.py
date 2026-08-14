"""
Query-parameter validation for the destinations API.
"""

from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    country = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True
    )

    def validate_country(self, value):
        return value.strip() or None


class AutocompleteQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
