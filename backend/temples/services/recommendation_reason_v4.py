from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecommendationReasonV4:
    reason_text: str
    fact: dict[str, Any] = field(default_factory=dict)
    interpretation: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "reason_text": self.reason_text,
            "fact": self.fact,
            "interpretation": self.interpretation,
            "action": self.action,
            "source": self.source,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
        if isinstance(value, tuple):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return None


NEED_COPY: dict[str, str] = {
    "mental": "気持ちを落ち着け、今の状態を整理したい",
    "rest": "疲れを整え、静かに回復したい",
    "career": "仕事や働き方を見直したい",
    "money": "生活や収入の土台を整えたい",
    "love": "人との縁や関係性を見直したい",
    "study": "学びや積み重ねを続けたい",
    "courage": "次に進むための一歩を決めたい",
}

DECISION_COPY: dict[str, str] = {
    "career_decision": "仕事や働き方について判断したい",
    "relationship_decision": "人との関係について見直したい",
    "money_decision": "お金や生活の判断を整えたい",
    "rest_or_action": "休むか動くかを見極めたい",
}

CONSTRAINT_COPY: dict[str, str] = {
    "time": "時間の余裕が少ない",
    "money": "お金や収入への不安がある",
    "energy": "体力や気力が落ちている",
    "relationship": "人間関係の制約がある",
}

OUTCOME_COPY: dict[str, str] = {
    "decide": "判断材料を持ち帰りたい",
    "calm": "気持ちを落ち着けたい",
    "move_forward": "小さく前に進みたい",
    "clarify": "考えを整理したい",
}

ACTION_INTENT_COPY: dict[str, str] = {
    "visit": "実際に足を運んで確認したい",
    "reflect": "問いを一つに絞って整理したい",
    "save": "今回の相談を残して振り返りたい",
}

VISIT_STYLE_COPY: dict[str, str] = {
    "quiet": "静かに参拝しやすい",
    "nature": "自然を感じながら過ごしやすい",
    "classic": "昔ながらの神社らしさを感じやすい",
    "less_crowded": "人の多さを避けて落ち着きやすい",
    "business": "仕事や日々の判断を意識しやすい",
    "reset": "気持ちを切り替えやすい",
}


def _copy_visit_style_tags(tags: list[Any]) -> list[str]:
    copies: list[str] = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        copied = VISIT_STYLE_COPY.get(tag.strip())
        if copied:
            copies.append(copied)
    return copies


def _copy_for_key(mapping: dict[str, str], key: str | None) -> str | None:
    if not key:
        return None
    return mapping.get(key, key)


def _build_fact(candidate_profile: dict[str, Any], meaning_translation: dict[str, Any]) -> dict[str, Any]:
    history_theme = _first_string(candidate_profile.get("history_theme"), meaning_translation.get("history_theme"))
    goriyaku = _first_string(candidate_profile.get("goriyaku"), candidate_profile.get("goriyaku_tags"))
    visit_style_tags = _as_list(candidate_profile.get("visit_style_tags"))
    name = _first_string(candidate_profile.get("name"))

    label = _first_string(history_theme, goriyaku, name, "候補神社") or "候補神社"
    evidence: list[str] = []

    if history_theme:
        evidence.append(f"history_theme:{history_theme}")
    if goriyaku:
        evidence.append(f"goriyaku:{goriyaku}")
    if visit_style_tags:
        evidence.append(f"visit_style_tags:{','.join(str(tag) for tag in visit_style_tags)}")
    if name:
        evidence.append(f"name:{name}")

    return {
        "label": label,
        "name": name,
        "goriyaku": goriyaku,
        "visit_style_tags": visit_style_tags,
        "evidence": evidence,
    }


def _build_interpretation(
    interpretation_profile: dict[str, Any],
    meaning_translation: dict[str, Any],
) -> dict[str, Any]:
    state_profile = _as_dict(interpretation_profile.get("state_profile"))
    emotion_profile = _as_dict(interpretation_profile.get("emotion_profile"))
    need_profile = _as_dict(interpretation_profile.get("need_profile"))
    decision_context = _as_dict(interpretation_profile.get("decision_context"))
    constraint_profile = _as_dict(interpretation_profile.get("constraint_profile"))
    outcome_hint = _as_dict(interpretation_profile.get("outcome_hint"))

    theme = _first_string(
        meaning_translation.get("history_theme"),
        need_profile.get("primary_need_tag"),
        decision_context.get("primary_decision"),
        constraint_profile.get("primary_constraint"),
        outcome_hint.get("primary_outcome"),
    ) or "相談文脈"

    shrine_context_need = _first_string(meaning_translation.get("shrine_context_need"))
    primary_need = _copy_for_key(
        NEED_COPY,
        _first_string(need_profile.get("primary_need_tag"), need_profile.get("need_tags")),
    )
    primary_state = _first_string(state_profile.get("primary_state"))
    emotion_intensity = _first_string(emotion_profile.get("intensity"))
    state_copy = {
        "uncertain": "判断に迷う様子",
        "tired": "無理なく休みたい様子",
        "anxious": "不安や心配",
        "stuck": "停滞を見直したい様子",
        "ready_to_change": "流れを切り替えたい様子",
    }.get(primary_state)

    parts: list[str] = []
    if shrine_context_need:
        parts.append(shrine_context_need)
    if state_copy:
        if primary_need and not shrine_context_need:
            parts.append(f"{primary_need}相談として受け取れます")
        state_suffix = "文脈が強めに含まれています" if emotion_intensity == "high" else "文脈があります"
        parts.append(f"{state_copy}を中心に、{state_suffix}")
    else:
        primary_decision = _copy_for_key(
            DECISION_COPY,
            _first_string(decision_context.get("primary_decision"), decision_context.get("decision_candidates")),
        )
        if primary_need:
            parts.append(f"{primary_need}相談として受け取れます")
        elif primary_decision:
            parts.append(f"{primary_decision}文脈があります")

    text = "。".join(parts) + "。" if parts else "相談内容と神社側の文脈を照合する候補です。"

    return {
        "theme": theme,
        "text": text,
    }


