import json
import re
from collections import Counter
from pathlib import Path


MASTER_PATH = (
    Path(__file__).resolve().parents[2]
    / "temples"
    / "data"
    / "shrine_expansion_candidate_master.json"
)

# Position Resolution Record の置き場所。Position 採用判断の Current 正本は
# `docs/knowledge/shrine-position-contract.md` を authority として、この
# directory の record が持つ（`scripts/audit_shrine_positions_v2.py` も同じ
# directory を glob して読む）。
#
# Candidate Master は Position provenance を所有しない。ここでは lifecycle
# 昇格の可否を判定するために record の `position_status` を**読むだけ**である。
POSITION_RESOLUTION_DIR = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "audit"
    / "shrine-position"
)

POSITION_HOLD = "HOLD_POSITION_REVIEW"

EXPECTED_STATUS_COUNTS = {
    "BUILD_READY": 21,
    "IMPORTED": 9,
    "CORE_READY": 5,
    "HOLD": 8,
    "REVIEW": 1,
}
EXPECTED_TOTAL = 44

# Data Build Batch を割り当てられた Candidate の lifecycle status。
#
#   BUILD_READY : Batch へ割り当て済み / Production import 未実施
#   IMPORTED    : Base Shrine と Batch 必須 Knowledge を Production へ write 済み
#   CORE_READY  : Completion Contract と post-import QA を完了済み
#
# `build_batch` は Data Build provenance であり lifecycle state ではない。
# BUILD_READY -> IMPORTED -> CORE_READY で消してはならない。HOLD / REVIEW は Batch 未割り当て
# なので `build_batch` は null のまま。
BATCH_ASSIGNED_STATUSES = frozenset({"BUILD_READY", "IMPORTED", "CORE_READY"})
UNASSIGNED_STATUSES = frozenset({"HOLD", "REVIEW"})

EXPECTED_REASON_COUNTS = {
    "WAVE0_CORE_READY_CANDIDATE": 35,
    "HOLD_MAPPING": 2,
    "SOURCE_HOLD": 3,
    "UNKNOWN_EVIDENCE": 3,
    "ENTITY_GRANULARITY_REVIEW": 1,
}

EXPECTED_HOLD_BY_REASON = {
    "HOLD_MAPPING": {"姫嶋神社", "行田八幡神社"},
    "SOURCE_HOLD": {"若宮八幡社", "富知六所浅間神社", "若宮神明社"},
    "UNKNOWN_EVIDENCE": {"居多神社", "唐澤山神社", "一之宮貫前神社"},
}

EXPECTED_REVIEW = {"諏訪大社 下社秋宮"}

# W0-B03 Namespace Reconciliation。
# Data Build Batch の canonical namespace は `W0-DB01`〜`W0-DB07`。
# 旧 `W0-B01`〜`W0-B07` は Wave0 の**工程ID**（W0-B01 = Base Shrine Seed Build /
# W0-B02 = Production Reconciliation）と衝突していたため、Data Build Batch 側だけを
# 改名した。工程ID は変更していない。
CANONICAL_BUILD_BATCHES = tuple(f"W0-DB0{n}" for n in range(1, 8))
LEGACY_BUILD_BATCHES = tuple(f"W0-B0{n}" for n in range(1, 8))

EXPECTED_BUILD_BATCH_COUNTS = {batch: 5 for batch in CANONICAL_BUILD_BATCHES}

# 次の Data Build target。member set を exact に固定する。
EXPECTED_W0_DB01_MEMBERS = {
    "三輪神社",
    "大鳥大社",
    "御岩神社",
    "烏森神社",
    "榴岡天満宮",
}

# W0-DB01 Production Import 完了後の lifecycle 実測値。
#
#   Base Shrine Import 成功 / Shrine total = 108 / exact match = 5 / missing = 0
#   Knowledge Import 成功 / Coverage 5/5 / Fact-ready Deity 5/5 / History 5/5
#
# CORE READY Completion Contract と post-transition alignment 完了後の状態を
# `CORE_READY` + `FACT_READY` として固定する。
EXPECTED_W0_DB01_STATUS = "CORE_READY"
EXPECTED_W0_DB01_KNOWLEDGE_STATUS = "FACT_READY"

