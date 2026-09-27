"""Shrine Knowledge production import foundation.

Shared logic for `export_shrine_knowledge` / `import_shrine_knowledge`
management commands. Neither command, nor this module, ever hardcodes a
numeric Shrine/Source/Deity/History primary key across environments — local
dev, any isolated test DB, and production each have independent, unrelated
auto-increment sequences, so a PK from one is meaningless in another.

Shrine identity resolution deliberately does not repeat the mistake found
and fixed in `temples/migrations/0091_fill_missing_local_shrine_reason_facts.py`
(see `docs/audit/temples-0091-production-remediation.md`): a bare
`Shrine.objects.filter(name_jp=...).first()` silently picks whichever row
`Shrine.Meta.ordering` (`-updated_at`) happens to put first, which is not
necessarily the intended shrine when duplicate-named rows exist. This module
never uses `.first()` on an unordered/ambiguous match; see `resolve_shrine`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from django.db.models import F
from django.utils import timezone
from temples.models import (
    KNOWLEDGE_CONFIDENCE_CHOICES,
    KNOWLEDGE_VERIFICATION_STATUS_CHOICES,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineHistory,
    ShrineKnowledgeSource,
)

# export_shrine_knowledge が出力する version。A-5a では変更しない。
SCHEMA_VERSION = "1.0"
# import 側が受け付ける version（docs/audit/collective-deity-knowledge-seed-v1-1-contract.md §3）。
# 1.0 は従来契約のまま。1.1 は shrine block に optional な `collectives` を追加する。
COLLECTIVE_SCHEMA_VERSION = "1.1"
SUPPORTED_SCHEMA_VERSIONS = (SCHEMA_VERSION, COLLECTIVE_SCHEMA_VERSION)

_VALID_VERIFICATION_STATUSES = {v for v, _ in KNOWLEDGE_VERIFICATION_STATUS_CHOICES}
_VALID_CONFIDENCES = {v for v, _ in KNOWLEDGE_CONFIDENCE_CHOICES} | {""}
_VALID_SOURCE_TYPES = {v for v, _ in ShrineKnowledgeSource.SOURCE_TYPE_CHOICES}
_VALID_ROLES = {v for v, _ in ShrineDeity.ROLE_CHOICES}
_VALID_HISTORY_TYPES = {v for v, _ in ShrineHistory.HISTORY_TYPE_CHOICES}
_VALID_MEMBER_COUNT_RELATIONS = {v for v, _ in ShrineDeityCollective.MEMBER_COUNT_RELATION_CHOICES}
_MEMBER_COUNT_RELATIONS_WITH_COUNT = set(ShrineDeityCollective.MEMBER_COUNT_RELATIONS_WITH_COUNT)
_VALID_MEMBER_LIST_STATUSES = {v for v, _ in ShrineDeityCollective.MEMBER_LIST_STATUS_CHOICES}

ShrineIdentityStatus = Literal["OK", "OK_CANONICAL_PREFERRED", "NOT_FOUND", "AMBIGUOUS"]
SourceIdentityStatus = Literal["CREATE", "REUSE_EXISTING", "CONFLICT", "AMBIGUOUS"]


@dataclass(frozen=True)
class ShrineIdentityResult:
    shrine: Shrine | None
    status: ShrineIdentityStatus
    detail: str = ""


@dataclass(frozen=True)
class SourceIdentityResult:
    source: ShrineKnowledgeSource | None
    status: SourceIdentityStatus
    detail: str = ""


#  Only the columns actually used by identity resolution below. In
# particular this excludes `location`: production's `temples_shrine.location`
# column is a legacy `text` field, but the live `Shrine` model declares it as
# a PostGIS `PointField` (the same schema drift documented in
# docs/audit/temples-0091-production-remediation.md). A bare, unrestricted
# `Shrine.objects.filter(...)` selects every column, which triggers the
# GeometryField converter on the drifted text value and raises
# `GEOSException` before any row is even used — confirmed by running this
# exact function against a restored production dump. `.only()` keeps
# `location` out of the generated SELECT entirely.
_SHRINE_IDENTITY_FIELDS = ("id", "name_jp", "address", "place_ref_id")


def resolve_shrine(name_jp: str, address: str = "") -> ShrineIdentityResult:
    """Resolve a `{name_jp, address}` shrine_ref to exactly one `Shrine` row.

    Never uses a bare `.first()` on an ambiguous match. Resolution order:

    1. Filter by `name_jp`. If `address` is given and narrows the match set
       to exactly one row, use it.
    2. If more than one row remains (duplicate-named shrines, or address
       didn't disambiguate — the historical 0091 case where duplicates share
       an identical address), prefer the row with `place_ref_id IS NULL`
       (the original catalog entry; a non-null `place_ref_id` marks a row
       created later via the map "resolve"/Google Places flow — see the
       0091 remediation doc for how this was established as a reliable
       canonical-vs-duplicate signal for this dataset).
    3. If that still leaves more than one candidate, or leaves zero, this is
       genuinely unresolvable — return AMBIGUOUS or NOT_FOUND. The caller
       must not guess.
    """
    if not name_jp or not name_jp.strip():
        return ShrineIdentityResult(None, "NOT_FOUND", "name_jp is empty")

    base_qs = Shrine.objects.filter(name_jp=name_jp).only(*_SHRINE_IDENTITY_FIELDS)
    candidates = list(base_qs.order_by(F("place_ref_id").asc(nulls_first=True), "id"))

    if not candidates:
        return ShrineIdentityResult(None, "NOT_FOUND", f"no shrine with name_jp={name_jp!r}")

    if address:
        addr_candidates = [c for c in candidates if c.address == address]
        if len(addr_candidates) == 1:
            return ShrineIdentityResult(addr_candidates[0], "OK")
        if addr_candidates:
            candidates = addr_candidates

    if len(candidates) == 1:
        return ShrineIdentityResult(candidates[0], "OK")

    canonical = [c for c in candidates if c.place_ref_id is None]
    if len(canonical) == 1:
        return ShrineIdentityResult(
            canonical[0],
            "OK_CANONICAL_PREFERRED",
            f"{len(candidates)} rows matched name_jp={name_jp!r}; "
            "resolved via place_ref_id IS NULL preference",
        )

    return ShrineIdentityResult(
        None,
        "AMBIGUOUS",
        f"{len(candidates)} rows matched name_jp={name_jp!r} "
        f"({len(canonical)} of which are canonical-preferred); cannot resolve safely",
    )


def normalize_source_url(url: str) -> str:
    """Normalize only URL syntax that cannot change the cited document.

    Scheme and host case and default ports are normalized, fragments are
    removed, and a non-root trailing slash is ignored. Query strings remain
    byte-for-byte significant, and http/https remain distinct.
    """
    value = (url or "").strip()
    if not value:
        return ""
    parts = urlsplit(value)
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    port = parts.port
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, hostname, path, parts.query, ""))


_SOURCE_REUSE_FIELDS = (
    "publisher",
    "verification_status",
    "confidence",
    "bibliography",
    "language",
)


def resolve_source_identity(entry: "SourceEntry") -> SourceIdentityResult:
    """Resolve a portable Source identity without silently duplicating URLs.

    URL-backed Sources use ``source_type + normalized URL`` as semantic
    identity. Exactly one matching row is reusable only when important
    metadata agrees. Multiple matches or metadata drift block the whole
    import. URL-less Sources retain the original title/bibliography lookup.
    """
    normalized_url = normalize_source_url(entry.url)
    if normalized_url:
        candidates = [
            source
            for source in ShrineKnowledgeSource.objects.filter(source_type=entry.source_type)
            .exclude(url="")
            .order_by("id")
            if normalize_source_url(source.url) == normalized_url
        ]
        if len(candidates) > 1:
            return SourceIdentityResult(
                None,
                "AMBIGUOUS",
                f"{len(candidates)} existing Sources match source_type + normalized URL",
            )
        if len(candidates) == 1:
            source = candidates[0]
            conflicts = [
                field
                for field in _SOURCE_REUSE_FIELDS
                if str(getattr(source, field) or "").strip()
                != str(getattr(entry, field) or "").strip()
            ]
            if conflicts:
                return SourceIdentityResult(
                    None,
                    "CONFLICT",
                    "meaningful metadata differs: " + ", ".join(conflicts),
                )
            return SourceIdentityResult(source, "REUSE_EXISTING")
        return SourceIdentityResult(None, "CREATE")

    qs = ShrineKnowledgeSource.objects.filter(
        source_type=entry.source_type,
        title=entry.title,
        url="",
    )
    if entry.bibliography:
        qs = qs.filter(bibliography=entry.bibliography)
    source = qs.order_by("id").first()
    return SourceIdentityResult(
        source,
        "REUSE_EXISTING" if source is not None else "CREATE",
    )


def find_existing_source(
    *, source_type: str, title: str, url: str = "", bibliography: str = ""
) -> ShrineKnowledgeSource | None:
    """Compatibility wrapper for callers that only need a reusable row."""
    result = resolve_source_identity(
        SourceEntry(
            key="",
            source_type=source_type,
            title=title,
            url=url,
            bibliography=bibliography,
        )
    )
    return result.source if result.status == "REUSE_EXISTING" else None


def find_existing_deity(shrine: Shrine, display_name: str) -> ShrineDeity | None:
    return (
        ShrineDeity.objects.filter(shrine=shrine, display_name=display_name).order_by("id").first()
    )


def find_existing_history(shrine: Shrine, history_type: str, title: str) -> ShrineHistory | None:
    return (
        ShrineHistory.objects.filter(shrine=shrine, history_type=history_type, title=title)
        .order_by("id")
        .first()
    )


MembershipDeityStatus = Literal[
    "RESOLVED_EXISTING",
    "RESOLVED_SEED",
    "MEMBERSHIP_DEITY_NOT_FOUND",
    "MEMBERSHIP_DEITY_AMBIGUOUS",
    "MEMBERSHIP_DEITY_WRONG_SHRINE",
]


@dataclass(frozen=True)
class MembershipDeityResult:
    deity: ShrineDeity | None
    status: MembershipDeityStatus
    detail: str = ""

    @property
    def resolved(self) -> bool:
        return self.status in ("RESOLVED_EXISTING", "RESOLVED_SEED")


def resolve_membership_deity(
    shrine: Shrine, display_name: str, seed_deity_names: list[str]
) -> MembershipDeityResult:
    """Membership の deity_ref を same Shrine + exact display_name で厳密に解決する。

    `find_existing_deity()` と違い `.first()` で重複を隠さない。既存 DB 行が無い場合だけ、
    同じ seed / shrine block で宣言された Deity（apply で CREATE される）を参照先として認める。
    Membership のために Deity を作ることはしない。canonical_name / 別名 / note / 近似名は使わない。
    """
    rows = list(ShrineDeity.objects.filter(shrine=shrine, display_name=display_name).order_by("id"))
    if any(row.shrine_id != shrine.pk for row in rows):
        return MembershipDeityResult(
            None, "MEMBERSHIP_DEITY_WRONG_SHRINE", f"display_name={display_name!r}"
        )
    if len(rows) > 1:
        return MembershipDeityResult(
            None,
            "MEMBERSHIP_DEITY_AMBIGUOUS",
            f"{len(rows)} ShrineDeity rows match display_name={display_name!r}",
        )
    if len(rows) == 1:
        return MembershipDeityResult(rows[0], "RESOLVED_EXISTING")

    declared = seed_deity_names.count(display_name)
    if declared > 1:
        return MembershipDeityResult(
            None,
            "MEMBERSHIP_DEITY_AMBIGUOUS",
            f"{declared} same-seed deities declare display_name={display_name!r}",
        )
    if declared == 1:
        return MembershipDeityResult(None, "RESOLVED_SEED")

    elsewhere = ShrineDeity.objects.filter(display_name=display_name).exclude(shrine=shrine)
    if elsewhere.exists():
        return MembershipDeityResult(
            None,
            "MEMBERSHIP_DEITY_WRONG_SHRINE",
            f"display_name={display_name!r} exists only on another Shrine",
        )
    return MembershipDeityResult(
        None, "MEMBERSHIP_DEITY_NOT_FOUND", f"display_name={display_name!r}"
    )


def find_collectives_by_identity(
    shrine: Shrine, source_attested_label: str
) -> list[ShrineDeityCollective]:
    """Collective identity（resolved Shrine + source_attested_label の完全一致）の全候補。

    `.first()` で曖昧さを隠さないよう、呼び出し側が件数で CREATE / 比較 / AMBIGUOUS を決める。
    """
    return list(
        ShrineDeityCollective.objects.filter(
            shrine=shrine, source_attested_label=source_attested_label
        ).order_by("id")
    )


_COLLECTIVE_COMPARE_FIELDS = (
    "role",
    "sort_order",
    "member_count",
    "member_count_relation",
    "member_list_status",
    "verification_status",
    "confidence",
    "verified_at",
    "note",
)
_MEMBERSHIP_COMPARE_FIELDS = (
    "sort_order",
    "verification_status",
    "confidence",
    "verified_at",
    "note",
)


def _comparable(field_name: str, value: Any) -> Any:
    if field_name == "verified_at" and isinstance(value, datetime) and timezone.is_naive(value):
        # DateTimeField は naive 値を TIME_ZONE で保存する。比較も同じ解釈にそろえる。
        return timezone.make_aware(value)
    return value


def diff_persisted_fields(existing: Any, entry: Any, field_names: tuple[str, ...]) -> list[str]:
    """既存行と seed entry の不一致 field 名（created_at / updated_at は比較しない）。"""
    return [
        name
        for name in field_names
        if _comparable(name, getattr(existing, name)) != _comparable(name, getattr(entry, name))
    ]


def diff_collective_fields(existing: ShrineDeityCollective, entry: "CollectiveEntry") -> list[str]:
    return diff_persisted_fields(existing, entry, _COLLECTIVE_COMPARE_FIELDS)


def diff_membership_fields(existing: Any, entry: "MembershipEntry") -> list[str]:
    return diff_persisted_fields(existing, entry, _MEMBERSHIP_COMPARE_FIELDS)


def _parse_date(value: Any, field_name: str, errors: list[str]) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name}: invalid ISO date {value!r}")
        return None


def _parse_datetime(value: Any, field_name: str, errors: list[str]) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        errors.append(f"{field_name}: invalid ISO datetime {value!r}")
        return None


@dataclass
class SourceEntry:
    key: str
    source_type: str
    title: str
    publisher: str = ""
    url: str = ""
    bibliography: str = ""
    accessed_at: date | None = None
    verified_at: datetime | None = None
    verification_status: str = "draft"
    confidence: str = ""
    language: str = ""
    note: str = ""


@dataclass
class DeityEntry:
    display_name: str
    canonical_name: str = ""
    role: str = "unknown"
    sort_order: int = 0
    verification_status: str = "draft"
    confidence: str = ""
    verified_at: datetime | None = None
    note: str = ""
    source_keys: list[str] = field(default_factory=list)


@dataclass
class HistoryEntry:
    history_type: str
    title: str
    content: str
    period_text: str = ""
    event_date: date | None = None
    sort_order: int = 0
    verification_status: str = "draft"
    confidence: str = ""
    verified_at: datetime | None = None
    note: str = ""
    source_keys: list[str] = field(default_factory=list)


@dataclass
class MembershipEntry:
    """schema 1.1 の ShrineDeityCollectiveMembership 1件。source_keys は Collective から継承しない。"""

    deity_display_name: str
    sort_order: int = 0
    verification_status: str = "draft"
    confidence: str = ""
    verified_at: datetime | None = None
    note: str = ""
    source_keys: list[str] = field(default_factory=list)


@dataclass
class CollectiveEntry:
    """schema 1.1 の ShrineDeityCollective 1件。identity = resolved Shrine + source_attested_label。"""

    source_attested_label: str
    role: str = "unknown"
    sort_order: int = 0
    member_count: int | None = None
    member_count_relation: str = "unspecified"
    member_list_status: str = "not_determined"
    verification_status: str = "draft"
    confidence: str = ""
    verified_at: datetime | None = None
    note: str = ""
    source_keys: list[str] = field(default_factory=list)
    memberships: list[MembershipEntry] = field(default_factory=list)


@dataclass
class ShrineBlock:
    name_jp: str
    address: str
    deities: list[DeityEntry] = field(default_factory=list)
    histories: list[HistoryEntry] = field(default_factory=list)
    collectives: list[CollectiveEntry] = field(default_factory=list)


@dataclass
class ParsedSeed:
    schema_version: str
    sources: dict[str, SourceEntry]
    shrines: list[ShrineBlock]
    errors: list[str]


def _check_verification_fields(
    verification_status: str,
    confidence: str,
    verified_at: datetime | None,
    prefix: str,
    errors: list[str],
) -> None:
    if verification_status not in _VALID_VERIFICATION_STATUSES:
        errors.append(f"{prefix}.verification_status: invalid value {verification_status!r}")
    if confidence not in _VALID_CONFIDENCES:
        errors.append(f"{prefix}.confidence: invalid value {confidence!r}")
    if verification_status in ("source_confirmed", "reviewed") and verified_at is None:
        errors.append(
            f"{prefix}.verified_at: required when verification_status={verification_status!r}"
        )


def _check_source_keys(
    source_keys: list, known_sources: dict, prefix: str, errors: list[str]
) -> None:
    for sk in source_keys:
        if sk not in known_sources:
            errors.append(f"{prefix}.source_keys: unknown source key {sk!r}")


def _parse_source(
    raw: dict, prefix: str, sources: dict[str, "SourceEntry"], errors: list[str]
) -> None:
    key = raw.get("key")
    if not key or not isinstance(key, str):
        errors.append(f"{prefix}.key: required, must be a non-empty string")
        return
    if key in sources:
        errors.append(f"{prefix}.key: duplicate key {key!r} within this seed file")
        return

    source_type = raw.get("source_type")
    if source_type not in _VALID_SOURCE_TYPES:
        errors.append(f"{prefix}.source_type: invalid value {source_type!r}")
    title = raw.get("title")
    if not title or not str(title).strip():
        errors.append(f"{prefix}.title: required, must not be blank")
    verification_status = raw.get("verification_status", "draft")
    confidence = raw.get("confidence", "")
    accessed_at = _parse_date(raw.get("accessed_at"), f"{prefix}.accessed_at", errors)
    verified_at = _parse_datetime(raw.get("verified_at"), f"{prefix}.verified_at", errors)
    _check_verification_fields(verification_status, confidence, verified_at, prefix, errors)

    sources[key] = SourceEntry(
        key=key,
        source_type=source_type or "",
        title=str(title or ""),
        publisher=raw.get("publisher", "") or "",
        url=raw.get("url", "") or "",
        bibliography=raw.get("bibliography", "") or "",
        accessed_at=accessed_at,
        verified_at=verified_at,
        verification_status=verification_status,
        confidence=confidence,
        language=raw.get("language", "") or "",
        note=raw.get("note", "") or "",
    )


def _parse_deity(raw: dict, prefix: str, sources: dict, errors: list[str]) -> DeityEntry:
    display_name = raw.get("display_name")
    if not display_name or not str(display_name).strip():
        errors.append(f"{prefix}.display_name: required, must not be blank")
    role = raw.get("role", "unknown")
    if role not in _VALID_ROLES:
        errors.append(f"{prefix}.role: invalid value {role!r}")
    verification_status = raw.get("verification_status", "draft")
    confidence = raw.get("confidence", "")
    verified_at = _parse_datetime(raw.get("verified_at"), f"{prefix}.verified_at", errors)
    _check_verification_fields(verification_status, confidence, verified_at, prefix, errors)
    source_keys = raw.get("source_keys") or []
    _check_source_keys(source_keys, sources, prefix, errors)

    return DeityEntry(
        display_name=str(display_name or ""),
        canonical_name=raw.get("canonical_name", "") or "",
        role=role,
        sort_order=int(raw.get("sort_order", 0) or 0),
        verification_status=verification_status,
        confidence=confidence,
        verified_at=verified_at,
        note=raw.get("note", "") or "",
        source_keys=list(source_keys),
    )


def _parse_history(raw: dict, prefix: str, sources: dict, errors: list[str]) -> HistoryEntry:
    history_type = raw.get("history_type")
    if history_type not in _VALID_HISTORY_TYPES:
        errors.append(f"{prefix}.history_type: invalid value {history_type!r}")
    title = raw.get("title")
    if not title or not str(title).strip():
        errors.append(f"{prefix}.title: required, must not be blank")
    content = raw.get("content")
    if not content or not str(content).strip():
        errors.append(f"{prefix}.content: required, must not be blank")
    verification_status = raw.get("verification_status", "draft")
    confidence = raw.get("confidence", "")
    verified_at = _parse_datetime(raw.get("verified_at"), f"{prefix}.verified_at", errors)
    _check_verification_fields(verification_status, confidence, verified_at, prefix, errors)
    event_date = _parse_date(raw.get("event_date"), f"{prefix}.event_date", errors)
    source_keys = raw.get("source_keys") or []
    _check_source_keys(source_keys, sources, prefix, errors)

    return HistoryEntry(
        history_type=history_type or "",
        title=str(title or ""),
        content=str(content or ""),
        period_text=raw.get("period_text", "") or "",
        event_date=event_date,
        sort_order=int(raw.get("sort_order", 0) or 0),
        verification_status=verification_status,
        confidence=confidence,
        verified_at=verified_at,
        note=raw.get("note", "") or "",
        source_keys=list(source_keys),
    )


def _is_choice(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def _parse_non_negative_int(
    raw: dict, key: str, prefix: str, errors: list[str], *, allow_none: bool
) -> int | None:
    """0 以上の int。bool は int として受け付けない（JSON true/false の誤入力を拒否する）。"""
    default = None if allow_none else 0
    value = raw.get(key, default)
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{prefix}.{key}: must be an integer >= 0, got {value!r}")
        return default
    if value < 0:
        errors.append(f"{prefix}.{key}: must be an integer >= 0, got {value!r}")
        return default
    return value


def _parse_text(raw: dict, key: str, prefix: str, errors: list[str]) -> str:
    value = raw.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        errors.append(f"{prefix}.{key}: must be a string, got {value!r}")
        return ""
    return value


def _parse_required_source_keys(
    raw: dict, prefix: str, sources: dict, errors: list[str]
) -> list[str]:
    """schema 1.1 の Collective / Membership は自分自身の非空 source_keys を必須とする。"""
    source_keys = raw.get("source_keys")
    if not isinstance(source_keys, list) or not source_keys:
        errors.append(f"{prefix}.source_keys: required, must be a non-empty list")
        return []
    valid: list[str] = []
    for sk in source_keys:
        if not isinstance(sk, str):
            errors.append(f"{prefix}.source_keys: source key must be a string, got {sk!r}")
            continue
        if sk not in sources:
            errors.append(f"{prefix}.source_keys: unknown source key {sk!r}")
            continue
        valid.append(sk)
    return valid


def _parse_verification(
    raw: dict, prefix: str, errors: list[str]
) -> tuple[str, str, datetime | None]:
    verification_status = raw.get("verification_status", "draft")
    confidence = raw.get("confidence", "")
    verified_at = _parse_datetime(raw.get("verified_at"), f"{prefix}.verified_at", errors)
    if not _is_choice(verification_status, _VALID_VERIFICATION_STATUSES):
        errors.append(f"{prefix}.verification_status: invalid value {verification_status!r}")
        verification_status = "draft"
    if not _is_choice(confidence, _VALID_CONFIDENCES):
        errors.append(f"{prefix}.confidence: invalid value {confidence!r}")
        confidence = ""
    if verification_status in ("source_confirmed", "reviewed") and verified_at is None:
        errors.append(
            f"{prefix}.verified_at: required when verification_status={verification_status!r}"
        )
    return verification_status, confidence, verified_at


def _parse_membership(
    raw: Any, prefix: str, sources: dict, errors: list[str]
) -> MembershipEntry | None:
    if not isinstance(raw, dict):
        errors.append(f"{prefix}: must be an object")
        return None

    # deity_ref は {"display_name": "..."} のみ。数値PK・別名・canonical_name では参照しない。
    deity_ref = raw.get("deity_ref")
    display_name = ""
    if not isinstance(deity_ref, dict) or set(deity_ref) != {"display_name"}:
        errors.append(
            f"{prefix}.deity_ref: must be an object with exactly one key 'display_name', "
            f"got {deity_ref!r}"
        )
    else:
        value = deity_ref["display_name"]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.deity_ref.display_name: required, must be a non-blank string")
        else:
            display_name = value

    sort_order = _parse_non_negative_int(raw, "sort_order", prefix, errors, allow_none=False)
    verification_status, confidence, verified_at = _parse_verification(raw, prefix, errors)
    return MembershipEntry(
        deity_display_name=display_name,
        sort_order=sort_order or 0,
        verification_status=verification_status,
        confidence=confidence,
        verified_at=verified_at,
        note=_parse_text(raw, "note", prefix, errors),
        source_keys=_parse_required_source_keys(raw, prefix, sources, errors),
    )


def _parse_collective(
    raw: Any, prefix: str, sources: dict, errors: list[str]
) -> CollectiveEntry | None:
    if not isinstance(raw, dict):
        errors.append(f"{prefix}: must be an object")
        return None

    # Source 上の表記をそのまま identity に使う。trim / 正規化 / 翻訳 / 同義語照合はしない。
    label = raw.get("source_attested_label")
    if not isinstance(label, str) or not label.strip():
        errors.append(f"{prefix}.source_attested_label: required, must be a non-blank string")
        label = ""
    elif label != label.strip():
        errors.append(
            f"{prefix}.source_attested_label: must not have leading/trailing whitespace, "
            f"got {label!r}"
        )

    role = raw.get("role", "unknown")
    if not _is_choice(role, _VALID_ROLES):
        errors.append(f"{prefix}.role: invalid value {role!r}")
        role = "unknown"
    sort_order = _parse_non_negative_int(raw, "sort_order", prefix, errors, allow_none=False)
    member_count = _parse_non_negative_int(raw, "member_count", prefix, errors, allow_none=True)
    member_count_relation = raw.get("member_count_relation", "unspecified")
    relation_valid = _is_choice(member_count_relation, _VALID_MEMBER_COUNT_RELATIONS)
    if not relation_valid:
        errors.append(f"{prefix}.member_count_relation: invalid value {member_count_relation!r}")
    member_list_status = raw.get("member_list_status", "not_determined")
    if not _is_choice(member_list_status, _VALID_MEMBER_LIST_STATUSES):
        errors.append(f"{prefix}.member_list_status: invalid value {member_list_status!r}")
        member_list_status = "not_determined"

    # DB constraint chk_deity_coll_count_rel と同じ不変条件。値域（>0 等）は追加しない。
    raw_count = raw.get("member_count")
    if relation_valid:
        if member_count_relation in _MEMBER_COUNT_RELATIONS_WITH_COUNT and raw_count is None:
            errors.append(
                f"{prefix}.member_count: required when "
                f"member_count_relation={member_count_relation!r}"
            )
        elif member_count_relation == "unspecified" and raw_count is not None:
            errors.append(
                f"{prefix}.member_count: must be null when member_count_relation='unspecified'"
            )
    else:
        member_count_relation = "unspecified"

    verification_status, confidence, verified_at = _parse_verification(raw, prefix, errors)
    source_keys = _parse_required_source_keys(raw, prefix, sources, errors)

    memberships: list[MembershipEntry] = []
    raw_memberships = raw.get("memberships", [])
    if not isinstance(raw_memberships, list):
        errors.append(f"{prefix}.memberships: must be a list")
        raw_memberships = []
    seen_deities: set[str] = set()
    for k, m in enumerate(raw_memberships):
        membership = _parse_membership(m, f"{prefix}.memberships[{k}]", sources, errors)
        if membership is None:
            continue
        name = membership.deity_display_name
        if name:
            if name in seen_deities:
                errors.append(
                    f"{prefix}.memberships[{k}].deity_ref.display_name: duplicate {name!r} "
                    "within this collective"
                )
            seen_deities.add(name)
        memberships.append(membership)

    return CollectiveEntry(
        source_attested_label=label,
        role=role,
        sort_order=sort_order or 0,
        member_count=member_count,
        member_count_relation=member_count_relation,
        member_list_status=member_list_status,
        verification_status=verification_status,
        confidence=confidence,
        verified_at=verified_at,
        note=_parse_text(raw, "note", prefix, errors),
        source_keys=source_keys,
        memberships=memberships,
    )


def _parse_collectives(
    raw: dict, schema_version: Any, prefix: str, sources: dict, errors: list[str]
) -> list[CollectiveEntry]:
    if "collectives" not in raw:
        return []
    if schema_version != COLLECTIVE_SCHEMA_VERSION:
        # 1.0 では空リストでも黙って無視しない（contract §3.1）。
        errors.append(
            f"{prefix}.collectives: not allowed in schema_version {schema_version!r}; "
            f"requires {COLLECTIVE_SCHEMA_VERSION!r}"
        )
        return []
    raw_collectives = raw["collectives"]
    if not isinstance(raw_collectives, list):
        errors.append(f"{prefix}.collectives: must be a list")
        return []

    collectives: list[CollectiveEntry] = []
    seen_labels: set[str] = set()
    for j, c in enumerate(raw_collectives):
        collective = _parse_collective(c, f"{prefix}.collectives[{j}]", sources, errors)
        if collective is None:
            continue
        label = collective.source_attested_label
        if label:
            if label in seen_labels:
                errors.append(
                    f"{prefix}.collectives[{j}].source_attested_label: duplicate {label!r} "
                    "within this shrine block"
                )
            seen_labels.add(label)
        collectives.append(collective)
    return collectives


def _parse_shrine_block(
    raw: dict, prefix: str, sources: dict, errors: list[str], schema_version: Any = SCHEMA_VERSION
) -> ShrineBlock:
    shrine_ref = raw.get("shrine_ref") or {}
    name_jp = shrine_ref.get("name_jp")
    if not name_jp or not str(name_jp).strip():
        errors.append(f"{prefix}.shrine_ref.name_jp: required, must not be blank")
        name_jp = ""
    address = shrine_ref.get("address", "") or ""

    deities = [
        _parse_deity(d, f"{prefix}.deities[{j}]", sources, errors)
        for j, d in enumerate(raw.get("deities") or [])
    ]
    histories = [
        _parse_history(h, f"{prefix}.histories[{j}]", sources, errors)
        for j, h in enumerate(raw.get("histories") or [])
    ]

    collectives = _parse_collectives(raw, schema_version, prefix, sources, errors)

    return ShrineBlock(
        name_jp=str(name_jp),
        address=str(address),
        deities=deities,
        histories=histories,
        collectives=collectives,
    )


def parse_seed(raw: dict) -> ParsedSeed:
    """Structural parse + field-level validation. Never touches the DB.

    Collects every structural error found (not just the first) so a single
    `--validate-only` run can report everything wrong with a seed at once.
    """
    errors: list[str] = []

    schema_version = raw.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"schema_version: expected one of {list(SUPPORTED_SCHEMA_VERSIONS)!r}, "
            f"got {schema_version!r}"
        )

    sources: dict[str, SourceEntry] = {}
    raw_sources = raw.get("sources")
    if not isinstance(raw_sources, list):
        errors.append("sources: must be a list")
        raw_sources = []
    for i, s in enumerate(raw_sources):
        _parse_source(s, f"sources[{i}]", sources, errors)

    shrines: list[ShrineBlock] = []
    raw_shrines = raw.get("shrines")
    if not isinstance(raw_shrines, list):
        errors.append("shrines: must be a list")
        raw_shrines = []
    for i, block in enumerate(raw_shrines):
        shrines.append(_parse_shrine_block(block, f"shrines[{i}]", sources, errors, schema_version))

    return ParsedSeed(
        schema_version=str(schema_version or ""), sources=sources, shrines=shrines, errors=errors
    )


__all__ = [
    "SCHEMA_VERSION",
    "COLLECTIVE_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "MembershipDeityResult",
    "resolve_membership_deity",
    "find_collectives_by_identity",
    "diff_collective_fields",
    "diff_membership_fields",
    "CollectiveEntry",
    "MembershipEntry",
    "ShrineIdentityResult",
    "SourceIdentityResult",
    "resolve_shrine",
    "normalize_source_url",
    "resolve_source_identity",
    "find_existing_source",
    "find_existing_deity",
    "find_existing_history",
    "SourceEntry",
    "DeityEntry",
    "HistoryEntry",
    "ShrineBlock",
    "ParsedSeed",
    "parse_seed",
]
