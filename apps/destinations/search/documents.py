"""
Elasticsearch index definition for destinations.

This is the ES-side counterpart to models.py — Postgres and ES are two
separate schemas describing the same data, kept in sync by the seed
command (and later, signal-based indexing on writes).
"""

INDEX_NAME = "destinations"

INDEX_BODY = {
    "settings": {
        "index": {
            "max_ngram_diff": 18,
        },
        "analysis": {
            "normalizer": {
                "destination_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase", "asciifolding"],
                }
            },
            "filter": {
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "preserve_original": True,
                }
            },
            "analyzer": {
                # Used when INDEXING city/country — expands each token into
                # its prefix ngrams. asciifolding strips accents so
                # "München"/"munchen" are indexed identically.
                "autocomplete_index_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "edge_ngram_filter"],
                },
                # Used when SEARCHING — deliberately NOT ngram'd, so a
                # search for "san" matches indexed ngram "san" exactly,
                # instead of exploding the query into ngrams too.
                "autocomplete_search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
                "standard_text_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
            },
        },
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
                    "raw": {"type": "keyword", "normalizer": "destination_normalizer"},
                    "standard": {"type": "text", "analyzer": "standard_text_analyzer"},
                },
            },
            "country": {
                "type": "text",
                "analyzer": "autocomplete_index_analyzer",
                "search_analyzer": "autocomplete_search_analyzer",
                "fields": {
                    "raw": {"type": "keyword", "normalizer": "destination_normalizer"},
                    "standard": {"type": "text", "analyzer": "standard_text_analyzer"},
                },
            },
            "population": {"type": "integer"},
            "location": {"type": "geo_point"},
        }
    },
}
