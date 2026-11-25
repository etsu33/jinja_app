"""Evidence Foundation PR-F5: normalized_evidence v1 transport contract。

このモジュールはDB非依存のdomain layerである。ORM・現在時刻・外部API・LLM・
randomへ一切触れず、値だけを扱う。Foundation DB stateからnormalized_evidenceを
組み立てる責務は ``temples.services.evidence_transport`` に置く。

ここが持つのは3つだけ:

* normalized_evidence v1 immutable runtime types（Django modelは作らない）
* canonical primitive serializer（date/datetimeのcanonical表現を含む）
* pure Transport Integrity predicate と、そのstable issue code契約

Mother Ship contractのcamelCase（``schemaVersion`` / ``canonicalKey`` /
``assignmentRef`` 等）は、wire表現であるserialized payloadのkeyとしてそのまま
保持し、Python attribute側だけをPR-F1と同じ方針でsnake_caseへ1:1変換している
（意味・数・順序は変更していない）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, Mapping, Sequence, Tuple

# --------------------------------------------------------------------------
# schema version / model type identity
# --------------------------------------------------------------------------

TRANSPORT_SCHEMA_VERSION = "v1"
SUPPORTED_TRANSPORT_SCHEMA_VERSIONS = frozenset({TRANSPORT_SCHEMA_VERSION})

# Sourceのtypeは単一。Assignment/Fact typeはPR-F4のdomain正本
# （temples.domain.evidence_link）をそのまま利用する。
SHRINE_KNOWLEDGE_SOURCE = "ShrineKnowledgeSource"


# --------------------------------------------------------------------------
# stable transport issue codes
# --------------------------------------------------------------------------

UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
MISSING_REQUIRED_FIELD = "missing_required_field"
UNEXPECTED_FIELD = "unexpected_field"
INVALID_FIELD_TYPE = "invalid_field_type"
ASSIGNMENT_IDENTITY_MISMATCH = "assignment_identity_mismatch"
ASSIGNMENT_STATE_MISMATCH = "assignment_state_mismatch"
LINK_SET_MISMATCH = "link_set_mismatch"
LINK_ORDER_MISMATCH = "link_order_mismatch"
ASSIGNMENT_REF_MISMATCH = "assignment_ref_mismatch"
FACT_IDENTITY_MISMATCH = "fact_identity_mismatch"
CROSS_SHRINE = "cross_shrine"
RATIONALE_MISMATCH = "rationale_mismatch"
FACT_PAYLOAD_MISMATCH = "fact_payload_mismatch"
FACT_METADATA_MISMATCH = "fact_metadata_mismatch"
SOURCE_SET_MISMATCH = "source_set_mismatch"
SOURCE_ORDER_MISMATCH = "source_order_mismatch"
SOURCE_PAYLOAD_MISMATCH = "source_payload_mismatch"
VALUE_COERCION_DETECTED = "value_coercion_detected"

#: Transport Integrityが返しうるissue codeのstable contract。
TRANSPORT_ISSUE_CODES: Tuple[str, ...] = (
    UNSUPPORTED_SCHEMA_VERSION,
    MISSING_REQUIRED_FIELD,
    UNEXPECTED_FIELD,
    INVALID_FIELD_TYPE,
    ASSIGNMENT_IDENTITY_MISMATCH,
    ASSIGNMENT_STATE_MISMATCH,
    LINK_SET_MISMATCH,
    LINK_ORDER_MISMATCH,
    ASSIGNMENT_REF_MISMATCH,
    FACT_IDENTITY_MISMATCH,
    CROSS_SHRINE,
    RATIONALE_MISMATCH,
    FACT_PAYLOAD_MISMATCH,
    FACT_METADATA_MISMATCH,
    SOURCE_SET_MISMATCH,
    SOURCE_ORDER_MISMATCH,
    SOURCE_PAYLOAD_MISMATCH,
    VALUE_COERCION_DETECTED,
)


class TransportSerializationError(ValueError):
    """canonical serializationがfail-closedすべき入力を受け取った場合に送出する。

    naive datetime等はここで例外にし、呼び出し側（F5 orchestration）が
    BUILD BLOCKへ変換する。Normalizerが値を補正することはない。
    """


# --------------------------------------------------------------------------
# canonical date / datetime serialization
# --------------------------------------------------------------------------


def canonical_datetime(value: Any) -> str | None:
    """timezone-aware datetimeをUTC ``YYYY-MM-DDTHH:MM:SS.ffffffZ`` へ変換する。

    - ``None`` はそのまま ``None``（persisted nullを維持する）。
    - naive datetimeは補完せずfail-closed（``TransportSerializationError``）。
    - microsecondは常に6桁固定。
    """

    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TransportSerializationError(f"invalid_transport_datetime: {value!r} is not a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise TransportSerializationError(
            f"invalid_transport_datetime: {value!r} is a naive datetime"
        )
    utc_value = value.astimezone(timezone.utc)
    return (
        f"{utc_value.year:04d}-{utc_value.month:02d}-{utc_value.day:02d}"
        f"T{utc_value.hour:02d}:{utc_value.minute:02d}:{utc_value.second:02d}"
        f".{utc_value.microsecond:06d}Z"
    )


def canonical_date(value: Any) -> str | None:
    """dateを ``YYYY-MM-DD`` へ変換する。``None`` はそのまま維持する。"""

    if value is None:
        return None
    if isinstance(value, datetime) or not isinstance(value, date):
        raise TransportSerializationError(f"invalid_transport_date: {value!r} is not a date")
    return f"{value.year:04d}-{value.month:02d}-{value.day:02d}"


# --------------------------------------------------------------------------
# normalized_evidence v1 immutable runtime types
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalizedTaxonomyV1:
    namespace: str
    taxonomy_version: str


@dataclass(frozen=True)
class NormalizedProvenanceV1:
    producer: str
    mechanism: str
    assigned_at: str | None


@dataclass(frozen=True)
class NormalizedAssignmentRefV1:
    """EvidenceLinkが指すAssignmentのtyped identity（model type + persistent PK）。"""

    type: str
    id: int


@dataclass(frozen=True)
class NormalizedAssignmentV1:
    type: str
    id: int
    shrine_id: int
    canonical_key: str
    taxonomy: NormalizedTaxonomyV1
    lifecycle: str
    provenance: NormalizedProvenanceV1


@dataclass(frozen=True)
class NormalizedSourceV1:
    id: int
    source_type: str
    title: str
    publisher: str
    url: str
    bibliography: str
    accessed_at: str | None
    verified_at: str | None
    verification_status: str
    confidence: str
    language: str
    type: str = SHRINE_KNOWLEDGE_SOURCE


@dataclass(frozen=True)
class NormalizedShrineHistoryPayloadV1:
    history_type: str
    title: str
    content: str
    period_text: str
    event_date: str | None


@dataclass(frozen=True)
class NormalizedShrineDeityPayloadV1:
    """Mother Ship Design Gate訂正により、v1 payloadは3項目のclosed schema。

    ``aliases`` は ``ShrineDeity`` に対応する永続fieldが存在しないため、
    v1 transportでは運ばない（推論・空値生成・他modelからの流用はしない）。
    """

    display_name: str
    canonical_name: str
    role: str


@dataclass(frozen=True)
class NormalizedFactV1:
    type: str
    id: int
    shrine_id: int
    verification_status: str
    confidence: str
    verified_at: str | None
    payload: NormalizedShrineHistoryPayloadV1 | NormalizedShrineDeityPayloadV1
    sources: Tuple[NormalizedSourceV1, ...]


@dataclass(frozen=True)
class NormalizedEvidenceLinkV1:
    id: int
    assignment_ref: NormalizedAssignmentRefV1
    rationale: str
    fact: NormalizedFactV1


@dataclass(frozen=True)
class NormalizedEvidenceV1:
    assignment: NormalizedAssignmentV1
    evidence_links: Tuple[NormalizedEvidenceLinkV1, ...]
    schema_version: str = TRANSPORT_SCHEMA_VERSION


# --------------------------------------------------------------------------
# deterministic primitive serializer
# --------------------------------------------------------------------------


def _serialize_source(source: NormalizedSourceV1) -> Dict[str, Any]:
    return {
        "type": source.type,
        "id": source.id,
        "sourceType": source.source_type,
        "title": source.title,
        "publisher": source.publisher,
        "url": source.url,
        "bibliography": source.bibliography,
        "accessedAt": source.accessed_at,
        "verifiedAt": source.verified_at,
        "verificationStatus": source.verification_status,
        "confidence": source.confidence,
        "language": source.language,
    }


def _serialize_payload(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, NormalizedShrineHistoryPayloadV1):
        return {
            "historyType": payload.history_type,
            "title": payload.title,
            "content": payload.content,
            "periodText": payload.period_text,
            "eventDate": payload.event_date,
        }
    if isinstance(payload, NormalizedShrineDeityPayloadV1):
        return {
            "displayName": payload.display_name,
            "canonicalName": payload.canonical_name,
            "role": payload.role,
        }
    raise TransportSerializationError(f"unsupported_transport_payload: {type(payload)!r}")


def _serialize_fact(fact: NormalizedFactV1) -> Dict[str, Any]:
    return {
        "type": fact.type,
        "id": fact.id,
        "shrineId": fact.shrine_id,
        "verificationStatus": fact.verification_status,
        "confidence": fact.confidence,
        "verifiedAt": fact.verified_at,
        "payload": _serialize_payload(fact.payload),
        "sources": [_serialize_source(source) for source in fact.sources],
    }


def _serialize_link(link: NormalizedEvidenceLinkV1) -> Dict[str, Any]:
    return {
        "id": link.id,
        "assignmentRef": {
            "type": link.assignment_ref.type,
            "id": link.assignment_ref.id,
        },
        "rationale": link.rationale,
        "fact": _serialize_fact(link.fact),
    }


def serialize_normalized_evidence(evidence: NormalizedEvidenceV1) -> Dict[str, Any]:
    """normalized_evidence v1をdeterministic primitive payloadへ変換する。

    同じ入力に対して常に同じ出力（key順序も含む）を返す。現在時刻・random・
    外部stateへは依存しない。
    """

    assignment = evidence.assignment
    return {
        "schemaVersion": evidence.schema_version,
        "assignment": {
            "type": assignment.type,
            "id": assignment.id,
            "shrineId": assignment.shrine_id,
            "canonicalKey": assignment.canonical_key,
            "taxonomy": {
                "namespace": assignment.taxonomy.namespace,
                "taxonomyVersion": assignment.taxonomy.taxonomy_version,
            },
            "lifecycle": assignment.lifecycle,
            "provenance": {
                "producer": assignment.provenance.producer,
                "mechanism": assignment.provenance.mechanism,
                "assignedAt": assignment.provenance.assigned_at,
            },
        },
        "evidenceLinks": [_serialize_link(link) for link in evidence.evidence_links],
    }


# --------------------------------------------------------------------------
# closed schema definition（schemaVersion="v1"を名乗るpayload用）
# --------------------------------------------------------------------------

_TEXT = "text"
_IDENT = "ident"
_OBJECT = "object"
_ARRAY = "array"

_TOP_FIELDS = {
    "schemaVersion": _TEXT,
    "assignment": _OBJECT,
    "evidenceLinks": _ARRAY,
}
_ASSIGNMENT_FIELDS = {
    "type": _TEXT,
    "id": _IDENT,
    "shrineId": _IDENT,
    "canonicalKey": _TEXT,
    "taxonomy": _OBJECT,
    "lifecycle": _TEXT,
    "provenance": _OBJECT,
}
_TAXONOMY_FIELDS = {"namespace": _TEXT, "taxonomyVersion": _TEXT}
_PROVENANCE_FIELDS = {"producer": _TEXT, "mechanism": _TEXT, "assignedAt": _TEXT}
_ASSIGNMENT_REF_FIELDS = {"type": _TEXT, "id": _IDENT}
_LINK_FIELDS = {
    "id": _IDENT,
    "assignmentRef": _OBJECT,
    "rationale": _TEXT,
    "fact": _OBJECT,
}
_FACT_FIELDS = {
    "type": _TEXT,
    "id": _IDENT,
    "shrineId": _IDENT,
    "verificationStatus": _TEXT,
    "confidence": _TEXT,
    "verifiedAt": _TEXT,
    "payload": _OBJECT,
    "sources": _ARRAY,
}
_HISTORY_PAYLOAD_FIELDS = {
    "historyType": _TEXT,
    "title": _TEXT,
    "content": _TEXT,
    "periodText": _TEXT,
    "eventDate": _TEXT,
}
_DEITY_PAYLOAD_FIELDS = {
    "displayName": _TEXT,
    "canonicalName": _TEXT,
    "role": _TEXT,
}
_SOURCE_FIELDS = {
    "type": _TEXT,
    "id": _IDENT,
    "sourceType": _TEXT,
    "title": _TEXT,
    "publisher": _TEXT,
    "url": _TEXT,
    "bibliography": _TEXT,
    "accessedAt": _TEXT,
    "verifiedAt": _TEXT,
    "verificationStatus": _TEXT,
    "confidence": _TEXT,
    "language": _TEXT,
}

_PAYLOAD_FIELDS_BY_FACT_TYPE = {
    "ShrineHistory": _HISTORY_PAYLOAD_FIELDS,
    "ShrineDeity": _DEITY_PAYLOAD_FIELDS,
}


# --------------------------------------------------------------------------
# Transport Integrity predicate
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TransportIntegrityIssue:
    code: str
    path: str


@dataclass(frozen=True)
class TransportIntegrityResult:
    transport_traceable: bool
    issues: Tuple[TransportIntegrityIssue, ...]

    @property
    def codes(self) -> Tuple[str, ...]:
        return tuple(issue.code for issue in self.issues)


_MISSING = object()


class _IssueCollector:
    """issue順序をdeterministicに保ちながら重複を排除する内部collector。"""

    def __init__(self) -> None:
        self._issues: list[TransportIntegrityIssue] = []
        self._seen: set[Tuple[str, str]] = set()

    def add(self, code: str, path: str) -> None:
        key = (code, path)
        if key in self._seen:
            return
        self._seen.add(key)
        self._issues.append(TransportIntegrityIssue(code=code, path=path))

    def result(self) -> TransportIntegrityResult:
        issues = tuple(self._issues)
        return TransportIntegrityResult(transport_traceable=not issues, issues=issues)


def _is_ident(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _matches_kind(value: Any, kind: str) -> bool:
    if kind == _TEXT:
        # blank ("") と null は区別して運ぶため、どちらもtype的にはvalid。
        # ""/null間のcoercionはcomparison側でvalue_coercion_detectedとして検出する。
        return value is None or isinstance(value, str)
    if kind == _IDENT:
        return _is_ident(value)
    if kind == _OBJECT:
        return isinstance(value, Mapping)
    if kind == _ARRAY:
        return isinstance(value, (list, tuple))
    return False


def _validate_object(
    candidate: Any,
    fields: Mapping[str, str],
    path: str,
    issues: _IssueCollector,
) -> bool:
    """closed schemaとしてobject 1件を検証する。構造が使える場合のみTrue。"""

    if not isinstance(candidate, Mapping):
        issues.add(INVALID_FIELD_TYPE, path)
        return False
    for name, kind in fields.items():
        if name not in candidate:
            issues.add(MISSING_REQUIRED_FIELD, f"{path}.{name}")
            continue
        if not _matches_kind(candidate[name], kind):
            issues.add(INVALID_FIELD_TYPE, f"{path}.{name}")
    for name in candidate:
        if name not in fields:
            issues.add(UNEXPECTED_FIELD, f"{path}.{name}")
    return True


def _validate_source(candidate: Any, path: str, issues: _IssueCollector) -> None:
    _validate_object(candidate, _SOURCE_FIELDS, path, issues)


def _validate_fact(candidate: Any, path: str, issues: _IssueCollector) -> None:
    if not _validate_object(candidate, _FACT_FIELDS, path, issues):
        return
    payload_fields = _PAYLOAD_FIELDS_BY_FACT_TYPE.get(candidate.get("type"))
    payload = candidate.get("payload", _MISSING)
    if payload_fields is not None and payload is not _MISSING:
        _validate_object(payload, payload_fields, f"{path}.payload", issues)
    sources = candidate.get("sources", _MISSING)
    if isinstance(sources, (list, tuple)):
        for index, source in enumerate(sources):
            _validate_source(source, f"{path}.sources[{index}]", issues)


def _validate_link(candidate: Any, path: str, issues: _IssueCollector) -> None:
    if not _validate_object(candidate, _LINK_FIELDS, path, issues):
        return
    assignment_ref = candidate.get("assignmentRef", _MISSING)
    if assignment_ref is not _MISSING:
        _validate_object(
            assignment_ref, _ASSIGNMENT_REF_FIELDS, f"{path}.assignmentRef", issues
        )
    fact = candidate.get("fact", _MISSING)
    if fact is not _MISSING:
        _validate_fact(fact, f"{path}.fact", issues)


def _validate_structure(candidate: Mapping[str, Any], issues: _IssueCollector) -> None:
    _validate_object(candidate, _TOP_FIELDS, "$", issues)
    assignment = candidate.get("assignment", _MISSING)
    if assignment is not _MISSING:
        if _validate_object(assignment, _ASSIGNMENT_FIELDS, "$.assignment", issues):
            taxonomy = assignment.get("taxonomy", _MISSING)
            if taxonomy is not _MISSING:
                _validate_object(taxonomy, _TAXONOMY_FIELDS, "$.assignment.taxonomy", issues)
            provenance = assignment.get("provenance", _MISSING)
            if provenance is not _MISSING:
                _validate_object(
                    provenance, _PROVENANCE_FIELDS, "$.assignment.provenance", issues
                )
    links = candidate.get("evidenceLinks", _MISSING)
    if isinstance(links, (list, tuple)):
        for index, link in enumerate(links):
            _validate_link(link, f"$.evidenceLinks[{index}]", issues)


def _is_blank_null_coercion(expected: Any, actual: Any) -> bool:
    return {type(expected), type(actual)} == {str, type(None)} and (
        expected == "" or actual == ""
    )


def _compare_value(
    expected: Any,
    actual: Any,
    code: str,
    path: str,
    issues: _IssueCollector,
) -> None:
    if actual is _MISSING or expected is _MISSING:
        return
    if expected == actual and type(expected) is type(actual):
        return
    if _is_blank_null_coercion(expected, actual):
        issues.add(VALUE_COERCION_DETECTED, path)
        return
    issues.add(code, path)


def _compare_fields(
    expected: Mapping[str, Any],
    actual: Any,
    names: Sequence[str],
    code: str,
    path: str,
    issues: _IssueCollector,
) -> None:
    if not isinstance(actual, Mapping):
        return
    for name in names:
        _compare_value(
            expected.get(name, _MISSING),
            actual.get(name, _MISSING),
            code,
            f"{path}.{name}",
            issues,
        )


def _compare_assignment(
    expected: Any, actual: Any, issues: _IssueCollector
) -> None:
    if not isinstance(expected, Mapping):
        return
    path = "$.assignment"
    _compare_fields(expected, actual, ("type", "id"), ASSIGNMENT_IDENTITY_MISMATCH, path, issues)
    _compare_fields(
        expected,
        actual,
        ("shrineId", "canonicalKey", "lifecycle"),
        ASSIGNMENT_STATE_MISMATCH,
        path,
        issues,
    )
    if not isinstance(actual, Mapping):
        return
    for nested, names in (
        ("taxonomy", ("namespace", "taxonomyVersion")),
        ("provenance", ("producer", "mechanism", "assignedAt")),
    ):
        expected_nested = expected.get(nested)
        actual_nested = actual.get(nested, _MISSING)
        if isinstance(expected_nested, Mapping) and actual_nested is not _MISSING:
            _compare_fields(
                expected_nested,
                actual_nested,
                names,
                ASSIGNMENT_STATE_MISMATCH,
                f"{path}.{nested}",
                issues,
            )


def _ids_of(items: Sequence[Any]) -> Tuple[Any, ...]:
    return tuple(item.get("id") if isinstance(item, Mapping) else _MISSING for item in items)


def _compare_ordering_and_set(
    expected_items: Sequence[Any],
    actual_items: Sequence[Any],
    set_code: str,
    order_code: str,
    path: str,
    issues: _IssueCollector,
) -> None:
    expected_ids = _ids_of(expected_items)
    actual_ids = _ids_of(actual_items)
    if sorted(map(repr, expected_ids)) != sorted(map(repr, actual_ids)):
        issues.add(set_code, path)
    comparable = [value for value in actual_ids if _is_ident(value)]
    if len(comparable) == len(actual_ids) and list(actual_ids) != sorted(comparable):
        issues.add(order_code, path)


def _compare_sources(
    expected_sources: Sequence[Any],
    actual_sources: Any,
    path: str,
    issues: _IssueCollector,
) -> None:
    if not isinstance(actual_sources, (list, tuple)):
        return
    _compare_ordering_and_set(
        expected_sources, actual_sources, SOURCE_SET_MISMATCH, SOURCE_ORDER_MISMATCH, path, issues
    )
    expected_by_id = {
        source.get("id"): source for source in expected_sources if isinstance(source, Mapping)
    }
    for index, actual_source in enumerate(actual_sources):
        if not isinstance(actual_source, Mapping):
            continue
        expected_source = expected_by_id.get(actual_source.get("id"))
        if expected_source is None:
            continue
        _compare_fields(
            expected_source,
            actual_source,
            tuple(_SOURCE_FIELDS),
            SOURCE_PAYLOAD_MISMATCH,
            f"{path}[{index}]",
            issues,
        )


def _compare_fact(
    expected_fact: Mapping[str, Any],
    actual_fact: Any,
    assignment_shrine_id: Any,
    path: str,
    issues: _IssueCollector,
) -> None:
    if not isinstance(actual_fact, Mapping):
        return
    _compare_fields(
        expected_fact, actual_fact, ("type", "id"), FACT_IDENTITY_MISMATCH, path, issues
    )
    _compare_fields(
        expected_fact,
        actual_fact,
        ("shrineId", "verificationStatus", "confidence", "verifiedAt"),
        FACT_METADATA_MISMATCH,
        path,
        issues,
    )
    fact_shrine_id = actual_fact.get("shrineId", _MISSING)
    if (
        fact_shrine_id is not _MISSING
        and assignment_shrine_id is not _MISSING
        and fact_shrine_id != assignment_shrine_id
    ):
        issues.add(CROSS_SHRINE, f"{path}.shrineId")
    expected_payload = expected_fact.get("payload")
    actual_payload = actual_fact.get("payload", _MISSING)
    if isinstance(expected_payload, Mapping) and isinstance(actual_payload, Mapping):
        names = tuple(expected_payload) + tuple(
            name for name in actual_payload if name not in expected_payload
        )
        _compare_fields(
            expected_payload,
            actual_payload,
            names,
            FACT_PAYLOAD_MISMATCH,
            f"{path}.payload",
            issues,
        )
    expected_sources = expected_fact.get("sources")
    if isinstance(expected_sources, (list, tuple)):
        _compare_sources(
            expected_sources, actual_fact.get("sources", _MISSING), f"{path}.sources", issues
        )


def _compare_link(
    expected_link: Mapping[str, Any],
    actual_link: Mapping[str, Any],
    assignment: Any,
    path: str,
    issues: _IssueCollector,
) -> None:
    _compare_value(
        expected_link.get("rationale", _MISSING),
        actual_link.get("rationale", _MISSING),
        RATIONALE_MISMATCH,
        f"{path}.rationale",
        issues,
    )
    actual_ref = actual_link.get("assignmentRef", _MISSING)
    if isinstance(actual_ref, Mapping) and isinstance(assignment, Mapping):
        for name in ("type", "id"):
            if actual_ref.get(name, _MISSING) != assignment.get(name, _MISSING):
                issues.add(ASSIGNMENT_REF_MISMATCH, f"{path}.assignmentRef.{name}")
    expected_fact = expected_link.get("fact")
    if isinstance(expected_fact, Mapping):
        assignment_shrine_id = (
            assignment.get("shrineId", _MISSING) if isinstance(assignment, Mapping) else _MISSING
        )
        _compare_fact(
            expected_fact,
            actual_link.get("fact", _MISSING),
            assignment_shrine_id,
            f"{path}.fact",
            issues,
        )


def _compare_links(
    expected_links: Any,
    actual_links: Any,
    assignment: Any,
    issues: _IssueCollector,
) -> None:
    if not isinstance(expected_links, (list, tuple)) or not isinstance(
        actual_links, (list, tuple)
    ):
        return
    _compare_ordering_and_set(
        expected_links,
        actual_links,
        LINK_SET_MISMATCH,
        LINK_ORDER_MISMATCH,
        "$.evidenceLinks",
        issues,
    )
    expected_by_id = {
        link.get("id"): link for link in expected_links if isinstance(link, Mapping)
    }
    for index, actual_link in enumerate(actual_links):
        if not isinstance(actual_link, Mapping):
            continue
        expected_link = expected_by_id.get(actual_link.get("id"))
        if expected_link is None:
            continue
        _compare_link(
            expected_link, actual_link, assignment, f"$.evidenceLinks[{index}]", issues
        )


def verify_transport_integrity(
    *,
    authoritative: Mapping[str, Any],
    candidate: Any,
) -> TransportIntegrityResult:
    """authoritative expectationとtransport candidateを照合する。

    ``authoritative`` は authoritative snapshotから **Normalizerを経由せずに**
    生成されたprimitive expectation payloadである（生成責務は
    ``temples.services.evidence_transport.build_authoritative_expectation``）。
    Normalizer outputを両辺に渡す自己比較は、Normalier自身の欠落・改変を検出
    できないため契約違反とする。

    pure deterministic function。DB・ORM・外部API・現在時刻へは触れない。

    ``transport_traceable`` は「issueが0件であること」と同値であり、0 EvidenceLink
    （``evidenceLinks == []``）はTransport failureではない。
    """

    if not isinstance(authoritative, Mapping):
        raise TypeError(
            "authoritative expectation must be a primitive Mapping built from the "
            "authoritative snapshot, not a normalizer output object"
        )

    issues = _IssueCollector()
    if not isinstance(candidate, Mapping):
        issues.add(INVALID_FIELD_TYPE, "$")
        return issues.result()

    schema_version = candidate.get("schemaVersion", _MISSING)
    if schema_version is _MISSING or schema_version not in SUPPORTED_TRANSPORT_SCHEMA_VERSIONS:
        issues.add(UNSUPPORTED_SCHEMA_VERSION, "$.schemaVersion")
        return issues.result()

    _validate_structure(candidate, issues)

    _compare_value(
        authoritative.get("schemaVersion", _MISSING),
        schema_version,
        UNSUPPORTED_SCHEMA_VERSION,
        "$.schemaVersion",
        issues,
    )
    _compare_assignment(
        authoritative.get("assignment", _MISSING), candidate.get("assignment", _MISSING), issues
    )
    _compare_links(
        authoritative.get("evidenceLinks", _MISSING),
        candidate.get("evidenceLinks", _MISSING),
        candidate.get("assignment", _MISSING),
        issues,
    )
    return issues.result()


__all__ = [
    "TRANSPORT_SCHEMA_VERSION",
    "SUPPORTED_TRANSPORT_SCHEMA_VERSIONS",
    "SHRINE_KNOWLEDGE_SOURCE",
    "TRANSPORT_ISSUE_CODES",
    "UNSUPPORTED_SCHEMA_VERSION",
    "MISSING_REQUIRED_FIELD",
    "UNEXPECTED_FIELD",
    "INVALID_FIELD_TYPE",
    "ASSIGNMENT_IDENTITY_MISMATCH",
    "ASSIGNMENT_STATE_MISMATCH",
    "LINK_SET_MISMATCH",
    "LINK_ORDER_MISMATCH",
    "ASSIGNMENT_REF_MISMATCH",
    "FACT_IDENTITY_MISMATCH",
    "CROSS_SHRINE",
    "RATIONALE_MISMATCH",
    "FACT_PAYLOAD_MISMATCH",
    "FACT_METADATA_MISMATCH",
    "SOURCE_SET_MISMATCH",
    "SOURCE_ORDER_MISMATCH",
    "SOURCE_PAYLOAD_MISMATCH",
    "VALUE_COERCION_DETECTED",
    "TransportSerializationError",
    "TransportIntegrityIssue",
    "TransportIntegrityResult",
    "NormalizedTaxonomyV1",
    "NormalizedProvenanceV1",
    "NormalizedAssignmentRefV1",
    "NormalizedAssignmentV1",
    "NormalizedSourceV1",
    "NormalizedShrineHistoryPayloadV1",
    "NormalizedShrineDeityPayloadV1",
    "NormalizedFactV1",
    "NormalizedEvidenceLinkV1",
    "NormalizedEvidenceV1",
    "canonical_date",
    "canonical_datetime",
    "serialize_normalized_evidence",
    "verify_transport_integrity",
]
