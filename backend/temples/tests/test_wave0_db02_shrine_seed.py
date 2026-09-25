"""W0-DB02 (射水神社 / 別小江神社 / 戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社).

このモジュールは W0-DB02 の3成果物を、凍結済み Source Packet に対して固定する。

- Candidate Master 行 wave0-007..011
- Base Seed 行（`shrines_seed_clean.json`）
- Knowledge Seed（`wave0_batch_02_seed.json`）

canonical identity・Knowledge Fact・goriyaku は Packet markdown から直接
読み出して比較する。テスト側に期待値を転記すると、転記が正本になってしまうため。

Position だけは正本が分かれる。凍結 Packet は 2026-09-15 時点の記録であり、
freeze 以後に人間 map QA で Visitor / Navigation Anchor を再解決した候補は
`docs/audit/shrine-position/` の Position Resolution Record が Current 正本に
なる（`docs/knowledge/shrine-position-contract.md`）。

したがって Position の検証は次の2系統に分ける。

- 再解決されていない候補 : 凍結 Packet の値と厳密一致すること
- 再解決された候補       : Resolution Record の値に従うこと

Packet を無条件に Current Position 正本として扱うと、freeze 後の QA 結果を
反映した時点でテストが必ず落ちる。それは検知ではなく構造的欠陥なので、
「Packet = 過去の凍結 / Record = 現在の Position」として責務を分離する。
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

# Source Packet Freeze 以後に Position を再解決した候補と、その Current 正本。
# ここに載らない候補の Position は凍結 Packet が Current 正本のままである。
POSITION_RESOLUTION_PATHS = {
    "wave0-007": (
        REPO_ROOT
        / "docs"
        / "audit"
        / "shrine-position"
        / "imizu-jinja-position-resolution.md"
    ),
    "wave0-010": (
        REPO_ROOT
        / "docs"
        / "audit"
        / "shrine-position"
        / "sapporo-suwa-jinja-position-resolution.md"
    ),
}

CANDIDATE_IDS = ["wave0-007", "wave0-008", "wave0-009", "wave0-010", "wave0-011"]

# Position が凍結 Packet のままである候補。
POSITION_FROZEN_CANDIDATE_IDS = [
    candidate_id
    for candidate_id in CANDIDATE_IDS
    if candidate_id not in POSITION_RESOLUTION_PATHS
]

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
            # 凍結 Packet 側に旧採用点の URL が実在するか。record の
            # `NOT_RECORDED_IN_SOURCE_PACKET` 宣言を裏取りするために読む。
            "position_source_url": (
                match.group(1).strip()
                if (
                    match := re.search(
                        r"^position_source_url\s+= (.+)$", block, re.M
                    )
                )
                else None
            ),
            # 文字列のまま保持する。float 経由で丸めると等値検証の意味が失われる。
            "latitude": re.search(r"^latitude\s+= (\S+)", block, re.M).group(1),
            "longitude": re.search(r"^longitude\s+= (\S+)", block, re.M).group(1),
        }
    return entries


PENDING = "PENDING_HUMAN_QA_INPUT"

# 凍結 Packet が旧採用点に対応する `position_source_url` を記録していない状態。
#
# URL field へ偽の URL や非 URL sentinel を入れると、以後の機械読取が
# 「URL が存在する」と誤認する。そのため record は `old_position_source_url`
# field 自体を持たず、専用の status field でその不在を宣言する。
#
# この表現は Position Resolution Record format のものであり、
# `docs/knowledge/shrine-position-contract.md`（採用ルールの authority）は
# `old_*` 系 field を定義していない。authority 側は変更しない。
SOURCE_URL_NOT_RECORDED = "NOT_RECORDED_IN_SOURCE_PACKET"


def _load_position_resolution(candidate_id):
    """Position Resolution Record を markdown から読み出す。

    Packet と同じく、値は record 側を直接パースする。テストへ転記しない。
    """
    text = POSITION_RESOLUTION_PATHS[candidate_id].read_text(encoding="utf-8")

    def optional_field(name):
        match = re.search(r"^%s\s+= (.+)$" % re.escape(name), text, re.M)
        return match.group(1).strip() if match else None

    def field(name):
        value = optional_field(name)
        assert value is not None, "%s not found in %s" % (name, candidate_id)
        return value

    return {
        "candidate_id": field("candidate_id"),
        "official_name": field("official_name"),
        "official_address": field("official_address"),
        "position_status": field("position_status"),
        "old_latitude": field("old_latitude"),
        "old_longitude": field("old_longitude"),
        # 旧採用点の URL が記録されていない record が存在しうるため optional。
        # 不在は `old_position_source_url_status` で明示的に宣言させる。
        "old_position_source_url": optional_field("old_position_source_url"),
        "old_position_source_url_status": optional_field(
            "old_position_source_url_status"
        ),
        "latitude": field("new_latitude"),
        "longitude": field("new_longitude"),
        "position_source_type": field("new_position_source_type"),
        "position_source_url": field("new_position_source_url"),
        "coordinate_delta_m": field("coordinate_delta_m"),
    }


def _current_position(candidate_id, packet):
    """その候補の Current Position 正本を返す。

    再解決済みなら Resolution Record、未再解決なら凍結 Packet。
    再解決が HOLD_POSITION_REVIEW の間は採用値が存在しないため None を返す。
    """
    if candidate_id not in POSITION_RESOLUTION_PATHS:
        frozen = packet[candidate_id]
        return frozen["latitude"], frozen["longitude"]

    record = _load_position_resolution(candidate_id)
    if record["position_status"] != "PASS":
        return None
    return record["latitude"], record["longitude"]


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


def test_wave0_db02_packet_freeze_is_readable_and_all_pass_at_freeze_time():
    """凍結 Packet 自体は 2026-09-15 時点の記録として不変であること。

    ここでの `PASS` は freeze 時点の判定であり、現在の Position 正本ではない。
    freeze 後に再解決された候補の Current Position は
    `POSITION_RESOLUTION_PATHS` 側が持つ。
    """
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


def test_wave0_db02_candidates_are_imported_after_production_import():
    """W0-DB02 は Base / Knowledge とも Production Import 完了済み。

    実測は `docs/audit/shrine-expansion-wave0-db02-production-import.md`。

    `IMPORTED` が主張するのは Production への write 完了だけである
    （`docs/knowledge/shrine-expansion-candidate-master-contract.md`）。
    CORE_READY は Completion Contract 12/12 を要する別 Gate であり、
    ここでは判定しない。Recommendation eligibility も `candidate_status`
    ではなく別 Gate が表す（W0-DB02 は 5/5 PASS を実測済みだが、それは
    `IMPORTED` の意味ではない）。

    `build_batch` は lifecycle state ではなく Data Build provenance なので、
    BUILD_READY -> IMPORTED の遷移でも `W0-DB02` のまま不変である。
    """
    candidates = _load_candidates()

    for candidate_id in CANDIDATE_IDS:
        row = candidates[candidate_id]
        assert row["build_batch"] == "W0-DB02"
        assert row["candidate_status"] == "IMPORTED"
        # Knowledge の質は candidate_status ではなく knowledge_status が表す。
        assert row["knowledge_status"] == "FACT_READY"


def test_wave0_db02_unresolved_shrines_keep_the_frozen_packet_position():
    """Position を再解決していない候補は、凍結 Packet と完全一致し続ける。

    これは「他4社に diff が無い」ことの固定でもある。
    """
    packet = _load_packet_identities()
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    # `wave0-007` は Position Resolution Record（HOLD_POSITION_REVIEW）を
    # 持つため、この pin の対象ではない。HOLD 中に Seed 座標が動かないことは
    # `test_hold_position_review_freezes_the_existing_seed_coordinate` が守る。
    assert POSITION_FROZEN_CANDIDATE_IDS == [
        "wave0-008",
        "wave0-009",
        "wave0-011",
    ]

    for candidate_id in POSITION_FROZEN_CANDIDATE_IDS:
        frozen = packet[candidate_id]
        master_row = candidates[candidate_id]
        base_row = base_rows[(frozen["official_name"], frozen["official_address"])]

        # repr 比較にすることで、桁落ち・丸め・再計算を検出する。
        assert repr(master_row["latitude"]) == frozen["latitude"], candidate_id
        assert repr(master_row["longitude"]) == frozen["longitude"], candidate_id
        assert repr(base_row["latitude"]) == frozen["latitude"], candidate_id
        assert repr(base_row["longitude"]) == frozen["longitude"], candidate_id


def test_wave0_db02_position_resolution_records_are_wellformed():
    """再解決 record が Position Contract の要求項目を保持していること。"""
    packet = _load_packet_identities()

    for candidate_id in POSITION_RESOLUTION_PATHS:
        record = _load_position_resolution(candidate_id)
        frozen = packet[candidate_id]

        assert record["candidate_id"] == candidate_id
        # identity は Position correction で変更しない。
        assert record["official_name"] == frozen["official_name"]
        assert record["official_address"] == frozen["official_address"]
        # 旧値は凍結 Packet の値を逐語で保持する（履歴として追跡可能にする）。
        assert record["old_latitude"] == frozen["latitude"]
        assert record["old_longitude"] == frozen["longitude"]
        # 旧 source URL は「URL が記録されている」か「記録が無いと明示宣言
        # されている」かのどちらかでなければならない。URL field へ sentinel を
        # 入れて truthiness だけ満たす表現は許さない。
        url = record["old_position_source_url"]
        url_status = record["old_position_source_url_status"]
        if url_status == SOURCE_URL_NOT_RECORDED:
            # 宣言した以上、URL field は本当に存在しないこと。
            assert url is None, (candidate_id, url)
            # 宣言の裏取り: 凍結 Packet 側にも実際に URL が無いこと。
            # Packet に URL があるのに未記録と宣言する record を弾く。
            assert frozen["position_source_url"] is None, candidate_id
        else:
            assert url_status is None, (candidate_id, url_status)
            assert url and url.startswith("http"), (candidate_id, url)
            assert url == frozen["position_source_url"], candidate_id

        assert record["position_status"] in ("PASS", "HOLD_POSITION_REVIEW")

        if record["position_status"] == "PASS":
            # 採用済みなら、推測値ではない実値と Source が揃っていること。
            for key in (
                "latitude",
                "longitude",
                "position_source_type",
                "position_source_url",
                "coordinate_delta_m",
            ):
                assert record[key] != PENDING, (candidate_id, key)
            assert float(record["latitude"])
            assert float(record["longitude"])
            # 再解決した以上、旧座標と同じ値ではないはず。
            assert (record["latitude"], record["longitude"]) != (
                record["old_latitude"],
                record["old_longitude"],
            )


def test_wave0_db02_resolved_shrine_position_follows_the_resolution_record():
    """再解決済み候補の Seed / Candidate Master は Resolution Record に従う。

    `HOLD_POSITION_REVIEW` の間は採用値が存在しない。Position Contract
    「HOLD 状態では座標を推測して Seed / Production へ投入しない」に従い、
    この間は Seed へ新座標を書かない。旧座標が残っている場合も、それは
    `PASS` ではなく HOLD 中の未反映状態として扱う。
    """
    packet = _load_packet_identities()
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    for candidate_id in POSITION_RESOLUTION_PATHS:
        record = _load_position_resolution(candidate_id)
        adopted = _current_position(candidate_id, packet)
        master_row = candidates[candidate_id]
        base_row = base_rows[
            (record["official_name"], record["official_address"])
        ]

        if adopted is None:
            # HOLD 中: 採用値が無いので Seed へ新座標を投入していないこと。
            assert record["latitude"] == PENDING, candidate_id
            assert record["longitude"] == PENDING, candidate_id
            continue

        latitude, longitude = adopted
        assert repr(master_row["latitude"]) == latitude, candidate_id
        assert repr(master_row["longitude"]) == longitude, candidate_id
        assert repr(base_row["latitude"]) == latitude, candidate_id
        assert repr(base_row["longitude"]) == longitude, candidate_id


def test_hold_position_review_freezes_the_existing_seed_coordinate():
    """HOLD 中は Base Seed / Candidate Master の座標が凍結 Packet のまま動かない。

    `POSITION_FROZEN_CANDIDATE_IDS` の pin は「Resolution Record を持たない
    候補」しか守らない。HOLD の Record を持つ候補はその対象から外れるため、
    採用値が確定するまで座標が書き換わらないことをここで別途固定する。

    Position Contract §HOLD_POSITION_REVIEW
    「HOLD状態では座標を推測してSeed / Productionへ投入しない」。

    旧座標が残っていること自体は `PASS` を意味しない。HOLD 中の未反映状態
    である（`test_wave0_db02_resolved_shrine_position_follows_the_resolution_record`
    の docstring と同じ扱い）。
    """
    packet = _load_packet_identities()
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    held = [
        candidate_id
        for candidate_id in POSITION_RESOLUTION_PATHS
        if _load_position_resolution(candidate_id)["position_status"]
        == "HOLD_POSITION_REVIEW"
    ]
    assert held == ["wave0-007"]

    for candidate_id in held:
        frozen = packet[candidate_id]
        master_row = candidates[candidate_id]
        base_row = base_rows[(frozen["official_name"], frozen["official_address"])]

        # repr 比較にすることで、桁落ち・丸め・再計算を検出する。
        assert repr(master_row["latitude"]) == frozen["latitude"], candidate_id
        assert repr(master_row["longitude"]) == frozen["longitude"], candidate_id
        assert repr(base_row["latitude"]) == frozen["latitude"], candidate_id
        assert repr(base_row["longitude"]) == frozen["longitude"], candidate_id

        # HOLD 中に location だけが差し替わる経路も塞ぐ。
        assert base_row["location"] == {
            "lat": base_row["latitude"],
            "lng": base_row["longitude"],
        }, candidate_id

        # 採用値を持たないこと（推測値が record へ入っていないこと）。
        record = _load_position_resolution(candidate_id)
        assert record["latitude"] == PENDING, candidate_id
        assert record["longitude"] == PENDING, candidate_id
        assert _current_position(candidate_id, packet) is None, candidate_id


def test_wave0_db02_base_seed_location_mirrors_latitude_longitude():
    """`location` は常に `latitude` / `longitude` と完全一致する。

    Position を再解決した候補でも、この対応が崩れないことを固定する。
    """
    packet = _load_packet_identities()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    for candidate_id in CANDIDATE_IDS:
        frozen = packet[candidate_id]
        base_row = base_rows[(frozen["official_name"], frozen["official_address"])]

        assert base_row["location"] == {
            "lat": base_row["latitude"],
            "lng": base_row["longitude"],
        }, candidate_id


def test_wave0_db02_candidate_master_and_base_seed_positions_always_agree():
    """Position 正本がどちらでも、Candidate Master と Base Seed は一致する。"""
    packet = _load_packet_identities()
    candidates = _load_candidates()
    base_rows = {(row["name_jp"], row["address"]): row for row in _load_base_rows()}

    for candidate_id in CANDIDATE_IDS:
        frozen = packet[candidate_id]
        master_row = candidates[candidate_id]
        base_row = base_rows[(frozen["official_name"], frozen["official_address"])]

        assert master_row["latitude"] == base_row["latitude"], candidate_id
        assert master_row["longitude"] == base_row["longitude"], candidate_id


def test_wave0_db02_base_seed_appends_five_rows_without_duplicates():
    packet = _load_packet_identities()
    base_rows = _load_base_rows()
    identities = [(row["name_jp"], row["address"]) for row in base_rows]

    # W0-DB03 G4 で4行（wave0-012 / 013 / 015 / 016）を追加し 113 -> 117。
    assert len(base_rows) == 117
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
