"""W0-DB03 G4 execution subset（大神神社 / 北野天満宮 / 平安神宮 / 岡田宮）.

このモジュールは W0-DB03 G4 の3成果物を、凍結済み Source Packet に対して固定する。

- Candidate Master 行 wave0-012 / 013 / 015 / 016
- Base Seed 行（`shrines_seed_clean.json`）
- Knowledge Seed（`wave0_batch_03_seed.json`）

canonical identity・座標・goriyaku は Packet markdown から直接読み出して比較する。
テスト側に期待値を転記すると、転記が正本になってしまうため。

W0-DB03 の original membership は5社のまま保持する（Mother Ship Decision A）。
`wave0-014 宮城縣護國神社` は G3 `MODEL_CHANGE_REQUIRED` で隔離されており、
Candidate Master hydration / Base Seed / Knowledge Seed のいずれにも入らない。
"""

import ast
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

SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "wave0_batch_03_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
CANDIDATE_MASTER_PATH = TEMPLES_DIR / "data" / "shrine_expansion_candidate_master.json"
PACKET_PATH = REPO_ROOT / "docs" / "audit" / "shrine-expansion-wave0-db03-source-packet-freeze.md"
CANONICAL_TAG_CONTRACT_PATH = TESTS_DIR / "test_bootstrap_goriyaku_master_exact39_contract.py"

EXECUTION_IDS = ["wave0-012", "wave0-013", "wave0-015", "wave0-016"]
MODEL_HOLD_ID = "wave0-014"
MODEL_HOLD_NAME = "宮城縣護國神社"
ORIGINAL_MEMBERSHIP = {
    "wave0-012": ("大神神社", 38),
    "wave0-013": ("北野天満宮", 40),
    "wave0-014": ("宮城縣護國神社", 44),
    "wave0-015": ("平安神宮", 46),
    "wave0-016": ("岡田宮", 47),
}

HYDRATION_FIELDS = {
    "official_name",
    "official_address",
    "official_source_type",
    "official_source_url",
    "verified_at",
    "latitude",
    "longitude",
    "goriyaku",
    "goriyaku_tags",
}

# W0-DB03 追加前（develop@7106958）の Base Seed 113 行。既存行の不変を固定する。
EXISTING_BASE_ROW_COUNT = 113
EXISTING_BASE_ROWS_SHA256 = "86acbc9aadfe0a86cd7b8642d567f0a59b335a33578d2cb5b0e75f73d0489d32"

EXPECTED_FACT_COUNTS = {
    "大神神社": (1, 1),
    "北野天満宮": (3, 1),
    "平安神宮": (2, 2),
    "岡田宮": (12, 1),
}

# Packet / normalization audit が canonical へ降ろさないとした表記。
HELD_GORIYAKU_WORDS = ("健康長寿", "身体健康", "旅行安全", "海外旅行安全")


def _load_packet():
    """凍結 Packet の canonical identity / 座標 / goriyaku subset を markdown から読む。"""
    text = PACKET_PATH.read_text(encoding="utf-8")
    entries = {}
    for block in re.split(r"^# ", text, flags=re.M):
        match = re.search(r"^candidate_id\s+= (\S+)$", block, re.M)
        if not match:
            continue

        def field(name, block=block):
            return re.search(r"^%s\s+= (.+)$" % re.escape(name), block, re.M).group(1).strip()

        tags_match = re.search(r"goriyaku_tags =\n\[(.+)\]", block)
        entries[match.group(1)] = {
            "official_name": field("official_name"),
            "official_address": field("official_address"),
            "official_source_type": field("official_source_type"),
            "official_source_url": field("official_source_url"),
            "verified_at": field("verified_at"),
            "position_status": field("position_status"),
            # 文字列のまま保持し、比較時に float 化する（Packet は末尾0を含む表記がある）。
            "latitude": field("latitude"),
            "longitude": field("longitude"),
            "goriyaku_tags": [tag.strip() for tag in tags_match.group(1).split(",")],
        }
    return entries


