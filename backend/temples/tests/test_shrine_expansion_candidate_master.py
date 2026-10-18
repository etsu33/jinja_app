import json
import re
from collections import Counter
from pathlib import Path

import pytest


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
    "BUILD_READY": 17,
    "IMPORTED": 5,
    "CORE_READY": 12,
    "HOLD": 9,
    "REVIEW": 1,
}
EXPECTED_WAVE0_TOTAL = 44

WAVE0_ID_RE = re.compile(r"^wave0-[0-9]{3}$")
NATIONWIDE_ID_RE = re.compile(r"^nsrc-[0-9]{6}$")
CANONICAL_CANDIDATE_STATUSES = frozenset(
    {"DISCOVERED", "BUILD_READY", "IMPORTED", "CORE_READY", "HOLD", "REVIEW"}
)
NATIONWIDE_CANDIDATE_REASON = "official_source_full_enumeration_candidate"
NATIONWIDE_TRACK = "nationwide_source_candidate"
NATIONWIDE_PROVENANCE_FIELDS = frozenset(
    {
        "track",
        "prefecture",
        "source_batch_id",
        "handoff_id",
        "source_position",
        "source_snapshot_sha256",
        "source_url",
        "source_verified_at",
        "captured_at",
    }
)
NATIONWIDE_POSITIVE_STATUS_REASONS = {
    "DISCOVERED": "REGISTRY_ADMISSION_COMPLETE",
    "BUILD_READY": "BUILD_READINESS_CONFIRMED",
    "IMPORTED": "PRODUCTION_IMPORT_COMPLETE",
    "CORE_READY": "CORE_READY_CONTRACT_PASS",
}
NATIONWIDE_IDENTITY_STATUSES = frozenset({"UNREVIEWED", "CONFIRMED"})
NATIONWIDE_DUPLICATE_STATUSES = frozenset(
    {
        "UNREVIEWED",
        "NEW",
        "DUPLICATE",
        "ALIAS",
        "SAME_NAME_DIFFERENT_SHRINE",
        "REVIEW",
    }
)
NATIONWIDE_OFFICIAL_SOURCE_STATUSES = frozenset(
    {"UNREVIEWED", "AVAILABLE", "CONFIRMED", "HOLD"}
)
NATIONWIDE_KNOWLEDGE_STATUSES = frozenset(
    {"UNREVIEWED", "ACQUISITION_PATH_CONFIRMED", "FACT_READY", "HOLD"}
)

# Data Build Batch を割り当てられた Candidate の lifecycle status。
#
#   BUILD_READY : Batch へ割り当て済み / Production import 未実施
#   IMPORTED    : Base Shrine と Batch 必須 Knowledge を Production へ write 済み
#   CORE_READY  : Completion Contract と post-import QA を完了済み
#
# `build_batch` は Data Build provenance であり lifecycle state ではない。
# 一度割り当てたら不変で、BUILD_READY -> IMPORTED -> CORE_READY でも、
# Batch 割り当て後の HOLD / REVIEW への遷移でも消してはならない（schema 1.3）。
#
# BATCH_ASSIGNED_STATUSES の行は必ず build_batch を持つ。HOLD / REVIEW は
# build_batch = null（Batch 割り当て前に停止）/ 非null（割り当て後に停止）のどちらもあり得る。
BATCH_ASSIGNED_STATUSES = frozenset({"BUILD_READY", "IMPORTED", "CORE_READY"})
UNASSIGNED_STATUSES = frozenset({"HOLD", "REVIEW"})

# Batch 割り当て後に HOLD / REVIEW となった Candidate と、その保持 build_batch。
# exact に固定する（ここに無い post-batch HOLD / REVIEW は test failure）。
EXPECTED_POST_BATCH_HOLDS = {"wave0-014": "W0-DB03"}

# status_reason_code は現在の candidate_status の理由（schema 1.3）。
# Registry への登録理由は candidate_reason が表す。
EXPECTED_REASON_COUNTS = {
    "WAVE0_CORE_READY_CANDIDATE": 34,
    "HOLD_MAPPING": 2,
    "SOURCE_HOLD": 3,
    "UNKNOWN_EVIDENCE": 3,
    "MODEL_CHANGE_REQUIRED": 1,
    "ENTITY_GRANULARITY_REVIEW": 1,
}

EXPECTED_HOLD_BY_REASON = {
    "HOLD_MAPPING": {"姫嶋神社", "行田八幡神社"},
    "SOURCE_HOLD": {"若宮八幡社", "富知六所浅間神社", "若宮神明社"},
    "UNKNOWN_EVIDENCE": {"居多神社", "唐澤山神社", "一之宮貫前神社"},
    "MODEL_CHANGE_REQUIRED": {"宮城縣護國神社"},
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
# この4社は IMPORTED / FACT_READY となり、G8 CORE READY Closure
# （docs/audit/shrine-expansion-wave0-db03-core-ready-gate.md）で CORE_READY / FACT_READY へ遷移した。
# wave0-014 は G4〜G8 NOT EXECUTED で、HOLD / MODEL_CHANGE_REQUIRED / 未 hydrate のまま。
W0_DB03_G4_HYDRATED_IDS = frozenset({"wave0-012", "wave0-013", "wave0-015", "wave0-016"})
W0_DB03_MODEL_HOLD_ID = "wave0-014"

# W0-DB04 G4 re-entry。original membership 5社のうち G4 eligible subset の3社だけを
# hydrate する（凍結入力: docs/audit/shrine-expansion-wave0-db04-source-packet-freeze.md /
# docs/audit/shrine-expansion-wave0-db04-evidence-backfill-freeze.md）。
# wave0-020（G2 HOLD_POSITION_REVIEW）/ wave0-022（G3 MODEL_REVIEW_REMAINS）は未 hydrate。
#
# goriyaku / goriyaku_tags は凍結されていない（goriyaku typed evidence storage は別タスク）ため
# 持ち込まない。
#
# G7 Production Import 完了後（docs/audit/shrine-expansion-wave0-db04-production-import.md）、
# この3社は IMPORTED / FACT_READY。CORE_READY は G8 の別 Gate であり未判定。
# wave0-020 / wave0-022 は G7 NOT EXECUTED で、BUILD_READY / 未 hydrate のまま。
#
# wave0-021 の official_address は Source 表記「大阪市北区天神橋2丁目1番8号」に
# 「大阪府」を前置した Candidate Master canonical address。Base Seed の prefecture 導出が
# 都道府県始まりを要求するための W0-DB04 Mother Ship decision（wave0-021 限定）であり、
# global な正規化ルールではない。
W0_DB04_G4_HYDRATED_IDS = frozenset({"wave0-019", "wave0-021", "wave0-025"})
W0_DB04_EXCLUDED_IDS = frozenset({"wave0-020", "wave0-022"})

EXPECTED_W0_DB04_HYDRATION = {
    "wave0-019": {
        "official_name": "建勲神社",
        "official_address": "京都府京都市北区紫野北舟岡町49",
        "official_source_type": "shrine_official",
        "official_source_url": "https://kenkun-jinja.org/history/",
        "verified_at": "2026-10-03",
        "latitude": 35.0386537,
        "longitude": 135.7431512,
    },
    "wave0-021": {
        "official_name": "大阪天満宮",
        "official_address": "大阪府大阪市北区天神橋2丁目1番8号",
        "official_source_type": "shrine_official",
        "official_source_url": "https://osakatemmangu.or.jp/about",
        "verified_at": "2026-10-03",
        "latitude": 34.6958917,
        "longitude": 135.5126472,
    },
    "wave0-025": {
        "official_name": "大崎八幡宮",
        "official_address": "宮城県仙台市青葉区八幡4-6-1",
        "official_source_type": "government",
        "official_source_url": "https://miyagi-jinjacho.or.jp/jinja-search/detail.php?code=310010033",
        "verified_at": "2026-10-03",
        "latitude": 38.2725678,
        "longitude": 140.8449622,
    },
}

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


MODEL_RISK_RESOLUTION_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "audit" / "shrine-model-risk"
)

MODEL_RISK_OWNING_GATE = "G3"
MODEL_RISK_HOLD = "HOLD"
MODEL_RISK_RELEASE_STATUSES = frozenset({MODEL_RISK_HOLD, "RELEASED"})
# docs/audit/model-risk-release-contract.md §5 Release Classification Rules。
MODEL_RISK_CLASSIFICATIONS = frozenset(
    {
        "CURATION_RELEASE_CANDIDATE",
        "RESEARCH_REQUIRED_BEFORE_RELEASE",
        "MODEL_REVIEW_REMAINS",
        "MODEL_CHANGE_REQUIRED",
        "PRODUCT_DECISION_REQUIRED",
    }
)
MODEL_RISK_RECORD_FIELDS = (
    "candidate_id",
    "owning_gate",
    "model_risk_classification",
    "model_risk_release_status",
)
PROMOTED_STATUSES = frozenset({"BUILD_READY", "IMPORTED", "CORE_READY"})


class ModelRiskRecordError(ValueError):
    """Current Model Risk Resolution Record を解釈できない（fail closed）。"""


