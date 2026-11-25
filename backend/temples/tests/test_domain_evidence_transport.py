"""Evidence Foundation PR-F5: normalized_evidence v1 schema + Transport Integrity。

pure domain test。DB・ORM・現在時刻・外部APIへ依存しない。
"""

from __future__ import annotations

import copy
import dataclasses
from datetime import date, datetime, timedelta, timezone

import pytest

from temples.domain.evidence_link import (
    GORIYAKU_ASSIGNMENT,
    HISTORY_THEME_ASSIGNMENT,
    SHRINE_DEITY,
    SHRINE_HISTORY,
)
from temples.domain.evidence_transport import (
    ASSIGNMENT_IDENTITY_MISMATCH,
    ASSIGNMENT_REF_MISMATCH,
    ASSIGNMENT_STATE_MISMATCH,
    CROSS_SHRINE,
    FACT_IDENTITY_MISMATCH,
    FACT_METADATA_MISMATCH,
    FACT_PAYLOAD_MISMATCH,
    INVALID_FIELD_TYPE,
    LINK_ORDER_MISMATCH,
    LINK_SET_MISMATCH,
    MISSING_REQUIRED_FIELD,
    RATIONALE_MISMATCH,
    SHRINE_KNOWLEDGE_SOURCE,
    SOURCE_ORDER_MISMATCH,
    SOURCE_PAYLOAD_MISMATCH,
    SOURCE_SET_MISMATCH,
    TRANSPORT_ISSUE_CODES,
    TRANSPORT_SCHEMA_VERSION,
    UNEXPECTED_FIELD,
    UNSUPPORTED_SCHEMA_VERSION,
    VALUE_COERCION_DETECTED,
    NormalizedAssignmentRefV1,
    NormalizedAssignmentV1,
    NormalizedEvidenceLinkV1,
    NormalizedEvidenceV1,
    NormalizedFactV1,
    NormalizedProvenanceV1,
    NormalizedShrineDeityPayloadV1,
    NormalizedShrineHistoryPayloadV1,
    NormalizedSourceV1,
    NormalizedTaxonomyV1,
    TransportSerializationError,
    canonical_date,
    canonical_datetime,
    serialize_normalized_evidence,
    verify_transport_integrity,
)

_ASSIGNED_AT = datetime(2026, 1, 1, 9, 0, 0, 123456, tzinfo=timezone(timedelta(hours=9)))
_VERIFIED_AT = datetime(2026, 2, 3, 4, 5, 6, 7, tzinfo=timezone.utc)


def _source(source_id: int, *, publisher: str = "", accessed_at=None) -> NormalizedSourceV1:
    return NormalizedSourceV1(
        id=source_id,
        source_type="shrine_official",
        title=f"出典{source_id}",
        publisher=publisher,
        url="",
        bibliography="",
        accessed_at=canonical_date(accessed_at),
        verified_at=canonical_datetime(_VERIFIED_AT),
        verification_status="reviewed",
        confidence="high",
        language="ja",
    )


def _history_fact(fact_id: int = 11, shrine_id: int = 1) -> NormalizedFactV1:
    return NormalizedFactV1(
        type=SHRINE_HISTORY,
        id=fact_id,
        shrine_id=shrine_id,
        verification_status="reviewed",
        confidence="high",
        verified_at=canonical_datetime(_VERIFIED_AT),
        payload=NormalizedShrineHistoryPayloadV1(
            history_type="official_origin",
            title="由緒",
            content="根拠となる由緒。",
            period_text="",
            event_date=canonical_date(date(1600, 3, 4)),
        ),
        sources=(_source(21), _source(22, publisher="出版社")),
    )


def _deity_fact(fact_id: int = 12, shrine_id: int = 1) -> NormalizedFactV1:
    return NormalizedFactV1(
        type=SHRINE_DEITY,
        id=fact_id,
        shrine_id=shrine_id,
        verification_status="source_confirmed",
        confidence="",
        verified_at=None,
        payload=NormalizedShrineDeityPayloadV1(
            display_name="天照大神",
            canonical_name="",
            role="primary",
        ),
        sources=(_source(23),),
    )


