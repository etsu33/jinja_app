# Pins the Text Evidence Scoring Contract adopted from
# docs/audit/compass-text-evidence-scoring-decision.md (RECOMMEND_C1_MAX):
# GID_ONLY -> gid_score, TEXT_ONLY -> text_score, BOTH -> max(gid_score,
# text_score) (tie -> GID), NONE -> 0. Ranking / Mapping / NEED_TEXT_WEIGHTS
# / PRIMARY_REASON_PRIORITY / Reason Body are out of scope for this PR and
# unchanged -- this file only covers the per-tag rank contribution formula
# inside _attach_breakdown.
from __future__ import annotations

from temples.services.concierge_chat_ranking import _attach_breakdown

WEIGHTS = {"element": 0.0, "need": 1.0, "popular": 0.0, "distance": 0.0}


def _run(*, need_tags, goriyaku, description="", goriyaku_tag_ids=None):
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
        weights=WEIGHTS,
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query="",
        requested_goriyaku_tag_ids=None,
        goriyaku_tag_label_by_id={},
        user=None,
    )
    return rec


class TestScoringStateContract:
    def test_gid_only_uses_gid_score(self):
        # 8-1: career GID={6,21,30,12,27}, goriyaku has no career text hint.
        rec = _run(need_tags=["career"], goriyaku="家内安全", goriyaku_tag_ids=[12])
        bd = rec["breakdown"]
        assert bd["matched_need_tags"] == ["career"]
        assert bd["need_evidence_winner_by_tag"] == {"career": "gid"}
        # need axis contribution: gid flat 2.0 (weights.need=1.0 above, so score_v3
        # isn't the target here -- verify via score_need_rank_weighted proxy: score_total
        # itself only carries score_need (binary), so assert via breakdown_detail.
        need_feature = rec["breakdown_detail"]["features"]["need"]
        assert need_feature["rank_weighted"] == 2.0

    def test_text_only_uses_text_score(self):
        # 8-2: career TEXT_ONLY real case (靖國神社/勝運), no matching GID.
        rec = _run(need_tags=["career"], goriyaku="厄除け・家内安全・勝運", goriyaku_tag_ids=[2])
        bd = rec["breakdown"]
        assert bd["matched_need_tags"] == ["career"]
        assert bd["need_evidence_winner_by_tag"] == {"career": "text"}
        need_feature = rec["breakdown_detail"]["features"]["need"]
        # NEED_TEXT_WEIGHTS["career"]["勝運"] == 2 -> 2 * 1.2 == 2.4
        assert need_feature["rank_weighted"] == 2.4

    def test_both_gid_winner(self):
        # 8-3: gid(2.0) > text(1.2) -- career's own real GID + weight-1 hint
        # (仕事運, weight=1 -> 1*1.2=1.2 < 2.0).
        rec = _run(need_tags=["career"], goriyaku="仕事運", goriyaku_tag_ids=[12])
        bd = rec["breakdown"]
        assert bd["need_evidence_winner_by_tag"] == {"career": "gid"}
        need_feature = rec["breakdown_detail"]["features"]["need"]
        assert need_feature["rank_weighted"] == 2.0  # not 2.0 + 1.2 (Additive)

    def test_both_text_winner(self):
        # 8-4: text(2.4) > gid(2.0) -- career's own real GID + weight-2 hint
        # (勝運, without "仕事運" also matching so the sum stays at 2 not 3).
        rec = _run(need_tags=["career"], goriyaku="家内安全・勝運", goriyaku_tag_ids=[12])
        bd = rec["breakdown"]
        assert bd["need_evidence_winner_by_tag"] == {"career": "text"}
        need_feature = rec["breakdown_detail"]["features"]["need"]
        assert need_feature["rank_weighted"] == 2.4  # not 2.0 + 2.4 (Additive)

    def test_both_tie_prefers_gid(self):
        # 8-5: a true tie (gid_score == text_score) is mathematically
        # unreachable through NEED_TEXT_WEIGHTS -- gid_score is always the
        # flat 2.0, text_score is always (integer weight sum) * 1.2, and no
        # positive integer N satisfies N * 1.2 == 2.0 (N would need to be
        # 5/3). The Contract's "tie -> GID" rule and the observed GID_WINNER
        # case (test_both_gid_winner, text(1.2) < gid(2.0)) exercise the same
        # `else: winner = "gid"` branch a genuine tie would take; this test
        # additionally asserts the comparison is strict (`>`, not `>=`) so an
        # equal value cannot make text win.
        import inspect

        from temples.services import concierge_chat_ranking as ranking_mod

        source = inspect.getsource(ranking_mod._attach_breakdown)
        assert '"text" if text_weighted > gid_weighted else "gid"' in source

    def test_none_has_zero_score_and_no_winner(self):
        # 8-6
        rec = _run(need_tags=["career"], goriyaku="縁結び・安産", goriyaku_tag_ids=[1])
        bd = rec["breakdown"]
        assert bd["matched_need_tags"] == []
        assert bd["need_evidence_winner_by_tag"] == {}
        need_feature = rec["breakdown_detail"]["features"]["need"]
        assert need_feature["rank_weighted"] == 0.0


class TestRawEvidencePreserved:
    def test_matched_by_gid_and_matched_by_text_counts_kept_for_both(self):
        # 9-6 (raw evidence preservation): even though text loses the max()
        # comparison, matched_by_gid_count/matched_by_text_count and
        # matched_need_tags must still reflect that both evidence types
        # actually matched -- only the *score contribution* is deduped.
        rec = _run(need_tags=["career"], goriyaku="仕事運・勝運", goriyaku_tag_ids=[12])
        need_feature = rec["breakdown_detail"]["features"]["need"]
        assert need_feature["matched_by_gid_count"] == 1
        assert need_feature["matched_by_text_count"] == 1
        assert rec["breakdown"]["matched_need_tags"] == ["career"]
