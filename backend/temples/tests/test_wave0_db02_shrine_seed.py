"""W0-DB02 (射水神社 / 別小江神社 / 戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社).

このモジュールは W0-DB02 の3成果物を、凍結済み Source Packet に対して固定する。

- Candidate Master 行 wave0-007..011
- Base Seed 行（`shrines_seed_clean.json`）
- Knowledge Seed（`wave0_batch_02_seed.json`）

座標・canonical identity は Packet markdown から直接読み出して比較する。
テスト側に期待値を転記すると、転記が正本になってしまうため。
"""

import ast
import json
import re
from pathlib import Path

from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed

TESTS_DIR = Path(__file__).resolve().parent
TEMPLES_DIR = TESTS_DIR.parent
REPO_ROOT = TEMPLES_DIR.parents[1]

SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "wave0_batch_02_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
CANDIDATE_MASTER_PATH = TEMPLES_DIR / "data" / "shrine_expansion_candidate_master.json"
PACKET_PATH = (
    REPO_ROOT
    / "docs"
    / "audit"
    / "shrine-expansion-wave0-db02-source-packet-freeze.md"
)
CANONICAL_TAG_CONTRACT_PATH = (
    TESTS_DIR / "test_bootstrap_goriyaku_master_exact39_contract.py"
)

CANDIDATE_IDS = ["wave0-007", "wave0-008", "wave0-009", "wave0-010", "wave0-011"]

EXPECTED_FACT_COUNTS = {
    "射水神社": (1, 2),
    "別小江神社": (6, 1),
    "戸隠神社 中社": (1, 1),
    "札幌諏訪神社": (2, 1),
    "少彦名神社": (2, 2),
}

# Packet が HOLD とした表記。Recommendation Evidence へ降ろしてはならない。
HELD_GORIYAKU_WORDS = (
    "開運厄祓",
    "みちひらき",
    "厄除開運",
    "戦の神様",
    "健康成就",
)


def _load_packet_identities():
    """凍結 Packet の canonical identity / 座標を markdown から読み出す。"""
    text = PACKET_PATH.read_text(encoding="utf-8")
    entries = {}
    for block in re.split(r"^# \d+\. ", text, flags=re.M)[1:]:
        candidate_id = re.search(r"candidate_id\s+= (\S+)", block).group(1)
        entries[candidate_id] = {
            "official_name": re.search(r"official_name\s+= (.+)", block).group(1).strip(),
            "official_address": re.search(r"official_address\s+= (.+)", block).group(1).strip(),
            "official_source_type": re.search(
                r"official_source_type = (.+)", block
            ).group(1).strip(),
            "position_status": re.search(r"position_status\s+= (\S+)", block).group(1),
            # 文字列のまま保持する。float 経由で丸めると等値検証の意味が失われる。
            "latitude": re.search(r"^latitude\s+= (\S+)", block, re.M).group(1),
            "longitude": re.search(r"^longitude\s+= (\S+)", block, re.M).group(1),
        }
    return entries


def _load_candidates():
    master = json.loads(CANDIDATE_MASTER_PATH.read_text(encoding="utf-8"))
    return {row["candidate_id"]: row for row in master["candidates"]}


def _load_base_rows():
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _load_seed():
    return parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))


