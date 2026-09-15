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
