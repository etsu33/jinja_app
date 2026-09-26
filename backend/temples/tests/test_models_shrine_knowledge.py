from __future__ import annotations

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
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


# --- ShrineDeityCollectiveMembership（docs/audit/collective-deity-model-change-design.md A-1 §5） ---


def _collective_with_deity(shrine: Shrine | None = None):
    shrine = shrine or _create_shrine()
    collective = ShrineDeityCollective.objects.create(
        shrine=shrine,
        source_attested_label="大己貴命ほか8柱",
        member_count=9,
        member_count_relation="exact",
        member_list_status="partial",
    )
    deity = ShrineDeity.objects.create(shrine=shrine, display_name="大己貴命", role="primary")
    return collective, deity


def _fact_ready_kwargs() -> dict:
    return dict(verification_status="source_confirmed", verified_at=timezone.now())


def _evaluate(fact) -> tuple:
    source_statuses = list(fact.sources.values_list("verification_status", flat=True))
    decision = decide_fact_usability(
        verification_status=fact.verification_status,
        confidence=fact.confidence,
        source_verification_statuses=source_statuses,
    )
    detail_state = decide_detail_display_state(
        verification_status=fact.verification_status,
        source_verification_statuses=source_statuses,
    )
    return decision, detail_state


def test_membership_create_and_str():
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)
    membership.refresh_from_db()

    assert membership.collective_id == collective.id
    assert membership.deity_id == deity.id
    assert str(membership) == f"{collective.id}:{deity.id}"


def test_membership_defaults():
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    assert membership.sort_order == 0
    assert membership.verification_status == "draft"
    assert membership.confidence == ""
    assert membership.verified_at is None
    assert membership.note == ""
    assert membership.created_at is not None
    assert membership.updated_at is not None
    assert membership.sources.count() == 0


def test_membership_related_names():
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    assert list(collective.memberships.all()) == [membership]
    assert list(deity.collective_memberships.all()) == [membership]


def test_membership_deterministic_ordering():
    shrine = _create_shrine()
    collective, _ = _collective_with_deity(shrine)
    deities = {
        name: ShrineDeity.objects.create(shrine=shrine, display_name=name)
        for name in ("甲", "乙", "丙", "丁")
    }
    for name, order in (("丁", 2), ("甲", 0), ("乙", 1), ("丙", 1)):
        ShrineDeityCollectiveMembership.objects.create(
            collective=collective, deity=deities[name], sort_order=order
        )

    names = [m.deity.display_name for m in collective.memberships.all()]
    assert names == ["甲", "乙", "丙", "丁"]


def test_membership_negative_sort_order_rejected():
    collective, deity = _collective_with_deity()
    with pytest.raises(ValidationError) as exc:
        ShrineDeityCollectiveMembership(
            collective=collective, deity=deity, sort_order=-1
        ).full_clean()
    assert "sort_order" in exc.value.message_dict


def test_membership_same_shrine_accepted():
    collective, deity = _collective_with_deity()
    ShrineDeityCollectiveMembership(collective=collective, deity=deity).full_clean()


def test_membership_cross_shrine_rejected_on_clean():
    collective, _ = _collective_with_deity(_create_shrine("神社甲"))
    other_deity = ShrineDeity.objects.create(
        shrine=_create_shrine("神社乙"), display_name="他社祭神"
    )

    membership = ShrineDeityCollectiveMembership(collective=collective, deity=other_deity)
    with pytest.raises(ValidationError) as exc:
        membership.clean()
    assert "deity" in exc.value.message_dict
    # endpoint を付け替えて修復しない。
    assert membership.collective_id == collective.id
    assert membership.deity_id == other_deity.id


def test_membership_cross_shrine_rejected_on_objects_create():
    collective, _ = _collective_with_deity(_create_shrine("神社甲"))
    other_deity = ShrineDeity.objects.create(
        shrine=_create_shrine("神社乙"), display_name="他社祭神"
    )

    with pytest.raises(ValidationError) as exc:
        ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=other_deity)
    assert "deity" in exc.value.message_dict
    assert ShrineDeityCollectiveMembership.objects.count() == 0


