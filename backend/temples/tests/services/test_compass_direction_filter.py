from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.direction_reference import _DIRECTION_LABELS

ORIGIN = {"lat": 35.0, "lng": 135.0}


def _shrine(id_: str, lat: float = 35.1, lng: float = 135.1) -> dict[str, Any]:
    return {"id": id_, "name": id_, "latitude": lat, "longitude": lng}


class TestFailSafeBehavior:
    def test_missing_origin_returns_none_not_empty_list(self) -> None:
        result = filter_candidates_by_direction(
            [_shrine("a")], origin=None, reference_directions=["北"]
        )
        assert result is None

    def test_origin_without_coordinates_returns_none(self) -> None:
        result = filter_candidates_by_direction(
            [_shrine("a")], origin={"source": "device"}, reference_directions=["北"]
        )
        assert result is None

    def test_none_reference_directions_returns_none(self) -> None:
        result = filter_candidates_by_direction(
            [_shrine("a")], origin=ORIGIN, reference_directions=None
        )
        assert result is None

    def test_empty_reference_directions_returns_none(self) -> None:
        result = filter_candidates_by_direction(
            [_shrine("a")], origin=ORIGIN, reference_directions=[]
        )
        assert result is None

    def test_unrecognized_reference_directions_returns_none(self) -> None:
        result = filter_candidates_by_direction(
            [_shrine("a")], origin=ORIGIN, reference_directions=["NE", "invalid"]
        )
        assert result is None

    def test_confirmed_empty_candidate_list_returns_empty_list_not_none(self) -> None:
        result = filter_candidates_by_direction(
            [], origin=ORIGIN, reference_directions=["北"]
        )
        assert result == []

    def test_missing_shrine_coordinates_excluded_not_crashed(self) -> None:
        candidates = [
            {"id": "no-coords", "name": "no-coords"},
            _shrine("has-coords", lat=36.0, lng=135.0),
        ]
        result = filter_candidates_by_direction(
            candidates, origin=ORIGIN, reference_directions=list(_DIRECTION_LABELS)
        )
        assert result is not None
        ids = [c["id"] for c in result]
        assert "no-coords" not in ids
        assert "has-coords" in ids

    def test_candidate_bearing_exception_is_isolated(self) -> None:
        candidates = [
            _shrine("bad", lat=float("nan"), lng=135.0),
            _shrine("good", lat=36.0, lng=135.0),
        ]
        result = filter_candidates_by_direction(
            candidates, origin=ORIGIN, reference_directions=list(_DIRECTION_LABELS)
        )
        assert result is not None
        ids = [c["id"] for c in result]
        assert "bad" not in ids
        assert "good" in ids

    def test_non_mapping_candidate_is_skipped(self) -> None:
        candidates = [None, "not-a-shrine", _shrine("good", lat=36.0, lng=135.0)]
        result = filter_candidates_by_direction(
            candidates,  # type: ignore[arg-type]
            origin=ORIGIN,
            reference_directions=list(_DIRECTION_LABELS),
        )
        assert result is not None
        assert [c["id"] for c in result] == ["good"]


class TestSectorBoundaries:
    """Boundary rule is inherited from direction_reference._direction_label:
    a bearing exactly at N*45+22.5 belongs to the NEXT sector, not the current one
    (floor-division bucketing). These tests prove the filter reuses that exact
    rule rather than defining a competing one.
    """

    @pytest.mark.parametrize(
        "bearing_degrees,expected_label",
        [
            (0.0, "北"),
            (22.499, "北"),
            (22.5, "北東"),
            (22.501, "北東"),
            (67.499, "北東"),
            (67.5, "東"),
            (67.501, "東"),
            (112.5, "南東"),
            (157.5, "南"),
            (202.5, "南西"),
            (247.5, "西"),
            (292.5, "北西"),
            (337.5, "北"),
            (337.499, "北西"),
            (359.999, "北"),
        ],
    )
    def test_boundary_bearing_maps_to_expected_sector(
        self, bearing_degrees: float, expected_label: str
    ) -> None:
        with patch(
            "temples.services.compass_direction_filter._bearing",
            return_value=bearing_degrees,
        ):
            matched = filter_candidates_by_direction(
                [_shrine("target")],
                origin=ORIGIN,
                reference_directions=[expected_label],
            )
            assert matched == [{"id": "target", "name": "target", "latitude": 35.1, "longitude": 135.1}]

            other_labels = [d for d in _DIRECTION_LABELS if d != expected_label]
            unmatched = filter_candidates_by_direction(
                [_shrine("target")],
                origin=ORIGIN,
                reference_directions=other_labels,
            )
            assert unmatched == []


class TestRealBearingIntegration:
    def test_due_north_shrine_matches_north_sector(self) -> None:
        origin = {"lat": 35.0, "lng": 135.0}
        shrine = _shrine("north-shrine", lat=36.0, lng=135.0)
        result = filter_candidates_by_direction(
            [shrine], origin=origin, reference_directions=["北"]
        )
        assert result == [shrine]

    def test_due_south_shrine_does_not_match_north_sector(self) -> None:
        origin = {"lat": 35.0, "lng": 135.0}
        shrine = _shrine("south-shrine", lat=34.0, lng=135.0)
        result = filter_candidates_by_direction(
            [shrine], origin=origin, reference_directions=["北"]
        )
        assert result == []

    def test_multiple_authorized_sectors(self) -> None:
        origin = {"lat": 35.0, "lng": 135.0}
        north = _shrine("north", lat=36.0, lng=135.0)
        south = _shrine("south", lat=34.0, lng=135.0)
        result = filter_candidates_by_direction(
            [north, south], origin=origin, reference_directions=["北", "南"]
        )
        assert result == [north, south]


class TestPreservation:
    def test_preserves_input_order(self) -> None:
        candidates = [
            _shrine("c", lat=36.0, lng=135.0),
            _shrine("a", lat=36.1, lng=135.0),
            _shrine("b", lat=36.2, lng=135.0),
        ]
        result = filter_candidates_by_direction(
            candidates, origin=ORIGIN, reference_directions=["北"]
        )
        assert result is not None
        assert [c["id"] for c in result] == ["c", "a", "b"]

    def test_preserves_candidate_object_identity_and_all_fields(self) -> None:
        shrine: dict[str, Any] = {
            "id": "x",
            "name": "x",
            "latitude": 36.0,
            "longitude": 135.0,
            "extra_field": "keep-me",
            "score_total": 0.5,
        }
        result = filter_candidates_by_direction(
            [shrine], origin=ORIGIN, reference_directions=["北"]
        )
        assert result is not None
        assert result[0] is shrine
        assert result[0]["extra_field"] == "keep-me"
        assert result[0]["score_total"] == 0.5

    def test_does_not_add_score_or_ranking_fields(self) -> None:
        shrine = _shrine("plain", lat=36.0, lng=135.0)
        result = filter_candidates_by_direction(
            [shrine], origin=ORIGIN, reference_directions=["北"]
        )
        assert result is not None
        assert set(result[0].keys()) == {"id", "name", "latitude", "longitude"}
