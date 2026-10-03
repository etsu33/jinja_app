"""W0-DB04 G4 re-entry（建勲神社 / 大阪天満宮 / 大崎八幡宮）.

このモジュールは W0-DB04 G4 の3成果物を、凍結済み input に対して固定する。

- Candidate Master 行 wave0-019 / 021 / 025
- Base Seed 行（`shrines_seed_clean.json`）
- Knowledge Seed（`wave0_batch_04_seed.json`）

Fact 値・Source metadata は Evidence Backfill Freeze
（docs/audit/shrine-expansion-wave0-db04-evidence-backfill-freeze.md）、
採用座標は G1-G3 Preflight の G2 表
（docs/audit/shrine-expansion-wave0-db04-unified-gate-preflight.md）から直接読む。
テスト側に期待値を転記すると、転記が正本になってしまうため。

History の title / period_text と Source key は G4 re-entry 指示の機械的 build rule であり、
freeze の外側の値なのでここで固定する。

W0-DB04 の original membership は5社のまま保持する。
`wave0-020 水堂須佐男神社`（G2 HOLD_POSITION_REVIEW）と
`wave0-022 毛谷黒龍神社`（G3 MODEL_REVIEW_REMAINS）は
Candidate Master hydration / Base Seed / Knowledge Seed のいずれにも入らない。

goriyaku は G4 の対象外（goriyaku typed evidence storage は未解決の architecture task）。
本 batch は goriyaku / goriyaku_tags を Candidate Master にも Base Seed にも書かない。
"""

import hashlib
import io
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed

TESTS_DIR = Path(__file__).resolve().parent
TEMPLES_DIR = TESTS_DIR.parent
REPO_ROOT = TEMPLES_DIR.parents[1]

SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "wave0_batch_04_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
CANDIDATE_MASTER_PATH = TEMPLES_DIR / "data" / "shrine_expansion_candidate_master.json"
FREEZE_PATH = REPO_ROOT / "docs" / "audit" / "shrine-expansion-wave0-db04-evidence-backfill-freeze.md"
PREFLIGHT_PATH = REPO_ROOT / "docs" / "audit" / "shrine-expansion-wave0-db04-unified-gate-preflight.md"
SOURCE_PACKET_PATH = REPO_ROOT / "docs" / "audit" / "shrine-expansion-wave0-db04-source-packet-freeze.md"

EXECUTION_IDS = ["wave0-019", "wave0-021", "wave0-025"]
EXCLUDED = {
    "wave0-020": "水堂須佐男神社",  # G2 HOLD_POSITION_REVIEW
    "wave0-022": "毛谷黒龍神社",  # G3 MODEL_REVIEW_REMAINS
}
ORIGINAL_MEMBERSHIP = {
    "wave0-019": ("建勲神社", 54),
    "wave0-020": ("水堂須佐男神社", 56),
    "wave0-021": ("大阪天満宮", 59),
    "wave0-022": ("毛谷黒龍神社", 61),
    "wave0-025": ("大崎八幡宮", 70),
}

# goriyaku を除く hydration fields（goriyaku は G4 対象外の architecture HOLD）。
HYDRATION_FIELDS = {
    "official_name",
    "official_address",
    "official_source_type",
    "official_source_url",
    "verified_at",
    "latitude",
    "longitude",
}
GORIYAKU_FIELDS = {"goriyaku", "goriyaku_tags"}

# W0-DB04 追加前（develop@3f117df4）の Base Seed 117 行。既存行の不変を固定する。
EXISTING_BASE_ROW_COUNT = 117
EXISTING_BASE_ROWS_SHA256 = "e55dda6303e5be59b5c202f4ff3e130af9ce1e2147da5b3f04c63df06d9fe296"

EXPECTED_FACT_COUNTS = {
    "建勲神社": (2, 5),
    "大阪天満宮": (1, 3),
    "大崎八幡宮": (3, 4),
}