def test_membership_cross_shrine_rejected_on_update():
    collective, deity = _collective_with_deity(_create_shrine("神社甲"))
    other_deity = ShrineDeity.objects.create(
        shrine=_create_shrine("神社乙"), display_name="他社祭神"
    )
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    membership.deity = other_deity
    with pytest.raises(ValidationError):
        membership.save()
    membership.refresh_from_db()
    assert membership.deity_id == deity.id


def test_membership_clean_reports_multiple_field_errors():
    collective, _ = _collective_with_deity(_create_shrine("神社甲"))
    other_deity = ShrineDeity.objects.create(
        shrine=_create_shrine("神社乙"), display_name="他社祭神"
    )

    membership = ShrineDeityCollectiveMembership(
        collective=collective, deity=other_deity, verification_status="reviewed", verified_at=None
    )
    with pytest.raises(ValidationError) as exc:
        membership.clean()
    assert {"deity", "verified_at"} <= set(exc.value.message_dict)


def test_membership_duplicate_pair_rejected_on_save():
    collective, deity = _collective_with_deity()
    ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    with pytest.raises(ValidationError):
        ShrineDeityCollectiveMembership.objects.create(
            collective=collective, deity=deity, sort_order=1
        )
    assert collective.memberships.count() == 1


def test_membership_unique_constraint_is_enforced_by_database():
    constraint_fields = {
        tuple(c.fields)
        for c in ShrineDeityCollectiveMembership._meta.constraints
        if c.name == "uniq_deity_coll_member"
    }
    assert constraint_fields == {("collective", "deity")}

    collective, deity = _collective_with_deity()
    ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)
    # bulk_create は save() / full_clean() を通らない。DB 制約だけで重複を拒否することを確認する。
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ShrineDeityCollectiveMembership.objects.bulk_create(
                [ShrineDeityCollectiveMembership(collective=collective, deity=deity)]
            )
    assert collective.memberships.count() == 1


def test_membership_source_confirmed_requires_verified_at():
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership(
        collective=collective, deity=deity, verification_status="source_confirmed", verified_at=None
    )
    with pytest.raises(ValidationError) as exc:
        membership.clean()
    assert "verified_at" in exc.value.message_dict


def test_membership_source_confirmed_with_verified_at_passes():
    collective, deity = _collective_with_deity()
    ShrineDeityCollectiveMembership(
        collective=collective, deity=deity, **_fact_ready_kwargs()
    ).full_clean()


def test_membership_sources_m2m():
    collective, deity = _collective_with_deity()
    source = _create_source()
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)
    membership.sources.add(source)

    assert list(membership.sources.all()) == [source]
    assert list(source.deity_collective_memberships.all()) == [membership]


def test_membership_evidence_b_case_a_collective_source_is_not_inherited():
    """Case A: Collective は fact-ready Source を持つ / Membership は Source なし。"""
    collective, deity = _collective_with_deity()
    collective.verification_status = "source_confirmed"
    collective.verified_at = timezone.now()
    collective.save()
    collective.sources.add(_create_source(title="Collective の出典"))
    membership = ShrineDeityCollectiveMembership.objects.create(
        collective=collective, deity=deity, **_fact_ready_kwargs()
    )

    collective_decision, collective_detail = _evaluate(collective)
    assert collective_decision.usable is True
    assert collective_detail == "full"

    # Membership は Collective の Source を継承しない。
    assert membership.sources.count() == 0
    membership_decision, membership_detail = _evaluate(membership)
    assert membership_decision.usable is False
    assert membership_decision.reason == "no_fact_ready_source"
    assert membership_detail == "hidden"


def test_membership_evidence_b_case_b_membership_own_source_is_independent():
    """Case B: Membership 自身の fact-ready Source で独立に usable になる。"""
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(
        collective=collective, deity=deity, confidence="high", **_fact_ready_kwargs()
    )
    source = _create_source(title="Membership の出典")
    membership.sources.add(source)

    membership_decision, membership_detail = _evaluate(membership)
    assert membership_decision.usable is True
    assert membership_decision.confidence == "high"
    assert membership_detail == "full"

    # Membership の Source は Collective に付かない（Collective は draft / Source なしのまま）。
    assert collective.sources.count() == 0
    collective_decision, _ = _evaluate(collective)
    assert collective_decision.usable is False


