from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecommendationReasonV4:
    reason_text: str
    fact: dict[str, Any] = field(default_factory=dict)
    interpretation: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    used_fact: dict[str, Any] = field(default_factory=dict)
    used_interpretation: dict[str, Any] = field(default_factory=dict)
    used_action: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "reason_text": self.reason_text,
            "fact": self.fact,
            "interpretation": self.interpretation,
            "action": self.action,
            "used_fact": self.used_fact,
            "used_interpretation": self.used_interpretation,
            "used_action": self.used_action,
            "quality": self.quality,
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

CONSULTATION_AXIS_COPY: dict[str, str] = {
    "career_decision": "仕事や働き方の判断",
    "relationship_review": "人との関係の見直し",
    "money_foundation": "生活や収入の土台",
    "rest_or_action": "休むか動くかの見極め",
    "mental_reset": "気持ちの切り替え",
    "study_growth": "学びや成長の積み重ね",
    "love_relationship": "人との縁や関係性",
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
    """Build the Fact layer from shrine-side information only.

    Fact must not interpret the user's state or suggest the next action.
    """
    history_theme = _first_string(candidate_profile.get("history_theme"), meaning_translation.get("history_theme"))
    deity = _first_string(candidate_profile.get("deity"), candidate_profile.get("main_deity"), candidate_profile.get("enshrined_deity"))
    shrine_history = _first_string(candidate_profile.get("history"), candidate_profile.get("shrine_history"), candidate_profile.get("origin"))
    place_context = _first_string(candidate_profile.get("place_context"), candidate_profile.get("area_context"), candidate_profile.get("location_context"))
    goriyaku = _first_string(candidate_profile.get("goriyaku"), candidate_profile.get("goriyaku_tags"))
    visit_style_tags = _as_list(candidate_profile.get("visit_style_tags"))
    name = _first_string(candidate_profile.get("name"))

    # label は互換目的の補助フィールド（既存テスト・evidence表示のみで参照）。
    # _build_reason_text の主判定には使用しない。place_context(住所)を含む算出方法は
    # 従来のまま維持し、reason_text生成側でplace_contextを除外することで
    # 「住所が神社の特徴として表示される」不具合のみを止める。
    label = _first_string(deity, shrine_history, place_context, history_theme, goriyaku, name, "候補神社") or "候補神社"
    evidence: list[str] = []

    if deity:
        evidence.append(f"deity:{deity}")
    if shrine_history:
        evidence.append(f"shrine_history:{shrine_history}")
    if place_context:
        evidence.append(f"place_context:{place_context}")
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
        "deity": deity,
        "shrine_history": shrine_history,
        "place_context": place_context,
        "history_theme": history_theme,
        "goriyaku": goriyaku,
        "visit_style_tags": visit_style_tags,
        "evidence": evidence,
    }


def _build_used_fact(fact: dict[str, Any]) -> dict[str, Any]:
    """Return shrine-side values actually available for the recommendation reason."""
    return {
        "deity": fact.get("deity"),
        "shrine_history": fact.get("shrine_history"),
        "place_context": fact.get("place_context"),
        "goriyaku": fact.get("goriyaku"),
        "history_theme": fact.get("history_theme"),
        "evidence": fact.get("evidence") or [],
    }


