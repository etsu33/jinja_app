from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from temples.models import Shrine
from temples.services.concierge_chat import build_chat_recommendations


OUTPUT_PATH = Path("docs/analytics/recommendation-output-snapshot.md")


@dataclass(frozen=True)
class RepresentativeCase:
    id: str
    title: str
    query: str
    expected_need_tags: tuple[str, ...]
    expected_history_theme: tuple[str, ...]
    public_mode: str = "need"
    flow: str = "A"
    birthdate: str | None = None
    extra_condition: str | None = None


REPRESENTATIVE_CASES: tuple[RepresentativeCase, ...] = (
    RepresentativeCase(
        id="career-anxiety",
        title="転職不安",
        query="転職が不安で、背中を押してほしい",
        expected_need_tags=("career", "mental", "courage"),
        expected_history_theme=("勝負", "導き", "再出発"),
    ),
    RepresentativeCase(
        id="rest-quiet",
        title="疲労回復",
        query="最近疲れていて、静かに落ち着きたい",
        expected_need_tags=("mental", "rest"),
        expected_history_theme=("静寂", "復興"),
        extra_condition="静かに過ごしたい",
    ),
    RepresentativeCase(
        id="money-business-flow",
        title="金運・事業",
        query="売上を伸ばしたい。事業の流れを良くしたい",
        expected_need_tags=("money", "career", "courage"),
        expected_history_theme=("巡り", "勝負"),
    ),
    RepresentativeCase(
        id="relationship-marriage",
        title="縁結び",
        query="良縁がほしい。人との関係を見直したい",
        expected_need_tags=("marriage", "relationship", "love"),
        expected_history_theme=("縁",),
    ),
    RepresentativeCase(
        id="study-focus",
        title="学業・集中",
        query="資格試験に合格したい。集中したい",
        expected_need_tags=("study", "focus"),
        expected_history_theme=("学び",),
    ),
    RepresentativeCase(
        id="protection-cleansing",
        title="厄除け・浄化",
        query="最近流れが悪い。厄を落としたい",
        expected_need_tags=("protection", "mental", "courage"),
        expected_history_theme=("浄化", "守り", "巡り"),
    ),
    RepresentativeCase(
        id="travel-safe",
        title="旅行・出張安全",
        query="出張前に安全に移動したい",
        expected_need_tags=("travel_safe",),
        expected_history_theme=("導き", "守り"),
    ),
    RepresentativeCase(
        id="compat-career",
        title="相性補助ありの仕事相談",
        query="仕事の流れを整えて、次の一歩を決めたい",
        expected_need_tags=("career", "courage"),
        expected_history_theme=("導き", "勝負", "再出発"),
        public_mode="compat",
        flow="B",
        birthdate="1988-03-12",
    ),
)


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _candidate_from_shrine(shrine: Shrine) -> dict[str, Any]:
    return {
        "id": shrine.id,
        "shrine_id": shrine.id,
        "name": shrine.name_jp,
        "display_name": shrine.name_jp,
        "address": getattr(shrine, "address", None),
        "latitude": getattr(shrine, "latitude", None),
        "longitude": getattr(shrine, "longitude", None),
        "goriyaku": getattr(shrine, "goriyaku", None),
        "description": getattr(shrine, "description", None),
        "history_theme": getattr(shrine, "history_theme", None),
        "element": getattr(shrine, "element", None),
        "place_tags": getattr(shrine, "place_tags", None) or [],
        "visit_style_tags": getattr(shrine, "visit_style_tags", None) or [],
        "astro_tags": getattr(shrine, "astro_tags", None) or [],
        "astro_elements": getattr(shrine, "astro_elements", None) or [],
        "popular_score": getattr(shrine, "popular_score", 0.0),
        "goriyaku_tag_ids": list(shrine.goriyaku_tags.values_list("id", flat=True)),
    }


def _load_candidates(limit: int) -> list[dict[str, Any]]:
    shrines = (
        Shrine.objects.all()
        .prefetch_related("goriyaku_tags")
        .order_by("id")[:limit]
    )
    return [_candidate_from_shrine(shrine) for shrine in shrines]


def _text_or_dash(value: Any) -> str:
    text = str(value or "").strip()
    return text or "-"


