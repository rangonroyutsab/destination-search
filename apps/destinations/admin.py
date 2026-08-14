from django.contrib.gis import admin

from .models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.GISModelAdmin):
    list_display = (
        "city",
        "country",
        "population",
        "location",
        "created_at",
        "updated_at",
    )
    search_fields = ("city", "country")
    list_filter = ("country",)
    ordering = ("country", "city", "population")
