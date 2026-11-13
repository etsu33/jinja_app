"""travel モード（英語の相談）の並べ替えと、英語の推薦理由。

指示書 v1.1（ルール v1.1 に整合）5章の3層を、次のように実装する（2026-11-13 えつこさん決定）。

① 出すかどうか（合否）
    特徴語を持たない神社も外さない。点数0として、特徴語を持つ神社の後ろに
    既存の推薦（need）の順番のまま並べる。
② 相談への合い方（重み 0.59）
    相談文から拾えた語のうち、神社が持っていた語の割合。F_QUIET もほかの語と同じに扱う。
    季節の語（S_FLOWERS / S_AUTUMN）は、見頃の時期のデータが無いので数えない。
③ 場所の価値（重み 0.41）
    神社が持つ特徴語のうち、Craft と Story の語の種類の数。
    PLACE_VALUE_CAP 種類で 1.0（2026-11-13 時点の最大は伏見稲荷大社の10種類）。

配点（0.59 / 0.41）と上限は仮説で、記録を見て調整する。
既存の need の点数は変えない。並べ替えは need で並んだ候補の中だけで行う。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from temples.domain.feature_words_en import FEATURE_WORDS
from temples.models import ShrineFeatureWordEn

TRAVEL_MATCH_WEIGHT = 0.59
TRAVEL_PLACE_WEIGHT = 0.41
PLACE_VALUE_CAP = 10
PLACE_VALUE_CATEGORIES = frozenset({"Craft", "Story"})
# 見頃の時期のデータが無いので、重なりに数えない（指示書 5章「季節は訪問時期が見頃のときだけ一致」）
SEASONAL_WORD_IDS = frozenset({"S_FLOWERS", "S_AUTUMN"})
KNOWN_FOR_LIMIT = 3

_WORD_ORDER = {word.id: index for index, word in enumerate(FEATURE_WORDS)}
_WORD_LABEL = {word.id: word.label_en for word in FEATURE_WORDS}
_WORD_CATEGORY = {word.id: word.category for word in FEATURE_WORDS}


def _shrine_id_of(recommendation: Dict[str, Any]) -> int | None:
    raw = recommendation.get("shrine_id")
    if raw is None:
        raw = recommendation.get("id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def load_shrine_feature_ids(shrine_ids: Iterable[int]) -> Dict[int, List[str]]:
    """神社IDごとの語ID（重複なし・語彙の並び順）。問い合わせは1回だけ。"""
    ids = [sid for sid in shrine_ids if sid is not None]
    if not ids:
        return {}
    by_shrine: Dict[int, set] = {}
    for shrine_id, word_id in ShrineFeatureWordEn.objects.filter(shrine_id__in=ids).values_list(
        "shrine_id", "word_id"
    ):
        by_shrine.setdefault(shrine_id, set()).add(word_id)
    return {
        shrine_id: sorted(words, key=lambda w: _WORD_ORDER.get(w, len(_WORD_ORDER)))
        for shrine_id, words in by_shrine.items()
    }


def match_score(request_ids: Sequence[str], shrine_ids: Sequence[str]) -> tuple[float, List[str]]:
    """② 相談への合い方：相談の語（季節の語を除く）のうち、神社が持っていた語の割合。"""
    wanted = [w for w in dict.fromkeys(request_ids or []) if w not in SEASONAL_WORD_IDS]
    if not wanted:
        return 0.0, []
    have = set(shrine_ids or [])
    overlap = [w for w in wanted if w in have]
    return len(overlap) / len(wanted), overlap


def place_value(shrine_ids: Sequence[str]) -> tuple[float, int]:
    """③ 場所の価値：Craft と Story の語の種類の数（PLACE_VALUE_CAP で 1.0）。"""
    count = len({w for w in shrine_ids or [] if _WORD_CATEGORY.get(w) in PLACE_VALUE_CATEGORIES})
    return min(count, PLACE_VALUE_CAP) / PLACE_VALUE_CAP, count


def build_reason_en(overlap_ids: Sequence[str], shrine_ids: Sequence[str]) -> Dict[str, Any] | None:
    """英語の推薦理由。一致があれば一致した語、なければ神社が持つ語を3つまで。"""
    if overlap_ids:
        labels = [_WORD_LABEL[w] for w in overlap_ids if w in _WORD_LABEL]
        return {"type": "matches", "ids": list(overlap_ids), "labels": labels,
                "text": "Matches your interests: " + ", ".join(labels)}
    if shrine_ids:
        picked = [w for w in shrine_ids if w in _WORD_LABEL][:KNOWN_FOR_LIMIT]
        labels = [_WORD_LABEL[w] for w in picked]
        return {"type": "known_for", "ids": picked, "labels": labels,
                "text": "Known for: " + ", ".join(labels)}
    return None


def rerank_for_travel(
    recommendations: Iterable[Any],
    request_feature_ids: Sequence[str],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """need で並んだ候補を travel の点数で並べ替える。

    特徴語を持つ神社を点数の高い順（同点は元の順）に、その後ろに持たない神社を元の順で並べる。
    各候補に travel_reason_en と travel_score を付ける。
    戻り値の2つ目は記録用（ConciergeRecommendationLog.result_state に残す）。
    """
    items = [r for r in (recommendations or []) if isinstance(r, dict)]
    features = load_shrine_feature_ids(_shrine_id_of(r) for r in items)

    scored: List[tuple] = []
    uncovered: List[Dict[str, Any]] = []
    for position, rec in enumerate(items):
        shrine_feature_ids = features.get(_shrine_id_of(rec)) or []
        if not shrine_feature_ids:
            rec["travel_score"] = None
            rec["travel_reason_en"] = None
            uncovered.append(rec)
            continue
        match, overlap = match_score(request_feature_ids, shrine_feature_ids)
        place, place_count = place_value(shrine_feature_ids)
        total = round(TRAVEL_MATCH_WEIGHT * match + TRAVEL_PLACE_WEIGHT * place, 6)
        rec["travel_score"] = {
            "total": total,
            "match": round(match, 6),
            "place": round(place, 6),
            "overlap_ids": overlap,
            "place_word_count": place_count,
        }
        rec["travel_reason_en"] = build_reason_en(overlap, shrine_feature_ids)
        scored.append((-total, position, rec))

    scored.sort(key=lambda row: (row[0], row[1]))
    ordered = [row[2] for row in scored] + uncovered
    observation = {
        "weights": {"match": TRAVEL_MATCH_WEIGHT, "place": TRAVEL_PLACE_WEIGHT},
        "place_value_cap": PLACE_VALUE_CAP,
        "request_ids": list(request_feature_ids or []),
        "seasonal_excluded": [w for w in request_feature_ids or [] if w in SEASONAL_WORD_IDS],
        "pool_size": len(items),
        "covered_in_pool": len(scored),
        "order": [
            {"shrine_id": _shrine_id_of(r), "score": (r.get("travel_score") or {}).get("total")}
            for r in ordered
        ],
    }
    return ordered, observation
