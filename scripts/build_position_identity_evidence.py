#!/usr/bin/env python
"""Real-data Identity Evidence Supply（Pilot 1 / read-only / deterministic）。

repository が裏付けている既存入力から **実データの identity evidence** を導出し、

```text
candidate_id  ->  PositionIdentityIntegrationResult
```

を作って Position Audit の `identity_integrations_by_candidate` に供給する。

## 位置づけ

```text
Candidate Master / Seed / Production snapshot / Spreadsheet snapshot /
Resolution / Canonical Production Candidate Linkage
→ 本 module（supply layer）
→ B03 assess_identity_evidence()
→ B04 integrate_position_identity()
→ Position Audit build_inputs()
```

非 exact join（`MISSING_PRODUCTION`）では canonical linkage が
**比較対象の Production 行だけ**を選ぶ。linkage 自体は identity の
証明ではなく、evidence も作らない。判定は既存の B03 / B04 がそのまま
行う。

下流の B02 / B03 / B04 の規則は **再実装しない**。既存 API をそのまま呼ぶ。
住所比較はすべて B02 の `compare_addresses()` を通す（legacy Position Audit
の `normalize_address()` は呼ばない）。住所は B02 へ入るまで raw のまま保つ。

## Pilot 1 の問い

```text
repository が裏付けているデータから、supply layer は正しい B03 / B04
evidence object を決定的に構成できるか
```

非 exact identity の救済を示すことは目的ではない。canonical Position
decision も変更しない。

## 行わないこと

* Production / Seed / Candidate Master / Spreadsheet への write
* live web discovery / network fetch
* Production 全体の fuzzy 候補探索
* 欠損 field の推測補完
* alias registry の新設

入力が欠けている・確定できない場合は fail closed する。

## Pilot 1 の構造的限界

```text
Pilot 1 は非 exact join の B04 救済経路を活性化できない。
```

決定的な Production candidate linkage が無いかぎり、非 exact identity は
`NOT_EVALUATED` のままであり、B04 integration も供給されない。
`MISSING_PRODUCTION` が正当に B03 / B04 evidence を受け取れるようになる
には、canonical な Production candidate linkage が先に必要である。

`MISSING_PRODUCTION` の結果を `INSUFFICIENT` と記述しない。
`INSUFFICIENT` は「比較対象が存在し B03 が実際に評価した上で必須
evidence が足りなかった」状態にだけ使う。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_sibling(module_name: str) -> Any:
    """`scripts/` は package ではないため canonical loader pattern を使う。

    同名 module が既に canonical path で読み込まれていれば再利用する。
    別名での二重読み込みを避けることで、B04 の型による信頼境界
    （`isinstance`）が成立し続ける。
    """
    path = _SCRIPTS_DIR / f"{module_name}.py"
    cached = sys.modules.get(module_name)
    if cached is not None and getattr(cached, "__file__", None) == str(path):
        return cached
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 依存方向:
#
#     supply layer -> B03 shrine_identity_evidence
#                  -> B04 position_identity_integration
#                  -> Position Audit（loader / exact join の再利用）
#                  -> canonical linkage loader
#
# B02 は **直接読まない**。住所 API は B03 が再公開しているものを使う
# （B02 の直接 consumer は B03 のままに保つ）。
#
# canonical linkage の parse / 検証 / active 一意性 / 逆方向曖昧さ /
# CONFIRMED・REVOKED 判定 / evidence 検証は **すべて loader の責務**で
# ある。本 module は検証済みの結果を消費するだけで、再実装しない。
identity_evidence = _load_sibling("shrine_identity_evidence")
identity_integration = _load_sibling("position_identity_integration")
position_audit = _load_sibling("audit_shrine_positions_v2")
canonical_linkage = _load_sibling("production_candidate_linkage")

# B02 canonical address API（B03 経由の再公開）。
compare_addresses = identity_evidence.compare_addresses


# ---------------------------------------------------------------------------
# activation status（**supply report 専用**）
# ---------------------------------------------------------------------------
# canonical な Position status ではない。`AUTO_PASS` / `REVIEW` / `HOLD` や
# `PASS` / `HOLD_POSITION_REVIEW` を置き換えるものでは一切ない。
ACTIVATED = "ACTIVATED"
NOT_ACTIVATED = "NOT_ACTIVATED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
INPUT_UNAVAILABLE = "INPUT_UNAVAILABLE"

ACTIVATION_STATUSES = frozenset(
    {ACTIVATED, NOT_ACTIVATED, REVIEW_REQUIRED, INPUT_UNAVAILABLE}
)

# Production 比較対象がどこから来たかを表す **supply report 専用**の
# provenance。
#
# ```text
# EXACT_JOIN         raw exact Seed ↔ Production join が返した行
# CANONICAL_LINKAGE  canonical linkage が指した production_shrine_id の行
# NONE               比較対象なし
# ```
#
# これは **report metadata** であり、B03 の evidence でも Position Audit の
# status でもない。B03 の採点にも B04 の identity 規則にも影響しない。
TARGET_SOURCE_EXACT_JOIN = "EXACT_JOIN"
TARGET_SOURCE_CANONICAL_LINKAGE = "CANONICAL_LINKAGE"
TARGET_SOURCE_NONE = "NONE"

PRODUCTION_TARGET_SOURCES = frozenset(
    {
        TARGET_SOURCE_EXACT_JOIN,
        TARGET_SOURCE_CANONICAL_LINKAGE,
        TARGET_SOURCE_NONE,
    }
)

# Seed ↔ Production join まで到達しなかったことを表す **supply report 専用**
# の値。Position Audit の join status 語彙には属さない。
# `JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE` は「snapshot が無い」ことを表す
# 別の事実であり、入力 metadata 不足をそれで騙らない。
JOIN_NOT_EVALUATED = "JOIN_NOT_EVALUATED"

# evidence 軸が **評価されなかった** ことを表す supply report 専用の値。
#
# ```text
# NOT_EVALUATED = 決定的な Production 比較対象がそもそも存在しない
# INSUFFICIENT  = 比較対象は存在し B03 は実際に評価された。その上で
#                 必須 evidence が足りなかった
# ```
#
# この2つを混ぜない。比較対象が無いことを `*_UNSUPPORTED` や
# `INSUFFICIENT` に変換すると、**未評価を評価済みに格上げ**してしまう。
# B03 / B04 のどの status 語彙にも属さない（test が固定する）。
EVIDENCE_NOT_EVALUATED = "NOT_EVALUATED"

# ---------------------------------------------------------------------------
# supply review reasons
# ---------------------------------------------------------------------------
REASON_CANDIDATE_MASTER_ROW_MISSING = "CANDIDATE_MASTER_ROW_MISSING"
REASON_CANDIDATE_IDENTITY_NOT_CONFIRMED = "CANDIDATE_IDENTITY_NOT_CONFIRMED"
REASON_OFFICIAL_SOURCE_NOT_CONFIRMED = "OFFICIAL_SOURCE_NOT_CONFIRMED"
REASON_OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE = (
    "OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE"
)
REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED = "OFFICIAL_IDENTITY_NOT_CORROBORATED"
REASON_SEED_ROW_MISSING = "SEED_ROW_MISSING"
REASON_PRODUCTION_SNAPSHOT_UNAVAILABLE = "PRODUCTION_SNAPSHOT_UNAVAILABLE"
REASON_PRODUCTION_CANDIDATE_UNRESOLVED = "PRODUCTION_CANDIDATE_UNRESOLVED"
REASON_PRODUCTION_IDENTITY_AMBIGUOUS = "PRODUCTION_IDENTITY_AMBIGUOUS"
# canonical linkage 活性化の失敗理由（supply layer 語彙）。
# loader の issue code を複製しない。要約だけを持つ。
REASON_LINKAGE_ARTIFACT_UNAVAILABLE = "LINKAGE_ARTIFACT_UNAVAILABLE"
REASON_LINKAGE_ARTIFACT_INVALID = "LINKAGE_ARTIFACT_INVALID"
REASON_LINKAGE_NOT_AVAILABLE_FOR_CANDIDATE = (
    "LINKAGE_NOT_AVAILABLE_FOR_CANDIDATE"
)
REASON_LINKAGE_TARGET_ROW_ABSENT = "LINKAGE_TARGET_ROW_ABSENT"
REASON_LINKAGE_TARGET_ROW_DUPLICATED = "LINKAGE_TARGET_ROW_DUPLICATED"
REASON_SPREADSHEET_SNAPSHOT_UNAVAILABLE = "SPREADSHEET_SNAPSHOT_UNAVAILABLE"
REASON_NAME_NOT_RAW_EQUAL = "NAME_NOT_RAW_EQUAL"
REASON_PLACE_ID_UNAVAILABLE = "PLACE_ID_UNAVAILABLE"
REASON_RESOLUTION_PRODUCTION_LINK_UNPROVEN = (
    "RESOLUTION_PRODUCTION_LINK_UNPROVEN"
)

REVIEW_REASON_ORDER = (
    REASON_CANDIDATE_MASTER_ROW_MISSING,
    REASON_CANDIDATE_IDENTITY_NOT_CONFIRMED,
    REASON_OFFICIAL_SOURCE_NOT_CONFIRMED,
    REASON_OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE,
    REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED,
    REASON_SEED_ROW_MISSING,
    REASON_PRODUCTION_SNAPSHOT_UNAVAILABLE,
    REASON_PRODUCTION_CANDIDATE_UNRESOLVED,
    REASON_PRODUCTION_IDENTITY_AMBIGUOUS,
    REASON_LINKAGE_ARTIFACT_UNAVAILABLE,
    REASON_LINKAGE_ARTIFACT_INVALID,
    REASON_LINKAGE_NOT_AVAILABLE_FOR_CANDIDATE,
    REASON_LINKAGE_TARGET_ROW_ABSENT,
    REASON_LINKAGE_TARGET_ROW_DUPLICATED,
    REASON_SPREADSHEET_SNAPSHOT_UNAVAILABLE,
    REASON_NAME_NOT_RAW_EQUAL,
    REASON_PLACE_ID_UNAVAILABLE,
    REASON_RESOLUTION_PRODUCTION_LINK_UNPROVEN,
)
REVIEW_REASONS = frozenset(REVIEW_REASON_ORDER)
_REASON_RANK = {reason: index for index, reason in enumerate(REVIEW_REASON_ORDER)}

# Candidate Master が identity evidence として使える最低条件。
REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id",
    "official_name",
    "official_address",
    "official_source_type",
    "official_source_url",
    "verified_at",
)

# Pilot 1 の対象（既存 W0-DB02 set）。
W0_DB02_CANDIDATE_IDS = (
    "wave0-007",
    "wave0-008",
    "wave0-009",
    "wave0-010",
    "wave0-011",
)

# B02 の住所一致のうち「同一住所」として使えるもの。
_USABLE_ADDRESS_MATCHES = frozenset(
    {
        identity_evidence.ADDRESS_EXACT_MATCH,
        identity_evidence.ADDRESS_NORMALIZED_MATCH,
    }
)


def _order_reasons(reasons: Iterable[str]) -> tuple[str, ...]:
    unique = {reason for reason in reasons if reason in _REASON_RANK}
    return tuple(sorted(unique, key=lambda reason: _REASON_RANK[reason]))


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(frozen=True)
class CandidateIdentitySupply:
    """1候補分の supply 結果（決定的・serialize 可能）。"""

    candidate_id: str
    input_availability: tuple[str, ...]

    name_identity_status: str
    address_identity_status: str
    official_source_entity_status: str
    place_id_status: str
    existing_resolution_status: str

    identity_evidence_status: str
    join_status: str
    identity_status: str

    activation_status: str
    # Production 比較対象の出どころ（report metadata）。
    production_target_source: str = TARGET_SOURCE_NONE
    duplicate_production_ids: tuple[int, ...] = ()
    review_reasons: tuple[str, ...] = ()

    # Position Audit へ渡す本物の B04 結果。
    #
    # **決定的な Production 比較対象が解決できた場合にのみ存在する。**
    # 未評価（比較対象なし）のときは `None` のままであり、
    # `identity_integrations_by_candidate()` にも載らない。
    integration: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "input_availability": list(self.input_availability),
            "name_identity_status": self.name_identity_status,
            "address_identity_status": self.address_identity_status,
            "official_source_entity_status": self.official_source_entity_status,
            "place_id_status": self.place_id_status,
            "existing_resolution_status": self.existing_resolution_status,
            "identity_evidence_status": self.identity_evidence_status,
            "join_status": self.join_status,
            "identity_status": self.identity_status,
            "activation_status": self.activation_status,
            "production_target_source": self.production_target_source,
            "duplicate_production_ids": list(self.duplicate_production_ids),
            "review_reasons": list(self.review_reasons),
        }


# ---------------------------------------------------------------------------
# evidence 導出（純関数）
# ---------------------------------------------------------------------------


def derive_name_identity_status(
    official_name: str | None, production_name: str | None
) -> str:
    """name identity を導出する（fuzzy 一致は使わない）。

    Pilot 1 では **raw 一致だけ**を同一の証明として扱う。

    ```text
    raw 一致            -> NAME_EXACT_MATCH
    両方あるが不一致     -> NAME_AMBIGUOUS
    どちらか欠落        -> NAME_UNSUPPORTED
    ```

    `NAME_NORMALIZED_MATCH` は **出さない**。住所における B02 に相当する
    canonical な名称正規化契約が repository に存在しないため、正規化一致を
    主張する根拠が無い。

    `NAME_DIFFERENT` も出さない。これは B03 の explicit trusted conflict で
    あり、canonical な名称正規化契約が無い状態では「別 entity」と
    「表記差」を区別できないためである（fail safe）。

    `NAME_ALIAS_CONFIRMED` は明示的な alias evidence を要求する。Pilot 1 は
    alias registry を新設しないため出さない。
    """
    left = _text(official_name)
    right = _text(production_name)
    if left is None or right is None:
        return identity_evidence.NAME_UNSUPPORTED
    if left == right:
        return identity_evidence.NAME_EXACT_MATCH
    return identity_evidence.NAME_AMBIGUOUS


def derive_place_id_status(
    production_place_ref_id: str | None, spreadsheet_google_place_id: str | None
) -> str:
    """明示的な provider 識別子だけを比較する。

    座標・名称・URL からは導出しない。
    """
    left = _text(production_place_ref_id)
    right = _text(spreadsheet_google_place_id)
    if left is None or right is None:
        return identity_evidence.PLACE_ID_UNAVAILABLE
    if left == right:
        return identity_evidence.PLACE_ID_MATCH
    return identity_evidence.PLACE_ID_DIFFERENT


def derive_official_source_entity_status(
    candidate: dict[str, Any],
    production_name: str | None,
    production_address: str | None,
    reasons: list[str],
) -> str:
    """official source evidence を導出する。

    `official_source_status = CONFIRMED` を `OFFICIAL_SOURCE_SAME` へ
    **直結しない**。confirmed な source record が証明するのは
    「凍結された official identity packet が存在する」ことだけである。

    `OFFICIAL_SOURCE_SAME` は次を **すべて** 満たすときにだけ出す。

    ```text
    identity_status = CONFIRMED
    official_source_status = CONFIRMED
    provenance 完備（official_source_type / official_source_url / verified_at）
    official_name   が評価対象の identity と一致（raw）
    official_address が評価対象の identity と B02 上で同一住所
    ```

    corroboration が成立しなければ `OFFICIAL_SOURCE_UNAVAILABLE` に倒す。
    `OFFICIAL_SOURCE_DIFFERENT`（trusted conflict）は Pilot 1 では出さない。
    別 entity であることまでは証明できないためである。
    """
    if (candidate.get("identity_status") or "").strip().upper() != "CONFIRMED":
        reasons.append(REASON_CANDIDATE_IDENTITY_NOT_CONFIRMED)
        return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE
    if (
        candidate.get("official_source_status") or ""
    ).strip().upper() != "CONFIRMED":
        reasons.append(REASON_OFFICIAL_SOURCE_NOT_CONFIRMED)
        return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE

    provenance = (
        _text(candidate.get("official_source_type")),
        _text(candidate.get("official_source_url")),
        _text(candidate.get("verified_at")),
    )
    if not all(provenance):
        reasons.append(REASON_OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE)
        return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE

    official_name = _text(candidate.get("official_name"))
    official_address = _text(candidate.get("official_address"))
    if official_name is None or official_address is None:
        reasons.append(REASON_OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE)
        return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE

    # 評価対象の identity と突き合わせる。
    if production_name is None or production_address is None:
        reasons.append(REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED)
        return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE

    if official_name != _text(production_name):
        reasons.append(REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED)
        return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE

    # 住所 corroboration は B02 を通す（raw のまま渡す）。
    comparison = compare_addresses(official_address, production_address)
    if comparison.address_identity_status in _USABLE_ADDRESS_MATCHES:
        return identity_evidence.OFFICIAL_SOURCE_SAME
    if comparison.address_identity_status == identity_evidence.ADDRESS_AMBIGUOUS:
        reasons.append(REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED)
        return identity_evidence.OFFICIAL_SOURCE_AMBIGUOUS
    reasons.append(REASON_OFFICIAL_IDENTITY_NOT_CORROBORATED)
    return identity_evidence.OFFICIAL_SOURCE_UNAVAILABLE


def derive_existing_resolution_status(
    resolution: Any, reasons: list[str]
) -> str:
    """existing resolution evidence を導出する。

    **Pilot 1 では常に `RESOLUTION_UNAVAILABLE` になる。**

    既存の repository loader（`load_resolution_records()` →
    `ExistingResolution`）は Position Resolution Record の
    **Production 側識別子を公開していない**。record は `candidate_id` で
    候補に紐づくが、B03 の `existing_resolution_status` が問うのは
    「この2つが同一 entity か」であり、Production 行との結び付きが
    必要になる。

    その linkage を既存 loader から決定的に証明できないため、
    `RESOLUTION_SAME` を主張しない（PASS な Position Resolution が
    任意の entity identity を証明するとは仮定しない）。

    loader を拡張すれば Production 側識別子を読めるようになるが、それは
    Position Audit の `ExistingResolution` 契約の変更であり Pilot 1 の
    scope 外である。
    """
    if resolution is None:
        return identity_evidence.RESOLUTION_UNAVAILABLE
    reasons.append(REASON_RESOLUTION_PRODUCTION_LINK_UNPROVEN)
    return identity_evidence.RESOLUTION_UNAVAILABLE


def _resolve_linkage_target(
    *,
    candidate_id: str,
    linkage_artifact: Any,
    production_rows: Sequence[dict[str, Any]],
    reasons: list[str],
    availability: list[str],
) -> dict[str, Any] | None:
    """canonical linkage から Production 比較対象を1行だけ解決する。

    ## これは identity の証明ではない

    ```text
    canonical linkage が意味するのは
      「比較してよい Production 行はこれだ」
    だけである。

    同一神社であること / SAME_SUPPORTED / IDENTITY_EXACT /
    canonical PASS のいずれも意味しない。
    ```

    したがって本関数は evidence を一切作らない。行を1つ返すだけで、
    判定は既存の B03 / B04 経路がそのまま行う。

    ## 解決は primary key の exact 一致のみ

    ```text
    row["id"] == active_linkage.production_shrine_id
    ```

    名称 / 住所 / 正規化住所 / fuzzy / 座標近接 / place id / 近傍 id /
    Spreadsheet join のいずれも **使わない**。linkage が既に比較対象を
    選んでいるので、supply layer が代替を探してはならない。

    解決できないときは `None` を返し、呼び出し側は未評価のままにする。
    """
    # 型による信頼境界。検証済みでない object を linkage として扱わない。
    if not isinstance(linkage_artifact, canonical_linkage.LinkageArtifact):
        reasons.append(REASON_LINKAGE_ARTIFACT_UNAVAILABLE)
        return None
    if linkage_artifact.artifact_state == canonical_linkage.ARTIFACT_NOT_PRESENT:
        # artifact 不在は正常な状態。identity の問題の証拠ではない。
        reasons.append(REASON_LINKAGE_ARTIFACT_UNAVAILABLE)
        return None
    if not linkage_artifact.is_valid:
        reasons.append(REASON_LINKAGE_ARTIFACT_INVALID)
        return None
    availability.append("linkage_artifact")

    # active 一意性・REVOKED・逆方向曖昧さの判定は loader の責務である。
    # ここで raw row を読み直して推測しない。
    active = linkage_artifact.active_linkage_for(candidate_id)
    if active is None:
        reasons.append(REASON_LINKAGE_NOT_AVAILABLE_FOR_CANDIDATE)
        return None
    availability.append("linkage_active")

    target_id = active.production_shrine_id
    matches = [
        row
        for row in production_rows
        if not isinstance(row.get("id"), bool) and row.get("id") == target_id
    ]
    if not matches:
        # linked 行が現況 snapshot に無い。代替行を探さない。
        reasons.append(REASON_LINKAGE_TARGET_ROW_ABSENT)
        return None
    if len(matches) > 1:
        # 供給された snapshot が壊れている。先頭を黙って採らない。
        reasons.append(REASON_LINKAGE_TARGET_ROW_DUPLICATED)
        return None
    availability.append("linkage_target_row")
    return matches[0]


def _activation_status(integration: Any, evidence_status: str | None) -> str:
    """supply report 専用の activation status を決める。

    `integration is None` は「決定的な Production 比較対象が無く、
    identity は **未評価** のまま」という意味であり、`INPUT_UNAVAILABLE`
    になる。`NOT_ACTIVATED` / `REVIEW_REQUIRED` は「評価された上で
    activate しない」状態であり、Pilot 1 では到達しない。
    非 exact join に対する B04 の救済経路は、明示的な Production
    candidate linkage が供給されて初めて成立するためである。
    """
    if integration is None:
        return INPUT_UNAVAILABLE
    status = integration.identity_status
    if status in (
        identity_integration.IDENTITY_EXACT,
        identity_integration.IDENTITY_SAME_SUPPORTED,
    ):
        return ACTIVATED
    if status in (
        identity_integration.IDENTITY_REVIEW_REQUIRED,
        identity_integration.IDENTITY_CONFLICT,
    ):
        return REVIEW_REQUIRED
    return NOT_ACTIVATED


def build_candidate_identity_supply(
    *,
    candidate: dict[str, Any] | None,
    candidate_id: str,
    seed_rows: Sequence[dict[str, Any]],
    production_rows: Sequence[dict[str, Any]] | None,
    spreadsheet_rows: Sequence[Any] | None,
    resolution: Any = None,
    linkage_artifact: Any = None,
) -> CandidateIdentitySupply:
    """1候補分の identity evidence を決定的に構成する（純関数）。

    候補探索は行わない。Production 行は次の2経路でだけ解決する。

    ```text
    EXACT_JOIN         raw exact Seed ↔ Production join
    CANONICAL_LINKAGE  canonical linkage が指した production_shrine_id
    ```

    ## 比較対象の有無で分岐する

    ```text
    MATCH_EXACT                    -> Production 行あり（従来どおり）
                                   -> B03 assessment
                                   -> B04 integration
                                   -> Position Audit へ供給しうる

    MISSING_PRODUCTION             -> canonical linkage を引く
                                      解決できれば B03 / B04 へ
                                      解決できなければ NOT_EVALUATED

    DUPLICATE_MATCH                -> 従来どおり（linkage で救済しない）
    PRODUCTION_SNAPSHOT_UNAVAILABLE-> 入力なし
    MISSING_SEED                   -> 入力なし
                                   -> B03 を呼ばない
                                   -> B04 integration を作らない
                                   -> identity_status = NOT_EVALUATED
    ```

    比較対象が無いまま B03 を呼ぶと `INSUFFICIENT`（評価済みだが evidence
    不足）に化ける。**未評価を評価済みへ格上げしない**のがこの層の責務で
    ある。linkage 解決の失敗もすべて `NOT_EVALUATED` に留める。

    `linkage_artifact` は **検証済みの** loader 結果を受け取る。raw JSON を
    受け取らないし、候補ごとに artifact を読み直しもしない。
    """
    reasons: list[str] = []
    availability: list[str] = []

    def _not_evaluated(
        *,
        join_status: str = JOIN_NOT_EVALUATED,
        duplicate_production_ids: tuple[int, ...] = (),
    ) -> CandidateIdentitySupply:
        """**未評価**の supply 結果を返す（B03 も B04 も呼ばない）。

        決定的な Production 比較対象が存在しない状態である。B03 は
        「2つの identity を比較する」層であり、比較対象が無いときに
        呼べば `NAME_UNSUPPORTED` + `ADDRESS_UNSUPPORTED` から
        `INSUFFICIENT` が出てしまう。それは「評価したが evidence が
        足りなかった」という **別の状態**であり、未評価をそこへ格上げ
        しない。

        B04 integration も作らない。作れば Position Audit は
        `NOT_EVALUATED` ではなく評価済み identity を受け取ることになる。
        """
        return CandidateIdentitySupply(
            candidate_id=candidate_id,
            input_availability=tuple(availability),
            name_identity_status=EVIDENCE_NOT_EVALUATED,
            address_identity_status=EVIDENCE_NOT_EVALUATED,
            official_source_entity_status=EVIDENCE_NOT_EVALUATED,
            place_id_status=EVIDENCE_NOT_EVALUATED,
            existing_resolution_status=EVIDENCE_NOT_EVALUATED,
            identity_evidence_status=EVIDENCE_NOT_EVALUATED,
            join_status=join_status,
            identity_status=identity_integration.IDENTITY_NOT_EVALUATED,
            activation_status=INPUT_UNAVAILABLE,
            duplicate_production_ids=duplicate_production_ids,
            review_reasons=_order_reasons(reasons),
            integration=None,
        )

    # --- Candidate Master ---------------------------------------------------
    if candidate is None:
        reasons.append(REASON_CANDIDATE_MASTER_ROW_MISSING)
        return _not_evaluated()
    availability.append("candidate_master")

    missing = [
        field for field in REQUIRED_CANDIDATE_FIELDS if not _text(candidate.get(field))
    ]
    if missing:
        reasons.append(REASON_OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE)
        return _not_evaluated()

    official_name = _text(candidate["official_name"])
    official_address = _text(candidate["official_address"])

    # --- Seed（exact identity で引く。推測しない）---------------------------
    seed_index = {
        (row.get("name_jp"), row.get("address")): row for row in seed_rows
    }
    seed_row = seed_index.get((official_name, official_address))
    if seed_row is None:
        reasons.append(REASON_SEED_ROW_MISSING)
        return _not_evaluated(join_status=position_audit.JOIN_MISSING_SEED)
    availability.append("seed")

    # --- Production（既存 exact join のみ。候補探索はしない）----------------
    if production_rows is None:
        reasons.append(REASON_PRODUCTION_SNAPSHOT_UNAVAILABLE)
        return _not_evaluated(
            join_status=position_audit.JOIN_PRODUCTION_SNAPSHOT_UNAVAILABLE
        )
    availability.append("production_snapshot")

    join_status, production_row, duplicates = position_audit.join_seed_to_production(
        seed_row, production_rows
    )
    if production_row is None:
        # 比較対象の Production identity が解決できていない。
        #
        # ```text
        # MISSING_PRODUCTION  -> 候補が無い。fuzzy 探索も自動採用もしない
        # DUPLICATE_MATCH     -> 候補が複数。どれか1行を選ばない
        # ```
        #
        # どちらも「個別の Production identity が確定していない」状態で
        # あり、任意の行に対して identity assessment を作らない。B03 も
        # B04 も呼ばずに未評価のまま返す。Position Audit は従来どおり
        # `RC_MISSING_PRODUCTION` / `RC_DUPLICATE_PRODUCTION_IDENTITY` で
        # HOLD する（B04 導入前の挙動を保つ）。
        #
        # 将来、明示的で信頼できる Production candidate linkage
        # （例: canonical な resolution production_shrine_id）が供給
        # されれば、その候補に対して B02 -> B03 -> B04 -> REVIEW の
        # 経路が成立しうる。Pilot 1 はその linkage 源を持たない。
        if join_status == position_audit.JOIN_DUPLICATE_MATCH:
            # MS-FOLLOWUP-05 は未決。linkage で duplicate を救済しない。
            reasons.append(REASON_PRODUCTION_IDENTITY_AMBIGUOUS)
            return _not_evaluated(
                join_status=join_status,
                duplicate_production_ids=tuple(duplicates),
            )

        # MISSING_PRODUCTION のみ canonical linkage を引く。
        reasons.append(REASON_PRODUCTION_CANDIDATE_UNRESOLVED)
        production_row = _resolve_linkage_target(
            candidate_id=candidate_id,
            linkage_artifact=linkage_artifact,
            production_rows=production_rows,
            reasons=reasons,
            availability=availability,
        )
        if production_row is None:
            return _not_evaluated(
                join_status=join_status,
                duplicate_production_ids=tuple(duplicates),
            )
        # raw join の結果は書き換えない。MISSING_PRODUCTION のままにする。
        # canonical linkage は **比較対象の別経路**であって、exact join の
        # 成立ではない。この区別は観測可能なまま保つ。
        target_source = TARGET_SOURCE_CANONICAL_LINKAGE
        availability.append("production_row")
    else:
        target_source = TARGET_SOURCE_EXACT_JOIN
        availability.append("production_row")

    # --- Spreadsheet（任意）-------------------------------------------------
    sheet_row = None
    if spreadsheet_rows is None:
        reasons.append(REASON_SPREADSHEET_SNAPSHOT_UNAVAILABLE)
    else:
        availability.append("spreadsheet_snapshot")
        # Spreadsheet の row id は Production id と等しいと仮定しない。
        # verified identity（official_name + official_address）でのみ引く。
        for row in spreadsheet_rows:
            if (
                _text(getattr(row, "official_name", None)) == official_name
                and _text(getattr(row, "official_address", None)) == official_address
            ):
                sheet_row = row
                break
        if sheet_row is not None:
            availability.append("spreadsheet_row")

    # ここから先は「決定的な Production 比較対象が存在する」状態である。
    production_name = _text(production_row.get("name_jp"))
    production_address = _text(production_row.get("address"))

    # --- evidence 導出 ------------------------------------------------------
    name_status = derive_name_identity_status(official_name, production_name)
    if name_status == identity_evidence.NAME_AMBIGUOUS:
        reasons.append(REASON_NAME_NOT_RAW_EQUAL)

    address_comparison = None
    if production_address is not None:
        # raw のまま B02 へ渡す。
        address_comparison = compare_addresses(official_address, production_address)

    official_status = derive_official_source_entity_status(
        candidate, production_name, production_address, reasons
    )
    place_status = derive_place_id_status(
        production_row.get("place_ref_id"),
        getattr(sheet_row, "google_place_id", None) if sheet_row else None,
    )
    if place_status == identity_evidence.PLACE_ID_UNAVAILABLE:
        reasons.append(REASON_PLACE_ID_UNAVAILABLE)
    resolution_status = derive_existing_resolution_status(resolution, reasons)

    # --- B03（手で組み立てない）--------------------------------------------
    assessment = identity_evidence.assess_identity_evidence(
        address_comparison=address_comparison,
        name_identity_status=name_status,
        official_source_entity_status=official_status,
        place_id_status=place_status,
        existing_resolution_status=resolution_status,
    )

    # --- B04（本物の統合結果。互換 object を捏造しない）---------------------
    integration = identity_integration.integrate_position_identity(
        join_status=join_status,
        production_id=int(production_row["id"]),
        duplicate_production_ids=duplicates,
        identity_assessment=assessment,
    )

    return CandidateIdentitySupply(
        candidate_id=candidate_id,
        input_availability=tuple(availability),
        name_identity_status=assessment.name_identity_status,
        address_identity_status=assessment.address_identity_status,
        official_source_entity_status=assessment.official_source_entity_status,
        place_id_status=assessment.place_id_status,
        existing_resolution_status=assessment.existing_resolution_status,
        identity_evidence_status=assessment.identity_evidence_status,
        join_status=integration.join_status,
        identity_status=integration.identity_status,
        activation_status=_activation_status(
            integration, assessment.identity_evidence_status
        ),
        production_target_source=target_source,
        duplicate_production_ids=tuple(duplicates),
        review_reasons=_order_reasons(reasons),
        integration=integration,
    )


def build_identity_supply(
    *,
    candidate_ids: Sequence[str],
    candidates: Sequence[dict[str, Any]],
    seed_rows: Sequence[dict[str, Any]],
    production_rows: Sequence[dict[str, Any]] | None,
    spreadsheet_rows: Sequence[Any] | None,
    resolution_records: dict[str, Any] | None = None,
    linkage_artifact: Any = None,
) -> list[CandidateIdentitySupply]:
    """候補群の supply 結果を candidate_id 順で返す（決定的）。

    `linkage_artifact` は **一度だけ読み込んだ検証済み結果**を受け取り、
    全候補で使い回す。候補ごとに artifact file を読み直さない。
    """
    by_id = {
        str(row.get("candidate_id")): row
        for row in candidates
        if row.get("candidate_id")
    }
    records = resolution_records or {}
    return [
        build_candidate_identity_supply(
            candidate=by_id.get(candidate_id),
            candidate_id=candidate_id,
            seed_rows=seed_rows,
            production_rows=production_rows,
            spreadsheet_rows=spreadsheet_rows,
            resolution=records.get(candidate_id),
            linkage_artifact=linkage_artifact,
        )
        for candidate_id in sorted(candidate_ids)
    ]


def identity_integrations_by_candidate(
    supplies: Sequence[CandidateIdentitySupply],
) -> dict[str, Any]:
    """Position Audit `build_inputs()` へ渡す mapping を作る。

    値は **本物の** `PositionIdentityIntegrationResult` である。

    決定的な Production 比較対象が解決できなかった候補は mapping に
    **載せない**。Position Audit はその候補について B04 導入前の挙動を
    保ち、`RC_MISSING_PRODUCTION` / `RC_DUPLICATE_PRODUCTION_IDENTITY`
    による HOLD のままになる。
    """
    return {
        supply.candidate_id: supply.integration
        for supply in supplies
        if supply.integration is not None
    }


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

# 1.0 -> 1.1 は additive。`production_target_source` /
# `target_source_counts` / `linkage_artifact_state` を足しただけで、
# 既存 field の意味は変えていない。
SCHEMA_VERSION = "position-identity-supply/1.1"


def build_report(
    supplies: Sequence[CandidateIdentitySupply],
    *,
    linkage_artifact: Any = None,
) -> dict[str, Any]:
    """決定的な supply report を作る。

    `linkage_artifact` を渡すと、loader の artifact state を診断として
    そのまま載せる。loader の判定を supply 側で作り直さない。
    """
    counts: dict[str, int] = {}
    target_counts: dict[str, int] = {}
    for supply in supplies:
        counts[supply.activation_status] = counts.get(supply.activation_status, 0) + 1
        target_counts[supply.production_target_source] = (
            target_counts.get(supply.production_target_source, 0) + 1
        )

    if isinstance(linkage_artifact, canonical_linkage.LinkageArtifact):
        linkage_state = linkage_artifact.artifact_state
    else:
        linkage_state = None

    return {
        "schema_version": SCHEMA_VERSION,
        "totals": {"total": len(supplies)},
        "activation_counts": dict(sorted(counts.items())),
        "target_source_counts": dict(sorted(target_counts.items())),
        "linkage_artifact_state": linkage_state,
        "results": [supply.to_dict() for supply in supplies],
    }


def dump_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Real-data Identity Evidence Supply — Pilot 1")
    lines.append("")
    lines.append(
        "本レポートは read-only な supply 結果である。Production / Seed / "
        "Candidate Master / Spreadsheet をいっさい変更していない。"
    )
    lines.append("")
    lines.append(
        "`activation_status` は **supply report 専用**であり、Position "
        "Contract の canonical status も Machine Audit status も置き換えない。"
    )
    lines.append("")
    lines.append("## 集計")
    lines.append("")
    lines.append("```text")
    lines.append(f"total = {report['totals']['total']}")
    for status, count in report["activation_counts"].items():
        lines.append(f"{status} = {count}")
    lines.append("```")
    lines.append("")
    lines.append("### Production 比較対象の出どころ")
    lines.append("")
    lines.append(
        "`production_target_source` は report metadata であり、B03 の "
        "evidence でも Position Audit の status でもない。"
    )
    lines.append("")
    lines.append("```text")
    lines.append(
        f"linkage_artifact_state = {report['linkage_artifact_state'] or '-'}"
    )
    for source, count in report["target_source_counts"].items():
        lines.append(f"{source} = {count}")
    lines.append("```")
    lines.append("")
    lines.append("## 候補ごとの結果")
    lines.append("")
    lines.append(
        "| candidate_id | inputs | target | name | address | official_source | "
        "place_id | resolution | B03 | B04 join | B04 identity | activation |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    for row in report["results"]:
        inputs = ", ".join(row["input_availability"]) or "-"
        lines.append(
            f"| {row['candidate_id']} | {inputs} | "
            f"{row['production_target_source']} | {row['name_identity_status']} | "
            f"{row['address_identity_status']} | "
            f"{row['official_source_entity_status']} | {row['place_id_status']} | "
            f"{row['existing_resolution_status']} | "
            f"{row['identity_evidence_status']} | {row['join_status']} | "
            f"{row['identity_status']} | {row['activation_status']} |"
        )
    lines.append("")
    lines.append("## review_reasons")
    lines.append("")
    for row in report["results"]:
        reasons = ", ".join(f"`{reason}`" for reason in row["review_reasons"]) or "なし"
        duplicates = row["duplicate_production_ids"]
        suffix = (
            f"（duplicate_production_ids = {duplicates}）" if duplicates else ""
        )
        lines.append(f"- `{row['candidate_id']}`: {reasons}{suffix}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI（read-only。出力は明示された report file のみ）
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Real-data identity evidence supply (Pilot 1). read-only。"
            "Production / Seed / Candidate Master / Spreadsheet を変更しない。"
        )
    )
    parser.add_argument("--production-snapshot", type=Path, default=None)
    parser.add_argument("--spreadsheet-snapshot", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument(
        "--candidate-ids", nargs="*", default=list(W0_DB02_CANDIDATE_IDS)
    )
    parser.add_argument(
        "--linkage-artifact",
        type=Path,
        default=None,
        help=(
            "canonical linkage artifact の path。省略時は canonical な既定 "
            "path を読む。存在しなければ ARTIFACT_NOT_PRESENT として扱う。"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    production_rows = (
        position_audit.load_production_snapshot(args.production_snapshot)
        if args.production_snapshot
        else None
    )
    spreadsheet_rows = (
        position_audit.load_spreadsheet_snapshot(args.spreadsheet_snapshot)
        if args.spreadsheet_snapshot
        else None
    )

    # canonical artifact は **ここで一度だけ**読む。候補ごとに読み直さない。
    linkage_artifact = canonical_linkage.load_linkage_artifact(
        args.linkage_artifact
        if args.linkage_artifact
        else canonical_linkage.DEFAULT_ARTIFACT_PATH
    )

    supplies = build_identity_supply(
        candidate_ids=args.candidate_ids,
        candidates=position_audit.load_candidate_master(),
        seed_rows=position_audit.load_base_seed(),
        production_rows=production_rows,
        spreadsheet_rows=spreadsheet_rows,
        resolution_records=position_audit.load_resolution_records(),
        linkage_artifact=linkage_artifact,
    )
    report = build_report(supplies, linkage_artifact=linkage_artifact)

    if args.output_json:
        args.output_json.write_text(dump_json(report), encoding="utf-8")
    if args.output_md:
        args.output_md.write_text(render_markdown(report), encoding="utf-8")

    counts = report["activation_counts"]
    summary = " ".join(f"{key}={value}" for key, value in counts.items())
    print(f"position-identity-supply total={report['totals']['total']} {summary}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
