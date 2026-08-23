# Pins the Compass Purpose -> Goriyaku mapping correction
# (docs/audit/compass-purpose-goriyaku-mapping.md, Option A) so a future
# edit to NEED_TO_GORIYAKU_IDS surfaces as an intentional diff here rather
# than a silent regression. VALID/QUESTIONABLE IDs kept from the audit are
# asserted alongside the INVALID removals / MISSING additions so both
# directions of the correction are covered.
from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS


def test_love_mapping_matches_audited_correction():
    assert NEED_TO_GORIYAKU_IDS["love"] == {1, 20}


def test_career_mapping_matches_audited_correction():
    assert NEED_TO_GORIYAKU_IDS["career"] == {6, 21, 30, 12, 27}


def test_money_mapping_matches_audited_correction():
    assert NEED_TO_GORIYAKU_IDS["money"] == {5, 36, 4, 28}


def test_study_mapping_matches_audited_correction():
    assert NEED_TO_GORIYAKU_IDS["study"] == {9, 10}


def test_protection_mapping_matches_audited_correction():
    assert NEED_TO_GORIYAKU_IDS["protection"] == {11, 32, 2}


def test_purposes_outside_correction_scope_are_unchanged():
    # relationship/marriage/communication/health/mental/courage/focus/rest/
    # family/travel_safe were explicitly out of scope for this correction
    # (docs/audit/compass-purpose-goriyaku-mapping.md "Out of Scope") --
    # pinned so a future edit can't silently widen the change.
    assert NEED_TO_GORIYAKU_IDS["relationship"] == {1, 27, 34, 43}
    assert NEED_TO_GORIYAKU_IDS["marriage"] == {1, 27, 29}
    assert NEED_TO_GORIYAKU_IDS["communication"] == {30, 33, 37, 39}
    assert NEED_TO_GORIYAKU_IDS["health"] == {7, 8, 44, 45}
    assert NEED_TO_GORIYAKU_IDS["mental"] == {11, 16, 26, 28, 38, 43}
    assert NEED_TO_GORIYAKU_IDS["courage"] == {12, 15, 18, 20, 24, 30, 38}
    assert NEED_TO_GORIYAKU_IDS["focus"] == {3, 4, 39}
    assert NEED_TO_GORIYAKU_IDS["rest"] == {7, 8, 43, 44, 45}
    assert NEED_TO_GORIYAKU_IDS["family"] == {2, 25, 27, 34, 42}
    assert NEED_TO_GORIYAKU_IDS["travel_safe"] == {10, 22, 23}