# G4 re-entry 指示の機械的 build rule。
EXPECTED_SOURCE_KEYS = {
    "wave0-019": "wave0-db04-kenkun-official",
    "wave0-021": "wave0-db04-osakatemmangu-official",
    "wave0-025": "wave0-db04-oosaki-hachiman-jinja-authority",
}
EXPECTED_HISTORY_TITLES = {
    "wave0-019": [
        "建勲神社創立の宣下",
        "神号「建勲」の宣下",
        "別格官幣社列格と船岡山の社地",
        "社殿造営と織田信忠卿の配祀",
        "現在地への移建",
    ],
    "wave0-021": ["大将軍社の鎮座", "菅原道真公の大将軍社参拝", "大阪天満宮の創建"],
    "wave0-025": [
        "成島八幡系統の系譜",
        "大崎八幡系統の系譜",
        "二系統の集結と現在地での造営",
        "慶長12年の遷座祭",
    ],
}
EXPECTED_PERIOD_TEXT = {
    "wave0-019": ["1869", "1870", "1875", "1880", "1910"],
    "wave0-021": ["650", "901", "949"],
    "wave0-025": ["", "", "", "慶長12年（1607）8月12日"],
}

# Source Packet Freeze が凍結した goriyaku source wording。G4 の書込先へ混入させない。
FROZEN_GORIYAKU_WORDING = (
    "国家安泰", "万民安堵", "大願成就", "難局突破", "産業指導", "災難除け",
    "試験合格", "就職成就", "学徳向上",
    "家内安全", "方除", "必勝", "身体堅固", "病気平癒", "開運厄除", "災難招福",
    "心願成就", "良縁", "安産", "旅行安全",
)


def _strip_code(cell):
    return cell.strip().strip("`")


def _load_freeze():
    """Evidence Backfill Freeze を候補ごとに読む。"""
    text = FREEZE_PATH.read_text(encoding="utf-8")
    metadata = dict(
        (key, value.strip())
        for key, value in re.findall(r"^(\S+(?: \S+)*?)\s+= (\S+)$", text.split("# 1.")[0], re.M)
    )
    entries = {}
    for match in re.finditer(r"^# \d+\. (.+)（(wave0-\d+)）$", text, re.M):
        name, cid = match.group(1), match.group(2)
        start = match.end()
        nxt = re.search(r"^# ", text[start:], re.M)
        block = text[start : start + nxt.start()] if nxt else text[start:]

        def field(key, block=block):
            return re.search(r"^%s\s+= (.+)$" % re.escape(key), block, re.M).group(1).strip()

        deities = []
        histories = []
        for row in re.findall(r"^\| (D\d+|H\d+) \|(.+)\|$", block, re.M):
            cells = [cell.strip() for cell in row[1].split("|")]
            if row[0].startswith("D"):
                deities.append(
                    {
                        "display_name": cells[0],
                        "role": next(_strip_code(c) for c in cells[1:] if c.startswith("`")),
                    }
                )
            else:
                histories.append(
                    {"period": cells[0], "history_type": _strip_code(cells[1]), "fact": cells[2]}
                )
        entries[cid] = {
            "name": name,
            "official_address": field("official_address"),
            "title": field("title"),
            "publisher": field("publisher"),
            "source_type": field("source_type"),
            "url": field("url"),
            "deities": deities,
            "histories": histories,
        }
    return metadata, entries


def _load_g2_positions():
    """G1-G3 Preflight の G2 PASS 表から採用座標を読む。"""
    text = PREFLIGHT_PATH.read_text(encoding="utf-8")
    positions = {}
    for cid in EXECUTION_IDS:
        row = re.search(r"^\| %s \| [^|]+ \| ([0-9.]+) \| ([0-9.]+) \|" % cid, text, re.M)
        positions[cid] = (float(row.group(1)), float(row.group(2)))
    return positions


def _load_candidates():
    master = json.loads(CANDIDATE_MASTER_PATH.read_text(encoding="utf-8"))
    return {row["candidate_id"]: row for row in master["candidates"]}


def _load_base_rows():
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _base_by_identity():
    return {(row["name_jp"], row["address"]): row for row in _load_base_rows()}


def _load_seed():
    return parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))


def _seed_shrine(seed, cid, freeze):
    return next(s for s in seed.shrines if s.name_jp == freeze[cid]["name"])


def _decide(seed, fact):
    return evidence_gate.decide_fact_usability(
        verification_status=fact.verification_status,
        confidence=fact.confidence,
        source_verification_statuses=[
            seed.sources[source_key].verification_status for source_key in fact.source_keys
        ],
    )


