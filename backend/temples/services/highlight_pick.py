"""推薦した神社ごとに「ここで見る」見どころを1つ選ぶ（見どころ単位の推薦 段階A）。

設計: プロジェクト文書 claude/highlight-level-recommendation-plan.md

- 順位は変えない。並んだ推薦の各神社に `highlight_pick` を足すだけ
- 推薦理由（reason_facts）には入れない。順位に寄与していない情報を推薦理由として見せないため
  （docs/product/recommendation-signal-authority.md の Faithful Explanation）。
  Shrine Profile の「④ Action Layer（参拝で何をするか）」として扱う
- 出すのは、相談の種類（need_tag）に合う承認済みのアンサーを持ち、見どころ自体も公開判定を
  通っているものだけ（highlight_publication.decide_answer_publication）。合うものが無ければ None
- 複数あるときは、相談の種類の優先順（NEED_PRIORITY）→ 見どころの sort_order → id の順で1つ
- 表示のときにAIは呼ばない
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from temples.domain.need_tags import NEED_PRIORITY
from temples.services import evidence_gate, highlight_publication

_NEED_RANK = {tag: index for index, tag in enumerate(NEED_PRIORITY)}


def _shrine_id_of(recommendation: Dict[str, Any]) -> Optional[int]:
    for key in ("shrine_id", "shrineId"):
        raw = recommendation.get(key)
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                return None
    return None


def ordered_need_tags(need_tags: Iterable[str]) -> List[str]:
    """相談の種類を優先順に並べる（知らない語は捨てる）。"""
    wanted = {str(tag) for tag in (need_tags or []) if isinstance(tag, str)}
    return [tag for tag in NEED_PRIORITY if tag in wanted]


def _load_answers(shrine_ids: List[int], need_tags: List[str], language_code: str):
    from temples.models import ShrineHighlight, ShrineHighlightAnswer

    return list(
        ShrineHighlightAnswer.objects.filter(
            highlight__shrine_id__in=shrine_ids,
            need_tag__in=need_tags,
            language_code=language_code,
            review_status=ShrineHighlightAnswer.ReviewStatus.APPROVED,
            highlight__publication_status=ShrineHighlight.PublicationStatus.PUBLISHED,
            highlight__verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES,
        )
        .select_related("highlight")
        .prefetch_related("highlight__translations", "highlight__source_links__source")
    )


def build_highlight_pick(answer, language_code: str) -> Dict[str, Any]:
    translation = highlight_publication.find_translation(
        answer.highlight.translations.all(), language_code
    )
    return {
        "highlight_id": answer.highlight_id,
        "shrine_id": answer.highlight.shrine_id,
        "name": (translation.name if translation else "").strip(),
        "need_tag": answer.need_tag,
        "answer_text": answer.answer_text.strip(),
    }


def attach_highlight_picks(
    recommendations: Iterable[Any],
    need_tags: Iterable[str],
    language_code: str = "ja",
) -> Dict[str, Any]:
    """各推薦に `highlight_pick`（dict か None）を付ける。戻り値は記録用。

    問い合わせはアンサーの取得1回と、その先読みだけ（推薦の件数に比例しない）。
    """
    items = [r for r in (recommendations or []) if isinstance(r, dict)]
    needs = ordered_need_tags(need_tags)
    shrine_ids = [sid for sid in (_shrine_id_of(r) for r in items) if sid is not None]

    by_shrine: Dict[int, list] = {}
    if needs and shrine_ids:
        for answer in _load_answers(shrine_ids, needs, language_code):
            if not highlight_publication.decide_answer_publication(
                answer, language_code
            ).displayable:
                continue
            by_shrine.setdefault(answer.highlight.shrine_id, []).append(answer)

    shown: List[Dict[str, Any]] = []
    for rec in items:
        candidates = by_shrine.get(_shrine_id_of(rec)) or []
        if not candidates:
            rec["highlight_pick"] = None
            continue
        best = min(
            candidates,
            key=lambda a: (
                _NEED_RANK.get(a.need_tag, len(_NEED_RANK)),
                a.highlight.sort_order,
                a.highlight_id,
            ),
        )
        rec["highlight_pick"] = build_highlight_pick(best, language_code)
        shown.append(
            {
                "shrine_id": best.highlight.shrine_id,
                "highlight_id": best.highlight_id,
                "need_tag": best.need_tag,
            }
        )

    return {
        "language": language_code,
        "need_tags": needs,
        "recommendation_count": len(items),
        "shown_count": len(shown),
        "shown": shown,
    }
