"""Compass Monthly API（POST /api/compass/recommendations/）のschema serializer。

docs/audit/compass-monthly-api-boundary.md Section 13-14（G5: PATH PRESENT /
CONTRACT MISSING）の remediation。

用途は **drf-spectacular によるOpenAPI生成のためのドキュメンテーションのみ**。
CompassRecommendationsView は従来どおり request.data を自前で読み、
Response(dict) を自前で組み立てる。ここで定義したserializerで runtime の
validation を掛け替えることはしない（Section 4 / 14: schema生成のために
runtime semantics を変えない）。

特に request 側:
  - purpose / birthdate / target_date はすべて optional string として表現する。
    実際の View は欠落を 400 にせず、purpose="" は invalid_purpose（400）、
    birthdate/target_date の欠落は direction 側の fail-safe state（200）へ
    落ちる。serializer を runtime validation に昇格させるとこの挙動が壊れる。
  - origin は「mapping のときだけ採用され、それ以外は None 扱い」という
    現行の runtime contract をそのまま表現する（型不正を 400 にはしない）。

response 側は Compass Monthly Public Contract v1（Section 9）そのもので、
recommendation item は temples.api.compass_public_projection が投影した
allowlist の shape だけを記述する。
"""

from __future__ import annotations

from rest_framework import serializers
from temples.services.compass_recommendation_orchestrator import (
    STATE_DIRECTION_FILTER_UNAVAILABLE,
    STATE_DIRECTION_ZERO_CANDIDATES,
    STATE_EVIDENCE_ZERO_CANDIDATES,
    STATE_INVALID_PURPOSE,
    STATE_NO_COMMON_DIRECTION,
    STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
    STATE_RECOMMENDATION_SUCCESS,
)

# orchestrator が返し得る state（Section 5）。ここで新しい state を発明しない。
COMPASS_MONTHLY_RESULT_STATES = (
    STATE_INVALID_PURPOSE,
    STATE_DIRECTION_FILTER_UNAVAILABLE,
    STATE_NO_COMMON_DIRECTION,
    STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
    STATE_DIRECTION_ZERO_CANDIDATES,
    STATE_EVIDENCE_ZERO_CANDIDATES,
    STATE_RECOMMENDATION_SUCCESS,
)


class CompassRecommendationsRequestSerializer(serializers.Serializer):
    """POST /api/compass/recommendations/ のrequest body（ドキュメント用）。

    現行 View の正規化挙動をそのまま表現する:
      purpose      -> str 化 + strip、欠落時は ""（その結果 invalid_purpose）
      birthdate    -> str 化 + strip、空なら None
      target_date  -> str 化 + strip、空なら None
      origin       -> dict のときのみ採用、それ以外は None
    """

    purpose = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="need tag（例: career）。未指定・空・未知の値は state=invalid_purpose（400）。",
    )
    birthdate = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="YYYY-MM-DD。欠落時は direction_filter_unavailable（200）。",
    )
    target_date = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="YYYY-MM-DD。欠落時はBackendの既定日が使われる。",
    )
    origin = serializers.DictField(
        required=False,
        allow_null=True,
        help_text=(
            "{lat, lng} の出発地点。mapping 以外の値は 400 にはならず、"
            "origin 未指定と同じ direction_filter_unavailable（200）へ落ちる。"
        ),
    )


class CompassDirectionContextSerializer(serializers.Serializer):
    """direction_context（Section 6）。Runtime data であり Recommendation evidence ではない。"""

    targetDate = serializers.CharField()
    targetYear = serializers.IntegerField()
    solarMonthIndex = serializers.IntegerField()
    referenceDirections = serializers.ListField(child=serializers.CharField())
    calculationMethod = serializers.ChoiceField(
        choices=["annual_monthly_kyusei_v1", "monthly_kyusei_v1"]
    )
    note = serializers.CharField()


class CompassRecommendationBreakdownSerializer(serializers.Serializer):
    """breakdown の公開部分（Section 9.3）。matched_need_tags 以外は公開しない。"""

    matched_need_tags = serializers.ListField(child=serializers.CharField(), required=False)


class CompassReasonFactSerializer(serializers.Serializer):
    """reason_facts[] の公開部分（Section 9.4）。type / label 以外は公開しない。"""

    type = serializers.CharField(required=False)
    label = serializers.CharField(required=False)


class CompassRecommendationItemSerializer(serializers.Serializer):
    """recommendations[] 1件 = Compass Monthly Public Contract v1 の allowlist（Section 9.2）。

    allowlist であって「全件が全fieldを持つ」という意味ではないため、
    recommendation_instance_id 以外は required=False。
    """

    shrine_id = serializers.IntegerField(required=False, allow_null=True)
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    distance_m = serializers.FloatField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_null=True)
    recommendation_instance_id = serializers.CharField(
        help_text=(
            "top-level recommendation_instance_id と必ず同一値の互換alias。"
            "canonical は top-level 側（Section 8）。"
        ),
    )
    breakdown = CompassRecommendationBreakdownSerializer(required=False)
    reason_facts = CompassReasonFactSerializer(many=True, required=False)


class CompassRecommendationsResponseSerializer(serializers.Serializer):
    """Monthly の structured response（Section 9.1）。200 と 400 で同一shape。"""

    state = serializers.ChoiceField(choices=list(COMPASS_MONTHLY_RESULT_STATES))
    purpose = serializers.CharField(allow_null=True)
    direction_context = CompassDirectionContextSerializer(allow_null=True)
    recommendation_instance_id = serializers.CharField()
    recommendations = CompassRecommendationItemSerializer(many=True)
    distance_stage_km = serializers.IntegerField(
        allow_null=True,
        help_text="15 / 30 / 60。distance stage へ到達しない state では null。",
    )
    direction_candidate_count = serializers.IntegerField(allow_null=True)
    distance_candidate_count = serializers.IntegerField(allow_null=True)


class CompassRecommendationsInvalidPurposeResponseSerializer(
    CompassRecommendationsResponseSerializer
):
    """400 応答。shape は 200 と同じで、state は invalid_purpose に固定される。"""

    state = serializers.ChoiceField(choices=[STATE_INVALID_PURPOSE])


class CompassErrorResponseSerializer(serializers.Serializer):
    """500 応答。View は {"state": "error"} のみを返す（内部情報を載せない）。"""

    state = serializers.ChoiceField(choices=["error"])


__all__ = [
    "COMPASS_MONTHLY_RESULT_STATES",
    "CompassRecommendationsRequestSerializer",
    "CompassDirectionContextSerializer",
    "CompassRecommendationBreakdownSerializer",
    "CompassReasonFactSerializer",
    "CompassRecommendationItemSerializer",
    "CompassRecommendationsResponseSerializer",
    "CompassRecommendationsInvalidPurposeResponseSerializer",
    "CompassErrorResponseSerializer",
]