# --- scope ---------------------------------------------------------------------


def test_freeze_covers_exactly_the_three_execution_shrines():
    _metadata, freeze = _load_freeze()
    assert sorted(freeze) == EXECUTION_IDS
    for cid in EXCLUDED:
        assert cid not in freeze


def test_exactly_three_execution_shrines_are_built():
    _metadata, freeze = _load_freeze()
    candidates = _load_candidates()
    seed = _load_seed()

    hydrated = sorted(
        cid
        for cid, row in candidates.items()
        if row["build_batch"] == "W0-DB04" and HYDRATION_FIELDS <= row.keys()
    )
    assert hydrated == EXECUTION_IDS

    added = _load_base_rows()[EXISTING_BASE_ROW_COUNT:]
    expected_identities = [
        (freeze[cid]["name"], freeze[cid]["official_address"]) for cid in EXECUTION_IDS
    ]
    assert [(row["name_jp"], row["address"]) for row in added] == expected_identities
    assert [(s.name_jp, s.address) for s in seed.shrines] == expected_identities


def test_excluded_candidates_are_absent_from_base_and_knowledge():
    base_names = {row["name_jp"] for row in _load_base_rows()}
    raw_seed = SEED_PATH.read_text(encoding="utf-8")
    for name in EXCLUDED.values():
        assert name not in base_names
        assert name not in raw_seed


def test_excluded_candidate_rows_are_exactly_pinned():
    candidates = _load_candidates()
    for cid, (name, rank) in ORIGINAL_MEMBERSHIP.items():
        if cid not in EXCLUDED:
            continue
        assert candidates[cid] == {
            "candidate_id": cid,
            "candidate_name": name,
            "prefecture": {"wave0-020": "兵庫県", "wave0-022": "福井県"}[cid],
            "candidate_status": "BUILD_READY",
            "status_reason_code": "WAVE0_CORE_READY_CANDIDATE",
            "build_batch": "W0-DB04",
            "duplicate_status": "NEW",
            "discovery_sources": [
                {
                    "discovery_source": "Omairi 全国神社人気ランキング2026",
                    "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/3",
                    "discovery_rank": rank,
                    "captured_at": "2026-08-27",
                }
            ],
        }


# --- Candidate Master ----------------------------------------------------------


def test_original_w0_db04_membership_and_provenance_remain_intact():
    candidates = _load_candidates()
    members = {cid: row for cid, row in candidates.items() if row["build_batch"] == "W0-DB04"}

    assert set(members) == set(ORIGINAL_MEMBERSHIP)
    for cid, (name, rank) in ORIGINAL_MEMBERSHIP.items():
        row = members[cid]
        assert row["candidate_name"] == name
        assert row["candidate_status"] == "BUILD_READY"
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE"
        assert row["duplicate_status"] == "NEW"
        assert [source["discovery_rank"] for source in row["discovery_sources"]] == [rank]


def test_execution_candidates_are_hydrated_from_frozen_inputs_without_goriyaku():
    _metadata, freeze = _load_freeze()
    positions = _load_g2_positions()
    candidates = _load_candidates()

    for cid in EXECUTION_IDS:
        row = candidates[cid]
        frozen = freeze[cid]

        assert row["official_name"] == frozen["name"] == row["candidate_name"]
        assert row["official_address"] == frozen["official_address"]
        assert row["official_source_type"] == frozen["source_type"]
        assert row["official_source_url"] == frozen["url"]
        assert row["verified_at"] == "2026-10-03"
        assert (row["latitude"], row["longitude"]) == positions[cid]
        assert row["identity_status"] == "CONFIRMED"
        assert row["official_source_status"] == "CONFIRMED"
        assert not GORIYAKU_FIELDS & row.keys()

        # G4 は lifecycle を進めない。FACT_READY は Production 実測が要件の後続 Gate。
        assert "knowledge_status" not in row
        assert row["candidate_status"] == "BUILD_READY"
        assert row["build_batch"] == "W0-DB04"


# --- Base Seed -----------------------------------------------------------------


