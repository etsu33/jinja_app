"""W0-DB04 G4 re-entry eligible subset（建勲神社 / 大阪天満宮 / 大崎八幡宮）の Base Seed.

このモジュールは W0-DB04 G4 re-entry の Base Seed 追加行を、凍結文書と Candidate Master に対して固定する。

- Base Seed 行（`shrines_seed_clean.json`）: wave0-019 / 021 / 025 の3行を末尾に追加

座標は Source Packet Freeze、住所は Evidence Backfill Freeze の markdown から直接読み出して比較する。
テスト側に期待値を転記すると、転記が正本になってしまうため。

W0-DB04 の original membership は5社のまま保持する。
`wave0-020 水堂須佐男神社`（G2 HOLD_POSITION_REVIEW）と `wave0-022 毛谷黒龍神社`
（G3 MODEL_REVIEW_REMAINS）は Base Seed に入らない。

goriyaku は HOLD_MODEL_BOUNDARY（goriyaku typed evidence / taxonomy mapping は未解決）であり、
Mother Ship decision により既存の builder 互換表現を使う:

    goriyaku      = ""（既存 Base Seed 行と同じ空文字列）
    goriyaku_tags = key ごと省略（builder / importer の optional key。key なし = 未管理）

wave0-021 の address は Source 表記「大阪市北区天神橋2丁目1番8号」に「大阪府」を前置した
Candidate Master canonical address。Base Seed の prefecture 導出が都道府県始まりを要求するための
W0-DB04 Mother Ship decision（wave0-021 限定）であり、global な正規化ルールではない。

決定論的 rebuild（byte 一致・2回目 build の差分ゼロ）と全 validation gate は
`test_base_shrine_seed_build_contract.py` が Base Seed 全体に対して固定する。
"""

import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command

TESTS_DIR = Path(__file__).resolve().parent
TEMPLES_DIR = TESTS_DIR.parent
REPO_ROOT = TEMPLES_DIR.parents[1]

BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
CANDIDATE_MASTER_PATH = TEMPLES_DIR / "data" / "shrine_expansion_candidate_master.json"
BUILDER_PATH = REPO_ROOT / "scripts" / "build_base_shrine_seed.py"
SOURCE_PACKET_PATH = REPO_ROOT / "docs" / "audit" / "shrine-expansion-wave0-db04-source-packet-freeze.md"
EVIDENCE_BACKFILL_PATH = (
    REPO_ROOT / "docs" / "audit" / "shrine-expansion-wave0-db04-evidence-backfill-freeze.md"
)

EXECUTION_IDS = ["wave0-019", "wave0-021", "wave0-025"]
EXCLUDED = {
    "wave0-020": "水堂須佐男神社",
    "wave0-022": "毛谷黒龍神社",
}
EXPECTED_PREFECTURES = {
    "wave0-019": "京都府",
    "wave0-021": "大阪府",
    "wave0-025": "宮城県",
}

# wave0-021 だけに適用する W0-DB04 Mother Ship decision（Source 表記への都道府県前置）。
NORMALIZED_PREFECTURE_PREFIX = {"wave0-021": "大阪府"}

# W0-DB04 追加前（W0-DB03 追加後）の Base Seed 117 行。既存行の不変を固定する。
EXISTING_BASE_ROW_COUNT = 117
EXISTING_BASE_ROWS_SHA256 = "e55dda6303e5be59b5c202f4ff3e130af9ce1e2147da5b3f04c63df06d9fe296"
# W0-DB04の3行が占めるcohort終端。Base Seed全体の最終件数ではない。
W0_DB04_BASE_ROW_END = EXISTING_BASE_ROW_COUNT + len(EXECUTION_IDS)

# goriyaku の既存 builder 互換な空表現。
EMPTY_GORIYAKU = ""


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_base_shrine_seed", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _split_candidate_sections(path):
    """`# N. 名称（wave0-0xx）` 見出しごとに markdown を分割する。"""
    text = path.read_text(encoding="utf-8")
    sections = {}
    for block in re.split(r"^# \d+\. ", text, flags=re.M)[1:]:
        match = re.match(r".+?（(wave0-\d{3})）", block)
        if match:
            sections[match.group(1)] = block
    return sections


def _field(block, name):
    return re.search(r"^%s\s+= (.+)$" % re.escape(name), block, re.M).group(1).strip()


