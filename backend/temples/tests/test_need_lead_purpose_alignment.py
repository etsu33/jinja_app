# Pins the Lead selection responsibility change adopted from
# docs/audit/compass-need-lead-purpose-alignment.md (Option C:
# USE_MATCHED_EVIDENCE_CHAIN): matched goriyaku_tag label -> matched
# text_hint -> Purpose fallback -> generic fallback. Ranking / Scoring /
# Mapping / NEED_TEXT_WEIGHTS / PRIMARY_REASON_PRIORITY / Reason Body
# (intent_map/mapping copy) are out of scope for this PR and unchanged.
from __future__ import annotations

from temples.services.concierge_chat_ranking import (
    _build_need_lead,
    _resolve_matched_lead_evidence,
    build_recommendation_reason,
)


class TestBuildNeedLeadEvidenceChain:
    def test_matched_gid_label_wins_over_unrelated_first_goriyaku(self):
        # 7-1: career, candidate's first-listed goriyaku is unrelated
        # ("厄除け"), but a career-matched GID label is available.
        assert (
            _build_need_lead(
                "career",
                "厄除け・家内安全",
                matched_gid_label="仕事運",
            )
            == "仕事運"
        )

    def test_protection_matched_gid_label_wins_over_love_first_goriyaku(self):
        # 7-2: the exact MISALIGNED case the audit found (protection
        # candidate's first goriyaku is "縁結び", a love-domain word).
        assert (
            _build_need_lead(
                "protection",
                "縁結び・厄除け・交通安全",
                matched_gid_label="厄除け",
            )
            == "厄除け"
        )

    def test_matched_gid_label_wins_over_matched_text_hint(self):
        # 7-3: both evidence types present -- GID label takes priority.
        assert (
            _build_need_lead(
                "career",
                "",
                matched_gid_label="仕事運",
                matched_text_hint="勝運",
            )
            == "仕事運"
        )

    def test_text_only_evidence_used_when_no_matched_gid(self):
        # 7-4: TEXT_ONLY candidate (no matched GID) -- career/靖國神社 real
        # case from docs/audit/compass-text-evidence-scoring-responsibility.md.
        assert (
            _build_need_lead(
                "career",
                "厄除け・家内安全・勝運",
                matched_gid_label=None,
                matched_text_hint="勝運",
            )
            == "勝運"
        )

    def test_purpose_fallback_used_when_no_matched_evidence(self):
        # 7-5: no matched GID, no matched text -- existing Purpose fallback.
        assert _build_need_lead("protection", "縁結び・厄除け") == "厄除け"
        assert _build_need_lead("career", "") == "仕事運"

    def test_generic_fallback_used_for_undefined_purpose_without_evidence(self):
        # 7-6: undefined Purpose (no fallback dict entry), no matched evidence.
        assert _build_need_lead("family", "縁結び・安産") == "ご利益"

    def test_first_goriyaku_item_is_never_used_as_lead(self):
        # goriyaku itself is retained only for call-site/signature stability
        # (docs/audit/compass-need-lead-purpose-alignment.md Phase 6) -- it
        # must never surface as the lead, matched evidence or not.
        assert _build_need_lead("money", "縁結び・仕事運") == "金運"


class TestResolveMatchedLeadEvidence:
    def test_matched_gid_resolved_from_rec_without_extra_query(self):
        rec = {"goriyaku_tag_ids": [2, 99], "_prefilter_debug": {}}
        gid_label, text_hint = _resolve_matched_lead_evidence(
            rec, "protection", {2: "厄除け", 11: "勝運", 32: "災難除け"}
        )
        assert gid_label == "厄除け"
        assert text_hint is None

    def test_lowest_id_wins_when_multiple_gids_match(self):
        # docs/audit/compass-need-lead-purpose-alignment.md 7節: ascending
        # GID id is the deterministic tie-break (no new taxonomy introduced).
        rec = {"goriyaku_tag_ids": [11, 2], "_prefilter_debug": {}}
        gid_label, _ = _resolve_matched_lead_evidence(
            rec, "protection", {2: "厄除け", 11: "勝運", 32: "災難除け"}
        )
        assert gid_label == "厄除け"

    def test_text_hint_resolved_only_when_no_gid_match(self):
        rec = {
            "goriyaku_tag_ids": [],
            "_prefilter_debug": {
                "matched_text_hints_by_tag": {"career": ["勝運", "仕事運"]},
            },
        }
        gid_label, text_hint = _resolve_matched_lead_evidence(rec, "career", {12: "仕事運"})
        assert gid_label is None
        # weight最大の語を採用（NEED_TEXT_WEIGHTS["career"]: 仕事運=1, 勝運=2）
        assert text_hint == "勝運"

    def test_text_hint_ignored_when_gid_already_matched(self):
        rec = {
            "goriyaku_tag_ids": [12],
            "_prefilter_debug": {
                "matched_text_hints_by_tag": {"career": ["勝運"]},
            },
        }
        gid_label, text_hint = _resolve_matched_lead_evidence(rec, "career", {12: "仕事運"})
        assert gid_label == "仕事運"
        assert text_hint is None

    def test_no_query_when_need_gid_label_by_id_is_empty(self):
        rec = {"goriyaku_tag_ids": [2], "_prefilter_debug": {}}
        gid_label, text_hint = _resolve_matched_lead_evidence(rec, "protection", {})
        assert gid_label is None
        assert text_hint is None


