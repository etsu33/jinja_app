# backend/temples/domain/goriyaku_taxonomy_v1.py
"""Evidence Foundation PR-F3 / PR-F3b: Goriyaku v1 canonical taxonomy registry.

PR-F1（`evidence_taxonomy.py`）は namespace（"history_theme" / "goriyaku"）と
canonical key format (`<namespace>:<key>`) のみを定義し、実際に有効な
key一覧はF2/F3のHOLD事項として意図的に未定義のままだった。PR-F2は
history_theme側のみを解決し、PR-F3はgoriyaku側の**構造**のみを追加して
registryを意図的に空のまま（fail-closed）にしていた。

PR-F3bは、そのDATA_REVIEWを完了させ、Production canonical master 39件の
canonical identityをMother Ship FINALとして登録する。registryはclosed
vocabularyであり、未登録のcanonical keyは常にrejectされる（fail-closedの
性質は維持され、「registryにある39件だけが有効」という形に変わっただけ）。

registryの正本はこのcode-level versioned registryであり、DBではない。
canonical keyはimmutable identityとして扱い、日本語ラベルは display value
に過ぎない（`GoriyakuTag.id`をidentityとして使わないのは、そのPKが
backfill順に依存する不安定な値であるため）。

境界（PR-F3bで変更していないこと）:
    - semantic merge / alias / synonym inference を一切行わない。
      表記が近い概念（`八方除` と `八方除け`、`芸能` と `芸能運` 等）は
      別々のcanonical identityとして保持する（39 concept → 39 identity）。
    - local dev DBにのみ存在するlegacy 7件（`子宝・安産` / `金運・商売繁盛`
      / `仕事運・出世` / `厄除け・方除け` / `勝運・必勝祈願` / `地域安泰` /
      `開運招福`）はProduction masterに存在しないため、registry対象外。
    - 既存の`GoriyakuTag` / `Shrine.goriyaku_tags` / `Shrine.goriyaku` /
      `NEED_TO_GORIYAKU_IDS`、Recommendation / Ranking / Concierge /
      Compassのいずれも変更していない。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from temples.domain.evidence_taxonomy import (
    TaxonomyNamespace,
    get_current_taxonomy_version,
    validate_canonical_semantic_key,
)

GORIYAKU_TAXONOMY_NAMESPACE: TaxonomyNamespace = "goriyaku"

# PR-F1のtaxonomy version infrastructureをそのまま参照する
# （バージョン番号をここで再定義しない）。
GORIYAKU_TAXONOMY_VERSION = get_current_taxonomy_version(GORIYAKU_TAXONOMY_NAMESPACE).version

# Mother Ship FINAL（PR-F3b）: canonical key（ローカル部分、namespace
# prefixなし）→ 日本語表示ラベル。Production canonical master 39件に
# 1:1で対応する closed vocabulary であり、ここに無いkeyは常にreject
# される。順序はProduction masterのID順（1〜39）で、追跡可能性のため
# だけに保っている（順序自体はidentityではない）。
GORIYAKU_V1_CANONICAL_KEYS: Dict[str, str] = {
    "enmusubi": "縁結び",
    "yakuyoke": "厄除け",
    "kotsu_anzen": "交通安全",
    "shobai_hanjo": "商売繁盛",
    "gokoku_hojo": "五穀豊穣",
    "kaiun": "開運",
    "kanai_anzen": "家内安全",
    "fukutoku": "福徳",
    "gakugyo_joju": "学業成就",
    "gokaku_kigan": "合格祈願",
    "shoun": "勝運",
    "shigoto_un": "仕事運",
    "kokai_anzen": "航海安全",
    "kaijo_anzen": "海上安全",
    "bun_chokyu": "武運長久",
    "anzan": "安産",
    # `happo_jo`（八方除）と`happo_yoke`（八方除け）は別concept として
    # 保持する。統合はMother Ship FINALで明示的に禁止されている。
    "happo_jo": "八方除",
    "fufu_enman": "夫婦円満",
    "hachinan_jo": "八難除",
    "renai_joju": "恋愛成就",
    "michibiki": "導き",
    "biyo": "美容",
    "katayoke": "方除け",
    "kenko_choju": "健康長寿",
    "geino": "芸能",
    "katei_enman": "家庭円満",
    "shusse_un": "出世運",
    "kinun": "金運",
    "geino_un": "芸能運",
    "kyoun_yakuyoke": "強運厄除け",
    "gigei_jotatsu": "技芸上達",
    "happo_yoke": "八方除け",
    "byoki_heiyu": "病気平癒",
    "hibuse": "火防",
    "kodakara": "子宝",
    "shingan_joju": "心願成就",
    "enmei_choju": "延命長寿",
    "ashikoshi_kenko": "足腰健康",
    "nogyo_shugo": "農業守護",
}

GORIYAKU_V1_CANONICAL_KEY_SET = set(GORIYAKU_V1_CANONICAL_KEYS)


@dataclass(frozen=True)
class GoriyakuV1KeyValidationResult:
    valid: bool
    reason: str
    canonical_key: Optional[str]
    display_label_ja: Optional[str]


def validate_goriyaku_v1_canonical_key(value: Optional[str]) -> GoriyakuV1KeyValidationResult:
    """`<namespace>:<key>`形式の入力を検証し、goriyaku v1の承認済みkeyの
    いずれかであることまで確認する。

    - PR-F1のformat validatorをそのまま利用（namespace/separator/非空key
      のformat検証を重複実装しない）。
    - namespaceが"goriyaku"以外（例: "history_theme:restart"）の場合は
      reject。
    - keyがv1の39件に含まれない場合はreject（reason=
      "unknown_goriyaku_key"）。closed vocabularyであり、fuzzy
      normalization・日本語ラベルからの自動推定・alias解決は一切行わない。
      formatが正しいことはregistry登録の代替にならない。
    """
    format_result = validate_canonical_semantic_key(value)

    if not format_result.valid:
        return GoriyakuV1KeyValidationResult(
            valid=False,
            reason=format_result.reason,
            canonical_key=None,
            display_label_ja=None,
        )

    if format_result.namespace != GORIYAKU_TAXONOMY_NAMESPACE:
        return GoriyakuV1KeyValidationResult(
            valid=False,
            reason="wrong_namespace",
            canonical_key=None,
            display_label_ja=None,
        )

    key = format_result.key
    if key not in GORIYAKU_V1_CANONICAL_KEY_SET:
        return GoriyakuV1KeyValidationResult(
            valid=False,
            reason="unknown_goriyaku_key",
            canonical_key=None,
            display_label_ja=None,
        )

    return GoriyakuV1KeyValidationResult(
        valid=True,
        reason="valid",
        canonical_key=f"{GORIYAKU_TAXONOMY_NAMESPACE}:{key}",
        display_label_ja=GORIYAKU_V1_CANONICAL_KEYS[key],
    )


__all__ = [
    "GORIYAKU_TAXONOMY_NAMESPACE",
    "GORIYAKU_TAXONOMY_VERSION",
    "GORIYAKU_V1_CANONICAL_KEYS",
    "GORIYAKU_V1_CANONICAL_KEY_SET",
    "GoriyakuV1KeyValidationResult",
    "validate_goriyaku_v1_canonical_key",
]
