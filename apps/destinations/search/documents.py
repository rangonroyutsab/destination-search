"""
Elasticsearch index definition for destinations.

This is the ES-side counterpart to models.py — Postgres and ES are two
separate schemas describing the same data, kept in sync by the seed
command (and later, signal-based indexing on writes).
"""

INDEX_NAME = "destinations"

INDEX_BODY = {
    "settings": {
        "analysis": {
            "filter": {
                # Builds "san" -> s, sa, san as indexed tokens, so a partial
                # prefix typed by the user matches without needing a
                # wildcard query (which is slow at 1M+ docs).
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 20,
                }
            },
            "analyzer": {
                # Used when INDEXING city/country — expands each token into
                # its prefix ngrams.
                "autocomplete_index_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "edge_ngram_filter"],
                },
                # Used when SEARCHING — deliberately NOT ngram'd, so a
                # search for "san" matches indexed ngram "san" exactly,
                # instead of exploding the query into ngrams too.
                "autocomplete_search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"],
                },
            },
        }
    },
    "mappings": {
        "properties": {
            "city": {
                "type": "text",
                "analyzer": "autocomplete_index_analyzer",
                "search_analyzer": "autocomplete_search_analyzer",
                "fields": {
                    # Untouched exact/keyword form — for exact-match
                    # boosting and sorting, separate from the ngram field.
                    "raw": {"type": "keyword"},
                },
            },
            "country": {
                "type": "text",
                "analyzer": "autocomplete_index_analyzer",
                "search_analyzer": "autocomplete_search_analyzer",
                "fields": {
                    "raw": {"type": "keyword"},
                },
            },
            "population": {"type": "integer"},
            "location": {"type": "geo_point"},
        }
    },
}
