"""Shrine Meaning Payload v2 composer.

This module builds a frontend-friendly meaning payload for shrine detail pages.
It intentionally does not depend on DRF serializers or views so it can be tested
as a small service before wiring an endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping, TypedDict

AccessLevel = Literal["anonymous", "free", "premium"]
DisplayBlockId = Literal[
    "hero",
    "consultation_summary",
    "shrine_meaning",
    "action_meaning",
    "history_context",
    "deity_symbol",
    "benefit_action",
    "public_info",
]


class ShrineMeaningSourceV2(TypedDict, total=False):
    shrineId: int
    nameJp: str
    address: str | None
    latitude: float | None
    longitude: float | None
    goriyaku: str | None
    goriyakuTags: list[str]
    sajin: str | None
    description: str | None
    historyTheme: str | None
    element: str | None
    placeTags: list[str]


class ShrineMeaningGeneratedV2(TypedDict):
    heroMeaningCopy: str
    consultationSummary: str
    shrineMeaning: str
    actionMeaning: str
    historyContext: str | None
    deitySymbolContext: str | None
    benefitActionContext: str | None


class ShrineMeaningDisplayBlockV2(TypedDict):
    id: DisplayBlockId
    title: str
    body: str
    access: AccessLevel


class ShrineMeaningDisplayV2(TypedDict):
    blocks: list[ShrineMeaningDisplayBlockV2]
    fallbackMessage: str | None


class ShrineMeaningPayloadV2(TypedDict):
    version: Literal["v2"]
    source: ShrineMeaningSourceV2
    generated: ShrineMeaningGeneratedV2
    display: ShrineMeaningDisplayV2


HISTORY_THEME_CONTEXT: dict[str, str] = {
    "再出発": "切り替えや新しい一歩を支える文脈として受け取りやすい場所です。",
    "静寂": "刺激を増やさず、静かに心を整える文脈として受け取りやすい場所です。",
    "復興": "立て直しや回復に向き合う文脈として受け取りやすい場所です。",
    "勝負": "決断や挑戦に向き合う文脈として受け取りやすい場所です。",
    "縁": "人や機会とのつながりを見直す文脈として受け取りやすい場所です。",
    "学び": "積み重ねや理解を深める文脈として受け取りやすい場所です。",
    "守り": "不安を鎮め、安心を得る文脈として受け取りやすい場所です。",
}


@dataclass(frozen=True)
class ShrineMeaningInput:
    shrine_id: int
    name_jp: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    goriyaku: str | None = None
    goriyaku_tags: tuple[str, ...] = ()
    sajin: str | None = None
    description: str | None = None
    history_theme: str | None = None
    element: str | None = None
    place_tags: tuple[str, ...] = ()


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        raw_items: Iterable[Any] = value.replace("、", "/").replace("，", "/").split("/")
    elif isinstance(value, Iterable):
        raw_items = value
    else:
        return ()

    items: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = _clean_str(item)
        if not text or text in seen:
            continue
        seen.add(text)
        items.append(text)
    return tuple(items)


def _read_value(source: Any, *keys: str) -> Any:
    for key in keys:
        if isinstance(source, Mapping) and key in source:
            return source.get(key)
        if hasattr(source, key):
            return getattr(source, key)
    return None


def _read_goriyaku_tags(source: Any) -> tuple[str, ...]:
    raw = _read_value(source, "goriyakuTags", "goriyaku_tags")

    if raw is None and hasattr(source, "goriyaku_tags"):
        manager = getattr(source, "goriyaku_tags")
        try:
            raw = list(manager.values_list("name", flat=True))
        except Exception:
            raw = None

    if raw and not isinstance(raw, str):
        names: list[str] = []
        for item in raw:
            if isinstance(item, Mapping):
                names.append(str(item.get("name") or ""))
            else:
                names.append(str(item or ""))
        return _clean_str_list(names)

    return _clean_str_list(raw)


def normalize_shrine_meaning_source(source: Any) -> ShrineMeaningInput:
    """Normalize a Shrine model-like object or dict into composer input."""

    shrine_id = _clean_int(_read_value(source, "shrine_id", "shrineId", "id", "pk"))
    name_jp = _clean_str(_read_value(source, "name_jp", "nameJp", "name"))

    if shrine_id is None:
        raise ValueError("shrine_id is required")
    if name_jp is None:
        raise ValueError("name_jp is required")

    return ShrineMeaningInput(
        shrine_id=shrine_id,
        name_jp=name_jp,
        address=_clean_str(_read_value(source, "address")),
        latitude=_clean_float(_read_value(source, "latitude", "lat")),
        longitude=_clean_float(_read_value(source, "longitude", "lng")),
        goriyaku=_clean_str(_read_value(source, "goriyaku")),
        goriyaku_tags=_read_goriyaku_tags(source),
        sajin=_clean_str(_read_value(source, "sajin")),
        description=_clean_str(_read_value(source, "description")),
        history_theme=_clean_str(_read_value(source, "history_theme", "historyTheme")),
        element=_clean_str(_read_value(source, "element")),
        place_tags=_clean_str_list(_read_value(source, "place_tags", "placeTags")),
    )


def _clip(text: str, max_length: int = 56) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}…"


def _primary_benefit(input_: ShrineMeaningInput) -> str | None:
    if input_.goriyaku_tags:
        return input_.goriyaku_tags[0]
    return input_.goriyaku


def _build_hero_meaning(input_: ShrineMeaningInput) -> str:
    if input_.history_theme:
        return f"{input_.name_jp}は、今の状態を整え直す節目として向き合いやすい神社です。"
    if _primary_benefit(input_):
        return f"{input_.name_jp}は、今の願いや状態を一度整理する入口として置きやすい神社です。"
    return f"{input_.name_jp}は、今の状態を落ち着いて見直す候補として扱いやすい神社です。"


def _build_consultation_summary(input_: ShrineMeaningInput) -> str:
    if input_.description or input_.history_theme:
        return "今回の相談は、いま何を優先して見直すべきかを整理しながら、次の判断軸を整えていく文脈として受け取れます。"
    if input_.goriyaku or input_.sajin or input_.element:
        return "今回の相談は、願いそのものを急いで決めるよりも、今の状態や優先順位を整理しながら向き合う文脈としてまとめられます。"
    return "今回の相談は、いま抱えているテーマを一度ほどき、何を先に見直すかを整理する段階として読むのが自然です。"


def _build_shrine_meaning(input_: ShrineMeaningInput) -> str:
    if input_.description:
        return f"{input_.name_jp}は「{_clip(input_.description)}」という特徴を持ち、今回の相談で主題になっている整理や見直しのテーマと接続しやすい神社です。"
    benefit = _primary_benefit(input_)
    if benefit:
        return f"{input_.name_jp}は「{_clip(benefit)}」に関わる文脈を持ち、今回の相談で求めている方向と結びつけて受け取りやすい神社です。"
    if input_.sajin:
        return f"{input_.name_jp}は、祭神の象徴を手がかりに、今回の相談テーマと接続して受け取りやすい神社です。"
    return f"{input_.name_jp}は、今回の相談で主題になっている整理や立て直しのテーマと接続しやすく、意味を重ねて受け取りやすい候補です。"


def _build_action_meaning(input_: ShrineMeaningInput) -> str:
    benefit = _primary_benefit(input_)
    if benefit:
        return f"参拝を、{_clip(benefit, 32)}という願いを急いで叶えるためではなく、今の状態を整理して次の一歩を置く行動として扱えます。"
    if input_.history_theme:
        return "参拝を、気持ちを切り替えながら今のテーマを見直すための小さな行動として置けます。"
    return "参拝を、考え続ける状態から少し離れ、現実の一歩へ移すための行動として置けます。"


def _build_history_context(input_: ShrineMeaningInput) -> str | None:
    if not input_.history_theme:
        return None
    return HISTORY_THEME_CONTEXT.get(
        input_.history_theme,
        "神社の歴史や土地の文脈を、今の状態を見直す補助材料として受け取りやすい場所です。",
    )


def _build_deity_symbol_context(input_: ShrineMeaningInput) -> str | None:
    if not input_.sajin:
        return None
    return f"祭神として「{_clip(input_.sajin)}」が伝わっており、由緒本文ではなく象徴接続の補助材料として扱います。"


def _build_benefit_action_context(input_: ShrineMeaningInput) -> str | None:
    benefit = _primary_benefit(input_)
    if not benefit:
        return None
    return f"「{_clip(benefit)}」は願望成就の断定ではなく、今の行動テーマを整える補助軸として扱います。"


def build_generated_fields(input_: ShrineMeaningInput) -> ShrineMeaningGeneratedV2:
    return {
        "heroMeaningCopy": _build_hero_meaning(input_),
        "consultationSummary": _build_consultation_summary(input_),
        "shrineMeaning": _build_shrine_meaning(input_),
        "actionMeaning": _build_action_meaning(input_),
        "historyContext": _build_history_context(input_),
        "deitySymbolContext": _build_deity_symbol_context(input_),
        "benefitActionContext": _build_benefit_action_context(input_),
    }


def build_source_fields(input_: ShrineMeaningInput) -> ShrineMeaningSourceV2:
    return {
        "shrineId": input_.shrine_id,
        "nameJp": input_.name_jp,
        "address": input_.address,
        "latitude": input_.latitude,
        "longitude": input_.longitude,
        "goriyaku": input_.goriyaku,
        "goriyakuTags": list(input_.goriyaku_tags),
        "sajin": input_.sajin,
        "description": input_.description,
        "historyTheme": input_.history_theme,
        "element": input_.element,
        "placeTags": list(input_.place_tags),
    }


def _block(
    id_: DisplayBlockId,
    title: str,
    body: str | None,
    access: AccessLevel,
) -> ShrineMeaningDisplayBlockV2 | None:
    if not body:
        return None
    return {
        "id": id_,
        "title": title,
        "body": body,
        "access": access,
    }


def build_display_fields(generated: ShrineMeaningGeneratedV2) -> ShrineMeaningDisplayV2:
    maybe_blocks = [
        _block("hero", "今のあなたとの接点", generated["heroMeaningCopy"], "anonymous"),
        _block("consultation_summary", "相談との接続", generated["consultationSummary"], "free"),
        _block("shrine_meaning", "この神社をすすめる意味", generated["shrineMeaning"], "free"),
        _block("action_meaning", "参拝を置く意味", generated["actionMeaning"], "premium"),
        _block("history_context", "歴史文脈との接続", generated["historyContext"], "premium"),
        _block("deity_symbol", "祭神の象徴", generated["deitySymbolContext"], "premium"),
        _block("benefit_action", "ご利益と行動テーマ", generated["benefitActionContext"], "premium"),
    ]
    blocks = [block for block in maybe_blocks if block is not None]
    return {
        "blocks": blocks,
        "fallbackMessage": None if blocks else "神社の意味情報はまだ準備中です。",
    }


def compose_shrine_meaning_payload(source: Any) -> ShrineMeaningPayloadV2:
    """Build ShrineMeaningPayloadV2 from a Shrine-like object or dict."""

    input_ = normalize_shrine_meaning_source(source)
    generated = build_generated_fields(input_)
    return {
        "version": "v2",
        "source": build_source_fields(input_),
        "generated": generated,
        "display": build_display_fields(generated),
    }


__all__ = [
    "ShrineMeaningInput",
    "ShrineMeaningPayloadV2",
    "build_display_fields",
    "build_generated_fields",
    "build_source_fields",
    "compose_shrine_meaning_payload",
    "normalize_shrine_meaning_source",
]
