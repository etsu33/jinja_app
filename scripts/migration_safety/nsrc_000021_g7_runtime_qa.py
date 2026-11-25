#!/usr/bin/env python3
"""nsrc-000021 荒川神社 G7 Production Runtime QA.

Read-only verification of the G5 / G6 runtime surfaces against the configured
database (Deity 1 / History 1; one Source). The entire verification runs inside a
PostgreSQL READ ONLY transaction, so any accidental write attempt fails closed.

The target is always the exact (name_jp, address) identity, never a name-only
match or a numeric PK. Recommendation Top1 / Compass Top1 is not required.
"""

# Django must be configured before the temples imports below.
# ruff: noqa: E402

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")

import django

django.setup()

from django.db import connection, transaction
from temples.api.serializers.shrine import ShrineDetailSerializer
from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineFactSourceCitation,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.concierge_chat import (
    _build_reason_v4_authority_context,
    _build_score_v3_candidate_profile,
)
from temples.services.concierge_chat_candidates import _distance_m, build_chat_candidates
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.knowledge_seed import normalize_source_url
from temples.services.recommendation_eligibility_verifier import (
    ELIGIBLE,
    ShrineIdentity,
    verify_recommendation_eligibility,
)
from temples.services.recommendation_input_profile import build_recommendation_input_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

SHRINE_NAME = "荒川神社"
SHRINE_ADDRESS = "新潟県胎内市桃崎浜187番地"
# frozen G2 adopted coordinate
SHRINE_LAT = 38.1409456
SHRINE_LNG = 139.4073314

SOURCE_TYPE = "government"
SOURCE_URL = "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html"
SOURCE_PUBLISHER = "新潟県"

EXPECTED_DEITIES = ["天鈿女命"]
# (history_type, title)
EXPECTED_HISTORIES = [("regional_context", "船主による船絵馬の奉納")]
FIRST_HISTORY_CONTENT = "荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。"
DEITY_LABEL = "天鈿女命"
EXCLUDED_TEXT = ("1814", "1841", "天保12")
# separate Fact owners sharing the target address (G1); must have no Shrine row at the address
FOREIGN_SAME_ADDRESS_NAMES = ()
FORBIDDEN_GUARANTEE_PHRASES = (
    "必ず",
    "確実",
    "保証",
    "絶対",
    "叶う",
    "成就します",
    "治ります",
    "合格します",
    "効果があります",
    "ご利益があります",
)
DIRECTIONS = ("北", "北東", "東", "南東", "南", "南西", "西", "北西")
QA_ORIGIN = {"lat": 35.681236, "lng": 139.767125}
# G6 measured values for the QA origin and the frozen coordinate
EXPECTED_DISTANCE_M = 275370
EXPECTED_DIRECTION = "北"
AGGREGATE_MODELS = (
    Shrine,
    ShrineKnowledgeSource,
    ShrineDeity,
    ShrineHistory,
    ShrineFactSourceCitation,
    ShrineSourceFact,
    ShrineDeityCollective,
    ShrineGoriyakuAssignment,
)


def _aggregates() -> tuple:
    return tuple(model.objects.count() for model in AGGREGATE_MODELS) + (
        Shrine.goriyaku_tags.through.objects.count(),
    )