def _load_candidates():
    master = json.loads(CANDIDATE_MASTER_PATH.read_text(encoding="utf-8"))
    return {row["candidate_id"]: row for row in master["candidates"]}


def _load_base_rows():
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _base_by_identity():
    return {(row["name_jp"], row["address"]): row for row in _load_base_rows()}


def _load_seed():
    return parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))


def _canonical_goriyaku_master():
    """canonical 39 GoriyakuTag master（id, name）を既存 contract テストから読み出す。"""
    tree = ast.parse(CANONICAL_TAG_CONTRACT_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        target = getattr(node, "target", None)
        if isinstance(node, ast.AnnAssign) and getattr(target, "id", None) == "CANONICAL_MASTER":
            return ast.literal_eval(node.value)
    raise AssertionError("CANONICAL_MASTER not found")


def _decide(seed, fact):
    return evidence_gate.decide_fact_usability(
        verification_status=fact.verification_status,
        confidence=fact.confidence,
        source_verification_statuses=[
            seed.sources[source_key].verification_status for source_key in fact.source_keys
        ],
    )


# --- scope ---------------------------------------------------------------------


def test_packet_freezes_exactly_the_four_execution_shrines():
    packet = _load_packet()
    assert sorted(packet) == EXECUTION_IDS
    assert MODEL_HOLD_ID not in packet
    assert all(entry["position_status"] in ("PASS", "PASS_ANCHOR") for entry in packet.values())


def test_exactly_four_execution_shrines_are_built():
    packet = _load_packet()
    candidates = _load_candidates()
    base = _base_by_identity()
    seed = _load_seed()

    hydrated = sorted(
        cid
        for cid, row in candidates.items()
        if row["build_batch"] == "W0-DB03" and HYDRATION_FIELDS <= row.keys()
    )
    assert hydrated == EXECUTION_IDS

    added = _load_base_rows()[EXISTING_BASE_ROW_COUNT:]
    assert [(row["name_jp"], row["address"]) for row in added] == [
        (packet[cid]["official_name"], packet[cid]["official_address"]) for cid in EXECUTION_IDS
    ]
    for cid in EXECUTION_IDS:
        assert (packet[cid]["official_name"], packet[cid]["official_address"]) in base

    assert [(s.name_jp, s.address) for s in seed.shrines] == [
        (packet[cid]["official_name"], packet[cid]["official_address"]) for cid in EXECUTION_IDS
    ]


def test_model_hold_shrine_is_absent_from_base_and_knowledge_additions():
    base_names = {row["name_jp"] for row in _load_base_rows()}
    seed = _load_seed()
    raw_seed = SEED_PATH.read_text(encoding="utf-8")

    assert MODEL_HOLD_NAME not in base_names
    assert all(shrine.name_jp != MODEL_HOLD_NAME for shrine in seed.shrines)
    assert MODEL_HOLD_NAME not in raw_seed
    assert "gokokujinja" not in raw_seed


def test_model_hold_candidate_row_is_unchanged():
    """wave0-014 は G3 で隔離。hydration / status 変更を一切受けない。"""
    row = _load_candidates()[MODEL_HOLD_ID]
    assert row == {
        "candidate_id": "wave0-014",
        "candidate_name": "宮城縣護國神社",
        "prefecture": "宮城県",
        "candidate_status": "BUILD_READY",
        "status_reason_code": "WAVE0_CORE_READY_CANDIDATE",
        "build_batch": "W0-DB03",
        "duplicate_status": "NEW",
        "discovery_sources": [
            {
                "discovery_source": "Omairi 全国神社人気ランキング2026",
                "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/2",
                "discovery_rank": 44,
                "captured_at": "2026-09-06",
            }
        ],
    }


# --- Candidate Master ----------------------------------------------------------


def test_original_w0_db03_membership_and_provenance_remain_intact():
    candidates = _load_candidates()
    members = {cid: row for cid, row in candidates.items() if row["build_batch"] == "W0-DB03"}

    assert set(members) == set(ORIGINAL_MEMBERSHIP)
    for cid, (name, rank) in ORIGINAL_MEMBERSHIP.items():
        row = members[cid]
        assert row["candidate_name"] == name
        # G7 後: execution subset は IMPORTED、wave0-014 は BUILD_READY のまま。
        expected_status = "IMPORTED" if cid in EXECUTION_IDS else "BUILD_READY"
        assert row["candidate_status"] == expected_status, cid
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE"
        assert row["duplicate_status"] == "NEW"
        assert [source["discovery_rank"] for source in row["discovery_sources"]] == [rank]


def test_execution_candidates_are_hydrated_and_imported_but_not_core_ready():
    """G7 Production Import 完了後の lifecycle。

    Production 実測は docs/audit/shrine-expansion-wave0-db03-production-import.md。
    IMPORTED / FACT_READY まで。CORE_READY は G8 の別 Gate であり未判定。
    """
    packet = _load_packet()
    candidates = _load_candidates()

    for cid in EXECUTION_IDS:
        row = candidates[cid]
        frozen = packet[cid]

        assert row["official_name"] == frozen["official_name"] == row["candidate_name"]
        assert row["official_address"] == frozen["official_address"]
        assert row["official_source_type"] == frozen["official_source_type"]
        assert row["official_source_url"] == frozen["official_source_url"]
        assert row["verified_at"] == frozen["verified_at"][:10]
        assert row["latitude"] == float(frozen["latitude"])
        assert row["longitude"] == float(frozen["longitude"])
        assert row["goriyaku_tags"] == frozen["goriyaku_tags"]
        assert row["identity_status"] == "CONFIRMED"
        assert row["official_source_status"] == "CONFIRMED"

        # G7 で Production 上の usable Knowledge を実測済み。
        assert row["knowledge_status"] == "FACT_READY"
        assert row["candidate_status"] == "IMPORTED"
        assert row["candidate_status"] != "CORE_READY"
        assert row["build_batch"] == "W0-DB03"
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE"


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
    identities = [(row["name_jp"], row["address"]) for row in _load_base_rows()]
    assert len(identities) == len(set(identities))
    names = [row["name_jp"] for row in _load_base_rows()[EXISTING_BASE_ROW_COUNT:]]
    existing_names = {row["name_jp"] for row in _load_base_rows()[:EXISTING_BASE_ROW_COUNT]}
    assert not set(names) & existing_names


def test_candidate_master_identity_and_position_match_base_seed():
    candidates = _load_candidates()
    base = _base_by_identity()

    for cid in EXECUTION_IDS:
        master_row = candidates[cid]
        base_row = base[(master_row["official_name"], master_row["official_address"])]

        assert base_row["latitude"] == master_row["latitude"]
        assert base_row["longitude"] == master_row["longitude"]
        assert base_row["goriyaku"] == master_row["goriyaku"]
        assert base_row["goriyaku_tags"] == master_row["goriyaku_tags"]


def test_base_seed_location_exactly_mirrors_latitude_longitude():
    for row in _load_base_rows()[EXISTING_BASE_ROW_COUNT:]:
        assert row["location"] == {"lat": row["latitude"], "lng": row["longitude"]}, row["name_jp"]
        assert -90 <= row["latitude"] <= 90
        assert -180 <= row["longitude"] <= 180


def test_new_base_rows_carry_no_legacy_or_inferred_fields():
    for row in _load_base_rows()[EXISTING_BASE_ROW_COUNT:]:
        assert set(row) == {
            "name_jp",
            "address",
            "latitude",
            "longitude",
            "goriyaku",
            "goriyaku_tags",
            "kyusei",
            "astro_elements",
            "location",
        }
        assert row["kyusei"] is None
        assert row["astro_elements"] == []


# --- goriyaku ------------------------------------------------------------------


def test_goriyaku_tags_are_packet_safe_subset_within_canonical_master():
    packet = _load_packet()
    canonical = {name for _tag_id, name in _canonical_goriyaku_master()}
    base = _base_by_identity()

    assert len(canonical) == 39
    for cid in EXECUTION_IDS:
        frozen = packet[cid]
        row = base[(frozen["official_name"], frozen["official_address"])]
        assert row["goriyaku_tags"] == frozen["goriyaku_tags"]
        assert set(row["goriyaku_tags"]) <= canonical
        assert len(row["goriyaku_tags"]) == len(set(row["goriyaku_tags"]))
        assert row["goriyaku"].split("・") == row["goriyaku_tags"]


def test_held_goriyaku_wording_never_reaches_recommendation_evidence():
    candidates = _load_candidates()
    surfaces = []
    for cid in EXECUTION_IDS:
        surfaces.append(candidates[cid]["goriyaku"])
        surfaces.extend(candidates[cid]["goriyaku_tags"])
    for row in _load_base_rows()[EXISTING_BASE_ROW_COUNT:]:
        surfaces.append(row["goriyaku"])
        surfaces.extend(row["goriyaku_tags"])

    for held in HELD_GORIYAKU_WORDS:
        assert all(held not in surface for surface in surfaces), held
    # 汎用の「健康」を健康系canonical tagへ写像していないこと。
    assert all("健康" not in surface for surface in surfaces)


# --- Knowledge Seed ------------------------------------------------------------


def test_knowledge_seed_schema_and_counts():
    seed = _load_seed()

    assert seed.errors == []
    assert seed.schema_version == "1.0"
    assert len(seed.sources) == 4
    assert len(seed.shrines) == 4
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}
    assert set(by_name) == set(EXPECTED_FACT_COUNTS)
    for name, (deity_count, history_count) in EXPECTED_FACT_COUNTS.items():
        assert len(by_name[name].deities) == deity_count, name
        assert len(by_name[name].histories) == history_count, name


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


