#!/usr/bin/env python
"""Canonical Production Candidate Linkage loader（foundation / read-only）。

正本契約: `docs/knowledge/production-candidate-linkage-contract.md`

canonical artifact:

```text
backend/temples/data/ops/production_candidate_linkage.json
```

を決定的に読み、検証し、**active な linkage だけ**を引けるようにする。

## 本 module の位置づけ

```text
Candidate Master
  -> candidate_id
Canonical Production Candidate Linkage（本 module が読む層）
  -> production_shrine_id
```

本 module は **loader であって Position Audit ではない**。
`PASS` / `HOLD` / `REVIEW` / `AUTO_PASS` といった Position Audit の語彙を
一切持たない。

## 行わないこと

* B02 / B03 / B04 / Position Audit / supply layer の呼び出し
* Production DB への接続・資格情報の参照
* network fetch（`evidence_refs` の外部 URL も取得しない）
* artifact への write / artifact の自動生成
* linkage の推測・補完・修復

## fail closed

```text
artifact が無い        -> ARTIFACT_NOT_PRESENT / active linkage 0件
artifact が不正        -> ARTIFACT_INVALID     / active linkage 0件
candidate が曖昧       -> その candidate だけ active linkage なし
REVOKED               -> 履歴としては読めるが active にはならない
```

「とりあえず読めた分だけ返す」ことはしない。

## 時間軸上の限界（重要）

```text
現在の artifact 単体の schema / invariant 検証
!=
履歴上の W1 / W2 mutation 規則の検証
```

契約 §7.2 の W1 は「既存 CONFIRMED row を、可変4 field だけを使って
REVOKED へ更新する」ことを要求するが、**現在の artifact 1枚からは、
過去に immutable な field が書き換えられなかったことを証明できない**。
それには repository history か以前の artifact 版との比較が要る。

本 module は git history を読まない。mutation history validator も
実装しない。それは別 task である。

`evidence_refs` の repository 追跡可能性についても、本 module が検証
するのは **形式**であって、参照先が現在の repository に実在するか
どうかではない。過去時点の evidence が移動・改名されうるためである。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ARTIFACT_PATH = (
    REPO_ROOT / "backend" / "temples" / "data" / "ops"
    / "production_candidate_linkage.json"
)

CONTRACT_PATH = "docs/knowledge/production-candidate-linkage-contract.md"

# 受け入れる schema version は **1つだけ**。未知の版は fail closed とし、
# 部分 parse も暗黙の up/down grade も行わない（契約 §4.1）。
SUPPORTED_SCHEMA_VERSION = "production-candidate-linkage/1.0"


# ---------------------------------------------------------------------------
# artifact state（**loader 専用**の語彙）
# ---------------------------------------------------------------------------
# Position Audit の status ではない。混ぜない。
ARTIFACT_NOT_PRESENT = "ARTIFACT_NOT_PRESENT"
ARTIFACT_VALID = "ARTIFACT_VALID"
ARTIFACT_INVALID = "ARTIFACT_INVALID"

ARTIFACT_STATES = frozenset(
    {ARTIFACT_NOT_PRESENT, ARTIFACT_VALID, ARTIFACT_INVALID}
)


# ---------------------------------------------------------------------------
# 契約の閉じた語彙（契約 §5 / §6 / §9.2）
# ---------------------------------------------------------------------------
STATUS_CONFIRMED = "CONFIRMED"
STATUS_REVOKED = "REVOKED"
LINKAGE_STATUSES = frozenset({STATUS_CONFIRMED, STATUS_REVOKED})

SOURCE_PRODUCTION_RECONCILIATION = "PRODUCTION_RECONCILIATION"
SOURCE_HUMAN_IDENTITY_ADJUDICATION = "HUMAN_IDENTITY_ADJUDICATION"
SOURCE_MIGRATION_RECORD = "MIGRATION_RECORD"
LINKAGE_SOURCES = frozenset(
    {
        SOURCE_PRODUCTION_RECONCILIATION,
        SOURCE_HUMAN_IDENTITY_ADJUDICATION,
        SOURCE_MIGRATION_RECORD,
    }
)

REVOKED_REASONS = frozenset(
    {
        "PRODUCTION_ROW_DELETED",
        "PRODUCTION_ROW_MERGED",
        "PRODUCTION_ROW_RECREATED",
        "PRODUCTION_ROW_RENUMBERED",
        "PRODUCTION_ROW_SUPERSEDED",
        "IDENTITY_ADJUDICATION_REVERSED",
    }
)


# ---------------------------------------------------------------------------
# 契約の field 集合（契約 §4.1 / §4.2）
# ---------------------------------------------------------------------------
TOP_LEVEL_FIELDS = (
    "schema_version",
    "title",
    "contract",
    "recorded_at",
    "linkages",
)

COMMON_ROW_FIELDS = (
    "linkage_id",
    "candidate_id",
    "production_shrine_id",
    "linkage_status",
    "linkage_source",
    "verified_at",
    "official_name",
    "official_address",
    "evidence_refs",
    "note",
)

REVOKED_ROW_FIELDS = (
    "revoked_at",
    "revoked_reason",
    "revocation_evidence_refs",
)

OPTIONAL_ROW_FIELDS = ("supersedes",)

ALLOWED_ROW_FIELDS = frozenset(
    COMMON_ROW_FIELDS + REVOKED_ROW_FIELDS + OPTIONAL_ROW_FIELDS
)

# 契約 §7.2 の W1 で変更してよい field / 確認後 immutable な field。
#
# 本 module はこれを **検証に使わない**（現在の artifact 1枚からは過去の
# mutation を証明できない。module docstring の「時間軸上の限界」を参照）。
# 将来の mutation-history validator が参照できるよう、契約上の集合だけを
# ここに固定しておく。
W1_MUTABLE_FIELDS = (
    "linkage_status",
    "revoked_at",
    "revoked_reason",
    "revocation_evidence_refs",
)

POST_CONFIRMATION_IMMUTABLE_FIELDS = (
    "candidate_id",
    "production_shrine_id",
    "linkage_source",
    "verified_at",
    "official_name",
    "official_address",
    "evidence_refs",
    "linkage_id",
)


# ---------------------------------------------------------------------------
# validation issue codes
# ---------------------------------------------------------------------------
# 出力順を固定するため、**定義順が canonical order** である（§ordering）。
ISSUE_ARTIFACT_UNREADABLE = "ARTIFACT_UNREADABLE"
ISSUE_ARTIFACT_NOT_JSON = "ARTIFACT_NOT_JSON"
ISSUE_ARTIFACT_NOT_OBJECT = "ARTIFACT_NOT_OBJECT"
ISSUE_TOP_LEVEL_FIELD_MISSING = "TOP_LEVEL_FIELD_MISSING"
ISSUE_TOP_LEVEL_FIELD_UNKNOWN = "TOP_LEVEL_FIELD_UNKNOWN"
ISSUE_TOP_LEVEL_FIELD_TYPE = "TOP_LEVEL_FIELD_TYPE"
ISSUE_SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
ISSUE_CONTRACT_PATH_UNEXPECTED = "CONTRACT_PATH_UNEXPECTED"
ISSUE_DATE_FORMAT_INVALID = "DATE_FORMAT_INVALID"
ISSUE_ROW_NOT_OBJECT = "ROW_NOT_OBJECT"
ISSUE_ROW_FIELD_MISSING = "ROW_FIELD_MISSING"
ISSUE_ROW_FIELD_UNKNOWN = "ROW_FIELD_UNKNOWN"
ISSUE_ROW_FIELD_TYPE = "ROW_FIELD_TYPE"
ISSUE_ROW_FIELD_EMPTY = "ROW_FIELD_EMPTY"
ISSUE_LINKAGE_STATUS_UNKNOWN = "LINKAGE_STATUS_UNKNOWN"
ISSUE_LINKAGE_SOURCE_UNKNOWN = "LINKAGE_SOURCE_UNKNOWN"
ISSUE_REVOKED_REASON_UNKNOWN = "REVOKED_REASON_UNKNOWN"
ISSUE_LINKAGE_ID_MALFORMED = "LINKAGE_ID_MALFORMED"
ISSUE_LINKAGE_ID_DUPLICATE = "LINKAGE_ID_DUPLICATE"
ISSUE_PRODUCTION_SHRINE_ID_INVALID = "PRODUCTION_SHRINE_ID_INVALID"
ISSUE_EVIDENCE_EMPTY = "EVIDENCE_EMPTY"
ISSUE_EVIDENCE_VALUE_EMPTY = "EVIDENCE_VALUE_EMPTY"
ISSUE_EVIDENCE_DUPLICATE = "EVIDENCE_DUPLICATE"
ISSUE_EVIDENCE_UNSORTED = "EVIDENCE_UNSORTED"
ISSUE_EVIDENCE_UNRECOGNIZED_FORM = "EVIDENCE_UNRECOGNIZED_FORM"
ISSUE_EVIDENCE_NOT_REPOSITORY_TRACEABLE = "EVIDENCE_NOT_REPOSITORY_TRACEABLE"
ISSUE_REVOKED_FIELD_PRESENT_ON_CONFIRMED = (
    "REVOKED_FIELD_PRESENT_ON_CONFIRMED"
)
ISSUE_ACTIVE_CANDIDATE_DUPLICATE = "ACTIVE_CANDIDATE_DUPLICATE"
ISSUE_ACTIVE_PRODUCTION_ID_AMBIGUOUS = "ACTIVE_PRODUCTION_ID_AMBIGUOUS"

ISSUE_CODE_ORDER = (
    ISSUE_ARTIFACT_UNREADABLE,
    ISSUE_ARTIFACT_NOT_JSON,
    ISSUE_ARTIFACT_NOT_OBJECT,
    ISSUE_TOP_LEVEL_FIELD_MISSING,
    ISSUE_TOP_LEVEL_FIELD_UNKNOWN,
    ISSUE_TOP_LEVEL_FIELD_TYPE,
    ISSUE_SCHEMA_VERSION_UNSUPPORTED,
    ISSUE_CONTRACT_PATH_UNEXPECTED,
    ISSUE_DATE_FORMAT_INVALID,
    ISSUE_ROW_NOT_OBJECT,
    ISSUE_ROW_FIELD_MISSING,
    ISSUE_ROW_FIELD_UNKNOWN,
    ISSUE_ROW_FIELD_TYPE,
    ISSUE_ROW_FIELD_EMPTY,
    ISSUE_LINKAGE_STATUS_UNKNOWN,
    ISSUE_LINKAGE_SOURCE_UNKNOWN,
    ISSUE_REVOKED_REASON_UNKNOWN,
    ISSUE_LINKAGE_ID_MALFORMED,
    ISSUE_LINKAGE_ID_DUPLICATE,
    ISSUE_PRODUCTION_SHRINE_ID_INVALID,
    ISSUE_EVIDENCE_EMPTY,
    ISSUE_EVIDENCE_VALUE_EMPTY,
    ISSUE_EVIDENCE_DUPLICATE,
    ISSUE_EVIDENCE_UNSORTED,
    ISSUE_EVIDENCE_UNRECOGNIZED_FORM,
    ISSUE_EVIDENCE_NOT_REPOSITORY_TRACEABLE,
    ISSUE_REVOKED_FIELD_PRESENT_ON_CONFIRMED,
    ISSUE_ACTIVE_CANDIDATE_DUPLICATE,
    ISSUE_ACTIVE_PRODUCTION_ID_AMBIGUOUS,
)
ISSUE_CODES = frozenset(ISSUE_CODE_ORDER)
_ISSUE_RANK = {code: index for index, code in enumerate(ISSUE_CODE_ORDER)}

# issue の適用範囲。
#
#   ARTIFACT / ROW   -> artifact 全体を ARTIFACT_INVALID にする
#   CANDIDATE        -> artifact は valid のまま。当該 candidate だけ
#                       active linkage なしにする（契約 §7.1 INV-5）
SCOPE_ARTIFACT = "ARTIFACT"
SCOPE_ROW = "ROW"
SCOPE_CANDIDATE = "CANDIDATE"

ISSUE_SCOPES = frozenset({SCOPE_ARTIFACT, SCOPE_ROW, SCOPE_CANDIDATE})

# artifact 全体を無効にする issue の scope。
_INVALIDATING_SCOPES = frozenset({SCOPE_ARTIFACT, SCOPE_ROW})


# ---------------------------------------------------------------------------
# evidence 参照の形式（契約 §8.1 / §8.4）
# ---------------------------------------------------------------------------
EVIDENCE_FORM_REPO_PATH = "REPO_PATH"
EVIDENCE_FORM_GIT_SHA = "GIT_SHA"
EVIDENCE_FORM_PR = "PR"
EVIDENCE_FORM_EXTERNAL_URL = "EXTERNAL_URL"
EVIDENCE_FORM_UNRECOGNIZED = "UNRECOGNIZED"

# repository 追跡可能とみなせる形式。
REPOSITORY_TRACEABLE_FORMS = frozenset(
    {EVIDENCE_FORM_REPO_PATH, EVIDENCE_FORM_GIT_SHA, EVIDENCE_FORM_PR}
)

_GIT_SHA_RE = re.compile(r"^git:[0-9a-fA-F]{40}$")
_PR_RE = re.compile(r"^pr:[1-9][0-9]*$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LINKAGE_ID_RE = re.compile(r"^(?P<candidate_id>.+)#(?P<sequence>[0-9]+)$")
# 任意の URL を repo-relative path と誤認しないための scheme 検出。
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


def classify_evidence_ref(value: str) -> str:
    """evidence 参照1件の形式を判定する（network access なし）。

    ```text
    git:<40 hex>          -> GIT_SHA          repository 追跡可能
    pr:<number>           -> PR               repository 追跡可能
    <repo-relative-path>  -> REPO_PATH        repository 追跡可能
    <path>#<anchor>       -> REPO_PATH        repository 追跡可能
    <scheme>://...        -> EXTERNAL_URL     補足のみ
    それ以外              -> UNRECOGNIZED     不正
    ```

    **参照先が実在するかは確認しない。** 検証するのは形式だけである
    （過去時点の evidence は移動・改名されうる）。外部 URL も取得しない。
    """
    if not isinstance(value, str) or not value:
        return EVIDENCE_FORM_UNRECOGNIZED

    if _GIT_SHA_RE.match(value):
        return EVIDENCE_FORM_GIT_SHA
    if _PR_RE.match(value):
        return EVIDENCE_FORM_PR

    # scheme を持つものは repo path ではない。`https://...` を
    # repo-relative path と誤認しないための境界。
    if _SCHEME_RE.match(value):
        if "://" in value:
            return EVIDENCE_FORM_EXTERNAL_URL
        # `git:` / `pr:` は上で処理済み。それ以外の scheme 様の文字列は
        # 既知の形式に当てはまらない。
        return EVIDENCE_FORM_UNRECOGNIZED

    path_part, _, anchor = value.partition("#")
    if "#" in value and not anchor:
        return EVIDENCE_FORM_UNRECOGNIZED
    if not path_part:
        return EVIDENCE_FORM_UNRECOGNIZED
    if path_part.startswith("/") or path_part.startswith("~"):
        return EVIDENCE_FORM_UNRECOGNIZED
    if "\\" in path_part:
        return EVIDENCE_FORM_UNRECOGNIZED
    if any(char.isspace() for char in path_part):
        return EVIDENCE_FORM_UNRECOGNIZED
    segments = path_part.split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        return EVIDENCE_FORM_UNRECOGNIZED
    return EVIDENCE_FORM_REPO_PATH


def is_repository_traceable(value: str) -> bool:
    return classify_evidence_ref(value) in REPOSITORY_TRACEABLE_FORMS


def _is_canonical_date(value: Any) -> bool:
    """canonical な `YYYY-MM-DD` か。

    `date.fromisoformat` は Python 3.11 以降 `YYYYMMDD` や
    `YYYY-MM-DDTHH:MM` も受けるため、先に厳密な形へ絞ってから
    暦としての妥当性を見る。
    """
    if not isinstance(value, str) or not _DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------------------
# dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LinkageValidationIssue:
    """決定的で machine-readable な検証所見。

    例外に頼らない。想定内の不正データは issue として返す。
    """

    code: str
    scope: str
    row_index: int | None = None
    linkage_id: str | None = None
    candidate_id: str | None = None
    field_name: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "scope": self.scope,
            "row_index": self.row_index,
            "linkage_id": self.linkage_id,
            "candidate_id": self.candidate_id,
            "field_name": self.field_name,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class LinkageRow:
    """契約 §4.2 の row（検証済み）。"""

    linkage_id: str
    candidate_id: str
    production_shrine_id: int
    linkage_status: str
    linkage_source: str
    verified_at: str
    official_name: str
    official_address: str
    evidence_refs: tuple[str, ...]
    note: str
    revoked_at: str | None = None
    revoked_reason: str | None = None
    revocation_evidence_refs: tuple[str, ...] = ()
    supersedes: str | None = None
    row_index: int = -1

    @property
    def is_active(self) -> bool:
        """active（= `CONFIRMED`）か。`REVOKED` は決して active にならない。"""
        return self.linkage_status == STATUS_CONFIRMED

    def to_dict(self) -> dict[str, Any]:
        return {
            "linkage_id": self.linkage_id,
            "candidate_id": self.candidate_id,
            "production_shrine_id": self.production_shrine_id,
            "linkage_status": self.linkage_status,
            "linkage_source": self.linkage_source,
            "verified_at": self.verified_at,
            "official_name": self.official_name,
            "official_address": self.official_address,
            "evidence_refs": list(self.evidence_refs),
            "note": self.note,
            "revoked_at": self.revoked_at,
            "revoked_reason": self.revoked_reason,
            "revocation_evidence_refs": list(self.revocation_evidence_refs),
            "supersedes": self.supersedes,
        }


@dataclass(frozen=True)
class LinkageArtifact:
    """artifact 1枚の読み取り結果。

    ## 概念を分ける

    ```text
    artifact_state        存在するか / 妥当か
    issues                決定的な検証所見
    rows                  parse できた履歴 row（REVOKED を含む）
    active_linkages       **使える** active linkage だけ
    ```

    `rows` に入っていることと active であることは別である。
    `active_linkages` は artifact が妥当なときにだけ populate される。
    """

    artifact_state: str
    path: str
    schema_version: str | None = None
    title: str | None = None
    contract: str | None = None
    recorded_at: str | None = None
    rows: tuple[LinkageRow, ...] = ()
    issues: tuple[LinkageValidationIssue, ...] = ()
    active_linkages: Mapping[str, LinkageRow] = field(default_factory=dict)

    @property
    def is_present(self) -> bool:
        return self.artifact_state != ARTIFACT_NOT_PRESENT

    @property
    def is_valid(self) -> bool:
        return self.artifact_state == ARTIFACT_VALID

    def active_linkage_for(self, candidate_id: str) -> LinkageRow | None:
        """candidate の active linkage を引く。無ければ `None`。

        次のいずれでも `None` を返す（best effort を返さない）。

        ```text
        candidate が artifact に無い
        REVOKED row しか無い
        active row が重複している
        逆方向 production_shrine_id が曖昧
        artifact が無い / 不正
        ```
        """
        if not self.is_valid:
            return None
        return self.active_linkages.get(candidate_id)

    def issue_codes(self) -> tuple[str, ...]:
        """出現順（canonical order）の issue code 列。"""
        return tuple(issue.code for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        """決定的な診断表現。同一 bytes からは常に同一 dict。"""
        return {
            "artifact_state": self.artifact_state,
            "path": self.path,
            "schema_version": self.schema_version,
            "title": self.title,
            "contract": self.contract,
            "recorded_at": self.recorded_at,
            "row_count": len(self.rows),
            "active_linkage_count": len(self.active_linkages),
            "active_candidate_ids": sorted(self.active_linkages),
            "issues": [issue.to_dict() for issue in self.issues],
            "rows": [row.to_dict() for row in self.rows],
        }


# ---------------------------------------------------------------------------
# issue ordering
# ---------------------------------------------------------------------------


def _issue_sort_key(issue: LinkageValidationIssue) -> tuple[Any, ...]:
    return (
        _ISSUE_RANK.get(issue.code, len(ISSUE_CODE_ORDER)),
        issue.scope,
        -1 if issue.row_index is None else issue.row_index,
        issue.candidate_id or "",
        issue.linkage_id or "",
        issue.field_name or "",
        issue.detail or "",
    )


def order_issues(
    issues: Iterable[LinkageValidationIssue],
) -> tuple[LinkageValidationIssue, ...]:
    """issue を canonical order で並べる（入力順を出力に漏らさない）。"""
    return tuple(sorted(issues, key=_issue_sort_key))


# ---------------------------------------------------------------------------
# evidence 検証
# ---------------------------------------------------------------------------


def _validate_evidence_list(
    values: Any,
    *,
    field_name: str,
    row_index: int,
    linkage_id: str | None,
    candidate_id: str | None,
    issues: list[LinkageValidationIssue],
) -> tuple[str, ...]:
    """evidence 配列を検証する（契約 §8.1 / §8.2 / §8.4 共通）。"""

    def _issue(code: str, detail: str | None = None) -> None:
        issues.append(
            LinkageValidationIssue(
                code=code,
                scope=SCOPE_ROW,
                row_index=row_index,
                linkage_id=linkage_id,
                candidate_id=candidate_id,
                field_name=field_name,
                detail=detail,
            )
        )

    if not isinstance(values, list):
        _issue(ISSUE_ROW_FIELD_TYPE, "expected list")
        return ()
    if not all(isinstance(item, str) for item in values):
        _issue(ISSUE_ROW_FIELD_TYPE, "expected list of string")
        return ()
    if not values:
        _issue(ISSUE_EVIDENCE_EMPTY, "at least 1 entry required")
        return ()

    ok = True
    if any(item == "" for item in values):
        _issue(ISSUE_EVIDENCE_VALUE_EMPTY, "empty value")
        ok = False
    if len(set(values)) != len(values):
        _issue(ISSUE_EVIDENCE_DUPLICATE, "duplicate value")
        ok = False

    # byte 順昇順で保持されていること（契約 §8.2）。並べ替えて直さない。
    encoded = [item.encode("utf-8") for item in values]
    if encoded != sorted(encoded):
        _issue(ISSUE_EVIDENCE_UNSORTED, "not in byte-order")
        ok = False

    forms = [classify_evidence_ref(item) for item in values]
    if EVIDENCE_FORM_UNRECOGNIZED in forms:
        _issue(ISSUE_EVIDENCE_UNRECOGNIZED_FORM, "unrecognized reference form")
        ok = False
    elif not any(form in REPOSITORY_TRACEABLE_FORMS for form in forms):
        # 外部 URL だけの list は不正（契約 §8.1 / §8.4）。
        _issue(
            ISSUE_EVIDENCE_NOT_REPOSITORY_TRACEABLE,
            "no repository-traceable reference",
        )
        ok = False

    return tuple(values) if ok else ()


# ---------------------------------------------------------------------------
# row 検証
# ---------------------------------------------------------------------------


def _validate_row(
    raw: Any, row_index: int, issues: list[LinkageValidationIssue]
) -> LinkageRow | None:
    """row 1件を検証する。不正なら `None`（修復しない）。"""
    if not isinstance(raw, dict):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_ROW_NOT_OBJECT, scope=SCOPE_ROW, row_index=row_index
            )
        )
        return None

    linkage_id = raw.get("linkage_id") if isinstance(
        raw.get("linkage_id"), str
    ) else None
    candidate_id = raw.get("candidate_id") if isinstance(
        raw.get("candidate_id"), str
    ) else None

    def _issue(
        code: str, field_name: str | None = None, detail: str | None = None
    ) -> None:
        issues.append(
            LinkageValidationIssue(
                code=code,
                scope=SCOPE_ROW,
                row_index=row_index,
                linkage_id=linkage_id,
                candidate_id=candidate_id,
                field_name=field_name,
                detail=detail,
            )
        )

    ok = True

    unknown = sorted(set(raw) - ALLOWED_ROW_FIELDS)
    for name in unknown:
        _issue(ISSUE_ROW_FIELD_UNKNOWN, name)
        ok = False

    missing_common = [name for name in COMMON_ROW_FIELDS if name not in raw]
    for name in missing_common:
        _issue(ISSUE_ROW_FIELD_MISSING, name)
    if missing_common:
        # 必須 field が欠けた row は補完しない。以降の検証も行わない。
        return None

    status = raw.get("linkage_status")
    if not isinstance(status, str):
        _issue(ISSUE_ROW_FIELD_TYPE, "linkage_status", "expected string")
        return None
    if status not in LINKAGE_STATUSES:
        _issue(ISSUE_LINKAGE_STATUS_UNKNOWN, "linkage_status", status)
        return None

    # --- 文字列 field -------------------------------------------------------
    for name in ("candidate_id", "official_name", "official_address"):
        value = raw.get(name)
        if not isinstance(value, str):
            _issue(ISSUE_ROW_FIELD_TYPE, name, "expected string")
            ok = False
        elif not value.strip():
            _issue(ISSUE_ROW_FIELD_EMPTY, name)
            ok = False

    note = raw.get("note")
    if not isinstance(note, str):
        _issue(ISSUE_ROW_FIELD_TYPE, "note", "expected string")
        ok = False

    # --- linkage_id（`<candidate_id>#<連番>`）------------------------------
    raw_linkage_id = raw.get("linkage_id")
    if not isinstance(raw_linkage_id, str):
        _issue(ISSUE_ROW_FIELD_TYPE, "linkage_id", "expected string")
        ok = False
    else:
        match = _LINKAGE_ID_RE.match(raw_linkage_id)
        if match is None or (
            isinstance(candidate_id, str)
            and match.group("candidate_id") != candidate_id
        ):
            # 生成も修復もしない。形が違えば不正のまま返す。
            _issue(ISSUE_LINKAGE_ID_MALFORMED, "linkage_id", raw_linkage_id)
            ok = False

    # --- production_shrine_id ----------------------------------------------
    production_shrine_id = raw.get("production_shrine_id")
    if isinstance(production_shrine_id, bool) or not isinstance(
        production_shrine_id, int
    ):
        _issue(
            ISSUE_ROW_FIELD_TYPE, "production_shrine_id", "expected integer"
        )
        ok = False
    elif production_shrine_id <= 0:
        # Production Shrine の primary key は正の整数である。
        _issue(
            ISSUE_PRODUCTION_SHRINE_ID_INVALID,
            "production_shrine_id",
            str(production_shrine_id),
        )
        ok = False

    # --- linkage_source -----------------------------------------------------
    source = raw.get("linkage_source")
    if not isinstance(source, str):
        _issue(ISSUE_ROW_FIELD_TYPE, "linkage_source", "expected string")
        ok = False
    elif source not in LINKAGE_SOURCES:
        _issue(ISSUE_LINKAGE_SOURCE_UNKNOWN, "linkage_source", source)
        ok = False

    # --- verified_at --------------------------------------------------------
    verified_at = raw.get("verified_at")
    if not _is_canonical_date(verified_at):
        _issue(ISSUE_DATE_FORMAT_INVALID, "verified_at", str(verified_at))
        ok = False

    # --- evidence_refs ------------------------------------------------------
    evidence_refs = _validate_evidence_list(
        raw.get("evidence_refs"),
        field_name="evidence_refs",
        row_index=row_index,
        linkage_id=linkage_id,
        candidate_id=candidate_id,
        issues=issues,
    )
    if not evidence_refs:
        ok = False

    # --- supersedes（任意。MS-FOLLOWUP-03 が未決のため最小限）--------------
    supersedes = raw.get("supersedes", None)
    if supersedes is not None:
        if not isinstance(supersedes, str):
            _issue(ISSUE_ROW_FIELD_TYPE, "supersedes", "expected string or null")
            ok = False
        elif not supersedes:
            _issue(ISSUE_ROW_FIELD_EMPTY, "supersedes")
            ok = False

    # --- REVOKED 固有 -------------------------------------------------------
    revoked_at: str | None = None
    revoked_reason: str | None = None
    revocation_evidence_refs: tuple[str, ...] = ()

    if status == STATUS_REVOKED:
        for name in REVOKED_ROW_FIELDS:
            if name not in raw:
                _issue(ISSUE_ROW_FIELD_MISSING, name)
                ok = False

        if "revoked_at" in raw:
            if not _is_canonical_date(raw.get("revoked_at")):
                _issue(
                    ISSUE_DATE_FORMAT_INVALID,
                    "revoked_at",
                    str(raw.get("revoked_at")),
                )
                ok = False
            else:
                revoked_at = raw["revoked_at"]

        if "revoked_reason" in raw:
            value = raw.get("revoked_reason")
            if not isinstance(value, str):
                _issue(ISSUE_ROW_FIELD_TYPE, "revoked_reason", "expected string")
                ok = False
            elif value not in REVOKED_REASONS:
                _issue(ISSUE_REVOKED_REASON_UNKNOWN, "revoked_reason", value)
                ok = False
            else:
                revoked_reason = value

        if "revocation_evidence_refs" in raw:
            revocation_evidence_refs = _validate_evidence_list(
                raw.get("revocation_evidence_refs"),
                field_name="revocation_evidence_refs",
                row_index=row_index,
                linkage_id=linkage_id,
                candidate_id=candidate_id,
                issues=issues,
            )
            if not revocation_evidence_refs:
                ok = False
    else:
        # CONFIRMED row に失効 field を載せない。
        for name in REVOKED_ROW_FIELDS:
            if name in raw:
                _issue(ISSUE_REVOKED_FIELD_PRESENT_ON_CONFIRMED, name)
                ok = False

    if not ok:
        return None

    return LinkageRow(
        linkage_id=raw["linkage_id"],
        candidate_id=raw["candidate_id"],
        production_shrine_id=raw["production_shrine_id"],
        linkage_status=status,
        linkage_source=raw["linkage_source"],
        verified_at=raw["verified_at"],
        official_name=raw["official_name"],
        official_address=raw["official_address"],
        evidence_refs=evidence_refs,
        note=raw["note"],
        revoked_at=revoked_at,
        revoked_reason=revoked_reason,
        revocation_evidence_refs=revocation_evidence_refs,
        supersedes=supersedes,
        row_index=row_index,
    )


# ---------------------------------------------------------------------------
# document 検証
# ---------------------------------------------------------------------------


def validate_linkage_document(
    payload: Any, *, path: str = str(DEFAULT_ARTIFACT_PATH)
) -> LinkageArtifact:
    """decode 済み payload を検証する（純関数・file を読まない）。"""
    issues: list[LinkageValidationIssue] = []

    if not isinstance(payload, dict):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_ARTIFACT_NOT_OBJECT, scope=SCOPE_ARTIFACT
            )
        )
        return LinkageArtifact(
            artifact_state=ARTIFACT_INVALID,
            path=path,
            issues=order_issues(issues),
        )

    for name in sorted(set(payload) - set(TOP_LEVEL_FIELDS)):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_TOP_LEVEL_FIELD_UNKNOWN,
                scope=SCOPE_ARTIFACT,
                field_name=name,
            )
        )
    for name in TOP_LEVEL_FIELDS:
        if name not in payload:
            issues.append(
                LinkageValidationIssue(
                    code=ISSUE_TOP_LEVEL_FIELD_MISSING,
                    scope=SCOPE_ARTIFACT,
                    field_name=name,
                )
            )

    schema_version = payload.get("schema_version")
    title = payload.get("title")
    contract = payload.get("contract")
    recorded_at = payload.get("recorded_at")
    linkages = payload.get("linkages")

    if not isinstance(schema_version, str):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_TOP_LEVEL_FIELD_TYPE,
                scope=SCOPE_ARTIFACT,
                field_name="schema_version",
                detail="expected string",
            )
        )
    elif schema_version != SUPPORTED_SCHEMA_VERSION:
        # 未知の版を部分 parse しない。暗黙の up/down grade もしない。
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_SCHEMA_VERSION_UNSUPPORTED,
                scope=SCOPE_ARTIFACT,
                field_name="schema_version",
                detail=schema_version,
            )
        )
        return LinkageArtifact(
            artifact_state=ARTIFACT_INVALID,
            path=path,
            schema_version=schema_version,
            issues=order_issues(issues),
        )

    if not isinstance(title, str) or not title.strip():
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_TOP_LEVEL_FIELD_TYPE,
                scope=SCOPE_ARTIFACT,
                field_name="title",
                detail="expected non-empty string",
            )
        )

    if not isinstance(contract, str):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_TOP_LEVEL_FIELD_TYPE,
                scope=SCOPE_ARTIFACT,
                field_name="contract",
                detail="expected string",
            )
        )
    elif contract != CONTRACT_PATH:
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_CONTRACT_PATH_UNEXPECTED,
                scope=SCOPE_ARTIFACT,
                field_name="contract",
                detail=contract,
            )
        )

    if not _is_canonical_date(recorded_at):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_DATE_FORMAT_INVALID,
                scope=SCOPE_ARTIFACT,
                field_name="recorded_at",
                detail=str(recorded_at),
            )
        )

    rows: list[LinkageRow] = []
    if not isinstance(linkages, list):
        issues.append(
            LinkageValidationIssue(
                code=ISSUE_TOP_LEVEL_FIELD_TYPE,
                scope=SCOPE_ARTIFACT,
                field_name="linkages",
                detail="expected list",
            )
        )
    else:
        for index, raw in enumerate(linkages):
            row = _validate_row(raw, index, issues)
            if row is not None:
                rows.append(row)

        seen_ids: dict[str, int] = {}
        for row in rows:
            if row.linkage_id in seen_ids:
                # `linkage_id` は安定した一意参照である（契約 §4.3）。
                issues.append(
                    LinkageValidationIssue(
                        code=ISSUE_LINKAGE_ID_DUPLICATE,
                        scope=SCOPE_ROW,
                        row_index=row.row_index,
                        linkage_id=row.linkage_id,
                        candidate_id=row.candidate_id,
                        field_name="linkage_id",
                    )
                )
            else:
                seen_ids[row.linkage_id] = row.row_index

    blocked_candidates = _collect_current_state_issues(rows, issues)

    invalid = any(issue.scope in _INVALIDATING_SCOPES for issue in issues)
    state = ARTIFACT_INVALID if invalid else ARTIFACT_VALID

    active: dict[str, LinkageRow] = {}
    if not invalid:
        for row in rows:
            if row.is_active and row.candidate_id not in blocked_candidates:
                active[row.candidate_id] = row

    return LinkageArtifact(
        artifact_state=state,
        path=path,
        schema_version=schema_version if isinstance(schema_version, str) else None,
        title=title if isinstance(title, str) else None,
        contract=contract if isinstance(contract, str) else None,
        recorded_at=recorded_at if isinstance(recorded_at, str) else None,
        rows=tuple(rows),
        issues=order_issues(issues),
        active_linkages=active,
    )


def _collect_current_state_issues(
    rows: Sequence[LinkageRow], issues: list[LinkageValidationIssue]
) -> frozenset[str]:
    """現在の artifact 1枚から証明できる invariant を検証する。

    ```text
    INV-1 / INV-5  同一 candidate に active row が複数 -> その candidate を塞ぐ
    §7.4 暫定      同一 production_shrine_id の active row が複数
                   -> 該当する **全** candidate を塞ぐ
    ```

    どちらも **どれか1つを選ばない**。candidate 単位の fail closed であり、
    artifact 全体を不正にはしない（契約 §7.1）。

    ここで検証できるのは現在の状態だけである。過去の W1 / W2 mutation が
    規則どおりだったかは artifact 1枚からは証明できない。
    """
    blocked: set[str] = set()

    by_candidate: dict[str, list[LinkageRow]] = {}
    for row in rows:
        if row.is_active:
            by_candidate.setdefault(row.candidate_id, []).append(row)

    for candidate_id in sorted(by_candidate):
        active_rows = by_candidate[candidate_id]
        if len(active_rows) > 1:
            blocked.add(candidate_id)
            issues.append(
                LinkageValidationIssue(
                    code=ISSUE_ACTIVE_CANDIDATE_DUPLICATE,
                    scope=SCOPE_CANDIDATE,
                    candidate_id=candidate_id,
                    detail=",".join(
                        sorted(row.linkage_id for row in active_rows)
                    ),
                )
            )

    by_production_id: dict[int, list[LinkageRow]] = {}
    for row in rows:
        if row.is_active:
            by_production_id.setdefault(row.production_shrine_id, []).append(row)

    for production_shrine_id in sorted(by_production_id):
        active_rows = by_production_id[production_shrine_id]
        candidate_ids = {row.candidate_id for row in active_rows}
        # 同一 candidate 内の重複は上で処理済み。ここは **逆方向**の曖昧さ。
        if len(candidate_ids) > 1:
            # MS-FOLLOWUP-02 は未決。全体の一意性 invariant を発明せず、
            # 契約 §7.4 の暫定挙動（該当全 candidate を塞ぐ）だけを実装する。
            for candidate_id in sorted(candidate_ids):
                blocked.add(candidate_id)
                issues.append(
                    LinkageValidationIssue(
                        code=ISSUE_ACTIVE_PRODUCTION_ID_AMBIGUOUS,
                        scope=SCOPE_CANDIDATE,
                        candidate_id=candidate_id,
                        field_name="production_shrine_id",
                        detail=str(production_shrine_id),
                    )
                )

    return frozenset(blocked)


# ---------------------------------------------------------------------------
# loader
# ---------------------------------------------------------------------------


def load_linkage_artifact(
    path: Path | str = DEFAULT_ARTIFACT_PATH,
) -> LinkageArtifact:
    """canonical artifact を読む（read-only）。

    artifact が無いのは **正常な状態**である。identity の問題の証拠では
    ないし、空 artifact を自動生成もしない。
    """
    artifact_path = Path(path)
    display_path = str(artifact_path)

    if not artifact_path.exists():
        return LinkageArtifact(
            artifact_state=ARTIFACT_NOT_PRESENT, path=display_path
        )

    try:
        text = artifact_path.read_text(encoding="utf-8")
    except OSError as error:
        return LinkageArtifact(
            artifact_state=ARTIFACT_INVALID,
            path=display_path,
            issues=(
                LinkageValidationIssue(
                    code=ISSUE_ARTIFACT_UNREADABLE,
                    scope=SCOPE_ARTIFACT,
                    detail=type(error).__name__,
                ),
            ),
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        return LinkageArtifact(
            artifact_state=ARTIFACT_INVALID,
            path=display_path,
            issues=(
                LinkageValidationIssue(
                    code=ISSUE_ARTIFACT_NOT_JSON,
                    scope=SCOPE_ARTIFACT,
                    detail=error.msg,
                ),
            ),
        )

    return validate_linkage_document(payload, path=display_path)


def active_linkage_map(artifact: LinkageArtifact) -> dict[str, int]:
    """`candidate_id -> production_shrine_id` の使える mapping。

    consumer へ渡すのはこれだけである。`REVOKED` も曖昧な candidate も
    含まれない。artifact が無い / 不正なら空 dict。
    """
    if not artifact.is_valid:
        return {}
    return {
        candidate_id: row.production_shrine_id
        for candidate_id, row in sorted(artifact.active_linkages.items())
    }


def dump_json(artifact: LinkageArtifact) -> str:
    """決定的な診断 JSON（同一 artifact からは常に同一 bytes）。"""
    return (
        json.dumps(
            artifact.to_dict(), ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n"
    )