def main() -> None:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
        before = _aggregates()

        shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
        assert shrine.latitude == SHRINE_LAT
        assert shrine.longitude == SHRINE_LNG
        print("TARGET_IDENTITY=PASS")

        body = ShrineDetailSerializer(shrine).data
        assert [row["display_name"] for row in body["deities"]] == EXPECTED_DEITIES
        assert [(row["history_type"], row["title"]) for row in body["histories"]] == (
            EXPECTED_HISTORIES
        )
        fact_rows = [*body["deities"], *body["histories"]]
        for row in fact_rows:
            assert row["verification_status"] == "source_confirmed"
            assert len(row["sources"]) == 1
            # A reused pre-existing Source may differ only in URL syntax; compare importer identity.
            assert row["sources"][0]["source_type"] == SOURCE_TYPE
            assert normalize_source_url(row["sources"][0]["url"]) == normalize_source_url(
                SOURCE_URL
            )
            assert row["sources"][0]["verification_status"] == "source_confirmed"
        source_ids = {row["sources"][0]["id"] for row in fact_rows}
        assert {row["id"] for row in body["deities"]} == set(
            ShrineDeity.objects.filter(shrine=shrine).values_list("id", flat=True)
        )
        assert {row["id"] for row in body["histories"]} == set(
            ShrineHistory.objects.filter(shrine=shrine).values_list("id", flat=True)
        )
        returned_text = str(body)
        for needle in EXCLUDED_TEXT:
            assert needle not in returned_text
        print("DETAIL_RUNTIME=PASS")

        # Every target Fact cites exactly the one Source identity; no citation rows exist.
        assert len(source_ids) == 1
        (source_id,) = source_ids
        source = ShrineKnowledgeSource.objects.get(pk=source_id)
        assert source.publisher.strip() == SOURCE_PUBLISHER
        assert (source.confidence, source.language) == ("high", "ja")
        assert (source.bibliography or "").strip() == ""
        assert not ShrineFactSourceCitation.objects.filter(shrine_deity__shrine=shrine).exists()
        assert not ShrineFactSourceCitation.objects.filter(shrine_history__shrine=shrine).exists()
        assert not ShrineSourceFact.objects.filter(shrine=shrine).exists()
        assert not ShrineDeityCollective.objects.filter(shrine=shrine).exists()
        print("SOURCE_RELATION_INTEGRITY=PASS")

        report = verify_recommendation_eligibility(
            shrine_identities=[ShrineIdentity(name=SHRINE_NAME, address=SHRINE_ADDRESS)]
        )
        assert report.summary_counts() == (1, 0, 0)
        [result] = report.results
        assert result.status == ELIGIBLE
        assert result.shrine_id == shrine.pk
        assert result.usable_deity_fact_count == 1
        assert result.usable_history_fact_count == 1
        print("SHARED_ELIGIBILITY=PASS")

        candidates = build_chat_candidates(
            lat=SHRINE_LAT,
            lng=SHRINE_LNG,
            area=None,
            goriyaku_tag_ids=None,
            trace_id="nsrc-000021-g7-production-runtime",
        )
        matches = [
            candidate
            for candidate in candidates
            if candidate.get("name") == SHRINE_NAME and candidate.get("address") == SHRINE_ADDRESS
        ]
        assert len(matches) == 1
        candidate = matches[0]
        assert candidate["id"] == shrine.pk
        assert candidate["shrine_id"] == shrine.pk
        assert candidate["lat"] == SHRINE_LAT
        assert candidate["lng"] == SHRINE_LNG
        assert candidate["distance_m"] == 0
        assert [d["display_name"] for d in candidate["knowledge_deities"]] == EXPECTED_DEITIES
        assert [(h["history_type"], h["title"]) for h in candidate["knowledge_histories"]] == (
            EXPECTED_HISTORIES
        )
        assert candidate["goriyaku_tag_ids"] == []
        print("CONCIERGE_CANDIDATE_PATH=PASS")

        candidate_profile = _build_score_v3_candidate_profile(candidate)
        recommendation_input = build_recommendation_input_profile(
            interpretation_profile={},
            translation_result={},
            candidate_profile=candidate_profile,
            score_v2_fields={},
        )
        preview = build_recommendation_reason_v4(
            recommendation_input_profile=recommendation_input,
            authority_context=_build_reason_v4_authority_context(candidate),
        )
        # G6 measured selection: the Deity sentence; the profile History is the first History.
        assert candidate_profile["deity"] == DEITY_LABEL
        assert preview["fact"]["deity"] == DEITY_LABEL
        assert candidate_profile["shrine_history"] == FIRST_HISTORY_CONTENT
        assert preview["fact"]["shrine_history"] == FIRST_HISTORY_CONTENT
        assert preview["fact"]["goriyaku"] is None
        assert preview["fact"]["history_theme"] is None
        assert preview["fact"]["name"] == SHRINE_NAME
        reason_text = preview["reason_text"]
        assert reason_text.startswith(f"{SHRINE_NAME}では、{DEITY_LABEL}が祀られています。")
        for needle in EXCLUDED_TEXT:
            assert needle not in reason_text
        for phrase in FORBIDDEN_GUARANTEE_PHRASES:
            assert phrase not in reason_text
        # The votive-tablet History is never turned into an efficacy claim.
        for phrase in ("航海安全の効果", "航海安全が叶"):
            assert phrase not in reason_text
        print("RECOMMENDATION_REASON=PASS")

        distance_m = _distance_m(
            QA_ORIGIN["lat"],
            QA_ORIGIN["lng"],
            candidate["lat"],
            candidate["lng"],
        )
        assert isinstance(distance_m, int)
        assert math.isfinite(distance_m)
        assert distance_m == EXPECTED_DISTANCE_M
        print("COMPASS_DISTANCE=PASS")

        bearing = _bearing(
            from_lat=QA_ORIGIN["lat"],
            from_lng=QA_ORIGIN["lng"],
            to_lat=candidate["lat"],
            to_lng=candidate["lng"],
        )
        direction = _direction_label(bearing)
        assert 0.0 <= bearing < 360.0
        assert direction == EXPECTED_DIRECTION
        assert filter_candidates_by_direction(
            [candidate],
            origin=QA_ORIGIN,
            reference_directions=[direction],
        ) == [candidate]
        for other in DIRECTIONS:
            if other != direction:
                assert (
                    filter_candidates_by_direction(
                        [candidate], origin=QA_ORIGIN, reference_directions=[other]
                    )
                    == []
                )
        print("COMPASS_DIRECTION=PASS")

        assert (shrine.goriyaku or "") == ""
        assert not shrine.goriyaku_tags.exists()
        assert not ShrineGoriyakuAssignment.objects.filter(shrine=shrine).exists()
        print("GORIYAKU_ISOLATION=PASS")

        # Only the exact target owns these Facts; no other row shares the precinct address.
        assert list(Shrine.objects.filter(address=SHRINE_ADDRESS).values_list("pk", flat=True)) == [
            shrine.pk
        ]
        for name in FOREIGN_SAME_ADDRESS_NAMES:
            assert not Shrine.objects.filter(name_jp=name, address=SHRINE_ADDRESS).exists()
        assert (
            not ShrineDeity.objects.filter(sources__pk=source_id)
            .exclude(shrine=shrine)
            .filter(display_name__in=EXPECTED_DEITIES)
            .exists()
        )
        print("FACT_OWNERSHIP_ISOLATION=PASS")

        assert _aggregates() == before
        print("AGGREGATES_UNCHANGED=PASS")

    print("G7_PRODUCTION_RUNTIME_QA=PASS")
    print("TRANSACTION_MODE=READ_ONLY")


if __name__ == "__main__":
    main()
