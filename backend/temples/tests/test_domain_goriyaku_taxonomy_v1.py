# backend/temples/tests/test_domain_goriyaku_taxonomy_v1.py
"""Evidence Foundation PR-F3b: goriyaku v1 canonical registry tests.

PR-F3ではregistryが意図的に空（fail-closed）だったため、本ファイルは
「どのkeyも受理されない」ことを確認していた。PR-F3bでProduction
canonical master 39件が登録されたため、closed vocabularyとしての
振る舞い（39件は受理・それ以外は常にreject）を確認する内容へ更新した。
"""
from __future__ import annotations

import pytest

from temples.domain.goriyaku_taxonomy_v1 import (
    GORIYAKU_TAXONOMY_NAMESPACE,
    GORIYAKU_TAXONOMY_VERSION,
    GORIYAKU_V1_CANONICAL_KEY_SET,
    GORIYAKU_V1_CANONICAL_KEYS,
    validate_goriyaku_v1_canonical_key,
)

# Mother Ship FINAL（PR-F3b）: Production canonical master 39件。
# テスト側にも独立した期待値として持ち、実装辞書をそのまま読み返す
# だけの自己参照テストにしない。
EXPECTED_V1_REGISTRY = {
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

# local dev DBにのみ存在するlegacy label（Production masterに不在）。
# registryへ入っていないことを明示的に固定する。
LOCAL_ONLY_LEGACY_LABELS = [
    "子宝・安産",
    "金運・商売繁盛",
    "仕事運・出世",
    "厄除け・方除け",
    "勝運・必勝祈願",
    "地域安泰",
    "開運招福",
]


def test_namespace_is_goriyaku():
    assert GORIYAKU_TAXONOMY_NAMESPACE == "goriyaku"


def test_taxonomy_version_is_v1_string():
    assert GORIYAKU_TAXONOMY_VERSION == "v1"
    assert isinstance(GORIYAKU_TAXONOMY_VERSION, str)


def test_registry_contains_exactly_the_39_production_concepts():
    assert GORIYAKU_V1_CANONICAL_KEYS == EXPECTED_V1_REGISTRY
    assert len(GORIYAKU_V1_CANONICAL_KEYS) == 39


def test_canonical_keys_are_unique():
    # dictのkeyは定義上一意なので、実質的な検査対象は
    # 「39 concept → 39 identity」が崩れていないこと（display labelの
    # 重複＝2 conceptが同じ意味へ潰れている兆候、も同時に見る）。
    assert len(GORIYAKU_V1_CANONICAL_KEY_SET) == 39
    assert len(set(GORIYAKU_V1_CANONICAL_KEYS.values())) == 39


@pytest.mark.parametrize("key", sorted(EXPECTED_V1_REGISTRY))
def test_every_registered_key_validates(key):
    result = validate_goriyaku_v1_canonical_key(f"goriyaku:{key}")
    assert result.valid is True
    assert result.reason == "valid"
    assert result.canonical_key == f"goriyaku:{key}"
    assert result.display_label_ja == EXPECTED_V1_REGISTRY[key]


def test_form_variants_remain_separate_identities():
    # Mother Ship FINAL: 八方除 と 八方除け を統合しない。
    happo_jo = validate_goriyaku_v1_canonical_key("goriyaku:happo_jo")
    happo_yoke = validate_goriyaku_v1_canonical_key("goriyaku:happo_yoke")
    assert happo_jo.valid and happo_yoke.valid
    assert happo_jo.canonical_key != happo_yoke.canonical_key
    assert happo_jo.display_label_ja == "八方除"
    assert happo_yoke.display_label_ja == "八方除け"


def test_domain_neighbours_remain_separate_identities():
    # 芸能 / 芸能運、健康長寿 / 延命長寿 も同様に別identity。
    for a, b in (("geino", "geino_un"), ("kenko_choju", "enmei_choju")):
        ra = validate_goriyaku_v1_canonical_key(f"goriyaku:{a}")
        rb = validate_goriyaku_v1_canonical_key(f"goriyaku:{b}")
        assert ra.valid and rb.valid
        assert ra.canonical_key != rb.canonical_key


def test_local_only_legacy_labels_are_not_registered():
    registered_labels = set(GORIYAKU_V1_CANONICAL_KEYS.values())
    for label in LOCAL_ONLY_LEGACY_LABELS:
        assert label not in registered_labels


@pytest.mark.parametrize(
    "candidate",
    [
        "goriyaku:love",
        "goriyaku:money",
        "goriyaku:test",
        "goriyaku:happo",  # 登録keyのprefixだが未登録
        "goriyaku:enmusubi_2",
        "goriyaku:chiiki_antai",  # local-only legacy 地域安泰
    ],
)
def test_unregistered_key_is_rejected_closed_vocabulary(candidate):
    result = validate_goriyaku_v1_canonical_key(candidate)
    assert result.valid is False
    assert result.reason == "unknown_goriyaku_key"
    assert result.canonical_key is None
    assert result.display_label_ja is None


def test_wrong_namespace_rejected():
    result = validate_goriyaku_v1_canonical_key("history_theme:restart")
    assert result.valid is False
    assert result.reason == "wrong_namespace"


def test_registered_key_without_namespace_prefix_is_rejected():
    # 「formatが正しいこと」がregistry登録の代替にならないのと同様、
    # 「registryにあるlocal key」単体もcanonical keyではない。
    result = validate_goriyaku_v1_canonical_key("enmusubi")
    assert result.valid is False
    assert result.reason == "malformed_key"


@pytest.mark.parametrize(
    ("value", "expected_reason"),
    [
        (None, "empty_key"),
        ("", "empty_key"),
        ("no_namespace_prefix", "malformed_key"),
        ("goriyaku:", "empty_key"),
        ("goriyaku:a:b", "malformed_key"),
        (":enmusubi", "missing_namespace"),
    ],
)
def test_format_errors_propagate_from_shared_validator(value, expected_reason):
    # Confirms goriyaku_taxonomy_v1 reuses evidence_taxonomy's format
    # validator rather than re-implementing format parsing.
    result = validate_goriyaku_v1_canonical_key(value)
    assert result.valid is False
    assert result.reason == expected_reason
