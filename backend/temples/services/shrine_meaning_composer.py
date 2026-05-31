"""Shrine Meaning Payload v2 composer.

This module builds a frontend-friendly meaning payload for shrine detail pages.
It intentionally does not depend on DRF serializers or views so it can be tested
as a small service before wiring an endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping, TypedDict
from temples.services.shrine_culture_translation import get_shrine_culture_translation


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
    "today_flow",
    "after_visit_reflection",
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
    todayFlowContext: str | None
    afterVisitReflection: str | None


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
    "勝負": "決断前に、一度立ち止まって覚悟を固めるために信仰されてきた場所です。",
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

BENEFIT_STATE_THEME_MAP: dict[str, tuple[str, ...]] = {
    "仕事運": ("決断", "主導権", "継続", "切替", "集中"),
    "商売繁盛": ("信頼形成", "循環", "継続", "受け渡し"),
    "勝運": ("決断", "主導権", "停滞打破", "勝負前の整理"),
    "縁結び": ("関係整理", "距離感", "受け取り直し", "選び直し"),
    "厄除け": ("不安整理", "境界線", "守り", "リスク回避"),
    "開運": ("切替", "停滞打破", "新しい流れ"),
    "学業成就": ("集中", "積み重ね", "理解", "継続"),
    "家内安全": ("土台確認", "安心", "生活維持"),
    "交通安全": ("移動前の確認", "無事に進む", "境界越え"),
    "航海安全": ("移動前の確認", "無事に進む", "境界越え"),
    "海上安全": ("移動前の確認", "無事に進む", "境界越え"),
    "金運": ("循環", "選択", "使い方", "商い"),
    "美容": ("自己回復", "見せ方", "整え直し"),
    "芸能運": ("表現", "継続", "技を磨く"),
    "技芸上達": ("表現", "継続", "技を磨く"),
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


CULTURAL_FLOW_CONTEXT: dict[str, str] = {
    "再出発": "今は、過去の延長で考え続けるより、一度区切りを置いて流れを作り直す方が合いやすい時期です。",
    "静寂": "今は、外へ答えを探しに行くより、情報や刺激を減らして静かに見直す方が合いやすい時期です。",
    "勝負": "今は、迷いを整理し続けるより、次に動かす方向を一つ決める方が流れを作りやすい時期です。",
    "縁": "今は、新しいつながりを急いで増やすより、今ある関係や機会の意味を見直す方が合いやすい時期です。",
    "学び": "今は、手を広げるより、積み重ねる対象を一つに絞る方が理解を深めやすい時期です。",
    "守り": "今は、大きく変えるより、不安を広げないために今の土台を静かに確認する方が合いやすい時期です。",
    "復興": "今は、無理に元へ戻そうとするより、疲れや停滞を少しずつ整え直す方が合いやすい時期です。",
}


def _cultural_flow_context(input_: ShrineMeaningInput) -> str | None:
    if not input_.history_theme:
        return None
    return CULTURAL_FLOW_CONTEXT.get(input_.history_theme)


# ---- SHRINE_HISTORY_STORY_OVERRIDES ----
SHRINE_HISTORY_STORY_OVERRIDES: dict[int, ShrineHistoryStoryOverride] = {
    17: {
        "subContext": "覚悟",
        "heroMeaningCopy": "三峯神社は、迷いや不安を抱えたままでも、前に進む覚悟を固めたい時に向き合いやすい神社です。",
        "shrineMeaning": "三峯神社は、山深い地で自然への祈りや狼を守りの象徴として受け継いできた神社です。迷いを消してから進むのではなく、不安を抱えたままでも一度腹を決める感覚と結びつきやすい場所です。",
        "actionMeaning": "参拝前に、今いちばん決めきれていないことを一つだけ書き出します。参拝中は、その答えを急がず、一つの問いとして心に置いてみます。",
    },
    14: {
        "subContext": "踏み出し",
        "heroMeaningCopy": "鹿島神宮は、迷いや不安を抱えたままでも、流れを変える一歩を踏み出したい時に向き合いやすい神社です。",
        "shrineMeaning": "鹿島神宮は、武神を祀る由緒を持ち、停滞した状況から主導権を取り戻し、次の動きを選び直す感覚と結びつきやすい神社です。",
        "actionMeaning": "参拝前に、今止まっている理由を一つだけ言葉にします。参拝中は、変えたい流れを一つに絞り、今日動かしたい方向を静かに確認します。",
    },
    4: {
        "subContext": "結び直し",
        "heroMeaningCopy": "出雲大社は、人や機会とのつながりを見直したい時に向き合いやすい神社です。",
        "shrineMeaning": "出雲大社は、縁結びの信仰で知られ、関係を増やすよりも、今あるつながりやこれから選びたい縁を見直す感覚と結びつきやすい神社です。",
        "actionMeaning": "参拝前に、今大切にしたい関係を一つだけ思い浮かべます。参拝中は、急いで答えを出さず、自分から整えたい関わり方を静かに確認します。",
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


def _benefit_labels(input_: ShrineMeaningInput) -> tuple[str, ...]:
    labels: list[str] = []
    seen: set[str] = set()

    for source in (*input_.goriyaku_tags, input_.goriyaku or ""):
        for label in _clean_str_list(source):
            if label in seen:
                continue
            seen.add(label)
            labels.append(label)

    return tuple(labels)


def _benefit_state_themes(input_: ShrineMeaningInput) -> tuple[str, ...]:
    themes: list[str] = []
    seen: set[str] = set()

    for label in _benefit_labels(input_):
        for theme in BENEFIT_STATE_THEME_MAP.get(label, ()):
            if theme in seen:
                continue
            seen.add(theme)
            themes.append(theme)

    return tuple(themes)


# Helper functions for context specificity
def _has_culture_translation(input_: ShrineMeaningInput) -> bool:
    return get_shrine_culture_translation(input_.shrine_id) is not None


def _has_story_override(input_: ShrineMeaningInput) -> bool:
    return input_.shrine_id in SHRINE_HISTORY_STORY_OVERRIDES


def _has_history_theme(input_: ShrineMeaningInput) -> bool:
    return bool(input_.history_theme and input_.history_theme in HISTORY_THEME_CONTEXT)


def _has_specific_context(input_: ShrineMeaningInput) -> bool:
    """Return whether this shrine has enough shrine-specific context for stronger meaning copy.

    Strong meaning copy should be used only when the shrine has curated cultural
    translation, an explicit story override, or a known history_theme.
    Generic benefit-only data is intentionally not treated as shrine-specific.
    """

    return (
        _has_culture_translation(input_)
        or _has_story_override(input_)
        or _has_history_theme(input_)
    )


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
        return f"{input_.name_jp}は、願いごとを手がかりに候補として確認しやすい神社です。"
    return f"{input_.name_jp}は、基本情報をもとに参拝先の候補として確認しやすい神社です。"

# consultation_summary:
# Free/Premium共通の「今の状態」を返す
# ユーザーの相談状態だけを整理する
# 神社説明は禁止
# 行動指示は禁止
# 「何を見直す段階か」を短く返す

def _build_consultation_summary(input_: ShrineMeaningInput) -> str:
    flow_context = _cultural_flow_context(input_)
    if flow_context:
        return f"{flow_context} 気になっていることを一つに絞ると、次の判断が見えやすくなります。"
    if _has_specific_context(input_):
        return "今は答えを急ぐより、何を決めきれていないのかを一つに絞る状態です。まず優先順位を見直す方が、次の判断に進みやすくなります。"
    return "相談内容に対して、まず気になっていることを一つに絞るための候補です。神社側の情報だけで状態を決めつけず、参拝先を選ぶ前の整理材料として扱います。"


# shrine_meaning:
# Freeの主表示「この場所が合う理由」を返す
# 神社固有文脈と今の状態の接続を扱う
# 神社説明だけで終わらせない
# Premium向けの深い個人解釈はここに混ぜない

def _build_shrine_meaning(input_: ShrineMeaningInput) -> str:
    culture = get_shrine_culture_translation(input_.shrine_id)
    if culture:
        return f"{culture.historical_background}{culture.place_meaning}"

    override = SHRINE_HISTORY_STORY_OVERRIDES.get(input_.shrine_id)
    if override:
        return override["shrineMeaning"]
    if input_.history_theme:
        history_context = HISTORY_THEME_CONTEXT.get(input_.history_theme)
        if history_context:
            return f"{input_.name_jp}は、{history_context} 今回の相談を整理する補助材料として受け取りやすい神社です。"
    if input_.description:
        return f"{input_.name_jp}には「{_clip(input_.description)}」という情報があります。現時点では、その公開情報を参拝先を選ぶための手がかりとして扱います。"
    benefit = _primary_benefit(input_)
    if benefit:
        return f"{input_.name_jp}は「{_clip(benefit)}」に関わる神社として確認できます。現時点では、願いごとの方向性を整理するための候補として扱います。"
    if input_.sajin:
        return f"{input_.name_jp}は、祭神の情報を手がかりに確認できる神社です。現時点では、相談内容との強い接続は断定せず、参拝先を選ぶための補助情報として扱います。"
    return f"{input_.name_jp}は、登録されている基本情報をもとに確認できる神社です。詳しい固有文脈は、今後の情報整備に合わせて補足します。"


# action_meaning:
# Free/Premium共通の「ここで試したいこと」を返す
# 参拝前・参拝中の行動だけを扱う
# 参拝後・帰り道・保存後の振り返りは禁止
# 結果保証は禁止
# 「次の一歩」を具体化する

def _build_action_meaning(input_: ShrineMeaningInput) -> str:
    override = SHRINE_HISTORY_STORY_OVERRIDES.get(input_.shrine_id)
    if override:
        return override["actionMeaning"]
    benefit = _primary_benefit(input_)
    theme_action = HISTORY_THEME_ACTION_CONTEXT.get(input_.history_theme or "")
    if benefit and theme_action:
        return f"参拝を、{_clip(benefit, 32)}という願いを急いで叶えるためではなく、{theme_action}"
    if theme_action:
        return f"参拝を、{theme_action}"
    if benefit:
        return f"参拝前に、{_clip(benefit, 32)}という願いの中で今いちばん整理したいことを一つだけ確認します。結果を急がず、参拝先を選ぶ前の小さな整理として扱います。"
    return "参拝前に、今気になっていることを一つだけ確認します。神社側の情報だけで意味を決めつけず、静かに整理するための候補として扱います。"

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

    culture = get_shrine_culture_translation(input_.shrine_id)
    if culture:
        return culture.benefit_translation

    action_result = HISTORY_THEME_ACTION_RESULT_CONTEXT.get(input_.history_theme or "")
    state_themes = _benefit_state_themes(input_)
    if state_themes:
        theme_text = "・".join(state_themes[:3])
        return (
            f"「{_clip(benefit)}」は結果を急ぐためではなく、"
            f"{theme_text}を見直すための手がかりとして扱います。"
        )
    if action_result:
        return (
            f"「{_clip(benefit)}」は結果を急ぐためではなく、"
            f"{action_result}きっかけとして受け取りやすい要素です。"
        )
    return f"「{_clip(benefit)}」は願望成就の断定ではなく、今の行動テーマを整える補助軸として扱います。"


#
# today_flow:
# 削除候補
# consultation_summary と状態整理の責務が重複しやすい
# すぐには削除せず、frontend/API依存を確認してから判断する
def _build_today_flow_context(input_: ShrineMeaningInput) -> str | None:
    culture = get_shrine_culture_translation(input_.shrine_id)
    if culture:
        return f"{culture.flow_guidance}{culture.action_reason}"

    flow_context = _cultural_flow_context(input_)
    if flow_context:
        return "今日は、結論を急がず、次の一歩を小さく試す日として置けます。まずは考えを増やさず、実際に動いて確かめることを優先します。"

    if not input_.history_theme:
        return None
    return "今日は、結論を出す日ではなく、次の一歩を小さく試す日として置けます。考えを増やすより、実際に動いて確かめることを優先します。"


#
# after_visit_reflection:
# Premium寄りの「参拝後に見直したいこと」を返す
# 帰り道・保存後・再相談につながる振り返りだけを扱う
# 参拝前・参拝中の行動指示は禁止
# 実際に参拝しなければ価値がない表現にしない
# 参拝後に何を持ち帰るかを扱う
def _build_after_visit_reflection(input_: ShrineMeaningInput) -> str | None:
    if not input_.history_theme:
        return None
    return "参拝後は、答えが出たかどうかより、次の一歩が少し見えたかを見直します。迷いが残っていても、保存した内容やもう一度の相談から整理し直せます。"


def build_generated_fields(input_: ShrineMeaningInput) -> ShrineMeaningGeneratedV2:
    return {
        "heroMeaningCopy": _build_hero_meaning(input_),
        "consultationSummary": _build_consultation_summary(input_),
        "shrineMeaning": _build_shrine_meaning(input_),
        "actionMeaning": _build_action_meaning(input_),
        "historyContext": _build_history_context(input_),
        "deitySymbolContext": _build_deity_symbol_context(input_),
        "benefitActionContext": _build_benefit_action_context(input_),
        "todayFlowContext": _build_today_flow_context(input_),
        "afterVisitReflection": _build_after_visit_reflection(input_),
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

#
# display responsibility:
# Free表示順:
# 1. 今のあなたとの接点: 今の状態に合う入口コピー
# 2. 今の状態: 相談状態の整理
# 3. この場所が合う理由: 神社固有文脈と今の状態の接続
# 4. ここで試したいこと: 参拝前・参拝中の具体行動。Freeでは行動の入口まで見せる
#
# Premium表示順:
# 5. 参拝後に見直したいこと: 帰り道・保存後・再相談につながる振り返り。Premiumでは変化記録へつなげる
# 6. この神社の背景: 補足としての歴史文脈
# 7. 祭神の象徴: 補足としての象徴情報
# 8. ご利益を行動に置き換える: 補足としてのご利益翻訳
# 9. today_flow: 削除候補。consultation_summary と責務が重複するため、依存確認後に整理する
def build_display_fields(generated: ShrineMeaningGeneratedV2) -> ShrineMeaningDisplayV2:
    maybe_blocks = [
        _block("hero", "今のあなたとの接点", generated["heroMeaningCopy"], "anonymous"),
        _block("shrine_meaning", "この場所が合う理由", generated["shrineMeaning"], "free"),
        _block("consultation_summary", "今の状態", generated["consultationSummary"], "free"),
        # _block("today_flow", "今日の向き合い方", generated["todayFlowContext"], "premium"),
        _block("action_meaning", "ここで試したいこと", generated["actionMeaning"], "premium"),
        _block("after_visit_reflection", "参拝後に見直したいこと", generated["afterVisitReflection"], "premium"),
        _block("history_context", "この神社の背景", generated["historyContext"], "premium"),
        _block("deity_symbol", "祭神の象徴", generated["deitySymbolContext"], "premium"),
        _block("benefit_action", "ご利益を行動に置き換える", generated["benefitActionContext"], "premium"),
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
    "_has_specific_context",
    "ShrineHistoryStoryOverride",
    "build_display_fields",
    "build_generated_fields",
    "build_source_fields",
    "compose_shrine_meaning_payload",
    "normalize_shrine_meaning_source",
]
