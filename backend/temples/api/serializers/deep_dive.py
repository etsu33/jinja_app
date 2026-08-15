"""Deep Dive Ask API(PR-B5)のrequest/response serializer。

docs/product/deep-dive-answer-generation-contract.md §11 API Responsibility。
readiness判定・question classification・Fact取得・Evidence filtering・LLM
payload構築・provenance決定はすべてBackend Authority
(temples.services.deep_dive_answer.generate_deep_dive_answer())が行う。
ここでは入力のvalidationと、既に確定した出力のstable public shapeへの
変換のみを行う(Thin Boundary)。

Clientからreadiness/facts/sources/confidence/verification_statusを受け取らない
(これらはBackend Authorityであり、Clientが指定できるパラメータではない)。
"""

from __future__ import annotations

from rest_framework import serializers


class DeepDiveAskRequestSerializer(serializers.Serializer):
    """POST /api/deep-dive/ask/ のrequest body。shrine_id + questionのみを受け取る。"""

    shrine_id = serializers.IntegerField(min_value=1)
    # 空文字は許容する(classify_question()が"other"へ分類し、通常のunanswered
    # 応答として処理される。分類できない入力を400にはしない、§12)。
    question = serializers.CharField(
        required=True, allow_blank=True, trim_whitespace=False, max_length=2000
    )


class DeepDiveFactUsedSerializer(serializers.Serializer):
    """facts_used 1件。docs §9 Provenance Contract通り、mechanicalに導出済みの値のみ。"""

    type = serializers.CharField()
    id = serializers.IntegerField()
    label = serializers.CharField()


class DeepDiveSourceUsedSerializer(serializers.Serializer):
    """sources_used 1件。stable public shapeのみ(内部note/管理用fieldは含まない)。"""

    id = serializers.IntegerField()
    title = serializers.CharField()
    publisher = serializers.CharField()
    source_type = serializers.CharField()
    url = serializers.CharField()


class DeepDiveAskResponseSerializer(serializers.Serializer):
    """docs §10 Output Contract + question_type(§3の分類結果、そのままpass through)。

    ドキュメンテーション用途(drf-spectacular schema)。Viewは
    generate_deep_dive_answer()の戻り値からdictを直接組み立ててResponse()へ渡し、
    このserializerでの再シリアライズは行わない(値の再解釈をしないため)。
    """

    answer = serializers.CharField()
    readiness = serializers.ChoiceField(choices=["full", "limited", "not_ready"])
    question_type = serializers.ListField(child=serializers.CharField())
    facts_used = DeepDiveFactUsedSerializer(many=True)
    sources_used = DeepDiveSourceUsedSerializer(many=True)
    limitations = serializers.CharField(allow_null=True)
    unanswered_aspects = serializers.ListField(child=serializers.CharField())


__all__ = [
    "DeepDiveAskRequestSerializer",
    "DeepDiveFactUsedSerializer",
    "DeepDiveSourceUsedSerializer",
    "DeepDiveAskResponseSerializer",
]
