from __future__ import annotations

from dataclasses import asdict, dataclass

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from temples.models import Shrine, ShrineSubmission


User = get_user_model()


class ShrineSubmissionError(Exception):
    pass


class ShrineSubmissionDuplicateError(ShrineSubmissionError):
    def __init__(self, message: str, *, candidates: list[dict] | None = None):
        super().__init__(message)
        self.candidates = candidates or []


class ShrineSubmissionInvalidStateError(ShrineSubmissionError):
    pass


@dataclass(frozen=True)
class DuplicateCheckResult:
    exists_in_shrine: bool
    exists_in_pending_submission: bool


@dataclass(frozen=True)
class DuplicateCandidate:
    id: int
    name: str
    address: str


def normalize_shrine_name(value: str) -> str:
    normalized = (value or "").strip()
    normalized = normalized.replace("\u3000", " ")
    normalized = " ".join(normalized.split())
    normalized = normalized.replace("(", "（").replace(")", "）")
    return normalized


def normalize_shrine_address(value: str) -> str:
    normalized = (value or "").strip()
    normalized = normalized.replace("\u3000", " ")
    normalized = " ".join(normalized.split())
    return normalized


def serialize_duplicate_candidates(candidates: list[DuplicateCandidate]) -> list[dict]:
    return [asdict(candidate) for candidate in candidates]


def find_duplicate_candidates(*, name: str, address: str, limit: int = 3) -> list[DuplicateCandidate]:
    normalized_name = normalize_shrine_name(name)
    normalized_address = normalize_shrine_address(address)
    if not normalized_name:
        return []

    name_terms = [term for term in normalized_name.replace("\u3000", " ").split(" ") if term]
    address_terms = [term for term in normalized_address.replace("\u3000", " ").split(" ") if term]

    qs = Shrine.objects.all()

    query = Q(name_jp__iexact=normalized_name)
    for term in name_terms:
        query |= Q(name_jp__icontains=term)
        query |= Q(name_romaji__icontains=term)

    if normalized_address:
        query |= Q(address__icontains=normalized_address)
        for term in address_terms:
            query |= Q(address__icontains=term)

    rows = (
        qs.filter(query)
        .order_by("id")
        .values("id", "name_jp", "address")[: max(1, limit)]
    )

    return [
        DuplicateCandidate(
            id=row["id"],
            name=row["name_jp"],
            address=row["address"] or "",
        )
        for row in rows
    ]


def has_duplicate_shrine(*, name: str, address: str) -> bool:
    normalized_name = normalize_shrine_name(name)
    normalized_address = normalize_shrine_address(address)
    if not normalized_name or not normalized_address:
        return False

    return Shrine.objects.filter(
        name_jp=normalized_name,
        address=normalized_address,
    ).exists()


def has_duplicate_pending_submission(
    *,
    name: str,
    address: str,
    exclude_submission_id: int | None = None,
) -> bool:
    normalized_name = normalize_shrine_name(name)
    normalized_address = normalize_shrine_address(address)
    if not normalized_name or not normalized_address:
        return False

    qs = ShrineSubmission.objects.filter(
        name=normalized_name,
        address=normalized_address,
        status=ShrineSubmission.Status.PENDING,
    )
    if exclude_submission_id is not None:
        qs = qs.exclude(pk=exclude_submission_id)
    return qs.exists()


def check_submission_duplicates(
    *,
    name: str,
    address: str,
    exclude_submission_id: int | None = None,
) -> DuplicateCheckResult:
    return DuplicateCheckResult(
        exists_in_shrine=has_duplicate_shrine(name=name, address=address),
        exists_in_pending_submission=has_duplicate_pending_submission(
            name=name,
            address=address,
            exclude_submission_id=exclude_submission_id,
        ),
    )


@transaction.atomic
def approve_shrine_submission(
    *,
    submission_id: int,
    reviewer: User,
) -> Shrine:
    submission = ShrineSubmission.objects.select_for_update().get(pk=submission_id)

    if submission.status != ShrineSubmission.Status.PENDING:
        raise ShrineSubmissionInvalidStateError(
            f"pending 以外は承認できません: submission_id={submission.id}, status={submission.status}"
        )

    duplicate = check_submission_duplicates(
        name=submission.name,
        address=submission.address,
        exclude_submission_id=submission.id,
    )

    if duplicate.exists_in_shrine:
        raise ShrineSubmissionDuplicateError(
            f"既存 Shrine と重複しています: name={submission.name}, address={submission.address}",
            candidates=serialize_duplicate_candidates(
                find_duplicate_candidates(name=submission.name, address=submission.address)
            ),
        )

    shrine = Shrine.objects.create(
        name_jp=normalize_shrine_name(submission.name),
        address=normalize_shrine_address(submission.address),
        latitude=submission.lat,
        longitude=submission.lng,
        owner=submission.user,
    )

    submission.status = ShrineSubmission.Status.APPROVED
    submission.reviewed_at = timezone.now()
    submission.reviewed_by = reviewer
    submission.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "updated_at",
        ]
    )

    return shrine


@transaction.atomic
def reject_shrine_submission(
    *,
    submission_id: int,
    reviewer: User,
    review_comment: str = "",
) -> ShrineSubmission:
    submission = ShrineSubmission.objects.select_for_update().get(pk=submission_id)

    submission.status = ShrineSubmission.Status.REJECTED
    submission.reviewed_at = timezone.now()
    submission.reviewed_by = reviewer

    if review_comment:
        submission.review_comment = review_comment

    submission.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "review_comment",
            "updated_at",
        ]
    )
    return submission
