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


# --- ShrineHistoryStoryOverride TypedDict ---
class ShrineHistoryStoryOverride(TypedDict):
    subContext: str
    heroMeaningCopy: str
    shrineMeaning: str
    actionMeaning: str


HISTORY_THEME_CONTEXT: dict[str, str] = {
    "再出発": "切り替えや新しい一歩を支える文脈として受け取りやすい場所です。",
    "静寂": "刺激を増やさず、静かに心を整える文脈として受け取りやすい場所です。",
    "勝負": "決断や挑戦に向き合う文脈として受け取りやすい場所です。",
    "縁": "人や機会とのつながりを見直す文脈として受け取りやすい場所です。",
    "学び": "積み重ねや理解を深める文脈として受け取りやすい場所です。",
    "守り": "不安を鎮め、安心を得る文脈として受け取りやすい場所です。",
    "復興": "疲れや停滞を抱えた状態を、少しずつ整え直す文脈として受け取りやすい場所です。",
}

HISTORY_THEME_DISPLAY_COPY: dict[str, str] = {
    "再出発": "気持ちを切り替えたい時",
    "静寂": "静かに整えたい時",
    "勝負": "決断や挑戦の前",
    "縁": "人や機会とのつながりを見直したい時",
    "学び": "努力や積み重ねを整えたい時",
    "守り": "不安を落ち着けたい時",
    "復興": "疲れた状態を整え直したい時",

}


HISTORY_THEME_ACTION_CONTEXT: dict[str, str] = {
    "再出発": "今の状態を区切り、次の一歩を置きたい時に向き合いやすい神社です。",
    "静寂": "予定や情報を増やさず、静かに気持ちを整えたい時に向き合いやすい神社です。",
    "勝負": "判断前や挑戦前に、気持ちを固めたい時に向き合いやすい神社です。",
    "縁": "人間関係や機会との向き合い方を見直したい時に向き合いやすい神社です。",
    "学び": "努力を続ける前に、集中や積み重ねの方向を整えたい時に向き合いやすい神社です。",
    "守り": "不安を広げず、今の生活を落ち着いて守りたい時に向き合いやすい神社です。",
    "復興": "疲れや停滞を抱えた状態から、無理なく整え直したい時に向き合いやすい神社です。",

}



HISTORY_THEME_ACTION_RESULT_CONTEXT: dict[str, str] = {
    "再出発": "今の状態を区切り、次の一歩を置き直す",
    "静寂": "情報や刺激を減らし、気持ちを落ち着ける",
    "勝負": "判断を急がず、次の動きを整理する",
    "縁": "人や機会との向き合い方を見直す",
    "学び": "努力の方向を整え、集中し直す",
    "守り": "不安を広げず、今の生活を落ち着いて守る",
    "復興": "疲れや停滞を抱えた状態を、少しずつ整え直す",
}


# ---- HISTORY_THEME_SUB_CONTEXT ----
HISTORY_THEME_SUB_CONTEXT: dict[str, dict[str, str]] = {
    "勝負": {
        "覚悟": "迷いや不安を抱えたままでも、前に進む覚悟を固めたい時",
        "踏み出し": "迷いや不安を抱えたままでも、流れを変える一歩を踏み出したい時",
        "主導権": "受け身の流れから抜け、自分で次の動きを選び直したい時",
    },
    "縁": {
        "結び直し": "人や機会との関係を、落ち着いて見直したい時",
        "受け取り直し": "今あるつながりの意味を、急がず受け取り直したい時",
    },
}