def _parse_model_risk_record(path: Path) -> dict:
    """1 file = 1 Candidate の record を parse する。

    各 field は行頭の `<field> = <value>` 1行だけを正とする。field 名で始まる
    行が形式違い（`=` 前後の空白違い・値の後の余分な語など）なら、その行を
    無視せず error にする。無視すると別の行だけが読まれ、record の意図と
    異なる状態が current として通過しうるため。
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ModelRiskRecordError(f"{path.name}: unreadable record: {exc}") from exc

    record: dict[str, str] = {}
    for field in MODEL_RISK_RECORD_FIELDS:
        loose = re.findall(rf"^[ \t]*{field}\b.*$", text, re.M)
        strict = re.findall(rf"^{field} = (\S+)$", text, re.M)
        if len(loose) != 1 or len(strict) != 1:
            raise ModelRiskRecordError(
                f"{path.name}: `{field}` must appear exactly once as `{field} = <value>` "
                f"(found {len(loose)} line(s), {len(strict)} well-formed)"
            )
        record[field] = strict[0]

    if record["owning_gate"] != MODEL_RISK_OWNING_GATE:
        raise ModelRiskRecordError(
            f"{path.name}: owning_gate must be G3, got {record['owning_gate']}"
        )
    if record["model_risk_classification"] not in MODEL_RISK_CLASSIFICATIONS:
        raise ModelRiskRecordError(
            f"{path.name}: unknown model_risk_classification {record['model_risk_classification']}"
        )
    if record["model_risk_release_status"] not in MODEL_RISK_RELEASE_STATUSES:
        raise ModelRiskRecordError(
            f"{path.name}: unknown model_risk_release_status {record['model_risk_release_status']}"
        )
    return record


def _load_model_risk_records(directory: Path) -> dict[str, dict]:
    """directory 内の全 record を candidate_id -> record で返す。

    Candidate を特定の id で絞らない（parser は wave0-014 を知らない）。
    directory が無い / 読めない / record が0件のとき、guard が無言で通過
    しないよう error にする。
    """
    if not directory.is_dir():
        raise ModelRiskRecordError(f"Model Risk record directory not found: {directory}")
    try:
        paths = sorted(directory.glob("*.md"))
    except OSError as exc:
        raise ModelRiskRecordError(
            f"Model Risk record directory unreadable: {directory}: {exc}"
        ) from exc
    if not paths:
        raise ModelRiskRecordError(f"no Model Risk Resolution Record found in {directory}")

    records: dict[str, dict] = {}
    for path in paths:
        record = _parse_model_risk_record(path)
        candidate_id = record["candidate_id"]
        if candidate_id in records:
            raise ModelRiskRecordError(
                f"duplicate Model Risk record for {candidate_id}: "
                f"{records[candidate_id]['_path']} and {path.name}"
            )
        records[candidate_id] = {**record, "_path": path.name}
    return records


def _model_risk_promotion_violations(records: dict[str, dict], rows: list[dict]) -> list[tuple]:
    """Model Risk HOLD の Candidate が lifecycle 上で昇格していないかを判定する。

    読むのは record の release status と Candidate Master 行だけである。
    model code / migration / usable History / eligibility / Production 上の存在
    からは release を推論しない。HOLD の解除は record を RELEASED へ更新する
    別タスク（G3 再判定）でだけ起きる。
    """
    rows_by_id: dict[str, dict] = {}
    for row in rows:
        if row["candidate_id"] in rows_by_id:
            raise ModelRiskRecordError(f"duplicate Candidate Master row: {row['candidate_id']}")
        rows_by_id[row["candidate_id"]] = row

    violations = []
    for candidate_id, record in sorted(records.items()):
        if record["model_risk_release_status"] != MODEL_RISK_HOLD:
            continue
        row = rows_by_id.get(candidate_id)
        # record はあるが Candidate Master に居ない、は昇格の危険が無いので許す。
        if row is None:
            continue
        if row["candidate_status"] != "HOLD":
            violations.append((candidate_id, "candidate_status", row["candidate_status"]))
        if (
            record["model_risk_classification"] == "MODEL_CHANGE_REQUIRED"
            and row["status_reason_code"] != "MODEL_CHANGE_REQUIRED"
        ):
            violations.append((candidate_id, "status_reason_code", row["status_reason_code"]))
    return violations


def test_model_risk_hold_candidates_are_never_promoted():
    """Model Risk HOLD の Candidate を BUILD_READY / IMPORTED / CORE_READY へ昇格させない。

    Candidate Master の `candidate_status` / `status_reason_code` だけを書き換えても
    Model Risk は解除されない。現在の release state は
    `docs/audit/shrine-model-risk/` の Current Model Risk Resolution Record が持つ。
    """
    records = _load_model_risk_records(MODEL_RISK_RESOLUTION_DIR)
    rows = _load_master()["candidates"]

    assert _model_risk_promotion_violations(records, rows) == []


def test_w0_db03_model_hold_has_a_current_model_risk_record():
    """wave0-014 の record を消すと guard の対象から外れるため、record の存在を固定する。

    parser / guard は特定 Candidate を知らない。ここは current state の pin である。
    RELEASED への更新は G3 の明示的な再判定を伴う別タスクで、この pin も同時に更新する。
    """
    records = _load_model_risk_records(MODEL_RISK_RESOLUTION_DIR)
    record = records[W0_DB03_MODEL_HOLD_ID]

    assert record["owning_gate"] == "G3"
    assert record["model_risk_classification"] == "MODEL_CHANGE_REQUIRED"
    assert record["model_risk_release_status"] == "HOLD"


def _write_model_risk_record(directory: Path, name: str, **overrides: str) -> Path:
    fields = {
        "candidate_id": "cand-001",
        "owning_gate": "G3",
        "model_risk_classification": "MODEL_CHANGE_REQUIRED",
        "model_risk_release_status": "HOLD",
        **overrides,
    }
    body = "\n".join(f"{key} = {value}" for key, value in fields.items())
    path = directory / name
    path.write_text(f"# record\n\n```text\n{body}\n```\n", encoding="utf-8")
    return path


def _held_row(candidate_status: str, status_reason_code: str = "MODEL_CHANGE_REQUIRED") -> dict:
    return {
        "candidate_id": "cand-001",
        "candidate_status": candidate_status,
        "status_reason_code": status_reason_code,
    }


@pytest.mark.parametrize("promoted_status", sorted(PROMOTED_STATUSES))
def test_model_risk_hold_blocks_promotion(tmp_path, promoted_status):
    _write_model_risk_record(tmp_path, "cand-001.md")
    records = _load_model_risk_records(tmp_path)

    # status_reason_code を HOLD 理由のまま残しても、昇格は拒否される。
    violations = _model_risk_promotion_violations(records, [_held_row(promoted_status)])
    assert violations == [("cand-001", "candidate_status", promoted_status)]

    # status_reason_code まで書き換えても、record が HOLD の間は拒否される。
    violations = _model_risk_promotion_violations(
        records, [_held_row(promoted_status, "WAVE0_CORE_READY_CANDIDATE")]
    )
    assert violations == [
        ("cand-001", "candidate_status", promoted_status),
        ("cand-001", "status_reason_code", "WAVE0_CORE_READY_CANDIDATE"),
    ]


def test_model_risk_hold_rejects_review_and_wrong_reason(tmp_path):
    _write_model_risk_record(tmp_path, "cand-001.md")
    records = _load_model_risk_records(tmp_path)

    assert _model_risk_promotion_violations(records, [_held_row("REVIEW")]) == [
        ("cand-001", "candidate_status", "REVIEW")
    ]
    assert _model_risk_promotion_violations(records, [_held_row("HOLD", "SOURCE_HOLD")]) == [
        ("cand-001", "status_reason_code", "SOURCE_HOLD")
    ]
    assert _model_risk_promotion_violations(records, [_held_row("HOLD")]) == []


def test_model_risk_hold_other_classification_still_requires_hold(tmp_path):
    _write_model_risk_record(
        tmp_path, "cand-001.md", model_risk_classification="MODEL_REVIEW_REMAINS"
    )
    records = _load_model_risk_records(tmp_path)

    assert _model_risk_promotion_violations(records, [_held_row("HOLD", "UNKNOWN_EVIDENCE")]) == []
    assert _model_risk_promotion_violations(
        records, [_held_row("CORE_READY", "UNKNOWN_EVIDENCE")]
    ) == [("cand-001", "candidate_status", "CORE_READY")]


def test_model_risk_released_record_does_not_constrain_lifecycle(tmp_path):
    _write_model_risk_record(tmp_path, "cand-001.md", model_risk_release_status="RELEASED")
    records = _load_model_risk_records(tmp_path)

    assert (
        _model_risk_promotion_violations(
            records, [_held_row("BUILD_READY", "WAVE0_CORE_READY_CANDIDATE")]
        )
        == []
    )


def test_model_risk_record_without_master_row_is_ignored(tmp_path):
    _write_model_risk_record(tmp_path, "cand-001.md")
    records = _load_model_risk_records(tmp_path)

    assert _model_risk_promotion_violations(records, []) == []


def test_model_risk_guard_rejects_duplicate_master_rows(tmp_path):
    _write_model_risk_record(tmp_path, "cand-001.md")
    records = _load_model_risk_records(tmp_path)

    with pytest.raises(ModelRiskRecordError, match="duplicate Candidate Master row"):
        _model_risk_promotion_violations(records, [_held_row("HOLD"), _held_row("CORE_READY")])


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"owning_gate": "G4"}, "owning_gate must be G3"),
        ({"model_risk_release_status": "PARTIALLY_RELEASED"}, "unknown model_risk_release_status"),
        ({"model_risk_release_status": "released"}, "unknown model_risk_release_status"),
        ({"model_risk_classification": "MODEL_FIXED"}, "unknown model_risk_classification"),
    ],
)
def test_model_risk_parser_rejects_unknown_values(tmp_path, overrides, message):
    _write_model_risk_record(tmp_path, "cand-001.md", **overrides)

    with pytest.raises(ModelRiskRecordError, match=message):
        _load_model_risk_records(tmp_path)


@pytest.mark.parametrize(
    "text",
    [
        # field 欠落
        "candidate_id = cand-001\nowning_gate = G3\nmodel_risk_classification = MODEL_CHANGE_REQUIRED\n",
        # 1 file に2 candidate
        "candidate_id = cand-001\ncandidate_id = cand-002\nowning_gate = G3\n"
        "model_risk_classification = MODEL_CHANGE_REQUIRED\nmodel_risk_release_status = HOLD\n",
        # release status が2行（順序依存で読まない）
        "candidate_id = cand-001\nowning_gate = G3\nmodel_risk_classification = MODEL_CHANGE_REQUIRED\n"
        "model_risk_release_status = HOLD\nmodel_risk_release_status = RELEASED\n",
        # 形式違いの行を無視して別の行を読まない
        "candidate_id = cand-001\nowning_gate = G3\nmodel_risk_classification = MODEL_CHANGE_REQUIRED\n"
        "model_risk_release_status = HOLD\nmodel_risk_release_status=RELEASED\n",
        "candidate_id = cand-001\nowning_gate = G3\nmodel_risk_classification = MODEL_CHANGE_REQUIRED\n"
        "model_risk_release_status = HOLD pending\n",
        # 空 file
        "",
    ],
)
def test_model_risk_parser_rejects_malformed_records(tmp_path, text):
    (tmp_path / "cand-001.md").write_text(text, encoding="utf-8")

    with pytest.raises(ModelRiskRecordError, match="must appear exactly once"):
        _load_model_risk_records(tmp_path)


def test_model_risk_parser_rejects_duplicate_candidate_records(tmp_path):
    _write_model_risk_record(tmp_path, "a.md")
    _write_model_risk_record(tmp_path, "b.md", model_risk_release_status="RELEASED")

    with pytest.raises(ModelRiskRecordError, match="duplicate Model Risk record for cand-001"):
        _load_model_risk_records(tmp_path)


def test_model_risk_parser_rejects_empty_or_missing_directory(tmp_path):
    with pytest.raises(ModelRiskRecordError, match="no Model Risk Resolution Record"):
        _load_model_risk_records(tmp_path)

    (tmp_path / "notes.txt").write_text("candidate_id = cand-001\n", encoding="utf-8")
    with pytest.raises(ModelRiskRecordError, match="no Model Risk Resolution Record"):
        _load_model_risk_records(tmp_path)

    with pytest.raises(ModelRiskRecordError, match="directory not found"):
        _load_model_risk_records(tmp_path / "missing")


def test_model_risk_parser_rejects_unreadable_record(tmp_path):
    (tmp_path / "cand-001.md").write_bytes(b"candidate_id = \xff\xfe\n")

    with pytest.raises(ModelRiskRecordError, match="unreadable record"):
        _load_model_risk_records(tmp_path)


def test_model_risk_parser_is_not_bound_to_a_specific_candidate(tmp_path):
    _write_model_risk_record(tmp_path, "x.md", candidate_id="wave9-999")
    _write_model_risk_record(
        tmp_path, "y.md", candidate_id="wave9-998", model_risk_release_status="RELEASED"
    )

    records = _load_model_risk_records(tmp_path)

    assert set(records) == {"wave9-999", "wave9-998"}
    assert records["wave9-999"]["model_risk_release_status"] == "HOLD"
    assert records["wave9-998"]["model_risk_release_status"] == "RELEASED"


def _load_master() -> dict:
    return json.loads(MASTER_PATH.read_text(encoding="utf-8"))


def _effective(master: dict, row: dict) -> dict:
    return {**master.get("candidate_defaults", {}), **row}


def _wave0_candidates(master: dict) -> list[dict]:
    return [
        row
        for row in master["candidates"]
        if WAVE0_ID_RE.fullmatch(str(row.get("candidate_id", "")))
    ]


def _nationwide_candidates(master: dict) -> list[dict]:
    return [
        row
        for row in master["candidates"]
        if NATIONWIDE_ID_RE.fullmatch(str(row.get("candidate_id", "")))
    ]


def test_candidate_master_global_registry_namespaces_are_partitioned():
    master = _load_master()
    candidates = master["candidates"]
    candidate_ids = [str(row.get("candidate_id", "")) for row in candidates]

    assert len(candidate_ids) == len(set(candidate_ids))

    unknown = [
        candidate_id
        for candidate_id in candidate_ids
        if not (
            WAVE0_ID_RE.fullmatch(candidate_id)
            or NATIONWIDE_ID_RE.fullmatch(candidate_id)
        )
    ]
    assert unknown == []

    wave0 = _wave0_candidates(master)
    nationwide = _nationwide_candidates(master)

    assert len(candidates) == len(wave0) + len(nationwide)
    assert {row["candidate_id"] for row in wave0}.isdisjoint(
        {row["candidate_id"] for row in nationwide}
    )
    assert all(row["candidate_status"] in CANONICAL_CANDIDATE_STATUSES for row in candidates)


def test_nationwide_candidate_contract_is_additive_and_fail_closed():
    """nsrc-* はWave0 defaultを暗黙継承せず、Nationwide contractをrow-levelで持つ。"""
    master = _load_master()

    for row in _nationwide_candidates(master):
        assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
        assert "admission_provenance" in row
        provenance = row["admission_provenance"]
        assert set(provenance) == NATIONWIDE_PROVENANCE_FIELDS
        assert provenance["track"] == NATIONWIDE_TRACK
        assert provenance["prefecture"] == row["prefecture"]
        assert provenance["source_batch_id"]
        assert provenance["handoff_id"]
        assert provenance["source_position"]
        assert re.fullmatch(r"[0-9a-f]{64}", provenance["source_snapshot_sha256"])
        assert provenance["source_url"]
        assert provenance["source_verified_at"]
        assert provenance["captured_at"]

        # Historical Wave0 defaultsをNationwide rowへ暗黙適用しない。
        assert "wave_id" in row and row["wave_id"] is None
        assert "identity_status" in row
        assert "duplicate_status" in row
        assert "official_source_status" in row
        assert "knowledge_status" in row
        assert "build_batch" in row

        if row["candidate_status"] in NATIONWIDE_POSITIVE_STATUS_REASONS:
            assert row["status_reason_code"] == NATIONWIDE_POSITIVE_STATUS_REASONS[
                row["candidate_status"]
            ]

        # candidate_status はData Build lifecycleのみを表す。
        # G1 Identity / DuplicateはDISCOVEREDのままsub-statusだけ進められるため、
        # G0初期値のUNREVIEWEDを永続条件として固定しない。
        assert row["identity_status"] in NATIONWIDE_IDENTITY_STATUSES
        assert row["duplicate_status"] in NATIONWIDE_DUPLICATE_STATUSES
        assert row["official_source_status"] in NATIONWIDE_OFFICIAL_SOURCE_STATUSES
        assert row["knowledge_status"] in NATIONWIDE_KNOWLEDGE_STATUSES

        if row["candidate_status"] == "DISCOVERED":
            assert row["build_batch"] is None

        assert row.get("build_batch") not in {
            provenance["source_batch_id"],
            provenance["handoff_id"],
        }


def test_wave0_candidate_master_registry_accounting():
    master = _load_master()
    candidates = _wave0_candidates(master)

    assert master["schema_version"] == "1.4"
    assert len(candidates) == EXPECTED_WAVE0_TOTAL
    assert len({row["candidate_id"] for row in candidates}) == EXPECTED_WAVE0_TOTAL
    assert Counter(row["candidate_status"] for row in candidates) == EXPECTED_STATUS_COUNTS
    assert Counter(row["status_reason_code"] for row in candidates) == EXPECTED_REASON_COUNTS


def test_wave0_batch_membership_is_deterministic():
    """Batch 割り当ては 7 batch x 5 社で固定（original membership）。

    初期 Registry 時点では 35 社すべてが `BUILD_READY` だったが、これは
    その時点のスナップショットであって恒久ルールではない。Batch 割り当ての
    不変条件は status ではなく「`build_batch` が付いた行の分布」である。
    Batch 割り当て後の HOLD / REVIEW も member として数える（schema 1.3）。
    """
    candidates = _wave0_candidates(_load_master())
    assigned = [row for row in candidates if row["build_batch"] is not None]

    assert len(assigned) == 35
    assert Counter(row["build_batch"] for row in assigned) == EXPECTED_BUILD_BATCH_COUNTS

    # 割り当て済みの行で BATCH_ASSIGNED_STATUSES 以外なのは、固定した post-batch HOLD だけ。
    post_batch_holds = {
        row["candidate_id"]: row["build_batch"]
        for row in assigned
        if row["candidate_status"] not in BATCH_ASSIGNED_STATUSES
    }
    assert post_batch_holds == EXPECTED_POST_BATCH_HOLDS
    assert all(
        row["candidate_status"] in UNASSIGNED_STATUSES
        for row in assigned
        if row["candidate_id"] in EXPECTED_POST_BATCH_HOLDS
    )

    # BUILD_READY / IMPORTED / CORE_READY は必ず Batch 割り当て済み。
    assert all(
        row["build_batch"] is not None
        for row in candidates
        if row["candidate_status"] in BATCH_ASSIGNED_STATUSES
    )


def test_build_batch_survives_the_import_lifecycle_transition():
    """`build_batch` は Data Build provenance であり lifecycle state ではない。

    BUILD_READY -> IMPORTED -> CORE_READY で消してはならない。消すと
    「どの Batch で Production へ入ったのか」が追跡不能になる。
    """
    candidates = _wave0_candidates(_load_master())

    imported_or_core_ready = [row for row in candidates if row["candidate_status"] in {"IMPORTED", "CORE_READY"}]
    assert len(imported_or_core_ready) == 17
    assert Counter(row["build_batch"] for row in imported_or_core_ready) == {
        "W0-DB01": 5,
        "W0-DB02": 5,
        "W0-DB03": 4,
        "W0-DB04": 3,
    }
    assert all(_effective(_load_master(), row)["knowledge_status"] == "FACT_READY" for row in imported_or_core_ready)

    # HOLD / REVIEW のうち Batch 割り当て前に停止したものは null のまま。
    # Batch 割り当て後に停止したもの（post-batch HOLD）は build_batch を保持する。
    held = [row for row in candidates if row["candidate_status"] in UNASSIGNED_STATUSES]
    assert {
        row["candidate_id"]: row["build_batch"] for row in held if row["build_batch"] is not None
    } == EXPECTED_POST_BATCH_HOLDS
    assert sum(1 for row in held if row["build_batch"] is None) == 9


def test_w0_db03_to_db07_stay_build_ready():
    """Production Import 済みは W0-DB01 / W0-DB02、W0-DB03 の G8 execution subset 4社、
    W0-DB04 の G7 execution subset 3社。

    W0-DB03 は original membership 5社のまま、4社 CORE_READY / wave0-014 post-batch HOLD
    （MODEL_CHANGE_REQUIRED）の混在状態である。W0-DB04 は original membership 5社のまま、
    3社 CORE_READY / wave0-020・wave0-022 BUILD_READY の混在状態である。
    W0-DB05〜W0-DB07 の 15 社は BUILD_READY のまま。
    """
    candidates = _wave0_candidates(_load_master())

    db03 = {row["candidate_id"]: row for row in candidates if row["build_batch"] == "W0-DB03"}
    assert len(db03) == 5
    assert set(db03) == W0_DB03_G4_HYDRATED_IDS | {W0_DB03_MODEL_HOLD_ID}
    for candidate_id in W0_DB03_G4_HYDRATED_IDS:
        assert db03[candidate_id]["candidate_status"] == "CORE_READY", candidate_id
        assert db03[candidate_id]["knowledge_status"] == "FACT_READY", candidate_id
    assert db03[W0_DB03_MODEL_HOLD_ID]["candidate_status"] == "HOLD"
    assert db03[W0_DB03_MODEL_HOLD_ID]["status_reason_code"] == "MODEL_CHANGE_REQUIRED"
    assert db03[W0_DB03_MODEL_HOLD_ID]["build_batch"] == "W0-DB03"

    db04 = {row["candidate_id"]: row for row in candidates if row["build_batch"] == "W0-DB04"}
    assert len(db04) == 5
    assert set(db04) == W0_DB04_G4_HYDRATED_IDS | W0_DB04_EXCLUDED_IDS
    for candidate_id in W0_DB04_G4_HYDRATED_IDS:
        assert db04[candidate_id]["candidate_status"] == "CORE_READY", candidate_id
        assert db04[candidate_id]["knowledge_status"] == "FACT_READY", candidate_id
    for candidate_id in W0_DB04_EXCLUDED_IDS:
        assert db04[candidate_id]["candidate_status"] == "BUILD_READY", candidate_id

    for batch in CANONICAL_BUILD_BATCHES[4:]:
        members = [row for row in candidates if row["build_batch"] == batch]
        assert len(members) == 5, batch
        assert all(row["candidate_status"] == "BUILD_READY" for row in members), batch


def test_wave0_build_batch_uses_the_canonical_db_namespace_only():
    """legacy `W0-B01`〜`W0-B07` が build_batch として残っていないこと。

    これらは Wave0 の工程ID と同じ文字列であり、Candidate Master 内に
    残っていると工程とデータバッチが区別できなくなる。
    """
    candidates = _wave0_candidates(_load_master())

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
    candidates = _wave0_candidates(_load_master())

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
            if row["candidate_id"] in W0_DB04_G4_HYDRATED_IDS:
                continue
            leaked = REQUIRED_W0_DB01_HYDRATION_FIELDS & row.keys()
            assert not leaked, (batch, row["candidate_id"], sorted(leaked))


def test_wave0_db04_g4_subset_is_hydrated_from_frozen_inputs_only():
    """W0-DB04 G4 re-entry: eligible subset 3社だけが凍結値で hydrate 済み。

    build_batch / duplicate_status は不変で、goriyaku は持ち込まない。G7 Production Import 後、
    3社は G8 遷移後 CORE_READY / FACT_READY。
    wave0-020 / wave0-022 は未 hydrate のまま BUILD_READY を保持する。
    """
    master = _load_master()
    db04 = {row["candidate_id"]: row for row in master["candidates"] if row["build_batch"] == "W0-DB04"}

    assert set(db04) == W0_DB04_G4_HYDRATED_IDS | W0_DB04_EXCLUDED_IDS
    assert set(EXPECTED_W0_DB04_HYDRATION) == W0_DB04_G4_HYDRATED_IDS

    for candidate_id, expected in EXPECTED_W0_DB04_HYDRATION.items():
        row = db04[candidate_id]
        assert {key: row.get(key) for key in expected} == expected, candidate_id
        assert row["official_name"] == row["candidate_name"], candidate_id
        assert row["official_address"].startswith(row["prefecture"]), candidate_id
        assert "goriyaku" not in row, candidate_id
        assert "goriyaku_tags" not in row, candidate_id
        assert row["knowledge_status"] == "FACT_READY", candidate_id
        assert row["candidate_status"] == "CORE_READY", candidate_id
        assert row["build_batch"] == "W0-DB04", candidate_id
        assert row["status_reason_code"] == "WAVE0_CORE_READY_CANDIDATE", candidate_id
        assert row["duplicate_status"] == "NEW", candidate_id

    for candidate_id in W0_DB04_EXCLUDED_IDS:
        row = db04[candidate_id]
        leaked = (REQUIRED_W0_DB01_HYDRATION_FIELDS | {"identity_status", "official_source_status"}) & row.keys()
        assert not leaked, (candidate_id, sorted(leaked))
        assert row["candidate_status"] == "BUILD_READY", candidate_id
        assert row["duplicate_status"] == "NEW", candidate_id


def test_wave0_hold_and_review_candidates_stay_separated():
    candidates = _wave0_candidates(_load_master())

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
    candidates = _wave0_candidates(master)

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
        elif row["candidate_id"] in W0_DB04_G4_HYDRATED_IDS:
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


def test_wave0_candidate_defaults_are_not_promoted_by_a_single_batch_import():
    """Wave0 legacy defaultsを単一Batch importで昇格させない。

    schema 1.4以降もtop-level candidate_defaultsはHistorical Wave0専用。
    Nationwide nsrc-* はrow-level explicit valuesを持ち、このdefaultを暗黙継承しない。
    """
    defaults = _load_master()["candidate_defaults"]

    assert defaults["knowledge_status"] == "ACQUISITION_PATH_CONFIRMED"
    assert defaults["identity_status"] == "UNREVIEWED"
    assert defaults["official_source_status"] == "AVAILABLE"


def test_wave0_candidate_reason_is_historical_admission_reason_and_not_overridden():
    """Wave0 candidate_reasonはhistorical Registry admission reasonとして固定する。

    Nationwide nsrc-* のcandidate_reasonは別Contractでrow-level overrideする。
    現在の candidate_status の理由はstatus_reason_codeが表す。
    """
    master = _load_master()

    assert master["candidate_defaults"]["candidate_reason"] == "historical_recovered_popularity_candidate"
    assert all("candidate_reason" not in row for row in _wave0_candidates(master))


def test_wave0_discovery_provenance_has_required_fields():
    master = _load_master()
    required = set(master["required_discovery_fields"])

    for row in _wave0_candidates(master):
        assert row["discovery_sources"]
        for source in row["discovery_sources"]:
            assert required <= source.keys()
            assert source["discovery_source"] == "Omairi 全国神社人気ランキング2026"
            assert source["discovery_source_url"].startswith(
                "https://omairi.club/spots/ranking/shrine"
            )
            assert isinstance(source["discovery_rank"], int)
            assert source["captured_at"]


# --- Nationwide Source Track: handoff regression（data-driven） ------------------------------
#
# docs/audit/niigata-batch001-ready-set-freeze.md の frozen handoff ごとの exact regression。
# Handoff ごとの regression であり、Global total の magic number ではない。
#
# 期待値は test 専用 manifest（tests/fixtures/shrine_expansion_handoffs.json）が持つ。
# 全 handoff は同じ generic validator（_handoff_violations）と同じ parametrized contract を通る。
# H003 以降は manifest に handoff を追加するだけで、専用の validator / block を足さない。
#
# 2つの層に分けて固定する:
#   immutable : membership / 名称 / prefecture / wave_id / candidate_reason /
#               admission_provenance（G0 登録後 immutable）/ G1 identity・duplicate
#   lifecycle : candidate_status / status_reason_code / official_source_status /
#               knowledge_status / build_batch（Candidate ごとに独立して進む）
# Candidate を次の state へ進めるときは manifest の該当 member だけを変える。
# 行全体は exact に比較するので、official_* / 座標 / goriyaku 等の premature な field も検出する。
#
# manifest 自体の誤りは frozen Ready Set（Markdown の H00x table）との cross-check で検出する
# （test_handoff_manifest_matches_frozen_ready_set）。
#
# 同名 Candidate（例: H002 の赤城社4件）は別々の Registry Candidate である。名前の一致から
# identity / duplicate を推論せず、統合・重複排除・alias をしない。candidate_name の一意性は要求しない。
# Source 上の住所は frozen handoff の evidence であり、Candidate Master には official_address 等として持たせない。

HANDOFF_MANIFEST_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "shrine_expansion_handoffs.json"
)
FROZEN_READY_SET_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "audit" / "niigata-batch001-ready-set-freeze.md"
)

H001_HANDOFF_ID = "NIIGATA-001-H001"
H002_HANDOFF_ID = "NIIGATA-001-H002"
H003_HANDOFF_ID = "NIIGATA-001-H003"
H004_HANDOFF_ID = "NIIGATA-001-H004"

HANDOFF_LIFECYCLE_FIELDS = (
    "candidate_status",
    "status_reason_code",
    "official_source_status",
    "knowledge_status",
    "build_batch",
)
HANDOFF_SPEC_FIELDS = frozenset(
    {
        "handoff_id",
        "source_batch_id",
        "prefecture",
        "source_snapshot_sha256",
        "source_url",
        "source_verified_at",
        "captured_at",
        "members",
    }
)
HANDOFF_MEMBER_FIELDS = frozenset(
    {
        "candidate_id",
        "candidate_name",
        "source_position",
        "identity_status",
        "duplicate_status",
        "lifecycle",
    }
)
WAVE0_RANKING_PROVENANCE_KEYS = frozenset({"discovery_sources", "discovery_rank"})
# Candidate Master に持たせてはいけない field（G1 以降の hydrate / Wave0 provenance）。
# G1 PASS 後も official_name / official_address 等は Candidate Master に持たせない。
HANDOFF_FORBIDDEN_HYDRATION_FIELDS = frozenset(
    {
        "official_name",
        "official_address",
        "address",
        "latitude",
        "longitude",
        "lat",
        "lng",
        "location",
        "shrine_id",
        "goriyaku",
        "goriyaku_tags",
        "knowledge",
        "deities",
        "histories",
    }
    | WAVE0_RANKING_PROVENANCE_KEYS
)

# Nationwide の lifecycle preset。Candidate 固有の test が manifest から独立した期待値として使う。
# build_batch は null のまま（Source batch / handoff / Wave0 の W0-DBxx を入れない）。
NATIONWIDE_DISCOVERED_LIFECYCLE = {
    "candidate_status": "DISCOVERED",
    "status_reason_code": "REGISTRY_ADMISSION_COMPLETE",
    "official_source_status": "AVAILABLE",
    "knowledge_status": "UNREVIEWED",
    "build_batch": None,
}
NATIONWIDE_IMPORTED_LIFECYCLE = {
    "candidate_status": "IMPORTED",
    "status_reason_code": "PRODUCTION_IMPORT_COMPLETE",
    "official_source_status": "CONFIRMED",
    "knowledge_status": "FACT_READY",
    "build_batch": None,
}
NATIONWIDE_CORE_READY_LIFECYCLE = {
    "candidate_status": "CORE_READY",
    "status_reason_code": "CORE_READY_CONTRACT_PASS",
    "official_source_status": "CONFIRMED",
    "knowledge_status": "FACT_READY",
    "build_batch": None,
}


def _load_handoff_manifest() -> dict:
    return json.loads(HANDOFF_MANIFEST_PATH.read_text(encoding="utf-8"))


HANDOFF_SPECS = tuple(_load_handoff_manifest()["handoffs"])


def _handoff_spec(handoff_id: str) -> dict:
    matches = [spec for spec in HANDOFF_SPECS if spec["handoff_id"] == handoff_id]
    assert len(matches) == 1, handoff_id
    return matches[0]


def _member_spec(candidate_id: str) -> dict:
    matches = [
        member
        for spec in HANDOFF_SPECS
        for member in spec["members"]
        if member["candidate_id"] == candidate_id
    ]
    assert len(matches) == 1, candidate_id
    return matches[0]


def _member_handoff(candidate_id: str) -> dict:
    matches = [
        spec
        for spec in HANDOFF_SPECS
        if any(member["candidate_id"] == candidate_id for member in spec["members"])
    ]
    assert len(matches) == 1, candidate_id
    return matches[0]


def _member_g1(candidate_id: str) -> dict:
    member = _member_spec(candidate_id)
    return {
        "identity_status": member["identity_status"],
        "duplicate_status": member["duplicate_status"],
    }


def _member_triples(handoff_id: str) -> list[tuple[str, str, str]]:
    return [
        (member["candidate_id"], member["candidate_name"], member["source_position"])
        for member in _handoff_spec(handoff_id)["members"]
    ]


def _expected_member_immutable(
    candidate_id: str, candidate_name: str, source_position: str
) -> dict:
    spec = _member_handoff(candidate_id)
    member = _member_spec(candidate_id)
    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "prefecture": spec["prefecture"],
        "duplicate_status": member["duplicate_status"],
        "wave_id": None,
        "identity_status": member["identity_status"],
        "candidate_reason": NATIONWIDE_CANDIDATE_REASON,
        "admission_provenance": {
            "track": NATIONWIDE_TRACK,
            "prefecture": spec["prefecture"],
            "source_batch_id": spec["source_batch_id"],
            "handoff_id": spec["handoff_id"],
            "source_position": source_position,
            "source_snapshot_sha256": spec["source_snapshot_sha256"],
            "source_url": spec["source_url"],
            "source_verified_at": spec["source_verified_at"],
            "captured_at": spec["captured_at"],
        },
    }


def _expected_member_row(candidate_id: str, candidate_name: str, source_position: str) -> dict:
    return {
        **_expected_member_immutable(candidate_id, candidate_name, source_position),
        **_member_spec(candidate_id)["lifecycle"],
    }


def _handoff_violations(master: dict, spec: dict) -> list[str]:
    """Handoff の exact contract からのずれを列挙する（空なら PASS）。全 handoff 共通。"""
    candidates = master["candidates"]
    handoff_id = spec["handoff_id"]
    violations: list[str] = []

    ids = [str(row.get("candidate_id", "")) for row in candidates]
    duplicated = sorted({cid for cid in ids if ids.count(cid) > 1})
    if duplicated:
        violations.append(f"reused candidate_id {duplicated}")
    unknown = [
        cid for cid in ids if not (WAVE0_ID_RE.fullmatch(cid) or NATIONWIDE_ID_RE.fullmatch(cid))
    ]
    if unknown:
        violations.append(f"unknown namespace {unknown}")

    members = spec["members"]
    in_handoff = [
        row
        for row in candidates
        if (row.get("admission_provenance") or {}).get("handoff_id") == handoff_id
    ]
    if [row.get("candidate_id") for row in in_handoff] != [m["candidate_id"] for m in members]:
        violations.append(f"{handoff_id} ids {[row.get('candidate_id') for row in in_handoff]}")

    by_id = {row.get("candidate_id"): row for row in candidates}
    for member in members:
        candidate_id = member["candidate_id"]
        if not NATIONWIDE_ID_RE.fullmatch(candidate_id):
            violations.append(f"{candidate_id} is not a nationwide candidate_id")
        want = _expected_member_row(
            candidate_id, member["candidate_name"], member["source_position"]
        )
        row = by_id.get(candidate_id)
        if row is None:
            violations.append(f"{candidate_id} missing")
            continue
        if row != want:
            diff = sorted(k for k in set(row) | set(want) if row.get(k) != want.get(k))
            violations.append(f"{candidate_id} differs: {diff}")
        effective = _effective(master, row)
        if effective.get("wave_id") is not None:
            violations.append(f"{candidate_id} wave_id={effective.get('wave_id')!r}")
        # Wave0 candidate_defaults を継承していないこと（key 欠落でも検出する）。
        for field in HANDOFF_LIFECYCLE_FIELDS:
            if effective.get(field) != want[field]:
                violations.append(f"{candidate_id} effective {field}={effective.get(field)!r}")
        if WAVE0_RANKING_PROVENANCE_KEYS & row.keys():
            violations.append(f"{candidate_id} has Wave0 ranking provenance")
        if HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys():
            violations.append(
                f"{candidate_id} premature fields {sorted(HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())}"
            )
        if row.get("build_batch") in {spec["source_batch_id"], handoff_id}:
            violations.append(f"{candidate_id} build_batch={row.get('build_batch')!r}")
    return violations


def test_handoff_manifest_is_well_formed():
    """Test 専用 manifest 自体の整合性。不正な manifest で contract を素通りさせない。"""
    manifest = _load_handoff_manifest()
    assert set(manifest) == {"schema_version", "purpose", "frozen_ready_set", "handoffs"}
    assert manifest["frozen_ready_set"] == "docs/audit/niigata-batch001-ready-set-freeze.md"

    handoff_ids = [spec["handoff_id"] for spec in HANDOFF_SPECS]
    assert len(handoff_ids) == len(set(handoff_ids))
    member_ids = [m["candidate_id"] for spec in HANDOFF_SPECS for m in spec["members"]]
    assert len(member_ids) == len(set(member_ids))
    positions = [m["source_position"] for spec in HANDOFF_SPECS for m in spec["members"]]
    assert len(positions) == len(set(positions))

    for spec in HANDOFF_SPECS:
        assert set(spec) == HANDOFF_SPEC_FIELDS, spec["handoff_id"]
        assert spec["handoff_id"].startswith(f"{spec['source_batch_id']}-H"), spec["handoff_id"]
        assert re.fullmatch(r"[0-9a-f]{64}", spec["source_snapshot_sha256"])
        assert spec["members"], spec["handoff_id"]
        for member in spec["members"]:
            assert set(member) == HANDOFF_MEMBER_FIELDS, member
            assert NATIONWIDE_ID_RE.fullmatch(member["candidate_id"]), member
            assert re.fullmatch(r"page[0-9]{3}-row[0-9]{3}", member["source_position"]), member
            assert member["identity_status"] in NATIONWIDE_IDENTITY_STATUSES, member
            assert member["duplicate_status"] in NATIONWIDE_DUPLICATE_STATUSES, member
            lifecycle = member["lifecycle"]
            assert tuple(lifecycle) == HANDOFF_LIFECYCLE_FIELDS, member
            assert lifecycle["candidate_status"] in CANONICAL_CANDIDATE_STATUSES, member
            assert lifecycle["status_reason_code"] == NATIONWIDE_POSITIVE_STATUS_REASONS.get(
                lifecycle["candidate_status"]
            ), member
            assert lifecycle["official_source_status"] in NATIONWIDE_OFFICIAL_SOURCE_STATUSES
            assert lifecycle["knowledge_status"] in NATIONWIDE_KNOWLEDGE_STATUSES
            assert lifecycle["build_batch"] is None, member


def test_every_registered_handoff_is_in_the_manifest():
    """Candidate Master に登録された handoff は全て manifest の contract を通る（未登録 handoff を見逃さない）。"""
    master = _load_master()
    registered = []
    for row in _nationwide_candidates(master):
        handoff_id = row["admission_provenance"]["handoff_id"]
        if handoff_id not in registered:
            registered.append(handoff_id)
    assert registered == [spec["handoff_id"] for spec in HANDOFF_SPECS]


@pytest.mark.parametrize("spec", HANDOFF_SPECS, ids=lambda spec: spec["handoff_id"])
def test_handoff_contract_is_exact(spec):
    master = _load_master()
    assert _handoff_violations(master, spec) == []

    members = spec["members"]
    rows = [
        row
        for row in _nationwide_candidates(master)
        if row["admission_provenance"]["handoff_id"] == spec["handoff_id"]
    ]
    assert len(rows) == len(members)
    assert [row["candidate_id"] for row in rows] == [m["candidate_id"] for m in members]
    assert [row["candidate_name"] for row in rows] == [m["candidate_name"] for m in members]
    assert [row["admission_provenance"]["source_position"] for row in rows] == [
        m["source_position"] for m in members
    ]
    assert len({row["candidate_id"] for row in rows}) == len(members)
    assert len({row["admission_provenance"]["source_position"] for row in rows}) == len(members)
    assert {row["admission_provenance"]["source_batch_id"] for row in rows} == {
        spec["source_batch_id"]
    }
    assert {row["admission_provenance"]["handoff_id"] for row in rows} == {spec["handoff_id"]}
    assert {row["admission_provenance"]["source_snapshot_sha256"] for row in rows} == {
        spec["source_snapshot_sha256"]
    }

    for row, member in zip(rows, members, strict=True):
        assert {field: row[field] for field in HANDOFF_LIFECYCLE_FIELDS} == member["lifecycle"]
        assert row["build_batch"] is None
        assert row["wave_id"] is None
        assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
        assert row["identity_status"] == member["identity_status"]
        assert row["duplicate_status"] == member["duplicate_status"]
        # Nationwide 行に Wave0 / Omairi の discovery_sources は要求しない（持たない）。
        assert "discovery_sources" not in row
        assert "discovery_rank" not in row
        assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())

    # Wave0 accounting は Nationwide handoff の登録・遷移で変わらない（global total は固定しない）。
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS
    assert Counter(r["status_reason_code"] for r in wave0) == EXPECTED_REASON_COUNTS


def test_handoffs_are_appended_after_wave0_in_manifest_order():
    """Historical Wave0 → H001 → H002 … の並び。handoff 同士は交差しない。"""
    master = _load_master()
    ids = [row["candidate_id"] for row in master["candidates"]]
    wave0_ids = [row["candidate_id"] for row in _wave0_candidates(master)]
    assert ids[: len(wave0_ids)] == wave0_ids

    expected = [m["candidate_id"] for spec in HANDOFF_SPECS for m in spec["members"]]
    assert ids[len(wave0_ids) : len(wave0_ids) + len(expected)] == expected


# --- Frozen Ready Set cross-check -------------------------------------------------------
#
# Data-driven test は manifest が誤っていれば誤った data を忠実に検証してしまう。
# frozen Ready Set（Markdown）の §3 input identity と §6 の `### <handoff_id>` table だけを
# 厳格に parse し、manifest と Candidate Master provenance の両方を照合する。
# 構造が想定と異なれば parse は ValueError で fail-closed する（推測で読まない）。

FROZEN_HANDOFF_HEADING_RE = re.compile(r"^### ([A-Z]+-[0-9]{3}-H[0-9]{3})$")
FROZEN_TABLE_HEADER = "| source_position | raw_name | raw_address | ready_basis |"
FROZEN_TABLE_SEPARATOR = "|---|---|---|---|"
FROZEN_READY_BASES = frozenset({"RUNNER_READY", "HUMAN_REVIEW_RELEASED"})
FROZEN_IDENTITY_KEYS = ("batch_id", "prefecture", "captured_at", "source_verified_at")


def _parse_frozen_handoffs(text: str) -> dict[str, list[dict]]:
    lines = text.splitlines()
    handoffs: dict[str, list[dict]] = {}
    index = 0
    while index < len(lines):
        match = FROZEN_HANDOFF_HEADING_RE.fullmatch(lines[index])
        index += 1
        if not match:
            continue
        handoff_id = match.group(1)
        if handoff_id in handoffs:
            raise ValueError(f"duplicate frozen handoff heading {handoff_id}")
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index + 1 >= len(lines):
            raise ValueError(f"{handoff_id}: table missing")
        if lines[index] != FROZEN_TABLE_HEADER or lines[index + 1] != FROZEN_TABLE_SEPARATOR:
            raise ValueError(f"{handoff_id}: unexpected table header")
        index += 2
        rows = []
        while index < len(lines) and lines[index].startswith("|"):
            line = lines[index]
            if not line.endswith("|"):
                raise ValueError(f"{handoff_id}: malformed row {line!r}")
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            if len(cells) != 4 or not all(cells):
                raise ValueError(f"{handoff_id}: malformed row {line!r}")
            source_position, raw_name, raw_address, ready_basis = cells
            if not re.fullmatch(r"page[0-9]{3}-row[0-9]{3}", source_position):
                raise ValueError(f"{handoff_id}: malformed source_position {source_position!r}")
            if ready_basis not in FROZEN_READY_BASES:
                raise ValueError(f"{handoff_id}: unknown ready_basis {ready_basis!r}")
            rows.append(
                {
                    "source_position": source_position,
                    "raw_name": raw_name,
                    "raw_address": raw_address,
                    "ready_basis": ready_basis,
                }
            )
            index += 1
        if not rows:
            raise ValueError(f"{handoff_id}: empty table")
        handoffs[handoff_id] = rows
    if not handoffs:
        raise ValueError("no frozen handoff tables")
    return handoffs


def _parse_frozen_identity(text: str) -> dict[str, str]:
    sections = re.findall(
        r"^## 3\. Frozen input identity\n(.*?)(?=^## )", text, flags=re.MULTILINE | re.DOTALL
    )
    if len(sections) != 1:
        raise ValueError("frozen input identity section not found exactly once")
    blocks = re.findall(r"^```text\n(.*?)^```$", sections[0], flags=re.MULTILINE | re.DOTALL)
    if len(blocks) != 1:
        raise ValueError("frozen input identity block not found exactly once")
    block = blocks[0]
    identity: dict[str, str] = {}
    for key in FROZEN_IDENTITY_KEYS:
        values = re.findall(rf"^{key}\s*=\s*(\S+)\s*$", block, flags=re.MULTILINE)
        if len(values) != 1:
            raise ValueError(f"frozen identity {key} not found exactly once")
        identity[key] = values[0]
    shas = re.findall(r"^snapshot_sha256\n=\s*([0-9a-f]{64})\s*$", block, flags=re.MULTILINE)
    if len(shas) != 1:
        raise ValueError("frozen identity snapshot_sha256 not found exactly once")
    identity["snapshot_sha256"] = shas[0]
    return identity


def _frozen_ready_set_violations(
    spec: dict, identity: dict[str, str], frozen: dict[str, list[dict]]
) -> list[str]:
    """manifest の handoff spec と frozen Ready Set のずれを列挙する（空なら PASS）。"""
    handoff_id = spec["handoff_id"]
    violations: list[str] = []
    for spec_key, frozen_key in (
        ("source_batch_id", "batch_id"),
        ("prefecture", "prefecture"),
        ("captured_at", "captured_at"),
        ("source_verified_at", "source_verified_at"),
        ("source_snapshot_sha256", "snapshot_sha256"),
    ):
        if spec[spec_key] != identity[frozen_key]:
            violations.append(
                f"{handoff_id} {spec_key}={spec[spec_key]!r} != frozen {identity[frozen_key]!r}"
            )
    rows = frozen.get(handoff_id)
    if rows is None:
        violations.append(f"{handoff_id} is not a frozen handoff")
        return violations
    want = [(row["source_position"], row["raw_name"]) for row in rows]
    have = [(m["source_position"], m["candidate_name"]) for m in spec["members"]]
    if have != want:
        violations.append(f"{handoff_id} members {have} != frozen {want}")
    return violations


def _frozen_ready_set_text() -> str:
    return FROZEN_READY_SET_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize("spec", HANDOFF_SPECS, ids=lambda spec: spec["handoff_id"])
def test_handoff_manifest_matches_frozen_ready_set(spec):
    text = _frozen_ready_set_text()
    assert (
        _frozen_ready_set_violations(
            spec, _parse_frozen_identity(text), _parse_frozen_handoffs(text)
        )
        == []
    )


@pytest.mark.parametrize("spec", HANDOFF_SPECS, ids=lambda spec: spec["handoff_id"])
def test_candidate_master_provenance_matches_frozen_ready_set(spec):
    """manifest を経由せず、Candidate Master の provenance 列を frozen table と直接照合する。"""
    master = _load_master()
    frozen = _parse_frozen_handoffs(_frozen_ready_set_text())[spec["handoff_id"]]
    rows = [
        row
        for row in _nationwide_candidates(master)
        if row["admission_provenance"]["handoff_id"] == spec["handoff_id"]
    ]
    assert [
        (row["admission_provenance"]["source_position"], row["candidate_name"]) for row in rows
    ] == [(row["source_position"], row["raw_name"]) for row in frozen]
    # manifest の id 列は、その frozen source_position 列へ同じ順序で対応する。
    assert [row["candidate_id"] for row in rows] == [m["candidate_id"] for m in spec["members"]]


def test_frozen_ready_set_parser_reads_the_frozen_handoff_boundaries():
    text = _frozen_ready_set_text()
    frozen = _parse_frozen_handoffs(text)
    assert len(frozen) == 20
    assert all(len(rows) == 5 for rows in frozen.values())
    positions = [row["source_position"] for rows in frozen.values() for row in rows]
    assert len(positions) == len(set(positions)) == 100
    assert positions[0] == "page001-row001"
    assert positions[-1] == "page010-row010"
    assert _parse_frozen_identity(text)["batch_id"] == "NIIGATA-001"


def _drift_spec(handoff_id: str, mutate) -> dict:
    spec = json.loads(json.dumps(_handoff_spec(handoff_id)))
    mutate(spec)
    return spec


def _swap_first_two_members(spec):
    spec["members"][0], spec["members"][1] = spec["members"][1], spec["members"][0]


@pytest.mark.parametrize("handoff_id", [spec["handoff_id"] for spec in HANDOFF_SPECS])
@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_swap_first_two_members, id="manifest-member-reordered"),
        pytest.param(lambda spec: spec["members"].pop(), id="manifest-member-removed"),
        pytest.param(
            lambda spec: spec["members"].append(
                dict(spec["members"][-1], source_position="page999-row999")
            ),
            id="manifest-member-added",
        ),
        pytest.param(
            lambda spec: spec["members"][0].update(source_position="page999-row999"),
            id="manifest-source-position-changed",
        ),
        pytest.param(
            lambda spec: spec["members"][0].update(candidate_name="架空神社"),
            id="manifest-candidate-name-changed",
        ),
        pytest.param(
            lambda spec: spec.update(handoff_id="NIIGATA-001-H999"), id="manifest-unknown-handoff"
        ),
        pytest.param(
            lambda spec: spec.update(source_batch_id="NIIGATA-999"), id="manifest-batch-changed"
        ),
        pytest.param(
            lambda spec: spec.update(source_snapshot_sha256="0" * 64),
            id="manifest-snapshot-sha-changed",
        ),
        pytest.param(
            lambda spec: spec.update(captured_at="2026-10-09T00:00:00+09:00"),
            id="manifest-captured-at-changed",
        ),
        pytest.param(
            lambda spec: spec.update(source_verified_at="2026-10-09"),
            id="manifest-verified-at-changed",
        ),
        pytest.param(
            lambda spec: spec.update(prefecture="長野県"), id="manifest-prefecture-changed"
        ),
    ],
)
def test_frozen_ready_set_cross_check_detects_manifest_drift(handoff_id, mutate):
    text = _frozen_ready_set_text()
    identity, frozen = _parse_frozen_identity(text), _parse_frozen_handoffs(text)
    assert _frozen_ready_set_violations(_handoff_spec(handoff_id), identity, frozen) == []
    assert _frozen_ready_set_violations(_drift_spec(handoff_id, mutate), identity, frozen) != []


@pytest.mark.parametrize(
    "transform",
    [
        pytest.param(
            lambda text: text.replace(
                "| page001-row006 | 赤井神社 |", "| page001-row006 | 架空神社 |"
            ),
            id="frozen-name-changed",
        ),
        pytest.param(
            lambda text: text.replace("| page001-row002 |", "| page001-row092 |"),
            id="frozen-position-changed",
        ),
    ],
)
def test_frozen_ready_set_cross_check_detects_frozen_drift(transform):
    text = transform(_frozen_ready_set_text())
    identity, frozen = _parse_frozen_identity(text), _parse_frozen_handoffs(text)
    assert any(_frozen_ready_set_violations(spec, identity, frozen) for spec in HANDOFF_SPECS)


@pytest.mark.parametrize(
    "transform",
    [
        pytest.param(
            lambda text: text.replace(
                FROZEN_TABLE_HEADER, "| position | name | address | basis |", 1
            ),
            id="table-header-changed",
        ),
        pytest.param(
            lambda text: text.replace(
                "| page001-row001 | 相吉神社 |", "| page001-row001 | 相吉神社 | extra |"
            ),
            id="extra-cell",
        ),
        pytest.param(
            lambda text: text.replace("| page001-row003 |", "| p1-r3 |"), id="malformed-position"
        ),
        pytest.param(
            lambda text: text.replace("RUNNER_READY |", "MAYBE |", 1), id="unknown-ready-basis"
        ),
        pytest.param(
            lambda text: text.replace("### NIIGATA-001-H002", "### NIIGATA-001-H001"),
            id="duplicate-heading",
        ),
        pytest.param(
            lambda text: re.sub(r"^### NIIGATA-001-H\d{3}$", "### moved", text, flags=re.MULTILINE),
            id="no-handoff-headings",
        ),
        pytest.param(
            lambda text: text.replace("snapshot_sha256\n=", "snapshot_sha256 :=", 1),
            id="identity-sha-unreadable",
        ),
        pytest.param(
            lambda text: text.replace("captured_at        =", "captured_on        =", 1),
            id="identity-key-missing",
        ),
    ],
)
def test_frozen_ready_set_parser_fails_closed_on_structure_drift(transform):
    text = transform(_frozen_ready_set_text())
    with pytest.raises(ValueError):
        _parse_frozen_identity(text)
        _parse_frozen_handoffs(text)


# --- Generic handoff mutation matrix ------------------------------------------------------
#
# 全 handoff に同じ protection category を適用する。H003 以降も manifest に追加するだけで
# 同じ fail-closed coverage を得る。各 mutation は manifest の現在値から「異なる値」を作る。


def _mutated(master: dict, mutate) -> dict:
    master = json.loads(json.dumps(master))
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    mutate(master, rows)
    return master


def _other(values, current):
    return next(value for value in sorted(values) if value != current)


def _generic_handoff_mutations(spec: dict) -> list:
    members = spec["members"]
    first, last = members[0]["candidate_id"], members[-1]["candidate_id"]
    second = members[1]["candidate_id"] if len(members) > 1 else first
    hid = spec["handoff_id"]

    def set_field(candidate_id, key, value):
        def mutate(master, rows):
            rows[candidate_id][key] = value

        return mutate

    def drop_field(candidate_id, key):
        def mutate(master, rows):
            del rows[candidate_id][key]

        return mutate

    def set_prov(candidate_id, key, value):
        def mutate(master, rows):
            rows[candidate_id]["admission_provenance"][key] = value

        return mutate

    def remove_member(master, rows):
        master["candidates"].remove(rows[last])

    def add_member(master, rows):
        extra = json.loads(json.dumps(rows[last]))
        extra["candidate_id"] = "nsrc-999999"
        extra["admission_provenance"]["source_position"] = "page999-row999"
        master["candidates"].append(extra)

    def reorder_members(master, rows):
        candidates = master["candidates"]
        i, j = candidates.index(rows[first]), candidates.index(rows[second])
        candidates[i], candidates[j] = candidates[j], candidates[i]

    def append_unknown(master, rows):
        master["candidates"].append(
            {"candidate_id": "src-999999", "candidate_status": "DISCOVERED"}
        )

    params = [
        ("member-removed", remove_member),
        ("member-added", add_member),
        ("member-reordered", reorder_members),
        ("reused-candidate-id", set_field(second, "candidate_id", first)),
        ("reused-wave0-id", set_field(first, "candidate_id", "wave0-010")),
        ("unknown-namespace", append_unknown),
        ("candidate-name-changed", set_field(first, "candidate_name", "架空神社")),
        ("prefecture-changed", set_field(first, "prefecture", "長野県")),
        ("source-position-changed", set_prov(first, "source_position", "page999-row999")),
        ("wrong-handoff-id", set_prov(first, "handoff_id", f"{spec['source_batch_id']}-H999")),
        ("wrong-source-batch-id", set_prov(first, "source_batch_id", "NIIGATA-999")),
        ("snapshot-sha-changed", set_prov(first, "source_snapshot_sha256", "0" * 64)),
        ("source-url-changed", set_prov(first, "source_url", "https://example.invalid/")),
        ("verified-at-changed", set_prov(first, "source_verified_at", "2026-10-09")),
        ("captured-at-changed", set_prov(first, "captured_at", "2026-10-09T00:00:00+09:00")),
        ("provenance-track-changed", set_prov(first, "track", "wave0")),
        ("provenance-prefecture-changed", set_prov(first, "prefecture", "長野県")),
        (
            "candidate-reason-changed",
            set_field(first, "candidate_reason", "historical_recovered_popularity_candidate"),
        ),
        ("wave-id-W0", set_field(first, "wave_id", "W0")),
        ("inherits-wave-id-W0", drop_field(first, "wave_id")),
        ("inherits-wave0-knowledge-default", drop_field(first, "knowledge_status")),
        ("inherits-wave0-identity-default", drop_field(first, "identity_status")),
        ("build-batch-source", set_field(first, "build_batch", spec["source_batch_id"])),
        ("build-batch-handoff", set_field(first, "build_batch", hid)),
        ("build-batch-invented-wave0", set_field(first, "build_batch", "W0-DB08")),
        ("build-batch-reused-wave0", set_field(first, "build_batch", "W0-DB04")),
    ]
    for field in sorted(HANDOFF_FORBIDDEN_HYDRATION_FIELDS):
        params.append((f"forbidden-{field}", set_field(first, field, "x")))
    params.append(
        (
            "wave0-omairi-provenance",
            set_field(
                first,
                "discovery_sources",
                [
                    {
                        "discovery_source": "Omairi 全国神社人気ランキング2026",
                        "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/1",
                        "discovery_rank": 1,
                        "captured_at": "2026-10-08",
                    }
                ],
            ),
        )
    )
    for member in members:
        cid = member["candidate_id"]
        lifecycle = member["lifecycle"]
        params += [
            (
                f"{cid}-identity-changed",
                set_field(
                    cid,
                    "identity_status",
                    _other(NATIONWIDE_IDENTITY_STATUSES, member["identity_status"]),
                ),
            ),
            (
                f"{cid}-duplicate-changed",
                set_field(
                    cid,
                    "duplicate_status",
                    _other(NATIONWIDE_DUPLICATE_STATUSES, member["duplicate_status"]),
                ),
            ),
            (
                f"{cid}-lifecycle-changed",
                set_field(
                    cid,
                    "candidate_status",
                    _other(CANONICAL_CANDIDATE_STATUSES, lifecycle["candidate_status"]),
                ),
            ),
            (
                f"{cid}-status-reason-changed",
                set_field(
                    cid,
                    "status_reason_code",
                    _other(
                        set(NATIONWIDE_POSITIVE_STATUS_REASONS.values()),
                        lifecycle["status_reason_code"],
                    ),
                ),
            ),
            (
                f"{cid}-official-source-changed",
                set_field(
                    cid,
                    "official_source_status",
                    _other(
                        NATIONWIDE_OFFICIAL_SOURCE_STATUSES, lifecycle["official_source_status"]
                    ),
                ),
            ),
            (
                f"{cid}-knowledge-changed",
                set_field(
                    cid,
                    "knowledge_status",
                    _other(NATIONWIDE_KNOWLEDGE_STATUSES, lifecycle["knowledge_status"]),
                ),
            ),
        ]
    return [pytest.param(spec, mutate, id=f"{hid}-{name}") for name, mutate in params]


@pytest.mark.parametrize(
    ("spec", "mutate"),
    [param for spec in HANDOFF_SPECS for param in _generic_handoff_mutations(spec)],
)
def test_handoff_contract_rejects_generic_mutations(spec, mutate):
    master = _load_master()
    assert _handoff_violations(master, spec) == []
    mutated = _mutated(master, mutate)
    assert mutated != master
    assert _handoff_violations(mutated, spec) != []


# --- Candidate-specific semantics -----------------------------------------------------------
#
# 以下は handoff の identity ではなく、Candidate 固有の履歴的な遷移（nsrc-000002 / nsrc-000004 の
# CORE_READY、H002 各 Candidate の G1 結果）を表す test。期待値は manifest から独立した literal を使う。

def test_nsrc_000004_is_core_ready_with_unchanged_evidence():
    """G8 Mother Ship decision（APPROVED_TARGET_ONLY）による CORE_READY。他の field は不変。"""
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000004"]

    assert row["candidate_status"] == "CORE_READY"
    assert row["status_reason_code"] == "CORE_READY_CONTRACT_PASS"
    assert row["official_source_status"] == "CONFIRMED"
    assert row["knowledge_status"] == "FACT_READY"
    assert row["build_batch"] is None
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "SAME_NAME_DIFFERENT_SHRINE"
    assert row["admission_provenance"] == _expected_member_immutable(
        "nsrc-000004", "青海神社", "page001-row004"
    )["admission_provenance"]

    # 他の H001 4社は現在の state のまま（nsrc-000004 の遷移に連動しない）。
    for candidate_id, name, position in _member_triples(H001_HANDOFF_ID):
        if candidate_id == "nsrc-000004":
            continue
        assert rows[candidate_id] == {
            **_expected_member_immutable(candidate_id, name, position),
            **_member_spec(candidate_id)["lifecycle"],
        }, candidate_id

    # Wave0 accounting は Nationwide の遷移で変わらない。
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS
    assert Counter(r["status_reason_code"] for r in wave0) == EXPECTED_REASON_COUNTS
    assert Counter(
        r["build_batch"] for r in wave0 if r["build_batch"] is not None
    ) == {batch: 5 for batch in CANONICAL_BUILD_BATCHES}


def test_nsrc_000002_is_core_ready_with_unchanged_evidence():
    """G8 Mother Ship decision（APPROVED_TARGET_ONLY）による CORE_READY。他の field は不変。"""
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000002"]

    assert row["candidate_status"] == "CORE_READY"
    assert row["status_reason_code"] == "CORE_READY_CONTRACT_PASS"
    assert row["official_source_status"] == "CONFIRMED"
    assert row["knowledge_status"] == "FACT_READY"
    assert row["build_batch"] is None
    assert row["wave_id"] is None
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "NEW"
    assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
    assert row == {
        **_expected_member_immutable("nsrc-000002", "青澤神社", "page001-row002"),
        **NATIONWIDE_CORE_READY_LIFECYCLE,
    }
    assert row["admission_provenance"] == {
        "track": "nationwide_source_candidate",
        "prefecture": "新潟県",
        "source_batch_id": "NIIGATA-001",
        "handoff_id": "NIIGATA-001-H001",
        "source_position": "page001-row002",
        "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
        "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T14:27:00+09:00",
    }

    # nsrc-000004 は CORE_READY のまま。
    assert rows["nsrc-000004"]["candidate_status"] == "CORE_READY"
    assert rows["nsrc-000004"]["status_reason_code"] == "CORE_READY_CONTRACT_PASS"

    # nsrc-000001 / 000003 / 000005 は G0 DISCOVERED のまま。
    for candidate_id, name, position in _member_triples(H001_HANDOFF_ID):
        if candidate_id in {"nsrc-000002", "nsrc-000004"}:
            continue
        assert rows[candidate_id] == {
            **_expected_member_immutable(candidate_id, name, position),
            **NATIONWIDE_DISCOVERED_LIFECYCLE,
        }, candidate_id

    # Historical Wave0 accounting は Nationwide の遷移で変わらない。
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS
    assert Counter(r["status_reason_code"] for r in wave0) == EXPECTED_REASON_COUNTS
    assert Counter(
        r["build_batch"] for r in wave0 if r["build_batch"] is not None
    ) == {batch: 5 for batch in CANONICAL_BUILD_BATCHES}


def _set(candidate_id: str, key: str, value):
    def mutate(master, rows):
        rows[candidate_id][key] = value

    return mutate


def _drop(candidate_id: str, key: str):
    def mutate(master, rows):
        del rows[candidate_id][key]

    return mutate


def _set_provenance(candidate_id: str, key: str, value):
    def mutate(master, rows):
        rows[candidate_id]["admission_provenance"][key] = value

    return mutate


def _append_row(row: dict):
    def mutate(master, rows):
        master["candidates"].append(row)

    return mutate


# nsrc-000002 / nsrc-000004 の CORE_READY 遷移と、他の H001 member が連動しないことの mutation。
# 汎用 category は test_handoff_contract_rejects_generic_mutations にもある（重複は意図的。既存 id を保持する）。
@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_set("nsrc-000003", "candidate_id", "nsrc-000006"), id="renamed-id"),
        pytest.param(_set("nsrc-000004", "candidate_id", "nsrc-000002"), id="reused-id"),
        pytest.param(_set("nsrc-000005", "candidate_id", "wave0-010"), id="reused-wave0-id"),
        pytest.param(
            _set_provenance("nsrc-000002", "source_position", "page001-row006"),
            id="changed-source-position",
        ),
        pytest.param(_drop("nsrc-000001", "wave_id"), id="inherits-wave-id-W0"),
        pytest.param(_set("nsrc-000001", "wave_id", "W0"), id="wave-id-W0"),
        pytest.param(
            _drop("nsrc-000002", "knowledge_status"), id="inherits-acquisition-path-confirmed"
        ),
        pytest.param(
            _set("nsrc-000002", "knowledge_status", "ACQUISITION_PATH_CONFIRMED"),
            id="acquisition-path-confirmed",
        ),
        pytest.param(_set("nsrc-000003", "candidate_status", "BUILD_READY"), id="build-ready"),
        pytest.param(_set("nsrc-000001", "identity_status", "UNREVIEWED"), id="g1-identity-regression"),
        pytest.param(_set("nsrc-000004", "duplicate_status", "NEW"), id="same-name-classification-regression"),
        pytest.param(_set("nsrc-000004", "build_batch", "NIIGATA-001"), id="build-batch-source"),
        pytest.param(
            _set("nsrc-000004", "build_batch", "NIIGATA-001-H001"), id="build-batch-handoff"
        ),
        pytest.param(
            _set(
                "nsrc-000005",
                "discovery_sources",
                [
                    {
                        "discovery_source": "Omairi 全国神社人気ランキング2026",
                        "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/1",
                        "discovery_rank": 1,
                        "captured_at": "2026-10-08",
                    }
                ],
            ),
            id="wave0-omairi-provenance",
        ),
        pytest.param(_set("nsrc-000005", "discovery_rank", 1), id="wave0-ranking"),
        pytest.param(_set("nsrc-000001", "official_name", "相吉神社"), id="premature-hydration"),
        pytest.param(
            _set_provenance("nsrc-000003", "source_snapshot_sha256", "0" * 64),
            id="changed-snapshot-sha",
        ),
        pytest.param(
            _append_row({"candidate_id": "src-000006", "candidate_status": "DISCOVERED"}),
            id="unknown-namespace",
        ),
        # nsrc-000004（CORE_READY）の lifecycle と immutable evidence。
        pytest.param(_set("nsrc-000004", "candidate_status", "IMPORTED"), id="n4-regressed-to-imported"),
        pytest.param(
            _set("nsrc-000004", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="n4-core-ready-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000004", "candidate_status", "DISCOVERED"), id="n4-lifecycle-regression"),
        pytest.param(_set("nsrc-000004", "knowledge_status", "UNREVIEWED"), id="n4-knowledge-regression"),
        pytest.param(_drop("nsrc-000004", "knowledge_status"), id="n4-inherits-wave0-knowledge-default"),
        pytest.param(
            _set("nsrc-000004", "official_source_status", "AVAILABLE"), id="n4-official-source-regression"
        ),
        pytest.param(_set("nsrc-000004", "build_batch", "W0-DB08"), id="n4-invented-wave0-build-batch"),
        pytest.param(_set("nsrc-000004", "build_batch", "W0-DB04"), id="n4-reused-wave0-build-batch"),
        pytest.param(
            _set_provenance("nsrc-000004", "source_url", "https://example.invalid/"),
            id="n4-changed-provenance",
        ),
        pytest.param(
            _set("nsrc-000004", "duplicate_status", "SAME_SHRINE"), id="n4-duplicate-evidence-change"
        ),
        # nsrc-000002（CORE_READY）の lifecycle と immutable evidence。
        pytest.param(_set("nsrc-000002", "candidate_status", "IMPORTED"), id="n2-regressed-to-imported"),
        pytest.param(
            _set("nsrc-000002", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="n2-core-ready-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000002", "candidate_status", "DISCOVERED"), id="n2-regressed-to-discovered"),
        pytest.param(
            _set("nsrc-000002", "status_reason_code", "REGISTRY_ADMISSION_COMPLETE"),
            id="n2-discovered-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000002", "candidate_status", "BUILD_READY"), id="n2-regressed-to-build-ready"),
        pytest.param(_set("nsrc-000002", "knowledge_status", "UNREVIEWED"), id="n2-knowledge-regression"),
        pytest.param(
            _set("nsrc-000002", "official_source_status", "AVAILABLE"), id="n2-official-source-regression"
        ),
        pytest.param(_drop("nsrc-000002", "official_source_status"), id="n2-inherits-wave0-official-default"),
        pytest.param(_set("nsrc-000002", "build_batch", "W0-DB08"), id="n2-invented-wave0-build-batch"),
        pytest.param(_set("nsrc-000002", "build_batch", "NIIGATA-001"), id="n2-build-batch-source"),
        pytest.param(_set("nsrc-000002", "build_batch", "NIIGATA-001-H001"), id="n2-build-batch-handoff"),
        pytest.param(_set("nsrc-000002", "identity_status", "UNREVIEWED"), id="n2-identity-regression"),
        pytest.param(_set("nsrc-000002", "duplicate_status", "SAME_SHRINE"), id="n2-duplicate-evidence-change"),
        pytest.param(
            _set_provenance("nsrc-000002", "captured_at", "2026-10-10T00:00:00+09:00"),
            id="n2-changed-provenance",
        ),
        # 他の4社が nsrc-000002 / nsrc-000004 に連動して進まないこと。
        pytest.param(_set("nsrc-000001", "candidate_status", "IMPORTED"), id="other-member-advanced"),
        pytest.param(_set("nsrc-000003", "candidate_status", "IMPORTED"), id="other-member-n3-advanced"),
        pytest.param(
            _set("nsrc-000003", "candidate_status", "CORE_READY"), id="other-member-n3-core-ready"
        ),
        pytest.param(
            _set("nsrc-000001", "status_reason_code", "CORE_READY_CONTRACT_PASS"),
            id="other-member-n1-core-ready-reason",
        ),
        pytest.param(
            _set("nsrc-000005", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="other-member-n5-reason-advanced",
        ),
        pytest.param(
            _set("nsrc-000005", "knowledge_status", "FACT_READY"), id="other-member-knowledge-advanced"
        ),
    ],
)
def test_niigata_h001_contract_rejects_mutations(mutate):
    master = _load_master()
    spec = _handoff_spec(H001_HANDOFF_ID)
    assert _handoff_violations(master, spec) == []
    assert _handoff_violations(_mutated(master, mutate), spec) != []


def test_nsrc_000006_is_core_ready_with_unchanged_evidence():
    """G8 Mother Ship decision（APPROVED_TARGET_ONLY）による CORE_READY。他の field は不変。"""
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000006"]

    assert row["candidate_status"] == "CORE_READY"
    assert row["status_reason_code"] == "CORE_READY_CONTRACT_PASS"
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "NEW"
    assert row["official_source_status"] == "CONFIRMED"
    assert row["knowledge_status"] == "FACT_READY"
    assert row["build_batch"] is None
    assert row["wave_id"] is None
    assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
    assert row == {
        **_expected_member_immutable("nsrc-000006", "赤井神社", "page001-row006"),
        **NATIONWIDE_CORE_READY_LIFECYCLE,
    }
    assert row["admission_provenance"] == {
        "track": "nationwide_source_candidate",
        "prefecture": "新潟県",
        "source_batch_id": "NIIGATA-001",
        "handoff_id": "NIIGATA-001-H002",
        "source_position": "page001-row006",
        "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
        "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T14:27:00+09:00",
    }
    assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())

    # 他の H002 Candidate は nsrc-000006 の G7 sync に連動しない。
    for candidate_id in ("nsrc-000007", "nsrc-000008", "nsrc-000009", "nsrc-000010"):
        expected = _member_spec(candidate_id)["lifecycle"]
        for field in HANDOFF_LIFECYCLE_FIELDS:
            assert rows[candidate_id][field] == expected[field], (candidate_id, field)

    assert _handoff_violations(master, _handoff_spec(H001_HANDOFF_ID)) == []
    assert _handoff_violations(master, _handoff_spec(H002_HANDOFF_ID)) == []
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


def test_nsrc_000007_is_core_ready_with_unchanged_evidence():
    """G8 Mother Ship decision（APPROVED_TARGET_ONLY）による CORE_READY。他の field は不変。"""
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000007"]

    assert row["candidate_status"] == "CORE_READY"
    assert row["status_reason_code"] == "CORE_READY_CONTRACT_PASS"
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "SAME_NAME_DIFFERENT_SHRINE"
    assert row["official_source_status"] == "CONFIRMED"
    assert row["knowledge_status"] == "FACT_READY"
    assert row["build_batch"] is None
    assert row["wave_id"] is None
    assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
    assert row == {
        **_expected_member_immutable("nsrc-000007", "赤城社", "page001-row007"),
        **NATIONWIDE_CORE_READY_LIFECYCLE,
    }
    assert row["admission_provenance"] == {
        "track": "nationwide_source_candidate",
        "prefecture": "新潟県",
        "source_batch_id": "NIIGATA-001",
        "handoff_id": "NIIGATA-001-H002",
        "source_position": "page001-row007",
        "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
        "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T14:27:00+09:00",
    }
    assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())
    assert "reading" not in row

    # 他の H002 Candidate は target-only transition に連動しない。
    for candidate_id in ("nsrc-000006", "nsrc-000008", "nsrc-000009", "nsrc-000010"):
        expected = _member_spec(candidate_id)["lifecycle"]
        for field in HANDOFF_LIFECYCLE_FIELDS:
            assert rows[candidate_id][field] == expected[field], (candidate_id, field)

    # 既存 CORE_READY Candidate は不変。
    for candidate_id in ("nsrc-000002", "nsrc-000004"):
        assert rows[candidate_id]["candidate_status"] == "CORE_READY", candidate_id
        assert rows[candidate_id]["status_reason_code"] == "CORE_READY_CONTRACT_PASS", candidate_id

    assert [r["candidate_id"] for r in master["candidates"] if r["candidate_name"] == "赤城社"] == [
        "nsrc-000007",
        "nsrc-000008",
        "nsrc-000009",
        "nsrc-000010",
    ]

    assert _handoff_violations(master, _handoff_spec(H001_HANDOFF_ID)) == []
    assert _handoff_violations(master, _handoff_spec(H002_HANDOFF_ID)) == []
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


def test_nsrc_000008_g1_is_confirmed_same_name_different_shrine_and_stays_discovered():
    """G1 PASS / SAME_NAME_DIFFERENT_SHRINE。他の赤城社3件とは別 identity。lifecycle は進めない。"""
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000008"]

    assert row["candidate_status"] == "DISCOVERED"
    assert row["status_reason_code"] == "REGISTRY_ADMISSION_COMPLETE"
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "SAME_NAME_DIFFERENT_SHRINE"
    assert row["official_source_status"] == "AVAILABLE"
    assert row["knowledge_status"] == "UNREVIEWED"
    assert row["build_batch"] is None
    assert row["wave_id"] is None
    assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
    assert row == _expected_member_row("nsrc-000008", "赤城社", "page001-row008")
    assert row["admission_provenance"] == {
        "track": "nationwide_source_candidate",
        "prefecture": "新潟県",
        "source_batch_id": "NIIGATA-001",
        "handoff_id": "NIIGATA-001-H002",
        "source_position": "page001-row008",
        "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
        "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T14:27:00+09:00",
    }
    assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())
    assert "reading" not in row

    # 他の H002 Candidate は nsrc-000008 の G1 に連動しない（各自の G1 現在値のまま）。
    for candidate_id in ("nsrc-000006", "nsrc-000007", "nsrc-000009", "nsrc-000010"):
        g1 = _member_g1(candidate_id)
        assert rows[candidate_id]["identity_status"] == g1["identity_status"], candidate_id
        assert rows[candidate_id]["duplicate_status"] == g1["duplicate_status"], candidate_id
        expected_status = _member_spec(candidate_id)["lifecycle"]["candidate_status"]
        assert rows[candidate_id]["candidate_status"] == expected_status, candidate_id

    # 赤城社4件は別 Candidate のまま（id / source_position が別々）。
    akagi = [r for r in master["candidates"] if r["candidate_name"] == "赤城社"]
    assert [r["candidate_id"] for r in akagi] == [
        "nsrc-000007",
        "nsrc-000008",
        "nsrc-000009",
        "nsrc-000010",
    ]
    assert [r["admission_provenance"]["source_position"] for r in akagi] == [
        "page001-row007",
        "page001-row008",
        "page001-row009",
        "page001-row010",
    ]

    assert _handoff_violations(master, _handoff_spec(H001_HANDOFF_ID)) == []
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


def test_nsrc_000009_is_core_ready_with_unchanged_evidence():
    """G8 Mother Ship decision（APPROVED_TARGET_ONLY）による CORE_READY。他の field は不変。

    docs/audit/niigata-h002-nsrc-000009-g8-core-ready-pretransition.md（PRE_TRANSITION 12/12 SATISFIED）。
    """
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000009"]

    assert row["candidate_status"] == "CORE_READY"
    assert row["status_reason_code"] == "CORE_READY_CONTRACT_PASS"
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "SAME_NAME_DIFFERENT_SHRINE"
    assert row["official_source_status"] == "CONFIRMED"
    assert row["knowledge_status"] == "FACT_READY"
    assert row["build_batch"] is None
    assert row["wave_id"] is None
    assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
    assert row == {
        **_expected_member_immutable("nsrc-000009", "赤城社", "page001-row009"),
        **NATIONWIDE_CORE_READY_LIFECYCLE,
    }
    assert row["admission_provenance"] == {
        "track": "nationwide_source_candidate",
        "prefecture": "新潟県",
        "source_batch_id": "NIIGATA-001",
        "handoff_id": "NIIGATA-001-H002",
        "source_position": "page001-row009",
        "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
        "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T14:27:00+09:00",
    }
    assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())
    assert "reading" not in row

    # 他の赤城社2件は nsrc-000009 の target-only transition に連動しない（DISCOVERED のまま）。
    for candidate_id in ("nsrc-000008", "nsrc-000010"):
        g1 = _member_g1(candidate_id)
        assert rows[candidate_id]["identity_status"] == g1["identity_status"], candidate_id
        assert rows[candidate_id]["duplicate_status"] == g1["duplicate_status"], candidate_id
        for field, value in NATIONWIDE_DISCOVERED_LIFECYCLE.items():
            assert rows[candidate_id][field] == value, (candidate_id, field)

    # H002 の CORE_READY は nsrc-000006 / nsrc-000007 / nsrc-000009 だけ。IMPORTED は残らない。
    h002_lifecycle = {
        r["candidate_id"]: (r["candidate_status"], r["status_reason_code"])
        for r in master["candidates"]
        if (r.get("admission_provenance") or {}).get("handoff_id") == H002_HANDOFF_ID
    }
    assert h002_lifecycle == {
        "nsrc-000006": ("CORE_READY", "CORE_READY_CONTRACT_PASS"),
        "nsrc-000007": ("CORE_READY", "CORE_READY_CONTRACT_PASS"),
        "nsrc-000008": ("DISCOVERED", "REGISTRY_ADMISSION_COMPLETE"),
        "nsrc-000009": ("CORE_READY", "CORE_READY_CONTRACT_PASS"),
        "nsrc-000010": ("DISCOVERED", "REGISTRY_ADMISSION_COMPLETE"),
    }

    # 既存 CORE_READY Candidate は不変。
    for candidate_id in ("nsrc-000002", "nsrc-000004"):
        assert rows[candidate_id]["candidate_status"] == "CORE_READY", candidate_id
        assert rows[candidate_id]["status_reason_code"] == "CORE_READY_CONTRACT_PASS", candidate_id

    # nsrc-000006 / nsrc-000007（既に CORE_READY）は不変。
    assert {
        k: rows["nsrc-000006"][k] for k in ("identity_status", "duplicate_status", "candidate_status")
    } == {"identity_status": "CONFIRMED", "duplicate_status": "NEW", "candidate_status": "CORE_READY"}
    assert {
        k: rows["nsrc-000007"][k] for k in ("identity_status", "duplicate_status", "candidate_status")
    } == {
        "identity_status": "CONFIRMED",
        "duplicate_status": "SAME_NAME_DIFFERENT_SHRINE",
        "candidate_status": "CORE_READY",
    }

    # 赤城社4件は別 Candidate のまま（id / source_position が別々）。
    akagi = [r for r in master["candidates"] if r["candidate_name"] == "赤城社"]
    assert [r["candidate_id"] for r in akagi] == [
        "nsrc-000007",
        "nsrc-000008",
        "nsrc-000009",
        "nsrc-000010",
    ]
    assert [r["admission_provenance"]["source_position"] for r in akagi] == [
        "page001-row007",
        "page001-row008",
        "page001-row009",
        "page001-row010",
    ]

    assert _handoff_violations(master, _handoff_spec(H001_HANDOFF_ID)) == []
    assert _handoff_violations(master, _handoff_spec(H002_HANDOFF_ID)) == []
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


def test_nsrc_000010_g1_is_confirmed_same_name_different_shrine_and_stays_discovered():
    """G1 PASS / SAME_NAME_DIFFERENT_SHRINE。他の赤城社3件とは別 identity。lifecycle は進めない。"""
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    row = rows["nsrc-000010"]

    assert row["candidate_status"] == "DISCOVERED"
    assert row["status_reason_code"] == "REGISTRY_ADMISSION_COMPLETE"
    assert row["identity_status"] == "CONFIRMED"
    assert row["duplicate_status"] == "SAME_NAME_DIFFERENT_SHRINE"
    assert row["official_source_status"] == "AVAILABLE"
    assert row["knowledge_status"] == "UNREVIEWED"
    assert row["build_batch"] is None
    assert row["wave_id"] is None
    assert row["candidate_reason"] == NATIONWIDE_CANDIDATE_REASON
    assert row == _expected_member_row("nsrc-000010", "赤城社", "page001-row010")
    assert row["admission_provenance"] == {
        "track": "nationwide_source_candidate",
        "prefecture": "新潟県",
        "source_batch_id": "NIIGATA-001",
        "handoff_id": "NIIGATA-001-H002",
        "source_position": "page001-row010",
        "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
        "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
        "source_verified_at": "2026-10-08",
        "captured_at": "2026-10-08T14:27:00+09:00",
    }
    assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys())
    assert "reading" not in row

    # 他の H002 Candidate は nsrc-000010 の G1 に連動しない（各自の G1 現在値のまま）。
    for candidate_id in ("nsrc-000006", "nsrc-000007", "nsrc-000008", "nsrc-000009"):
        g1 = _member_g1(candidate_id)
        assert rows[candidate_id]["identity_status"] == g1["identity_status"], candidate_id
        assert rows[candidate_id]["duplicate_status"] == g1["duplicate_status"], candidate_id
        expected_status = _member_spec(candidate_id)["lifecycle"]["candidate_status"]
        assert rows[candidate_id]["candidate_status"] == expected_status, candidate_id

    # 赤城社4件は別 Candidate のまま（id / source_position が別々）。
    akagi = [r for r in master["candidates"] if r["candidate_name"] == "赤城社"]
    assert [r["candidate_id"] for r in akagi] == [
        "nsrc-000007",
        "nsrc-000008",
        "nsrc-000009",
        "nsrc-000010",
    ]
    assert [r["admission_provenance"]["source_position"] for r in akagi] == [
        "page001-row007",
        "page001-row008",
        "page001-row009",
        "page001-row010",
    ]

    assert _handoff_violations(master, _handoff_spec(H001_HANDOFF_ID)) == []
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


def test_niigata_h002_g1_is_resolved_with_independent_lifecycle_states():
    """H002 の G1 は全5件 resolved。Lifecycle は Candidate ごとに独立して進む。"""
    master = _load_master()
    h002 = [
        row
        for row in master["candidates"]
        if (row.get("admission_provenance") or {}).get("handoff_id") == H002_HANDOFF_ID
    ]
    assert {
        row["candidate_id"]: (row["identity_status"], row["duplicate_status"]) for row in h002
    } == {
        "nsrc-000006": ("CONFIRMED", "NEW"),
        "nsrc-000007": ("CONFIRMED", "SAME_NAME_DIFFERENT_SHRINE"),
        "nsrc-000008": ("CONFIRMED", "SAME_NAME_DIFFERENT_SHRINE"),
        "nsrc-000009": ("CONFIRMED", "SAME_NAME_DIFFERENT_SHRINE"),
        "nsrc-000010": ("CONFIRMED", "SAME_NAME_DIFFERENT_SHRINE"),
    }
    assert {row["candidate_id"]: row["candidate_status"] for row in h002} == {
        "nsrc-000006": "CORE_READY",
        "nsrc-000007": "CORE_READY",
        "nsrc-000008": "DISCOVERED",
        "nsrc-000009": "CORE_READY",
        "nsrc-000010": "DISCOVERED",
    }
    assert not any(
        row["identity_status"] == "UNREVIEWED" or row["duplicate_status"] == "UNREVIEWED"
        for row in h002
    )
    assert _handoff_violations(master, _handoff_spec(H002_HANDOFF_ID)) == []


def _h002_reorder(master, rows):
    candidates = master["candidates"]
    i, j = (
        candidates.index(rows["nsrc-000007"]),
        candidates.index(rows["nsrc-000008"]),
    )
    candidates[i], candidates[j] = candidates[j], candidates[i]


def _h002_remove(candidate_id: str):
    def mutate(master, rows):
        master["candidates"].remove(rows[candidate_id])

    return mutate


def _h002_extra_member(master, rows):
    extra = json.loads(json.dumps(rows["nsrc-000010"]))
    # 未登録の candidate_id（nsrc-000011〜000015 は H003、nsrc-000016〜000020 は H004 が使用済み）。
    extra["candidate_id"] = "nsrc-000021"
    extra["admission_provenance"]["source_position"] = "page003-row001"
    master["candidates"].append(extra)


# H002 各 Candidate の current identity / lifecycle（regression / premature advancement / 同名統合）の mutation。
@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_set("nsrc-000008", "candidate_id", "nsrc-000011"), id="h002-renamed-id"),
        pytest.param(_set("nsrc-000007", "candidate_id", "nsrc-000002"), id="h002-reused-nsrc-id"),
        pytest.param(_set("nsrc-000006", "candidate_id", "wave0-010"), id="h002-reused-wave0-id"),
        pytest.param(
            _set_provenance("nsrc-000009", "source_position", "page001-row011"),
            id="h002-changed-source-position",
        ),
        pytest.param(
            _set_provenance("nsrc-000010", "handoff_id", "NIIGATA-001-H001"),
            id="h002-changed-handoff-id",
        ),
        pytest.param(
            _set_provenance("nsrc-000006", "source_snapshot_sha256", "0" * 64),
            id="h002-changed-snapshot-sha",
        ),
        pytest.param(_set("nsrc-000008", "duplicate_status", "NEW"), id="h002-premature-duplicate-new"),
        pytest.param(
            _set("nsrc-000009", "duplicate_status", "SAME_SHRINE"),
            id="h002-premature-duplicate-same-shrine",
        ),
        pytest.param(_set("nsrc-000006", "candidate_status", "DISCOVERED"), id="h002-n6-regressed-discovered"),
        pytest.param(_set("nsrc-000006", "candidate_status", "BUILD_READY"), id="h002-n6-regressed-build-ready"),
        pytest.param(_set("nsrc-000006", "candidate_status", "IMPORTED"), id="h002-n6-regressed-imported"),
        pytest.param(
            _set("nsrc-000006", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="h002-n6-core-ready-reason-regression",
        ),
        pytest.param(
            _set("nsrc-000006", "official_source_status", "AVAILABLE"),
            id="h002-n6-official-source-regression",
        ),
        pytest.param(
            _set("nsrc-000006", "knowledge_status", "UNREVIEWED"),
            id="h002-n6-knowledge-regression",
        ),
        pytest.param(_set("nsrc-000006", "official_name", "赤井神社"), id="h002-premature-official-name"),
        pytest.param(
            _set("nsrc-000007", "official_address", "十日町市四日町2534番地"),
            id="h002-premature-official-address",
        ),
        pytest.param(_set("nsrc-000010", "latitude", 37.0), id="h002-premature-coordinate"),
        pytest.param(_set("nsrc-000008", "build_batch", "NIIGATA-001"), id="h002-build-batch-source"),
        pytest.param(
            _set("nsrc-000008", "build_batch", "NIIGATA-001-H002"), id="h002-build-batch-handoff"
        ),
        pytest.param(_set("nsrc-000009", "build_batch", "W0-DB08"), id="h002-invented-wave0-build-batch"),
        pytest.param(
            _set(
                "nsrc-000006",
                "discovery_sources",
                [
                    {
                        "discovery_source": "Omairi 全国神社人気ランキング2026",
                        "discovery_source_url": "https://omairi.club/spots/ranking/shrine/page/1",
                        "discovery_rank": 1,
                        "captured_at": "2026-10-08",
                    }
                ],
            ),
            id="h002-wave0-discovery-sources",
        ),
        pytest.param(_set("nsrc-000007", "discovery_rank", 1), id="h002-wave0-discovery-rank"),
        pytest.param(_drop("nsrc-000010", "wave_id"), id="h002-inherits-wave-id-W0"),
        pytest.param(_drop("nsrc-000006", "knowledge_status"), id="h002-inherits-wave0-knowledge"),
        pytest.param(
            _append_row({"candidate_id": "src-000011", "candidate_status": "DISCOVERED"}),
            id="h002-unknown-namespace",
        ),
        pytest.param(_h002_reorder, id="h002-member-reordered"),
        pytest.param(_h002_remove("nsrc-000006"), id="h002-member-removed"),
        pytest.param(_h002_extra_member, id="h002-member-added"),
        # nsrc-000006（G7 IMPORTED / G1 NEW）の identity / duplicate / forbidden hydration regression。
        # lifecycle / official_source / knowledge の G7 regression と premature CORE_READY は上の n6 cases で固定済み。
        pytest.param(_set("nsrc-000006", "identity_status", "UNREVIEWED"), id="n6-identity-regression"),
        pytest.param(_set("nsrc-000006", "duplicate_status", "UNREVIEWED"), id="n6-duplicate-regression"),
        pytest.param(_set("nsrc-000006", "duplicate_status", "SAME_SHRINE"), id="n6-duplicate-same-shrine"),
        pytest.param(
            _set("nsrc-000006", "duplicate_status", "SAME_NAME_DIFFERENT_SHRINE"),
            id="n6-duplicate-same-name-different-shrine",
        ),
        pytest.param(
            _set("nsrc-000006", "official_address", "新潟県佐渡市加茂歌代2662番地"),
            id="n6-official-address-hydrated",
        ),
        pytest.param(_set("nsrc-000006", "latitude", 38.0), id="n6-coordinate-before-g2"),
        pytest.param(
            _set_provenance("nsrc-000006", "source_url", "https://example.invalid/"),
            id="n6-changed-provenance",
        ),
        # nsrc-000007（G8 CORE_READY）の lifecycle / immutable evidence regression。
        pytest.param(_set("nsrc-000007", "identity_status", "UNREVIEWED"), id="n7-identity-regression"),
        pytest.param(_set("nsrc-000007", "duplicate_status", "UNREVIEWED"), id="n7-duplicate-regression"),
        pytest.param(_set("nsrc-000007", "duplicate_status", "NEW"), id="n7-duplicate-new"),
        pytest.param(_set("nsrc-000007", "duplicate_status", "SAME_SHRINE"), id="n7-duplicate-same-shrine"),
        pytest.param(_set("nsrc-000007", "candidate_status", "IMPORTED"), id="n7-regressed-to-imported"),
        pytest.param(
            _set("nsrc-000007", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="n7-core-ready-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000007", "candidate_status", "DISCOVERED"), id="n7-regressed-to-discovered"),
        pytest.param(
            _set("nsrc-000007", "status_reason_code", "REGISTRY_ADMISSION_COMPLETE"),
            id="n7-discovered-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000007", "candidate_status", "BUILD_READY"), id="n7-regressed-to-build-ready"),
        pytest.param(
            _set("nsrc-000007", "official_source_status", "AVAILABLE"),
            id="n7-official-source-regression",
        ),
        pytest.param(_set("nsrc-000007", "knowledge_status", "UNREVIEWED"), id="n7-knowledge-regression"),
        pytest.param(_set("nsrc-000007", "build_batch", "W0-DB08"), id="n7-invented-wave0-build-batch"),
        pytest.param(_set("nsrc-000007", "build_batch", "NIIGATA-001"), id="n7-build-batch-source"),
        pytest.param(_set("nsrc-000007", "build_batch", "NIIGATA-001-H002"), id="n7-build-batch-handoff"),
        pytest.param(
            _set("nsrc-000007", "official_address", "新潟県十日町市四日町2534番地"),
            id="n7-official-address-hydrated",
        ),
        pytest.param(_set("nsrc-000007", "reading", "あかぎしゃ"), id="n7-reading-hydrated"),
        pytest.param(_set("nsrc-000007", "latitude", 37.1), id="n7-coordinate-before-g2"),
        pytest.param(
            _set_provenance("nsrc-000007", "source_position", "page001-row008"),
            id="n7-changed-provenance",
        ),
        # nsrc-000008（G1 PASS / SAME_NAME_DIFFERENT_SHRINE）の regression と G1 を超えた advancement。
        # 旧 h002-n8-unapproved-* は nsrc-000008 の G1 PASS で no-op になるため置き換えた。
        pytest.param(_set("nsrc-000008", "identity_status", "UNREVIEWED"), id="n8-identity-regression"),
        pytest.param(_set("nsrc-000008", "duplicate_status", "UNREVIEWED"), id="n8-duplicate-regression"),
        pytest.param(_set("nsrc-000008", "duplicate_status", "SAME_SHRINE"), id="n8-duplicate-same-shrine"),
        pytest.param(_set("nsrc-000008", "candidate_status", "BUILD_READY"), id="n8-lifecycle-beyond-g1"),
        pytest.param(
            _set("nsrc-000008", "official_source_status", "CONFIRMED"), id="n8-official-source-beyond-g1"
        ),
        pytest.param(_set("nsrc-000008", "knowledge_status", "FACT_READY"), id="n8-knowledge-beyond-g1"),
        pytest.param(
            _set("nsrc-000008", "official_name", "赤城社"),
            id="n8-official-name-hydrated",
        ),
        pytest.param(
            _set("nsrc-000008", "official_address", "新潟県十日町市上組2059番地子"),
            id="n8-official-address-hydrated",
        ),
        pytest.param(_set("nsrc-000008", "reading", "あかぎしゃ"), id="n8-reading-hydrated"),
        pytest.param(_set("nsrc-000008", "latitude", 37.1), id="n8-coordinate-before-g2"),
        pytest.param(
            _set_provenance("nsrc-000008", "source_position", "page001-row007"),
            id="n8-changed-provenance",
        ),
        # nsrc-000009（G8 CORE_READY）の lifecycle / immutable evidence regression。
        pytest.param(_set("nsrc-000009", "identity_status", "UNREVIEWED"), id="n9-identity-regression"),
        pytest.param(_set("nsrc-000009", "duplicate_status", "UNREVIEWED"), id="n9-duplicate-regression"),
        pytest.param(_set("nsrc-000009", "duplicate_status", "NEW"), id="n9-duplicate-new"),
        pytest.param(_set("nsrc-000009", "duplicate_status", "SAME_SHRINE"), id="n9-duplicate-same-shrine"),
        pytest.param(_set("nsrc-000009", "candidate_status", "IMPORTED"), id="n9-regressed-to-imported"),
        pytest.param(
            _set("nsrc-000009", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="n9-core-ready-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000009", "candidate_status", "DISCOVERED"), id="n9-regressed-to-discovered"),
        pytest.param(
            _set("nsrc-000009", "status_reason_code", "REGISTRY_ADMISSION_COMPLETE"),
            id="n9-discovered-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000009", "candidate_status", "BUILD_READY"), id="n9-regressed-to-build-ready"),
        pytest.param(
            _set("nsrc-000009", "official_source_status", "AVAILABLE"),
            id="n9-official-source-regression",
        ),
        pytest.param(_set("nsrc-000009", "knowledge_status", "UNREVIEWED"), id="n9-knowledge-regression"),
        pytest.param(
            _set("nsrc-000009", "official_address", "新潟県十日町市伊達乙48番地"),
            id="n9-official-address-hydrated",
        ),
        pytest.param(_set("nsrc-000009", "reading", "あかぎしゃ"), id="n9-reading-hydrated"),
        pytest.param(_set("nsrc-000009", "latitude", 37.1), id="n9-coordinate-before-g2"),
        pytest.param(
            _set_provenance("nsrc-000009", "captured_at", "2026-10-11T00:00:00+09:00"),
            id="n9-changed-provenance",
        ),
        # nsrc-000010（G1 PASS / SAME_NAME_DIFFERENT_SHRINE）の regression と G1 を超えた advancement。
        # nsrc-000010 の G1 PASS で H002 に未判定 Candidate は無くなった。no-op になる
        # h002-premature-identity / h002-n10-unapproved-identity /
        # h002-n10-unapproved-same-name-different-shrine は削除し、以下の regression に置き換えた。
        pytest.param(_set("nsrc-000010", "identity_status", "UNREVIEWED"), id="n10-identity-regression"),
        pytest.param(_set("nsrc-000010", "duplicate_status", "UNREVIEWED"), id="n10-duplicate-regression"),
        pytest.param(_set("nsrc-000010", "duplicate_status", "NEW"), id="n10-duplicate-new"),
        pytest.param(_set("nsrc-000010", "duplicate_status", "SAME_SHRINE"), id="n10-duplicate-same-shrine"),
        pytest.param(_set("nsrc-000010", "candidate_status", "BUILD_READY"), id="n10-lifecycle-beyond-g1"),
        pytest.param(
            _set("nsrc-000010", "status_reason_code", "BUILD_READY_COMPLETE"),
            id="n10-status-reason-changed",
        ),
        pytest.param(
            _set("nsrc-000010", "official_source_status", "CONFIRMED"), id="n10-official-source-beyond-g1"
        ),
        pytest.param(_set("nsrc-000010", "knowledge_status", "FACT_READY"), id="n10-knowledge-beyond-g1"),
        pytest.param(_set("nsrc-000010", "build_batch", "W0-DB08"), id="n10-build-batch-assigned"),
        pytest.param(_set("nsrc-000010", "wave_id", "W0"), id="n10-wave-id-assigned"),
        pytest.param(
            _set("nsrc-000010", "candidate_reason", "ranking_seed_candidate"),
            id="n10-candidate-reason-changed",
        ),
        pytest.param(_set("nsrc-000010", "official_name", "赤城社"), id="n10-official-name-hydrated"),
        pytest.param(
            _set("nsrc-000010", "official_address", "新潟県南魚沼市芹田79番地"),
            id="n10-official-address-hydrated",
        ),
        pytest.param(_set("nsrc-000010", "reading", "あかぎしゃ"), id="n10-reading-hydrated"),
        pytest.param(_set("nsrc-000010", "latitude", 37.1), id="n10-coordinate-before-g2"),
        pytest.param(_set("nsrc-000010", "longitude", 138.9), id="n10-longitude-before-g2"),
        pytest.param(_set("nsrc-000010", "shrine_id", 123), id="n10-shrine-id-hydrated"),
        pytest.param(_set("nsrc-000010", "goriyaku", "家内安全"), id="n10-goriyaku-hydrated"),
        pytest.param(
            _set_provenance("nsrc-000010", "source_position", "page001-row009"),
            id="n10-changed-provenance",
        ),
        # 同名の赤城社を1件に統合（重複排除）した状態。
        pytest.param(_h002_remove("nsrc-000009"), id="h002-akagi-deduplicated"),
        pytest.param(_set("nsrc-000008", "candidate_name", "赤城神社"), id="h002-akagi-renamed"),
    ],
)
def test_niigata_h002_contract_rejects_mutations(mutate):
    master = _load_master()
    spec = _handoff_spec(H002_HANDOFF_ID)
    assert _handoff_violations(master, spec) == []
    assert _handoff_violations(_mutated(master, mutate), spec) != []


# --- NIIGATA-001-H003（Catalog-only C6 / C7 closed） -------------------------------------
#
# H003 は G1 PASS。nsrc-000011 / 000012 / 000013 / 000015 は Catalog-only Track で C6 Production
# Import CLOSED / PASS、C7 CATALOG_READY（audit-level）。gate contract §11A C7:
#   Candidate Master lifecycle after Catalog import = IMPORTED
#   Recommendation eligibility = NOT_APPLICABLE, CORE_READY = NO
# CATALOG_READY は candidate_status enum に追加しない。Catalog import は Knowledge を書かないため
# knowledge_status は FACT_READY にしない（UNREVIEWED のまま）。official_source_status も不変。
# nsrc-000014 は G2 HOLD_POSITION_REVIEW / NOT_IN_WRITE_COHORT のまま DISCOVERED。
# docs/audit/niigata-h003-c6-production-import-artifact.md / docs/audit/niigata-h003-c7-catalog-ready.md
# 同名の赤城神社5件は別々の Candidate であり、名前から identity / duplicate を推論しない。
# 期待値は manifest から独立した literal を使う。

H003_MEMBERS = (
    ("nsrc-000011", "赤城神社", "page002-row001"),
    ("nsrc-000012", "赤城神社", "page002-row002"),
    ("nsrc-000013", "赤城神社", "page002-row003"),
    ("nsrc-000014", "赤城神社", "page002-row004"),
    ("nsrc-000015", "赤城神社", "page002-row005"),
)
H003_CATALOG_IMPORTED = ("nsrc-000011", "nsrc-000012", "nsrc-000013", "nsrc-000015")
H003_HOLD = "nsrc-000014"
# Catalog-only import: lifecycle と reason だけが IMPORTED 側へ進む。Knowledge は書かれていない。
NATIONWIDE_CATALOG_IMPORTED_LIFECYCLE = {
    "candidate_status": "IMPORTED",
    "status_reason_code": "PRODUCTION_IMPORT_COMPLETE",
    "official_source_status": "AVAILABLE",
    "knowledge_status": "UNREVIEWED",
    "build_batch": None,
}


def test_niigata_h003_catalog_cohort_is_imported_and_hold_stays_discovered():
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    h003 = [
        row
        for row in master["candidates"]
        if (row.get("admission_provenance") or {}).get("handoff_id") == H003_HANDOFF_ID
    ]
    assert [row["candidate_id"] for row in h003] == [m[0] for m in H003_MEMBERS]

    for candidate_id, name, position in H003_MEMBERS:
        row = rows[candidate_id]
        lifecycle = (
            NATIONWIDE_CATALOG_IMPORTED_LIFECYCLE
            if candidate_id in H003_CATALOG_IMPORTED
            else NATIONWIDE_DISCOVERED_LIFECYCLE
        )
        assert row == {
            "candidate_id": candidate_id,
            "candidate_name": name,
            "prefecture": "新潟県",
            "candidate_status": lifecycle["candidate_status"],
            "status_reason_code": lifecycle["status_reason_code"],
            "build_batch": None,
            "duplicate_status": "SAME_NAME_DIFFERENT_SHRINE",
            "wave_id": None,
            "identity_status": "CONFIRMED",
            "official_source_status": lifecycle["official_source_status"],
            "knowledge_status": lifecycle["knowledge_status"],
            "candidate_reason": NATIONWIDE_CANDIDATE_REASON,
            "admission_provenance": {
                "track": "nationwide_source_candidate",
                "prefecture": "新潟県",
                "source_batch_id": "NIIGATA-001",
                "handoff_id": "NIIGATA-001-H003",
                "source_position": position,
                "source_snapshot_sha256": (
                    "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380"
                ),
                "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
                "source_verified_at": "2026-10-08",
                "captured_at": "2026-10-08T14:27:00+09:00",
            },
        }, candidate_id
        assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys()), candidate_id
        assert "reading" not in row, candidate_id
        # Catalog は Recommendation / CORE_READY を主張しない。Product Surface field も持たない。
        assert row["candidate_status"] != "CORE_READY", candidate_id
        assert row["knowledge_status"] != "FACT_READY", candidate_id
        assert not {"product_surface", "catalog_status", "catalog_ready"} & row.keys(), candidate_id

    # nsrc-000014（G2 HOLD_POSITION_REVIEW）は Catalog import に含まれず G0 初期 state のまま。
    assert rows[H003_HOLD]["candidate_status"] == "DISCOVERED"
    assert rows[H003_HOLD]["status_reason_code"] == "REGISTRY_ADMISSION_COMPLETE"

    # H003 の IMPORTED は exact 4件、nsrc-000014 を含まない。
    h003_imported = [r["candidate_id"] for r in h003 if r["candidate_status"] == "IMPORTED"]
    assert h003_imported == list(H003_CATALOG_IMPORTED)
    assert H003_HOLD not in h003_imported

    # CATALOG_READY は lifecycle enum ではない（audit-level closure state）。
    assert "CATALOG_READY" not in {r["candidate_status"] for r in master["candidates"]}
    assert "CATALOG_READY" not in {r["status_reason_code"] for r in master["candidates"]}

    # H003 の Catalog import は H001 / H002 に連動しない。
    assert _handoff_violations(master, _handoff_spec(H001_HANDOFF_ID)) == []
    assert _handoff_violations(master, _handoff_spec(H002_HANDOFF_ID)) == []
    assert _handoff_violations(master, _handoff_spec(H003_HANDOFF_ID)) == []
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


# H003 の Catalog IMPORTED / HOLD 境界・regression・同名統合の mutation。
@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_set("nsrc-000011", "identity_status", "UNREVIEWED"), id="h003-identity-regression"),
        pytest.param(_set("nsrc-000012", "duplicate_status", "NEW"), id="h003-duplicate-new"),
        pytest.param(
            _set("nsrc-000013", "duplicate_status", "UNREVIEWED"),
            id="h003-duplicate-regression",
        ),
        pytest.param(_set("nsrc-000014", "duplicate_status", "SAME_SHRINE"), id="h003-duplicate-same-shrine"),
        # Catalog cohort（IMPORTED）: regression / premature CORE_READY / Knowledge 主張。
        pytest.param(_set("nsrc-000015", "candidate_status", "BUILD_READY"), id="h003-regressed-to-build-ready"),
        pytest.param(_set("nsrc-000011", "candidate_status", "DISCOVERED"), id="h003-regressed-to-discovered"),
        pytest.param(
            _set("nsrc-000012", "status_reason_code", "REGISTRY_ADMISSION_COMPLETE"),
            id="h003-imported-reason-mismatch",
        ),
        pytest.param(_set("nsrc-000013", "candidate_status", "CORE_READY"), id="h003-premature-core-ready"),
        pytest.param(
            _set("nsrc-000015", "status_reason_code", "CORE_READY_CONTRACT_PASS"),
            id="h003-premature-core-ready-reason",
        ),
        pytest.param(_set("nsrc-000011", "candidate_status", "CATALOG_READY"), id="h003-catalog-ready-enum"),
        pytest.param(
            _set("nsrc-000011", "official_source_status", "CONFIRMED"), id="h003-official-source-changed"
        ),
        pytest.param(_set("nsrc-000012", "knowledge_status", "FACT_READY"), id="h003-catalog-claims-fact-ready"),
        pytest.param(_set("nsrc-000013", "product_surface", "CATALOG_ONLY"), id="h003-product-surface-field"),
        # nsrc-000014（G2 HOLD_POSITION_REVIEW）は write cohort 外: lifecycle を進めない。
        pytest.param(_set("nsrc-000014", "candidate_status", "IMPORTED"), id="h003-hold-imported"),
        pytest.param(
            _set("nsrc-000014", "status_reason_code", "PRODUCTION_IMPORT_COMPLETE"),
            id="h003-hold-import-reason",
        ),
        pytest.param(_set("nsrc-000014", "candidate_status", "BUILD_READY"), id="h003-hold-build-ready"),
        pytest.param(_set("nsrc-000013", "build_batch", "NIIGATA-001-H003"), id="h003-build-batch-handoff"),
        pytest.param(_set("nsrc-000014", "wave_id", "W0"), id="h003-wave-id-assigned"),
        pytest.param(_set("nsrc-000015", "official_name", "赤城神社"), id="h003-official-name-hydrated"),
        pytest.param(
            _set("nsrc-000011", "official_address", "新潟県新潟市江南区二本木1丁目7番16号"),
            id="h003-official-address-hydrated",
        ),
        pytest.param(_set("nsrc-000012", "reading", "あかぎじんじゃ"), id="h003-reading-hydrated"),
        pytest.param(_set("nsrc-000013", "latitude", 37.8), id="h003-coordinate-hydrated"),
        pytest.param(_set("nsrc-000014", "shrine_id", 123), id="h003-shrine-id-hydrated"),
        pytest.param(_set("nsrc-000015", "goriyaku", "家内安全"), id="h003-goriyaku-hydrated"),
        pytest.param(
            _set_provenance("nsrc-000011", "source_position", "page002-row002"),
            id="h003-changed-provenance",
        ),
        pytest.param(
            _set_provenance("nsrc-000012", "handoff_id", "NIIGATA-001-H002"),
            id="h003-member-moved-to-h002",
        ),
        # 同名の赤城神社を1件に統合（重複排除）した状態。
        pytest.param(_h002_remove("nsrc-000013"), id="h003-akagi-deduplicated"),
        pytest.param(_set("nsrc-000014", "candidate_name", "赤城社"), id="h003-akagi-renamed"),
    ],
)
def test_niigata_h003_contract_rejects_mutations(mutate):
    master = _load_master()
    spec = _handoff_spec(H003_HANDOFF_ID)
    assert _handoff_violations(master, spec) == []
    assert _handoff_violations(_mutated(master, mutate), spec) != []


# --- NIIGATA-001-H004（G0 Admission only） -------------------------------------------------
#
# docs/audit/niigata-h004-g0-candidate-registry.md
# H004 は G0 Registry Admission だけ。G1（identity / duplicate）、G2 以降は未実施。
# 「赤坂」「赤崎」「赤澤」等の名前の類似から identity / duplicate を推論しない。
# 期待値は manifest から独立した literal を使う。

H004_MEMBERS = (
    ("nsrc-000016", "赤坂神社", "page002-row006"),
    ("nsrc-000017", "赤坂諏訪神社", "page002-row007"),
    ("nsrc-000018", "赤崎神社", "page002-row008"),
    ("nsrc-000019", "赤鏥神社", "page002-row009"),
    ("nsrc-000020", "赤澤神社", "page002-row010"),
)
H004_G0_LIFECYCLE = {
    "candidate_status": "DISCOVERED",
    "status_reason_code": "REGISTRY_ADMISSION_COMPLETE",
    "build_batch": None,
    "duplicate_status": "UNREVIEWED",
    "wave_id": None,
    "identity_status": "UNREVIEWED",
    "official_source_status": "AVAILABLE",
    "knowledge_status": "UNREVIEWED",
}


def test_niigata_h004_is_registered_at_g0_only():
    master = _load_master()
    rows = {row["candidate_id"]: row for row in master["candidates"]}
    h004 = [
        row
        for row in master["candidates"]
        if (row.get("admission_provenance") or {}).get("handoff_id") == H004_HANDOFF_ID
    ]
    assert [row["candidate_id"] for row in h004] == [m[0] for m in H004_MEMBERS]

    for candidate_id, name, position in H004_MEMBERS:
        row = rows[candidate_id]
        assert row == {
            "candidate_id": candidate_id,
            "candidate_name": name,
            "prefecture": "新潟県",
            **H004_G0_LIFECYCLE,
            "candidate_reason": NATIONWIDE_CANDIDATE_REASON,
            "admission_provenance": {
                "track": "nationwide_source_candidate",
                "prefecture": "新潟県",
                "source_batch_id": "NIIGATA-001",
                "handoff_id": "NIIGATA-001-H004",
                "source_position": position,
                "source_snapshot_sha256": (
                    "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380"
                ),
                "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
                "source_verified_at": "2026-10-08",
                "captured_at": "2026-10-08T14:27:00+09:00",
            },
        }, candidate_id
        # G1 の結論を持たない（名前類似から identity / duplicate を推論しない）。
        assert row["identity_status"] != "CONFIRMED", candidate_id
        assert row["duplicate_status"] == "UNREVIEWED", candidate_id
        # G0 を超える lifecycle / build_batch / Product Surface を持たない。
        assert row["candidate_status"] not in {"BUILD_READY", "IMPORTED", "CORE_READY"}, (
            candidate_id
        )
        assert row["build_batch"] is None, candidate_id
        assert not {"product_surface", "catalog_status", "catalog_ready"} & row.keys(), candidate_id
        assert not (HANDOFF_FORBIDDEN_HYDRATION_FIELDS & row.keys()), candidate_id
        assert "reading" not in row, candidate_id

    # H004 は frozen Ready Set の §NIIGATA-001-H004 と exact に一致（name / position）。
    text = FROZEN_READY_SET_PATH.read_text(encoding="utf-8")
    section = text[text.index("### NIIGATA-001-H004") : text.index("### NIIGATA-001-H005")]
    frozen = re.findall(
        r"\| (page\d{3}-row\d{3}) \| ([^|]+?) \| [^|]+? \| RUNNER_READY \|", section
    )
    assert frozen == [(position, name) for _, name, position in H004_MEMBERS]

    # H004 の G0 登録は H001 / H002 / H003 に連動しない。
    for handoff_id in (H001_HANDOFF_ID, H002_HANDOFF_ID, H003_HANDOFF_ID, H004_HANDOFF_ID):
        assert _handoff_violations(master, _handoff_spec(handoff_id)) == [], handoff_id
    h003_states = {
        r["candidate_id"]: (r["candidate_status"], r["status_reason_code"])
        for r in master["candidates"]
        if (r.get("admission_provenance") or {}).get("handoff_id") == H003_HANDOFF_ID
    }
    assert h003_states == {
        "nsrc-000011": ("IMPORTED", "PRODUCTION_IMPORT_COMPLETE"),
        "nsrc-000012": ("IMPORTED", "PRODUCTION_IMPORT_COMPLETE"),
        "nsrc-000013": ("IMPORTED", "PRODUCTION_IMPORT_COMPLETE"),
        "nsrc-000014": ("DISCOVERED", "REGISTRY_ADMISSION_COMPLETE"),
        "nsrc-000015": ("IMPORTED", "PRODUCTION_IMPORT_COMPLETE"),
    }
    wave0 = _wave0_candidates(master)
    assert len(wave0) == EXPECTED_WAVE0_TOTAL
    assert Counter(r["candidate_status"] for r in wave0) == EXPECTED_STATUS_COUNTS


# H004（G0 only）の premature G1+ / hydration / 名前類似による統合の mutation。
@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            _set("nsrc-000016", "identity_status", "CONFIRMED"), id="h004-premature-identity"
        ),
        pytest.param(
            _set("nsrc-000017", "duplicate_status", "NEW"), id="h004-premature-duplicate-new"
        ),
        pytest.param(
            _set("nsrc-000018", "duplicate_status", "SAME_NAME_DIFFERENT_SHRINE"),
            id="h004-premature-same-name-different-shrine",
        ),
        pytest.param(_set("nsrc-000019", "duplicate_status", "ALIAS"), id="h004-premature-alias"),
        pytest.param(
            _set("nsrc-000020", "duplicate_status", "DUPLICATE"), id="h004-premature-duplicate"
        ),
        pytest.param(_set("nsrc-000016", "candidate_status", "BUILD_READY"), id="h004-build-ready"),
        pytest.param(_set("nsrc-000017", "candidate_status", "IMPORTED"), id="h004-imported"),
        pytest.param(_set("nsrc-000018", "candidate_status", "CORE_READY"), id="h004-core-ready"),
        pytest.param(
            _set("nsrc-000019", "status_reason_code", "BUILD_READINESS_CONFIRMED"),
            id="h004-reason-beyond-g0",
        ),
        pytest.param(
            _set("nsrc-000020", "official_source_status", "CONFIRMED"),
            id="h004-official-source-beyond-g0",
        ),
        pytest.param(
            _set("nsrc-000016", "knowledge_status", "FACT_READY"), id="h004-knowledge-beyond-g0"
        ),
        pytest.param(
            _set("nsrc-000017", "build_batch", "NIIGATA-001-H004"), id="h004-build-batch-handoff"
        ),
        pytest.param(
            _set("nsrc-000018", "build_batch", "NIIGATA-001"), id="h004-build-batch-source-batch"
        ),
        pytest.param(_set("nsrc-000019", "wave_id", "W0"), id="h004-wave-id-assigned"),
        pytest.param(
            _set("nsrc-000020", "product_surface", "CATALOG_ONLY"), id="h004-product-surface"
        ),
        pytest.param(
            _set("nsrc-000016", "official_name", "赤坂神社"), id="h004-official-name-hydrated"
        ),
        pytest.param(
            _set("nsrc-000017", "official_address", "新潟県燕市下粟生津515番地"),
            id="h004-official-address-hydrated",
        ),
        pytest.param(
            _set("nsrc-000018", "reading", "あかさきじんじゃ"), id="h004-reading-hydrated"
        ),
        pytest.param(_set("nsrc-000019", "latitude", 37.7), id="h004-coordinate-hydrated"),
        pytest.param(_set("nsrc-000020", "shrine_id", 123), id="h004-shrine-id-hydrated"),
        pytest.param(_set("nsrc-000016", "goriyaku", "家内安全"), id="h004-goriyaku-hydrated"),
        pytest.param(
            _set_provenance("nsrc-000017", "source_position", "page002-row006"),
            id="h004-changed-provenance",
        ),
        pytest.param(
            _set_provenance("nsrc-000018", "source_snapshot_sha256", "0" * 64),
            id="h004-changed-snapshot",
        ),
        pytest.param(
            _set_provenance("nsrc-000019", "handoff_id", "NIIGATA-001-H003"),
            id="h004-member-moved-to-h003",
        ),
        # 名前の類似（赤坂神社 / 赤坂諏訪神社）から1件に統合した状態。
        pytest.param(_h002_remove("nsrc-000017"), id="h004-akasaka-merged"),
        pytest.param(_set("nsrc-000020", "candidate_name", "赤沢神社"), id="h004-name-normalized"),
    ],
)
def test_niigata_h004_contract_rejects_mutations(mutate):
    master = _load_master()
    spec = _handoff_spec(H004_HANDOFF_ID)
    assert _handoff_violations(master, spec) == []
    assert _handoff_violations(_mutated(master, mutate), spec) != []
