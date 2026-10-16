"""nsrc-000009 赤城社 G4 Knowledge Seed static contract.

This file freezes only the repository Seed payload and parser-level contract.
Evidence Gate / validate / dry-run / apply / idempotency are handled by the next G4 execution step.
"""

import json
from pathlib import Path

from temples.services.knowledge_seed import parse_seed

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000009_seed.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市伊達乙48番地"
S2_KEY = "TOKAMACHI_REKIBUN_SHIRYOU"
S2_URL = "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf"
LEGACY_BIBLIOGRAPHY = "中魚沼郡誌上 p.398"
TARGET_LOCATOR = "中魚沼郡誌上 p.445"
FACT_VERIFIED_AT = "2026-10-16T00:00:00+09:00"

H1 = {
    "history_type": "historical_event",
    "title": "天明3年8月の創立記録",
    "content": "赤城社は天明3年8月に創立されたと記録されている。",
    "period_text": "天明3年8月",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": FACT_VERIFIED_AT,
    "source_keys": [S2_KEY],
    "citations": [{"source_key": S2_KEY, "locator_text": TARGET_LOCATOR}],
}

H2 = {
    "history_type": "historical_event",
    "title": "大正2年の改築記録",
    "content": "赤城社は大正2年に改築されたと記録されている。",
    "period_text": "大正2年",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": FACT_VERIFIED_AT,
    "source_keys": [S2_KEY],
    "citations": [{"source_key": S2_KEY, "locator_text": TARGET_LOCATOR}],
}


def _raw() -> dict:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def test_nsrc_000009_seed_parses_as_schema_1_3():
    raw = _raw()
    parsed = parse_seed(raw)

    assert parsed.errors == []
    assert parsed.schema_version == "1.3"
    assert len(parsed.sources) == 1
    assert len(parsed.shrines) == 1

    block = parsed.shrines[0]
    assert (block.name_jp, block.address) == (SHRINE_NAME, SHRINE_ADDRESS)
    assert len(block.deities) == 0
    assert len(block.histories) == 2
    assert list(block.collectives) == []
    assert list(block.source_facts) == []


def test_nsrc_000009_reuses_legacy_document_source_metadata():
    [source] = _raw()["sources"]

    assert source == {
        "key": S2_KEY,
        "source_type": "government",
        "title": "歴史文化基本構想 資料集",
        "publisher": "十日町市",
        "url": S2_URL,
        "bibliography": LEGACY_BIBLIOGRAPHY,
        "language": "ja",
        "accessed_at": "2026-10-13",
        "verified_at": "2026-10-13T00:00:00+09:00",
        "verification_status": "source_confirmed",
        "confidence": "high",
    }
    assert source["bibliography"] != TARGET_LOCATOR


def test_nsrc_000009_histories_and_fact_source_citations_are_frozen():
    raw = _raw()
    assert raw["shrines"][0]["histories"] == [H1, H2]

    parsed = parse_seed(raw)
    h1, h2 = parsed.shrines[0].histories

    for history in (h1, h2):
        assert history.source_keys == [S2_KEY]
        assert [(c.source_key, c.locator_text) for c in history.citations] == [
            (S2_KEY, TARGET_LOCATOR)
        ]
        assert history.event_date is None


def test_nsrc_000009_seed_contains_no_unauthorized_current_deity_or_derived_data():
    raw = _raw()
    shrine = raw["shrines"][0]
    text = SEED_PATH.read_text(encoding="utf-8")

    assert shrine["deities"] == []
    assert "大山祇命" not in text

    for key in ("goriyaku", "goriyaku_tags", "source_facts", "collectives", "history_theme"):
        assert key not in raw
        assert key not in shrine
