"""Deep Dive Deterministic Answer Builder Foundation (PR-ND1)。

docs/audit/deep-dive-non-llm-runtime-alignment.md §5 Non-LLM Answer
Contractの実装。Evidence-gated済みの`DeepDiveFact`（temples.services.
deep_dive_retrieval）から、LLMを一切使わずにユーザー向け回答文字列を
構築するpure functionを提供する。

**本モジュールはFoundationのみである。** 既存の
`temples.services.deep_dive_answer.generate_deep_dive_answer()`の
production behaviorには接続しない（呼び出し元を持たない、PR-ND2の
スコープ）。API・Frontend・DB schemaのいずれにも影響しない。

Absolute Safety Rules（docs/audit/deep-dive-non-llm-runtime-alignment.md
§5・§6 No-Hallucination Contractをそのまま継承）:
  - Factに無い固有情報を追加しない -- `build_deterministic_answer()`は
    `DeepDiveFact.label`/`.content`の引用・連結のみで構成し、新しい
    文を生成しない。
  - 一般知識で補完しない -- テンプレート自体が固定文言のみを追加する
    （Fact本文を書き換えない）。
  - deity/history間の意味推論をしない -- `deity_nature`はdeity_who相当
    まで安全に縮退する（§5.3、本モジュール内コメント参照）。History
    からdeityの性質を推論する経路はコード上存在しない。
  - Sourceをanswer textから生成しない -- 本モジュールはSource/
    provenanceを一切扱わない（既存のfacts_used/sources_used機械導出
    ロジック、deep_dive_answer.pyの責務のまま）。
  - zero usable factsでは回答を捏造しない -- 該当factが無い場合は
    `None`を返す（空文字列や説明文を生成しない）。
  - suppressed factを使用しない -- `reason_strength == "suppressed"`
    のFactは入力から除外してから組み立てる。
  - LLMを呼ばない -- 本モジュールはtemples.llm以下のいかなるモジュール
    もimportしない。
"""

from __future__ import annotations

from typing import Iterable, Optional

from temples.services.deep_dive_retrieval import (
    QUESTION_TYPE_DEITY_NATURE,
    QUESTION_TYPE_DEITY_WHO,
    QUESTION_TYPE_FOUNDING,
    QUESTION_TYPE_HISTORICAL_EVENTS,
    QUESTION_TYPE_TRADITION,
    DeepDiveFact,
)

# ---------------------------------------------------------------------------
# reason_strength定数（deep_dive_retrieval.pyの値と同一。Recommendation
# Authority領域のファイルをimportせず値のみ複製する既存パターン
# (deep_dive_retrieval.py自身のdocstring参照)をここでも踏襲する）。
# ---------------------------------------------------------------------------

_SUPPRESSED = "suppressed"
_ASSERTIVE = "assertive"
_WEAKENED = "weakened"

_DEITY_FACT_TYPE = "deity"
_HISTORY_FACT_TYPE = "history"

# この対応表に無いquestion_type（source_basis/other等）はPR-ND1の対象外。
# build_deterministic_answer()は未対応のquestion_typeに対して常にNoneを返す
# （推測でどれかのtemplateへ寄せない）。
_HISTORY_QUESTION_TYPES = (
    QUESTION_TYPE_FOUNDING,
    QUESTION_TYPE_HISTORICAL_EVENTS,
    QUESTION_TYPE_TRADITION,
)


def _scoped_usable_facts(question_type: str, facts: Iterable[DeepDiveFact]) -> list[DeepDiveFact]:
    """指定question_typeに属し、かつsuppressedでないfactのみへ絞り込む。

    facts自体は呼び出し側がbuild_deep_dive_context()から取得した
    evidence-gated済みの集合を渡す想定だが、本関数はfact.question_typeの
    一致とreason_strength != suppressedの両方を自前で再確認する
    （呼び出し側の絞り込みに依存しない、defense in depth）。
    """
    return [
        fact
        for fact in facts
        if fact.question_type == question_type and fact.reason_strength != _SUPPRESSED
    ]


