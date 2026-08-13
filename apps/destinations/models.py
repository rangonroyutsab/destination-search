from django.contrib.gis.db import models


class Destination(models.Model):
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    population = models.IntegerField(default=0)

    location = models.PointField(geography=True, srid=4326)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["location"], name="destination_location_gist"),
            models.Index(
                fields=["country", "city"], name="destination_country_city_idx"
            ),
        ]

    def __str__(self):
        return f"{self.city}, {self.country}"
