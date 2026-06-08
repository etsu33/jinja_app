from __future__ import annotations


from typing import Any, Dict, List, Optional

from temples.services.action_suggestions import get_action_suggestions_for_theme


NEED_LABELS_JA: Dict[str, str] = {
    "study": "学業・合格",
    "career": "転機・仕事",
    "mental": "不安・心",
    "love": "恋愛",
    "money": "金運",
    "rest": "休息",
    "courage": "前進・後押し",
    "protection": "厄除け・守り",
    "focus": "集中・継続",
    "travel_safe": "移動・安全",
    "element": "生年月日との相性",
    "fallback": "近い候補",
    "visit_style": "参拝スタイル",
}


GOGYOU_TONE_JA: Dict[str, str] = {
    "木": "伸びていく力を受け取りやすい流れ",
    "火": "前へ進む力や活力を受け取りやすい流れ",
    "土": "足元を固め、落ち着いて整えやすい流れ",
    "金": "区切りをつけ、選び直しやすい流れ",
    "水": "静かに整え直す流れ",
}


# --- HISTORY THEME LABELS & TONES ---
HISTORY_THEME_LABELS_JA: Dict[str, str] = {
    "再出発": "再出発",
    "静寂": "静寂",
    "復興": "復興",
    "勝負": "勝負",
    "縁": "縁",
    "学び": "学び",
    "守り": "守り",
}

HISTORY_THEME_TONE_JA: Dict[str, str] = {
    "再出発": "切り替えや新しい一歩を支える文脈",
    "静寂": "静かに心を整える文脈",
    "復興": "立て直しや回復を支える文脈",
    "勝負": "決断や挑戦に向き合う文脈",
    "縁": "人や機会とのつながりを見直す文脈",
    "学び": "積み重ねや理解を深める文脈",
    "守り": "不安を鎮め、安心を得る文脈",
}


def _build_history_context(rec: Dict[str, Any]) -> Dict[str, Any] | None:
    raw_theme = str(rec.get("history_theme") or "").strip()
    if not raw_theme:
        return None

    return {
        "theme": raw_theme,
        "label": HISTORY_THEME_LABELS_JA.get(raw_theme, raw_theme),
        "tone": HISTORY_THEME_TONE_JA.get(raw_theme, "神社の歴史や土地の文脈"),
    }


def _build_gogyou_context(birthdate: Optional[str]) -> Dict[str, Any] | None:
    if not birthdate:
        return None

    try:
        from temples.domain.fortune import fortune_profile
    except Exception:
        return None

    profile = fortune_profile(birthdate)
    gogyou = str(getattr(profile, "gogyou", "") or "").strip()
    eto = str(getattr(profile, "eto", "") or "").strip()

    if not gogyou:
        return None

    return {
        "gogyou": gogyou,
        "eto": eto or None,
        "tone": GOGYOU_TONE_JA.get(gogyou, "今の流れを受け取りやすい状態"),
    }


def _safe_str_list(value: Any, *, limit: int | None = None) -> List[str]:
    if not isinstance(value, list):
        return []

    out: List[str] = []
    for x in value:
        if not isinstance(x, str):
            continue
        s = x.strip()
        if not s:
            continue
        if s not in out:
            out.append(s)

    if limit is not None:
        return out[:limit]
    return out


def _normalize_reason_facts(value: Any, *, limit: int | None = None) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []

    out: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        type_ = str(item.get("type") or "").strip()
        label = str(item.get("label") or "").strip()
        label_ja = str(item.get("label_ja") or "").strip() or NEED_LABELS_JA.get(label, label or None)
        evidence = _safe_str_list(item.get("evidence"), limit=5)
        score = float(item.get("score") or 0.0)
        is_primary = bool(item.get("is_primary"))

        if not type_:
            continue

        out.append(
            {
                "type": type_,
                "label": label,
                "label_ja": label_ja,
                "evidence": evidence,
                "score": score,
                "is_primary": is_primary,
            }
        )

    if limit is not None:
        return out[:limit]
    return out


def _build_visit_style_primary_reason(rec: Dict[str, Any]) -> Dict[str, Any] | None:
    breakdown_detail = (
        rec.get("breakdown_detail")
        if isinstance(rec.get("breakdown_detail"), dict)
        else {}
    )
    features = breakdown_detail.get("features") if isinstance(breakdown_detail, dict) else {}
    if not isinstance(features, dict):
        return None

    visit_style = features.get("visit_style")
    if not isinstance(visit_style, dict):
        return None

    matched_tags = _safe_str_list(visit_style.get("matched_tags"), limit=5)
    if not matched_tags:
        return None

    contribution = float(visit_style.get("contribution") or 0.0)
    if contribution <= 0:
        return None

    return {
        "type": "visit_style",
        "label": matched_tags[0],
        "label_ja": NEED_LABELS_JA["visit_style"],
        "evidence": matched_tags,
        "score": contribution,
        "is_primary": True,
    }


