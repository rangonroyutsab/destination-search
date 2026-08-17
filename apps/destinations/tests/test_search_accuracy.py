"""
Search accuracy tests:
"Search accuracy is tested using common, ambiguous, typo, and
country-specific queries."
"""

import pytest

from apps.destinations.services import autocomplete_service, search_service

pytestmark = pytest.mark.integration


class TestCommonQueryAccuracy:
    """Straightforward, unambiguous queries."""

    def test_exact_city_match_ranks_first(self):
        results = search_service.search("miami")
        assert results, "Expected at least one result for 'miami'."
        assert results[0]["city"] == "miami"

    def test_multi_word_city_search(self):
        results = search_service.search("san antonio")
        assert results
        assert results[0]["city"] == "san antonio"

    def test_autocomplete_prefix_match(self):
        results = autocomplete_service.autocomplete("san")
        assert results, "Expected autocomplete suggestions for prefix 'san'."
        assert results[0]["city"].startswith("san")

    def test_autocomplete_returns_at_most_five(self):
        results = autocomplete_service.autocomplete("san")
        assert len(results) <= 5


class TestCountryAwareQueryAccuracy:
    """Queries combining city + country."""

    def test_city_country_combo_search(self):
        results = search_service.search("paris france")
        assert results
        assert results[0]["city"] == "paris"
        assert results[0]["country"].lower() == "france"

    def test_explicit_country_filter(self):
        results = search_service.search("paris", country="france")
        assert results
        assert all(r["country"].lower() == "france" for r in results)


class TestAmbiguousQueryAccuracy:
    """Queries with multiple plausible matches."""

    def test_ambiguous_query_surfaces_the_canonical_match(self):
        results = search_service.search("andorra")
        assert results
        assert results[0]["city"] == "andorra"

    def test_ambiguous_query_still_returns_related_variants(self):
        results = search_service.search("andorra")
        cities = {r["city"] for r in results}
        assert cities & {"andorra la vella", "andorre", "andorre-la-vieille"}, (
            "Expected at least one andorra variant among results."
        )


class TestTypoToleranceAccuracy:
    """
    Typo handling differs deliberately by endpoint:
    - Full /search HAS fuzziness (fuzziness="AUTO" on city.standard)
        - should recover from a typo.
    - /autocomplete has NO fuzziness by design.
    """

    def test_full_search_recovers_from_a_typo(self):
        results = search_service.search("dhka")
        cities = {r["city"] for r in results}
        assert "dhaka" in cities, (
            "Full search should tolerate a 1-edit typo via fuzziness=AUTO."
        )

    def test_autocomplete_does_not_recover_from_a_typo(self):
        """
        Autocomplete has no fuzzy fallback by design.
        """
        results = autocomplete_service.autocomplete("dhka")
        assert results == [], (
            "Autocomplete has no fuzzy fallback yet - see fuzzy-fallback discussion."
        )

    def test_autocomplete_works_for_a_true_prefix(self):
        results = autocomplete_service.autocomplete("dha")
        cities = {r["city"] for r in results}
        assert "dhaka" in cities
