from __future__ import annotations

import math
from typing import Any
from unittest.mock import patch

import pytest

from temples.models import Shrine
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.services import compass_recommendation_orchestrator as orchestrator
from temples.services.compass_recommendation_orchestrator import (
    STATE_DIRECTION_FILTER_UNAVAILABLE,
    STATE_DIRECTION_ZERO_CANDIDATES,
    STATE_EVIDENCE_ZERO_CANDIDATES,
    STATE_INVALID_PURPOSE,
    STATE_NO_COMMON_DIRECTION,
    STATE_RECOMMENDATION_SUCCESS,
    get_compass_recommendations,
)
from temples.services.compass_runtime import NoCommonDirectionResult

ORIGIN = {"lat": 35.0, "lng": 135.0}
NORTH_DIRECTION_CONTEXT = {"referenceDirections": ["北"]}

# Shrine fixture coordinates below are chosen to stay within the Compass
# Geographic Distance Boundary's 60km outer stage (see
# TestDistanceStage*/TestDistanceStageBoundaries below for the boundary
# behavior itself) while preserving the same direction label as before this
# feature existed -- verified against the real _bearing()/_direction_label()
# functions, not assumed from the lat/lng ratio alone.


@pytest.fixture
def shrine_factory(db):
    def _factory(
        *,
        name: str,
        latitude: float,
        longitude: float,
        goriyaku: str = "",
        address: str = "東京都千代田区",
        popular_score: float = 0.0,
        usable_knowledge: bool = True,
    ) -> Shrine:
        shrine = Shrine(
            name_jp=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            goriyaku=goriyaku,
            popular_score=popular_score,
        )
        Shrine.objects.bulk_create([shrine])
        created = Shrine.objects.get(pk=shrine.pk)
        if usable_knowledge:
            # Shared Recommendation Eligibility gate（build_chat_candidates）を
            # 通過させるためのusable Deity Fact。Compass側にeligibility判定は
            # 一切実装していない -- 共有層の判定をそのまま受けている。
            attach_usable_deity_fact(created, display_name=f"{name}の祭神")
        return created

    return _factory


@pytest.mark.django_db
class TestInvalidPurpose:
    def test_unknown_purpose_returns_invalid_purpose_without_recommendations(self) -> None:
        result = get_compass_recommendations(
            purpose="not_a_real_need_tag",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_INVALID_PURPOSE
        assert result.recommendations == []

    def test_empty_purpose_returns_invalid_purpose(self) -> None:
        result = get_compass_recommendations(
            purpose="",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_INVALID_PURPOSE

    def test_invalid_purpose_never_queries_shrine_table(self, django_assert_num_queries) -> None:
        with django_assert_num_queries(0):
            get_compass_recommendations(
                purpose="not_a_real_need_tag",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )


@pytest.mark.django_db
class TestDirectionFilterUnavailable:
    def test_missing_direction_context_is_unavailable_not_zero(self) -> None:
        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=None,
        )
        assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE
        assert result.recommendations == []

    def test_missing_origin_is_unavailable_not_zero(self) -> None:
        result = get_compass_recommendations(
            purpose="career",
            origin=None,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE

    def test_unrecognized_reference_directions_is_unavailable(self) -> None:
        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context={"referenceDirections": ["invalid-label"]},
        )
        assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE

    def test_unavailable_state_never_calls_recommendation_domain(self) -> None:
        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations"
        ) as mock_recommend:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=None,
            )
        mock_recommend.assert_not_called()


