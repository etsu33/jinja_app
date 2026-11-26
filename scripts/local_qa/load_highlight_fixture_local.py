"""見どころの下書きデータを、手元（ローカル）のDBにだけ入れて、画面の見た目を確かめるためのスクリプト。

本番DBには絶対に使わない。接続先が手元のDB（localhost / 127.0.0.1 / ::1 / ソケット）で
なければ、何もせずに止まる。本番の公開条件（highlight_publication）は変えない。
ORM の save() を通すので、モデルの検証（full_clean）もそのまま効く。

使い方（backend ディレクトリで。本番の DATABASE_URL を読み込んでいない新しいターミナルで）:
    python ../scripts/local_qa/load_highlight_fixture_local.py <fixture.json> [--dry-run]
    python ../scripts/local_qa/load_highlight_fixture_local.py <fixture.json> --publish-for-local-qa
        [--history-content-json <h1.json>]

--dry-run               何が作られるかを表示するだけ（書き込まない）
--publish-for-local-qa  手元のDBでだけ、見どころを公開・日本語の文を承認にし、
                        この神社の下書きの由緒・歴史を source_confirmed にして、詳細ページに出る状態にする
--history-content-json  手元のDBでだけ、既存の由緒・歴史の本文を差し替える
                        （形式: [{"history_type": ..., "title": ..., "content": ..., "source_urls": [...]}]）

前提: 先に同じ手元のDBへ import_shrine_knowledge で投入用ファイル（出典・由緒・歴史）を入れておくこと。
出典はURLで、由緒・歴史は「種類＋題名」で探す。見つからなければ止まる（推測で作らない）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")

LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}


def _assert_local_database() -> None:
    from django.conf import settings

    db = settings.DATABASES["default"]
    host = str(db.get("HOST") or "")
    if host.startswith("/"):  # Unix ソケット（手元のDB）
        return
    if host not in LOCAL_HOSTS:
        raise SystemExit(
            "STOP: 接続先が手元のDBではありません。本番の DATABASE_URL を読み込んでいない"
            "ターミナルで実行してください（このスクリプトは手元のDB専用です）。"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish-for-local-qa", action="store_true")
    parser.add_argument("--history-content-json")
    args = parser.parse_args()

    import django

    django.setup()
    _assert_local_database()

    from django.db import transaction
    from django.utils import timezone
    from temples.models import Shrine, ShrineHistory, ShrineKnowledgeSource
    from temples.models_highlights import (
        ShrineHighlight,
        ShrineHighlightHistory,
        ShrineHighlightSource,
        ShrineHighlightTranslation,
    )
    from temples.services import highlight_publication
    from temples.services.knowledge_seed import normalize_source_url

    data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    ref = data["shrine_ref"]
    shrines = list(Shrine.objects.filter(name_jp=ref["name_jp"], address=ref["address"]))
    if len(shrines) != 1:
        raise SystemExit(f"STOP: 神社が1件に決まりません（{len(shrines)}件）: {ref}")
    shrine = shrines[0]

    def find_source(url: str) -> ShrineKnowledgeSource:
        target = normalize_source_url(url)
        hits = [
            s
            for s in ShrineKnowledgeSource.objects.exclude(url="")
            if normalize_source_url(s.url) == target
        ]
        if len(hits) != 1:
            raise SystemExit(f"STOP: 出典が1件に決まりません（{len(hits)}件）: {url}")
        return hits[0]

    def find_history(history_type: str, title: str) -> ShrineHistory:
        hits = list(
            ShrineHistory.objects.filter(shrine=shrine, history_type=history_type, title=title)
        )
        if len(hits) != 1:
            raise SystemExit(
                f"STOP: 由緒・歴史が1件に決まりません（{len(hits)}件）: {history_type} {title}"
            )
        return hits[0]

    # 先に全部を解決してから書く（途中で止まって半端に入るのを防ぐ）
    plan = []
    for item in data["highlights"]:
        if ShrineHighlight.objects.filter(stable_key=item["stable_key"]).exists():
            raise SystemExit(
                f"STOP: stable_key がすでにあります（上書きしない）: {item['stable_key']}"
            )
        sources = [find_source(u) for u in item["source_urls"]]
        histories = [find_history(h["history_type"], h["title"]) for h in item["histories"]]
        plan.append((item, sources, histories))

    history_updates = []
    if args.history_content_json:
        for h in json.loads(Path(args.history_content_json).read_text(encoding="utf-8")):
            history_updates.append(
                (
                    find_history(h["history_type"], h["title"]),
                    h["content"],
                    [find_source(u) for u in h.get("source_urls", [])],
                )
            )

    print(f"shrine: id={shrine.pk} {shrine.name_jp}")
    for item, sources, histories in plan:
        print(
            f"CREATE highlight {item['stable_key']} ({item['category']}, sort={item['sort_order']}) "
            f"sources={[s.pk for s in sources]} histories={[h.pk for h in histories]}"
        )
    for history, _content, add_sources in history_updates:
        print(
            f"UPDATE history id={history.pk} {history.title} (+sources {[s.pk for s in add_sources]})"
        )
    if args.dry_run:
        print("dry-run: 書き込みなし")
        return 0

    now = timezone.now()
    with transaction.atomic():
        for history, content, add_sources in history_updates:
            history.content = content
            history.verified_at = now
            history.save()
            history.sources.add(*add_sources)

        for item, sources, histories in plan:
            highlight = ShrineHighlight(
                shrine=shrine,
                stable_key=item["stable_key"],
                category=item["category"],
                sort_order=item["sort_order"],
                verification_status=item["verification_status"],
                verified_at=item["verified_at"],
                confidence=item["confidence"],
                publication_status="published"
                if args.publish_for_local_qa
                else item["publication_status"],
            )
            highlight.save()
            t = item["translation_ja"]
            approved = args.publish_for_local_qa
            ShrineHighlightTranslation(
                highlight=highlight,
                language_code="ja",
                name=t["name"],
                description=t["description"],
                historical_connection=t["historical_connection"],
                location_hint=t["location_hint"],
                review_status="approved" if approved else t["review_status"],
                reviewed_at=now if approved else None,
            ).save()
            for s in sources:
                ShrineHighlightSource(highlight=highlight, source=s).save()
            for h in histories:
                ShrineHighlightHistory(highlight=highlight, history=h, shrine=shrine).save()

        if args.publish_for_local_qa:
            # 手元のDBでだけ：この神社の下書きの由緒・歴史を確認済みにして、詳細ページに出す
            for h in ShrineHistory.objects.filter(shrine=shrine, verification_status="draft"):
                h.verification_status = "source_confirmed"
                h.verified_at = now
                h.save()
                print(f"LOCAL ONLY: history id={h.pk} {h.title} -> source_confirmed")

    for highlight in ShrineHighlight.objects.filter(shrine=shrine).prefetch_related(
        "translations", "source_links__source"
    ):
        decision = highlight_publication.decide_for_highlight(highlight, "ja")
        print(
            f"表示条件 {highlight.stable_key}: {'ja: OK' if decision.displayable else decision.reasons}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
