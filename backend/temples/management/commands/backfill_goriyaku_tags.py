from __future__ import annotations

import re
from typing import Iterable

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from temples.models import GoriyakuTag, Shrine


_SPLIT_RE = re.compile(r"[、,／/・\|\n\r\t]+")  # "縁結び・厄除け・交通安全" 対応


def parse_goriyaku(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in _SPLIT_RE.split(raw)]
    # 空と重複を落とす（順序は維持）
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def infer_visit_style_tags(shrine: Shrine) -> list[str]:
    text = " ".join(
        [
            shrine.name_jp or "",
            shrine.goriyaku or "",
            shrine.sajin or "",
            shrine.description or "",
            shrine.address or "",
        ]
    )

    tags: list[str] = []

    def add(tag: str) -> None:
        if tag not in tags:
            tags.append(tag)

    if any(word in text for word in ["森", "山", "自然", "滝", "湖", "木", "緑"]):
        add("nature")

    if any(word in text for word in ["癒", "静", "安", "清", "休", "疲", "厄除", "浄化"]):
        add("quiet")
        add("reset")

    if any(word in text for word in ["金運", "商売", "仕事", "出世", "開運", "勝負", "成功"]):
        add("business")
        add("classic")

    if any(word in text for word in ["縁結", "恋", "夫婦", "結婚"]):
        add("classic")

    if any(word in text for word in ["東京", "駅", "区", "市", "町"]):
        add("urban")

    if not tags:
        add("classic")

    return tags


class Command(BaseCommand):
    help = "Split Shrine.goriyaku and backfill Shrine.goriyaku_tags (M2M)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Don't write changes.")
        parser.add_argument("--force", action="store_true", help="Also process shrines that already have goriyaku_tags.")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of shrines processed (0 = no limit).")
        parser.add_argument(
            "--with-visit-style",
            action="store_true",
            help="Also backfill Shrine.visit_style_tags when empty.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run: bool = bool(opts["dry_run"])
        force: bool = bool(opts["force"])
        limit: int = int(opts["limit"] or 0)
        with_visit_style: bool = bool(opts["with_visit_style"])

        qs = (
            Shrine.objects.exclude(goriyaku__isnull=True)
            .exclude(goriyaku__exact="")
            .order_by("id")
            .prefetch_related("goriyaku_tags")
        )
        if not force:
            qs = qs.annotate(gcnt=Count("goriyaku_tags"))
            if not force:
                qs = qs.filter(gcnt=0)
        if limit > 0:
            qs = qs[:limit]

        total = 0
        updated = 0
        created_tags = 0
        added_links = 0
        visit_style_total = 0
        visit_style_updated = 0

        for s in qs:
            total += 1
            names = parse_goriyaku(s.goriyaku or "")
            if not names:
                continue

            # force=false の時は基本 empty 対象だが、念のため差分だけ add する
            existing = {t.name for t in s.goriyaku_tags.all()}

            to_add: list[GoriyakuTag] = []
            for name in names:
                if name in existing:
                    continue
                tag, created = GoriyakuTag.objects.get_or_create(name=name)
                if created:
                    created_tags += 1
                to_add.append(tag)

            if not to_add:
                continue

            updated += 1
            added_links += len(to_add)

            if not dry_run:
                s.goriyaku_tags.add(*to_add)

        if with_visit_style:
            visit_qs = Shrine.objects.order_by("id")
            if limit > 0:
                visit_qs = visit_qs[:limit]

            for shrine in visit_qs:
                visit_style_total += 1
                if shrine.visit_style_tags:
                    continue

                tags = infer_visit_style_tags(shrine)
                if not tags:
                    continue

                visit_style_updated += 1
                if not dry_run:
                    shrine.visit_style_tags = tags
                    shrine.save(update_fields=["visit_style_tags", "updated_at"])

        self.stdout.write(
            f"[backfill_goriyaku_tags] dry_run={dry_run} force={force} "
            f"total={total} updated={updated} created_tags={created_tags} added_links={added_links} "
            f"with_visit_style={with_visit_style} visit_style_total={visit_style_total} "
            f"visit_style_updated={visit_style_updated}"
        )

        if dry_run:
            # transaction.atomic なので dry-run でも念のため rollback したいなら例外で落とす手もあるが、
            # 今回は write を避けてるので不要。
            pass
