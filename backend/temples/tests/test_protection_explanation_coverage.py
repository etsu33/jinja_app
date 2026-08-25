# Pins the protection Explanation coverage added in
# docs/audit/compass-protection-explanation-coverage.md: intent_map (both
# the name-present and name-absent branches of _build_need_reason_text) and
# _build_need_lead's goriyaku-empty fallback. Text Coverage
# (NEED_TEXT_WEIGHTS) and Mapping (NEED_TO_GORIYAKU_IDS) are out of scope
# for this PR and asserted unchanged elsewhere -- this file only covers the
# two Explanation-layer dicts.
from temples.services.concierge_chat_ranking import (
    _build_need_lead,
    _build_need_reason_text,
)


class TestProtectionReason:
    def test_protection_with_name_no_longer_falls_back_to_generic_today_wish(self):
        text = _build_need_reason_text("protection", name="明治神宮", goriyaku="縁結び・厄除け・交通安全")
        assert "今の願いを願う参拝先" not in text
        assert "厄除けや守りを願う参拝先" in text

    def test_protection_with_name_and_no_matched_evidence_uses_purpose_fallback(self):
        # docs/audit/compass-need-lead-purpose-alignment.md (Option C):
        # goriyaku's own first-listed item is no longer used as the lead --
        # it is not matched evidence for the tag. Without matched_gid_label/
        # matched_text_hint, the lead falls to the Purpose fallback.
        text = _build_need_reason_text("protection", name="明治神宮", goriyaku="縁結び・厄除け・交通安全")
        assert text == "厄除けのご利益で知られる明治神宮は、厄除けや守りを願う参拝先として適しています。"

    def test_protection_with_name_prefers_matched_gid_label_over_goriyaku(self):
        text = _build_need_reason_text(
            "protection",
            name="明治神宮",
            goriyaku="縁結び・厄除け・交通安全",
            matched_gid_label="厄除け",
        )
        assert text == "厄除けのご利益で知られる明治神宮は、厄除けや守りを願う参拝先として適しています。"

    def test_protection_without_name_no_longer_falls_back_to_generic_copy(self):
        text = _build_need_reason_text("protection", name="", goriyaku="")
        assert text != "今の悩みや願いに寄り添いやすい神社としておすすめしています。"
        assert "厄除けや守り" in text

    def test_protection_reason_does_not_claim_a_guaranteed_outcome(self):
        # Explicit outcome-guarantee phrases are prohibited
        # (docs/audit/compass-protection-explanation-coverage.md 禁止事項).
        for text in (
            _build_need_reason_text("protection", name="明治神宮", goriyaku="厄除け"),
            _build_need_reason_text("protection", name="", goriyaku=""),
        ):
            assert "厄が払われます" not in text
            assert "守られます" not in text
            assert "災難を防げます" not in text


class TestProtectionLead:
    def test_protection_lead_without_matched_evidence_uses_purpose_fallback(self):
        # docs/audit/compass-need-lead-purpose-alignment.md (Option C):
        # goriyaku is no longer consulted for the lead; without matched
        # evidence this always resolves to protection's Purpose fallback.
        assert _build_need_lead("protection", "厄除け・家内安全") == "厄除け"
        assert _build_need_lead("protection", "縁結び・厄除け") == "厄除け"

    def test_protection_lead_prefers_matched_gid_label(self):
        assert (
            _build_need_lead("protection", "縁結び・厄除け", matched_gid_label="厄除け")
            == "厄除け"
        )

    def test_protection_lead_falls_back_to_specific_term_not_generic_goriyaku(self):
        assert _build_need_lead("protection", "") != "ご利益"
        assert _build_need_lead("protection", "") == "厄除け"


class TestOtherPurposesUnchanged:
    """Regression: adding protection must not alter any of the 7 existing
    intent_map / lead-fallback entries."""

    def test_intent_map_with_name_unchanged_for_existing_purposes(self):
        # intent_map（user_intent句）自体はこのPRで変更していない。lead部分は
        # matched evidence未指定のためPurpose fallbackへ変わる
        # (docs/audit/compass-need-lead-purpose-alignment.md Option C)。
        assert _build_need_reason_text("love", name="明治神宮", goriyaku="縁結び") == (
            "良縁成就のご利益で知られる明治神宮は、恋愛や良縁を願う参拝先として適しています。"
        )
        assert _build_need_reason_text("study", name="湯島天満宮", goriyaku="学業成就") == (
            "学業成就のご利益で知られる湯島天満宮は、学業や合格を願う参拝先として適しています。"
        )
        assert _build_need_reason_text("money", name="花園神社", goriyaku="商売繁盛") == (
            "金運のご利益で知られる花園神社は、金運向上を願う参拝先として適しています。"
        )
        # matched_gid_labelを指定すれば、その具体的な語がleadに使われる。
        assert _build_need_reason_text(
            "money", name="花園神社", goriyaku="商売繁盛", matched_gid_label="商売繁盛"
        ) == (
            "商売繁盛のご利益で知られる花園神社は、金運向上を願う参拝先として適しています。"
        )

    def test_mapping_without_name_unchanged_for_existing_purposes(self):
        assert _build_need_reason_text("study", name="", goriyaku="") == (
            "学業や合格を願う今の気持ちに寄り添いやすく、参拝にも向いています。"
        )
        assert _build_need_reason_text("courage", name="", goriyaku="") == (
            "前に進みたい、流れを変えたい今の気持ちを後押しする参拝に向いています。"
        )

    def test_lead_fallback_unchanged_for_existing_purposes(self):
        assert _build_need_lead("study", "") == "学業成就"
        assert _build_need_lead("money", "") == "金運"
        assert _build_need_lead("courage", "") == "開運"

    def test_untouched_purposes_still_fall_back_to_generic_copy(self):
        # Purposes outside this PR's scope (career/health/etc. that still
        # have no intent_map entry) must keep falling back exactly as
        # before -- this PR only added "protection".
        assert _build_need_reason_text("family", name="", goriyaku="") == (
            "今の悩みや願いに寄り添いやすい神社としておすすめしています。"
        )
        assert _build_need_reason_text("family", name="X", goriyaku="") == (
            "ご利益のご利益で知られるXは、今の願いを願う参拝先として適しています。"
        )
        assert _build_need_lead("family", "") == "ご利益"
