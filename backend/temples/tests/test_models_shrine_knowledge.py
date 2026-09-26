from __future__ import annotations

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services.evidence_gate import decide_detail_display_state, decide_fact_usability

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "Knowledge監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_source(**kwargs) -> ShrineKnowledgeSource:
    defaults = dict(
        source_type="shrine_official",
        title="公式由緒書",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


# --- ShrineDeity ---


def test_shrine_deity_create_and_str():
    shrine = _create_shrine()
    deity = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="大己貴命",
        canonical_name="大国主神",
        role="primary",
    )
    assert deity.shrine_id == shrine.id
    assert deity.role == "primary"
    assert deity.verification_status == "draft"
    assert deity.confidence == ""
    assert str(deity) == f"{shrine.id}:大己貴命"


def test_shrine_deity_multiple_per_shrine():
    shrine = _create_shrine()
    ShrineDeity.objects.create(shrine=shrine, display_name="伊弉諾尊", role="primary", sort_order=0)
    ShrineDeity.objects.create(shrine=shrine, display_name="伊弉冉尊", role="primary", sort_order=1)

    names = list(shrine.deities.order_by("sort_order").values_list("display_name", flat=True))
    assert names == ["伊弉諾尊", "伊弉冉尊"]


def test_shrine_deity_blank_display_name_rejected():
    shrine = _create_shrine()
    deity = ShrineDeity(shrine=shrine, display_name="   ")
    with pytest.raises(ValidationError):
        deity.full_clean()


def test_shrine_deity_negative_sort_order_rejected():
    shrine = _create_shrine()
    deity = ShrineDeity(shrine=shrine, display_name="祭神", sort_order=-1)
    with pytest.raises(ValidationError):
        deity.full_clean()


def test_shrine_deity_invalid_role_rejected():
    shrine = _create_shrine()
    deity = ShrineDeity(shrine=shrine, display_name="祭神", role="main")
    with pytest.raises(ValidationError):
        deity.full_clean()


def test_shrine_deity_source_confirmed_requires_verified_at():
    shrine = _create_shrine()
    deity = ShrineDeity(
        shrine=shrine,
        display_name="祭神",
        verification_status="source_confirmed",
        verified_at=None,
    )
    with pytest.raises(ValidationError):
        deity.clean()


def test_shrine_deity_source_confirmed_with_verified_at_passes():
    shrine = _create_shrine()
    deity = ShrineDeity(
        shrine=shrine,
        display_name="祭神",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity.clean()  # raises if invalid


def test_shrine_deity_draft_without_verified_at_passes():
    shrine = _create_shrine()
    deity = ShrineDeity(shrine=shrine, display_name="祭神", verification_status="draft")
    deity.clean()


def test_shrine_deity_sources_m2m():
    shrine = _create_shrine()
    source = _create_source()
    deity = ShrineDeity.objects.create(shrine=shrine, display_name="祭神")
    deity.sources.add(source)

    assert list(deity.sources.all()) == [source]
    assert list(source.deities.all()) == [deity]


# --- ShrineHistory ---


def test_shrine_history_create_and_str():
    shrine = _create_shrine()
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title="創建の由緒",
        content="公式サイトに掲載された由緒本文。",
    )
    assert history.shrine_id == shrine.id
    assert str(history) == f"{shrine.id}:創建の由緒"


def test_shrine_history_blank_content_rejected():
    shrine = _create_shrine()
    history = ShrineHistory(
        shrine=shrine,
        history_type="tradition",
        title="伝承",
        content="   ",
    )
    with pytest.raises(ValidationError):
        history.full_clean()


def test_shrine_history_invalid_history_type_rejected():
    shrine = _create_shrine()
    history = ShrineHistory(
        shrine=shrine,
        history_type="myth",
        title="伝承",
        content="内容",
    )
    with pytest.raises(ValidationError):
        history.full_clean()