def _assignment(assignment_id: int = 5, shrine_id: int = 1) -> NormalizedAssignmentV1:
    return NormalizedAssignmentV1(
        type=HISTORY_THEME_ASSIGNMENT,
        id=assignment_id,
        shrine_id=shrine_id,
        canonical_key="history_theme:restart",
        taxonomy=NormalizedTaxonomyV1(namespace="history_theme", taxonomy_version="v1"),
        lifecycle="ACTIVE",
        provenance=NormalizedProvenanceV1(
            producer="admin",
            mechanism="manual_review",
            assigned_at=canonical_datetime(_ASSIGNED_AT),
        ),
    )


def _evidence(*, links=None, assignment=None) -> NormalizedEvidenceV1:
    assignment = assignment or _assignment()
    ref = NormalizedAssignmentRefV1(type=assignment.type, id=assignment.id)
    if links is None:
        links = (
            NormalizedEvidenceLinkV1(
                id=101, assignment_ref=ref, rationale="由緒が再出発を裏付ける。",
                fact=_history_fact(),
            ),
            NormalizedEvidenceLinkV1(
                id=102, assignment_ref=ref, rationale="祭神が再出発を裏付ける。",
                fact=_deity_fact(),
            ),
        )
    return NormalizedEvidenceV1(assignment=assignment, evidence_links=tuple(links))


def _candidate(evidence: NormalizedEvidenceV1):
    return copy.deepcopy(serialize_normalized_evidence(evidence))


def _expected(evidence: NormalizedEvidenceV1):
    """authoritative expectation（primitive payload）。

    serviceのofficial pathではNormalizerを経由しない独立経路で生成されるが、
    predicate単体testでは同じprimitive形状であれば十分なので、canonical
    serializerの出力をexpectationとして与える。
    """

    return serialize_normalized_evidence(evidence)


# --------------------------------------------------------------------------
# normalized_evidence v1 schema
# --------------------------------------------------------------------------


def test_normalized_types_are_immutable_frozen_dataclasses():
    evidence = _evidence()
    for instance in (
        evidence,
        evidence.assignment,
        evidence.assignment.taxonomy,
        evidence.assignment.provenance,
        evidence.evidence_links[0],
        evidence.evidence_links[0].assignment_ref,
        evidence.evidence_links[0].fact,
        evidence.evidence_links[0].fact.payload,
        evidence.evidence_links[0].fact.sources[0],
    ):
        assert dataclasses.is_dataclass(instance)
        with pytest.raises(dataclasses.FrozenInstanceError):
            instance.id = 999


def test_schema_version_is_v1():
    assert TRANSPORT_SCHEMA_VERSION == "v1"
    assert _candidate(_evidence())["schemaVersion"] == "v1"


def test_history_transport_shape():
    payload = _candidate(_evidence())["evidenceLinks"][0]["fact"]["payload"]
    assert tuple(payload) == ("historyType", "title", "content", "periodText", "eventDate")


def test_deity_transport_shape_has_no_aliases():
    payload = _candidate(_evidence())["evidenceLinks"][1]["fact"]["payload"]
    assert tuple(payload) == ("displayName", "canonicalName", "role")
    assert "aliases" not in payload


def test_source_transport_shape():
    source = _candidate(_evidence())["evidenceLinks"][0]["fact"]["sources"][0]
    assert tuple(source) == (
        "type",
        "id",
        "sourceType",
        "title",
        "publisher",
        "url",
        "bibliography",
        "accessedAt",
        "verifiedAt",
        "verificationStatus",
        "confidence",
        "language",
    )
    assert source["type"] == SHRINE_KNOWLEDGE_SOURCE


def test_typed_identity_is_preserved():
    candidate = _candidate(_evidence())
    assert candidate["assignment"]["type"] == HISTORY_THEME_ASSIGNMENT
    assert candidate["assignment"]["id"] == 5
    assert candidate["evidenceLinks"][0]["fact"]["type"] == SHRINE_HISTORY
    assert candidate["evidenceLinks"][0]["fact"]["id"] == 11
    assert candidate["evidenceLinks"][1]["fact"]["type"] == SHRINE_DEITY
    assert candidate["evidenceLinks"][0]["fact"]["sources"][0]["id"] == 21


