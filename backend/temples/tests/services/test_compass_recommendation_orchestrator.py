from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from temples.models import Shrine
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
        return Shrine.objects.get(pk=shrine.pk)

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
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.state == STATE_RECOMMENDATION_SUCCESS
        names = [r.get("name") for r in result.recommendations]
        assert "北の神社" in names

    def test_direction_context_is_passed_through_unmodified(self, shrine_factory) -> None:
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
        assert result.direction_context == NORTH_DIRECTION_CONTEXT

    def test_only_direction_filtered_candidates_are_considered(self, shrine_factory) -> None:
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運")
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
class TestPurposeIntegration:
    def test_changing_purpose_changes_recommendation_order(self, shrine_factory) -> None:
        # Both north of origin (same authorized sector), so any ranking
        # difference must come from purpose, not from the direction filter.
        shrine_factory(
            name="仕事の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運祈願"
        )
        shrine_factory(
            name="学問の神社", latitude=36.0, longitude=135.05, goriyaku="学問成就"
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
        shrine_factory(name="仕事の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運祈願")
        shrine_factory(name="学問の神社", latitude=36.0, longitude=135.05, goriyaku="学問成就")

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
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運")

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
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運")

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
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運")

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
        shrine_factory(name="北の神社", latitude=36.0, longitude=135.0, goriyaku="仕事運祈願")

        result = get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )

        assert result.state == STATE_RECOMMENDATION_SUCCESS
        reason = result.recommendations[0].get("reason")
        assert isinstance(reason, str)
        assert reason.strip()


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