def _join_or_dash(values: Any) -> str:
    if not values:
        return "-"
    if isinstance(values, (list, tuple, set)):
        return " / ".join(str(v) for v in values if str(v).strip()) or "-"
    return str(values)


def _format_component_table(score_v2: dict[str, Any]) -> list[str]:
    components = _safe_dict(score_v2.get("components"))
    rows = [
        "| component | value |",
        "|---|---:|",
    ]
    for key in (
        "user_state_match",
        "shrine_meaning_match",
        "context_match",
        "element_match",
        "distance_score",
        "popularity_score",
        "astro_bonus",
        "behavior_signal",
        "behavior_contribution",
        "capped_behavior_contribution",
        "behavior_ratio",
        "direction_bonus",
    ):
        value = components.get(key)
        if isinstance(value, float):
            rendered = f"{value:.4f}"
        else:
            rendered = _text_or_dash(value)
        rows.append(f"| `{key}` | {rendered} |")
    return rows


def _format_recommendation(rec: dict[str, Any], rank: int) -> list[str]:
    score_v2 = _safe_dict(rec.get("score_v2"))
    rank_explanation = _safe_dict(rec.get("rank_explanation"))
    rank_comparison = _safe_dict(rec.get("rank_comparison"))
    explanation_payload = _safe_dict(rec.get("_explanation_payload"))
    breakdown = _safe_dict(rec.get("breakdown"))
    payload_primary_reason = _safe_dict(explanation_payload.get("primary_reason"))
    payload_history_context = _safe_dict(explanation_payload.get("history_context"))
    payload_score_v2 = _safe_dict(explanation_payload.get("score_v2"))
    payload_action_suggestions = explanation_payload.get("action_suggestions") or []
    payload_action_titles = [
        str(item.get("title") or "").strip()
        for item in payload_action_suggestions
        if isinstance(item, dict) and str(item.get("title") or "").strip()
    ]

    lines = [
        f"#### {rank}. {_text_or_dash(rec.get('display_name') or rec.get('name'))}",
        "",
        f"- shrine_id: `{_text_or_dash(rec.get('shrine_id') or rec.get('id'))}`",
        f"- history_theme: `{_text_or_dash(rec.get('history_theme') or payload_history_context.get('theme'))}`",
        f"- reason_source: `{_text_or_dash(rec.get('reason_source'))}`",
        f"- action_state: `{_text_or_dash(rec.get('action_state'))}`",
        f"- matched_need_tags: `{_join_or_dash(breakdown.get('matched_need_tags'))}`",
        f"- matched_visit_style_tags: `{_join_or_dash((_safe_dict(score_v2.get('signals'))).get('matched_visit_style_tags'))}`",
        f"- score_v2.total: `{_text_or_dash(score_v2.get('total'))}`",
        "",
        "##### score_v2.components",
        "",
        *_format_component_table(score_v2),
        "",
        "##### rank_explanation",
        "",
        f"- summary: {_text_or_dash(rank_explanation.get('summary'))}",
        f"- primary_axis: `{_text_or_dash(rank_explanation.get('primary_axis'))}`",
        f"- top_contributors: `{_join_or_dash(rank_explanation.get('top_contributors'))}`",
        "",
        "##### rank_comparison",
        "",
        f"- label: {_text_or_dash(rank_comparison.get('label'))}",
        f"- summary: {_text_or_dash(rank_comparison.get('summary'))}",
        f"- top_summary: {_text_or_dash(rank_comparison.get('top_summary'))}",
        "",
        "##### _explanation_payload",
        "",
        f"- matched_need_tags: `{_join_or_dash(explanation_payload.get('matched_need_tags'))}`",
        f"- primary_need_tag: `{_text_or_dash(explanation_payload.get('primary_need_tag'))}`",
        f"- primary_need_label_ja: `{_text_or_dash(explanation_payload.get('primary_need_label_ja'))}`",
        f"- primary_reason.type: `{_text_or_dash(payload_primary_reason.get('type'))}`",
        f"- primary_reason.label: `{_text_or_dash(payload_primary_reason.get('label'))}`",
        f"- primary_reason.label_ja: `{_text_or_dash(payload_primary_reason.get('label_ja'))}`",
        f"- primary_reason.evidence: `{_join_or_dash(payload_primary_reason.get('evidence'))}`",
        f"- primary_reason.score: `{_text_or_dash(payload_primary_reason.get('score'))}`",
        f"- history_context.theme: `{_text_or_dash(payload_history_context.get('theme'))}`",
        f"- history_context.label: `{_text_or_dash(payload_history_context.get('label'))}`",
        f"- history_context.tone: {_text_or_dash(payload_history_context.get('tone'))}",
        f"- action_suggestions: `{_join_or_dash(payload_action_titles)}`",
        f"- score_v2.total: `{_text_or_dash(payload_score_v2.get('total'))}`",
        "",
    ]
    return lines