def test_existing_base_seed_rows_are_unchanged():
    rows = _load_base_rows()
    assert len(rows) == EXISTING_BASE_ROW_COUNT + len(EXECUTION_IDS)
    digest = hashlib.sha256(
        json.dumps(
            rows[:EXISTING_BASE_ROW_COUNT],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert digest == EXISTING_BASE_ROWS_SHA256


def test_base_seed_canonical_identities_are_unique():
    rows = _load_base_rows()
    identities = [(row["name_jp"], row["address"]) for row in rows]
    assert len(identities) == len(set(identities))
    added_names = {row["name_jp"] for row in rows[EXISTING_BASE_ROW_COUNT:]}
    existing_names = {row["name_jp"] for row in rows[:EXISTING_BASE_ROW_COUNT]}
    assert not added_names & existing_names


def test_base_seed_rows_match_candidate_master_and_g2():
    candidates = _load_candidates()
    positions = _load_g2_positions()
    base = _base_by_identity()

    for cid in EXECUTION_IDS:
        master_row = candidates[cid]
        base_row = base[(master_row["official_name"], master_row["official_address"])]
        assert (base_row["latitude"], base_row["longitude"]) == positions[cid]
        assert (base_row["latitude"], base_row["longitude"]) == (
            master_row["latitude"],
            master_row["longitude"],
        )
        assert base_row["location"] == {"lat": base_row["latitude"], "lng": base_row["longitude"]}


def test_new_base_rows_carry_no_goriyaku_or_inferred_fields():
    # `goriyaku` は Base Seed builder の required schema key のため空文字で持つ（自由メモ欄。evidenceではない）。
    # `goriyaku_tags` は optional key であり、key なし = M2M 同期対象外（taxonomy mapping を行わない）。
    for row in _load_base_rows()[EXISTING_BASE_ROW_COUNT:]:
        assert set(row) == {
            "name_jp",
            "address",
            "latitude",
            "longitude",
            "goriyaku",
            "kyusei",
            "astro_elements",
            "location",
        }
        assert row["goriyaku"] == ""
        assert row["kyusei"] is None
        assert row["astro_elements"] == []


def test_frozen_goriyaku_wording_is_not_written_anywhere_in_this_build():
    candidates = _load_candidates()
    surfaces = [SEED_PATH.read_text(encoding="utf-8")]
    surfaces += [json.dumps(row, ensure_ascii=False) for row in _load_base_rows()[EXISTING_BASE_ROW_COUNT:]]
    surfaces += [json.dumps(candidates[cid], ensure_ascii=False) for cid in EXECUTION_IDS]
    for word in FROZEN_GORIYAKU_WORDING:
        assert all(word not in surface for surface in surfaces), word


# --- Knowledge Seed ------------------------------------------------------------


def test_knowledge_seed_schema_and_counts():
    seed = _load_seed()

    assert seed.errors == []
    assert seed.schema_version == "1.0"
    assert len(seed.sources) == 3
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}
    assert set(by_name) == set(EXPECTED_FACT_COUNTS)
    for name, (deity_count, history_count) in EXPECTED_FACT_COUNTS.items():
        assert len(by_name[name].deities) == deity_count, name
        assert len(by_name[name].histories) == history_count, name
    assert sum(len(s.deities) for s in seed.shrines) == 6
    assert sum(len(s.histories) for s in seed.shrines) == 12


def test_knowledge_shrine_refs_match_base_seed_and_candidate_master():
    seed = _load_seed()
    base = _base_by_identity()
    candidates = _load_candidates()
    master_identities = {
        (candidates[cid]["official_name"], candidates[cid]["official_address"])
        for cid in EXECUTION_IDS
    }
    for shrine in seed.shrines:
        assert (shrine.name_jp, shrine.address) in base
        assert (shrine.name_jp, shrine.address) in master_identities


def test_sources_match_freeze_and_metadata():
    metadata, freeze = _load_freeze()
    seed = _load_seed()

    assert set(seed.sources) == set(EXPECTED_SOURCE_KEYS.values())
    for cid, key in EXPECTED_SOURCE_KEYS.items():
        source = seed.sources[key]
        frozen = freeze[cid]
        assert source.source_type == frozen["source_type"]
        assert source.title == frozen["title"]
        assert source.publisher == frozen["publisher"]
        assert source.url == frozen["url"]
        assert source.accessed_at.isoformat() == metadata["Source.accessed_at"]
        assert source.verified_at.isoformat() == metadata["Source.verified_at"]
        assert source.verification_status == metadata["verification_status"]
        assert source.confidence == metadata["confidence"]


def test_each_shrine_uses_only_its_own_source():
    _metadata, freeze = _load_freeze()
    seed = _load_seed()
    referenced = set()
    for cid, key in EXPECTED_SOURCE_KEYS.items():
        shrine = _seed_shrine(seed, cid, freeze)
        for fact in [*shrine.deities, *shrine.histories]:
            assert fact.source_keys == [key], (cid, fact)
            referenced.add(key)
    assert referenced == set(seed.sources)


def test_fact_metadata_matches_freeze_and_is_not_a_g2_timestamp():
    metadata, _freeze = _load_freeze()
    seed = _load_seed()
    for shrine in seed.shrines:
        for deity in shrine.deities:
            assert deity.verified_at.isoformat() == metadata["ShrineDeity.verified_at"]
        for history in shrine.histories:
            assert history.verified_at.isoformat() == metadata["ShrineHistory.verified_at"]
        for fact in [*shrine.deities, *shrine.histories]:
            assert fact.verification_status == metadata["verification_status"]
            assert fact.confidence == metadata["confidence"]
    # G2 Position verified_at（2026-10-03T17:..〜18:..）を Knowledge へ流用していない。
    assert not re.search(r"2026-10-03T1[78]:", SEED_PATH.read_text(encoding="utf-8"))


def test_deities_match_freeze_with_canonical_name_equal_to_display_name():
    _metadata, freeze = _load_freeze()
    seed = _load_seed()
    for cid in EXECUTION_IDS:
        shrine = _seed_shrine(seed, cid, freeze)
        assert [(d.display_name, d.role) for d in shrine.deities] == [
            (d["display_name"], d["role"]) for d in freeze[cid]["deities"]
        ]
        assert all(d.canonical_name == d.display_name for d in shrine.deities)


def test_histories_match_freeze_verbatim_and_build_rules():
    _metadata, freeze = _load_freeze()
    seed = _load_seed()
    for cid in EXECUTION_IDS:
        shrine = _seed_shrine(seed, cid, freeze)
        frozen = freeze[cid]["histories"]
        assert [h.history_type for h in shrine.histories] == [h["history_type"] for h in frozen]
        assert [h.content for h in shrine.histories] == [h["fact"] for h in frozen]
        assert [h.title for h in shrine.histories] == EXPECTED_HISTORY_TITLES[cid]
        assert [h.period_text for h in shrine.histories] == EXPECTED_PERIOD_TEXT[cid]
        assert all(h.event_date is None for h in shrine.histories)


def test_history_semantic_boundaries_are_preserved():
    _metadata, freeze = _load_freeze()
    seed = _load_seed()

    kenkun = _seed_shrine(seed, "wave0-019", freeze)
    founding = [h.period_text for h in kenkun.histories if h.history_type == "founding"]
    assert founding == ["1869"]
    assert next(h for h in kenkun.histories if h.period_text == "1910").history_type == "historical_event"
    assert [(d.display_name, d.role) for d in kenkun.deities] == [
        ("織田信長公", "primary"),
        ("織田信忠卿", "enshrined"),
    ]

    tenmangu = _seed_shrine(seed, "wave0-021", freeze)
    by_period = {h.period_text: h.history_type for h in tenmangu.histories}
    assert by_period == {"650": "regional_context", "901": "historical_event", "949": "founding"}
    assert all("大将軍" not in d.display_name for d in tenmangu.deities)

    oosaki = _seed_shrine(seed, "wave0-025", freeze)
    assert [h.history_type for h in oosaki.histories] == [
        "regional_context",
        "regional_context",
        "official_origin",
        "historical_event",
    ]
    assert not any(h.history_type == "founding" for h in oosaki.histories)
    assert oosaki.address == "宮城県仙台市青葉区八幡4-6-1"


def test_evidence_gate_accepts_all_eighteen_seed_facts():
    seed = _load_seed()
    decisions = [
        _decide(seed, fact)
        for shrine in seed.shrines
        for fact in [*shrine.deities, *shrine.histories]
    ]
    assert len(decisions) == 18
    assert all(decision.usable for decision in decisions)


def test_no_within_shrine_fact_duplicates():
    seed = _load_seed()
    for shrine in seed.shrines:
        names = [deity.display_name for deity in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp
        keys = [(history.history_type, history.title) for history in shrine.histories]
        assert len(keys) == len(set(keys)), shrine.name_jp


def test_no_collective_is_introduced():
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for block in raw["shrines"]:
        assert "collectives" not in block


def test_seed_parse_is_deterministic():
    raw = SEED_PATH.read_text(encoding="utf-8")
    first = parse_seed(json.loads(raw))
    second = parse_seed(json.loads(raw))
    assert repr(first) == repr(second)
    assert raw == json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n"


def test_source_packet_and_freeze_documents_exist():
    assert SOURCE_PACKET_PATH.exists()
    assert FREEZE_PATH.exists()
    assert "EVIDENCE_BACKFILL_FREEZE = PASS" in FREEZE_PATH.read_text(encoding="utf-8")


# --- DB: import / Evidence Gate / idempotency ----------------------------------


def _write_execution_base_seed(tmp_path):
    path = tmp_path / "w0_db04_base.json"
    path.write_text(
        json.dumps(_load_base_rows()[EXISTING_BASE_ROW_COUNT:], ensure_ascii=False),
        encoding="utf-8",
    )
    return path


@pytest.mark.django_db
def test_import_evidence_gate_and_idempotency(tmp_path):
    from temples.models import (
        GoriyakuTag,
        Shrine,
        ShrineDeity,
        ShrineHistory,
        ShrineKnowledgeSource,
    )

    tags_before = set(GoriyakuTag.objects.values_list("id", "name"))

    base_path = _write_execution_base_seed(tmp_path)
    out = io.StringIO()
    call_command("import_shrines_seed", source=str(base_path), stdout=out)
    assert "created=3 updated=0 skipped=0" in out.getvalue()

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=out)
    assert "sources created=3, deities created=6, histories created=12" in out.getvalue()

    targets = list(Shrine.objects.filter(name_jp__in=EXPECTED_FACT_COUNTS))
    assert len(targets) == 3
    decisions = []
    for shrine in targets:
        assert shrine.goriyaku_tags.count() == 0
        assert (shrine.goriyaku or "") == ""
        facts = [*ShrineDeity.objects.filter(shrine=shrine), *ShrineHistory.objects.filter(shrine=shrine)]
        expected = EXPECTED_FACT_COUNTS[shrine.name_jp]
        assert len(facts) == expected[0] + expected[1]
        for fact in facts:
            sources = list(fact.sources.all())
            assert sources
            assert {source.url for source in sources} <= set(
                ShrineKnowledgeSource.objects.values_list("url", flat=True)
            )
            decisions.append(
                evidence_gate.decide_fact_usability(
                    verification_status=fact.verification_status,
                    confidence=fact.confidence,
                    source_verification_statuses=[s.verification_status for s in sources],
                )
            )
    assert len(decisions) == 18
    assert all(decision.usable for decision in decisions)

    def snapshot():
        return (
            sorted(Shrine.objects.values_list("id", "name_jp", "address", "latitude", "longitude")),
            sorted(ShrineKnowledgeSource.objects.values_list("id", "url")),
            sorted(ShrineDeity.objects.values_list("id", "shrine_id", "display_name", "role")),
            sorted(ShrineHistory.objects.values_list("id", "shrine_id", "history_type", "title")),
            sorted(
                (h.id, sorted(h.sources.values_list("id", flat=True)))
                for h in ShrineHistory.objects.all()
            ),
            sorted(
                (d.id, sorted(d.sources.values_list("id", flat=True)))
                for d in ShrineDeity.objects.all()
            ),
        )

    before = snapshot()

    out = io.StringIO()
    call_command("import_shrines_seed", source=str(base_path), stdout=out)
    assert "created=0 updated=0 skipped=3" in out.getvalue()
    out = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=out)
    assert "sources created=0, deities created=0, histories created=0" in out.getvalue()

    assert snapshot() == before
    assert set(GoriyakuTag.objects.values_list("id", "name")) == tags_before