def test_assignment_ref_is_preserved_on_every_link():
    candidate = _candidate(_evidence())
    for link in candidate["evidenceLinks"]:
        assert link["assignmentRef"] == {"type": HISTORY_THEME_ASSIGNMENT, "id": 5}


def test_rationale_is_preserved_edge_bound():
    candidate = _candidate(_evidence())
    assert candidate["evidenceLinks"][0]["rationale"] == "由緒が再出発を裏付ける。"
    assert candidate["evidenceLinks"][1]["rationale"] == "祭神が再出発を裏付ける。"


def test_blank_and_null_are_distinguished():
    candidate = _candidate(_evidence())
    source = candidate["evidenceLinks"][0]["fact"]["sources"][0]
    assert source["publisher"] == ""
    assert source["accessedAt"] is None
    assert candidate["evidenceLinks"][0]["fact"]["payload"]["periodText"] == ""
    assert candidate["evidenceLinks"][1]["fact"]["verifiedAt"] is None
    assert candidate["evidenceLinks"][1]["fact"]["payload"]["canonicalName"] == ""


def test_canonical_datetime_is_utc_with_six_digit_microseconds():
    assert canonical_datetime(_ASSIGNED_AT) == "2026-01-01T00:00:00.123456Z"
    assert canonical_datetime(_VERIFIED_AT) == "2026-02-03T04:05:06.000007Z"
    assert canonical_datetime(None) is None


def test_naive_datetime_is_fail_closed():
    with pytest.raises(TransportSerializationError):
        canonical_datetime(datetime(2026, 1, 1, 0, 0, 0))


def test_canonical_date_format():
    assert canonical_date(date(2026, 3, 4)) == "2026-03-04"
    assert canonical_date(None) is None
    with pytest.raises(TransportSerializationError):
        canonical_date(_VERIFIED_AT)


def test_link_and_source_order_is_pk_ascending():
    candidate = _candidate(_evidence())
    assert [link["id"] for link in candidate["evidenceLinks"]] == [101, 102]
    assert [
        source["id"] for source in candidate["evidenceLinks"][0]["fact"]["sources"]
    ] == [21, 22]


def test_serializer_is_deterministic():
    evidence = _evidence()
    first = serialize_normalized_evidence(evidence)
    second = serialize_normalized_evidence(evidence)
    assert first == second
    assert list(first) == list(second)
    assert list(first["assignment"]) == list(second["assignment"])


def test_normalized_payload_carries_no_qualification_or_f4_state():
    forbidden = {
        "qualified",
        "qualificationVersion",
        "unmetDimensions",
        "transportTraceable",
        "identifiable",
        "taxonomyStable",
        "provenanceSatisfied",
        "semanticAssignmentTraceable",
        "createdAt",
        "updatedAt",
        "note",
    }

    def walk(node):
        if isinstance(node, dict):
            assert forbidden.isdisjoint(node), f"forbidden key in {sorted(node)}"
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(_candidate(_evidence()))


def test_transport_issue_codes_are_a_stable_contract():
    assert TRANSPORT_ISSUE_CODES == (
        "unsupported_schema_version",
        "missing_required_field",
        "unexpected_field",
        "invalid_field_type",
        "assignment_identity_mismatch",
        "assignment_state_mismatch",
        "link_set_mismatch",
        "link_order_mismatch",
        "assignment_ref_mismatch",
        "fact_identity_mismatch",
        "cross_shrine",
        "rationale_mismatch",
        "fact_payload_mismatch",
        "fact_metadata_mismatch",
        "source_set_mismatch",
        "source_order_mismatch",
        "source_payload_mismatch",
        "value_coercion_detected",
    )


# --------------------------------------------------------------------------
# Transport Integrity: positive
# --------------------------------------------------------------------------


def test_exact_complete_transport_is_traceable():
    evidence = _evidence()
    result = verify_transport_integrity(
        authoritative=_expected(evidence), candidate=_candidate(evidence)
    )
    assert result.transport_traceable is True
    assert result.issues == ()