def _load_frozen():
    """凍結座標（Source Packet）と Source 表記の住所（Evidence Backfill）を読む。"""
    packet = _split_candidate_sections(SOURCE_PACKET_PATH)
    backfill = _split_candidate_sections(EVIDENCE_BACKFILL_PATH)
    frozen = {}
    for cid in EXECUTION_IDS:
        frozen[cid] = {
            "position_status": _field(packet[cid], "position_status"),
            # 文字列のまま保持し、比較時に float 化する。
            "latitude": _field(packet[cid], "latitude"),
            "longitude": _field(packet[cid], "longitude"),
            "source_attested_address": _field(backfill[cid], "official_address"),
        }
    return frozen


def _load_candidates():
    master = json.loads(CANDIDATE_MASTER_PATH.read_text(encoding="utf-8"))
    return {row["candidate_id"]: row for row in master["candidates"]}


def _load_base_rows():
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _added_rows():
    return _load_base_rows()[EXISTING_BASE_ROW_COUNT:W0_DB04_BASE_ROW_END]


def _added_by_candidate():
    candidates = _load_candidates()
    by_identity = {(row["name_jp"], row["address"]): row for row in _added_rows()}
    return {
        cid: by_identity[(candidates[cid]["official_name"], candidates[cid]["official_address"])]
        for cid in EXECUTION_IDS
    }


# --- scope ---------------------------------------------------------------------


def test_frozen_inputs_cover_exactly_the_three_execution_shrines():
    packet = _split_candidate_sections(SOURCE_PACKET_PATH)
    backfill = _split_candidate_sections(EVIDENCE_BACKFILL_PATH)
    assert sorted(packet) == EXECUTION_IDS
    assert sorted(backfill) == EXECUTION_IDS
    assert all(entry["position_status"] == "PASS" for entry in _load_frozen().values())


def test_exactly_three_rows_are_appended_in_execution_order():
    rows = _load_base_rows()
    candidates = _load_candidates()

    assert len(rows) >= W0_DB04_BASE_ROW_END
    assert len(_added_rows()) == len(EXECUTION_IDS)
    assert [(row["name_jp"], row["address"]) for row in _added_rows()] == [
        (candidates[cid]["official_name"], candidates[cid]["official_address"])
        for cid in EXECUTION_IDS
    ]


def test_excluded_candidates_are_absent_from_base_seed():
    names = {row["name_jp"] for row in _load_base_rows()}
    candidates = _load_candidates()

    for cid, name in EXCLUDED.items():
        assert candidates[cid]["candidate_name"] == name
        assert candidates[cid]["build_batch"] == "W0-DB04"
        assert name not in names, cid


def test_no_other_build_ready_candidate_is_added():
    candidates = _load_candidates()
    added_names = {row["name_jp"] for row in _added_rows()}
    assert added_names == {candidates[cid]["candidate_name"] for cid in EXECUTION_IDS}


# --- Candidate Master lifecycle（G7 後）-----------------------------------------

# G7 NOT EXECUTED の4社。Candidate Master の行全体を固定する（G7 lifecycle sync で変えない）。
UNCHANGED_CANDIDATE_ROWS = {
    "wave0-020": {
        "candidate_id": "wave0-020",
        "candidate_name": "水堂須佐男神社",
        "prefecture": "兵庫県",
        "candidate_status": "BUILD_READY",
        "status_reason_code": "WAVE0_CORE_READY_CANDIDATE",
        "build_batch": "W0-DB04",
        "duplicate_status": "NEW",
        "discovery_sources": [
            {
                "discovery_source": "Omairi 全国神社人気ランキング2026",
                "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/3",
                "discovery_rank": 56,
                "captured_at": "2026-08-27",
            }
        ],
    },
    "wave0-022": {
        "candidate_id": "wave0-022",
        "candidate_name": "毛谷黒龍神社",
        "prefecture": "福井県",
        "candidate_status": "BUILD_READY",
        "status_reason_code": "WAVE0_CORE_READY_CANDIDATE",
        "build_batch": "W0-DB04",
        "duplicate_status": "NEW",
        "discovery_sources": [
            {
                "discovery_source": "Omairi 全国神社人気ランキング2026",
                "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/3",
                "discovery_rank": 61,
                "captured_at": "2026-08-27",
            }
        ],
    },
    "wave0-023": {
        "candidate_id": "wave0-023",
        "candidate_name": "富知六所浅間神社",
        "prefecture": "静岡県",
        "candidate_status": "HOLD",
        "status_reason_code": "SOURCE_HOLD",
        "build_batch": None,
        "duplicate_status": "NEW",
        "discovery_sources": [
            {
                "discovery_source": "Omairi 全国神社人気ランキング2026",
                "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/3",
                "discovery_rank": 62,
                "captured_at": "2026-08-27",
            }
        ],
    },
    "wave0-024": {
        "candidate_id": "wave0-024",
        "candidate_name": "居多神社",
        "prefecture": "新潟県",
        "candidate_status": "HOLD",
        "status_reason_code": "UNKNOWN_EVIDENCE",
        "build_batch": None,
        "duplicate_status": "NEW",
        "discovery_sources": [
            {
                "discovery_source": "Omairi 全国神社人気ランキング2026",
                "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/3",
                "discovery_rank": 66,
                "captured_at": "2026-08-27",
            }
        ],
    },
}


