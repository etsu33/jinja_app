"""英語の神社詳細に出す特徴語（読み取り専用）。

GET /api/shrines/{id}/feature-words-en/

- 神社ごとの英語の特徴語（ShrineFeatureWordEn）を、英語の詳細ページの枠に分けて返す。
  - Story → history_culture（歴史・文化）
  - Sight・Craft・Feel → scenery_experience（景観・季節・体験）
- 季節の語（S_FLOWERS・S_AUTUMN）は返さない。見頃の時期のデータがまだ無いため
  （travel_ranking.SEASONAL_WORD_IDS と同じ扱い）。
- 公式サイトの引用（evidence_quote）は返さない。出典は source_url と checked_on で示す。
- 特徴語を持たない神社は、空の一覧を返す（エラーにしない）。神社が無いときは 404。
- ログインなしで読める。
"""

from __future__ import annotations

from typing import Any, Dict, List

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from temples.domain.feature_words_en import FEATURE_WORDS
from temples.models import Shrine
from temples.models_feature_words_en import ShrineFeatureWordEn
from temples.services.travel_ranking import SEASONAL_WORD_IDS

SLOT_HISTORY_CULTURE = "history_culture"
SLOT_SCENERY_EXPERIENCE = "scenery_experience"
# 特徴語の分類 → 英語の詳細ページの枠（2026-11-14 承認）。
SLOT_BY_CATEGORY: Dict[str, str] = {
    "Story": SLOT_HISTORY_CULTURE,
    "Sight": SLOT_SCENERY_EXPERIENCE,
    "Craft": SLOT_SCENERY_EXPERIENCE,
    "Feel": SLOT_SCENERY_EXPERIENCE,
}

_WORD_BY_ID = {word.id: word for word in FEATURE_WORDS}
_WORD_ORDER = {word.id: index for index, word in enumerate(FEATURE_WORDS)}


def build_feature_words_en_payload(shrine_id: int) -> Dict[str, Any]:
    """神社の英語の特徴語を、枠つきの一覧にする（語彙の並び順）。"""
    rows = (
        ShrineFeatureWordEn.objects.filter(shrine_id=shrine_id)
        .exclude(word_id__in=SEASONAL_WORD_IDS)
        .only("word_id", "source_url", "checked_on")
    )
    items: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(rows, key=lambda r: (_WORD_ORDER.get(r.word_id, len(_WORD_ORDER)), r.word_id)):
        word = _WORD_BY_ID.get(row.word_id)
        slot = SLOT_BY_CATEGORY.get(word.category) if word else None
        if word is None or slot is None or row.word_id in seen:
            continue  # 語彙に無い語・分類の分からない語は出さない
        seen.add(row.word_id)
        items.append(
            {
                "word_id": word.id,
                "label_en": word.label_en,
                "category": word.category,
                "slot": slot,
                "source_url": row.source_url,
                "checked_on": row.checked_on.isoformat() if row.checked_on else None,
            }
        )
    return {"shrine_id": shrine_id, "items": items}


class ShrineFeatureWordsEnView(APIView):
    """英語の神社詳細に出す特徴語（出典つき）。"""

    permission_classes = [AllowAny]
    throttle_scope = "shrines"

    @extend_schema(
        summary="English feature words for the shrine detail",
        tags=["shrines"],
        responses={
            200: inline_serializer(
                name="ShrineFeatureWordsEnResponse",
                fields={
                    "shrine_id": serializers.IntegerField(),
                    "items": inline_serializer(
                        name="ShrineFeatureWordEnItem",
                        many=True,
                        fields={
                            "word_id": serializers.CharField(),
                            "label_en": serializers.CharField(),
                            "category": serializers.ChoiceField(choices=list(SLOT_BY_CATEGORY)),
                            "slot": serializers.ChoiceField(
                                choices=[SLOT_HISTORY_CULTURE, SLOT_SCENERY_EXPERIENCE]
                            ),
                            "source_url": serializers.URLField(),
                            "checked_on": serializers.DateField(allow_null=True),
                        },
                    ),
                },
            )
        },
    )
    def get(self, request, pk: int, *args, **kwargs):
        if not Shrine.objects.filter(pk=pk).exists():
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(build_feature_words_en_payload(pk), status=status.HTTP_200_OK)
