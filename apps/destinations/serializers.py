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


class NearbyQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True, min_value=-90, max_value=90)
    lon = serializers.FloatField(required=True, min_value=-180, max_value=180)
    radius = serializers.FloatField(required=True, min_value=0.01)


class WithinBoundsQuerySerializer(serializers.Serializer):
    north = serializers.FloatField(required=True, min_value=-90, max_value=90)
    south = serializers.FloatField(required=True, min_value=-90, max_value=90)
    east = serializers.FloatField(required=True, min_value=-180, max_value=180)
    west = serializers.FloatField(required=True, min_value=-180, max_value=180)

    def validate(self, data):
        if data["north"] <= data["south"]:
            raise serializers.ValidationError(
                {"bounds": "'north' must be greater than 'south'."}
            )
        return data