def _build_deity_segment(facts: list[DeepDiveFact]) -> Optional[str]:
    """deity Factからの回答segment（§5.2）。deity_who・deity_nature共通。

    同一reason_strengthのdeity Factは1文にまとめ、labelを「・」で連結する。
    assertiveとweakenedが混在する場合は2文に分け、1文で断定調と伝聞調を
    混ぜない。
    """
    deity_facts = [f for f in facts if f.type == _DEITY_FACT_TYPE]
    if not deity_facts:
        return None

    assertive_labels = [f.label for f in deity_facts if f.reason_strength == _ASSERTIVE]
    weakened_labels = [f.label for f in deity_facts if f.reason_strength == _WEAKENED]

    sentences: list[str] = []
    if assertive_labels:
        sentences.append(f"{'・'.join(assertive_labels)}をお祀りしています。")
    if weakened_labels:
        sentences.append(f"{'・'.join(weakened_labels)}をお祀りしていると伝わっています。")

    return "\n".join(sentences) if sentences else None


def _hedge_history_content(content: str) -> str:
    """weakenedなhistory Factへ伝聞表現を付与する。content自体は書き換えない。"""
    trimmed = content[:-1] if content.endswith("。") else content
    return f"{trimmed}と伝わっています。"


def _build_history_segment(facts: list[DeepDiveFact]) -> Optional[str]:
    """history Factからの回答segment（§5.2）。founding/historical_events/
    tradition共通。tradition種別のFactはretrieval層
    （_apply_tradition_hedge_floor）が既にreason_strength="weakened"へ
    floorしているため、本関数はhistory_typeを個別に判定しない
    （reason_strengthのみを見れば十分、値の二重管理をしない）。
    """
    history_facts = [f for f in facts if f.type == _HISTORY_FACT_TYPE]
    if not history_facts:
        return None

    sentences: list[str] = []
    for fact in history_facts:
        if fact.reason_strength == _ASSERTIVE:
            sentences.append(fact.content)
        else:
            sentences.append(_hedge_history_content(fact.content))

    return "\n".join(sentences) if sentences else None


def build_deterministic_answer(
    *, question_type: str, facts: Iterable[DeepDiveFact]
) -> Optional[str]:
    """1つのquestion_typeに対する回答segmentを、Factの引用・連結のみで構築する。

    docs/audit/deep-dive-non-llm-runtime-alignment.md §5 Non-LLM Answer
    Contractの実装。呼び出し側で複数question_type（複合質問）を扱う場合は、
    question_typeごとに本関数を呼び出しsegmentを連結する（本関数自体は
    1 question_type分のみを扱うpure function、Architecture要件どおり）。

    Returns:
        構築できた回答文字列。該当するusable factが1件も無い場合は
        `None`（空文字列や説明文を生成しない、捏造しない）。

    Safety:
        - suppressed（confidence="low"相当）なFactは`_scoped_usable_facts()`
          で除外済みのため、生成に使われない。
        - `question_type == QUESTION_TYPE_DEITY_NATURE`の場合、facts引数に
          history Factが含まれていても、`_build_deity_segment()`は
          `fact.type == "deity"`のみを見るため、history Factの内容が
          deityの性質説明として混入することはない（PR #2456 §5.3の
          安全な縮退。role fieldも現行DeepDiveFactに存在しないため使わない
          -- deity_whoと出力が一致する）。
    """
    scoped_facts = _scoped_usable_facts(question_type, facts)
    if not scoped_facts:
        return None

    if question_type in (QUESTION_TYPE_DEITY_WHO, QUESTION_TYPE_DEITY_NATURE):
        return _build_deity_segment(scoped_facts)

    if question_type in _HISTORY_QUESTION_TYPES:
        return _build_history_segment(scoped_facts)

    # source_basis/other/未知のquestion_typeはPR-ND1の対象外。推測で
    # deity/historyいずれかのtemplateへ寄せない。
    return None


__all__ = ["build_deterministic_answer"]
