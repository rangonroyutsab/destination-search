"""
Search accuracy tests, per the spec's acceptance criteria:
"Search accuracy is tested using common, ambiguous, typo, and
country-specific queries."

These hit the real seeded Elasticsearch index, not mocks

Run with: docker compose exec web python manage.py test apps.destinations.tests.test_search_accuracy
"""
from django.test import TestCase

from apps.destinations.services import autocomplete_service, search_service


class CommonQueryAccuracyTests(TestCase):
    """Straightforward, unambiguous queries - the baseline that must work."""

    def test_exact_city_match_ranks_first(self):
        results = search_service.search("miami")
        self.assertTrue(results, "Expected at least one result for 'miami'.")
        self.assertEqual(results[0]["city"], "miami")

    def test_multi_word_city_search(self):
        results = search_service.search("san antonio")
        self.assertTrue(results)
        self.assertEqual(results[0]["city"], "san antonio")

    def test_autocomplete_prefix_match(self):
        results = autocomplete_service.autocomplete("san")
        self.assertTrue(results, "Expected autocomplete suggestions for prefix 'san'.")
        self.assertTrue(results[0]["city"].startswith("san"))

    def test_autocomplete_returns_at_most_five(self):
        results = autocomplete_service.autocomplete("san")
        self.assertLessEqual(len(results), 5)


class CountryAwareQueryAccuracyTests(TestCase):
    def test_city_country_combo_search(self):
        results = search_service.search("paris france")
        self.assertTrue(results)
        self.assertEqual(results[0]["city"], "paris")
        self.assertEqual(results[0]["country"].lower(), "france")

    def test_explicit_country_filter(self):
        results = search_service.search("paris", country="france")
        self.assertTrue(results)
        self.assertTrue(all(r["country"].lower() == "france" for r in results))


class AmbiguousQueryAccuracyTests(TestCase):
    def test_ambiguous_query_surfaces_the_canonical_match(self):
        results = search_service.search("andorra")
        self.assertTrue(results)
        self.assertEqual(results[0]["city"], "andorra")

    def test_ambiguous_query_still_returns_related_variants(self):
        results = search_service.search("andorra")
        cities = {r["city"] for r in results}
        self.assertTrue(
            cities & {"andorra la vella", "andorre", "andorre-la-vieille"},
            "Expected at least one andorra variant among results.",
        )


class TypoToleranceAccuracyTests(TestCase):
    def test_full_search_recovers_from_a_typo(self):
        results = search_service.search("dhka")
        cities = {r["city"] for r in results}
        self.assertIn("dhaka", cities, "Full search should tolerate a 1-edit typo via fuzziness=AUTO.")

    def test_autocomplete_does_not_recover_from_a_typo(self):
        results = autocomplete_service.autocomplete("dhka")
        self.assertEqual(results, [], "Autocomplete has no fuzzy fallback yet - see fuzzy-fallback discussion.")

    def test_autocomplete_works_for_a_true_prefix(self):
        results = autocomplete_service.autocomplete("dha")
        cities = {r["city"] for r in results}
        self.assertIn("dhaka", cities)