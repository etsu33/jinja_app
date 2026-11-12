"""英語の特徴語の当てはめ（シードJSON）を ShrineFeatureWordEn に取り込む。

使い方:
    python manage.py import_feature_words_en              # 取り込む
    python manage.py import_feature_words_en --dry-run    # 何が入るかだけ表示（書き込まない）
    python manage.py import_feature_words_en --strict     # 結びつけられない神社があれば失敗にする

決まり:
- 神社は名前＋住所で書き、resolve_shrine（知識データの取り込みと同じ）で本番の神社に結びつける。
  結びつけられない神社は推測で入れず、ERROR として表示して飛ばす。
- 結びつけた神社は、その神社の行をすべて入れ替える（シードJSONの内容がそのまま入る）。
  シードJSONに無い神社の行は触らない。
- 語のIDが語彙（FEATURE_WORDS）に無ければ、その神社は取り込まない。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from temples.domain.feature_words_en import FEATURE_WORDS
from temples.models import ShrineFeatureWordEn
from temples.services.knowledge_seed import resolve_shrine

DEFAULT_SEED = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "feature_words_en"
    / "shrine_feature_words_en_seed.json"
)
KNOWN_WORD_IDS = {w.id for w in FEATURE_WORDS}


class Command(BaseCommand):
    help = "英語の特徴語の当てはめ（シードJSON）を取り込む"

    def add_arguments(self, parser):
        parser.add_argument("seed_path", nargs="?", default=str(DEFAULT_SEED))
        parser.add_argument("--dry-run", action="store_true", help="書き込まずに内容だけ表示する")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="結びつけられない神社や不正な語があれば失敗にする",
        )

    def handle(self, *args, **options):
        seed_path = Path(options["seed_path"])
        if not seed_path.exists():
            raise CommandError(f"seed not found: {seed_path}")
        with seed_path.open(encoding="utf-8") as f:
            seed = json.load(f)

        vocabulary_version = str(seed.get("vocabulary_version") or "").strip()
        if not vocabulary_version:
            raise CommandError("vocabulary_version is empty")

        dry_run = options["dry_run"]
        problems: List[str] = []
        imported_shrines = 0
        imported_rows = 0

        for block in seed.get("shrines", []):
            ref = block.get("shrine_ref") or {}
            name_jp = ref.get("name_jp", "")
            features: List[Dict[str, Any]] = block.get("features") or []

            unknown = sorted({f.get("word_id") for f in features} - KNOWN_WORD_IDS)
            if unknown:
                problems.append(f"{name_jp}: unknown word_id {unknown}")
                self.stderr.write(
                    f"[import_feature_words_en] ERROR shrine={name_jp!r} unknown word_id={unknown}"
                )
                continue

            result = resolve_shrine(name_jp, ref.get("address", ""))
            if result.shrine is None:
                problems.append(f"{name_jp}: {result.status}")
                self.stderr.write(
                    f"[import_feature_words_en] ERROR shrine={name_jp!r} {result.status} ({result.detail})"
                )
                continue

            rows = [
                ShrineFeatureWordEn(
                    shrine_id=result.shrine.pk,
                    word_id=f["word_id"],
                    vocabulary_version=vocabulary_version,
                    evidence_quote=f["evidence_quote"],
                    note=f.get("note") or "",
                    source_url=f["source_url"],
                    source_type=f.get("source_type") or "",
                    checked_on=date.fromisoformat(f["checked_on"]),
                )
                for f in features
            ]

            if not dry_run:
                with transaction.atomic():
                    ShrineFeatureWordEn.objects.filter(shrine_id=result.shrine.pk).delete()
                    ShrineFeatureWordEn.objects.bulk_create(rows)

            imported_shrines += 1
            imported_rows += len(rows)
            self.stdout.write(
                f"[import_feature_words_en] {'PLAN' if dry_run else 'OK'} shrine={name_jp!r} "
                f"shrine_id={result.shrine.pk} rows={len(rows)}"
            )

        self.stdout.write(
            f"[import_feature_words_en] done dry_run={dry_run} shrines={imported_shrines} "
            f"rows={imported_rows} problems={len(problems)}"
        )
        if problems and options["strict"]:
            raise CommandError("; ".join(problems))