def test_shrine_history_founding_year_and_estimated_period_are_separate_fields():
    shrine = _create_shrine()
    confirmed = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="founding",
        title="創建年（確定）",
        content="棟札により確認済み。",
        event_date=date(1200, 1, 1),
    )
    estimated = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="tradition",
        title="創建年代（伝承）",
        content="社伝による推定。",
        period_text="8世紀頃",
    )
    assert confirmed.event_date == date(1200, 1, 1)
    assert confirmed.period_text == ""
    assert estimated.event_date is None
    assert estimated.period_text == "8世紀頃"


def test_shrine_history_reviewed_requires_verified_at():
    shrine = _create_shrine()
    history = ShrineHistory(
        shrine=shrine,
        history_type="official_origin",
        title="由緒",
        content="内容",
        verification_status="reviewed",
        verified_at=None,
    )
    with pytest.raises(ValidationError):
        history.clean()


def test_shrine_history_sources_m2m():
    shrine = _create_shrine()
    source = _create_source()
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title="由緒",
        content="内容",
    )
    history.sources.add(source)

    assert list(history.sources.all()) == [source]
    assert list(source.histories.all()) == [history]


# --- ShrineKnowledgeSource ---


def test_shrine_knowledge_source_create_and_str():
    source = _create_source(title="神社公式サイト")
    assert "神社公式サイト" in str(source)
    assert source.verification_status == "source_confirmed"


def test_shrine_knowledge_source_blank_title_rejected():
    source = ShrineKnowledgeSource(source_type="shrine_official", title="  ")
    with pytest.raises(ValidationError):
        source.full_clean()


def test_shrine_knowledge_source_invalid_source_type_rejected():
    source = ShrineKnowledgeSource(source_type="ai_generated_draft", title="AI下書き")
    with pytest.raises(ValidationError):
        source.full_clean()


def test_shrine_knowledge_source_disputed_without_verified_at_passes():
    # disputedはFact利用不可のverification_statusであり、verified_at必須の対象外
    source = ShrineKnowledgeSource(
        source_type="secondary_editorial",
        title="矛盾する二次資料",
        verification_status="disputed",
        verified_at=None,
    )
    source.clean()


def test_shrine_knowledge_source_shared_across_deity_and_history():
    shrine = _create_shrine()
    source = _create_source()
    deity = ShrineDeity.objects.create(shrine=shrine, display_name="祭神")
    history = ShrineHistory.objects.create(
        shrine=shrine, history_type="official_origin", title="由緒", content="内容"
    )
    deity.sources.add(source)
    history.sources.add(source)

    assert source.deities.count() == 1
    assert source.histories.count() == 1


# --- ShrineDeityCollective（docs/audit/collective-deity-model-change-design.md A-1 §4） ---


def _collective(shrine: Shrine, **kwargs) -> ShrineDeityCollective:
    defaults = dict(shrine=shrine, source_attested_label="明治維新以降戦歿者の御霊")
    defaults.update(kwargs)
    return ShrineDeityCollective(**defaults)


def test_shrine_deity_collective_create_and_str():
    shrine = _create_shrine()
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine,
        source_attested_label="明治維新以降戦歿者の御霊",
        role="primary",
        member_count=56091,
        member_count_relation="exact",
        member_list_status="not_enumerated",
    )
    collective.refresh_from_db()

    assert collective.shrine_id == shrine.id
    assert collective.role == "primary"
    assert collective.member_count == 56091
    assert collective.member_count_relation == "exact"
    assert collective.member_list_status == "not_enumerated"
    assert collective.verification_status == "draft"
    assert collective.confidence == ""
    assert collective.verified_at is None
    assert collective.note == ""
    assert collective.created_at is not None
    assert collective.updated_at is not None
    assert str(collective) == f"{shrine.id}:明治維新以降戦歿者の御霊"