def test_execution_candidates_are_core_ready_after_g8():
    """G8 で承認された3社のみ CORE_READY に遷移し、FACT_READY を維持する。

    G7 Production Import の記録は履歴として保持する。G8 は Candidate Master の
    lifecycle 遷移であり、Production データへの書き込みを意味しない。
    """
    candidates = _load_candidates()

    for cid in EXECUTION_IDS:
        row = candidates[cid]
        assert row["candidate_status"] == "CORE_READY", cid
        assert row["knowledge_status"] == "FACT_READY", cid
        assert row["build_batch"] == "W0-DB04", cid
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE", cid
        assert row["duplicate_status"] == "NEW", cid


def test_g7_not_executed_candidate_rows_are_unchanged():
    """wave0-020 / 022（W0-DB04 member）と wave0-023 / 024（HOLD）は G7 対象外で、行全体が不変。"""
    candidates = _load_candidates()

    for cid, expected in UNCHANGED_CANDIDATE_ROWS.items():
        assert candidates[cid] == expected, cid


# --- identity / position -------------------------------------------------------


def test_added_rows_match_candidate_master_and_frozen_values():
    frozen = _load_frozen()
    candidates = _load_candidates()

    for cid, row in _added_by_candidate().items():
        master_row = candidates[cid]
        assert row["name_jp"] == master_row["official_name"] == master_row["candidate_name"], cid
        assert row["address"] == master_row["official_address"], cid
        assert row["latitude"] == master_row["latitude"] == float(frozen[cid]["latitude"]), cid
        assert row["longitude"] == master_row["longitude"] == float(frozen[cid]["longitude"]), cid
        assert row["location"] == {"lat": row["latitude"], "lng": row["longitude"]}, cid


def test_canonical_address_keeps_source_attested_wording():
    """Source 表記は書き換えない。wave0-021 だけが都道府県前置を受ける。"""
    frozen = _load_frozen()

    for cid, row in _added_by_candidate().items():
        prefix = NORMALIZED_PREFECTURE_PREFIX.get(cid, "")
        assert row["address"] == prefix + frozen[cid]["source_attested_address"], cid

    assert not _load_frozen()["wave0-021"]["source_attested_address"].startswith("大阪府")


def test_prefecture_derivation_matches_the_candidate_prefecture():
    builder = _load_builder()
    candidates = _load_candidates()

    for cid, row in _added_by_candidate().items():
        prefecture = builder.derive_prefecture(row["address"])
        assert prefecture == EXPECTED_PREFECTURES[cid] == candidates[cid]["prefecture"], cid
        assert "prefecture" not in row, cid


def test_base_seed_identities_remain_unique():
    rows = _load_base_rows()
    identities = [(row["name_jp"], row["address"]) for row in rows]
    assert len(identities) == len(set(identities))

    existing_names = {row["name_jp"] for row in rows[:EXISTING_BASE_ROW_COUNT]}
    assert not {row["name_jp"] for row in _added_rows()} & existing_names


# --- goriyaku boundary ---------------------------------------------------------


