"""英語の神社詳細に出す特徴語（GET /api/shrines/{id}/feature-words-en/）と、
英語の推薦理由の「ご縁」の言い方の契約。

- Story は history_culture、Sight・Craft・Feel は scenery_experience の枠に分ける（2026-11-14 承認）。
- 季節の語（見頃のデータが無い）は返さない。
- 公式サイトの引用（evidence_quote）は返さない。出典は source_url と checked_on。
- 特徴語を持たない神社は空の一覧。神社が無いときは 404。ログインなしで読める。
- 英語の推薦理由（travel_ranking.build_reason_en）は、ご縁の強さや運命を名乗らず、
  一致していない Known for の文は相談との一致を名乗らない。
"""

from __future__ import annotations

import datetime
import itertools
import re

import pytest
from django.test import Client

from temples.domain.feature_words_en import FEATURE_WORDS
from temples.models import Shrine
from temples.models_feature_words_en import ShrineFeatureWordEn
from temples.services.travel_ranking import SEASONAL_WORD_IDS, build_reason_en

WORDS_BY_CATEGORY = {
    category: [w for w in FEATURE_WORDS if w.category == category and w.id not in SEASONAL_WORD_IDS]
    for category in ("Sight", "Craft", "Story", "Feel")
}


def _url(pk: int) -> str:
    return f"/api/shrines/{pk}/feature-words-en/"


def _get(pk: int):
    return Client().get(_url(pk), HTTP_HOST="localhost")


def _shrine(name: str = "英語の神社") -> Shrine:
    return Shrine.objects.create(name_jp=name, address=f"東京都{name}", latitude=35.0, longitude=139.0)


def _attach(shrine: Shrine, word_id: str, *, source_url: str = "https://example.jp/official", quote: str = "公式の文言") -> None:
    ShrineFeatureWordEn.objects.create(
        shrine=shrine,
        word_id=word_id,
        vocabulary_version="test",
        evidence_quote=quote,
        source_url=source_url,
        source_type="神社公式",
        checked_on=datetime.date(2026, 11, 1),
    )


# ---------- 特徴語の API ----------


@pytest.mark.django_db
def test_words_are_split_into_slots_by_category():
    shrine = _shrine()
    story = WORDS_BY_CATEGORY["Story"][0]
    sight = WORDS_BY_CATEGORY["Sight"][0]
    craft = WORDS_BY_CATEGORY["Craft"][0]
    feel = WORDS_BY_CATEGORY["Feel"][0]
    for word in (feel, story, craft, sight):
        _attach(shrine, word.id, source_url=f"https://example.jp/{word.id}")

    res = _get(shrine.pk)
    assert res.status_code == 200
    body = res.json()
    assert body["shrine_id"] == shrine.pk
    by_id = {item["word_id"]: item for item in body["items"]}
    assert by_id[story.id]["slot"] == "history_culture"
    for word in (sight, craft, feel):
        assert by_id[word.id]["slot"] == "scenery_experience"
    assert by_id[story.id] == {
        "word_id": story.id,
        "label_en": story.label_en,
        "category": "Story",
        "slot": "history_culture",
        "source_url": f"https://example.jp/{story.id}",
        "checked_on": "2026-11-01",
    }
    # 並びは語彙の順
    order = [w.id for w in FEATURE_WORDS]
    assert [item["word_id"] for item in body["items"]] == sorted(by_id, key=order.index)


@pytest.mark.django_db
def test_evidence_quote_is_not_returned():
    shrine = _shrine()
    _attach(shrine, WORDS_BY_CATEGORY["Story"][0].id, quote="引用_SECRET_MARKER")
    res = _get(shrine.pk)
    assert "引用_SECRET_MARKER" not in res.content.decode("utf-8")
    assert all("evidence_quote" not in item for item in res.json()["items"])