def _canonical_goriyaku_tags():
    """canonical 39 GoriyakuTag master を既存 contract テストから読み出す。"""
    tree = ast.parse(CANONICAL_TAG_CONTRACT_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        target = getattr(node, "target", None)
        if isinstance(node, ast.AnnAssign) and getattr(target, "id", None) == "CANONICAL_MASTER":
            return {name for _tag_id, name in ast.literal_eval(node.value)}
    raise AssertionError("CANONICAL_MASTER not found")


def test_wave0_db02_packet_freeze_is_readable_and_all_pass():
    packet = _load_packet_identities()

    assert sorted(packet) == CANDIDATE_IDS
    assert all(entry["position_status"] == "PASS" for entry in packet.values())


def test_wave0_db02_candidate_master_matches_packet_identity():
    packet = _load_packet_identities()
    candidates = _load_candidates()

    for candidate_id in CANDIDATE_IDS:
        row = candidates[candidate_id]
        frozen = packet[candidate_id]

        assert row["official_name"] == frozen["official_name"]
        assert row["official_address"] == frozen["official_address"]
        assert row["official_source_type"] == frozen["official_source_type"]
        assert row["identity_status"] == "CONFIRMED"
        assert row["official_source_status"] == "CONFIRMED"
        assert row["knowledge_status"] == "FACT_READY"


def test_wave0_db02_candidates_stay_build_ready_in_w0_db02():
    candidates = _load_candidates()

    for candidate_id in CANDIDATE_IDS:
        row = candidates[candidate_id]
        assert row["build_batch"] == "W0-DB02"
        # このバッチは Base/Knowledge Seed の作成までを範囲とする。
        # Production import と CORE_READY 昇格は別フェーズ。
        assert row["candidate_status"] == "BUILD_READY"


def test_wave0_db02_coordinates_are_identical_across_packet_master_and_base_seed():
    packet = _load_packet_identities()
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    for candidate_id in CANDIDATE_IDS:
        frozen = packet[candidate_id]
        master_row = candidates[candidate_id]
        base_row = base_rows[(frozen["official_name"], frozen["official_address"])]

        # repr 比較にすることで、桁落ち・丸め・再計算を検出する。
        assert repr(master_row["latitude"]) == frozen["latitude"]
        assert repr(master_row["longitude"]) == frozen["longitude"]
        assert repr(base_row["latitude"]) == frozen["latitude"]
        assert repr(base_row["longitude"]) == frozen["longitude"]
        assert base_row["location"] == {
            "lat": base_row["latitude"],
            "lng": base_row["longitude"],
        }


def test_wave0_db02_base_seed_appends_five_rows_without_duplicates():
    packet = _load_packet_identities()
    base_rows = _load_base_rows()
    identities = [(row["name_jp"], row["address"]) for row in base_rows]

    assert len(base_rows) == 113
    assert len(identities) == len(set(identities))

    for candidate_id in CANDIDATE_IDS:
        frozen = packet[candidate_id]
        key = (frozen["official_name"], frozen["official_address"])
        assert identities.count(key) == 1


def test_wave0_db02_goriyaku_tags_are_canonical_and_mirror_candidate_master():
    packet = _load_packet_identities()
    canonical = _canonical_goriyaku_tags()
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    assert len(canonical) == 39

    for candidate_id in CANDIDATE_IDS:
        frozen = packet[candidate_id]
        master_row = candidates[candidate_id]
        base_row = base_rows[(frozen["official_name"], frozen["official_address"])]

        assert master_row["goriyaku_tags"], candidate_id
        assert set(master_row["goriyaku_tags"]) <= canonical
        assert base_row["goriyaku_tags"] == master_row["goriyaku_tags"]
        assert base_row["goriyaku"] == master_row["goriyaku"]
        # goriyaku 文字列とタグ列は同じ集合を表す。
        assert base_row["goriyaku"].split("・") == base_row["goriyaku_tags"]


def test_wave0_db02_held_goriyaku_wording_never_reaches_recommendation_evidence():
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    surfaces = []
    for candidate_id in CANDIDATE_IDS:
        master_row = candidates[candidate_id]
        surfaces.append(master_row["goriyaku"])
        surfaces.extend(master_row["goriyaku_tags"])
        base_row = base_rows[(master_row["official_name"], master_row["official_address"])]
        surfaces.append(base_row["goriyaku"])
        surfaces.extend(base_row["goriyaku_tags"])

    for held in HELD_GORIYAKU_WORDS:
        assert all(held not in surface for surface in surfaces), held


def test_wave0_db02_seed_schema_counts_and_identities():
    packet = _load_packet_identities()
    seed = _load_seed()

    assert seed.errors == []
    assert seed.schema_version == "1.0"
    assert len(seed.sources) == 7
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 12
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 7

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert len(identities) == len(set(identities))
    assert set(identities) == {
        (entry["official_name"], entry["official_address"]) for entry in packet.values()
    }


def test_wave0_db02_shrine_refs_exist_in_base_seed():
    seed = _load_seed()
    base_identities = {(row["name_jp"], row["address"]) for row in _load_base_rows()}

    for shrine in seed.shrines:
        assert (shrine.name_jp, shrine.address) in base_identities


def test_wave0_db02_source_keys_are_resolved_and_no_fact_is_source_less():
    seed = _load_seed()
    known_sources = set(seed.sources)
    referenced = set()

    for shrine in seed.shrines:
        for fact in [*shrine.deities, *shrine.histories]:
            assert fact.source_keys, (shrine.name_jp, fact)
            assert set(fact.source_keys) <= known_sources
            referenced.update(fact.source_keys)

    # 参照されない Source を持ち込まない（既存 Knowledge Seed と同じ規約）。
    assert referenced == known_sources


def test_wave0_db02_per_shrine_fact_counts_are_frozen():
    seed = _load_seed()
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    assert set(by_name) == set(EXPECTED_FACT_COUNTS)
    for name, (deity_count, history_count) in EXPECTED_FACT_COUNTS.items():
        assert len(by_name[name].deities) == deity_count
        assert len(by_name[name].histories) == history_count


def test_wave0_db02_every_shrine_meets_shared_recommendation_eligibility():
    seed = _load_seed()

    for shrine in seed.shrines:
        usable_deities = 0
        usable_histories = 0
        for fact, bucket in (
            [(deity, "deity") for deity in shrine.deities]
            + [(history, "history") for history in shrine.histories]
        ):
            decision = evidence_gate.decide_fact_usability(
                verification_status=fact.verification_status,
                confidence=fact.confidence,
                source_verification_statuses=[
                    seed.sources[source_key].verification_status
                    for source_key in fact.source_keys
                ],
            )
            if not decision.usable:
                continue
            if bucket == "deity":
                usable_deities += 1
            else:
                usable_histories += 1

        # Shared Recommendation Eligibility:
        # usable Deity Fact >= 1 OR usable History Fact >= 1
        assert usable_deities >= 1 or usable_histories >= 1, shrine.name_jp


def test_wave0_db02_no_within_shrine_fact_duplicates():
    seed = _load_seed()

    for shrine in seed.shrines:
        deity_names = [deity.display_name for deity in shrine.deities]
        assert len(deity_names) == len(set(deity_names)), shrine.name_jp

        history_keys = [(history.history_type, history.title) for history in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_wave0_db02_all_facts_are_fact_ready_and_high_confidence():
    seed = _load_seed()

    for source in seed.sources.values():
        assert source.verification_status == "source_confirmed"
        assert source.confidence == "high"
        assert source.verified_at is not None

    for shrine in seed.shrines:
        for fact in [*shrine.deities, *shrine.histories]:
            assert fact.verification_status == "source_confirmed"
            assert fact.confidence == "high"
            assert fact.verified_at is not None


def test_wave0_db02_evidence_gate_accepts_all_seed_facts():
    seed = _load_seed()
    decisions = []

    for shrine in seed.shrines:
        for fact in [*shrine.deities, *shrine.histories]:
            decisions.append(
                evidence_gate.decide_fact_usability(
                    verification_status=fact.verification_status,
                    confidence=fact.confidence,
                    source_verification_statuses=[
                        seed.sources[source_key].verification_status
                        for source_key in fact.source_keys
                    ],
                )
            )

    assert len(decisions) == 19
    assert all(decision.usable for decision in decisions)


def test_wave0_db02_human_review_boundaries_are_preserved():
    seed = _load_seed()
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    # 射水神社: 二上神と瓊瓊杵尊を2柱へ分割しない（Packet 境界）。
    imizu = by_name["射水神社"]
    assert [deity.display_name for deity in imizu.deities] == ["二上神（瓊瓊杵尊）"]

    # 別小江神社: 創始伝承は保持しつつ、争いのある経過年数は持ち込まない。
    wakeoe = by_name["別小江神社"]
    assert [history.history_type for history in wakeoe.histories] == ["tradition"]
    founding = wakeoe.histories[0]
    assert "1300" not in founding.content
    assert "1700" not in founding.content
    assert "神功皇后" in founding.content

    # 戸隠神社 中社: 中社の祭神のみ。奥社・宝光社等を混載しない。
    togakushi = by_name["戸隠神社 中社"]
    assert [deity.display_name for deity in togakushi.deities] == ["天八意思兼命"]

    # 札幌諏訪神社 / 少彦名神社: Packet が確定した祭神のみ。
    assert [deity.display_name for deity in by_name["札幌諏訪神社"].deities] == [
        "建御名方命",
        "八坂刀売命",
    ]
    assert [deity.display_name for deity in by_name["少彦名神社"].deities] == [
        "少彦名命",
        "炎帝神農",
    ]