def test_source_keys_resolve_and_no_fact_is_source_less():
    seed = _load_seed()
    known = set(seed.sources)
    referenced = set()

    for shrine in seed.shrines:
        for fact in [*shrine.deities, *shrine.histories]:
            assert fact.source_keys, (shrine.name_jp, fact)
            assert set(fact.source_keys) <= known
            referenced.update(fact.source_keys)

    assert referenced == known


def test_sources_are_official_and_do_not_reuse_knowledge_source_identity():
    seed = _load_seed()
    urls = [source.url for source in seed.sources.values()]

    assert len(urls) == len(set(urls))
    for source in seed.sources.values():
        assert source.source_type == "shrine_official"
        assert source.url.startswith("https://")
        assert source.verification_status == "source_confirmed"
        assert source.confidence == "high"
        assert source.verified_at is not None


def test_sources_match_packet_official_source_urls():
    packet = _load_packet()
    seed = _load_seed()
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    for cid in EXECUTION_IDS:
        frozen = packet[cid]
        shrine = by_name[frozen["official_name"]]
        keys = {key for fact in [*shrine.deities, *shrine.histories] for key in fact.source_keys}
        assert {seed.sources[key].url for key in keys} == {frozen["official_source_url"]}


def test_every_shrine_has_at_least_one_usable_deity_or_history_fact():
    seed = _load_seed()

    for shrine in seed.shrines:
        usable = [
            fact for fact in [*shrine.deities, *shrine.histories] if _decide(seed, fact).usable
        ]
        assert usable, shrine.name_jp


