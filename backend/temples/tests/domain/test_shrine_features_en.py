# -*- coding: utf-8 -*-
"""神社ごとの英語の特徴語（temples/domain/shrine_features_en.py）の単体テスト。"""

import glob
import json
import os

from temples.domain.feature_words_en import FEATURE_WORDS
from temples.domain.shrine_features_en import SHRINE_FEATURES

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_seeds")


def test_ten_shrines_with_unique_names():
    names = [entry.name_jp for entry in SHRINE_FEATURES]
    assert len(names) == 10
    assert len(set(names)) == 10


def test_feature_ids_exist_in_vocabulary_and_are_not_duplicated():
    known = {w.id for w in FEATURE_WORDS}
    for entry in SHRINE_FEATURES:
        assert entry.feature_ids, entry.name_jp
        assert len(entry.feature_ids) == len(set(entry.feature_ids)), entry.name_jp
        assert set(entry.feature_ids) <= known, entry.name_jp


def test_matches_spreadsheet_row_count():
    # 当てはめ表は104行。日光東照宮の C_CARVINGS が2行（根拠が2つ）あるので、IDとしては103
    assert sum(len(entry.feature_ids) for entry in SHRINE_FEATURES) == 103


def test_name_and_address_match_knowledge_seeds_exactly():
    # resolve_shrine は正式名称と住所の完全一致で結びつける。知識データと1文字でも違うと外れる
    refs = set()
    for path in glob.glob(os.path.join(SEED_DIR, "*.json")):
        with open(path, encoding="utf-8") as f:
            for shrine in json.load(f).get("shrines", []):
                ref = shrine.get("shrine_ref") or {}
                refs.add((ref.get("name_jp"), ref.get("address")))
    for entry in SHRINE_FEATURES:
        assert (entry.name_jp, entry.address) in refs, entry.name_jp
