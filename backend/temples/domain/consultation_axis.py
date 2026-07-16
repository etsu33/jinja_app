from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


ConsultationAxis = str

CONSULTATION_AXES: List[ConsultationAxis] = [
    "money_growth",
    "career_change",
    "independence",
    "rest_healing",
    "restart_mindset",
    "nature_reset",
    "study_success",
    "other",
]

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
}

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