@pytest.mark.django_db
@pytest.mark.parametrize("seasonal", sorted(SEASONAL_WORD_IDS))
def test_seasonal_words_are_not_returned(seasonal):
    shrine = _shrine()
    _attach(shrine, seasonal)
    _attach(shrine, WORDS_BY_CATEGORY["Sight"][0].id)
    ids = [item["word_id"] for item in _get(shrine.pk).json()["items"]]
    assert seasonal not in ids
    assert ids == [WORDS_BY_CATEGORY["Sight"][0].id]


@pytest.mark.django_db
def test_shrine_without_feature_words_returns_empty_list():
    shrine = _shrine()
    res = _get(shrine.pk)
    assert res.status_code == 200
    assert res.json() == {"shrine_id": shrine.pk, "items": []}


@pytest.mark.django_db
def test_unknown_word_ids_are_skipped():
    shrine = _shrine()
    _attach(shrine, "X_NOT_IN_VOCABULARY")
    assert _get(shrine.pk).json()["items"] == []


@pytest.mark.django_db
def test_other_shrines_words_are_not_mixed_in():
    mine, other = _shrine("自分の神社"), _shrine("別の神社")
    _attach(other, WORDS_BY_CATEGORY["Story"][0].id)
    assert _get(mine.pk).json()["items"] == []


@pytest.mark.django_db
def test_missing_shrine_returns_404():
    assert _get(999999).status_code == 404


@pytest.mark.django_db
def test_readable_without_login():
    shrine = _shrine()
    res = Client().get(_url(shrine.pk), HTTP_HOST="localhost")  # 認証なし
    assert res.status_code == 200


def test_every_vocabulary_category_has_a_slot():
    from temples.api.views.shrine_feature_words_en import SLOT_BY_CATEGORY

    assert {w.category for w in FEATURE_WORDS} <= set(SLOT_BY_CATEGORY)
    assert SLOT_BY_CATEGORY["Story"] == "history_culture"
    assert {SLOT_BY_CATEGORY[c] for c in ("Sight", "Craft", "Feel")} == {"scenery_experience"}


# ---------- 英語の推薦理由の「ご縁」の言い方 ----------

# ご縁を強さで比べる・運命として語る言い方（ルール v1.1 12章）。
FORBIDDEN_GOEN_WORDS = re.compile(
    r"\b(goen|fate|fated|destiny|destined|strong connection|deep connection|soulmate)\b", re.IGNORECASE
)
# 一致していない（Known for の）文が、相談との一致を名乗る言い方。
MATCH_CLAIM_WORDS = re.compile(r"\b(match|matches|matched|matching|connect|connects|connected|connection|your)\b", re.IGNORECASE)

ALL_IDS = [w.id for w in FEATURE_WORDS]


def _reason_samples():
    # 全部の語を、1語ずつと3語ずつの組み合わせで試す。
    singles = [[word_id] for word_id in ALL_IDS]
    triples = [list(c) for c in itertools.islice(itertools.combinations(ALL_IDS, 3), 200)]
    return singles + triples


@pytest.mark.parametrize("ids", _reason_samples())
def test_matches_reason_never_uses_goen_strength_or_fate_words(ids):
    reason = build_reason_en(ids, ids)
    assert reason["type"] == "matches"
    assert not FORBIDDEN_GOEN_WORDS.search(reason["text"]), reason["text"]


def _frame(reason: dict) -> str:
    """文から語彙のラベルを除いた、文の枠の部分（語彙には imperial connection などの語がある）。"""
    text = reason["text"]
    for label in reason["labels"]:
        text = text.replace(label, "")
    return text


@pytest.mark.parametrize("ids", _reason_samples())
def test_known_for_reason_does_not_claim_a_match(ids):
    reason = build_reason_en([], ids)
    assert reason["type"] == "known_for"
    assert reason["text"].startswith("Known for: ")
    assert not FORBIDDEN_GOEN_WORDS.search(reason["text"]), reason["text"]
    assert not MATCH_CLAIM_WORDS.search(_frame(reason)), reason["text"]


def test_vocabulary_labels_have_no_goen_strength_or_fate_words():
    for word in FEATURE_WORDS:
        assert not FORBIDDEN_GOEN_WORDS.search(word.label_en), word.label_en
