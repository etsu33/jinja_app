# backend/temples/tests/test_reason_family.py
"""Reason R2: family.

Adds the missing `intent_map["family"]` entry inside `_build_need_reason_text`
(temples/services/concierge_chat_ranking.py) so recommendations matched to
`family` via valid Family GID evidence no longer fall to the generic
"今の願い" copy.

Depends on Track M1 (merged, PR #2607): family = {16, 35} = 子宝 (id 35) +
安産 (id 16); mental = {11, 26, 28, 38}; protection keeps id 2. The copy
"子宝や安産" is exactly those two GID labels, in the same "AやB" pattern used
by every other Need's intent_map entry. It stays within the adopted NARROW
Family semantics (fertility / childbirth / parenting) and does not broaden
toward household harmony, family-relationship repair, general relationships,
protection, or mental health.

Scope: intent_map["family"] only. Does not touch Interpreter, Need
normalization, Mapping, Axis, Text Evidence, C1, Ranking, or Lead
(docs/audit/remaining-need-semantic-decision-packets.md, Track R2).
"""

from __future__ import annotations

import pytest

from temples.models import GoriyakuTag
from temples.services.concierge_chat import build_chat_recommendations

_GENERIC = "今の願いを願う参拝先として"
_FAMILY_INTENT = "子宝や安産を願う参拝先として適しています。"


def _candidate(name, goriyaku_tag_ids, **overrides):
    base = {
        "name": name,
        "goriyaku_tag_ids": goriyaku_tag_ids,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "astro_elements": [],
        "astro_priority": 0,
        "popular_score": 5.0,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. The intent_map entry exists in the active Reason contract
# ---------------------------------------------------------------------------


def test_intent_map_has_family_entry():
    import inspect

    from temples.services.concierge_chat_ranking import _build_need_reason_text

    src = inspect.getsource(_build_need_reason_text)
    assert '"family": "子宝や安産"' in src


# ---------------------------------------------------------------------------
# 2 & 3. Family recommendation with GID 16 / GID 35 -> family-specific Reason
# 4. ...and not the generic fallback
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("gid", "gid_label"),
    [(16, "安産"), (35, "子宝")],
)
def test_family_gid_evidence_produces_family_specific_reason(gid, gid_label):
    GoriyakuTag.objects.get_or_create(
        id=gid, defaults={"name": gid_label, "category": "ご利益"}
    )
    recs = build_chat_recommendations(
        query="子宝に恵まれたい",
        language="ja",
        candidates=[_candidate(f"{gid_label}神社", [gid])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert "family" in top1["breakdown"]["matched_need_tags"]
    assert top1["breakdown"]["need_evidence_winner_by_tag"].get("family") == "gid"
    reason = top1["reason"]
    assert _GENERIC not in reason
    assert _FAMILY_INTENT in reason
    assert reason.startswith(f"{gid_label}のご利益で知られる")


# ---------------------------------------------------------------------------
# 5. The Reason never presents a removed former Family GID (2/26/34) as
#    Family evidence -- such a candidate has no valid Family evidence after
#    M1, so it correctly falls back rather than claiming a family match.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("former_gid", [2, 26, 34])
def test_former_family_gids_do_not_yield_family_reason(former_gid):
    recs = build_chat_recommendations(
        query="子宝に恵まれたい",
        language="ja",
        candidates=[_candidate("旧family神社", [former_gid])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert top1["breakdown"]["matched_need_tags"] == []
    assert _FAMILY_INTENT not in top1["reason"]


# ---------------------------------------------------------------------------
# 6-8. M1 mapping contract is untouched by this explanation-only PR
# ---------------------------------------------------------------------------


def test_m1_mappings_unchanged():
    from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS

    assert NEED_TO_GORIYAKU_IDS["family"] == {16, 35}
    assert NEED_TO_GORIYAKU_IDS["mental"] == {11, 26, 28, 38}
    assert 2 in NEED_TO_GORIYAKU_IDS["protection"]


def test_family_has_no_text_evidence_entry():
    from temples.services.concierge_chat_ranking import NEED_TEXT_WEIGHTS

    assert "family" not in NEED_TEXT_WEIGHTS


# ---------------------------------------------------------------------------
# 9. Lead / score / matched_tags unchanged -- only the user_intent clause
#    after "、" changed.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_lead_score_and_matched_tags_unchanged():
    GoriyakuTag.objects.get_or_create(
        id=16, defaults={"name": "安産", "category": "ご利益"}
    )
    recs = build_chat_recommendations(
        query="安産祈願をしたい",
        language="ja",
        candidates=[_candidate("安産神社", [16])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    bd = top1["breakdown"]
    assert bd["matched_need_tags"] == ["family"]
    assert bd["score_need"] == 1
    lead_clause = top1["reason"].split("、", 1)[0]
    assert "のご利益で知られる" in lead_clause


# ---------------------------------------------------------------------------
# 10. Top3 composition / ranking unchanged (Reason text is built after
#     scoring and never feeds back into it).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_family_top3_composition_unchanged_by_reason_copy():
    GoriyakuTag.objects.get_or_create(
        id=16, defaults={"name": "安産", "category": "ご利益"}
    )
    candidates = [
        _candidate("安産神社", [16]),
        _candidate("無関係神社", []),
    ]
    recs = build_chat_recommendations(
        query="子宝に恵まれたい",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )
    names_in_order = [r["name"] for r in recs["recommendations"]]
    assert names_in_order[0] == "安産神社"
    assert (
        recs["recommendations"][0]["_score_total"]
        > recs["recommendations"][1]["_score_total"]
    )


# ---------------------------------------------------------------------------
# Unrelated Reason outputs unchanged -- regression controls
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "candidate_name", "goriyaku_tag_ids", "expected"),
    [
        ("いい出会いがほしい", "縁結び神社", [1], "恋愛や良縁を願う参拝先として適しています。"),
        ("結婚したい", "夫婦円満神社", [18], "良縁や夫婦円満を願う参拝先として適しています。"),
        ("転職を考えている", "導き神社", [21], "仕事や転機を願う参拝先として適しています。"),
        ("健康でいたい", "健康神社", [7], "健康や体調の安定を願う参拝先として適しています。"),
        ("集中力を高めたい", "集中神社", [9], "集中や習慣づくりを願う参拝先として適しています。"),
    ],
)
def test_unrelated_need_reason_unchanged(query, candidate_name, goriyaku_tag_ids, expected):
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    assert expected in recs["recommendations"][0]["reason"]
