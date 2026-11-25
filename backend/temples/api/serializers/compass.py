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
    """reason_facts[] の公開部分（Section 9.4）。

    Recommendation Meaning（なぜ今回この神社が候補なのか）。
    type / label / label_ja / is_primary 以外（evidence / score 等）は公開しない。
    """

    type = serializers.CharField(required=False)
    label = serializers.CharField(required=False)
    label_ja = serializers.CharField(required=False)
    is_primary = serializers.BooleanField(required=False)


class CompassShrineFactDeitySerializer(serializers.Serializer):
    """shrine_facts.deity。Evidence Gate 通過済みの祭神Fact 1件。"""

    display_name = serializers.CharField()


class CompassShrineFactHistorySerializer(serializers.Serializer):
    """shrine_facts.history。Evidence Gate 通過済みの由緒Fact 1件。"""

    history_type = serializers.CharField()
    content = serializers.CharField()


class CompassShrineFactsSerializer(serializers.Serializer):
    """shrine_facts。ユーザーの相談とは独立した、その神社そのものの確認済みFact。

    Recommendation Meaning（reason_facts）ではない。deity / history は
    それぞれ最大1件で、存在しない側は省略される。
    """

    deity = CompassShrineFactDeitySerializer(required=False)
    history = CompassShrineFactHistorySerializer(required=False)


class CompassRecommendationItemSerializer(serializers.Serializer):
    """recommendations[] 1件 = Compass Monthly Public Contract v1 の allowlist（Section 9.2）。

    allowlist であって「全件が全fieldを持つ」という意味ではないため、
    原則として required=False。

    例外は identity と transport metadata:

    - `shrine_id` は **必須かつ non-null**
      （R-2 / R-4。docs/audit/compass-shrine-id-presence-audit.md §10 / §12）
      public response に recommendation item が存在するなら、その item は
      必ず Shrine identity を持つ。runtime 側の強制は R-3（§11）が
      Public Projection の identity gate として実装済みで、違反時は
      HTTP 500 / {"state": "error"} へ fail-closed する。
      本 serializer は OpenAPI 記述専用であり、runtime validation は行わない。

    - `recommendation_instance_id` は View が注入する互換 alias（Section 8）。
    """

    # SHRINE_IDENTITY_AUTHORITY = Shrine.id / PUBLIC_IDENTITY_KEY = shrine_id。
    # required / allow_null は DRF の既定値に依存させず、契約としてコード上に
    # 明示する（R-4）。
    shrine_id = serializers.IntegerField(
        required=True,
        allow_null=False,
        help_text=(
            "当該 Shrine の永続化 primary key。recommendation item が存在する限り"
            "必須かつ non-null（R-2 / R-3 / R-4）。Shrine identity の authority は"
            "この field であり、`id` ではない。"
        ),
    )
    # `id` は COMPATIBILITY_FIELD。identity authority ではないため optional のまま
    # 維持する（R-2 / #2952）。必須化も削除も R-4 の対象外。
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
    shrine_facts = CompassShrineFactsSerializer(
        required=False,
        help_text=(
            "その神社そのものの確認済みFact（祭神・由緒 各最大1件）。"
            "推薦理由（reason_facts）ではない。Factが無い場合はkeyごと省略される。"
        ),
    )


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
    "CompassShrineFactDeitySerializer",
    "CompassShrineFactHistorySerializer",
    "CompassShrineFactsSerializer",
    "CompassRecommendationItemSerializer",
    "CompassRecommendationsResponseSerializer",
    "CompassRecommendationsInvalidPurposeResponseSerializer",
    "CompassErrorResponseSerializer",
]
