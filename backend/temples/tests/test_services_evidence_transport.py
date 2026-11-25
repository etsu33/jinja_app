"""Evidence Foundation PR-F5: normalization builder / authoritative snapshot /
final qualification orchestration。"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone as dt_timezone

import pytest
from django.db import DatabaseError, connection
from django.test.utils import CaptureQueriesContext

from temples.domain.evidence_link import (
    GORIYAKU_ASSIGNMENT,
    HISTORY_THEME_ASSIGNMENT,
    SHRINE_DEITY,
    SHRINE_HISTORY,
    FactSourceQualityStatus,
)
from temples.domain.evidence_qualification import (
    EVIDENCE_QUALIFICATION_CONTRACT_VERSION,
    EvidenceQualificationInput,
    EvidenceQualificationResult,
)
from temples.domain.evidence_transport import (
    NormalizedShrineDeityPayloadV1,
    NormalizedShrineHistoryPayloadV1,
)
from temples.domain.goriyaku_taxonomy_v1 import GORIYAKU_V1_CANONICAL_KEYS
from temples.models import (
    EvidenceLink,
    HistoryThemeAssignment,
    Shrine,
    ShrineDeity,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services import evidence_foundation, evidence_transport
from temples.services.evidence_foundation import (
    F4DimensionPreparation,
    F4QualificationPreparation,
)
from temples.services.evidence_transport import (
    F5NormalizationResult,
    FinalQualificationStatus,
    build_final_qualification,
    normalize_evidence_transport,
    qualify_evidence,
)

pytestmark = pytest.mark.django_db

_ASSIGNED_AT = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
_VERIFIED_AT = datetime(2026, 2, 3, 4, 5, 6, 7, tzinfo=dt_timezone.utc)


def _shrine(name: str = "F5神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _assignment(shrine: Shrine, **overrides) -> HistoryThemeAssignment:
    values = dict(
        shrine=shrine,
        canonical_key="history_theme:restart",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_ASSIGNED_AT,
    )
    values.update(overrides)
    return HistoryThemeAssignment.objects.create(**values)


def _source(status: str = "reviewed", **overrides) -> ShrineKnowledgeSource:
    values = dict(
        source_type="shrine_official",
        title=f"{status}出典",
        verification_status=status,
        verified_at=_VERIFIED_AT if status in ("reviewed", "source_confirmed") else None,
    )
    values.update(overrides)
    return ShrineKnowledgeSource.objects.create(**values)


def _history(shrine: Shrine, status: str = "reviewed", **overrides) -> ShrineHistory:
    values = dict(
        shrine=shrine,
        history_type="official_origin",
        title="由緒",
        content="根拠となる由緒。",
        verification_status=status,
        confidence="low",
        verified_at=_VERIFIED_AT if status in ("reviewed", "source_confirmed") else None,
    )
    values.update(overrides)
    return ShrineHistory.objects.create(**values)


def _deity(shrine: Shrine, status: str = "source_confirmed", **overrides) -> ShrineDeity:
    values = dict(
        shrine=shrine,
        display_name="天照大神",
        verification_status=status,
        confidence="low",
        verified_at=_VERIFIED_AT if status in ("reviewed", "source_confirmed") else None,
    )
    values.update(overrides)
    return ShrineDeity.objects.create(**values)


def _qualified_fixture():
    """5次元すべてTrueになる最小構成を作る。"""

    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    history.sources.add(_source())
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="由緒が再出発を裏付ける。",
    )
    return assignment


# --------------------------------------------------------------------------
# normalization builder
# --------------------------------------------------------------------------


def test_history_assignment_with_history_fact_is_normalized():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine, period_text="", event_date=date(1600, 3, 4))
    source = _source(publisher="", accessed_at=date(2026, 5, 6), language="ja")
    history.sources.add(source)
    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="由緒が再出発を裏付ける。",
    )

    result = normalize_evidence_transport(assignment)
    evidence = result.normalized_evidence

    assert result.build_blocked is False
    assert result.transport_traceable is True
    assert result.transport_issues == ()
    assert evidence.schema_version == "v1"
    assert evidence.assignment.type == HISTORY_THEME_ASSIGNMENT
    assert evidence.assignment.id == assignment.pk
    assert evidence.assignment.shrine_id == shrine.pk
    assert evidence.assignment.canonical_key == "history_theme:restart"
    assert evidence.assignment.taxonomy.namespace == "history_theme"
    assert evidence.assignment.taxonomy.taxonomy_version == "v1"
    assert evidence.assignment.lifecycle == HistoryThemeAssignment.Lifecycle.ACTIVE
    assert evidence.assignment.provenance.producer == "admin"
    assert evidence.assignment.provenance.mechanism == "manual_review"
    assert evidence.assignment.provenance.assigned_at == "2026-01-01T00:00:00.000000Z"

    normalized_link = evidence.evidence_links[0]
    assert normalized_link.id == link.pk
    assert normalized_link.assignment_ref.type == HISTORY_THEME_ASSIGNMENT
    assert normalized_link.assignment_ref.id == assignment.pk
    assert normalized_link.rationale == "由緒が再出発を裏付ける。"
    assert normalized_link.fact.type == SHRINE_HISTORY
    assert normalized_link.fact.id == history.pk
    assert normalized_link.fact.shrine_id == shrine.pk
    assert isinstance(normalized_link.fact.payload, NormalizedShrineHistoryPayloadV1)
    assert normalized_link.fact.payload.period_text == ""
    assert normalized_link.fact.payload.event_date == "1600-03-04"
    assert normalized_link.fact.sources[0].id == source.pk
    assert normalized_link.fact.sources[0].accessed_at == "2026-05-06"
    assert normalized_link.fact.sources[0].publisher == ""
    assert normalized_link.fact.sources[0].url == ""


def test_history_assignment_with_deity_fact_is_normalized():
    shrine = _shrine()
    assignment = _assignment(shrine)
    deity = _deity(shrine, canonical_name="", role="primary")
    deity.sources.add(_source())
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_deity=deity,
        rationale="祭神が再出発を裏付ける。",
    )

    evidence = normalize_evidence_transport(assignment).normalized_evidence
    fact = evidence.evidence_links[0].fact

    assert fact.type == SHRINE_DEITY
    assert fact.id == deity.pk
    assert isinstance(fact.payload, NormalizedShrineDeityPayloadV1)
    assert fact.payload.display_name == "天照大神"
    assert fact.payload.canonical_name == ""
    assert fact.payload.role == "primary"
    assert not hasattr(fact.payload, "aliases")


def test_multiple_links_and_sources_keep_pk_ascending_order():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    deity = _deity(shrine)
    first_source = _source()
    second_source = _source("source_confirmed")
    history.sources.add(second_source, first_source)
    deity.sources.add(first_source)
    first_link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="1つ目。",
    )
    second_link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_deity=deity,
        rationale="2つ目。",
    )

    evidence = normalize_evidence_transport(assignment).normalized_evidence

    assert [link.id for link in evidence.evidence_links] == sorted(
        [first_link.pk, second_link.pk]
    )
    history_sources = evidence.evidence_links[0].fact.sources
    assert [source.id for source in history_sources] == sorted(
        [first_source.pk, second_source.pk]
    )


def test_complete_source_set_is_kept_including_draft_source():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    ready_source = _source("reviewed")
    draft_source = _source("draft")
    history.sources.add(ready_source, draft_source)
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="draft Sourceも落とさない。",
    )

    result = normalize_evidence_transport(assignment)
    sources = result.normalized_evidence.evidence_links[0].fact.sources

    assert result.f4_preparation.fact_source_quality_prerequisite is FactSourceQualityStatus.PASS
    assert [source.id for source in sources] == sorted([ready_source.pk, draft_source.pk])
    assert {source.verification_status for source in sources} == {"reviewed", "draft"}


def test_normalizer_re_resolves_current_db_assignment_not_the_caller_instance():
    assignment = _qualified_fixture()
    HistoryThemeAssignment.objects.filter(pk=assignment.pk).update(
        canonical_key="history_theme:overcome"
    )
    assert assignment.canonical_key == "history_theme:restart"

    evidence = normalize_evidence_transport(assignment).normalized_evidence

    assert evidence.assignment.canonical_key == "history_theme:overcome"


def test_normalizer_does_not_write_to_the_database():
    assignment = _qualified_fixture()

    with CaptureQueriesContext(connection) as captured:
        qualify_evidence(assignment)

    write_statements = [
        query["sql"]
        for query in captured.captured_queries
        if query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert write_statements == []


# --------------------------------------------------------------------------
# authoritative snapshot / stale caller state
# --------------------------------------------------------------------------


def test_stale_caller_instance_is_not_authoritative():
    assignment = _qualified_fixture()
    HistoryThemeAssignment.objects.filter(pk=assignment.pk).update(
        lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED
    )
    assert assignment.lifecycle == HistoryThemeAssignment.Lifecycle.ACTIVE

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert outcome.block_reasons == ("non_active_assignment",)
    assert outcome.qualification_input is None
    assert outcome.qualification_result is None


def test_single_authoritative_materialization_per_invocation(monkeypatch):
    assignment = _qualified_fixture()
    materializations = []
    graph_reads = []

    original_materialize = evidence_transport.materialize_evidence_snapshot
    original_link_queryset = evidence_foundation._link_queryset

    def counting_materialize(value):
        materializations.append(value)
        return original_materialize(value)

    def counting_link_queryset(value):
        graph_reads.append(value)
        return original_link_queryset(value)

    def fail_if_called(value):  # pragma: no cover - 呼ばれたら即失敗させるための番人
        raise AssertionError("F5はF4のためにEvidence graphを再materializeしてはいけない")

    monkeypatch.setattr(evidence_transport, "materialize_evidence_snapshot", counting_materialize)
    monkeypatch.setattr(evidence_foundation, "_link_queryset", counting_link_queryset)
    monkeypatch.setattr(evidence_foundation, "prepare_f4_qualification", fail_if_called)

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert len(materializations) == 1
    assert len(graph_reads) == 1


def test_f4_and_f5_share_the_same_immutable_snapshot(monkeypatch):
    assignment = _qualified_fixture()
    snapshots = []
    original_evaluate = evidence_transport.evaluate_f4_from_snapshot
    original_build = evidence_transport.build_normalized_evidence

    def capture_evaluate(snapshot):
        snapshots.append(snapshot)
        return original_evaluate(snapshot)

    def capture_build(snapshot):
        snapshots.append(snapshot)
        return original_build(snapshot)

    monkeypatch.setattr(evidence_transport, "evaluate_f4_from_snapshot", capture_evaluate)
    monkeypatch.setattr(evidence_transport, "build_normalized_evidence", capture_build)

    normalize_evidence_transport(assignment)

    assert len(snapshots) == 2
    assert snapshots[0] is snapshots[1]
    assert dataclasses.is_dataclass(snapshots[0])
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshots[0].links = ()


# --------------------------------------------------------------------------
# BUILD BLOCK
# --------------------------------------------------------------------------


def test_f4_build_block_is_propagated_as_f5_build_block(monkeypatch):
    shrine = _shrine()
    assignment = _assignment(shrine, lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED)
    calls = []
    monkeypatch.setattr(
        evidence_transport,
        "evaluate_evidence_qualification",
        lambda *args, **kwargs: calls.append(args),
    )

    result = normalize_evidence_transport(assignment)
    outcome = build_final_qualification(result)

    assert result.build_blocked is True
    assert result.block_reasons == ("non_active_assignment",)
    assert result.normalized_evidence is None
    assert result.transport_traceable is None
    assert result.transport_issues == ()
    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert calls == []


def test_required_provider_unavailable_is_build_blocked():
    assignment = _qualified_fixture()

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            HistoryThemeAssignment.objects,
            "filter",
            lambda *args, **kwargs: (_ for _ in ()).throw(DatabaseError("provider unavailable")),
        )
        outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert outcome.block_reasons == ("required_provider_unavailable",)
    assert outcome.qualification_result is None


def test_naive_transport_datetime_is_build_blocked(monkeypatch):
    assignment = _qualified_fixture()
    original_materialize = evidence_transport.materialize_evidence_snapshot
    evaluator_calls = []

    def naive_snapshot(value):
        snapshot = original_materialize(value)
        snapshot.assignment.assigned_at = datetime(2026, 1, 1, 0, 0, 0)
        return snapshot

    monkeypatch.setattr(evidence_transport, "materialize_evidence_snapshot", naive_snapshot)
    monkeypatch.setattr(
        evidence_transport,
        "evaluate_evidence_qualification",
        lambda *args, **kwargs: evaluator_calls.append(args),
    )

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert "invalid_transport_datetime" in outcome.block_reasons
    assert outcome.qualification_input is None
    assert evaluator_calls == []


def test_required_dimension_provider_invalid_is_build_blocked(monkeypatch):
    assignment = _qualified_fixture()
    original_materialize = evidence_transport.materialize_evidence_snapshot

    def invalid_provider_snapshot(value):
        snapshot = original_materialize(value)
        snapshot.assignment.producer = None
        return snapshot

    monkeypatch.setattr(
        evidence_transport, "materialize_evidence_snapshot", invalid_provider_snapshot
    )

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert "required_dimension_provider_invalid" in outcome.block_reasons
    assert outcome.qualification_result is None


# --------------------------------------------------------------------------
# final qualification（BLOCKED vs NOT QUALIFIED）
# --------------------------------------------------------------------------


def _preparation(**dimension_overrides) -> F4QualificationPreparation:
    dimensions = dataclasses.replace(
        F4DimensionPreparation(
            identifiable=True,
            taxonomy_stable=True,
            provenance_satisfied=True,
            semantic_assignment_traceable=True,
        ),
        **dimension_overrides,
    )
    return F4QualificationPreparation(
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=1,
        lifecycle_prerequisite=True,
        structural_prerequisite=True,
        fact_source_quality_prerequisite=FactSourceQualityStatus.PASS,
        dimensions=dimensions,
        build_blocked=False,
        block_reasons=(),
        structural_issues=(),
    )


def _normalization(*, transport_traceable=True, **dimension_overrides) -> F5NormalizationResult:
    return F5NormalizationResult(
        f4_preparation=_preparation(**dimension_overrides),
        normalized_evidence=None,
        transport_traceable=transport_traceable,
        transport_issues=(),
        build_blocked=False,
        block_reasons=(),
    )


def test_all_five_dimensions_true_is_evaluated_and_qualified():
    outcome = build_final_qualification(_normalization())

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.build_blocked is False
    assert isinstance(outcome.qualification_input, EvidenceQualificationInput)
    assert isinstance(outcome.qualification_result, EvidenceQualificationResult)
    assert outcome.qualification_result.qualified is True
    assert outcome.qualification_result.unmet_dimensions == ()
    assert (
        outcome.qualification_result.qualification_version
        == EVIDENCE_QUALIFICATION_CONTRACT_VERSION
    )
    assert not hasattr(outcome, "qualified")


@pytest.mark.parametrize(
    "dimension",
    [
        "identifiable",
        "taxonomy_stable",
        "provenance_satisfied",
        "semantic_assignment_traceable",
    ],
)
def test_false_f4_dimension_is_evaluated_and_not_qualified(dimension):
    outcome = build_final_qualification(_normalization(**{dimension: False}))

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert outcome.qualification_result.unmet_dimensions == (dimension,)


def test_false_transport_traceable_is_evaluated_and_not_qualified():
    outcome = build_final_qualification(_normalization(transport_traceable=False))

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert outcome.qualification_result.unmet_dimensions == ("transport_traceable",)


def test_five_dimensions_are_assembled_one_to_one_without_recomputation():
    normalization = _normalization(taxonomy_stable=False, provenance_satisfied=False)

    outcome = build_final_qualification(normalization)

    assert outcome.qualification_input.as_dimension_dict() == {
        "identifiable": True,
        "taxonomy_stable": False,
        "provenance_satisfied": False,
        "semantic_assignment_traceable": True,
        "transport_traceable": True,
    }


def test_blocked_and_not_qualified_are_never_conflated():
    blocked = build_final_qualification(
        F5NormalizationResult(
            f4_preparation=_preparation(),
            normalized_evidence=None,
            transport_traceable=None,
            transport_issues=(),
            build_blocked=True,
            block_reasons=("non_active_assignment",),
        )
    )
    not_qualified = build_final_qualification(_normalization(transport_traceable=False))

    assert blocked.status is FinalQualificationStatus.BLOCKED
    assert blocked.qualification_input is None
    assert blocked.qualification_result is None
    assert not_qualified.status is FinalQualificationStatus.EVALUATED
    assert not_qualified.qualification_result.qualified is False


def test_evaluator_is_called_exactly_once_on_the_official_evaluated_path(monkeypatch):
    assignment = _qualified_fixture()
    calls = []
    original = evidence_transport.evaluate_evidence_qualification

    def counting(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(evidence_transport, "evaluate_evidence_qualification", counting)

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is True
    assert len(calls) == 1


def test_zero_evidence_link_is_transport_traceable_but_not_semantically_traceable():
    assignment = _assignment(_shrine())

    outcome = qualify_evidence(assignment)
    normalization = normalize_evidence_transport(assignment)

    assert normalization.normalized_evidence.evidence_links == ()
    assert normalization.transport_traceable is True
    assert normalization.f4_preparation.dimensions.semantic_assignment_traceable is False
    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert outcome.qualification_result.unmet_dimensions == ("semantic_assignment_traceable",)


def test_stale_taxonomy_version_is_not_qualified_but_not_blocked():
    shrine = _shrine()
    assignment = _assignment(shrine, taxonomy_version="v999")
    history = _history(shrine)
    history.sources.add(_source())
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="taxonomyだけが古い。",
    )

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert outcome.qualification_result.unmet_dimensions == ("taxonomy_stable",)


def test_unapproved_goriyaku_canonical_key_is_not_taxonomy_stable():
    # G1 activated 18 approved canonical keys, but the registry stays
    # fail-closed for everything else: an unapproved key still cannot make
    # taxonomy_stable True.
    assert "unapproved_pending_data_review" not in GORIYAKU_V1_CANONICAL_KEYS
    shrine = _shrine()
    assignment = ShrineGoriyakuAssignment.objects.create(
        shrine=shrine,
        canonical_key="goriyaku:unapproved_pending_data_review",
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_ASSIGNED_AT,
    )

    normalization = normalize_evidence_transport(assignment)
    outcome = qualify_evidence(assignment)

    assert normalization.f4_preparation.assignment_model == GORIYAKU_ASSIGNMENT
    assert normalization.f4_preparation.dimensions.taxonomy_stable is False
    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert "taxonomy_stable" in outcome.qualification_result.unmet_dimensions


def test_goriyaku_assignment_with_approved_key_can_be_qualified():
    # G1: with an approved canonical key (goriyaku:misfortune_warding) the
    # existing 5-dimension evaluator reaches qualified=True through the same
    # official path used by history_theme -- no qualification logic changed,
    # and taxonomy_stable alone is still not sufficient (the other four
    # dimensions are satisfied by this fixture's links/provenance/transport).
    assert "misfortune_warding" in GORIYAKU_V1_CANONICAL_KEYS
    shrine = _shrine()
    assignment = ShrineGoriyakuAssignment.objects.create(
        shrine=shrine,
        canonical_key="goriyaku:misfortune_warding",
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_ASSIGNED_AT,
    )
    history = _history(shrine)
    history.sources.add(_source())
    EvidenceLink.objects.create(
        goriyaku_assignment=assignment,
        shrine_history=history,
        rationale="由緒が厄除けの由来を裏付ける。",
    )

    normalization = normalize_evidence_transport(assignment)
    outcome = qualify_evidence(assignment)

    assert normalization.f4_preparation.assignment_model == GORIYAKU_ASSIGNMENT
    assert normalization.f4_preparation.dimensions.taxonomy_stable is True
    assert normalization.build_blocked is False
    assert normalization.transport_traceable is True
    assert normalization.normalized_evidence.assignment.canonical_key == (
        "goriyaku:misfortune_warding"
    )
    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is True
    assert outcome.qualification_result.unmet_dimensions == ()


def test_taxonomy_stable_alone_does_not_qualify_a_goriyaku_assignment():
    # F4/F5 regression guard: an approved canonical key makes taxonomy_stable
    # True, but with no EvidenceLink the assignment is still not qualified.
    shrine = _shrine()
    assignment = ShrineGoriyakuAssignment.objects.create(
        shrine=shrine,
        canonical_key="goriyaku:misfortune_warding",
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_ASSIGNED_AT,
    )

    outcome = qualify_evidence(assignment)

    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert "semantic_assignment_traceable" in outcome.qualification_result.unmet_dimensions


# --------------------------------------------------------------------------
# Transport IntegrityはNormalizer自身のbugを検知する
# --------------------------------------------------------------------------


def _two_source_fixture():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    history.sources.add(_source("reviewed"), _source("source_confirmed"))
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="由緒が再出発を裏付ける。",
    )
    return assignment


def _sabotaged_normalizer(monkeypatch, transform):
    """official orchestration pathのNormalizerだけを意図的に破損させる。"""

    original = evidence_transport.build_normalized_evidence

    def broken(snapshot):
        return transform(original(snapshot))

    monkeypatch.setattr(evidence_transport, "build_normalized_evidence", broken)


def _replace_first_link(evidence, **changes):
    link = dataclasses.replace(evidence.evidence_links[0], **changes)
    return dataclasses.replace(
        evidence, evidence_links=(link,) + evidence.evidence_links[1:]
    )


def test_normalizer_dropping_one_source_is_detected_by_transport_integrity(monkeypatch):
    assignment = _two_source_fixture()

    def drop_last_source(evidence):
        fact = evidence.evidence_links[0].fact
        return _replace_first_link(
            evidence, fact=dataclasses.replace(fact, sources=fact.sources[:-1])
        )

    _sabotaged_normalizer(monkeypatch, drop_last_source)

    result = normalize_evidence_transport(assignment)
    outcome = build_final_qualification(result)

    assert result.build_blocked is False
    assert result.transport_traceable is False
    assert "source_set_mismatch" in tuple(issue.code for issue in result.transport_issues)
    assert outcome.status is FinalQualificationStatus.EVALUATED
    assert outcome.qualification_result.qualified is False
    assert outcome.qualification_result.unmet_dimensions == ("transport_traceable",)


def test_normalizer_mutating_rationale_is_detected_by_transport_integrity(monkeypatch):
    assignment = _qualified_fixture()

    _sabotaged_normalizer(
        monkeypatch, lambda evidence: _replace_first_link(evidence, rationale="書き換えた根拠。")
    )

    result = normalize_evidence_transport(assignment)

    assert result.transport_traceable is False
    assert "rationale_mismatch" in tuple(issue.code for issue in result.transport_issues)


def test_normalizer_mutating_fact_payload_is_detected_by_transport_integrity(monkeypatch):
    assignment = _qualified_fixture()

    def mutate_payload(evidence):
        fact = evidence.evidence_links[0].fact
        payload = dataclasses.replace(fact.payload, title="改変されたタイトル")
        return _replace_first_link(evidence, fact=dataclasses.replace(fact, payload=payload))

    _sabotaged_normalizer(monkeypatch, mutate_payload)

    result = normalize_evidence_transport(assignment)

    assert result.transport_traceable is False
    assert "fact_payload_mismatch" in tuple(issue.code for issue in result.transport_issues)


def test_authoritative_expectation_is_built_without_the_normalizer(monkeypatch):
    assignment = _two_source_fixture()
    snapshot = evidence_foundation.materialize_evidence_snapshot(assignment)

    def fail_if_called(value):  # pragma: no cover - 呼ばれたら即失敗させるための番人
        raise AssertionError("authoritative expectationはNormalizerを経由してはいけない")

    monkeypatch.setattr(evidence_transport, "build_normalized_evidence", fail_if_called)

    expectation = evidence_transport.build_authoritative_expectation(snapshot)

    assert expectation["schemaVersion"] == "v1"
    assert expectation["assignment"]["id"] == assignment.pk
    assert len(expectation["evidenceLinks"][0]["fact"]["sources"]) == 2


# --------------------------------------------------------------------------
# final qualification: 5 dimensionsのbool contract
# --------------------------------------------------------------------------


def test_non_bool_transport_traceable_is_blocked_without_calling_the_evaluator(monkeypatch):
    calls = []
    monkeypatch.setattr(
        evidence_transport,
        "evaluate_evidence_qualification",
        lambda *args, **kwargs: calls.append(args),
    )

    outcome = build_final_qualification(_normalization(transport_traceable=None))

    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert outcome.build_blocked is True
    assert outcome.block_reasons == ("required_dimension_provider_invalid",)
    assert outcome.qualification_input is None
    assert outcome.qualification_result is None
    assert calls == []


@pytest.mark.parametrize(
    "dimension, value",
    [
        ("identifiable", None),
        ("taxonomy_stable", "True"),
        ("provenance_satisfied", 1),
        ("semantic_assignment_traceable", object()),
    ],
)
def test_non_bool_f4_dimension_is_blocked_without_calling_the_evaluator(
    monkeypatch, dimension, value
):
    calls = []
    monkeypatch.setattr(
        evidence_transport,
        "evaluate_evidence_qualification",
        lambda *args, **kwargs: calls.append(args),
    )

    outcome = build_final_qualification(_normalization(**{dimension: value}))

    assert outcome.status is FinalQualificationStatus.BLOCKED
    assert outcome.build_blocked is True
    assert outcome.block_reasons == ("required_dimension_provider_invalid",)
    assert outcome.qualification_result is None
    assert calls == []