def test_shrine_deity_collective_defaults():
    shrine = _create_shrine()
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine, source_attested_label="ほか8柱"
    )

    assert collective.role == "unknown"
    assert collective.sort_order == 0
    assert collective.member_count is None
    assert collective.member_count_relation == "unspecified"
    assert collective.member_list_status == "not_determined"
    collective.full_clean()


def test_shrine_deity_collective_shrine_related_name():
    shrine = _create_shrine()
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine, source_attested_label="集合祭神"
    )

    assert list(shrine.deity_collectives.all()) == [collective]
    # ShrineDeity 側の関連には現れない（ShrineDeity の意味を広げない）。
    assert shrine.deities.count() == 0


def test_shrine_deity_collective_deterministic_ordering():
    shrine = _create_shrine()
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="C", sort_order=2)
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="A", sort_order=0)
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="B1", sort_order=1)
    ShrineDeityCollective.objects.create(shrine=shrine, source_attested_label="B2", sort_order=1)

    labels = list(shrine.deity_collectives.values_list("source_attested_label", flat=True))
    assert labels == ["A", "B1", "B2", "C"]


def test_shrine_deity_collective_blank_label_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, source_attested_label="   ").full_clean()
    assert "source_attested_label" in exc.value.message_dict


@pytest.mark.parametrize("role", ["primary", "enshrined", "secondary", "unknown"])
def test_shrine_deity_collective_valid_roles_accepted(role):
    shrine = _create_shrine()
    _collective(shrine, role=role).full_clean()


def test_shrine_deity_collective_role_vocabulary_matches_shrine_deity():
    role_field = ShrineDeityCollective._meta.get_field("role")
    assert list(role_field.choices) == list(ShrineDeity.ROLE_CHOICES)


def test_shrine_deity_collective_invalid_role_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, role="main").full_clean()
    assert "role" in exc.value.message_dict


def test_shrine_deity_collective_negative_sort_order_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, sort_order=-1).full_clean()
    assert "sort_order" in exc.value.message_dict


@pytest.mark.parametrize("relation", ["exact", "minimum", "approximate"])
def test_shrine_deity_collective_count_relation_with_count_passes(relation):
    shrine = _create_shrine()
    _collective(shrine, member_count=15, member_count_relation=relation).full_clean()


@pytest.mark.parametrize("relation", ["exact", "minimum", "approximate"])
def test_shrine_deity_collective_count_relation_without_count_rejected(relation):
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, member_count=None, member_count_relation=relation).full_clean()
    assert "member_count" in exc.value.message_dict


def test_shrine_deity_collective_unspecified_with_null_count_passes():
    shrine = _create_shrine()
    _collective(shrine, member_count=None, member_count_relation="unspecified").full_clean()


def test_shrine_deity_collective_unspecified_with_count_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, member_count=8, member_count_relation="unspecified").full_clean()
    assert "member_count" in exc.value.message_dict


def test_shrine_deity_collective_invalid_count_relation_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, member_count=8, member_count_relation="at_least").full_clean()
    assert "member_count_relation" in exc.value.message_dict


def test_shrine_deity_collective_negative_member_count_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, member_count=-1, member_count_relation="exact").full_clean()
    assert "member_count" in exc.value.message_dict


@pytest.mark.parametrize("status", ["complete", "partial", "not_enumerated", "not_determined"])
def test_shrine_deity_collective_member_list_status_values_accepted(status):
    shrine = _create_shrine()
    _collective(shrine, member_list_status=status).full_clean()


def test_shrine_deity_collective_invalid_member_list_status_rejected():
    shrine = _create_shrine()
    with pytest.raises(ValidationError) as exc:
        _collective(shrine, member_list_status="unknown").full_clean()
    assert "member_list_status" in exc.value.message_dict


def test_shrine_deity_collective_source_confirmed_requires_verified_at():
    shrine = _create_shrine()
    collective = _collective(shrine, verification_status="source_confirmed", verified_at=None)
    with pytest.raises(ValidationError) as exc:
        collective.clean()
    assert "verified_at" in exc.value.message_dict