def test_goriyaku_uses_the_existing_empty_representation():
    rows = _load_base_rows()
    # 既存 Base Seed がすでに使っている表現であること（新しい空表現を導入しない）。
    assert any(row.get("goriyaku") == EMPTY_GORIYAKU for row in rows[:EXISTING_BASE_ROW_COUNT])
    assert any("goriyaku_tags" not in row for row in rows[:EXISTING_BASE_ROW_COUNT])

    candidates = _load_candidates()
    for cid, row in _added_by_candidate().items():
        assert row["goriyaku"] == EMPTY_GORIYAKU, cid
        assert "goriyaku_tags" not in row, cid
        assert "goriyaku" not in candidates[cid], cid
        assert "goriyaku_tags" not in candidates[cid], cid


def test_new_rows_carry_no_inferred_fields():
    for row in _added_rows():
        assert list(row) == [
            "name_jp",
            "address",
            "latitude",
            "longitude",
            "goriyaku",
            "kyusei",
            "astro_elements",
            "location",
        ], row["name_jp"]
        assert row["kyusei"] is None
        assert row["astro_elements"] == []
        assert "visit_style_tags" not in row


# --- existing rows / determinism -----------------------------------------------


def test_existing_base_seed_rows_are_unchanged():
    digest = hashlib.sha256(
        json.dumps(
            _load_base_rows()[:EXISTING_BASE_ROW_COUNT],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert digest == EXISTING_BASE_ROWS_SHA256


def test_builder_gates_pass_and_rebuild_is_a_no_op():
    builder = _load_builder()
    source_rows = builder.load_source(BASE_SEED_PATH)
    built_rows = [builder.canonicalize_row(row) for row in source_rows]

    result = builder.validate(source_rows, built_rows)
    assert builder.gate_failures(result) == []
    assert len(source_rows) >= W0_DB04_BASE_ROW_END
    assert result["total"] == len(source_rows)

    first = builder.serialize(built_rows)
    second = builder.serialize([builder.canonicalize_row(row) for row in json.loads(first)])
    assert first == second == BASE_SEED_PATH.read_text(encoding="utf-8")


# --- importer compatibility (isolated test DB) ---------------------------------


@pytest.mark.django_db
def test_isolated_import_is_idempotent_and_assigns_no_goriyaku_tag(tmp_path):
    from temples.models import Shrine

    base_path = tmp_path / "w0_db04_base.json"
    base_path.write_text(json.dumps(_added_rows(), ensure_ascii=False), encoding="utf-8")

    out = io.StringIO()
    call_command("import_shrines_seed", source=str(base_path), stdout=out)
    assert "created=3 updated=0 skipped=0" in out.getvalue()

    names = [row["name_jp"] for row in _added_rows()]

    def snapshot():
        return sorted(
            (
                shrine.name_jp,
                shrine.address,
                shrine.latitude,
                shrine.longitude,
                shrine.goriyaku,
                sorted(shrine.goriyaku_tags.values_list("name", flat=True)),
            )
            for shrine in Shrine.objects.filter(name_jp__in=names)
        )

    before = snapshot()
    assert [(name, goriyaku, tags) for name, _a, _lat, _lng, goriyaku, tags in before] == sorted(
        (row["name_jp"], EMPTY_GORIYAKU, []) for row in _added_rows()
    )

    out = io.StringIO()
    call_command("import_shrines_seed", source=str(base_path), stdout=out)
    assert "created=0 updated=0 skipped=3" in out.getvalue()
    assert snapshot() == before


# ===============================================================================
# Knowledge Seed（wave0_batch_04_seed.json）
#
# Source / Deity / History の値は Evidence Backfill Freeze の markdown から直接読み出して比較する。
# 例外は wave0-025 H3 だけで、W0-DB04 G4 re-entry の Mother Ship decision により
# Evidence Backfill Freeze の値（official_origin / 「二つの系統を集結し、…」）を SUPERSEDE した:
#
#     history_type = historical_event
#     title        = 仙台開府後の現在地造営
#     content      = 仙台開府後、仙台の現在地で社殿を造営
#     period_text  = ""
#     event_date   = null
#
# 系統の集結は H1 / H2（regional_context）が持ち、H4 が 1607-08-12 の遷座祭を持つ。
# 大崎八幡宮には単一の創建年（founding / official_origin）を作らない。
# Evidence Backfill Freeze（#3073）自体は履歴として書き換えない。
# ===============================================================================

KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "wave0_batch_04_seed.json"

SOURCE_KEYS = {
    "wave0-019": "wave0-db04-kenkun-official",
    "wave0-021": "wave0-db04-osaka-tenmangu-official",
    "wave0-025": "wave0-db04-oosaki-hachiman-authority",
}

# (Source, Deity, History)
EXPECTED_KNOWLEDGE_COUNTS = {
    "wave0-019": (1, 2, 5),
    "wave0-021": (1, 1, 3),
    "wave0-025": (1, 3, 4),
}

KNOWLEDGE_VERIFIED_AT = "2026-10-03T00:00:00+09:00"
SOURCE_ACCESSED_AT = "2026-10-03"

EXPECTED_DEITY_ROLES = {
    "wave0-019": [("織田信長公", "primary"), ("織田信忠卿", "enshrined")],
    "wave0-021": [("菅原道真公", "primary")],
    "wave0-025": [("応神天皇", "primary"), ("仲哀天皇", "primary"), ("神功皇后", "primary")],
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
        "仙台開府後の現在地造営",
        "慶長12年の遷座祭",
    ],
}

# Mother Ship decision で Evidence Backfill Freeze を supersede した History（candidate_id, H番号）。
SUPERSEDED_HISTORY = {
    ("wave0-025", "H3"): {
        "frozen_history_type": "official_origin",
        "frozen_fact": "二つの系統を集結し、仙台開府後、現在地に社殿を造営",
        "history_type": "historical_event",
        "content": "仙台開府後、仙台の現在地で社殿を造営",
        "period_text": "",
    },
}


def _load_knowledge_seed():
    from temples.services.knowledge_seed import parse_seed

    return parse_seed(json.loads(KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8")))


def _knowledge_by_candidate():
    candidates = _load_candidates()
    by_identity = {(shrine.name_jp, shrine.address): shrine for shrine in _load_knowledge_seed().shrines}
    return {
        cid: by_identity[(candidates[cid]["official_name"], candidates[cid]["official_address"])]
        for cid in EXECUTION_IDS
    }


def _backfill_block(cid, heading):
    """Evidence Backfill Freeze の candidate 節から `## <heading>` 節を返す。"""
    block = _split_candidate_sections(EVIDENCE_BACKFILL_PATH)[cid]
    match = re.search(r"^## %s\n(.*?)(?=^## |\Z)" % re.escape(heading), block, re.M | re.S)
    return match.group(1)


def _backfill_primary_source(cid):
    block = _backfill_block(cid, "Primary Source")
    return {key: _field(block, key) for key in ("title", "publisher", "source_type", "url", "language")}


def _backfill_history_rows(cid):
    """`| H1 | period | `history_type` | fact |` 行を [(H番号, period, history_type, fact)] で返す。"""
    block = _backfill_block(cid, "History")
    return [
        (number, period.strip(), history_type, fact.strip())
        for number, period, history_type, fact in re.findall(
            r"^\| (H\d+) \| (.+?) \| `(\w+)` \| (.+?) \|$", block, re.M
        )
    ]


# --- scope / counts ------------------------------------------------------------


def test_knowledge_seed_schema_and_counts():
    seed = _load_knowledge_seed()

    assert seed.errors == []
    assert seed.schema_version == "1.0"
    assert len(seed.sources) == 3
    assert len(seed.shrines) == 3
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 6
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 12
    assert sum(len(shrine.deities) + len(shrine.histories) for shrine in seed.shrines) == 18

    for cid, shrine in _knowledge_by_candidate().items():
        source_count, deity_count, history_count = EXPECTED_KNOWLEDGE_COUNTS[cid]
        referenced = {key for fact in [*shrine.deities, *shrine.histories] for key in fact.source_keys}
        assert len(referenced) == source_count, cid
        assert len(shrine.deities) == deity_count, cid
        assert len(shrine.histories) == history_count, cid
        assert shrine.collectives == [], cid


def test_knowledge_shrines_are_exactly_the_base_seed_execution_rows():
    seed = _load_knowledge_seed()
    assert [(shrine.name_jp, shrine.address) for shrine in seed.shrines] == [
        (row["name_jp"], row["address"]) for row in _added_rows()
    ]


def test_excluded_candidates_and_goriyaku_are_absent_from_knowledge_seed():
    raw = KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8")
    for name in EXCLUDED.values():
        assert name not in raw
    assert "goriyaku" not in raw
    assert "ご利益" not in raw
    assert "ご神徳" not in raw


# --- Source --------------------------------------------------------------------


def test_sources_match_the_evidence_backfill_freeze():
    seed = _load_knowledge_seed()
    assert set(seed.sources) == set(SOURCE_KEYS.values())

    for cid, key in SOURCE_KEYS.items():
        source = seed.sources[key]
        frozen = _backfill_primary_source(cid)
        assert source.title == frozen["title"], cid
        assert source.publisher == frozen["publisher"], cid
        assert source.source_type == frozen["source_type"], cid
        assert source.url == frozen["url"], cid
        assert source.language == frozen["language"] == "ja", cid
        assert source.bibliography == "", cid

    assert seed.sources[SOURCE_KEYS["wave0-025"]].source_type == "government"


def test_source_timestamps_follow_the_frozen_contract():
    raw = json.loads(KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8"))
    for source in raw["sources"]:
        assert source["accessed_at"] == SOURCE_ACCESSED_AT, source["key"]
        assert source["verified_at"] == KNOWLEDGE_VERIFIED_AT, source["key"]
        assert source["verification_status"] == "source_confirmed", source["key"]
        assert source["confidence"] == "high", source["key"]


# --- Source relation / verification --------------------------------------------


def test_every_fact_is_bound_only_to_its_own_candidate_source():
    seed = _load_knowledge_seed()
    referenced = set()

    for cid, shrine in _knowledge_by_candidate().items():
        for fact in [*shrine.deities, *shrine.histories]:
            assert fact.source_keys == [SOURCE_KEYS[cid]], (cid, fact)
            referenced.update(fact.source_keys)

    assert referenced == set(seed.sources)


def test_every_fact_is_source_confirmed_high_with_the_frozen_verified_at():
    raw = json.loads(KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8"))
    for shrine in raw["shrines"]:
        for fact in [*shrine["deities"], *shrine["histories"]]:
            assert fact["verification_status"] == "source_confirmed"
            assert fact["confidence"] == "high"
            assert fact["verified_at"] == KNOWLEDGE_VERIFIED_AT


def test_every_fact_is_usable_under_the_evidence_gate():
    from temples.services import evidence_gate

    seed = _load_knowledge_seed()
    decisions = [
        evidence_gate.decide_fact_usability(
            verification_status=fact.verification_status,
            confidence=fact.confidence,
            source_verification_statuses=[
                seed.sources[key].verification_status for key in fact.source_keys
            ],
        )
        for shrine in seed.shrines
        for fact in [*shrine.deities, *shrine.histories]
    ]
    assert len(decisions) == 18
    assert all(decision.usable for decision in decisions)


# --- Deity ---------------------------------------------------------------------


def test_deities_match_the_frozen_roles_and_order():
    for cid, shrine in _knowledge_by_candidate().items():
        assert [(deity.display_name, deity.role) for deity in shrine.deities] == EXPECTED_DEITY_ROLES[cid]
        assert [deity.sort_order for deity in shrine.deities] == list(range(len(shrine.deities)))
        for deity in shrine.deities:
            assert deity.canonical_name == deity.display_name, (cid, deity.display_name)


def test_deity_boundaries_are_preserved():
    shrines = _knowledge_by_candidate()

    kenkun = {deity.display_name: deity for deity in shrines["wave0-019"].deities}
    # Source 表記の「配祀」は W0-DB03 の「相殿」precedent と同じく note にだけ保持する。
    assert kenkun["織田信忠卿"].note == "公式Sourceが配祀として明示。"
    assert kenkun["織田信長公"].note == ""

    # 大将軍社の祭神を本社へ混入させない。
    assert [deity.display_name for deity in shrines["wave0-021"].deities] == ["菅原道真公"]

    # 大崎八幡宮は3柱とも primary。集合 Deity（collective）は作らない。
    assert {deity.role for deity in shrines["wave0-025"].deities} == {"primary"}
    assert shrines["wave0-025"].collectives == []


# --- History -------------------------------------------------------------------


def test_histories_match_the_frozen_facts_except_the_superseded_row():
    for cid, shrine in _knowledge_by_candidate().items():
        frozen_rows = _backfill_history_rows(cid)
        assert len(frozen_rows) == len(shrine.histories), cid
        assert [history.title for history in shrine.histories] == EXPECTED_HISTORY_TITLES[cid]
        assert [history.sort_order for history in shrine.histories] == list(range(len(shrine.histories)))

        for (number, period, frozen_type, frozen_fact), history in zip(frozen_rows, shrine.histories, strict=True):
            assert history.event_date is None, (cid, number)
            superseded = SUPERSEDED_HISTORY.get((cid, number))
            if superseded:
                # Evidence Backfill Freeze 側は履歴として当時の値のまま残っている。
                assert (frozen_type, frozen_fact) == (
                    superseded["frozen_history_type"],
                    superseded["frozen_fact"],
                )
                assert history.history_type == superseded["history_type"], (cid, number)
                assert history.content == superseded["content"], (cid, number)
                assert history.period_text == superseded["period_text"], (cid, number)
                continue

            assert history.history_type == frozen_type, (cid, number)
            assert history.content == frozen_fact, (cid, number)
            if period.startswith("（単一年なし）"):
                assert history.period_text == "", (cid, number)
            else:
                assert history.period_text == period, (cid, number)


def test_kenkun_founding_is_1869_and_1910_is_relocation():
    histories = _knowledge_by_candidate()["wave0-019"].histories
    founding = [history for history in histories if history.history_type in ("founding", "official_origin")]
    assert [(history.period_text, history.title) for history in founding] == [("1869", "建勲神社創立の宣下")]
    relocation = histories[4]
    assert (relocation.period_text, relocation.history_type) == ("1910", "historical_event")


def test_osaka_tenmangu_founding_is_949_not_650():
    histories = _knowledge_by_candidate()["wave0-021"].histories
    assert [(history.period_text, history.history_type) for history in histories] == [
        ("650", "regional_context"),
        ("901", "historical_event"),
        ("949", "founding"),
    ]
    assert not any("1843" in history.period_text or "1843" in history.content for history in histories)


def test_oosaki_hachiman_has_no_single_founding_year():
    histories = _knowledge_by_candidate()["wave0-025"].histories

    assert [history.history_type for history in histories] == [
        "regional_context",
        "regional_context",
        "historical_event",
        "historical_event",
    ]
    assert not any(history.history_type in ("founding", "official_origin") for history in histories)
    assert all(history.event_date is None for history in histories)

    h3 = histories[2]
    assert h3.history_type == "historical_event"
    assert h3.history_type != "official_origin"
    assert h3.content == "仙台開府後、仙台の現在地で社殿を造営"
    assert "二つの系統を集結" not in h3.content
    assert h3.period_text == ""

    # 年代を持つのは H4 の遷座祭だけで、それは創建ではない。
    assert [history.period_text for history in histories] == ["", "", "", "慶長12年（1607）8月12日"]


# --- determinism / isolated import ---------------------------------------------


def test_knowledge_seed_parse_is_deterministic_and_canonically_serialized():
    from temples.services.knowledge_seed import parse_seed

    raw = KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8")
    assert repr(parse_seed(json.loads(raw))) == repr(parse_seed(json.loads(raw)))
    assert raw == json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n"


@pytest.mark.django_db
def test_isolated_knowledge_import_is_idempotent_and_keeps_source_relations(tmp_path):
    from temples.models import Shrine, ShrineDeity, ShrineDeityCollective, ShrineHistory

    base_path = tmp_path / "w0_db04_base.json"
    base_path.write_text(json.dumps(_added_rows(), ensure_ascii=False), encoding="utf-8")
    call_command("import_shrines_seed", source=str(base_path), stdout=io.StringIO())

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(KNOWLEDGE_SEED_PATH), stdout=out)
    assert "sources created=3, deities created=6, histories created=12" in out.getvalue()

    shrines = Shrine.objects.filter(name_jp__in=[row["name_jp"] for row in _added_rows()])
    deities = ShrineDeity.objects.filter(shrine__in=shrines)
    histories = ShrineHistory.objects.filter(shrine__in=shrines)
    assert deities.count() == 6
    assert histories.count() == 12
    assert not ShrineDeityCollective.objects.filter(shrine__in=shrines).exists()
    for fact in [*deities, *histories]:
        assert fact.sources.count() == 1

    oosaki = histories.filter(shrine__name_jp="大崎八幡宮")
    assert not oosaki.filter(history_type__in=("founding", "official_origin")).exists()

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(KNOWLEDGE_SEED_PATH), stdout=out)
    assert "sources created=0, deities created=0, histories created=0" in out.getvalue()
