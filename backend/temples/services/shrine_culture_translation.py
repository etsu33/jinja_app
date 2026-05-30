"""Cultural translation dictionary for shrine meaning payloads.

This module keeps shrine-specific cultural context outside the generic payload
composer. The goal is not to explain shrine knowledge as trivia, but to
translate history, faith, landscape, and benefit themes into user-facing
meaning and action language.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShrineCultureTranslation:
    """Shrine-specific cultural translation used by meaning composer."""

    landscape_tags: tuple[str, ...]
    faith_tags: tuple[str, ...]
    body_feeling_tags: tuple[str, ...]
    historical_background: str
    place_meaning: str
    flow_guidance: str
    action_reason: str
    benefit_translation: str


BLOCKED_CULTURE_WORDS: tuple[str, ...] = (
    "強エネルギー",
    "波動",
    "覚醒",
    "人生が変わる",
    "人を選ぶ",
    "運気が上がる",
)


SHRINE_CULTURE_TRANSLATIONS: dict[int, ShrineCultureTranslation] = {
    17: ShrineCultureTranslation(
        landscape_tags=("山", "境界"),
        faith_tags=("守護", "修験", "浄化"),
        body_feeling_tags=("静けさ", "圧", "境界"),
        historical_background=(
            "三峯神社は、山深い地で自然への畏れや守りの感覚を受け継いできた神社です。"
            "狼は単なる象徴ではなく、山の境界を守る存在として信仰されてきました。"
        ),
        place_meaning=(
            "開けた場所で勢いをつけるというより、山の静けさの中で余計なものを削ぎ落とし、"
            "迷いが残っていても次の一歩を決める感覚に近い場所です。"
        ),
        flow_guidance=(
            "今は、答えを急いで探し切るより、山の静けさの中で、"
            "迷いを抱えたままでも進む方向を一つ決める方が合っています。"
        ),
        action_reason=(
            "まずは大きな結論ではなく、今いちばん決めきれていない問いを一つだけ心に置く感覚で向き合えます。"
        ),
        benefit_translation=(
            "仕事運は結果を急ぐためではなく、決断・主導権・切替を見直すための手がかりとして扱います。"
        ),
    ),
    14: ShrineCultureTranslation(
        landscape_tags=("境界", "東国"),
        faith_tags=("守護", "起動", "突破"),
        body_feeling_tags=("前進", "切替", "境界"),
        historical_background=(
            "鹿島神宮は、武神・剣神として信仰される武甕槌大神を祀り、"
            "国譲りや神武東征の物語と結びついてきた神社です。"
            "古くから旅立ちや勝負の前に、進む方向を定める場所として信仰されてきました。"
        ),
        place_meaning=(
            "三峯神社が山の静けさの中で整える場所なら、"
            "鹿島神宮は迷いを断ち、次の局面へ踏み出す感覚に近い場所です。"
        ),
        flow_guidance=(
            "今は、迷いを抱えたまま立ち止まるより、"
            "進む方向を一つ決めて動き始める方が合っています。"
        ),
        action_reason=(
            "まずは大きな勝ち負けではなく、今日動かしたい方向と、"
            "手放したい迷いを一つずつ確認する感覚で向き合えます。"
        ),
        benefit_translation=(
            "勝運・仕事運は結果を急ぐためではなく、決断・主導権・切替を明確にし、"
            "次の局面へ踏み出すための手がかりとして扱います。"
        ),
    ),
}


def get_shrine_culture_translation(shrine_id: int) -> ShrineCultureTranslation | None:
    """Return shrine-specific cultural translation when available."""

    return SHRINE_CULTURE_TRANSLATIONS.get(shrine_id)