def _build_interpretation(
    interpretation_profile: dict[str, Any],
    meaning_translation: dict[str, Any],
) -> dict[str, Any]:
    """Build the Interpretation layer from the consultation profile only.

    Interpretation may use history_theme as a meaning label, but must not write shrine facts or action steps.
    """
    state_profile = _as_dict(interpretation_profile.get("state_profile"))
    emotion_profile = _as_dict(interpretation_profile.get("emotion_profile"))
    need_profile = _as_dict(interpretation_profile.get("need_profile"))
    decision_context = _as_dict(interpretation_profile.get("decision_context"))
    constraint_profile = _as_dict(interpretation_profile.get("constraint_profile"))
    outcome_hint = _as_dict(interpretation_profile.get("outcome_hint"))

    consultation_axis = _first_string(
        interpretation_profile.get("consultation_axis"),
        interpretation_profile.get("axis"),
        need_profile.get("consultation_axis"),
    )
    consultation_axis_copy = _copy_for_key(CONSULTATION_AXIS_COPY, consultation_axis)

    theme = _first_string(
        consultation_axis,
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
    if consultation_axis_copy:
        parts.append(f"{consultation_axis_copy}を中心にした相談として受け取れます")
    if shrine_context_need:
        parts.append(shrine_context_need)
    if state_copy:
        if primary_need and not shrine_context_need and not consultation_axis_copy:
            parts.append(f"{primary_need}相談として受け取れます")
        state_suffix = "要素が強めに出ています" if emotion_intensity == "high" else "要素があります"
        parts.append(f"{state_copy}を中心に、{state_suffix}")
    else:
        primary_decision = _copy_for_key(
            DECISION_COPY,
            _first_string(decision_context.get("primary_decision"), decision_context.get("decision_candidates")),
        )
        if primary_need and not consultation_axis_copy:
            parts.append(f"{primary_need}相談として受け取れます")
        elif primary_decision and not consultation_axis_copy:
            parts.append(f"{primary_decision}相談として受け取れます")

    text = "。".join(parts) + "。" if parts else "相談内容から、今扱いたいテーマを読み取っています。"

    return {
        "theme": theme,
        "text": text,
    }


def _build_used_interpretation(
    interpretation_profile: dict[str, Any],
    meaning_translation: dict[str, Any],
    interpretation: dict[str, Any],
    fact: dict[str, Any],
) -> dict[str, Any]:
    """Return consultation-side values used to explain the recommendation."""
    state_profile = _as_dict(interpretation_profile.get("state_profile"))
    need_profile = _as_dict(interpretation_profile.get("need_profile"))
    consultation_axis = _first_string(
        interpretation_profile.get("consultation_axis"),
        interpretation_profile.get("axis"),
        need_profile.get("consultation_axis"),
    )
    historical_interpretation = None
    shrine_history = _first_string(fact.get("shrine_history"))
    if shrine_history:
        historical_interpretation = f"{shrine_history}を、今回の相談を受け取る補助材料として参照しています。"

    return {
        "consultation_axis": consultation_axis,
        "need_profile": {
            "primary_need_tag": _first_string(need_profile.get("primary_need_tag"), need_profile.get("need_tags")),
            "need_tags": _as_list(need_profile.get("need_tags")),
        },
        "state_profile": {
            "primary_state": _first_string(state_profile.get("primary_state")),
            "secondary_states": _as_list(state_profile.get("secondary_states")),
        },
        "historical_interpretation": historical_interpretation,
        "theme": interpretation.get("theme"),
    }


def _build_action(interpretation_profile: dict[str, Any], meaning_translation: dict[str, Any]) -> dict[str, Any]:
    """Build the Action layer as one concrete next step.

    Action must not explain history_theme or repeat the consultation interpretation.
    """
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



def _build_used_action(interpretation_profile: dict[str, Any], meaning_translation: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    """Return action-side values used to build the next-step suggestion."""
    action_intent = _as_dict(interpretation_profile.get("action_intent"))
    return {
        "action_context": _first_string(meaning_translation.get("action_context")),
        "reflection_question_seed": _first_string(meaning_translation.get("reflection_question_seed")),
        "action_intent": _first_string(action_intent.get("intent"), action_intent.get("candidates")),
        "source": action.get("source") or "fallback",
    }


def _rate(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 4)


def build_recommendation_reason_quality_audit(reason: dict[str, Any]) -> dict[str, Any]:
    """Calculate lightweight quality metrics for Recommendation Reason v4.

    This audit is deterministic and only evaluates the generated payload.
    It does not change recommendation ranking or copy generation.
    """
    used_fact = _as_dict(reason.get("used_fact"))
    used_interpretation = _as_dict(reason.get("used_interpretation"))
    used_action = _as_dict(reason.get("used_action"))

    shrine_fact_keys = ["deity", "shrine_history", "place_context", "goriyaku", "history_theme"]
    consultation_keys = ["consultation_axis", "need_profile", "state_profile", "historical_interpretation"]
    action_keys = ["action_context", "reflection_question_seed", "action_intent"]

    shrine_data_count = sum(1 for key in shrine_fact_keys if used_fact.get(key))
    evidence_count = len(_as_list(used_fact.get("evidence")))
    consultation_count = 0
    for key in consultation_keys:
        value = used_interpretation.get(key)
        if isinstance(value, dict):
            if any(v for v in value.values()):
                consultation_count += 1
        elif value:
            consultation_count += 1
    action_count = sum(1 for key in action_keys if used_action.get(key))

    source = _first_string(used_action.get("source")) or "fallback"
    is_fallback = source == "fallback"
    is_ai_inference_only = shrine_data_count == 0 and evidence_count == 0

    return {
        "shrine_data_rate": _rate(shrine_data_count, len(shrine_fact_keys)),
        "consultation_reflection_rate": _rate(consultation_count, len(consultation_keys)),
        "fallback_reason_rate": 1.0 if is_fallback else 0.0,
        "evidence_rate": _rate(evidence_count, len(shrine_fact_keys)),
        "action_grounding_rate": _rate(action_count, len(action_keys)),
        "is_ai_inference_only": is_ai_inference_only,
        "fallback_source": source if is_fallback else None,
    }


def _build_fact_text(fact: dict[str, Any]) -> str:
    """Compose the Fact sentence by branching on Fact type.

    Each Fact type (deity / shrine_history / goriyaku / history_theme) has its own
    sentence form instead of being flattened into a single "label" template.
    place_context (raw address) is never used as the sentence subject: an address is
    not a shrine-specific feature, and stating "shrine X has the feature of <address>"
    reads as broken Japanese and misrepresents empty Fact data as grounded content.
    """
    fact_name = _first_string(fact.get("name"))
    fact_deity = _first_string(fact.get("deity"))
    fact_shrine_history = _first_string(fact.get("shrine_history"))
    fact_goriyaku = _first_string(fact.get("goriyaku"))
    fact_history_theme = _first_string(fact.get("history_theme"))
    visit_style_copies = _copy_visit_style_tags(_as_list(fact.get("visit_style_tags")))

    subject = fact_name or "この神社"
    fact_details: list[str] = []

    if fact_deity:
        fact_text = f"{subject}では、{fact_deity}が祀られています。"
        if fact_goriyaku:
            fact_details.append(f"{fact_goriyaku}の要素")
    elif fact_shrine_history:
        history_text = fact_shrine_history.rstrip("。")
        fact_text = f"{subject}には、{history_text}という背景があります。"
        if fact_goriyaku:
            fact_details.append(f"{fact_goriyaku}の要素")
    elif fact_goriyaku:
        fact_text = f"{subject}には、{fact_goriyaku}に関する情報があります。"
    elif fact_history_theme:
        fact_text = f"{subject}は、{fact_history_theme}という文脈で整理されています。"
    else:
        # deity / shrine_history / goriyaku / history_theme が一つもない場合。
        # place_context(住所)や神社名だけでは神社固有Factがあるとは表現しない。
        fact_text = "神社固有情報が十分でないため、相談条件との一致を中心に整理しています。"

    if visit_style_copies:
        fact_details.extend(visit_style_copies[:2])

    if fact_details:
        detail_text = "、".join(fact_details)
        fact_text = f"{fact_text.rstrip('。')}。{detail_text}も確認材料になります。"

    return fact_text


def _build_reason_text(fact: dict[str, Any], interpretation: dict[str, Any], action: dict[str, Any]) -> str:
    """Compose reason_text as Fact -> Interpretation -> Action.

    Keep each sentence responsible for one layer only.
    """
    fact_text = _build_fact_text(fact)
    interpretation_text = _first_string(interpretation.get("text")) or "相談内容から、今扱いたいテーマを読み取っています。"
    action_text = _first_string(action.get("text")) or "次に確認したいことを一つだけ決めます。"

    reason_parts = [fact_text, interpretation_text, action_text]
    return "".join(reason_parts[:3])


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
    used_fact = _build_used_fact(fact)
    used_interpretation = _build_used_interpretation(interpretation, meaning, interpretation_layer, fact)
    used_action = _build_used_action(interpretation, meaning, action)

    reason = RecommendationReasonV4(
        reason_text=_build_reason_text(fact, interpretation_layer, action),
        fact=fact,
        interpretation=interpretation_layer,
        action=action,
        used_fact=used_fact,
        used_interpretation=used_interpretation,
        used_action=used_action,
        source={
            "fact": "candidate_profile|meaning_translation",
            "interpretation": "interpretation_profile|meaning_translation",
            "action": action.get("source") or "fallback",
        },
    ).as_dict()
    reason["quality"] = build_recommendation_reason_quality_audit(reason)
    return reason



__all__ = [
    "RecommendationReasonV4",
    "build_recommendation_reason_quality_audit",
    "build_recommendation_reason_v4",
]