def build_explanation_payload(rec: Dict[str, Any], *, birthdate: Optional[str] = None) -> Dict[str, Any]:
    """
    explanation 用の正規化 payload を作る。

    用語定義:
    - primary_need_tag:
      相談全体の中心テーマ。ユーザー意図の主語。
      detail で「相談の中心」を説明するために使う。
    - primary_reason:
      この神社が上位に入った直接理由。順位根拠の主語。
      card や explanation で「なぜこの候補か」を説明するために使う。

    この payload 自体は自然文を生成せず、
    explanation 表示用の構造化データだけを持つ。
    """

    breakdown = rec.get("breakdown") if isinstance(rec.get("breakdown"), dict) else {}
    breakdown_detail = (
        rec.get("breakdown_detail")
        if isinstance(rec.get("breakdown_detail"), dict)
        else {}
    )

    # 相談文脈
    matched_need_tags = _safe_str_list(
        breakdown.get("matched_need_tags"),
        limit=3,
    )
    primary_need_tag = matched_need_tags[0] if matched_need_tags else None
    primary_need_label_ja = NEED_LABELS_JA.get(primary_need_tag or "", None)

    # 表示補助
    highlights = _safe_str_list(rec.get("highlights"), limit=3)
    # reason_source は表示文の生成経路を表す。primary_reason そのものではない。
    reason_source = str(rec.get("reason_source") or "").strip() or None
    original_reason = str(rec.get("reason") or "").strip() or None

    # スコア
    score_element = int(breakdown.get("score_element") or 0)
    score_need = int(breakdown.get("score_need") or 0)
    score_total = float(breakdown.get("score_total") or 0.0)

    score_total_ranked = 0.0
    if isinstance(breakdown_detail.get("features"), dict):
        score_total_ranked = float(
            (breakdown_detail["features"].get("score_total_ranked") or 0.0)
        )

    score_v2 = rec.get("score_v2") if isinstance(rec.get("score_v2"), dict) else None

    # 候補採用理由
    reason_facts = _normalize_reason_facts(
        rec.get("_reason_facts"),
        limit=5,
    )

    primary_reason = next(
        (x for x in reason_facts if x.get("is_primary")),
        None,
    )

    visit_style_primary_reason = _build_visit_style_primary_reason(rec)
    if (
        visit_style_primary_reason is not None
        and (
            primary_reason is None
            or str(primary_reason.get("type") or "").strip() == "fallback"
        )
    ):
        primary_reason = visit_style_primary_reason

    if primary_reason is None:
        source = str(rec.get("_primary_reason_source") or "").strip()
        label = str(rec.get("_primary_reason_label") or "").strip()
        if source:
            primary_reason = {
                "type": source,
                "label": label,
                "label_ja": NEED_LABELS_JA.get(label, label or NEED_LABELS_JA.get(source, source)),
                "evidence": [],
                "score": 0.0,
                "is_primary": True,
            }

    secondary_reasons = [x for x in reason_facts if not x.get("is_primary")]

    gogyou_context = _build_gogyou_context(birthdate)
    history_context = _build_history_context(rec)
    action_suggestions = get_action_suggestions_for_theme(
        history_context.get("theme") if isinstance(history_context, dict) else None,
    )

    return {
        "version": 2,
        "matched_need_tags": matched_need_tags,
        "primary_need_tag": primary_need_tag,
        "primary_need_label_ja": primary_need_label_ja,
        "primary_reason": primary_reason,
        "secondary_reasons": secondary_reasons[:3],
        "highlights": highlights,
        "reason_source": reason_source,
        "original_reason": original_reason,
        "gogyou_context": gogyou_context,
        "history_context": history_context,
        "action_suggestions": action_suggestions,
        "score": {
            "element": score_element,
            "need": score_need,
            "total": score_total,
            "total_ranked": score_total_ranked,
        },
        "score_v2": score_v2,
    }


def attach_explanation_payload(recs: Dict[str, Any], *, birthdate: Optional[str] = None) -> Dict[str, Any]:
    items = recs.get("recommendations") or []
    if not isinstance(items, list):
        return recs

    for rec in items:
        if not isinstance(rec, dict):
            continue
        rec["_explanation_payload"] = build_explanation_payload(rec, birthdate=birthdate)

    return recs


__all__ = [
    "NEED_LABELS_JA",
    "build_explanation_payload",
    "attach_explanation_payload",
]