def _format_case(case: RepresentativeCase, recs: dict[str, Any]) -> list[str]:
    need_payload = _safe_dict(recs.get("_need"))
    recommendations = _safe_list(recs.get("recommendations"))[:3]
    response_meta = _safe_dict(recs.get("response_meta"))

    lines = [
        f"## {case.title}",
        "",
        f"- case_id: `{case.id}`",
        f"- query: {case.query}",
        f"- public_mode: `{case.public_mode}`",
        f"- flow: `{case.flow}`",
        f"- birthdate: `{_text_or_dash(case.birthdate)}`",
        f"- extra_condition: `{_text_or_dash(case.extra_condition)}`",
        f"- expected_need_tags: `{_join_or_dash(case.expected_need_tags)}`",
        f"- actual_need_tags: `{_join_or_dash(need_payload.get('tags'))}`",
        f"- expected_history_theme: `{_join_or_dash(case.expected_history_theme)}`",
        f"- displayed_count: `{_text_or_dash(response_meta.get('displayed_count'))}`",
        "",
    ]

    if not recommendations:
        lines.extend(["_No recommendations returned._", ""])
        return lines

    for index, rec in enumerate(recommendations, start=1):
        if isinstance(rec, dict):
            lines.extend(_format_recommendation(rec, index))

    return lines


def _build_markdown(*, cases: tuple[RepresentativeCase, ...], candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# Recommendation Output Snapshot",
        "",
        "## 目的",
        "",
        "Representative case ごとの Recommendation Score v2 実出力を保存する。",
        "",
        "この snapshot は、推薦結果が検索結果ではなく、ユーザー状態と神社意味の接続になっているかを確認するための監査資料である。",
        "",
        "---",
        "",
        "## 実行条件",
        "",
        f"- candidates_count: `{len(candidates)}`",
        "- source: `build_chat_recommendations`",
        "- output: `docs/analytics/recommendation-output-snapshot.md`",
        "",
        "---",
        "",
    ]

    for case in cases:
        recs = build_chat_recommendations(
            query=case.query,
            language="ja",
            candidates=candidates,
            bias=None,
            birthdate=case.birthdate,
            goriyaku_tag_ids=None,
            extra_condition=case.extra_condition,
            public_mode=case.public_mode,
            flow=case.flow,
            user=None,
        )
        lines.extend(_format_case(case, recs))
        lines.extend(["---", ""])

    lines.extend(
        [
            "## TODO",
            "",
            "```markdown",
            "- [x] representative case を8件定義",
            "- [x] build_chat_recommendations を service 直叩きで実行",
            "- [x] recommendations_v2 相当の top3 recommendations を保存",
            "- [x] score_v2 を保存",
            "- [x] rank_explanation を保存",
            "- [x] rank_comparison を保存",
            "- [x] _explanation_payload を保存",
            "- [x] docs/analytics/recommendation-output-snapshot.md 作成",
            "- [ ] 実出力を見て検索結果化していないか判定",
            "- [ ] 代表ケースごとの差分を次PRで改善候補へ分解",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Export Recommendation Score v2 representative output snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=300,
            help="Maximum number of Shrine rows used as recommendation candidates.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=str(OUTPUT_PATH),
            help="Markdown output path.",
        )

    def handle(self, *args, **options):
        limit = int(options["limit"])
        output_path = Path(str(options["output"]))

        candidates = _load_candidates(limit=limit)
        if not candidates:
            self.stderr.write(self.style.ERROR("No Shrine candidates found."))
            return

        markdown = _build_markdown(
            cases=REPRESENTATIVE_CASES,
            candidates=candidates,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported recommendation output snapshot: {output_path} cases={len(REPRESENTATIVE_CASES)} candidates={len(candidates)}"
            )
        )