def test_membership_evidence_b_case_c_same_source_shared():
    """Case C: 同じ ShrineKnowledgeSource を Collective と Membership の両方が参照する。"""
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)
    source = _create_source()
    collective.sources.add(source)
    membership.sources.add(source)

    assert ShrineKnowledgeSource.objects.count() == 1
    assert list(source.deity_collectives.all()) == [collective]
    assert list(source.deity_collective_memberships.all()) == [membership]


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
def test_membership_is_consumed_by_existing_evidence_gate(
    verification_status, source_status, usable, detail_state
):
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(
        collective=collective,
        deity=deity,
        verification_status=verification_status,
        verified_at=timezone.now(),
        confidence="medium",
    )
    membership.sources.add(
        _create_source(
            verification_status=source_status,
            verified_at=timezone.now()
            if source_status in ("source_confirmed", "reviewed")
            else None,
        )
    )

    decision, detail = _evaluate(membership)
    assert decision.usable is usable
    assert detail == detail_state


def test_membership_without_fact_ready_source_is_not_usable():
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(
        collective=collective, deity=deity, **_fact_ready_kwargs()
    )
    membership.sources.add(_create_source(verification_status="draft", verified_at=None))

    decision, detail = _evaluate(membership)
    assert decision.usable is False
    assert decision.reason == "no_fact_ready_source"
    assert detail == "hidden"


def test_membership_is_deleted_with_collective():
    collective, deity = _collective_with_deity()
    ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    collective.delete()

    assert ShrineDeityCollectiveMembership.objects.count() == 0
    assert ShrineDeity.objects.filter(pk=deity.pk).exists()


def test_membership_protects_referenced_shrine_deity():
    collective, deity = _collective_with_deity()
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    with pytest.raises(ProtectedError):
        with transaction.atomic():
            deity.delete()
    assert ShrineDeity.objects.filter(pk=deity.pk).exists()
    assert ShrineDeityCollectiveMembership.objects.filter(pk=membership.pk).exists()


def test_membership_does_not_mutate_collective_count_or_list_status():
    shrine = _create_shrine()
    collective, deity = _collective_with_deity(shrine)
    second = ShrineDeity.objects.create(shrine=shrine, display_name="少彦名命")
    ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)
    ShrineDeityCollectiveMembership.objects.create(
        collective=collective, deity=second, sort_order=1
    )

    collective.refresh_from_db()
    assert collective.memberships.count() == 2
    # Membership 行数から member_count / member_list_status を導出しない。
    assert collective.member_count == 9
    assert collective.member_count_relation == "exact"
    assert collective.member_list_status == "partial"


def test_collective_without_memberships_remains_valid():
    collective = ShrineDeityCollective.objects.create(
        shrine=_create_shrine(),
        source_attested_label="明治維新以降戦歿者の御霊",
        member_count=56091,
        member_count_relation="exact",
        member_list_status="not_enumerated",
    )
    collective.full_clean()
    assert collective.memberships.count() == 0


def test_membership_leaves_shrine_deity_and_collective_behavior_unchanged():
    shrine = _create_shrine()
    collective, deity = _collective_with_deity(shrine)
    ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    deity.refresh_from_db()
    deity.full_clean()
    assert str(deity) == f"{shrine.id}:大己貴命"
    assert list(shrine.deities.values_list("display_name", flat=True)) == ["大己貴命"]
    collective.refresh_from_db()
    collective.full_clean()
    assert str(collective) == f"{shrine.id}:大己貴命ほか8柱"
    assert list(shrine.deity_collectives.all()) == [collective]


def test_membership_protect_also_blocks_shrine_delete_like_evidence_link():
    """PROTECT は Shrine 経由の CASCADE 削除でも ProtectedError になる（EvidenceLink.shrine_deity と同じ挙動）。

    Membership を持つ Shrine の削除は、Membership を先に明示削除しない限り失敗する。
    RESTRICT へ変える場合は別の判断として扱う。
    """
    collective, deity = _collective_with_deity()
    ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)

    with pytest.raises(ProtectedError):
        with transaction.atomic():
            collective.shrine.delete()
    assert ShrineDeity.objects.filter(pk=deity.pk).exists()

    collective.memberships.all().delete()
    collective.shrine.delete()
    assert not ShrineDeity.objects.filter(pk=deity.pk).exists()
