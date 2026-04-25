

from __future__ import annotations

from django.core.management.base import BaseCommand

from temples.models import Shrine


DUPLICATE_CANDIDATE_SHRINES = [
    {
        "name_jp": "重複検証神社",
        "address": "東京都千代田区重複1-1-1",
        "latitude": 35.681236,
        "longitude": 139.767125,
    },
    {
        "name_jp": "重複検証神社",
        "address": "東京都中央区重複2-2-2",
        "latitude": 35.680959,
        "longitude": 139.767306,
    },
    {
        "name_jp": "重複検証神社（別宮）",
        "address": "東京都港区重複3-3-3",
        "latitude": 35.658581,
        "longitude": 139.745433,
    },
]


class Command(BaseCommand):
    help = "duplicate_candidate の実機確認用 Shrine seed を投入します。"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for row in DUPLICATE_CANDIDATE_SHRINES:
            shrine, created = Shrine.objects.update_or_create(
                name_jp=row["name_jp"],
                address=row["address"],
                defaults={
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "owner": None,
                },
            )

            if created:
                created_count += 1
                action = "created"
            else:
                updated_count += 1
                action = "updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{action}: id={shrine.id}, name={shrine.name_jp}, address={shrine.address}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"duplicate_candidate seed complete: created={created_count}, updated={updated_count}"
            )
        )
