

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

HistoryTheme = Literal["守り", "静寂", "再出発", "復興", "勝負", "学び", "縁"]
ActionCategory = Literal["reflect", "prepare", "connect", "visit", "record"]
ActionTiming = Literal["before_visit", "during_visit", "after_visit", "anytime"]
ActionDifficulty = Literal["easy", "normal"]
ActionTimeEstimate = Literal["3min", "10min", "30min"]


@dataclass(frozen=True)
class ActionSuggestion:
    id: str
    history_theme: str
    title: str
    description: str
    category: ActionCategory
    timing: ActionTiming
    difficulty: ActionDifficulty
    time_estimate: ActionTimeEstimate
    measurement_key: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


DEFAULT_HISTORY_THEME = "静寂"


HISTORY_THEME_ACTION_SUGGESTIONS: dict[str, tuple[ActionSuggestion, ...]] = {
    "守り": (
        ActionSuggestion(
            id="protect_write_anxieties",
            history_theme="守り",
            title="不安を3つだけ書く",
            description="今気になっている不安を3つだけ書き出し、今日扱うものを1つに絞ります。",
            category="reflect",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="mamori_reflect_anxieties",
        ),
        ActionSuggestion(
            id="protect_check_route_day",
            history_theme="守り",
            title="無理なく行ける日を1つ候補にする",
            description="経路や予定を確認し、負担が少ない参拝候補日を1つだけ選びます。",
            category="visit",
            timing="before_visit",
            difficulty="easy",
            time_estimate="10min",
            measurement_key="mamori_prepare_visit_day",
        ),
    ),
    "静寂": (
        ActionSuggestion(
            id="silence_turn_off_notifications",
            history_theme="静寂",
            title="3分だけ通知を切る",
            description="通知を切り、今考えすぎていることを1行だけメモします。",
            category="reflect",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="seijaku_reflect_notifications_off",
        ),
        ActionSuggestion(
            id="silence_record_after_visit",
            history_theme="静寂",
            title="参拝後の変化を一言だけ残す",
            description="参拝後に、気持ちが少し変わった点を一言だけ記録します。",
            category="record",
            timing="after_visit",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="seijaku_record_after_visit",
        ),
    ),
    "再出発": (
        ActionSuggestion(
            id="restart_write_stop_start",
            history_theme="再出発",
            title="やめたいことと始めたいことを書く",
            description="今やめたいことを1つ、始めたいことを1つ書き、切り替えの入口を作ります。",
            category="reflect",
            timing="anytime",
            difficulty="easy",
            time_estimate="10min",
            measurement_key="saishuppatsu_reflect_stop_start",
        ),
        ActionSuggestion(
            id="restart_choose_next_step",
            history_theme="再出発",
            title="次に動くことを1つ保存する",
            description="参拝後に、次の一歩として実行できる小さな行動を1つ保存します。",
            category="record",
            timing="after_visit",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="saishuppatsu_record_next_step",
        ),
    ),
    "復興": (
        ActionSuggestion(
            id="recovery_write_done_one",
            history_theme="復興",
            title="今日できたことを1つ書く",
            description="大きな成果ではなく、今日できた小さなことを1つだけ確認します。",
            category="reflect",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="fukkou_reflect_done_one",
        ),
        ActionSuggestion(
            id="recovery_remove_one_burden",
            history_theme="復興",
            title="無理を減らす予定を1つ決める",
            description="回復の邪魔になっている予定や負担を1つだけ軽くします。",
            category="prepare",
            timing="anytime",
            difficulty="normal",
            time_estimate="10min",
            measurement_key="fukkou_prepare_reduce_burden",
        ),
    ),
    "勝負": (
        ActionSuggestion(
            id="challenge_choose_this_week",
            history_theme="勝負",
            title="今週勝負したいことを1つ決める",
            description="気合いではなく、今週動かす対象を1つに絞ります。",
            category="prepare",
            timing="anytime",
            difficulty="easy",
            time_estimate="10min",
            measurement_key="shoubu_prepare_weekly_focus",
        ),
        ActionSuggestion(
            id="challenge_send_one_message",
            history_theme="勝負",
            title="先延ばししている連絡を1つ送る",
            description="挑戦の入口として、止めていた連絡を1つだけ送ります。",
            category="connect",
            timing="anytime",
            difficulty="normal",
            time_estimate="10min",
            measurement_key="shoubu_connect_send_message",
        ),
    ),
    "学び": (
        ActionSuggestion(
            id="learning_choose_scope",
            history_theme="学び",
            title="今日学ぶ範囲を1つに絞る",
            description="完璧な計画ではなく、今日扱う学習範囲を1つだけ決めます。",
            category="prepare",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="manabi_prepare_scope",
        ),
        ActionSuggestion(
            id="learning_note_question",
            history_theme="学び",
            title="分からないことを1つメモする",
            description="次に調べるために、今分からないことを1つだけ残します。",
            category="record",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="manabi_record_question",
        ),
    ),
    "縁": (
        ActionSuggestion(
            id="connection_choose_one_person",
            history_theme="縁",
            title="連絡したい人を1人だけ選ぶ",
            description="今つながり直したい人を1人だけ選び、無理のない接点を考えます。",
            category="connect",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="en_connect_choose_person",
        ),
        ActionSuggestion(
            id="connection_write_gratitude",
            history_theme="縁",
            title="感謝を伝えたい相手を1人思い出す",
            description="関係を動かす前に、感謝を伝えたい相手を1人思い出します。",
            category="reflect",
            timing="anytime",
            difficulty="easy",
            time_estimate="3min",
            measurement_key="en_reflect_gratitude",
        ),
    ),
}


def normalize_history_theme(history_theme: str | None) -> str:
    value = str(history_theme or "").strip()
    if value in HISTORY_THEME_ACTION_SUGGESTIONS:
        return value
    return DEFAULT_HISTORY_THEME


def get_action_suggestions_for_theme(
    history_theme: str | None,
    *,
    limit: int = 2,
) -> list[dict[str, str]]:
    normalized_theme = normalize_history_theme(history_theme)
    suggestions = HISTORY_THEME_ACTION_SUGGESTIONS[normalized_theme]
    safe_limit = max(0, int(limit))
    return [suggestion.to_dict() for suggestion in suggestions[:safe_limit]]