def test_zero_evidence_link_is_valid_transport():
    evidence = _evidence(links=())
    result = verify_transport_integrity(
        authoritative=_expected(evidence), candidate=_candidate(evidence)
    )
    assert _candidate(evidence)["evidenceLinks"] == []
    assert result.transport_traceable is True
    assert result.issues == ()


def test_multiple_links_and_sources_exact_transport_is_traceable():
    ref = NormalizedAssignmentRefV1(type=HISTORY_THEME_ASSIGNMENT, id=5)
    evidence = _evidence(
        links=(
            NormalizedEvidenceLinkV1(
                id=101, assignment_ref=ref, rationale="1つ目。", fact=_history_fact()
            ),
            NormalizedEvidenceLinkV1(
                id=102, assignment_ref=ref, rationale="2つ目。", fact=_deity_fact()
            ),
            NormalizedEvidenceLinkV1(
                id=103,
                assignment_ref=ref,
                rationale="3つ目。",
                fact=_history_fact(fact_id=13),
            ),
        )
    )
    result = verify_transport_integrity(
        authoritative=_expected(evidence), candidate=_candidate(evidence)
    )
    assert result.transport_traceable is True


# --------------------------------------------------------------------------
# Transport Integrity: negative（1 contractにつき最低1 case）
# --------------------------------------------------------------------------


def _assert_issue(candidate_mutation, expected_code, *, evidence=None):
    evidence = evidence or _evidence()
    candidate = _candidate(evidence)
    candidate_mutation(candidate)
    result = verify_transport_integrity(authoritative=_expected(evidence), candidate=candidate)
    assert result.transport_traceable is False
    assert expected_code in result.codes, result.codes


def test_unsupported_schema_version():
    _assert_issue(lambda c: c.__setitem__("schemaVersion", "v2"), UNSUPPORTED_SCHEMA_VERSION)


def test_missing_required_field():
    _assert_issue(lambda c: c["assignment"].pop("canonicalKey"), MISSING_REQUIRED_FIELD)


def test_unexpected_field():
    _assert_issue(lambda c: c["assignment"].__setitem__("aliases", []), UNEXPECTED_FIELD)


def test_invalid_field_type():
    _assert_issue(lambda c: c["assignment"].__setitem__("canonicalKey", 123), INVALID_FIELD_TYPE)


def test_assignment_type_mismatch():
    _assert_issue(
        lambda c: c["assignment"].__setitem__("type", GORIYAKU_ASSIGNMENT),
        ASSIGNMENT_IDENTITY_MISMATCH,
    )


def test_assignment_id_mismatch():
    _assert_issue(lambda c: c["assignment"].__setitem__("id", 999), ASSIGNMENT_IDENTITY_MISMATCH)


def test_assignment_state_mismatch():
    _assert_issue(
        lambda c: c["assignment"].__setitem__("lifecycle", "SUPERSEDED"),
        ASSIGNMENT_STATE_MISMATCH,
    )


def test_assignment_taxonomy_state_mismatch():
    _assert_issue(
        lambda c: c["assignment"]["taxonomy"].__setitem__("taxonomyVersion", "v2"),
        ASSIGNMENT_STATE_MISMATCH,
    )


def test_assignment_provenance_state_mismatch():
    _assert_issue(
        lambda c: c["assignment"]["provenance"].__setitem__("producer", "llm"),
        ASSIGNMENT_STATE_MISMATCH,
    )


def test_link_omission():
    _assert_issue(lambda c: c["evidenceLinks"].pop(), LINK_SET_MISMATCH)


def test_link_addition():
    def mutate(candidate):
        extra = copy.deepcopy(candidate["evidenceLinks"][0])
        extra["id"] = 999
        candidate["evidenceLinks"].append(extra)

    _assert_issue(mutate, LINK_SET_MISMATCH)


def test_link_duplicate():
    def mutate(candidate):
        candidate["evidenceLinks"].append(copy.deepcopy(candidate["evidenceLinks"][0]))

    _assert_issue(mutate, LINK_SET_MISMATCH)


def test_link_order_mismatch():
    _assert_issue(lambda c: c["evidenceLinks"].reverse(), LINK_ORDER_MISMATCH)


