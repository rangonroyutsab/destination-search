from django.test import TestCase

from apps.destinations.search.client import get_es_client, index_name


class ESClientTests(TestCase):
    def test_client_is_singleton(self):
        self.assertIs(get_es_client(), get_es_client())

    def test_client_connects(self):
        es = get_es_client()
        self.assertTrue(es.ping())

    def test_index_exists_and_has_docs(self):
        es = get_es_client()
        self.assertTrue(es.indices.exists(index=index_name()))
        count = es.count(index=index_name())["count"]
        self.assertGreater(count, 0)
