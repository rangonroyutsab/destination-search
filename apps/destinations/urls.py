from django.urls import path

from apps.destinations import views

urlpatterns = [
    path("search/", views.SearchView.as_view(), name="destination-search"),
]
