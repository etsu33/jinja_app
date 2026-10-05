"""MS-5 の Channel B 理由文の型付き provenance（内部用）。

理由文に実際に使った TypedNeedMatch 1件だけを rec["_channel_b_reason_provenance"] に記録する。
公開 Reason Fact schema（_reason_facts / reason_facts / _explanation_payload）には入れず、
carrier と同じ出口（strip_channel_b_carrier）で取り除く。
"""

from __future__ import annotations

import copy
import itertools
import json

import pytest

from temples.services import channel_b_reason_copy, concierge_chat, concierge_chat_ranking
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_REASON_PROVENANCE_KEY,
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
    strip_channel_b_carrier,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import build_recommendation_reason

PRAYER = "official_prayer_supported"
GENERIC = "試験神社は、今の悩みや願いに合わせて参拝先の候補に入れています。"


def _match(
    need: str = "money",
    key: str = "synthetic-prov-0001",
    *,
    wording: str = "商売繁昌",
    signal_type: str = PRAYER,
) -> TypedNeedMatch:
    return TypedNeedMatch(
        need=need,
        canonical_concept_name="商売繁盛",
        signal_type=signal_type,
        source_fact_key=key,
        source_attested_wording=wording,
    )


def _rec(*matches: TypedNeedMatch, **overrides) -> dict:
    rec = {
        "name": "試験神社",
        "goriyaku": "",
        "goriyaku_tag_ids": [],
        "breakdown": {"matched_need_tags": []},
        "_primary_reason_label": "fallback",
        "_primary_reason_source": "fallback",
        "_reason_facts": [{"type": "fallback", "label": "fallback", "evidence": []}],
        CHANNEL_B_TYPED_NEED_MATCHES_KEY: tuple(matches),
    }
    rec.update(overrides)
    return rec


def _reason(rec: dict, need_tags: list[str], public_mode: str = "need") -> str:
    return build_recommendation_reason(
        rec, public_mode=public_mode, birthdate=None, need_tags=need_tags
    )


# ---------- 理由文に使った match だけを記録する ----------


def test_b_only_reason_records_the_provenance_of_the_rendered_match():
    rec = _rec(_match())
    text = _reason(rec, ["money"])
    assert "『商売繁昌』" in text
    assert rec[CHANNEL_B_REASON_PROVENANCE_KEY] == {
        "channel": "channel_b",
        "type": "channel_b_source_fact",
        "source_fact_key": "synthetic-prov-0001",
        "signal_type": PRAYER,
        "need": "money",
    }
    # source wording・concept・confidence は provenance に複製しない。
    assert set(rec[CHANNEL_B_REASON_PROVENANCE_KEY]) == {
        "channel",
        "type",
        "source_fact_key",
        "signal_type",
        "need",
    }
    # 公開 Reason Fact schema（Channel A の reason fact）には入れない。
    assert rec["_reason_facts"] == [{"type": "fallback", "label": "fallback", "evidence": []}]


def test_text_and_provenance_come_from_the_same_selected_instance(monkeypatch):
    seen: dict[str, list] = {"render": [], "provenance": []}
    real_render = concierge_chat_ranking.render_channel_b_reason
    real_provenance = concierge_chat_ranking.channel_b_reason_provenance

    def _render(match, *, name):
        seen["render"].append(match)
        return real_render(match, name=name)

    def _provenance(match):
        seen["provenance"].append(match)
        return real_provenance(match)

    monkeypatch.setattr(concierge_chat_ranking, "render_channel_b_reason", _render)
    monkeypatch.setattr(concierge_chat_ranking, "channel_b_reason_provenance", _provenance)
    rec = _rec(_match("money", "z-key"), _match("money", "a-key"))
    _reason(rec, ["money"])
    assert len(seen["render"]) == len(seen["provenance"]) == 1
    assert seen["provenance"][0] is seen["render"][0]
    assert rec[CHANNEL_B_REASON_PROVENANCE_KEY]["source_fact_key"] == "a-key"


_CANDIDATE_MATCHES = (
    _match("money", "z-money", wording="Z金運"),
    _match("money", "a-money", wording="A金運"),
    _match("study", "b-study", wording="B学業"),
    _match("study", "a-study", wording="A学業"),
)


@pytest.mark.parametrize(
    "need_tags,expected_key,expected_wording",
    [
        (["money", "study"], "a-money", "A金運"),
        (["study", "money"], "a-study", "A学業"),
    ],
)
def test_carrier_order_permutations_keep_text_and_provenance_aligned(
    need_tags, expected_key, expected_wording
):
    for carrier in itertools.permutations(_CANDIDATE_MATCHES):
        rec = _rec(*carrier)
        text = _reason(rec, need_tags)
        selected = channel_b_reason_copy.select_channel_b_reason_match(rec, need_tags, [])
        provenance = rec[CHANNEL_B_REASON_PROVENANCE_KEY]
        assert selected.source_fact_key == provenance["source_fact_key"] == expected_key
        assert provenance["need"] == selected.need
        assert f"『{expected_wording}』" in text
        assert text == channel_b_reason_copy.render_channel_b_reason(selected, name="試験神社")


