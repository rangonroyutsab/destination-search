"""
Seed the destinations dataset from a CSV into Postgres and Elasticsearch.

Usage (run ONCE, manually, after the stack is up):

    docker compose exec web python manage.py seed_destinations data/cities.csv

or via the dedicated one-off compose service:

    docker compose --profile seed run --rm seed

Expected CSV columns: country, city, population, latitude, longitude

Idempotency: by default the command refuses to run if the Destination
table already has rows, so re-running (or an accidental second run)
is a no-op instead of duplicating 1M+ rows. Pass --force to wipe and
reseed anyway.
"""

import csv

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from apps.destinations.models import Destination
from apps.destinations.search.documents import INDEX_BODY, INDEX_NAME

BATCH_SIZE = 15000
ES_INDEX = INDEX_NAME


class Command(BaseCommand):
    help = "Seed destinations from a CSV file into Postgres and Elasticsearch."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument(
            "--force",
            action="store_true",
            help="Wipe existing rows/index and reseed even if data already exists.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        force = options["force"]

        if not self._check_and_clear_data(force):
            return

        es = self._setup_elasticsearch(force)

        try:
            total, skipped = self._process_csv(csv_path, es)
            self._restore_elasticsearch(es)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. Seeded {total} destinations. Skipped {skipped} malformed rows."
                )
            )
        except FileNotFoundError as exc:
            raise CommandError(f"CSV not found: {csv_path}") from exc

    def _check_and_clear_data(self, force):
        already_seeded = Destination.objects.exists()
        if already_seeded and not force:
            self.stdout.write(
                self.style.WARNING(
                    "Destination table already has data — skipping. "
                    "Pass --force to wipe and reseed."
                )
            )
            return False

        if already_seeded and force:
            self.stdout.write("Force flag set — clearing existing data...")
            Destination.objects.all().delete()
            
        return True

    def _setup_elasticsearch(self, force):
        es = Elasticsearch(self._es_url(), request_timeout=60)
        if force:
            es.indices.delete(index=ES_INDEX, ignore_unavailable=True)
        if not es.indices.exists(index=ES_INDEX):
            es.indices.create(index=ES_INDEX, body=INDEX_BODY)

        # Optimize for bulk indexing: disable refresh and replicas
        es.indices.put_settings(
            index=ES_INDEX,
            settings={
                "index": {
                    "refresh_interval": "-1",
                    "number_of_replicas": 0,
                }
            },
        )
        return es

    def _restore_elasticsearch(self, es):
        es.indices.put_settings(
            index=ES_INDEX,
            settings={
                "index": {
                    "refresh_interval": "1s",
                }
            },
        )

    def _process_csv(self, csv_path, es):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Normalize header casing (e.g. "Country,City,Population,Latitude,Longitude")
            # so lookups below work regardless of how a given CSV capitalizes columns.
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
            pg_batch, es_batch, total, skipped = [], [], 0, 0

            for line_num, row in enumerate(reader, start=2):  # header is line 1
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                    population = int(row["population"]) if row.get("population") else 0
                    city = row["city"].strip()
                    country = row["country"].strip()
                    if not city or not country:
                        raise ValueError("empty city/country")
                except (KeyError, TypeError, ValueError) as exc:
                    skipped += 1
                    self.stderr.write(f"  skipping line {line_num}: {exc} ({row})")
                    continue

                pg_batch.append(
                    Destination(
                        city=city,
                        country=country,
                        population=population,
                        location=Point(lon, lat, srid=4326),
                    )
                )
                es_batch.append(
                    {
                        "_index": ES_INDEX,
                        "_source": {
                            "city": city,
                            "country": country,
                            "population": population,
                            "location": {"lat": lat, "lon": lon},
                        },
                    }
                )

                if len(pg_batch) >= BATCH_SIZE:
                    total += self._flush(pg_batch, es_batch, es)
                    self.stdout.write(f"  ...{total} rows seeded")

            if pg_batch:
                total += self._flush(pg_batch, es_batch, es)

            return total, skipped

    @transaction.atomic
    def _flush(self, pg_batch, es_batch, es):
        Destination.objects.bulk_create(pg_batch, batch_size=BATCH_SIZE)
        bulk(es, es_batch, request_timeout=60)
        count = len(pg_batch)
        pg_batch.clear()
        es_batch.clear()
        return count

    @staticmethod
    def _es_url():
        import os

        return os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