# W0-DB02 は Production Import 完了後の状態。
#
# Candidate Master / Base Seed / Knowledge Seed は frozen Source Packet
# (docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md) から
# hydrate 済みで、Base / Knowledge とも Production へ write 済みのため
# `candidate_status` は `IMPORTED`。実測は
# docs/audit/shrine-expansion-wave0-db02-production-import.md。
#
# `IMPORTED` は Production write 完了だけを主張する。CORE_READY は
# Completion Contract 12/12 を要する別 Gate であり未判定。
EXPECTED_W0_DB02_MEMBERS = {
    "射水神社",
    "別小江神社",
    "戸隠神社 中社",
    "札幌諏訪神社",
    "少彦名神社",
}

EXPECTED_W0_DB02_STATUS = "IMPORTED"
EXPECTED_W0_DB02_KNOWLEDGE_STATUS = "FACT_READY"

# Seed Build 済みの batch。identity / official source / knowledge が
# hydrate 済みであることを共通で要求する。
HYDRATED_BUILD_BATCHES = ("W0-DB01", "W0-DB02")

# W0-DB03 は Mother Ship Decision A により original membership 5社のうち
# G4 execution subset の4社だけを hydrate する（凍結 Source Packet:
# docs/audit/shrine-expansion-wave0-db03-source-packet-freeze.md）。
# wave0-014 宮城縣護國神社は G3 MODEL_CHANGE_REQUIRED で隔離され未 hydrate。
#
# G7 Production Import 完了後（docs/audit/shrine-expansion-wave0-db03-production-import.md）、
# この4社は IMPORTED / FACT_READY。CORE_READY は G8 の別 Gate であり未判定。
# wave0-014 は G7 NOT EXECUTED で、BUILD_READY / 未 hydrate のまま。
W0_DB03_G4_HYDRATED_IDS = frozenset({"wave0-012", "wave0-013", "wave0-015", "wave0-016"})
W0_DB03_MODEL_HOLD_ID = "wave0-014"