def _build_action(interpretation_profile: dict[str, Any], meaning_translation: dict[str, Any]) -> dict[str, Any]:
    action_intent = _as_dict(interpretation_profile.get("action_intent"))
    outcome_hint = _as_dict(interpretation_profile.get("outcome_hint"))

    action_context = _first_string(meaning_translation.get("action_context"))
    reflection_question_seed = _first_string(meaning_translation.get("reflection_question_seed"))
    intent = _first_string(action_intent.get("intent"), action_intent.get("candidates"))
    outcome = _first_string(outcome_hint.get("primary_outcome"), outcome_hint.get("outcome_candidates"))

    if reflection_question_seed:
        text = f"参拝後は「{reflection_question_seed}」を一つだけ振り返ると、次の行動に残しやすくなります。"
        source = "meaning_translation.reflection_question_seed"
    elif action_context:
        text = f"参拝前に、{action_context}ことを一つだけ決めておくと、行動につなげやすくなります。"
        source = "meaning_translation.action_context"
    elif intent:
        intent_copy = _copy_for_key(ACTION_INTENT_COPY, intent) or "次に取りたい行動"
        text = f"次に取る行動として、{intent_copy}ことを小さく確認します。"
        source = "interpretation_profile.action_intent"
    elif outcome:
        outcome_copy = _copy_for_key(OUTCOME_COPY, outcome) or outcome
        text = f"望む着地点として、{outcome_copy}方向に向けた小さな確認を行います。"
        source = "interpretation_profile.outcome_hint"
    else:
        text = "参拝前に、次に確認したいことを一つだけ決めておきます。"
        source = "fallback"

    return {
        "text": text,
        "source": source,
    }


def _build_reason_text(fact: dict[str, Any], interpretation: dict[str, Any], action: dict[str, Any]) -> str:
    fact_label = _first_string(fact.get("label")) or "候補神社"
    fact_name = _first_string(fact.get("name"))
    fact_goriyaku = _first_string(fact.get("goriyaku"))
    visit_style_copies = _copy_visit_style_tags(_as_list(fact.get("visit_style_tags")))
    interpretation_text = _first_string(interpretation.get("text")) or "相談内容と神社側の文脈を照合しています。"
    action_text = _first_string(action.get("text")) or "次に確認したいことを一つだけ決めます。"

    if fact_name and fact_label != "候補神社":
        fact_text = f"{fact_name}には、{fact_label}という文脈があります。"
    elif fact_name:
        fact_text = f"{fact_name}は、相談内容と神社側の文脈を照合する候補です。"
    elif fact_label == "候補神社":
        fact_text = "この候補は、相談内容と神社側の文脈を照合する候補です。"
    else:
        fact_text = f"この候補には、{fact_label}という文脈があります。"

    fact_details: list[str] = []
    if fact_goriyaku and fact_goriyaku != fact_label:
        fact_details.append(f"{fact_goriyaku}の要素")
    if visit_style_copies:
        fact_details.append("、".join(visit_style_copies[:2]))
    if fact_details:
        fact_text = f"{fact_text[:-1]}。{ '。'.join(fact_details) }も確認材料になります。"

    if fact_label == "候補神社" and interpretation_text == "相談内容と神社側の文脈を照合する候補です。":
        interpretation_text = "相談内容に合う神社側の手がかりを確認しています。"

    return "".join([fact_text, interpretation_text, action_text])


def build_recommendation_reason_v4(
    *,
    recommendation_input_profile: dict[str, Any] | None = None,
    interpretation_profile: dict[str, Any] | None = None,
    meaning_translation: dict[str, Any] | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a preview-only Recommendation Reason v4 payload.

    This function is deterministic and side-effect free.
    It does not change ranking, Score v3 weights, or existing recommendation reason output.
    """

    recommendation_input = _as_dict(recommendation_input_profile)
    interpretation = _as_dict(interpretation_profile) or _as_dict(recommendation_input.get("interpretation_profile"))
    meaning = _as_dict(meaning_translation) or _as_dict(recommendation_input.get("translation_result"))
    candidate = _as_dict(candidate_profile) or _as_dict(recommendation_input.get("candidate_profile"))

    fact = _build_fact(candidate, meaning)
    interpretation_layer = _build_interpretation(interpretation, meaning)
    action = _build_action(interpretation, meaning)

    return RecommendationReasonV4(
        reason_text=_build_reason_text(fact, interpretation_layer, action),
        fact=fact,
        interpretation=interpretation_layer,
        action=action,
        source={
            "fact": "candidate_profile|meaning_translation",
            "interpretation": "interpretation_profile|meaning_translation",
            "action": action.get("source") or "fallback",
        },
    ).as_dict()


__all__ = [
    "RecommendationReasonV4",
    "build_recommendation_reason_v4",
]
