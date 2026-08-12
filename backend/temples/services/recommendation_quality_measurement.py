"""Knowledge推薦理由 品質Baseline計測（read-only）。

docs/audit/knowledge-recommendation-quality-audit.mdで定義した
FULLY_KNOWLEDGE_BACKED / PARTIALLY_KNOWLEDGE_BACKED / LEGACY_BACKED / UNKNOWN
の4分類を、実際のRecommendation Reason生成ロジックと完全に同一の判定で
再現可能な計測へ落とし込む。

このモジュールは以下を再実装しない（既存contractをそのまま利用する）。

- Knowledge Fact取得・Fact-ready判定
  （temples.services.shrine_knowledge_selector / evidence_gateへ委譲）
- Knowledge優先・Legacy fallbackの合成ロジック
  （temples.services.concierge_chat._build_score_v3_candidate_profileへ委譲）
- confidenceに基づく表現強度判定・suppression
  （temples.services.recommendation_reason_v4._build_factへ委譲）
- QA fixture Shrineの除外条件
  （temples.services.shrine_qa_fixture_exclusion.exclude_qa_fixture_shrinesへ委譲）

DBへの書き込みは一切行わない。Recommendation Candidate / Ranking / Score /
Reason生成・Action Suggestionのいずれも変更しない（read-only observer）。

## history_theme名称衝突ガード

docs/audit/knowledge-recommendation-quality-audit.md 4.2で確認した通り、
`Shrine.history_theme`（Legacy分類タグ）とKnowledge（`ShrineHistory`モデル、
`shrine_history`フィールド）は名前が似ているだけの別物である。本モジュールの
分類は`deity`/`shrine_history`フィールドのみを対象とし、`history_theme`は
一切参照しない（`_build_score_v3_candidate_profile`・`_build_fact`いずれも
`history_theme`を`fact["history_theme"]`として保持するが、分類判定には
使わない）。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

from temples.models import Shrine, ShrineDeity, ShrineHistory
from temples.services import evidence_gate
from temples.services.concierge_chat import _build_score_v3_candidate_profile
from temples.services.recommendation_reason_v4 import _build_fact
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines

FieldStatus = Literal["KNOWLEDGE_USED", "LEGACY_USED", "EMPTY"]
Classification = Literal[
    "FULLY_KNOWLEDGE_BACKED",
    "PARTIALLY_KNOWLEDGE_BACKED",
    "LEGACY_BACKED",
    "UNKNOWN",
]


@dataclass(frozen=True)
class ShrineReasonProvenance:
    """1神社分の、Recommendation Reasonが実際に使用したFactの由来。"""

    shrine_id: int
    name: str
    deity_status: FieldStatus
    history_status: FieldStatus
    classification: Classification


def _field_status(*, confidence_is_knowledge: bool, fact_value: Any) -> FieldStatus:
    """fieldの最終可視状態から由来を判定する。

    confidence_is_knowledge=True でも fact_value が None（低confidenceで
    suppressされた、またはそもそも値がない）場合はEMPTYとする。
    「Knowledgeが存在したが表示されなかった」ことと「Legacyが使われた」ことを
    混同しないための区別（suppressed Knowledge Factは"Legacy扱い"にしない）。
    """
    if fact_value is None:
        return "EMPTY"
    return "KNOWLEDGE_USED" if confidence_is_knowledge else "LEGACY_USED"


def classify_provenance(
    deity_status: FieldStatus, history_status: FieldStatus
) -> Classification:
    """deity/history 2フィールドの由来からshrine単位の分類を決定する。

    FULLY_KNOWLEDGE_BACKED: 少なくとも一方がKNOWLEDGE_USEDで、LEGACY_USEDがない
    PARTIALLY_KNOWLEDGE_BACKED: KNOWLEDGE_USEDとLEGACY_USEDが両方ある
    LEGACY_BACKED: LEGACY_USEDのみ（KNOWLEDGE_USEDがない）
    UNKNOWN: 両方EMPTY（由来を判定する材料がない）
    """
    statuses = (deity_status, history_status)
    knowledge_used = "KNOWLEDGE_USED" in statuses
    legacy_used = "LEGACY_USED" in statuses

    if knowledge_used and legacy_used:
        return "PARTIALLY_KNOWLEDGE_BACKED"
    if knowledge_used:
        return "FULLY_KNOWLEDGE_BACKED"
    if legacy_used:
        return "LEGACY_BACKED"
    return "UNKNOWN"


def build_shrine_reason_provenance(candidate: dict[str, Any]) -> ShrineReasonProvenance:
    """1候補dict（build_chat_candidates()と同一shape）からprovenanceを構築する。

    実際のReason生成と同一の関数（_build_score_v3_candidate_profile /
    _build_fact）をそのまま呼び出す。計測のためだけに合成・suppressionロジックを
    再実装しない（実装の重複によるdriftを避けるため、意図的に"private"関数を
    直接importしている）。
    """
    candidate_profile = _build_score_v3_candidate_profile(candidate)
    fact, _reason_strength = _build_fact(candidate_profile, meaning_translation={})

    deity_status = _field_status(
        confidence_is_knowledge=candidate_profile.get("deity_confidence") is not None,
        fact_value=fact.get("deity"),
    )
    history_status = _field_status(
        confidence_is_knowledge=candidate_profile.get("shrine_history_confidence") is not None,
        fact_value=fact.get("shrine_history"),
    )

    shrine_id = candidate.get("shrine_id") or candidate.get("id")
    return ShrineReasonProvenance(
        shrine_id=int(shrine_id) if shrine_id is not None else 0,
        name=str(candidate.get("name") or ""),
        deity_status=deity_status,
        history_status=history_status,
        classification=classify_provenance(deity_status, history_status),
    )


def aggregate_measurements(records: list[ShrineReasonProvenance]) -> dict[str, Any]:
    """provenance一覧からBaseline指標を集計する。

    UNKNOWNの扱い: 全rateの分母は"分類可能な"件数ではなく、常にsample_count
    （測定対象の全件）とする。UNKNOWNを分母から除外すると
    knowledge_backed_rateが実態より高く見える（一部の神社にデータが
    存在しないという事実を無視した楽観的な数値になる）ため、保守的に
    sample_countを分母として固定する。
    """
    total = len(records)
    counts = Counter(r.classification for r in records)

    def rate(n: int) -> float:
        return round(n / total, 4) if total else 0.0

    fully = counts.get("FULLY_KNOWLEDGE_BACKED", 0)
    partially = counts.get("PARTIALLY_KNOWLEDGE_BACKED", 0)
    legacy = counts.get("LEGACY_BACKED", 0)
    unknown = counts.get("UNKNOWN", 0)

    deity_knowledge_used = sum(1 for r in records if r.deity_status == "KNOWLEDGE_USED")
    history_knowledge_used = sum(1 for r in records if r.history_status == "KNOWLEDGE_USED")
    deity_legacy_used = sum(1 for r in records if r.deity_status == "LEGACY_USED")
    history_legacy_used = sum(1 for r in records if r.history_status == "LEGACY_USED")

    return {
        "sample_count": total,
        "fully_knowledge_backed": fully,
        "partially_knowledge_backed": partially,
        "legacy_backed": legacy,
        "unknown": unknown,
        "fully_knowledge_backed_rate": rate(fully),
        "partially_knowledge_backed_rate": rate(partially),
        "legacy_backed_rate": rate(legacy),
        "unknown_rate": rate(unknown),
        # numerator: FULLY + PARTIALLY. denominator: sample_count（UNKNOWN含む）。
        "knowledge_backed_rate": rate(fully + partially),
        "deity_knowledge_usage_rate": rate(deity_knowledge_used),
        "history_knowledge_usage_rate": rate(history_knowledge_used),
        "deity_legacy_fallback_rate": rate(deity_legacy_used),
        "history_legacy_fallback_rate": rate(history_legacy_used),
    }


def _audit_target_shrine_ids() -> list[int]:
    return list(exclude_qa_fixture_shrines(Shrine.objects.all()).values_list("id", flat=True))


def _build_candidates_for_measurement(shrine_ids: list[int]) -> list[dict[str, Any]]:
    """build_chat_candidates()と同一shapeの最小candidate dictを構築する。

    Ranking/距離/goriyaku一致等の計測に不要な処理は行わない
    （read-only observerとしての責務を最小限に保つ）。
    """
    shrines = list(Shrine.objects.filter(id__in=shrine_ids).only(
        "id", "name_jp", "name_romaji", "sajin", "description"
    ))
    knowledge_deities_by_shrine = fetch_fact_ready_knowledge_deities(shrine_ids)
    knowledge_histories_by_shrine = fetch_fact_ready_knowledge_histories(shrine_ids)

    candidates: list[dict[str, Any]] = []
    for s in shrines:
        candidates.append(
            {
                "id": s.id,
                "shrine_id": s.id,
                "name": s.name_jp or s.name_romaji,
                "sajin": s.sajin,
                "description": s.description,
                "knowledge_deities": knowledge_deities_by_shrine.get(s.id, []),
                "knowledge_histories": knowledge_histories_by_shrine.get(s.id, []),
            }
        )
    return candidates


def _source_confirmed_fact_rate(shrine_ids: list[int]) -> dict[str, Any]:
    """Fact-ready（source_confirmed/reviewed）Deity+History中、source_confirmedの割合。

    shrine単位のprovenance分類とは別軸の、Fact単位の集計であることに注意
    （分母は「そのshrineのreasonで実際に採用されたFact数」ではなく、
    「対象shrine群に存在するFact-ready Deity+History総数」）。
    """
    status_counter: Counter[str] = Counter()
    for model in (ShrineDeity, ShrineHistory):
        status_counter.update(
            model.objects.filter(
                shrine_id__in=shrine_ids,
                verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES,
            ).values_list("verification_status", flat=True)
        )

    total_fact_ready = sum(status_counter.values())
    source_confirmed = status_counter.get("source_confirmed", 0)
    rate = round(source_confirmed / total_fact_ready, 4) if total_fact_ready else 0.0
    return {
        "fact_ready_total": total_fact_ready,
        "source_confirmed_count": source_confirmed,
        "source_confirmed_fact_rate": rate,
        "verification_status_distribution": dict(sorted(status_counter.items())),
    }


def build_recommendation_quality_measurement_report(
    shrine_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Baseline計測レポートをdictで返す（read-only、DB書き込みなし）。

    shrine_idsを指定しない場合はQA fixtureを除外した全Shrineを対象にする
    （knowledge_coverage_reportと同一の対象定義を共有する）。
    """
    target_ids = shrine_ids if shrine_ids is not None else _audit_target_shrine_ids()

    candidates = _build_candidates_for_measurement(target_ids)
    records = [build_shrine_reason_provenance(c) for c in candidates]

    report = aggregate_measurements(records)
    report["source_confirmed_fact"] = _source_confirmed_fact_rate(target_ids)
    report["classification_by_shrine"] = [
        {
            "shrine_id": r.shrine_id,
            "name": r.name,
            "deity_status": r.deity_status,
            "history_status": r.history_status,
            "classification": r.classification,
        }
        for r in records
    ]
    return report


__all__ = [
    "ShrineReasonProvenance",
    "classify_provenance",
    "build_shrine_reason_provenance",
    "aggregate_measurements",
    "build_recommendation_quality_measurement_report",
]
