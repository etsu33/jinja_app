# temples/management/commands/debug_concierge_candidates.py
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count

from temples.models import PlaceCache, PlacesSeed, Shrine


class Command(BaseCommand):
    help = "Print read-only counts useful for debugging concierge candidates."

    def _safe_count(self, model) -> int | str:
        table_name = model._meta.db_table
        existing_tables = connection.introspection.table_names()
        if table_name not in existing_tables:
            return "missing_table"
        return model.objects.count()

    def handle(self, *args, **options):
        shrine_qs = Shrine.objects.all()

        shrine_total = shrine_qs.count()
        shrine_kind_counts = shrine_qs.values("kind").annotate(total=Count("id")).order_by("kind")
        shrine_with_location = shrine_qs.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        ).count()
        shrine_with_visit_style_tags = shrine_qs.exclude(visit_style_tags=[]).count()
        shrine_with_goriyaku_tags = shrine_qs.filter(goriyaku_tags__isnull=False).distinct().count()

        self.stdout.write("Concierge candidate debug counts")
        self.stdout.write(f"Shrine total: {shrine_total}")
        self.stdout.write("Shrine by kind:")
        for row in shrine_kind_counts:
            self.stdout.write(f"  {row['kind'] or '(blank)'}: {row['total']}")
        self.stdout.write(f"Shrine with latitude/longitude: {shrine_with_location}")
        self.stdout.write(f"Shrine with visit_style_tags: {shrine_with_visit_style_tags}")
        self.stdout.write(f"Shrine with goriyaku_tags: {shrine_with_goriyaku_tags}")
        self.stdout.write(f"PlaceCache total: {self._safe_count(PlaceCache)}")
        self.stdout.write(f"PlacesSeed total: {self._safe_count(PlacesSeed)}")
