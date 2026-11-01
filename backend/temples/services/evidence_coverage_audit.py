"""Evidence Coverage Audit（PR-E1、read-only）。

`docs/audit/shrine-recommendation-evidence-eligibility-audit-2026-11-01.md` §6 の
提案分類（D / H / C(axis)、VERIFIED / PARTIAL-A / PARTIAL-B / INSUFFICIENT、
軸単位 CONFLICTING）を、現DBに対して観測する唯一の計算ロジック。

このモジュールは以下を再実装しない（既存 authority へ委譲する）。

- Fact usable 判定: `evidence_gate.decide_fact_usability`
- Shared Recommendation Eligibility: `shrine_knowledge_selector.fetch_fact_ready_*`
  + `concierge_chat_candidates.is_recommendation_eligible`
- Channel B（Source Fact → registry → Need）: `channel_b_typed_need_match.fetch_typed_need_matches`
- Need → GoriyakuTag id: `need_to_goriyaku_tag_ids.NEED_TO_GORIYAKU_IDS`
- QA fixture 除外 / 母集団選択: `knowledge_coverage_report` と同じ helper

不変条件:

- DB へ書き込まない。Recommendation の挙動（eligibility / ranking / score / Reason / API）を変えない。
  本モジュールの分類は観測値であり、候補境界ではない。
- 利用者の相談文・Concierge thread / message・利用ログを一切読まない。
- 出典が追跡できないこと（provenance 欠落）を「事実として誤り」とは扱わない。
  legacy の goriyaku タグは `legacy_unattributed`（未検証）として別枠で数え、C(axis) には数えない。
- 出力は決定的（時刻・乱数・DB 実装依存の順序を含まない）。

`knowledge_coverage_report` との責務分担と、意図的な重複クエリ:

- `knowledge_coverage_report` は Knowledge の量（件数・分布・fact-ready 件数）の集計であり、
  出力の意味も形も変えない。本モジュールは「出典で追跡できるか」と相談根拠までの連鎖の観測で、
  同じ command へは混ぜない。
- 本モジュールは ShrineDeity / ShrineHistory を Source（fact-ready 以外も含む全件）付きで読む。
  Source ごとの URL / 確認日を見る必要があるため、coverage report の集計クエリは流用できない。
- そのうえで `eligible_now` は `shrine_knowledge_selector.fetch_fact_ready_*`（deity / history
  各 2 クエリ）で別に読む。行から再計算すれば省けるが、Shared Eligibility の正本を通して
  runtime と判定がずれないことを優先した、意図的な重複である（対象 Shrine 数によらず定数回）。
- Channel B は `fetch_typed_need_matches` で読み、その Source Fact を出典確認のためにもう一度
  （Source 付きで）読む。gate・registry・Need の意味は runtime の正本だけが判定する。
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from django.db.models import Prefetch, QuerySet
from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS
from temples.forms import PREF_CHOICES
from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services import evidence_gate
from temples.services.channel_b_typed_need_match import (
    fetch_typed_need_matches,
    needs_for_concept_id,
)
from temples.services.concierge_chat_candidates import is_recommendation_eligible
from temples.services.knowledge_coverage_report import _qa_filtered_shrine_ids, _resolve_scope
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)

REPORT_SCHEMA_VERSION = "1"

DATA_ORIGIN_REPOSITORY_SEED_LOCAL = "repository-seed-local"
DATA_ORIGIN_PRODUCTION_READONLY = "production-readonly"
DATA_ORIGIN_OTHER = "other"
DATA_ORIGINS = (
    DATA_ORIGIN_REPOSITORY_SEED_LOCAL,
    DATA_ORIGIN_PRODUCTION_READONLY,
    DATA_ORIGIN_OTHER,
)

CLASS_VERIFIED = "VERIFIED"
CLASS_PARTIAL_A = "PARTIAL_A"
CLASS_PARTIAL_B = "PARTIAL_B"
CLASS_INSUFFICIENT = "INSUFFICIENT"
CLASSES = (CLASS_VERIFIED, CLASS_PARTIAL_A, CLASS_PARTIAL_B, CLASS_INSUFFICIENT)

EPISTEMIC_FACT = "fact"
EPISTEMIC_TRADITION = "tradition"
EPISTEMIC_INTERPRETATION = "interpretation"
EPISTEMIC_TYPES = (EPISTEMIC_FACT, EPISTEMIC_TRADITION, EPISTEMIC_INTERPRETATION)

# H 柱に数える history_type（§6.2）。解釈・文脈系は数えない。
H_PILLAR_HISTORY_TYPES = frozenset({"official_origin", "founding", "historical_event", "tradition"})
INTERPRETIVE_HISTORY_TYPES = frozenset({"regional_context", "editorial_summary"})
TRADITION_HISTORY_TYPES = frozenset({"tradition", "official_origin"})
# 神社自身ではない一次・公的な史料。founding / historical_event をこれらの Source で
# 裏付けられた場合だけ「historical fact」とし、それ以外は神社側の伝承として扱う（§6.1）。
INDEPENDENT_HISTORICAL_SOURCE_TYPES = frozenset(
    {"government", "cultural_property", "academic", "museum_or_archive"}
)

LEGACY_PROVENANCE_LABEL = "legacy_unattributed"

PREFECTURES = tuple(value for value, _ in PREF_CHOICES if value)
_GMAPS_PREFIX_RE = re.compile(r"^日本、\s*〒?[0-9\-－]*\s*")

NEEDS = tuple(sorted(NEED_TO_GORIYAKU_IDS))


def prefecture_of(address: str | None) -> str | None:
    """住所の前方一致で都道府県を返す。解決できなければ None（推測しない）。"""
    normalized = _GMAPS_PREFIX_RE.sub("", str(address or "")).strip()
    for pref in PREFECTURES:
        if normalized.startswith(pref):
            return pref
    return None


def needs_for_goriyaku_ids(goriyaku_ids: Iterable[int]) -> list[str]:
    """GoriyakuTag id 群 → Need（Channel B と同じ `needs_for_concept_id` を使い、写像を複製しない）。"""
    needs: set[str] = set()
    for gid in goriyaku_ids:
        needs.update(needs_for_concept_id(int(gid)))
    return sorted(needs)


# ---------------------------------------------------------------------------
# 正規化された入力（DB loader とは独立。分類は純関数で行う）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceRecord:
    id: int
    source_type: str
    verification_status: str
    url: str
    bibliography: str
    has_verified_at: bool
    verified_at: str | None = None

    @property
    def attributable(self) -> bool:
        """fact-ready で、URL（または書誌）と確認日を持つ Source。"""
        return (
            self.verification_status in evidence_gate.FACT_READY_VERIFICATION_STATUSES
            and bool((self.url or "").strip() or (self.bibliography or "").strip())
            and self.has_verified_at
        )


@dataclass(frozen=True)
class FactRecord:
    kind: str  # "deity" | "history"
    id: int
    label: str
    verification_status: str
    confidence: str
    sources: tuple[SourceRecord, ...]
    history_type: str | None = None

    @property
    def usable(self) -> bool:
        return evidence_gate.decide_fact_usability(
            verification_status=self.verification_status,
            confidence=self.confidence,
            source_verification_statuses=[s.verification_status for s in self.sources],
        ).usable

    @property
    def attributable(self) -> bool:
        return self.usable and any(s.attributable for s in self.sources)

    @property
    def epistemic_type(self) -> str:
        if self.kind == "deity":
            # 祭神は「神社が祀っている」という神社側の主張（§6.1）。
            return EPISTEMIC_TRADITION
        if self.history_type in INTERPRETIVE_HISTORY_TYPES:
            return EPISTEMIC_INTERPRETATION
        if self.history_type in TRADITION_HISTORY_TYPES:
            return EPISTEMIC_TRADITION
        if any(
            s.attributable and s.source_type in INDEPENDENT_HISTORICAL_SOURCE_TYPES
            for s in self.sources
        ):
            return EPISTEMIC_FACT
        return EPISTEMIC_TRADITION


@dataclass(frozen=True)
class ConsultationMatch:
    need: str
    canonical_concept_name: str
    source_fact_key: str
    signal_type: str
    attributable: bool


@dataclass(frozen=True)
class ShrineRecord:
    id: int
    name_jp: str
    address: str
    eligible_now: bool
    deities: tuple[FactRecord, ...]
    histories: tuple[FactRecord, ...]
    consultation_matches: tuple[ConsultationMatch, ...]
    legacy_goriyaku_tags: tuple[tuple[int, str], ...]
    history_theme: str = ""
    source_fact_wordings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def identity_key(self) -> str:
        """環境間で比較するための key（DB id は環境ごとに異なるため使わない）。"""
        return f"{self.name_jp}\t{self.address}"


# ---------------------------------------------------------------------------
# 分類（純関数）
# ---------------------------------------------------------------------------


def classify_shrine(
    shrine: ShrineRecord, *, conflicted_needs: Iterable[str] = ()
) -> dict[str, Any]:
    d_pillar = any(f.attributable for f in shrine.deities)
    h_pillar = any(
        f.attributable and f.history_type in H_PILLAR_HISTORY_TYPES for f in shrine.histories
    )

    pillar_conflicts = []
    if not d_pillar and any(f.verification_status == "disputed" for f in shrine.deities):
        pillar_conflicts.append("D")
    if not h_pillar and any(
        f.verification_status == "disputed" and f.history_type in H_PILLAR_HISTORY_TYPES
        for f in shrine.histories
    ):
        pillar_conflicts.append("H")

    c_needs = sorted({m.need for m in shrine.consultation_matches if m.attributable})
    legacy_needs = needs_for_goriyaku_ids(gid for gid, _ in shrine.legacy_goriyaku_tags)
    conflicts = sorted(set(conflicted_needs))
    verified_needs = sorted(set(c_needs) - set(conflicts)) if (d_pillar and h_pillar) else []

    if not shrine.eligible_now:
        evidence_class = CLASS_INSUFFICIENT
    elif verified_needs:
        evidence_class = CLASS_VERIFIED
    elif d_pillar and h_pillar:
        evidence_class = CLASS_PARTIAL_A
    else:
        evidence_class = CLASS_PARTIAL_B

    epistemic = Counter(
        f.epistemic_type for f in (*shrine.deities, *shrine.histories) if f.attributable
    )
    return {
        "id": shrine.id,
        "name_jp": shrine.name_jp,
        "prefecture": prefecture_of(shrine.address),
        "identity_key": shrine.identity_key,
        "evidence_class": evidence_class,
        "eligible_now": shrine.eligible_now,
        "pillar_d": d_pillar,
        "pillar_h": h_pillar,
        "base_complete": shrine.eligible_now and d_pillar and h_pillar,
        "c_needs": c_needs,
        "verified_needs": verified_needs,
        "conflicting_needs": conflicts,
        "legacy_unattributed_needs": legacy_needs,
        "pillar_conflicts": pillar_conflicts,
        "disputed_fact_count": sum(
            1 for f in (*shrine.deities, *shrine.histories) if f.verification_status == "disputed"
        ),
        "attributable_fact_epistemic": {t: epistemic.get(t, 0) for t in EPISTEMIC_TYPES},
    }


def build_trace_chain(shrine: ShrineRecord, row: Mapping[str, Any]) -> dict[str, Any]:
    """Shrine -> Fact -> Source -> Consultation evidence -> Reason inputs。

    Reason inputs は Reason V4 が候補 dict から読む Knowledge / Channel A / Channel B の値で、
    Evidence Gate を通過した Fact だけを載せる（runtime と同じ）。history の本文は載せない。
    """

    def fact_entry(f: FactRecord) -> dict[str, Any]:
        return {
            "kind": f.kind,
            "fact_id": f.id,
            "label": f.label,
            "history_type": f.history_type,
            "verification_status": f.verification_status,
            "usable": f.usable,
            "attributable": f.attributable,
            "epistemic_type": f.epistemic_type,
            "sources": [
                {
                    "source_id": s.id,
                    "source_type": s.source_type,
                    "url": s.url,
                    "verified_at": s.verified_at,
                    "verification_status": s.verification_status,
                    "attributable": s.attributable,
                }
                for s in sorted(f.sources, key=lambda s: s.id)
            ],
        }

    usable_deities = [f for f in shrine.deities if f.usable]
    usable_histories = [f for f in shrine.histories if f.usable]
    return {
        "shrine": {
            "id": shrine.id,
            "name_jp": shrine.name_jp,
            "prefecture": row["prefecture"],
            "evidence_class": row["evidence_class"],
        },
        "facts": [fact_entry(f) for f in (*shrine.deities, *shrine.histories)],
        "consultation_evidence": {
            "channel_b_source_backed": [
                {
                    "need": m.need,
                    "canonical_concept_name": m.canonical_concept_name,
                    "source_fact_key": m.source_fact_key,
                    "signal_type": m.signal_type,
                    "attributable": m.attributable,
                }
                for m in sorted(
                    shrine.consultation_matches, key=lambda m: (m.need, m.source_fact_key)
                )
            ],
            "channel_a_legacy": {
                "provenance": LEGACY_PROVENANCE_LABEL,
                "note": "出典未追跡（未検証）。事実として誤りという意味ではない。",
                "tags": [name for _, name in shrine.legacy_goriyaku_tags],
                "needs": row["legacy_unattributed_needs"],
            },
            "conflicting_needs": row["conflicting_needs"],
        },
        "reason_inputs": {
            "knowledge_deity_names": [f.label for f in usable_deities],
            "knowledge_histories": [
                {
                    "history_type": f.history_type,
                    "title": f.label,
                    "epistemic_type": f.epistemic_type,
                }
                for f in usable_histories
            ],
            "history_theme": shrine.history_theme,
            "goriyaku_tag_labels": [name for _, name in shrine.legacy_goriyaku_tags],
            "channel_b_wordings": list(shrine.source_fact_wordings),
        },
    }


def aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    class_counts = Counter(r["evidence_class"] for r in rows)

    by_need: dict[str, dict[str, int]] = {}
    for need in NEEDS:
        legacy = [r for r in rows if need in r["legacy_unattributed_needs"]]
        by_need[need] = {
            "legacy_unattributed": len(legacy),
            "legacy_unattributed_and_eligible_now": sum(1 for r in legacy if r["eligible_now"]),
            "legacy_unattributed_and_base_complete": sum(1 for r in legacy if r["base_complete"]),
            "c_source_backed": sum(1 for r in rows if need in r["c_needs"]),
            "verified": sum(1 for r in rows if need in r["verified_needs"]),
            "conflicting": sum(1 for r in rows if need in r["conflicting_needs"]),
        }

    by_prefecture: dict[str, dict[str, int]] = {}
    for row in rows:
        key = row["prefecture"] or "UNRESOLVED"
        bucket = by_prefecture.setdefault(
            key,
            {"total": 0, "eligible_now": 0, "base_complete": 0, **{c: 0 for c in CLASSES}},
        )
        bucket["total"] += 1
        bucket["eligible_now"] += int(row["eligible_now"])
        bucket["base_complete"] += int(row["base_complete"])
        bucket[row["evidence_class"]] += 1

    epistemic = Counter()
    for row in rows:
        epistemic.update(row["attributable_fact_epistemic"])

    return {
        "shrine_count": len(rows),
        "class_counts": {c: class_counts.get(c, 0) for c in CLASSES},
        "eligible_now": sum(1 for r in rows if r["eligible_now"]),
        "base_complete": sum(1 for r in rows if r["base_complete"]),
        "pillar_counts": {
            "D": sum(1 for r in rows if r["pillar_d"]),
            "H": sum(1 for r in rows if r["pillar_h"]),
            "C_any_need": sum(1 for r in rows if r["c_needs"]),
        },
        "pillar_conflict_shrines": sum(1 for r in rows if r["pillar_conflicts"]),
        "axis_conflict_shrines": sum(1 for r in rows if r["conflicting_needs"]),
        "disputed_fact_shrines": sum(1 for r in rows if r["disputed_fact_count"]),
        "attributable_fact_epistemic": {t: epistemic.get(t, 0) for t in EPISTEMIC_TYPES},
        "by_need": by_need,
        "by_prefecture": dict(sorted(by_prefecture.items())),
    }


# ---------------------------------------------------------------------------
# DB loader（read-only）
# ---------------------------------------------------------------------------


def _source_record(source: ShrineKnowledgeSource) -> SourceRecord:
    return SourceRecord(
        id=source.id,
        source_type=source.source_type,
        verification_status=source.verification_status,
        url=source.url or "",
        bibliography=source.bibliography or "",
        has_verified_at=source.verified_at is not None,
        verified_at=source.verified_at.isoformat() if source.verified_at else None,
    )


def load_shrine_records(shrine_ids: list[int]) -> list[ShrineRecord]:
    """対象 Shrine を読み、分類用の正規化 record を返す（id 昇順）。書き込みはしない。"""
    if not shrine_ids:
        return []
    all_sources = Prefetch("sources", queryset=ShrineKnowledgeSource.objects.order_by("id"))

    deities: dict[int, list[FactRecord]] = defaultdict(list)
    for d in (
        ShrineDeity.objects.filter(shrine_id__in=shrine_ids)
        .order_by("shrine_id", "sort_order", "id")
        .prefetch_related(all_sources)
    ):
        deities[d.shrine_id].append(
            FactRecord(
                kind="deity",
                id=d.id,
                label=d.display_name,
                verification_status=d.verification_status,
                confidence=d.confidence,
                sources=tuple(_source_record(s) for s in d.sources.all()),
            )
        )

    histories: dict[int, list[FactRecord]] = defaultdict(list)
    for h in (
        ShrineHistory.objects.filter(shrine_id__in=shrine_ids)
        .order_by("shrine_id", "sort_order", "id")
        .prefetch_related(all_sources)
    ):
        histories[h.shrine_id].append(
            FactRecord(
                kind="history",
                id=h.id,
                label=h.title,
                verification_status=h.verification_status,
                confidence=h.confidence,
                sources=tuple(_source_record(s) for s in h.sources.all()),
                history_type=h.history_type,
            )
        )

    # Shared Recommendation Eligibility（authority をそのまま使う）。
    fr_deities = fetch_fact_ready_knowledge_deities(shrine_ids)
    fr_histories = fetch_fact_ready_knowledge_histories(shrine_ids)

    # Channel B: gate / registry / Need の意味は runtime の authority に委譲し、
    # 本監査はその Source Fact が出典追跡可能（URL + 確認日）かだけを追加で見る。
    typed = fetch_typed_need_matches(shrine_ids)
    source_facts = {
        f.stable_key: f
        for f in ShrineSourceFact.objects.filter(shrine_id__in=shrine_ids)
        .order_by("id")
        .prefetch_related(all_sources)
    }

    def source_fact_attributable(key: str, shrine_id: int) -> bool:
        """Channel B の一致を出典追跡可能として数えてよいか（fail closed）。

        - stable_key は DB で一意（`ShrineSourceFact.stable_key unique=True`）。見つからなければ不可。
        - Source Fact の所有 Shrine が一致の対象 Shrine と同じであること。
        - Source Fact 自身が fact-ready であること（runtime gate の再確認）。
        - fact-ready で URL（または書誌）と確認日を持つ Source が 1 件以上あること。
        """
        fact = source_facts.get(key)
        if fact is None or fact.shrine_id != shrine_id:
            return False
        if fact.verification_status not in evidence_gate.FACT_READY_VERIFICATION_STATUSES:
            return False
        return any(_source_record(s).attributable for s in fact.sources.all())

    records: list[ShrineRecord] = []
    for shrine in (
        Shrine.objects.filter(id__in=shrine_ids).order_by("id").prefetch_related("goriyaku_tags")
    ):
        matches = tuple(
            ConsultationMatch(
                need=m.need,
                canonical_concept_name=m.canonical_concept_name,
                source_fact_key=m.source_fact_key,
                signal_type=m.signal_type,
                attributable=source_fact_attributable(m.source_fact_key, shrine.id),
            )
            for m in typed.get(shrine.id, ())
        )
        wordings = tuple(sorted({m.source_attested_wording for m in typed.get(shrine.id, ())}))
        records.append(
            ShrineRecord(
                id=shrine.id,
                name_jp=shrine.name_jp,
                address=shrine.address or "",
                eligible_now=is_recommendation_eligible(
                    knowledge_deities=fr_deities.get(shrine.id, []),
                    knowledge_histories=fr_histories.get(shrine.id, []),
                ),
                deities=tuple(deities.get(shrine.id, [])),
                histories=tuple(histories.get(shrine.id, [])),
                consultation_matches=matches,
                legacy_goriyaku_tags=tuple(
                    sorted((t.id, t.name) for t in shrine.goriyaku_tags.all())
                ),
                history_theme=shrine.history_theme or "",
                source_fact_wordings=wordings,
            )
        )
    return records


# ---------------------------------------------------------------------------
# 軸単位の CONFLICTING 入力 / 比較
# ---------------------------------------------------------------------------


class EvidenceCoverageInputError(ValueError):
    """入力ファイル（axis conflicts / compare 対象）が契約に合わない。"""


def parse_axis_conflicts(entries: Any) -> dict[str, dict[str, str]]:
    """review 済みの軸単位 CONFLICTING を `{identity_key: {need: basis}}` にする。

    DB には「公式 Source に記載が無い」ことを表す永続 marker が無いため、軸単位の
    CONFLICTING は review 記録（例: shrine-evidence-integrity-full-audit.md の
    CANONICAL_BUT_UNSUPPORTED）から明示的に渡す。推測で補わない。
    """
    if not isinstance(entries, list):
        raise EvidenceCoverageInputError("axis conflicts must be a JSON array")
    out: dict[str, dict[str, str]] = {}
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise EvidenceCoverageInputError(f"axis conflicts[{i}]: must be an object")
        name = str(entry.get("name_jp") or "").strip()
        address = str(entry.get("address") or "").strip()
        need = str(entry.get("need") or "").strip()
        basis = str(entry.get("basis") or "").strip()
        if not name or not need or not basis:
            raise EvidenceCoverageInputError(
                f"axis conflicts[{i}]: name_jp, need and basis are required"
            )
        if need not in NEED_TO_GORIYAKU_IDS:
            raise EvidenceCoverageInputError(f"axis conflicts[{i}]: unknown need {need!r}")
        out.setdefault(f"{name}\t{address}", {})[need] = basis
    return out


def _duplicate_identity_keys(rows: Iterable[Mapping[str, Any]]) -> set[str]:
    counts = Counter(r["identity_key"] for r in rows)
    return {key for key, n in counts.items() if n > 1}


def compare_reports(current: Mapping[str, Any], other: Mapping[str, Any]) -> dict[str, Any]:
    """2つの report を identity_key（name_jp + address）で突き合わせる。

    差分は「どちらが正しいか」を判定しない。seed と Production の乖離として列挙するだけ。
    """
    if other.get("schema_version") != current.get("schema_version"):
        raise EvidenceCoverageInputError(
            f"schema_version mismatch: current={current.get('schema_version')!r} "
            f"other={other.get('schema_version')!r}"
        )
    # 同じ identity_key（name_jp + address）を持つ行が複数ある場合は、黙って1行へ潰さない。
    # 突き合わせ対象から外し、duplicate_identity_keys として明示する（identity 監査の対象）。
    cur_dups = _duplicate_identity_keys(current["shrines"])
    oth_dups = _duplicate_identity_keys(other["shrines"])
    cur = {r["identity_key"]: r for r in current["shrines"] if r["identity_key"] not in cur_dups}
    oth = {r["identity_key"]: r for r in other["shrines"] if r["identity_key"] not in oth_dups}
    fields = ("evidence_class", "eligible_now", "pillar_d", "pillar_h", "c_needs")
    changed = []
    for key in sorted(cur.keys() & oth.keys()):
        diffs = {
            f: {"other": oth[key][f], "current": cur[key][f]}
            for f in fields
            if oth[key][f] != cur[key][f]
        }
        if diffs:
            changed.append({"identity_key": key, "differences": diffs})
    cur_counts = current["summary"]["class_counts"]
    oth_counts = other["summary"]["class_counts"]
    return {
        "other_data_origin": other.get("data_origin"),
        "duplicate_identity_keys": {
            "current": sorted(cur_dups),
            "other": sorted(oth_dups),
        },
        "only_in_current": sorted(cur.keys() - oth.keys() - oth_dups),
        "only_in_other": sorted(oth.keys() - cur.keys() - cur_dups),
        "changed": changed,
        "class_count_delta": {c: cur_counts.get(c, 0) - oth_counts.get(c, 0) for c in CLASSES},
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_evidence_coverage_report(
    *,
    data_origin: str,
    shrine_ids: Iterable[int] | QuerySet | None = None,
    axis_conflicts: Mapping[str, Mapping[str, str]] | None = None,
    trace_per_class: int = 1,
    trace_shrine_ids: Sequence[int] = (),
) -> dict[str, Any]:
    if data_origin not in DATA_ORIGINS:
        raise EvidenceCoverageInputError(f"unknown data_origin {data_origin!r}")
    axis_conflicts = axis_conflicts or {}

    scope_mode, target_ids = _resolve_scope(shrine_ids, default_ids=_qa_filtered_shrine_ids())
    records = load_shrine_records(sorted(set(target_ids)))
    rows = [
        classify_shrine(r, conflicted_needs=axis_conflicts.get(r.identity_key, {}).keys())
        for r in records
    ]
    by_id = {r.id: (r, row) for r, row in zip(records, rows, strict=True)}

    trace_ids: list[int] = []
    for cls in CLASSES:
        trace_ids.extend(
            [row["id"] for row in rows if row["evidence_class"] == cls][:trace_per_class]
        )
    trace_ids.extend(int(i) for i in trace_shrine_ids)
    trace_ids = list(dict.fromkeys(i for i in trace_ids if i in by_id))

    matched_conflict_keys = {r.identity_key for r in records} & set(axis_conflicts)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report": "evidence_coverage_audit",
        "data_origin": data_origin,
        "scope": {
            "mode": scope_mode,
            "requested_count": len(target_ids),
            "resolved_in_db": len(records),
        },
        "axis_conflict_input": {
            "supplied_entries": sum(len(v) for v in axis_conflicts.values()),
            "unmatched_identity_keys": sorted(set(axis_conflicts) - matched_conflict_keys),
        },
        "definitions": {
            "D": "attributable usable ShrineDeity (fact-ready Source with url/bibliography and verified_at)",
            "H": "attributable usable ShrineHistory with history_type in "
            + ",".join(sorted(H_PILLAR_HISTORY_TYPES)),
            "C(need)": "Channel B typed need match whose ShrineSourceFact has an attributable Source",
            "legacy_unattributed": "goriyaku_tags mapped to needs; provenance not traceable, NOT counted as C, NOT implied false",
            "classification_is_observation_only": True,
        },
        "summary": aggregate(rows),
        "shrines": rows,
        "trace_chains": [build_trace_chain(by_id[i][0], by_id[i][1]) for i in trace_ids],
    }


__all__ = [
    "CLASSES",
    "DATA_ORIGINS",
    "DATA_ORIGIN_PRODUCTION_READONLY",
    "DATA_ORIGIN_REPOSITORY_SEED_LOCAL",
    "EvidenceCoverageInputError",
    "REPORT_SCHEMA_VERSION",
    "build_evidence_coverage_report",
    "classify_shrine",
    "compare_reports",
    "parse_axis_conflicts",
    "prefecture_of",
]
