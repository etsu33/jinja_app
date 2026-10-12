"""Shared Recommendation Eligibilityのread-only検証サービス。

W0-DB01 CORE READY Gate（`docs/audit/shrine-expansion-wave0-db01-core-ready-gate.md`
§9.1）で手動実行したper-shrine eligibility確認を、再利用可能かつ決定的な形へ
置き換える。同Auditは「再利用可能な automated read-only verifier はまだ存在しない。
W0-DB02 前の Pipeline Hardening task として分離する」と記録している。

判定式は**一切再実装しない**。既存authorityへ委譲する。

    temples.services.concierge_chat_candidates.is_recommendation_eligible
        （Shared Recommendation Eligibilityの唯一の判定式）
    temples.services.shrine_knowledge_selector
        .fetch_fact_ready_knowledge_deities() / _histories()
            -> temples.services.evidence_gate.decide_fact_usability()

契約（`docs/knowledge/recommendation-eligibility-contract.md`）:

    Shrine DB presence != Recommendation eligibility
    Recommendation eligibility = usable Deity Fact または usable History Fact が
                                 少なくとも1件存在すること

本モジュールはDBへの書き込みを一切行わない（read-only）。Recommendation
eligibility rule、Evidence Gate条件、Ranking / Scoreのいずれも変更しない。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from django.conf import settings

from temples.models import Shrine
from temples.services.concierge_chat_candidates import is_recommendation_eligible
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)

ELIGIBLE = "ELIGIBLE"
INELIGIBLE = "INELIGIBLE"
UNRESOLVED = "UNRESOLVED"

CANDIDATE_MASTER_RELATIVE_PATH = Path("temples") / "data" / "shrine_expansion_candidate_master.json"
NATIONWIDE_IDENTITY_MANIFEST_RELATIVE_PATH = (
    Path("temples") / "data" / "shrine_expansion_nationwide_identity_manifest.json"
)


@dataclass(frozen=True)
class ShrineIdentity:
    """Candidate Masterのcanonical identity。

    Shrineは `(name_jp, address, location)` がuniqueであり、`name_jp` 単独では
    同名別所在の神社を一意に特定できない。Batch解決では Candidate Master の
    `(official_name, official_address)` を canonical identity として用いる。
    """

    name: str
    address: str

    def label(self) -> str:
        return f"{self.name} / {self.address}"


@dataclass(frozen=True)
class ShrineEligibilityResult:
    """1 Shrineあたりの検証結果。

    `status` が `UNRESOLVED` の場合、そのidentityはProduction Shrineへ解決できて
    いない。eligibilityを主張できないため、ELIGIBLE / INELIGIBLE のいずれとしても
    扱わない（eligible側へ混ぜない）。
    """

    requested: str
    status: str
    shrine_id: int | None = None
    name_jp: str | None = None
    usable_deity_fact_count: int = 0
    usable_history_fact_count: int = 0
    note: str | None = None

    @property
    def usable_fact_count(self) -> int:
        return self.usable_deity_fact_count + self.usable_history_fact_count

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "status": self.status,
            "shrine_id": self.shrine_id,
            "name_jp": self.name_jp,
            "usable_deity_fact_count": self.usable_deity_fact_count,
            "usable_history_fact_count": self.usable_history_fact_count,
            "usable_fact_count": self.usable_fact_count,
            "note": self.note,
        }


@dataclass(frozen=True)
class EligibilityVerificationReport:
    results: list[ShrineEligibilityResult] = field(default_factory=list)

    @property
    def eligible_count(self) -> int:
        return sum(1 for r in self.results if r.status == ELIGIBLE)

    @property
    def ineligible_count(self) -> int:
        return sum(1 for r in self.results if r.status == INELIGIBLE)

    @property
    def unresolved_count(self) -> int:
        return sum(1 for r in self.results if r.status == UNRESOLVED)

    @property
    def all_eligible(self) -> bool:
        """全要求identityがELIGIBLEであるか。

        UNRESOLVEDが1件でもあればFalse（解決できないidentityをPASSにしない）。
        """
        return bool(self.results) and all(r.status == ELIGIBLE for r in self.results)

    def summary_counts(self) -> tuple[int, int, int]:
        """(ELIGIBLE, INELIGIBLE, UNRESOLVED) の件数。"""
        return (self.eligible_count, self.ineligible_count, self.unresolved_count)

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "requested_count": len(self.results),
                "eligible_count": self.eligible_count,
                "ineligible_count": self.ineligible_count,
                "unresolved_count": self.unresolved_count,
                "all_eligible": self.all_eligible,
            },
            "results": [r.as_dict() for r in self.results],
        }


def _candidate_master_path() -> Path:
    return Path(settings.BASE_DIR) / CANDIDATE_MASTER_RELATIVE_PATH


def load_batch_shrine_identities(
    build_batch: str, *, path: Path | None = None
) -> list[ShrineIdentity]:
    """Candidate Masterから指定`build_batch`のcanonical identityを読み出す（read-only）。

    `(official_name, official_address)` を identity として返す。`name_jp` 単独では
    同名別所在の神社を一意に特定できないため、name-only解決は行わない。

    `official_name` / `official_address` のいずれかが欠けるCandidateは、canonical
    identityが確定していないため**含めない**（推測で`candidate_name`等へ代替しない）。
    欠落は呼び出し側が件数差として検知できる。

    Candidate Masterは本番Shrine DBではないため、ここで得られるのは「そのBatchが
    対象とするidentity」であって、eligibilityでもProduction存在保証でもない。
    """
    master_path = path or _candidate_master_path()
    if not master_path.is_file():
        raise FileNotFoundError(f"candidate master not found: {master_path}")

    payload = json.loads(master_path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(candidates, list):
        raise ValueError(f"unexpected candidate master shape: {master_path}")

    identities: list[ShrineIdentity] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("build_batch") != build_batch:
            continue
        name = candidate.get("official_name")
        address = candidate.get("official_address")
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(address, str) or not address.strip():
            continue
        identities.append(ShrineIdentity(name=name.strip(), address=address.strip()))
    return identities


def count_batch_candidates(build_batch: str, *, path: Path | None = None) -> int:
    """指定`build_batch`のCandidate総数（canonical identity欠落分を含む）。"""
    master_path = path or _candidate_master_path()
    if not master_path.is_file():
        raise FileNotFoundError(f"candidate master not found: {master_path}")
    payload = json.loads(master_path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(candidates, list):
        raise ValueError(f"unexpected candidate master shape: {master_path}")
    return sum(
        1
        for c in candidates
        if isinstance(c, dict) and c.get("build_batch") == build_batch
    )


# --- Nationwide handoff identity（G-6） -----------------------------------------------------
#
# Nationwide Candidate Master 行は official_name / official_address を持たず build_batch = null
# のため、`--batch` 経路では解決できない。Nationwide handoff の verifier identity は専用 manifest
# （temples/data/shrine_expansion_nationwide_identity_manifest.json）が持つ。
#
# manifest は reviewed canonical identity の exact 文字列だけを保持する（H001 は
# docs/audit/niigata-h001-g6-verifier-identity-decision.md、H002 は各 G1 audit）。
# 本 loader は文字列を正規化・補完・推論せず、Candidate Master と照合して fail closed する。
# DB へのアクセスは行わない。identity の存在は eligibility を意味しない。

NATIONWIDE_MANIFEST_SCHEMA_VERSION = 1
_MANIFEST_FIELDS = frozenset({"schema_version", "purpose", "handoffs"})
_HANDOFF_FIELDS = frozenset({"handoff_id", "members"})
_MEMBER_FIELDS = frozenset(
    {"candidate_id", "source_position", "name", "address", "identity_evidence"}
)
_EVIDENCE_FIELDS = frozenset({"verifier_identity_authority", "g1_identity_audit"})
_HANDOFF_ID_RE = re.compile(r"^[A-Z]+-[0-9]{3}-H[0-9]{3}$")
_NATIONWIDE_ID_RE = re.compile(r"^nsrc-[0-9]{6}$")
_SOURCE_POSITION_RE = re.compile(r"^page[0-9]{3}-row[0-9]{3}$")
_EVIDENCE_PATH_RE = re.compile(r"^docs/audit/[A-Za-z0-9_\-]+(?:/[A-Za-z0-9_\-]+)*\.md$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f\u2028\u2029]")


class HandoffIdentityError(ValueError):
    """Nationwide handoff identity manifest が不正、または Candidate Master と一致しない。"""


def _nationwide_identity_manifest_path() -> Path:
    return Path(settings.BASE_DIR) / NATIONWIDE_IDENTITY_MANIFEST_RELATIVE_PATH


def _exact_fields(obj: Any, expected: frozenset[str], where: str) -> dict:
    if not isinstance(obj, dict):
        raise HandoffIdentityError(f"{where}: must be an object")
    missing = sorted(expected - obj.keys())
    unknown = sorted(obj.keys() - expected)
    if missing:
        raise HandoffIdentityError(f"{where}: missing field(s) {missing}")
    if unknown:
        raise HandoffIdentityError(f"{where}: unknown field(s) {unknown}")
    return obj


def _exact_text(value: Any, where: str) -> str:
    # 文字列は検査するだけで、strip / 正規化はしない（exact identity をそのまま使う）。
    if not isinstance(value, str) or not value:
        raise HandoffIdentityError(f"{where}: must be a non-empty string")
    if value != value.strip() or _CONTROL_RE.search(value):
        raise HandoffIdentityError(
            f"{where}: must not have surrounding whitespace or control chars"
        )
    return value


def _cross_check_candidate_master(handoff_id: str, members: list, candidates: list) -> None:
    """Candidate Master の membership / order / provenance / G1 status / boundary を照合する。"""
    rows = [
        row
        for row in candidates
        if isinstance(row, dict)
        and (row.get("admission_provenance") or {}).get("handoff_id") == handoff_id
    ]
    want_ids = [member["candidate_id"] for member in members]
    have_ids = [row.get("candidate_id") for row in rows]
    if have_ids != want_ids:
        raise HandoffIdentityError(
            f"{handoff_id}: Candidate Master members {have_ids} != manifest {want_ids}"
        )
    for member, row in zip(members, rows, strict=True):
        cid = member["candidate_id"]
        provenance = row.get("admission_provenance") or {}
        if provenance.get("source_position") != member["source_position"]:
            raise HandoffIdentityError(f"{cid}: source_position differs from Candidate Master")
        if row.get("candidate_name") != member["name"]:
            raise HandoffIdentityError(f"{cid}: name differs from Candidate Master candidate_name")
        if row.get("identity_status") != "CONFIRMED":
            raise HandoffIdentityError(f"{cid}: Candidate Master identity_status is not CONFIRMED")
        if row.get("build_batch") is not None:
            raise HandoffIdentityError(
                f"{cid}: Nationwide Candidate Master build_batch must be null"
            )
        if {"official_name", "official_address"} & row.keys():
            raise HandoffIdentityError(
                f"{cid}: Candidate Master must not carry official_* identity"
            )


def validate_nationwide_identity_manifest(manifest: Any, candidate_master: Any) -> None:
    """manifest を schema と Candidate Master に照らして検証する（fail closed、pure）。"""
    _exact_fields(manifest, _MANIFEST_FIELDS, "manifest")
    version = manifest["schema_version"]
    if version != NATIONWIDE_MANIFEST_SCHEMA_VERSION or isinstance(version, bool):
        raise HandoffIdentityError(
            f"manifest.schema_version: must be {NATIONWIDE_MANIFEST_SCHEMA_VERSION}"
        )
    _exact_text(manifest["purpose"], "manifest.purpose")
    handoffs = manifest["handoffs"]
    if not isinstance(handoffs, list) or not handoffs:
        raise HandoffIdentityError("manifest.handoffs: must be a non-empty list")

    candidates = candidate_master.get("candidates") if isinstance(candidate_master, dict) else None
    if not isinstance(candidates, list):
        raise HandoffIdentityError("candidate master: unexpected shape")

    handoff_ids: list[str] = []
    candidate_ids: list[str] = []
    identities: list[tuple[str, str]] = []
    for h_index, handoff in enumerate(handoffs):
        hwhere = f"manifest.handoffs[{h_index}]"
        _exact_fields(handoff, _HANDOFF_FIELDS, hwhere)
        handoff_id = handoff["handoff_id"]
        if not isinstance(handoff_id, str) or not _HANDOFF_ID_RE.fullmatch(handoff_id):
            raise HandoffIdentityError(f"{hwhere}.handoff_id: invalid {handoff_id!r}")
        handoff_ids.append(handoff_id)
        members = handoff["members"]
        if not isinstance(members, list) or not members:
            raise HandoffIdentityError(f"{hwhere}.members: must be a non-empty list")
        for m_index, member in enumerate(members):
            mwhere = f"{hwhere}.members[{m_index}]"
            _exact_fields(member, _MEMBER_FIELDS, mwhere)
            if not isinstance(member["candidate_id"], str) or not _NATIONWIDE_ID_RE.fullmatch(
                member["candidate_id"]
            ):
                raise HandoffIdentityError(f"{mwhere}.candidate_id: invalid")
            if not isinstance(member["source_position"], str) or not _SOURCE_POSITION_RE.fullmatch(
                member["source_position"]
            ):
                raise HandoffIdentityError(f"{mwhere}.source_position: invalid")
            name = _exact_text(member["name"], f"{mwhere}.name")
            address = _exact_text(member["address"], f"{mwhere}.address")
            evidence = _exact_fields(
                member["identity_evidence"], _EVIDENCE_FIELDS, f"{mwhere}.identity_evidence"
            )
            for key in sorted(_EVIDENCE_FIELDS):
                ref = evidence[key]
                if not isinstance(ref, str) or not _EVIDENCE_PATH_RE.fullmatch(ref):
                    raise HandoffIdentityError(
                        f"{mwhere}.identity_evidence.{key}: invalid reference"
                    )
            candidate_ids.append(member["candidate_id"])
            identities.append((name, address))

        _cross_check_candidate_master(handoff_id, members, candidates)

    for label, values in (
        ("handoff_id", handoff_ids),
        ("candidate_id", candidate_ids),
        ("exact (name, address)", identities),
    ):
        duplicated = sorted({str(v) for v in values if values.count(v) > 1})
        if duplicated:
            raise HandoffIdentityError(f"manifest: duplicate {label} {duplicated}")


def load_handoff_shrine_identities(
    handoff_id: str,
    *,
    manifest_path: Path | None = None,
    candidate_master_path: Path | None = None,
) -> list[ShrineIdentity]:
    """Nationwide handoff の exact canonical identity を handoff 順で返す（read-only、DB 不使用）。

    manifest 全体を検証し Candidate Master と照合してから、指定 handoff の members を
    `ShrineIdentity(name, address)` として返す。不明な handoff / 空 handoff / 重複 / Candidate
    Master との不一致はすべて HandoffIdentityError。identity があることは eligibility を意味しない。
    """
    manifest_file = manifest_path or _nationwide_identity_manifest_path()
    master_file = candidate_master_path or _candidate_master_path()
    for path in (manifest_file, master_file):
        if not Path(path).is_file():
            raise HandoffIdentityError(f"file not found: {path}")
    try:
        manifest = json.loads(Path(manifest_file).read_text(encoding="utf-8"))
        candidate_master = json.loads(Path(master_file).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HandoffIdentityError(f"invalid JSON: {exc}") from exc
    validate_nationwide_identity_manifest(manifest, candidate_master)
    matches = [h for h in manifest["handoffs"] if h["handoff_id"] == handoff_id]
    if len(matches) != 1:
        raise HandoffIdentityError(f"unknown handoff {handoff_id!r}")
    return [ShrineIdentity(name=m["name"], address=m["address"]) for m in matches[0]["members"]]


def _resolve_identities(
    *,
    shrine_ids: Iterable[int],
    shrine_names: Iterable[str],
    shrine_identities: Iterable[ShrineIdentity],
) -> list[tuple[str, Shrine | None, str | None]]:
    """要求identityをProduction Shrineへ解決する（read-only）。

    戻り値は (requested, shrine|None, note) のlist。要求順を保持する。

    解決方式は3種類あり、いずれも推測解決をしない。

    - `shrine_ids`: Shrine idで一意に解決する
    - `shrine_identities`: canonical identity `(name_jp, address)` で解決する
    - `shrine_names`: `name_jp` のみで解決する。同名が複数ある場合はUNRESOLVED
      （どれか1件を推測で採用しない）
    """
    resolved: list[tuple[str, Shrine | None, str | None]] = []

    id_list = list(dict.fromkeys(shrine_ids))
    identity_list = list(dict.fromkeys(shrine_identities))
    name_list = list(dict.fromkeys(shrine_names))

    by_id = {s.id: s for s in Shrine.objects.filter(id__in=id_list)} if id_list else {}
    for shrine_id in id_list:
        shrine = by_id.get(shrine_id)
        note = None if shrine else "shrine id not found in Production Shrine table"
        resolved.append((str(shrine_id), shrine, note))

    if identity_list:
        identity_names = {identity.name for identity in identity_list}
        by_identity: dict[tuple[str, str], list[Shrine]] = {}
        for shrine in Shrine.objects.filter(name_jp__in=identity_names):
            by_identity.setdefault((shrine.name_jp, shrine.address), []).append(shrine)
        for identity in identity_list:
            found = by_identity.get((identity.name, identity.address)) or []
            if len(found) == 1:
                resolved.append((identity.label(), found[0], None))
            elif not found:
                resolved.append(
                    (
                        identity.label(),
                        None,
                        "(name_jp, address) not found in Production Shrine table",
                    )
                )
            else:
                ids = ", ".join(str(s.id) for s in sorted(found, key=lambda s: s.id))
                resolved.append(
                    (
                        identity.label(),
                        None,
                        f"(name_jp, address) matched multiple shrines (ids: {ids}); not resolved",
                    )
                )

    if name_list:
        matches: dict[str, list[Shrine]] = {name: [] for name in name_list}
        for shrine in Shrine.objects.filter(name_jp__in=name_list):
            matches.setdefault(shrine.name_jp, []).append(shrine)
        for name in name_list:
            found = matches.get(name) or []
            if len(found) == 1:
                resolved.append((name, found[0], None))
            elif not found:
                resolved.append((name, None, "name_jp not found in Production Shrine table"))
            else:
                ids = ", ".join(str(s.id) for s in sorted(found, key=lambda s: s.id))
                resolved.append(
                    (name, None, f"name_jp matched multiple shrines (ids: {ids}); not resolved")
                )

    return resolved


def verify_recommendation_eligibility(
    *,
    shrine_ids: Iterable[int] = (),
    shrine_names: Iterable[str] = (),
    shrine_identities: Iterable[ShrineIdentity] = (),
) -> EligibilityVerificationReport:
    """指定Shrineのeligibilityをread-onlyで検証する。

    判定は`is_recommendation_eligible()`へ委譲し、usable Factの取得は
    `shrine_knowledge_selector`（内部でEvidence Gate）へ委譲する。本関数は
    新しいeligibility ruleを定義しない。

    出力にはEvidence件数（usable Deity Fact数 / usable History Fact数）を含める。
    これは結果を説明するための最小限の根拠であり、閾値判定には使用しない。
    """
    resolved = _resolve_identities(
        shrine_ids=shrine_ids,
        shrine_names=shrine_names,
        shrine_identities=shrine_identities,
    )

    found_ids = [shrine.id for _, shrine, _ in resolved if shrine is not None]
    deities_by_shrine = fetch_fact_ready_knowledge_deities(found_ids) if found_ids else {}
    histories_by_shrine = fetch_fact_ready_knowledge_histories(found_ids) if found_ids else {}

    results: list[ShrineEligibilityResult] = []
    for requested, shrine, note in resolved:
        if shrine is None:
            results.append(
                ShrineEligibilityResult(requested=requested, status=UNRESOLVED, note=note)
            )
            continue

        deities = deities_by_shrine.get(shrine.id, [])
        histories = histories_by_shrine.get(shrine.id, [])
        eligible = is_recommendation_eligible(
            knowledge_deities=deities,
            knowledge_histories=histories,
        )
        results.append(
            ShrineEligibilityResult(
                requested=requested,
                status=ELIGIBLE if eligible else INELIGIBLE,
                shrine_id=shrine.id,
                name_jp=shrine.name_jp,
                usable_deity_fact_count=len(deities),
                usable_history_fact_count=len(histories),
            )
        )

    return EligibilityVerificationReport(results=results)


def render_text_report(report: EligibilityVerificationReport) -> str:
    lines = [
        "Shared Recommendation Eligibility Verification (read-only)",
        "authority: docs/knowledge/recommendation-eligibility-contract.md",
        "",
    ]
    width = max((len(r.requested) for r in report.results), default=9)
    for result in report.results:
        if result.status == UNRESOLVED:
            lines.append(f"{result.requested:<{width}}  {result.status:<10}  {result.note or ''}")
            continue
        lines.append(
            f"{result.requested:<{width}}  {result.status:<10}  "
            f"id={result.shrine_id}  "
            f"usable_deity={result.usable_deity_fact_count}  "
            f"usable_history={result.usable_history_fact_count}"
        )
    lines += [
        "",
        f"requested  = {len(report.results)}",
        f"ELIGIBLE   = {report.eligible_count}",
        f"INELIGIBLE = {report.ineligible_count}",
        f"UNRESOLVED = {report.unresolved_count}",
        f"ALL_ELIGIBLE = {'PASS' if report.all_eligible else 'FAIL'}",
    ]
    return "\n".join(lines)
