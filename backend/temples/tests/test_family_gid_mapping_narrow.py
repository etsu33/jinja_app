# backend/temples/tests/test_family_gid_mapping_narrow.py
"""Family GID mapping narrowed to fertility evidence (Track M1).

Mother Ship 2026-08-29 (docs/audit/remaining-need-semantic-decision-
packets.md "## Mother Ship Decisions" / "### Family GID Mapping
sub-decision"): Family = NARROW, Family GID Policy = DROP_ALL.

    family:  {2, 26, 34}  ->  {16, 35}   (厄除け/家庭円満/火防 dropped;
                                          安産 + 子宝 added)
    mental:  {11, 16, 26, 28, 38}  ->  {11, 26, 28, 38}   (安産 removed)
    protection: {11, 32, 2}  (unchanged -- id 2 stays)

Scope: temples/domain/need_to_goriyaku_tag_ids.py only. No interpreter /
consultation-axis / NEED_TEXT_WEIGHTS / Reason copy / Lead / C1 scoring /
ranking change. Family Reason copy is Track R2 (after M1 merges).
"""

from __future__ import annotations

import pytest

from temples.domain.need_to_goriyaku_tag_ids import (
    NEED_TO_GORIYAKU_IDS,
    need_tags_to_goriyaku_ids,
)
from temples.services.concierge_chat_ranking import _attach_breakdown

_NEED_WEIGHTS = {"element": 0.0, "need": 1.0, "popular": 0.0, "distance": 0.0}


def _breakdown(*, need_tags, goriyaku="", goriyaku_tag_ids=None):
    rec = {
        "id": 1,
        "name": "テスト神社",
        "astro_tags": [],
        "astro_elements": [],
        "goriyaku": goriyaku,
        "description": "",
        "goriyaku_tag_ids": goriyaku_tag_ids or [],
        "popular_score": 0,
    }
    _attach_breakdown(
        rec,
        birthdate=None,
        need_tags=need_tags,
        weights=_NEED_WEIGHTS,
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query="",
        requested_goriyaku_tag_ids=None,
        goriyaku_tag_label_by_id={},
        user=None,
    )
    return rec


def _matches_via_gid(need, gid):
    rec = _breakdown(need_tags=[need], goriyaku_tag_ids=[gid])
    bd = rec["breakdown"]
    return bd["matched_need_tags"] == [need] and bd["need_evidence_winner_by_tag"] == {
        need: "gid"
    }


# ---------------------------------------------------------------------------
# 1-3. Mapping contract
# ---------------------------------------------------------------------------


def test_family_mapping_is_exactly_16_35():
    assert NEED_TO_GORIYAKU_IDS["family"] == {16, 35}
    assert need_tags_to_goriyaku_ids(["family"]) == {16, 35}


def test_mental_mapping_is_exactly_11_26_28_38():
    assert NEED_TO_GORIYAKU_IDS["mental"] == {11, 26, 28, 38}
    assert 16 not in NEED_TO_GORIYAKU_IDS["mental"]


def test_protection_still_contains_gid_2():
    assert 2 in NEED_TO_GORIYAKU_IDS["protection"]
    assert NEED_TO_GORIYAKU_IDS["protection"] == {11, 32, 2}


# ---------------------------------------------------------------------------
# 4-8. Family GID evidence behavior
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gid", [16, 35])
def test_family_matches_via_new_fertility_gids(gid):
    assert _matches_via_gid("family", gid)


@pytest.mark.parametrize("gid", [2, 26, 34])
def test_former_family_gids_no_longer_count_as_family_evidence(gid):
    rec = _breakdown(need_tags=["family"], goriyaku_tag_ids=[gid])
    bd = rec["breakdown"]
    assert bd["matched_need_tags"] == []
    assert bd["need_evidence_winner_by_tag"] == {}
    assert rec["breakdown_detail"]["features"]["need"]["rank_weighted"] == 0.0


# ---------------------------------------------------------------------------
# 9-10. Mental non-regression + id 16 removal
# ---------------------------------------------------------------------------


def test_mental_no_longer_matches_via_gid_16():
    rec = _breakdown(need_tags=["mental"], goriyaku_tag_ids=[16])
    bd = rec["breakdown"]
    assert bd["matched_need_tags"] == []
    assert bd["need_evidence_winner_by_tag"] == {}


@pytest.mark.parametrize("gid", [11, 26, 28, 38])
def test_mental_still_matches_via_its_retained_gids(gid):
    assert _matches_via_gid("mental", gid)


# ---------------------------------------------------------------------------
# 11. Protection non-regression
# ---------------------------------------------------------------------------


def test_protection_still_matches_via_gid_2():
    assert _matches_via_gid("protection", 2)


# ---------------------------------------------------------------------------
# 12. No unrelated Need mapping changed
# ---------------------------------------------------------------------------


def test_no_unrelated_need_mapping_changed():
    expected = {
        "love": {1, 20},
        "relationship": {1},
        "marriage": {1, 18},
        "communication": set(),
        "career": {6, 21, 30, 12, 27},
        "money": {5, 36, 4, 28},
        "study": {9, 10},
        "health": {7, 8, 24, 33, 38},
        "protection": {11, 32, 2},
        "courage": {12, 15, 18, 20, 24, 30, 38},
        "focus": {9, 10},
        "rest": {7, 8},
        "travel_safe": {3, 13, 14},
    }
    for need, ids in expected.items():
        assert NEED_TO_GORIYAKU_IDS[need] == ids, need
