"""
Load test for the destinations API.

Run with the dashboard:
    locust -f locustfile.py --host=http://localhost:8000

Or headless:
    locust -f locustfile.py --host=http://localhost:8000 \
        --headless --users 100 --spawn-rate 10 --run-time 2m
"""

import random

from locust import HttpUser, between, task


# Prefixes chosen from cities in countries that actually exist
# in the current dataset.
AUTOCOMPLETE_PREFIXES = [
    "dha",  # Dhaka, Bangladesh
    "lon",  # London, United Kingdom
    "par",  # Paris, France
    "ber",  # Berlin, Germany
    "cai",  # Cairo, Egypt
    "bei",  # Beijing, China
    "sao",  # Sao Paulo, Brazil
    "bue",  # Buenos Aires, Argentina
    "syd",  # Sydney, Australia
    "bru",  # Brussels, Belgium
    "cop",  # Copenhagen, Denmark
    "hel",  # Helsinki, Finland
    "ath",  # Athens, Greece
    "mad",  # Madrid, Spain
]


SEARCH_QUERIES = [
    "dhaka",
    "dhaka bangladesh",
    "london",
    "london united kingdom",
    "paris",
    "paris france",
    "berlin",
    "berlin germany",
    "cairo",
    "cairo egypt",
    "beijing",
    "beijing china",
    "sao paulo",
    "sao paulo brazil",
    "sydney",
    "sydney australia",
    "athens",
    "athens greece",
]


NEARBY_POINTS = [
    {
        "lat": 23.8103,
        "lon": 90.4125,
        "radius": 25,
    },  # Dhaka, Bangladesh
    {
        "lat": 51.5074,
        "lon": -0.1278,
        "radius": 30,
    },  # London, United Kingdom
    {
        "lat": 48.8566,
        "lon": 2.3522,
        "radius": 25,
    },  # Paris, France
    {
        "lat": 52.5200,
        "lon": 13.4050,
        "radius": 25,
    },  # Berlin, Germany
    {
        "lat": 30.0444,
        "lon": 31.2357,
        "radius": 25,
    },  # Cairo, Egypt
    {
        "lat": -23.5505,
        "lon": -46.6333,
        "radius": 30,
    },  # Sao Paulo, Brazil
]


BOUNDING_BOXES = [
    {
        "north": 23.95,
        "south": 23.65,
        "east": 90.55,
        "west": 90.25,
    },  # Dhaka
    {
        "north": 51.70,
        "south": 51.30,
        "east": 0.30,
        "west": -0.50,
    },  # London
    {
        "north": 48.95,
        "south": 48.75,
        "east": 2.50,
        "west": 2.10,
    },  # Paris
    {
        "north": 52.65,
        "south": 52.35,
        "east": 13.65,
        "west": 13.15,
    },  # Berlin
    {
        "north": 30.20,
        "south": 29.90,
        "east": 31.40,
        "west": 31.10,
    },  # Cairo
]


class DestinationSearchUser(HttpUser):
    # Simulated user think time between requests.
    wait_time = between(1, 3)

    @task(5)
    def autocomplete(self):
        q = random.choice(AUTOCOMPLETE_PREFIXES)  # NOSONAR

        with self.client.get(
            "/api/v1/destinations/autocomplete",
            params={"q": q},
            name="/autocomplete",
            catch_response=True,
        ) as resp:
            self._check(resp)

    @task(3)
    def search(self):
        q = random.choice(SEARCH_QUERIES)  # NOSONAR

        with self.client.get(
            "/api/v1/destinations/search",
            params={"q": q},
            name="/search",
            catch_response=True,
        ) as resp:
            self._check(resp)

    @task(2)
    def nearby(self):
        point = random.choice(NEARBY_POINTS)  # NOSONAR

        with self.client.get(
            "/api/v1/destinations/nearby",
            params={
                "lat": point["lat"],
                "lon": point["lon"],
                "radius": point["radius"],
            },
            name="/nearby",
            catch_response=True,
        ) as resp:
            self._check(resp)

    @task(1)
    def within_bounds(self):
        bounds = random.choice(BOUNDING_BOXES)  # NOSONAR

        with self.client.get(
            "/api/v1/destinations/within-bounds",
            params={
                "north": bounds["north"],
                "south": bounds["south"],
                "east": bounds["east"],
                "west": bounds["west"],
            },
            name="/within-bounds",
            catch_response=True,
        ) as resp:
            self._check(resp)

    @staticmethod
    def _check(resp):
        if resp.status_code != 200:
            resp.failure(f"status {resp.status_code}")
            return

        try:
            json_data = resp.json()
        except ValueError:
            resp.failure("non-JSON response")
            return

        if not json_data.get("success"):
            resp.failure("envelope success=false")
            return

        data = json_data.get("data")

        if not data:
            resp.failure("empty data returned")