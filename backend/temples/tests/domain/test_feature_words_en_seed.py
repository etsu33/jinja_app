# -*- coding: utf-8 -*-
"""英語の特徴語の当てはめシード（temples/data/feature_words_en/）の検査。"""

import glob
import json
import os
from datetime import date

from temples.domain.feature_words_en import FEATURE_WORDS, FEATURE_WORDS_VERSION

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
SEED_PATH = os.path.join(DATA_DIR, "feature_words_en", "shrine_feature_words_en_seed.json")


def _seed():
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_seed_shape_matches_spreadsheet():
    seed = _seed()
    assert seed["vocabulary_version"] == FEATURE_WORDS_VERSION
    names = [s["shrine_ref"]["name_jp"] for s in seed["shrines"]]
    assert len(names) == 10
    assert len(set(names)) == 10
    # 当てはめ表は104行（日光東照宮の C_CARVINGS は根拠が2つで2行）
    assert sum(len(s["features"]) for s in seed["shrines"]) == 104


def test_every_row_has_known_word_quote_url_and_date():
    known = {w.id for w in FEATURE_WORDS}
    for block in _seed()["shrines"]:
        for row in block["features"]:
            assert row["word_id"] in known, row
            assert row["evidence_quote"].strip(), row
            assert row["source_url"].startswith("http"), row
            assert row["source_type"], row
            date.fromisoformat(row["checked_on"])


def test_name_and_address_match_knowledge_seeds_exactly():
    # resolve_shrine は正式名称と住所の完全一致で結びつける。知識データと1文字でも違うと外れる
    refs = set()
    for path in glob.glob(os.path.join(DATA_DIR, "knowledge_seeds", "*.json")):
        with open(path, encoding="utf-8") as f:
            for shrine in json.load(f).get("shrines", []):
                ref = shrine.get("shrine_ref") or {}
                refs.add((ref.get("name_jp"), ref.get("address")))
    for block in _seed()["shrines"]:
        ref = block["shrine_ref"]
        assert (ref["name_jp"], ref["address"]) in refs, ref["name_jp"]