def test_evidence_gate_accepts_all_seed_facts():
    seed = _load_seed()
    decisions = [
        _decide(seed, fact)
        for shrine in seed.shrines
        for fact in [*shrine.deities, *shrine.histories]
    ]
    assert len(decisions) == 23
    assert all(decision.usable for decision in decisions)


def test_no_within_shrine_fact_duplicates():
    seed = _load_seed()
    for shrine in seed.shrines:
        names = [deity.display_name for deity in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp
        keys = [(history.history_type, history.title) for history in shrine.histories]
        assert len(keys) == len(set(keys)), shrine.name_jp


def test_packet_boundaries_are_preserved():
    seed = _load_seed()
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    # 大神神社: 大物主大神のみ。創祀伝承を史実化しない。
    oomiwa = by_name["大神神社"]
    assert [(d.display_name, d.role) for d in oomiwa.deities] == [("大物主大神", "primary")]
    assert [h.history_type for h in oomiwa.histories] == ["historical_event"]
    assert "大国主" not in {d.canonical_name for d in oomiwa.deities}

    # 北野天満宮: 主祭神 + 相殿2柱のみ。摂社・末社の祭神を持ち込まない。
    kitano = by_name["北野天満宮"]
    assert [(d.display_name, d.role) for d in kitano.deities] == [
        ("菅原道真公", "primary"),
        ("中将殿", "secondary"),
        ("吉祥女", "secondary"),
    ]

    # 平安神宮: 序列を推測しない。
    heian = by_name["平安神宮"]
    assert [(d.display_name, d.role) for d in heian.deities] == [
        ("桓武天皇", "unknown"),
        ("孝明天皇", "unknown"),
    ]

    # 岡田宮: 12柱を個別に保持し、集合ラベルへ畳まない。伝承は tradition のまま。
    okada = by_name["岡田宮"]
    assert len(okada.deities) == 12
    assert okada.deities[0].display_name == "神日本磐余彦命（神武天皇）"
    assert okada.deities[0].canonical_name == "神日本磐余彦命"
    assert all(d.role == "unknown" for d in okada.deities)
    assert [h.history_type for h in okada.histories] == ["tradition"]
    assert "伝えられている" in okada.histories[0].content


def test_seed_parse_is_deterministic():
    raw = SEED_PATH.read_text(encoding="utf-8")
    first = parse_seed(json.loads(raw))
    second = parse_seed(json.loads(raw))
    assert repr(first) == repr(second)
    assert raw == json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n"


# --- DB: import / idempotency / no new GoriyakuTag -----------------------------


def _write_execution_base_seed(tmp_path):
    path = tmp_path / "w0_db03_base.json"
    path.write_text(
        json.dumps(_load_base_rows()[EXISTING_BASE_ROW_COUNT:], ensure_ascii=False),
        encoding="utf-8",
    )
    return path


@pytest.mark.django_db
def test_import_is_idempotent_and_creates_no_goriyaku_tag(tmp_path):
    from temples.models import (
        GoriyakuTag,
        Shrine,
        ShrineDeity,
        ShrineHistory,
        ShrineKnowledgeSource,
    )

    for tag_id, name in _canonical_goriyaku_master():
        GoriyakuTag.objects.update_or_create(id=tag_id, defaults={"name": name})
    tags_before = set(GoriyakuTag.objects.values_list("id", "name"))

    base_path = _write_execution_base_seed(tmp_path)
    out = io.StringIO()
    call_command("import_shrines_seed", source=str(base_path), stdout=out)
    assert "created=4 updated=0 skipped=0" in out.getvalue()

    out = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=out)
    assert "sources created=4, deities created=18, histories created=5" in out.getvalue()

    def snapshot():
        return (
            sorted(Shrine.objects.values_list("id", "name_jp", "address", "latitude", "longitude")),
            sorted(
                (s.name_jp, sorted(s.goriyaku_tags.values_list("name", flat=True)))
                for s in Shrine.objects.all()
            ),
            sorted(ShrineKnowledgeSource.objects.values_list("id", "url")),
            sorted(ShrineDeity.objects.values_list("id", "shrine_id", "display_name")),
            sorted(ShrineHistory.objects.values_list("id", "shrine_id", "title")),
        )

    before = snapshot()

    out = io.StringIO()
    call_command("import_shrines_seed", source=str(base_path), stdout=out)
    assert "created=0 updated=0 skipped=4" in out.getvalue()
    out = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=out)
    assert "sources created=0, deities created=0, histories created=0" in out.getvalue()

    assert snapshot() == before
    assert set(GoriyakuTag.objects.values_list("id", "name")) == tags_before

    for deity in ShrineDeity.objects.all():
        assert deity.sources.exists()
    for history in ShrineHistory.objects.all():
        assert history.sources.exists()
