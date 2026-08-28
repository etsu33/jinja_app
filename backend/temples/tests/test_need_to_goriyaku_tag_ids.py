# Pins the Compass Purpose -> Goriyaku mapping corrections:
# - docs/audit/compass-purpose-goriyaku-mapping.md (Option A): love/career/
#   money/study/protection
# - docs/audit/goriyaku-mapping-master-integrity.md /
#   goriyaku-mapping-master-integrity-correction.md: removal of stale
#   references to canonical ids 42/43/44/45 (absent from the current 39-row
#   master) from relationship/health/mental/rest/family, and travel_safe
#   corrected to the canonical master's actual travel-safety labels
#   ({3, 13, 14} = 交通安全/航海安全/海上安全, replacing the semantically
#   invalid {10, 22, 23}).
# - docs/audit/remaining-need-goriyaku-semantic-mapping.md
#   (SAFE_CORRECTIONS, Section 19) / safe-remaining-need-goriyaku-mapping-
#   correction.md: relationship/health/focus/family corrected. communication/
#   mental/courage remain unchanged (Section 20, Mother Ship product
#   decisions pending).
# - docs/audit/marriage-love-alias-boundary.md /
#   marriage-need-independence-implementation.md: marriage corrected to
#   {1, 18} and made independently reachable (NEED_TAG_ALIASES["marriage"]
#   removed).
# A future edit to NEED_TO_GORIYAKU_IDS surfaces as an intentional diff
# here rather than a silent regression.
from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS

# Canonical GoriyakuTag master baseline (docs/audit/goriyaku-mapping-master-
# integrity.md Section 4): 39 rows, contiguous ids 1-39. Any
# NEED_TO_GORIYAKU_IDS reference outside this range is a structural
# integrity violation.
CANONICAL_MASTER_ID_RANGE = range(1, 40)


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


def test_travel_safe_mapping_matches_master_integrity_correction():
    assert NEED_TO_GORIYAKU_IDS["travel_safe"] == {3, 13, 14}


def test_stale_ids_removed_from_previously_referencing_purposes():
    # relationship/health/family were also touched by the safe-remaining-
    # need correction below; only mental/rest remain exactly as the
    # stale-id removal alone left them.
    assert NEED_TO_GORIYAKU_IDS["mental"] == {11, 16, 26, 28, 38}
    assert NEED_TO_GORIYAKU_IDS["rest"] == {7, 8}


def test_relationship_mapping_matches_safe_remaining_need_correction():
    assert NEED_TO_GORIYAKU_IDS["relationship"] == {1}


def test_health_mapping_matches_safe_remaining_need_correction():
    assert NEED_TO_GORIYAKU_IDS["health"] == {7, 8, 24, 33, 38}


def test_focus_mapping_matches_safe_remaining_need_correction():
    assert NEED_TO_GORIYAKU_IDS["focus"] == {9, 10}


def test_family_mapping_matches_safe_remaining_need_correction():
    assert NEED_TO_GORIYAKU_IDS["family"] == {2, 26, 34}


def test_marriage_mapping_matches_need_independence_correction():
    assert NEED_TO_GORIYAKU_IDS["marriage"] == {1, 18}
    assert 27 not in NEED_TO_GORIYAKU_IDS["marriage"]
    assert 29 not in NEED_TO_GORIYAKU_IDS["marriage"]


def test_purposes_outside_correction_scope_are_unchanged():
    # communication/mental/courage remain Mother Ship product decisions
    # (docs/audit/remaining-need-goriyaku-semantic-mapping.md Section 20)
    # -- pinned so a future edit can't silently widen the change beyond
    # the approved Needs above.
    assert NEED_TO_GORIYAKU_IDS["communication"] == {30, 33, 37, 39}
    assert NEED_TO_GORIYAKU_IDS["mental"] == {11, 16, 26, 28, 38}
    assert NEED_TO_GORIYAKU_IDS["courage"] == {12, 15, 18, 20, 24, 30, 38}


def test_no_reference_points_outside_canonical_master_id_range():
    for need_tag, goriyaku_ids in NEED_TO_GORIYAKU_IDS.items():
        for goriyaku_id in goriyaku_ids:
            assert goriyaku_id in CANONICAL_MASTER_ID_RANGE, (
                f"{need_tag!r} references goriyaku id {goriyaku_id}, "
                f"outside the canonical master range {CANONICAL_MASTER_ID_RANGE}"
            )


def test_ids_42_to_45_referenced_nowhere():
    stale_ids = {42, 43, 44, 45}
    for need_tag, goriyaku_ids in NEED_TO_GORIYAKU_IDS.items():
        assert not (goriyaku_ids & stale_ids), (
            f"{need_tag!r} still references stale id(s) {goriyaku_ids & stale_ids}"
        )
