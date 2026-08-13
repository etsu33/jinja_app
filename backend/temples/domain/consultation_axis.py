from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


ConsultationAxis = str

CONSULTATION_AXES: List[ConsultationAxis] = [
    "money_growth",
    "career_change",
    "independence",
    "relationship_repair",
    "rest_healing",
    "restart_mindset",
    "nature_reset",
    "study_success",
    "other",
]
# "relationship_repair" (恋愛・家族・職場・友人など、人との関係を整える
# 相談) was already documented as the primary consultation_axis for the
# `relationship` theme_key in docs/product/consultation-theme-taxonomy.md
# and docs/audit/score-v3-consultation-axis-history-theme-mapping.md
# §6.2, and already has real (non-shadow) ranking weights in
# concierge_chat_ranking.HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS -- but was
# never actually connected here, so every relationship/love consultation
# fell through to "other" (docs/audit/concierge-l1-freetext-readiness.md
# Finding A, PR #2409). Adding it to the official axis list only wires up
# an axis the design docs and ranking layer already treat as real.

CONSULTATION_AXIS_SET = set(CONSULTATION_AXES)

CONSULTATION_AXIS_ALIASES: Dict[str, ConsultationAxis] = {
    "money": "money_growth",
    "business": "money_growth",
    "career": "career_change",
    "work": "career_change",
    "job": "career_change",
    "independent": "independence",
    "startup": "independence",
    "freelance": "independence",
    "relationship": "relationship_repair",
    "human_relationship": "relationship_repair",
    # score-v3-consultation-axis-history-theme-mapping.md §6.2 scopes
    # relationship_repair to include 恋愛 (romantic love) alongside
    # family/workplace/friend relationships -- love shares this axis at
    # the consultation_axis layer while remaining a distinct need_tag
    # (temples/domain/need_tags.py) and reason label (PR #2410). No
    # independent "love_connection" axis exists in the taxonomy docs, so
    # one is not invented here.
    "love": "relationship_repair",
    "rest": "rest_healing",
    "healing": "rest_healing",
    "mental": "restart_mindset",
    "restart": "restart_mindset",
    "nature": "nature_reset",
    "study": "study_success",
    "focus": "study_success",
}

CONSULTATION_AXIS_KEYWORDS: Dict[ConsultationAxis, List[str]] = {
    "money_growth": [
        "金運",
        "お金",
        "お金を増やしたい",
        "収入",
        "年収",
        "給料",
        "売上",
        "収益",
        "利益",
        "資金",
        "稼ぎたい",
        "もっと稼ぎたい",
        "稼ぐ",
        "稼ぎ",
    ],
    "career_change": [
        "転職",
        "仕事を辞めたい",
        "好きな仕事",
        "天職",
        "仕事運",
        "仕事の方向性",
        "キャリア",
        "働き方",
    ],
    "independence": [
        "独立",
        "起業",
        "副業",
        "会社を作りたい",
        "自由に働きたい",
        "会社に縛られたくない",
        "フリーランス",
        "組織に依存しない",
        "場所に縛られず",
        "自分のサービス",
        "経営者",
    ],
    # Query-level relationship phrasing only (Task 4). Love-specific
    # keywords (恋愛/出会い/良縁) are intentionally NOT duplicated here --
    # need_tags.py already extracts them as the "love" need tag, and
    # NEED_TAG_TO_CONSULTATION_AXIS below routes "love" to this same axis
    # via the need_tags fallback branch of resolve_consultation_axis().
    "relationship_repair": [
        "人間関係",
        "職場の人間関係",
        "家族との関係",
        "友人との関係",
        "対人関係",
        "関係を整理",
        "関係を修復",
        "関係がうまくいかない",
        "仲直り",
    ],
    "rest_healing": [
        "疲れ",
        "疲れて",
        "疲労",
        "落ち着ける",
        "落ち着きたい",
        "静か",
        "人が少ない",
        "休みたい",
        "休息",
        "癒し",
        "ひと息",
        "穏やか",
        "落ち込",
        "落ち込み",
        "気分が沈",
        "気分が沈む",
        "沈んで",
        "立て直したい",
        "立て直す",
        "立て直し",
    ],
    "restart_mindset": [
        "気持ちを切り替えたい",
        "気持ちを切り替えて",
        "前向き",
        "前向きになりたい",
        "前向きになれる",
        "再出発",
        "流れを変えたい",
        "リセット",
        "動き出したい",
        "一歩踏み出したい",
    ],
    "nature_reset": [
        "自然",
        "緑",
        "開放感",
        "散歩",
        "空気",
        "森",
        "木々",
    ],
    "study_success": [
        "学業",
        "合格",
        "合格祈願",
        "試験",
        "受験",
        "資格",
        "勉強",
        "成績",
        "学び",
        "集中",
    ],
}

NEED_TAG_TO_CONSULTATION_AXIS: Dict[str, ConsultationAxis] = {
    "money": "money_growth",
    "career": "career_change",
    "courage": "restart_mindset",
    "mental": "restart_mindset",
    "rest": "rest_healing",
    "study": "study_success",
    "focus": "study_success",
    "relationship": "relationship_repair",
    "love": "relationship_repair",
}
# "relationship" and "love" stay distinct need_tags (PR #2410) but share
# the relationship_repair consultation_axis -- see the CONSULTATION_AXIS_ALIASES
# comment above for the design rationale (score-v3-consultation-axis-history-theme-mapping.md §6.2).

CONSULTATION_AXIS_PRIORITY: Dict[ConsultationAxis, int] = {
    axis: index for index, axis in enumerate(CONSULTATION_AXES)
}


@dataclass(frozen=True)
class ConsultationAxisExtract:
    axis: ConsultationAxis
    source: str
    hits: Dict[ConsultationAxis, List[str]]


def normalize_consultation_axis(value: Any) -> ConsultationAxis:
    axis = str(value or "").strip().lower()
    axis = CONSULTATION_AXIS_ALIASES.get(axis, axis)
    return axis if axis in CONSULTATION_AXIS_SET else "other"


def resolve_consultation_axis(
    *,
    query: str,
    need_tags: Any = None,
    llm_axis: Any = None,
) -> ConsultationAxisExtract:
    normalized_llm_axis = normalize_consultation_axis(llm_axis)
    if normalized_llm_axis != "other":
        return ConsultationAxisExtract(axis=normalized_llm_axis, source="llm", hits={})

    hits: Dict[ConsultationAxis, List[str]] = {}
    text = str(query or "")
    if text.strip():
        for axis, words in CONSULTATION_AXIS_KEYWORDS.items():
            for word in words:
                if word and word in text:
                    hits.setdefault(axis, [])
                    if word not in hits[axis]:
                        hits[axis].append(word)

    if hits:
        axis = sorted(
            hits.keys(),
            key=lambda item: (
                -len(hits[item]),
                CONSULTATION_AXIS_PRIORITY.get(item, 99),
                item,
            ),
        )[0]
        return ConsultationAxisExtract(axis=axis, source="query", hits=hits)

    for tag in need_tags or []:
        axis = NEED_TAG_TO_CONSULTATION_AXIS.get(str(tag or "").strip().lower())
        if axis:
            return ConsultationAxisExtract(axis=axis, source="need_tags", hits={})

    return ConsultationAxisExtract(axis="other", source="fallback", hits={})


__all__ = [
    "CONSULTATION_AXES",
    "CONSULTATION_AXIS_SET",
    "ConsultationAxisExtract",
    "normalize_consultation_axis",
    "resolve_consultation_axis",
]