def test_shrine_deity_collective_source_confirmed_with_verified_at_passes():
    shrine = _create_shrine()
    collective = _collective(
        shrine, verification_status="source_confirmed", verified_at=timezone.now()
    )
    collective.clean()  # raises if invalid


def test_shrine_deity_collective_clean_reports_all_field_errors():
    shrine = _create_shrine()
    collective = _collective(
        shrine,
        verification_status="reviewed",
        verified_at=None,
        member_count=None,
        member_count_relation="minimum",
    )
    with pytest.raises(ValidationError) as exc:
        collective.clean()
    assert {"verified_at", "member_count"} <= set(exc.value.message_dict)


def test_shrine_deity_collective_sources_m2m():
    shrine = _create_shrine()
    source = _create_source()
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine, source_attested_label="集合祭神"
    )
    collective.sources.add(source)

    assert list(collective.sources.all()) == [source]
    assert list(source.deity_collectives.all()) == [collective]


def test_shrine_knowledge_source_shared_across_deity_and_collective():
    shrine = _create_shrine()
    source = _create_source()
    deity = ShrineDeity.objects.create(shrine=shrine, display_name="祭神")
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine, source_attested_label="集合祭神"
    )
    deity.sources.add(source)
    collective.sources.add(source)

    assert ShrineKnowledgeSource.objects.count() == 1
    assert list(source.deities.all()) == [deity]
    assert list(source.deity_collectives.all()) == [collective]


def test_shrine_deity_collective_does_not_touch_shrine_deity_rows():
    shrine = _create_shrine()
    ShrineDeity.objects.create(shrine=shrine, display_name="祭神")
    ShrineDeityCollective.objects.create(
        shrine=shrine,
        source_attested_label="ほか15柱以上",
        member_count=15,
        member_count_relation="minimum",
        member_list_status="partial",
    )

    assert list(shrine.deities.values_list("display_name", flat=True)) == ["祭神"]
    assert shrine.deity_collectives.count() == 1


@pytest.mark.parametrize(
    "verification_status, source_status, usable, detail_state",
    [
        ("source_confirmed", "source_confirmed", True, "full"),
        ("reviewed", "reviewed", True, "full"),
        ("draft", "source_confirmed", False, "hidden"),
        ("source_confirmed", "draft", False, "hidden"),
        ("disputed", "source_confirmed", False, "disputed"),
    ],
)
def test_shrine_deity_collective_is_consumed_by_existing_evidence_gate(
    verification_status, source_status, usable, detail_state
):
    """Collective の Evidence 判定は既存 Evidence Gate をそのまま使う（新しい判定主体を作らない）。"""
    shrine = _create_shrine()
    source = _create_source(
        verification_status=source_status,
        verified_at=timezone.now() if source_status in ("source_confirmed", "reviewed") else None,
    )
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine,
        source_attested_label="集合祭神",
        verification_status=verification_status,
        confidence="medium",
        verified_at=timezone.now(),
    )
    collective.sources.add(source)

    source_statuses = list(collective.sources.values_list("verification_status", flat=True))
    decision = decide_fact_usability(
        verification_status=collective.verification_status,
        confidence=collective.confidence,
        source_verification_statuses=source_statuses,
    )
    assert decision.usable is usable
    assert decision.confidence == "medium"
    assert (
        decide_detail_display_state(
            verification_status=collective.verification_status,
            source_verification_statuses=source_statuses,
        )
        == detail_state
    )


def test_shrine_deity_collective_without_source_is_not_usable():
    shrine = _create_shrine()
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine,
        source_attested_label="集合祭神",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )

    decision = decide_fact_usability(
        verification_status=collective.verification_status,
        confidence=collective.confidence,
        source_verification_statuses=collective.sources.values_list(
            "verification_status", flat=True
        ),
    )
    assert decision.usable is False
    assert decision.reason == "no_fact_ready_source"