def test_assignment_ref_mismatch():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["assignmentRef"].__setitem__("id", 999),
        ASSIGNMENT_REF_MISMATCH,
    )


def test_fact_type_mismatch():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"].__setitem__("type", SHRINE_DEITY),
        FACT_IDENTITY_MISMATCH,
    )


def test_fact_id_mismatch():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"].__setitem__("id", 999), FACT_IDENTITY_MISMATCH
    )


def test_cross_shrine_authoritative_graph_is_not_transport_traceable():
    ref = NormalizedAssignmentRefV1(type=HISTORY_THEME_ASSIGNMENT, id=5)
    evidence = _evidence(
        links=(
            NormalizedEvidenceLinkV1(
                id=101,
                assignment_ref=ref,
                rationale="別Shrineのfact。",
                fact=_history_fact(shrine_id=2),
            ),
        )
    )
    result = verify_transport_integrity(
        authoritative=_expected(evidence), candidate=_candidate(evidence)
    )
    assert result.transport_traceable is False
    assert CROSS_SHRINE in result.codes


def test_rationale_mutation():
    _assert_issue(
        lambda c: c["evidenceLinks"][0].__setitem__("rationale", "書き換えた根拠。"),
        RATIONALE_MISMATCH,
    )


def test_fact_payload_mutation():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"]["payload"].__setitem__("title", "改変"),
        FACT_PAYLOAD_MISMATCH,
    )


def test_fact_metadata_mutation():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"].__setitem__("verificationStatus", "draft"),
        FACT_METADATA_MISMATCH,
    )


def test_source_omission():
    _assert_issue(lambda c: c["evidenceLinks"][0]["fact"]["sources"].pop(), SOURCE_SET_MISMATCH)


def test_source_addition():
    def mutate(candidate):
        sources = candidate["evidenceLinks"][0]["fact"]["sources"]
        extra = copy.deepcopy(sources[0])
        extra["id"] = 999
        sources.append(extra)

    _assert_issue(mutate, SOURCE_SET_MISMATCH)


def test_source_duplicate():
    def mutate(candidate):
        sources = candidate["evidenceLinks"][0]["fact"]["sources"]
        sources.append(copy.deepcopy(sources[0]))

    _assert_issue(mutate, SOURCE_SET_MISMATCH)


def test_source_order_mismatch():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"]["sources"].reverse(), SOURCE_ORDER_MISMATCH
    )


def test_source_payload_mutation():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"]["sources"][0].__setitem__("title", "改変"),
        SOURCE_PAYLOAD_MISMATCH,
    )


def test_blank_to_null_coercion_is_detected():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"]["sources"][0].__setitem__("publisher", None),
        VALUE_COERCION_DETECTED,
    )


def test_null_to_blank_coercion_is_detected():
    _assert_issue(
        lambda c: c["evidenceLinks"][0]["fact"]["sources"][0].__setitem__("accessedAt", ""),
        VALUE_COERCION_DETECTED,
    )


def test_transport_traceable_is_equivalent_to_zero_issues():
    evidence = _evidence()
    ok = verify_transport_integrity(
        authoritative=_expected(evidence), candidate=_candidate(evidence)
    )
    assert ok.transport_traceable is (len(ok.issues) == 0)
    broken_candidate = _candidate(evidence)
    broken_candidate["evidenceLinks"][0]["rationale"] = "改変"
    broken = verify_transport_integrity(authoritative=_expected(evidence), candidate=broken_candidate)
    assert broken.transport_traceable is (len(broken.issues) == 0)


def test_issue_order_is_deterministic():
    evidence = _evidence()
    candidate = _candidate(evidence)
    candidate["assignment"]["id"] = 999
    candidate["evidenceLinks"][0]["rationale"] = "改変"
    first = verify_transport_integrity(authoritative=_expected(evidence), candidate=candidate)
    second = verify_transport_integrity(authoritative=_expected(evidence), candidate=candidate)
    assert first.issues == second.issues


def test_authoritative_expectation_must_be_a_primitive_mapping():
    evidence = _evidence()
    with pytest.raises(TypeError):
        verify_transport_integrity(authoritative=evidence, candidate=_candidate(evidence))
