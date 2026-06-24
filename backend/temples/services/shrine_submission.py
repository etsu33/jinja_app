from __future__ import annotations

from dataclasses import asdict, dataclass

from django.contrib.auth import get_user_model
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.db.models.functions import Coalesce, Replace
from django.db import transaction
from django.utils import timezone

from temples.models import Shrine, ShrineSubmission

from temples.services.shrine_duplicate_normalize import (
    normalize_shrine_address_for_duplicate,
    normalize_shrine_name_for_duplicate,
    shrine_name_duplicate_base_key,
)


User = get_user_model()

# 括弧除去キーでの広い検索は短すぎるとノイズになる
_MIN_BASE_NAME_KEY_LEN = 3


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
    """保存・照合用の神社名正規化（service 内の単一実装へ委譲）。"""
    return normalize_shrine_name_for_duplicate(value)


def normalize_shrine_address(value: str) -> str:
    """保存・照合用の住所正規化（service 内の単一実装へ委譲）。"""
    return normalize_shrine_address_for_duplicate(value)


def serialize_duplicate_candidates(candidates: list[DuplicateCandidate]) -> list[dict]:
    return [asdict(candidate) for candidate in candidates]


def find_duplicate_candidates(*, name: str, address: str, limit: int = 3) -> list[DuplicateCandidate]:
    normalized_name = normalize_shrine_name_for_duplicate(name)
    normalized_address = normalize_shrine_address_for_duplicate(address)
    if not normalized_name:
        return []

    base_key = shrine_name_duplicate_base_key(normalized_name)
    legacy_exact = normalized_name.replace("(", "（").replace(")", "）")

    qs = Shrine.objects.all().annotate(
        _dup_name_exact_score=Case(
            When(name_jp__iexact=normalized_name, then=Value(2)),
            When(name_jp__iexact=legacy_exact, then=Value(2)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    if len(base_key) >= _MIN_BASE_NAME_KEY_LEN:
        qs = qs.annotate(
            _dup_name_base_score=Case(
                When(name_jp__icontains=base_key, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
    else:
        qs = qs.annotate(
            _dup_name_base_score=Value(0, output_field=IntegerField())
        )

    if normalized_address:
        qs = qs.annotate(
            _dup_addr_cmp=Replace(
                Replace(Coalesce(F("address"), Value("")), Value("\u3000"), Value("")),
                Value(" "),
                Value(""),
            )
        ).annotate(
            _dup_address_score=Case(
                When(address__icontains=normalized_address, then=Value(1)),
                When(_dup_addr_cmp__icontains=normalized_address, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
    else:
        qs = qs.annotate(
            _dup_address_score=Value(0, output_field=IntegerField())
        )

    rows = (
        qs.filter(Q(_dup_name_exact_score__gt=0) | Q(_dup_name_base_score__gt=0))
        .order_by("-_dup_name_exact_score", "-_dup_name_base_score", "-_dup_address_score", "id")
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

    # 投稿者選択の goriyaku_tags / note は審査時の参考情報として扱う。
    # 検索・推薦に使う Shrine.goriyaku_tags は admin が確認後に確定するため、ここでは自動反映しない。
    # 将来的にタグ自動提案や半自動承認を入れる場合も、正本反映は信頼済みルールを経由させる。
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
