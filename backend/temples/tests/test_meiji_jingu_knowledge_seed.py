"""明治神宮の投入用ファイル（2026-11-26）と見どころの下書きデータの形を固定する。

本番には 2026-11-26 に投入済み（出典 id=155〜167、由緒・歴史 id=248〜250、すべて draft）。
記録: docs/audit/meiji-jingu-knowledge-import-2026-11-26.md
"""

import json
from pathlib import Path

from temples.models_highlights import ShrineHighlight
from temples.services.knowledge_seed import normalize_source_url, parse_seed

ROOT = Path(__file__).resolve().parents[3]
SEED_PATH = (
    ROOT / "backend" / "temples" / "data" / "knowledge_seeds" / "meiji_jingu_2026_11_26_seed.json"
)
HIGHLIGHTS_PATH = ROOT / "docs" / "audit" / "fixtures" / "meiji-jingu-highlights-2026-11-26.json"


def _seed():
    return parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))


def test_seed_schema_counts():
    seed = _seed()
    assert seed.errors == []
    assert len(seed.sources) == 14
    assert [(s.name_jp, s.address) for s in seed.shrines] == [
        ("明治神宮", "東京都渋谷区代々木神園町1-1")
    ]
    histories = seed.shrines[0].histories
    assert [h.title for h in histories] == [
        "人工の杜の造営",
        "戦災と復興",
        "御本殿以下36棟の重要文化財指定",
    ]
    assert seed.shrines[0].deities == []


def test_seed_histories_are_draft_without_confidence():
    """下書きで投入し、公開時に管理画面で確認状態・確信度を個別に設定する（2026-11-26 えつこさん決定）。"""
    for h in _seed().shrines[0].histories:
        assert h.history_type == "historical_event"
        assert h.verification_status == "draft"
        assert h.confidence == ""
        assert h.verified_at is None
        assert h.source_keys


def test_seed_reuses_existing_about_source_metadata():
    """既存の出典 id=1（明治神宮とは）を再利用するため、再利用判定の項目を既存と一致させている。"""
    about = _seed().sources["meiji-about"]
    assert about.url == "https://www.meijijingu.or.jp/about/"
    assert (
        about.publisher,
        about.verification_status,
        about.confidence,
        about.bibliography,
        about.language,
    ) == (
        "明治神宮",
        "source_confirmed",
        "high",
        "",
        "ja",
    )


def test_seed_source_types_one_value_per_url():
    """出典URLごとに1つの source_type（複数の種類を1つの値にしない）。"""
    seed = _seed()
    types = {key: s.source_type for key, s in seed.sources.items()}
    assert types["bunka-kunishitei-meiji-honden"] == "cultural_property"
    assert types["bunka-shingikai-218-gijiyoshi"] == "cultural_property"
    assert all(t in ("shrine_official", "cultural_property") for t in types.values())
    urls = [normalize_source_url(s.url) for s in seed.sources.values()]
    assert len(urls) == len(set(urls))


def test_highlight_fixture_matches_model_vocabulary_and_seed_sources():
    data = json.loads(HIGHLIGHTS_PATH.read_text(encoding="utf-8"))
    categories = {c for c, _ in ShrineHighlight.Category.choices}
    seed_urls = {normalize_source_url(s.url) for s in _seed().sources.values()}
    items = data["highlights"]
    assert [i["stable_key"] for i in items] == [
        "meiji-yoyogi",
        "meiji-gyoen",
        "meiji-kiyomasa-ido",
        "meiji-otorii",
        "meiji-honden",
        "meiji-houmotsuden",
    ]
    assert [i["sort_order"] for i in items] == list(range(1, 7))
    for i in items:
        assert i["category"] in categories
        assert i["publication_status"] == "draft"
        assert i["translation_ja"]["review_status"] == "draft"
        assert i["source_urls"]
        assert all(normalize_source_url(u) in seed_urls for u in i["source_urls"])