# ---- SHRINE_HISTORY_STORY_OVERRIDES ----
SHRINE_HISTORY_STORY_OVERRIDES: dict[int, ShrineHistoryStoryOverride] = {
    17: {
        "subContext": "覚悟",
        "heroMeaningCopy": "三峯神社は、迷いや不安を抱えたままでも、前に進む覚悟を固めたい時に向き合いやすい神社です。",
        "shrineMeaning": "三峯神社は、険しい山中で信仰されてきた背景を持ち、簡単には進めない場面で覚悟を固める文脈と重ねて受け取りやすい神社です。",
        "actionMeaning": "参拝を、結果を急ぐためではなく、迷いを抱えたままでも一度腹を決め、次の一歩へ向かうための行動として置けます。",
    },
    14: {
        "subContext": "踏み出し",
        "heroMeaningCopy": "鹿島神宮は、迷いや不安を抱えたままでも、流れを変える一歩を踏み出したい時に向き合いやすい神社です。",
        "shrineMeaning": "鹿島神宮は、武神を祀る由緒を持ち、迷いを断ち、前へ進む判断を整える文脈と重ねて受け取りやすい神社です。",
        "actionMeaning": "参拝を、勝ち負けを急ぐためではなく、停滞した気持ちから主導権を取り戻し、次の動きを選び直す行動として置けます。",
    },
    4: {
        "subContext": "結び直し",
        "heroMeaningCopy": "出雲大社は、人や機会とのつながりを見直したい時に向き合いやすい神社です。",
        "shrineMeaning": "出雲大社は、縁結びの信仰で知られ、人との関係や機会の受け取り方を落ち着いて見直す文脈と重ねて受け取りやすい神社です。",
        "actionMeaning": "参拝を、良い縁を急いで求めるためではなく、今ある関係やこれから選びたいつながりを整理する行動として置けます。",
    },
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

    if hasattr(raw, "values_list"):
        try:
            return _clean_str_list(list(raw.values_list("name", flat=True)))
        except Exception:
            return ()

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


# hero:
# 今の自分との接点を返す
# 神社説明は禁止
# 歴史説明は禁止
# 「なぜ今この神社か」を短く返す

def _build_hero_meaning(input_: ShrineMeaningInput) -> str:
    override = SHRINE_HISTORY_STORY_OVERRIDES.get(input_.shrine_id)
    if override:
        return override["heroMeaningCopy"]
    if input_.history_theme:
        display_copy = HISTORY_THEME_DISPLAY_COPY.get(input_.history_theme, "今の状態を整えたい時")
        return f"{input_.name_jp}は、{display_copy}に向き合いやすい神社です。"
    if _primary_benefit(input_):
        return f"{input_.name_jp}は、今の願いや状態を一度整理する入口として置きやすい神社です。"
    return f"{input_.name_jp}は、今の状態を落ち着いて見直す候補として扱いやすい神社です。"

# consultation_summary:
# 今回の相談状態を整理する
# 神社説明は禁止
# 行動指示は禁止
# 「何を見直す段階か」を返す

def _build_consultation_summary(input_: ShrineMeaningInput) -> str:
    if input_.description or input_.history_theme:
        return "今回の相談は、いま何を優先して見直すべきかを整理しながら、次の判断軸を整えていく文脈として受け取れます。"
    if input_.goriyaku or input_.sajin or input_.element:
        return "今回の相談は、願いそのものを急いで決めるよりも、今の状態や優先順位を整理しながら向き合う文脈としてまとめられます。"
    return "今回の相談は、いま抱えているテーマを一度ほどき、何を先に見直すかを整理する段階として読むのが自然です。"


# shrine_meaning:
# なぜこの神社なのかを返す
# 神社固有文脈を扱う
# 歴史説明だけで終わらせない
# 「今の状態との接続」を含める

def _build_shrine_meaning(input_: ShrineMeaningInput) -> str:
    override = SHRINE_HISTORY_STORY_OVERRIDES.get(input_.shrine_id)
    if override:
        return override["shrineMeaning"]
    if input_.description:
        return f"{input_.name_jp}は「{_clip(input_.description)}」という特徴を持ち、今回の相談で主題になっている整理や見直しのテーマと接続しやすい神社です。"
    benefit = _primary_benefit(input_)
    if benefit:
        return f"{input_.name_jp}は「{_clip(benefit)}」に関わる文脈を持ち、今回の相談で求めている方向と結びつけて受け取りやすい神社です。"
    if input_.sajin:
        return f"{input_.name_jp}は、祭神の象徴を手がかりに、今回の相談テーマと接続して受け取りやすい神社です。"
    return f"{input_.name_jp}は、今回の相談で主題になっている整理や立て直しのテーマと接続しやすく、意味を重ねて受け取りやすい候補です。"


# action_meaning:
# なぜ参拝という行動を置くのかを返す
# 結果保証は禁止
# 行動理由へ翻訳する
# 「次の一歩」を扱う

def _build_action_meaning(input_: ShrineMeaningInput) -> str:
    override = SHRINE_HISTORY_STORY_OVERRIDES.get(input_.shrine_id)
    if override:
        return override["actionMeaning"]
    benefit = _primary_benefit(input_)
    theme_action = HISTORY_THEME_ACTION_CONTEXT.get(input_.history_theme or "")
    if benefit and theme_action:
        return f"参拝を、{_clip(benefit, 32)}という願いを急いで叶えるためではなく、{theme_action}"
    if benefit:
        return f"参拝を、{_clip(benefit, 32)}という願いを急いで叶えるためではなく、今の状態を整理して次の一歩を置く行動として扱えます。"
    if theme_action:
        return f"参拝を、{theme_action}"
    return "参拝を、考え続ける状態から少し離れ、現実の一歩へ移すための行動として置けます。"

# history_context:
# 歴史・土地・背景を状態理解へ接続する
# Wikipedia説明は禁止
# 固有名詞紹介で終わらせない
# 「だから今の状態と接続する」を返す

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

# benefit_action:
# ご利益を行動テーマへ翻訳する
# 願望成就の断定は禁止
# 「今の自分ならどう置くか」を返す
# 結果ではなく状態変化へ寄せる

def _build_benefit_action_context(input_: ShrineMeaningInput) -> str | None:
    benefit = _primary_benefit(input_)
    if not benefit:
        return None
    action_result = HISTORY_THEME_ACTION_RESULT_CONTEXT.get(input_.history_theme or "")
    if action_result:
        return (
            f"「{_clip(benefit)}」は結果を急ぐためではなく、"
            f"{action_result}きっかけとして受け取りやすい要素です。"
        )
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
    "HISTORY_THEME_SUB_CONTEXT",
    "SHRINE_HISTORY_STORY_OVERRIDES",
    "ShrineHistoryStoryOverride",
    "build_display_fields",
    "build_generated_fields",
    "build_source_fields",
    "compose_shrine_meaning_payload",
    "normalize_shrine_meaning_source",
]