@pytest.mark.django_db
class TestNoCommonDirection:
    """Runtime Contract Section 8 Group B: valid input, calculation
    completed, but annual ∩ monthly is empty. Distinct from Group A
    (STATE_DIRECTION_FILTER_UNAVAILABLE, tested above)."""

    def test_no_common_direction_marker_maps_to_its_own_state(self) -> None:
        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NoCommonDirectionResult(),
        )
        assert result.state == STATE_NO_COMMON_DIRECTION
        assert result.state != STATE_DIRECTION_FILTER_UNAVAILABLE
        assert result.recommendations == []

    def test_no_common_direction_never_calls_candidate_filter(self) -> None:
        with patch(
            "temples.services.compass_recommendation_orchestrator.filter_candidates_by_direction"
        ) as mock_filter:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NoCommonDirectionResult(),
            )
        mock_filter.assert_not_called()

    def test_no_common_direction_never_calls_recommendation_domain(self) -> None:
        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations"
        ) as mock_recommend:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NoCommonDirectionResult(),
            )
        mock_recommend.assert_not_called()

    def test_no_common_direction_response_carries_no_direction_context(self) -> None:
        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NoCommonDirectionResult(),
        )
        assert result.direction_context is None

    def test_invalid_purpose_with_no_common_direction_marker_stays_json_safe(self) -> None:
        """Regression: the NoCommonDirectionResult marker must never leak
        into CompassRecommendationResult.direction_context, even when a
        different validation (purpose) fails first -- it is not
        JSON-serializable and api_views_compass.py serializes this field
        directly into the HTTP response body."""
        result = get_compass_recommendations(
            purpose="not_a_real_need_tag",
            origin=ORIGIN,
            direction_context=NoCommonDirectionResult(),
        )
        assert result.state == STATE_INVALID_PURPOSE
        assert result.direction_context is None


@pytest.mark.django_db
class TestDirectionZeroCandidates:
    def test_shrine_outside_authorized_sector_yields_zero_candidates_state(
        self, shrine_factory
    ) -> None:
        # South of origin -- outside the authorized "北" (north) sector.
        shrine_factory(name="南の神社", latitude=34.0, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
        assert result.recommendations == []

    def test_zero_candidates_never_calls_recommendation_domain(self, shrine_factory) -> None:
        shrine_factory(name="南の神社", latitude=34.0, longitude=135.0)

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations"
        ) as mock_recommend:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )
        mock_recommend.assert_not_called()