REQUIRED_W0_DB01_HYDRATION_FIELDS = {
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

EXPECTED_W0_DB01_HYDRATION = {
    "三輪神社": {
        "official_name": "三輪神社",
        "official_address": "愛知県名古屋市中区大須3-9-32",
        "official_source_type": "shrine_official",
        "official_source_url": "https://miwajinnjya.com/guide/miwa-yuisyo/",
        "verified_at": "2026-09-12",
        "latitude": 35.1608797,
        "longitude": 136.9054313,
        "goriyaku": "厄除け",
        "goriyaku_tags": ["厄除け"],
    },
    "大鳥大社": {
        "official_name": "大鳥大社",
        "official_address": "大阪府堺市西区鳳北町1-1-2",
        "official_source_type": "shrine_official",
        "official_source_url": "https://www.ootoritaisha.jp/taisha/",
        "verified_at": "2026-09-12",
        "latitude": 34.5367778,
        "longitude": 135.4608611,
        "goriyaku": "家内安全・厄除け・安産・勝運・合格祈願・商売繁盛",
        "goriyaku_tags": [
            "家内安全",
            "厄除け",
            "安産",
            "勝運",
            "合格祈願",
            "商売繁盛",
        ],
    },
    "御岩神社": {
        "official_name": "御岩神社",
        "official_address": "茨城県日立市入四間町752",
        "official_source_type": "shrine_official",
        "official_source_url": "https://www.oiwajinja.jp/jinjasyoukai.html",
        "verified_at": "2026-09-12",
        "latitude": 36.63604985,
        "longitude": 140.58558306,
        "goriyaku": "安産・家内安全・厄除け・開運・病気平癒・商売繁盛・縁結び",
        "goriyaku_tags": [
            "安産",
            "家内安全",
            "厄除け",
            "開運",
            "病気平癒",
            "商売繁盛",
            "縁結び",
        ],
    },
    "烏森神社": {
        "official_name": "烏森神社",
        "official_address": "東京都港区新橋2-15-5",
        "official_source_type": "shrine_official",
        "official_source_url": "https://karasumorijinja.or.jp/烏森神社について",
        "verified_at": "2026-09-12",
        "latitude": 35.666443,
        "longitude": 139.756134,
        "goriyaku": "商売繁盛・技芸上達・家内安全・勝運",
        "goriyaku_tags": ["商売繁盛", "技芸上達", "家内安全", "勝運"],
    },
    "榴岡天満宮": {
        "official_name": "榴岡天満宮",
        "official_address": "宮城県仙台市宮城野区榴ケ岡105-3",
        "official_source_type": "shrine_official",
        "official_source_url": "https://tsutsujigaokatenmangu.jp/about/",
        "verified_at": "2026-09-12",
        "latitude": 38.260624,
        "longitude": 140.893021,
        "goriyaku": "合格祈願・学業成就・厄除け・安産・交通安全・商売繁盛",
        "goriyaku_tags": [
            "合格祈願",
            "学業成就",
            "厄除け",
            "安産",
            "交通安全",
            "商売繁盛",
        ],
    },
}


CANONICAL_POSITION_STATUSES = frozenset({"PASS", POSITION_HOLD})


def _held_position_candidate_ids() -> tuple[set[str], int]:
    """HOLD 中の candidate_id 集合と、走査した record 件数を返す。

    値は record から直接 parse する。テスト側へ転記すると転記が正本に
    なってしまうため、期待値をここへ書かない。

    判定規則は **fail closed** である。1 record 内の `^position_status` 行の
    うち **1つでも** `HOLD_POSITION_REVIEW` があれば、その candidate は HOLD
    として扱う。

    record は凍結 Source Packet の内容を逐語引用することがあり、その引用が
    `position_status = PASS` を含みうる（`imizu-jinja-position-resolution.md`
    は Packet の旧 Position ブロックをそのまま引用している）。
    `scripts/audit_shrine_positions_v2.py` は「最初の一致」を採るが、guard は
    report ではなく昇格の可否を決めるため、ブロックの並び順で結果が変わる
    規則を採らない。**HOLD の痕跡がある record は昇格させない**、が本 guard の
    規則である。

    `old_position_status` は行頭が一致しないため拾わない（過去の状態であり
    Current 正本ではない）。
    """
    held: set[str] = set()
    seen: set[str] = set()
    record_count = 0
    for path in sorted(POSITION_RESOLUTION_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        candidate_ids = set(re.findall(r"^candidate_id\s+= (\S+)$", text, re.M))
        statuses = set(re.findall(r"^position_status\s+= (\S+)$", text, re.M))
        if not candidate_ids or not statuses:
            continue

        # 1 record = 1 candidate。複数 candidate を混ぜた record は、どの
        # status がどの candidate のものか決められないので弾く。
        assert len(candidate_ids) == 1, (path.name, sorted(candidate_ids))
        # 未知の status を「HOLD ではない」と黙って解釈しない。
        unknown = statuses - CANONICAL_POSITION_STATUSES
        assert not unknown, (path.name, sorted(unknown))

        candidate_id = candidate_ids.pop()
        assert candidate_id not in seen, (path.name, candidate_id)
        seen.add(candidate_id)
        record_count += 1
        if POSITION_HOLD in statuses:
            held.add(candidate_id)
    return held, record_count


def test_position_hold_candidates_are_never_core_ready():
    """`HOLD_POSITION_REVIEW` の Candidate を `CORE_READY` へ昇格させない。

    Position Contract §HOLD_POSITION_REVIEW は HOLD 中に座標を Seed /
    Production へ投入しないことを求めるが、**lifecycle 昇格を止める実行可能な
    guard はこれまで存在しなかった**。

    - Shared Recommendation Eligibility は usable Deity / History Fact だけで
      判定し、Position を読まない（`concierge_chat_candidates.is_recommendation_eligible`）。
    - Post-Import CORE READY QA の Position 項目は座標一致と Compass 計算の
      成否だけで、Position status を見ない。
    - `candidate_status` を書き換える実行コードは存在せず、Candidate Master は
      手編集 + テスト検証で守られている。

    したがって HOLD の Candidate が `CORE_READY` へ進める経路が開いていた。
    この guard はその経路だけを塞ぐ。Position 判断そのものは行わず、
    Resolution Record の `position_status` を読むだけである。

    eligibility rule には触れない（Knowledge ベースの判定式であり、Position
    governance を混ぜると責務が壊れるため）。
    """
    held, record_count = _held_position_candidate_ids()

    # record を1件も読めていないのに無言で通過し、guard として機能しなく
    # なることを防ぐ（path の typo / directory 移動の検知）。
    assert record_count, "no Position Resolution Record found in %s" % POSITION_RESOLUTION_DIR

    rows = {row["candidate_id"]: row for row in _load_master()["candidates"]}

    for candidate_id in sorted(held):
        row = rows.get(candidate_id)
        # record はあるが Candidate Master に居ない、は昇格の危険が無いので許す。
        if row is None:
            continue
        assert row["candidate_status"] != "CORE_READY", (
            candidate_id,
            row["candidate_status"],
            "Position status is %s; CORE_READY promotion is blocked until the "
            "Position Resolution Record reaches PASS." % POSITION_HOLD,
        )


def _load_master() -> dict:
    return json.loads(MASTER_PATH.read_text(encoding="utf-8"))


def _effective(master: dict, row: dict) -> dict:
    return {**master.get("candidate_defaults", {}), **row}


def test_wave0_candidate_master_registry_accounting():
    master = _load_master()
    candidates = master["candidates"]

    assert master["schema_version"] == "1.2"
    assert len(candidates) == EXPECTED_TOTAL
    assert len({row["candidate_id"] for row in candidates}) == EXPECTED_TOTAL
    assert Counter(row["candidate_status"] for row in candidates) == EXPECTED_STATUS_COUNTS
    assert Counter(row["status_reason_code"] for row in candidates) == EXPECTED_REASON_COUNTS


def test_wave0_batch_membership_is_deterministic():
    """Batch 割り当ては 7 batch x 5 社で固定。

    初期 Registry 時点では 35 社すべてが `BUILD_READY` だったが、これは
    その時点のスナップショットであって恒久ルールではない。Batch 割り当ての
    不変条件は status ではなく「`build_batch` が付いた行の分布」である。
    """
    candidates = _load_master()["candidates"]
    assigned = [row for row in candidates if row["build_batch"] is not None]

    assert len(assigned) == 35
    assert Counter(row["build_batch"] for row in assigned) == EXPECTED_BUILD_BATCH_COUNTS
    assert all(row["candidate_status"] in BATCH_ASSIGNED_STATUSES for row in assigned)


def test_build_batch_survives_the_import_lifecycle_transition():
    """`build_batch` は Data Build provenance であり lifecycle state ではない。

    BUILD_READY -> IMPORTED -> CORE_READY で消してはならない。消すと
    「どの Batch で Production へ入ったのか」が追跡不能になる。
    """
    candidates = _load_master()["candidates"]

    imported_or_core_ready = [row for row in candidates if row["candidate_status"] in {"IMPORTED", "CORE_READY"}]
    assert len(imported_or_core_ready) == 14
    assert Counter(row["build_batch"] for row in imported_or_core_ready) == {
        "W0-DB01": 5,
        "W0-DB02": 5,
        "W0-DB03": 4,
    }
    assert all(_effective(_load_master(), row)["knowledge_status"] == "FACT_READY" for row in imported_or_core_ready)

    # Batch 未割り当ての lifecycle state は null を維持する。
    assert all(
        row["build_batch"] is None
        for row in candidates
        if row["candidate_status"] in UNASSIGNED_STATUSES
    )


def test_w0_db03_to_db07_stay_build_ready():
    """Production Import 済みは W0-DB01 / W0-DB02 と W0-DB03 の G7 execution subset 4社。

    W0-DB03 は original membership 5社のまま、4社 IMPORTED / wave0-014 BUILD_READY の
    混在状態である。W0-DB04〜W0-DB07 の 20 社は BUILD_READY のまま。
    """
    candidates = _load_master()["candidates"]

    db03 = {row["candidate_id"]: row for row in candidates if row["build_batch"] == "W0-DB03"}
    assert len(db03) == 5
    assert set(db03) == W0_DB03_G4_HYDRATED_IDS | {W0_DB03_MODEL_HOLD_ID}
    for candidate_id in W0_DB03_G4_HYDRATED_IDS:
        assert db03[candidate_id]["candidate_status"] == "IMPORTED", candidate_id
        assert db03[candidate_id]["knowledge_status"] == "FACT_READY", candidate_id
    assert db03[W0_DB03_MODEL_HOLD_ID]["candidate_status"] == "BUILD_READY"

    for batch in CANONICAL_BUILD_BATCHES[3:]:
        members = [row for row in candidates if row["build_batch"] == batch]
        assert len(members) == 5, batch
        assert all(row["candidate_status"] == "BUILD_READY" for row in members), batch


def test_wave0_build_batch_uses_the_canonical_db_namespace_only():
    """legacy `W0-B01`〜`W0-B07` が build_batch として残っていないこと。

    これらは Wave0 の工程ID と同じ文字列であり、Candidate Master 内に
    残っていると工程とデータバッチが区別できなくなる。
    """
    candidates = _load_master()["candidates"]

    batches = {row["build_batch"] for row in candidates if row["build_batch"] is not None}
    assert batches == set(CANONICAL_BUILD_BATCHES)

    legacy = [
        (row["candidate_id"], row["build_batch"])
        for row in candidates
        if row["build_batch"] in LEGACY_BUILD_BATCHES
    ]
    assert legacy == []


def test_wave0_db01_member_set_is_frozen():
    """次の Data Build target `W0-DB01` の member set を exact に固定する。"""
    candidates = _load_master()["candidates"]

    members = {
        row["candidate_name"]
        for row in candidates
        if row["build_batch"] == "W0-DB01"
    }
    assert members == EXPECTED_W0_DB01_MEMBERS

    # Production Import 完了後は全員 IMPORTED（HOLD / REVIEW が混ざらない）。
    assert all(
        row["candidate_status"] == EXPECTED_W0_DB01_STATUS
        for row in candidates
        if row["build_batch"] == "W0-DB01"
    )


def test_wave0_db01_candidates_are_hydrated_from_frozen_source_packet():
    master = _load_master()
    rows = {
        row["candidate_name"]: row
        for row in master["candidates"]
        if row["build_batch"] == "W0-DB01"
    }

    assert set(rows) == EXPECTED_W0_DB01_MEMBERS

    for name, expected in EXPECTED_W0_DB01_HYDRATION.items():
        row = rows[name]
        effective = _effective(master, row)

        assert REQUIRED_W0_DB01_HYDRATION_FIELDS <= row.keys()
        assert effective["identity_status"] == "CONFIRMED"
        assert effective["official_source_status"] == "CONFIRMED"
        assert effective["knowledge_status"] == EXPECTED_W0_DB01_KNOWLEDGE_STATUS
        assert row["candidate_status"] == EXPECTED_W0_DB01_STATUS
        assert row["build_batch"] == "W0-DB01"
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE"
        assert row["duplicate_status"] == "NEW"

        for field, expected_value in expected.items():
            assert row[field] == expected_value


def test_wave0_db02_candidates_are_hydrated_and_imported():
    """W0-DB02 は Production Import 完了状態。IMPORTED だが CORE_READY ではない。

    座標・canonical identity の値そのものは frozen Source Packet と突き合わせる
    `test_wave0_db02_shrine_seed.py` 側で固定する。ここでは Registry 上の
    lifecycle と hydration の有無だけを契約として持つ。
    """
    master = _load_master()
    rows = {
        row["candidate_name"]: row
        for row in master["candidates"]
        if row["build_batch"] == "W0-DB02"
    }

    assert set(rows) == EXPECTED_W0_DB02_MEMBERS

    for name, row in rows.items():
        effective = _effective(master, row)

        assert REQUIRED_W0_DB01_HYDRATION_FIELDS <= row.keys(), name
        assert effective["identity_status"] == "CONFIRMED", name
        assert effective["official_source_status"] == "CONFIRMED", name
        assert effective["knowledge_status"] == EXPECTED_W0_DB02_KNOWLEDGE_STATUS, name
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE", name
        assert row["duplicate_status"] == "NEW", name

        # Production import 済み。CORE_READY は別 Gate のため進めない。
        assert row["candidate_status"] == EXPECTED_W0_DB02_STATUS, name


def test_wave0_db03_to_db07_remain_unhydrated():
    """Seed Build 未着手の batch に hydration fields を持ち込まない。

    W0-DB03 は G4 execution subset の4社だけが hydrate 済み。
    wave0-014 を含む残りは未 hydrate のまま。
    """
    master = _load_master()

    for batch in CANONICAL_BUILD_BATCHES:
        if batch in HYDRATED_BUILD_BATCHES:
            continue
        for row in master["candidates"]:
            if row["build_batch"] != batch:
                continue
            if row["candidate_id"] in W0_DB03_G4_HYDRATED_IDS:
                continue
            leaked = REQUIRED_W0_DB01_HYDRATION_FIELDS & row.keys()
            assert not leaked, (batch, row["candidate_id"], sorted(leaked))


def test_wave0_hold_and_review_candidates_stay_separated():
    candidates = _load_master()["candidates"]

    for reason, expected_names in EXPECTED_HOLD_BY_REASON.items():
        actual_names = {
            row["candidate_name"]
            for row in candidates
            if row["status_reason_code"] == reason
        }
        assert actual_names == expected_names
        assert all(
            row["candidate_status"] == "HOLD"
            for row in candidates
            if row["status_reason_code"] == reason
        )

    review_names = {
        row["candidate_name"]
        for row in candidates
        if row["status_reason_code"] == "ENTITY_GRANULARITY_REVIEW"
    }
    assert review_names == EXPECTED_REVIEW
    assert all(
        row["candidate_status"] == "REVIEW"
        for row in candidates
        if row["candidate_name"] in EXPECTED_REVIEW
    )


def test_wave0_duplicate_and_availability_states_match_completed_audits():
    master = _load_master()
    candidates = master["candidates"]

    assert Counter(row["duplicate_status"] for row in candidates) == {
        "NEW": 43,
        "REVIEW": 1,
    }

    for row in candidates:
        effective = _effective(master, row)
        if row["build_batch"] in HYDRATED_BUILD_BATCHES:
            assert effective["identity_status"] == "CONFIRMED"
            assert effective["official_source_status"] == "CONFIRMED"
            assert effective["knowledge_status"] == "FACT_READY"
        elif row["candidate_id"] in W0_DB03_G4_HYDRATED_IDS:
            assert effective["identity_status"] == "CONFIRMED"
            assert effective["official_source_status"] == "CONFIRMED"
            assert effective["knowledge_status"] == "FACT_READY"
        elif row["candidate_status"] == "REVIEW":
            assert effective["identity_status"] == "UNREVIEWED"
            assert effective["official_source_status"] == "UNREVIEWED"
            assert effective["knowledge_status"] == "UNREVIEWED"
        else:
            assert effective["identity_status"] == "UNREVIEWED"
            assert effective["official_source_status"] == "AVAILABLE"
            assert effective["knowledge_status"] == "ACQUISITION_PATH_CONFIRMED"


def test_candidate_defaults_are_not_promoted_by_a_single_batch_import():
    """W0-DB01 の FACT_READY は行レベルの事実であり、Registry 全体の既定ではない。

    `candidate_defaults` を FACT_READY にすると、未 import の 39 社まで
    「Production 上で usable Knowledge が確認済み」と読めてしまう。
    """
    defaults = _load_master()["candidate_defaults"]

    assert defaults["knowledge_status"] == "ACQUISITION_PATH_CONFIRMED"
    assert defaults["identity_status"] == "UNREVIEWED"
    assert defaults["official_source_status"] == "AVAILABLE"


def test_wave0_discovery_provenance_has_required_fields():
    master = _load_master()
    required = set(master["required_discovery_fields"])

    for row in master["candidates"]:
        assert row["discovery_sources"]
        for source in row["discovery_sources"]:
            assert required <= source.keys()
            assert source["discovery_source"] == "Omairi 全国神社人気ランキング2026"
            assert source["discovery_source_url"].startswith(
                "https://omairi.club/spots/ranking/shrine"
            )
            assert isinstance(source["discovery_rank"], int)
            assert source["captured_at"]