class TestBuildRecommendationReasonLeadWiring:
    def test_purpose_matched_via_gid_uses_matched_gid_label_as_lead(self):
        rec = {
            "name": "赤坂氷川神社",
            "goriyaku": "縁結び・厄除け・仕事運",
            "goriyaku_tag_ids": [2],
            "_prefilter_debug": {"matched_text_hints_by_tag": {}},
            "breakdown": {"matched_need_tags": ["protection"]},
            "_primary_reason_label": "protection",
        }
        text = build_recommendation_reason(
            rec,
            public_mode="need",
            birthdate=None,
            need_tags=["protection"],
            need_gid_label_by_id={2: "厄除け", 11: "勝運", 32: "災難除け"},
        )
        assert text == "厄除けのご利益で知られる赤坂氷川神社は、厄除けや守りを願う参拝先として適しています。"

    def test_purpose_matched_via_text_only_uses_matched_text_hint_as_lead(self):
        rec = {
            "name": "靖國神社",
            "goriyaku": "厄除け・家内安全・勝運",
            "goriyaku_tag_ids": [2],
            "_prefilter_debug": {"matched_text_hints_by_tag": {"career": ["勝運"]}},
            "breakdown": {"matched_need_tags": ["career"]},
            "_primary_reason_label": "career",
        }
        text = build_recommendation_reason(
            rec,
            public_mode="need",
            birthdate=None,
            need_tags=["career"],
            need_gid_label_by_id={12: "仕事運", 27: "出世運"},
        )
        assert text == "勝運のご利益で知られる靖國神社は、仕事や転機を願う参拝先として適しています。"

    def test_no_matched_evidence_falls_back_without_extra_wiring(self):
        rec = {
            "name": "長太稲荷神社",
            "goriyaku": "",
            "goriyaku_tag_ids": [],
            "_prefilter_debug": {},
            "breakdown": {"matched_need_tags": []},
            "_primary_reason_label": "",
        }
        text = build_recommendation_reason(
            rec,
            public_mode="need",
            birthdate=None,
            need_tags=["study"],
            need_gid_label_by_id={9: "学業成就", 10: "合格祈願"},
        )
        assert text == "長太稲荷神社は、今の悩みや願いに合わせて参拝先の候補に入れています。"

    def test_generic_primary_reason_label_falls_back_to_generic_lead(self):
        # 実運用でPurpose Evidenceが皆無の候補は、_resolve_primary_reasonが
        # label="fallback"を返す（docs/audit/compass-reason-evidence-priority.md
        # 3節）。"fallback"はPurpose fallback辞書にもmatched evidenceにも
        # 存在しないため、genericな"ご利益"へ落ちる（goriyaku先頭語を
        # 推測で使わない、Phase A9のstudy境界と整合）。
        rec = {
            "name": "明治神宮",
            "goriyaku": "縁結び・厄除け・交通安全",
            "goriyaku_tag_ids": [1, 2],
            "_prefilter_debug": {},
            "breakdown": {"matched_need_tags": []},
            "_primary_reason_label": "fallback",
        }
        text = build_recommendation_reason(
            rec,
            public_mode="need",
            birthdate=None,
            need_tags=["study"],
            need_gid_label_by_id={9: "学業成就", 10: "合格祈願"},
        )
        assert text == "ご利益のご利益で知られる明治神宮は、今の願いを願う参拝先として適しています。"

    def test_need_gid_label_by_id_omitted_does_not_error(self):
        # Backward compatibility: callers that don't pass need_gid_label_by_id
        # (default None) must not error and must fall back cleanly.
        rec = {
            "name": "明治神宮",
            "goriyaku": "縁結び・厄除け・交通安全",
            "goriyaku_tag_ids": [2],
            "_prefilter_debug": {},
            "breakdown": {"matched_need_tags": ["protection"]},
            "_primary_reason_label": "protection",
        }
        text = build_recommendation_reason(
            rec,
            public_mode="need",
            birthdate=None,
            need_tags=["protection"],
        )
        assert text == "厄除けのご利益で知られる明治神宮は、厄除けや守りを願う参拝先として適しています。"
