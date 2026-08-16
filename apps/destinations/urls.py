from django.urls import path

from apps.destinations import views

urlpatterns = [
    path("search/", views.SearchView.as_view(), name="destination-search"),
    path(
        "autocomplete/",
        views.AutocompleteView.as_view(),
        name="destination-autocomplete",
    ),
    path("nearby/", views.NearbyView.as_view(), name="destination-nearby"),
]
