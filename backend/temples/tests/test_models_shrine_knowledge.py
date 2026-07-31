from __future__ import annotations

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource

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
