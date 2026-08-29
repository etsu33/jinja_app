# backend/temples/tests/test_communication_gid_evidence_disabled.py
"""Communication Evidence Policy = DISABLE_GID_EVIDENCE (Track C-EL).

Implements the Mother Ship decision (2026-08-29,
docs/audit/remaining-need-semantic-decision-packets.md
"## Mother Ship Decisions"): Communication = EVIDENCE_LIMITED with Evidence
Policy = DISABLE_GID_EVIDENCE.

The interpreter recognizes `communication` (KEYWORDS / NEED_KEYWORDS,
PR #2601), but its previously-mapped GIDs {30, 33, 37, 39}
(強運厄除け / 病気平癒 / 延命長寿 / 農業守護) are semantically unrelated to
interpersonal communication. This PR removes ``NEED_TO_GORIYAKU_IDS
["communication"]`` (now ``set()``) and adds **no** replacement GID and
**no** Text Evidence.

Expected contract (all intentional):

    communication interpreter recognition  = preserved
    communication GID evidence             = none
    communication Text Evidence            = none
    C1 evidence branch (communication-only)= NONE
    score_need (communication-only)        = 0

Scope: temples/domain/need_to_goriyaku_tag_ids.py only. No interpreter
change, no new taxonomy, no consultation-axis change, no
NEED_TEXT_WEIGHTS["communication"], no Reason copy, no Lead fallback logic,
no C1 scoring rule change, no ranking change.
"""

from __future__ import annotations

import pytest

from temples.domain.need_tags import extract_need_tags
from temples.domain.need_to_goriyaku_tag_ids import (
    NEED_TO_GORIYAKU_IDS,
    need_tags_to_goriyaku_ids,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_need import resolve_need_payload
from temples.services.concierge_chat_ranking import NEED_TEXT_WEIGHTS, _attach_breakdown

# The GIDs communication used to (invalidly) map to.
_FORMER_COMMUNICATION_GIDS = {30, 33, 37, 39}

_NEED_WEIGHTS = {"element": 0.0, "need": 1.0, "popular": 0.0, "distance": 0.0}


def _breakdown(*, need_tags, goriyaku="", goriyaku_tag_ids=None, description=""):
    rec = {
        "id": 1,
        "name": "テスト神社",
        "astro_tags": [],
        "astro_elements": [],
        "goriyaku": goriyaku,
        "description": description,
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


# ---------------------------------------------------------------------------
# Mapping / evidence-path contract
# ---------------------------------------------------------------------------


def test_communication_has_no_mapped_gids():
    assert NEED_TO_GORIYAKU_IDS["communication"] == set()
    assert need_tags_to_goriyaku_ids(["communication"]) == set()


def test_communication_has_no_text_evidence_path():
    assert "communication" not in NEED_TEXT_WEIGHTS


def test_no_replacement_gid_was_added():
    assert NEED_TO_GORIYAKU_IDS["communication"] & _FORMER_COMMUNICATION_GIDS == set()
    assert len(NEED_TO_GORIYAKU_IDS["communication"]) == 0


# ---------------------------------------------------------------------------
# Interpreter recognition is preserved (not this PR's change, guarded here)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "コミュニケーション能力を上げたい",
        "人とうまく話せるようになりたい",
        "営業で成果を出したい",
    ],
)
def test_communication_interpreter_recognition_preserved(query):
    assert "communication" in extract_need_tags(query, max_tags=3).tags
    assert "communication" in resolve_need_payload(
        query=query, need_tags=None, max_tags=3
    )["tags"]


# ---------------------------------------------------------------------------
# C1 NONE branch / score_need == 0 for communication-only evidence
# ---------------------------------------------------------------------------


def test_communication_only_candidate_reaches_c1_none_branch():
    # candidate carries a former communication GID (30) + its label text --
    # neither is evidence for communication any more.
    rec = _breakdown(
        need_tags=["communication"],
        goriyaku="強運厄除け",
        goriyaku_tag_ids=[30],
    )
    bd = rec["breakdown"]
    assert bd["matched_need_tags"] == []
    assert bd["need_evidence_winner_by_tag"] == {}
    assert rec["breakdown_detail"]["features"]["need"]["rank_weighted"] == 0.0
    assert rec["breakdown_detail"]["features"]["need"]["matched_by_gid_count"] == 0
    assert rec["breakdown_detail"]["features"]["need"]["matched_by_text_count"] == 0


def test_communication_only_query_scores_need_zero_end_to_end():
    recs = build_chat_recommendations(
        query="コミュニケーション能力を上げたい",
        language="ja",
        candidates=[
            {
                "name": "強運厄除け神社",
                "goriyaku_tag_ids": [30, 33, 37, 39],
                "goriyaku": "強運厄除け・病気平癒・延命長寿・農業守護",
                "description": "",
                "astro_tags": [],
                "astro_elements": [],
                "astro_priority": 0,
                "popular_score": 5.0,
            }
        ],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    # interpreter still recognized communication as the query's need
    assert recs["_need"]["tags"] == ["communication"]
    # ...but it produced no evidence on this candidate
    assert top1["breakdown"]["matched_need_tags"] == []
    assert top1["breakdown"]["score_need"] == 0

    ep = top1.get("_explanation_payload") or {}
    assert ep.get("primary_need_tag") is None
    primary_reason = ep.get("primary_reason") or {}
    assert primary_reason.get("type") == "fallback"
    # no communication GID (or its label) is cited as evidence anywhere
    assert primary_reason.get("evidence") in ([], None)
    for rf in top1.get("reason_facts") or []:
        assert rf.get("label") != "communication"


def test_no_former_communication_gid_appears_in_winner_metadata():
    rec = _breakdown(need_tags=["communication"], goriyaku_tag_ids=[30, 33, 37, 39])
    detail = rec["breakdown_detail"]["features"]["need"]
    assert detail.get("matched_gid_ids", []) == []
    assert rec["breakdown"]["need_evidence_winner_by_tag"] == {}


# ---------------------------------------------------------------------------
# Non-regression: GID 30 (career, courage) and GID 33 (health) still work
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("need", ["career", "courage"])
def test_gid_30_still_valid_evidence_for_career_and_courage(need):
    assert 30 in NEED_TO_GORIYAKU_IDS[need]
    rec = _breakdown(need_tags=[need], goriyaku_tag_ids=[30])
    assert rec["breakdown"]["matched_need_tags"] == [need]
    assert rec["breakdown"]["need_evidence_winner_by_tag"] == {need: "gid"}
    assert rec["breakdown_detail"]["features"]["need"]["rank_weighted"] == 2.0


def test_gid_33_still_valid_evidence_for_health():
    assert 33 in NEED_TO_GORIYAKU_IDS["health"]
    rec = _breakdown(need_tags=["health"], goriyaku_tag_ids=[33])
    assert rec["breakdown"]["matched_need_tags"] == ["health"]
    assert rec["breakdown"]["need_evidence_winner_by_tag"] == {"health": "gid"}


def test_career_courage_health_mappings_bytewise_unchanged():
    assert NEED_TO_GORIYAKU_IDS["career"] == {6, 21, 30, 12, 27}
    assert NEED_TO_GORIYAKU_IDS["courage"] == {12, 15, 18, 20, 24, 30, 38}
    assert NEED_TO_GORIYAKU_IDS["health"] == {7, 8, 24, 33, 38}