# ---------- Channel B の理由文を使わないときは provenance を付けない ----------


@pytest.mark.parametrize(
    "rec_factory,need_tags",
    [
        # Channel A が同じ Need の理由を持つ。
        (lambda: _rec(_match(), breakdown={"matched_need_tags": ["money"]}), ["money"]),
        (
            lambda: _rec(
                _match(), _primary_reason_label="money", _primary_reason_source="need_tag"
            ),
            ["money"],
        ),
        # request の Need が無い・一致しない。
        (lambda: _rec(_match()), []),
        (lambda: _rec(_match()), ["study"]),
        # Channel B の一致が無い。
        (lambda: _rec(), ["money"]),
        # 想定外の signal_type・空の wording（generic fallback）。
        (lambda: _rec(_match(signal_type="official_goriyaku_wording")), ["money"]),
        (lambda: _rec(_match(signal_type="")), ["money"]),
        (lambda: _rec(_match(wording="  ")), ["money"]),
    ],
)
def test_no_provenance_when_the_channel_b_reason_is_not_used(rec_factory, need_tags):
    rec = rec_factory()
    text = _reason(rec, need_tags)
    assert "『" not in text
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in rec


def test_generic_fallback_and_compat_mode_have_no_provenance():
    rec = _rec(_match(signal_type="unknown"))
    assert _reason(rec, ["money"]) == GENERIC
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in rec
    compat = _rec(_match())
    _reason(compat, ["money"], public_mode="compat")
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in compat


def test_stale_provenance_is_removed_when_the_reason_no_longer_uses_channel_b():
    rec = _rec(_match())
    _reason(rec, ["money"])
    assert CHANNEL_B_REASON_PROVENANCE_KEY in rec
    rec["breakdown"] = {"matched_need_tags": ["money"]}
    _reason(rec, ["money"])
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in rec


# ---------- 公開の出口 ----------


def test_strip_removes_the_provenance_with_the_carrier():
    row = _rec(_match())
    _reason(row, ["money"])
    recs = {"recommendations": [row], "recommendations_v2": [copy.deepcopy(row)]}
    strip_channel_b_carrier(recs)
    for key in ("recommendations", "recommendations_v2"):
        assert CHANNEL_B_REASON_PROVENANCE_KEY not in recs[key][0]
        assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in recs[key][0]


def _candidate(name: str, **overrides) -> dict:
    row = {
        "id": sum(map(ord, name)),
        "shrine_id": sum(map(ord, name)),
        "name": name,
        "address": "東京都試験区1-1-1",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": 100.0,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "popular_score": 0.0,
    }
    row.update(overrides)
    return row


@pytest.mark.django_db
def test_provenance_exists_before_the_public_boundary_and_not_after(settings, monkeypatch):
    settings.CONCIERGE_USE_LLM = False
    pre_strip: list[dict] = []
    real_strip = concierge_chat.strip_channel_b_carrier

    def _spy(recs):
        pre_strip.extend(copy.deepcopy(r) for r in recs.get("recommendations") or [])
        return real_strip(recs)

    monkeypatch.setattr(concierge_chat, "strip_channel_b_carrier", _spy)
    b_only = _candidate("経路B神社")
    b_only[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = (_match(),)
    a_and_b = _candidate("経路AB神社", goriyaku_tag_ids=[4])
    a_and_b[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = (_match(key="synthetic-prov-0002"),)
    out = build_chat_recommendations(
        query="",
        language="ja",
        candidates=[b_only, a_and_b, _candidate("一致なし神社")],
        bias={"lat": 35.0, "lng": 139.0},
        public_mode="need",
        flow="A",
        need_tags=["money"],
        llm_enabled=False,
    )

    internal = {r["name"]: r for r in pre_strip}
    assert internal["経路B神社"][CHANNEL_B_REASON_PROVENANCE_KEY]["source_fact_key"] == (
        "synthetic-prov-0001"
    )
    # A + B が同じ Need（Channel A の理由）・Channel B の一致が無い候補には付かない。
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in internal["経路AB神社"]
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in internal["一致なし神社"]
    for row in out["recommendations"]:
        assert CHANNEL_B_REASON_PROVENANCE_KEY not in row
        assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in row
        # provenance は公開 Reason Fact schema にも説明 payload にも入らない。
        blob = json.dumps(
            [row.get("_reason_facts"), row.get("reason_facts"), row.get("_explanation_payload")],
            ensure_ascii=False,
            default=str,
        )
        assert "channel_b_source_fact" not in blob
        assert "synthetic-prov-000" not in blob
    raw = json.dumps(out, ensure_ascii=False, default=str)
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in raw
    assert "source_fact_key" not in raw
    assert "synthetic-prov-000" not in raw