@pytest.mark.django_db
class TestRecommendationSuccess:
    def test_shrine_inside_authorized_sector_is_recommended(self, shrine_factory) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_RECOMMENDATION_SUCCESS
        names = [r.get("name") for r in result.recommendations]
        assert "北の神社" in names

    def test_direction_context_is_passed_through_unmodified(self, shrine_factory) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.direction_context == NORTH_DIRECTION_CONTEXT

    def test_only_direction_filtered_candidates_are_considered(self, shrine_factory) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")
        shrine_factory(name="南の神社", latitude=34.0, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        names = [r.get("name") for r in result.recommendations]
        assert "北の神社" in names
        assert "南の神社" not in names


@pytest.mark.django_db
class TestMonthlyFallbackDirectionContext:
    """Product Contract Section 2.2 / Runtime Contract Section 5-1 (#2508
    Option C): a Monthly Fallback direction_context is just a
    CompassDirectionRuntime dict with calculationMethod="monthly_kyusei_v1"
    instead of "annual_monthly_kyusei_v1" -- this orchestrator does not (and
    must not) branch on calculationMethod, so a fallback-shaped context must
    reach exactly the same states (recommendation_success,
    direction_zero_candidates) as a common-direction context. Proves
    "fallback direction exists" is not the same thing as "recommendation
    candidate exists" (Section 27/28 of the implementation task)."""

    FALLBACK_DIRECTION_CONTEXT = {
        "referenceDirections": ["南東"],
        "calculationMethod": "monthly_kyusei_v1",
    }

    def test_fallback_context_reaches_recommendation_success(self, shrine_factory) -> None:
        shrine_factory(name="南東の神社", latitude=34.825, longitude=135.35, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=self.FALLBACK_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_RECOMMENDATION_SUCCESS
        names = [r.get("name") for r in result.recommendations]
        assert "南東の神社" in names

    def test_fallback_context_calculation_method_passed_through_unmodified(self, shrine_factory) -> None:
        shrine_factory(name="南東の神社", latitude=34.825, longitude=135.35, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=self.FALLBACK_DIRECTION_CONTEXT,
        )
        assert result.direction_context == self.FALLBACK_DIRECTION_CONTEXT

    def test_fallback_context_with_no_matching_shrine_is_zero_candidates_not_no_common_direction(
        self, shrine_factory
    ) -> None:
        # North of origin -- outside the authorized "南東" (southeast) sector.
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=self.FALLBACK_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
        assert result.state != STATE_NO_COMMON_DIRECTION
        assert result.recommendations == []


@pytest.mark.django_db
class TestPurposeIntegration:
    def test_changing_purpose_changes_recommendation_order(self, shrine_factory) -> None:
        # Both north of origin (same authorized sector), so any ranking
        # difference must come from purpose, not from the direction filter.
        shrine_factory(
            name="仕事の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運祈願"
        )
        shrine_factory(
            name="学問の神社", latitude=35.3, longitude=135.05, goriyaku="学問成就"
        )

        career_result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        study_result = get_compass_recommendations(
            purpose="study",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert career_result.state == STATE_RECOMMENDATION_SUCCESS
        assert study_result.state == STATE_RECOMMENDATION_SUCCESS

        career_top = career_result.recommendations[0].get("name")
        study_top = study_result.recommendations[0].get("name")
        assert career_top == "仕事の神社"
        assert study_top == "学問の神社"

    def test_changing_purpose_does_not_change_which_shrines_pass_direction_filter(
        self, shrine_factory
    ) -> None:
        shrine_factory(name="仕事の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運祈願")
        shrine_factory(name="学問の神社", latitude=35.3, longitude=135.05, goriyaku="学問成就")

        career_result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        study_result = get_compass_recommendations(
            purpose="study",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        career_names = {r.get("name") for r in career_result.recommendations}
        study_names = {r.get("name") for r in study_result.recommendations}
        assert career_names == study_names
        assert {"仕事の神社", "学問の神社"} <= career_names

    def test_purpose_does_not_alter_direction_filter_call_arguments(
        self, shrine_factory
    ) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.filter_candidates_by_direction",
            wraps=orchestrator.filter_candidates_by_direction,
        ) as spy:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )
            get_compass_recommendations(
                purpose="study",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert spy.call_count == 2
        for call in spy.call_args_list:
            assert call.kwargs["origin"] == ORIGIN
            assert call.kwargs["reference_directions"] == ["北"]


@pytest.mark.django_db
class TestEvidenceZeroCandidates:
    def test_empty_recommendations_from_domain_maps_to_evidence_zero_candidates(
        self, shrine_factory
    ) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            return_value={"recommendations": []},
        ):
            result = get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert result.state == STATE_EVIDENCE_ZERO_CANDIDATES
        assert result.recommendations == []


@pytest.mark.django_db
class TestRankingAndReasonAuthorityUnchanged:
    def test_orchestrator_does_not_pass_custom_weights(self, shrine_factory) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        _, kwargs = spy.call_args
        assert "weights" not in kwargs
        assert kwargs["public_mode"] == "need"

    def test_recommendation_reason_field_is_present_and_shrine_grounded(
        self, shrine_factory
    ) -> None:
        shrine_factory(name="北の神社", latitude=35.3, longitude=135.0, goriyaku="仕事運祈願")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        reason = result.recommendations[0].get("reason")
        assert isinstance(reason, str)
        assert reason.strip()


def _lat_at_distance_m(distance_m: float, origin_lat: float = ORIGIN["lat"]) -> float:
    """Latitude due north of ORIGIN (same longitude) at approximately
    `distance_m`. Good enough for placing candidates clearly inside/outside
    a distance ring. Exact boundary values are hardcoded separately (see
    LAT_AT_*M below) because int(...) truncation inside the real
    _distance_m() can land 1m off the simple formula right at an edge."""
    delta_phi = distance_m / 6371000.0
    return origin_lat + math.degrees(delta_phi)


# Binary-searched against the real concierge_chat_candidates._distance_m()
# (haversine, same longitude as ORIGIN) so int(distance_m) equals exactly
# these meter values -- not approximately -- for the Boundary tests below.
LAT_AT_15000M = 35.134898240887814
LAT_AT_15001M = 35.13490723410387
LAT_AT_30000M = 35.26979648177562
LAT_AT_60000M = 35.53959296355124
LAT_AT_60001M = 35.5396019567673


def _recommendation_candidate_names(spy) -> set[str]:
    """Names of the candidates actually passed into build_chat_recommendations
    -- i.e. what survived the distance stage -- independent of whatever
    subset Ranking/Presentation later trims to top-3. Distance Stage's
    Ordering Contract is about this handoff, not the final displayed cards."""
    _, kwargs = spy.call_args
    return {c.get("name") for c in kwargs["candidates"]}


@pytest.mark.django_db
class TestDistanceStage15km:
    def test_five_or_more_within_15km_adopts_stage_15_and_excludes_beyond(
        self, shrine_factory
    ) -> None:
        near_names = set()
        for i, dist in enumerate([1000, 3000, 5000, 8000, 11000, 14000]):
            name = f"近傍神社{i}"
            shrine_factory(name=name, latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運")
            near_names.add(name)
        far_names = set()
        for i, dist in enumerate([20000, 25000]):
            name = f"遠方神社{i}"
            shrine_factory(name=name, latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運")
            far_names.add(name)

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            result = get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_1_KM
        assert result.direction_candidate_count == 8
        assert result.distance_candidate_count == 6
        passed_names = _recommendation_candidate_names(spy)
        assert passed_names == near_names
        assert not (passed_names & far_names)


@pytest.mark.django_db
class TestDistanceStage30km:
    def test_under_5_within_15km_expands_to_30km(self, shrine_factory) -> None:
        within_30_names = set()
        for i, dist in enumerate([5000, 8000, 12000]):
            name = f"15km圏内{i}"
            shrine_factory(name=name, latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運")
            within_30_names.add(name)
        for i, dist in enumerate([18000, 22000, 28000]):
            name = f"30km圏内{i}"
            shrine_factory(name=name, latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運")
            within_30_names.add(name)
        beyond_30 = "30km超神社"
        shrine_factory(name=beyond_30, latitude=_lat_at_distance_m(45000), longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            result = get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_2_KM
        assert result.direction_candidate_count == 7
        assert result.distance_candidate_count == 6
        passed_names = _recommendation_candidate_names(spy)
        assert passed_names == within_30_names
        assert beyond_30 not in passed_names


@pytest.mark.django_db
class TestDistanceStage60km:
    def test_1_to_4_within_60km_succeeds_at_stage_60(self, shrine_factory) -> None:
        within_60_names = set()
        for i, dist in enumerate([5000, 12000, 25000, 55000]):
            name = f"60km圏内{i}"
            shrine_factory(name=name, latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運")
            within_60_names.add(name)
        beyond_60 = "60km超神社"
        shrine_factory(name=beyond_60, latitude=_lat_at_distance_m(90000), longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            result = get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_3_KM
        assert result.direction_candidate_count == 5
        assert result.distance_candidate_count == 4
        passed_names = _recommendation_candidate_names(spy)
        assert passed_names == within_60_names
        assert beyond_60 not in passed_names

    def test_single_candidate_within_60km_succeeds_with_that_one_candidate(
        self, shrine_factory
    ) -> None:
        shrine_factory(
            name="唯一の神社", latitude=_lat_at_distance_m(58000), longitude=135.0, goriyaku="仕事運"
        )

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_3_KM
        assert result.direction_candidate_count == 1
        assert result.distance_candidate_count == 1
        names = {r.get("name") for r in result.recommendations}
        assert "唯一の神社" in names


@pytest.mark.django_db
class TestDistanceStageZeroCandidates:
    def test_direction_filter_empty_has_null_stage_and_zero_counts(self, shrine_factory) -> None:
        # South of origin -- outside the authorized "北" sector. Excluded by
        # Direction Filter itself; the distance stage is never reached.
        shrine_factory(name="南の神社", latitude=34.0, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
        assert result.direction_candidate_count == 0
        assert result.distance_candidate_count == 0
        assert result.distance_stage_km is None
        assert result.recommendations == []

    def test_direction_candidates_exist_but_all_beyond_60km_reports_stage_60(
        self, shrine_factory
    ) -> None:
        # Correct direction (north), but too far for even the widest ring --
        # must not be backfilled from beyond 60km, and must stay
        # direction_zero_candidates (not a new result_state) while
        # metadata distinguishes it from the direction-empty case above.
        shrine_factory(
            name="遠すぎる神社", latitude=_lat_at_distance_m(90000), longitude=135.0, goriyaku="仕事運"
        )

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
        assert result.direction_candidate_count == 1
        assert result.distance_candidate_count == 0
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_3_KM
        assert result.recommendations == []


@pytest.mark.django_db
class TestDistanceStageBoundaries:
    """Distance boundaries are inclusive (<=)."""

    def test_exactly_15000m_is_eligible_15001m_is_not(self, shrine_factory) -> None:
        for i, dist in enumerate([1000, 3000, 5000, 8000]):
            shrine_factory(
                name=f"圏内{i}", latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運"
            )
        shrine_factory(name="境界ちょうど", latitude=LAT_AT_15000M, longitude=135.0, goriyaku="仕事運")
        shrine_factory(name="境界超え", latitude=LAT_AT_15001M, longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            result = get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_1_KM
        assert result.distance_candidate_count == 5
        passed_names = _recommendation_candidate_names(spy)
        assert "境界ちょうど" in passed_names
        assert "境界超え" not in passed_names

    def test_exactly_30000m_is_eligible(self, shrine_factory) -> None:
        # Only 2 candidates within 15km -- forces expansion to Stage 30,
        # where the exact-30000m candidate must be included among the 5.
        for i, dist in enumerate([16000, 18000, 19000, 20000]):
            shrine_factory(
                name=f"30km圏内{i}", latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運"
            )
        shrine_factory(name="30km境界ちょうど", latitude=LAT_AT_30000M, longitude=135.0, goriyaku="仕事運")

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            result = get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_2_KM
        assert result.distance_candidate_count == 5
        passed_names = _recommendation_candidate_names(spy)
        assert "30km境界ちょうど" in passed_names

    def test_exactly_60000m_is_eligible_60001m_is_not(self, shrine_factory) -> None:
        shrine_factory(name="60km境界ちょうど", latitude=LAT_AT_60000M, longitude=135.0, goriyaku="仕事運")
        shrine_factory(name="60km境界超え", latitude=LAT_AT_60001M, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_3_KM
        assert result.direction_candidate_count == 2
        assert result.distance_candidate_count == 1
        names = {r.get("name") for r in result.recommendations}
        assert "60km境界ちょうど" in names
        assert "60km境界超え" not in names


@pytest.mark.django_db
class TestDistanceStageOrderingAndFailSafeStates:
    def test_distance_stage_preserves_direction_filter_order(self, shrine_factory) -> None:
        """Ordering Contract: the distance stage must not re-rank -- it is a
        subset in the same order Direction Filter produced, which itself
        preserves build_chat_candidates' order (distance-sorted when lat/lng
        are given, per that module's own contract)."""
        for i, dist in enumerate([1000, 3000, 5000, 8000, 11000]):
            shrine_factory(
                name=f"順序神社{i}", latitude=_lat_at_distance_m(dist), longitude=135.0, goriyaku="仕事運"
            )

        with patch(
            "temples.services.compass_recommendation_orchestrator.build_chat_recommendations",
            wraps=orchestrator.build_chat_recommendations,
        ) as spy:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NORTH_DIRECTION_CONTEXT,
            )

        _, kwargs = spy.call_args
        passed = kwargs["candidates"]
        distances = [c.get("distance_m") for c in passed]
        assert distances == sorted(distances)

    def test_invalid_distance_m_candidate_is_excluded_but_does_not_break_the_stage(self) -> None:
        """A candidate missing/invalid distance_m must never be eligible at
        any stage, and must never raise -- same isolation guarantee
        filter_candidates_by_direction already provides for bad candidates.
        Unit-tested directly against the pure helper (Required Behavior:
        "1件の不正candidateで全処理を落とさない") rather than through the full
        orchestrator, since a synthetic minimal candidate dict here is not a
        realistic build_chat_candidates() shape."""
        candidates = [
            {"shrine_id": 1, "name": "正常神社0", "distance_m": 1000},
            {"shrine_id": 2, "name": "距離None", "distance_m": None},
            {"shrine_id": 3, "name": "距離が文字列", "distance_m": "not-a-number"},
            {"shrine_id": 4, "name": "distance_m欠落"},
        ]

        eligible, stage_km = orchestrator._apply_compass_distance_stage(candidates)

        assert stage_km == orchestrator.DISTANCE_STAGE_3_KM
        assert [c["name"] for c in eligible] == ["正常神社0"]

    def test_bool_distance_m_is_excluded_not_treated_as_0_or_1(self) -> None:
        """bool is a subclass of int in Python -- a stray `True`/`False`
        distance_m must not be silently treated as 1/0 meters."""
        candidates = [{"shrine_id": 1, "name": "bool距離", "distance_m": True}]

        eligible, stage_km = orchestrator._apply_compass_distance_stage(candidates)

        assert eligible == []
        assert stage_km == orchestrator.DISTANCE_STAGE_3_KM

    def test_common_direction_context_never_calls_distance_stage_short_circuit_states(self) -> None:
        """invalid_purpose / direction_filter_unavailable / no_common_direction
        never reach the distance stage -- metadata stays null (Fail-safe
        contract)."""
        invalid_purpose = get_compass_recommendations(
            purpose="not_a_real_need_tag", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
        )
        assert invalid_purpose.distance_stage_km is None
        assert invalid_purpose.direction_candidate_count is None
        assert invalid_purpose.distance_candidate_count is None

        unavailable = get_compass_recommendations(
            purpose="career", origin=ORIGIN, direction_context=None
        )
        assert unavailable.distance_stage_km is None
        assert unavailable.direction_candidate_count is None
        assert unavailable.distance_candidate_count is None

        no_common = get_compass_recommendations(
            purpose="career", origin=ORIGIN, direction_context=NoCommonDirectionResult()
        )
        assert no_common.distance_stage_km is None
        assert no_common.direction_candidate_count is None
        assert no_common.distance_candidate_count is None

    def test_no_common_direction_never_calls_distance_stage(self) -> None:
        with patch(
            "temples.services.compass_recommendation_orchestrator._apply_compass_distance_stage"
        ) as mock_stage:
            get_compass_recommendations(
                purpose="career",
                origin=ORIGIN,
                direction_context=NoCommonDirectionResult(),
            )
        mock_stage.assert_not_called()


@pytest.mark.django_db
class TestDistanceStageMonthlyFallbackRegression:
    """Distance Stage applies identically under calculationMethod=
    'monthly_kyusei_v1' -- never a different 15/30/60 rule."""

    FALLBACK_DIRECTION_CONTEXT = {
        "referenceDirections": ["南東"],
        "calculationMethod": "monthly_kyusei_v1",
    }

    def test_monthly_fallback_reaches_stage_60_same_as_common(self, shrine_factory) -> None:
        # Southeast of origin, ~37.4km, and the only candidate in the sector
        # -- too few for Stage 15/30's expansion threshold at any ring
        # thickness, so it lands at Stage 60 with 1 candidate, same rule as
        # the COMMON-direction TestDistanceStage60km cases (verified against
        # the real _bearing()/_direction_label()/_distance_m() functions).
        shrine_factory(name="南東の神社", latitude=34.825, longitude=135.35, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=self.FALLBACK_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        assert result.distance_stage_km == orchestrator.DISTANCE_STAGE_3_KM
        assert result.direction_context == self.FALLBACK_DIRECTION_CONTEXT
        assert result.direction_context["calculationMethod"] == "monthly_kyusei_v1"


class TestConciergeIsolation:
    """Regression proof (Section 13): Concierge orchestration must not import
    or depend on the new Compass orchestrator."""

    def test_concierge_chat_view_does_not_import_compass_orchestrator(self) -> None:
        import inspect

        from temples import api_views_concierge

        source = inspect.getsource(api_views_concierge)
        assert "compass_recommendation_orchestrator" not in source

    def test_concierge_chat_service_does_not_import_compass_orchestrator(self) -> None:
        import inspect

        from temples.services import concierge_chat

        source = inspect.getsource(concierge_chat)
        assert "compass_recommendation_orchestrator" not in source
