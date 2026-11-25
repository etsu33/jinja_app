"""Highlights PR-3: 公開判定（Publication Gate）・位置の目安・承認の取り消し。"""

from datetime import date

import pytest
from django.contrib import admin

from temples.models import ShrineHighlight, ShrineHighlightTranslation
from temples.services import highlight_publication as gate
from temples.tests.highlight_factories import (
    link_source,
    make_displayable_highlight,
    make_highlight,
    make_shrine,
    make_source,
    make_translation,
)

pytestmark = pytest.mark.django_db


def _decide(highlight, language="ja"):
    highlight = ShrineHighlight.objects.prefetch_related(
        "translations", "source_links__source"
    ).get(pk=highlight.pk)
    return gate.decide_for_highlight(highlight, language)


# --- 公開判定 -----------------------------------------------------------------


def test_displayable_when_all_conditions_met():
    decision = _decide(make_displayable_highlight(make_shrine()))
    assert decision.displayable is True
    assert decision.reasons == ()


@pytest.mark.parametrize("status", ["draft", "archived"])
def test_not_displayable_unless_published(status):
    highlight = make_highlight(make_shrine(), publication_status=status)
    make_translation(highlight)
    link_source(highlight, make_source())
    decision = _decide(highlight)
    assert decision.displayable is False
    assert decision.reasons == (gate.REASON_NOT_PUBLISHED,)


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed", "outdated", "rejected"])
def test_not_displayable_unless_highlight_fact_ready(status):
    highlight = make_highlight(make_shrine(), verification_status=status)
    make_translation(highlight)
    link_source(highlight, make_source())
    assert _decide(highlight).reasons == (gate.REASON_NOT_VERIFIED,)


def test_not_displayable_without_any_source():
    highlight = make_highlight(make_shrine())
    make_translation(highlight)
    assert _decide(highlight).reasons == (gate.REASON_NO_PUBLIC_SOURCE,)


@pytest.mark.parametrize("source_type", ["user_observation", "internal_research"])
def test_observation_or_internal_source_alone_is_not_public_evidence(source_type):
    highlight = make_highlight(make_shrine())
    make_translation(highlight)
    link_source(highlight, make_source(source_type=source_type))
    assert _decide(highlight).reasons == (gate.REASON_NO_PUBLIC_SOURCE,)


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed"])
def test_unverified_official_source_is_not_counted(status):
    highlight = make_highlight(make_shrine())
    make_translation(highlight)
    link_source(highlight, make_source(verification_status=status))
    assert _decide(highlight).reasons == (gate.REASON_NO_PUBLIC_SOURCE,)


@pytest.mark.parametrize("review_status", ["draft", "rejected"])
def test_not_displayable_unless_translation_approved(review_status):
    highlight = make_highlight(make_shrine())
    make_translation(highlight, review_status=review_status)
    link_source(highlight, make_source())
    assert _decide(highlight).reasons == (gate.REASON_NO_APPROVED_TRANSLATION,)


def test_language_is_decided_separately():
    highlight = make_displayable_highlight(make_shrine())
    assert _decide(highlight, "ja").displayable is True
    assert _decide(highlight, "en").reasons == (gate.REASON_NO_APPROVED_TRANSLATION,)


@pytest.mark.parametrize("description", ["", "   ", "　"])
def test_approved_translation_needs_description(description):
    highlight = make_highlight(make_shrine())
    make_translation(highlight, description=description)
    link_source(highlight, make_source())
    assert _decide(highlight).reasons == (gate.REASON_EMPTY_DESCRIPTION,)


def test_multiple_failures_are_all_reported():
    highlight = make_highlight(
        make_shrine(), publication_status="draft", verification_status="draft"
    )
    assert _decide(highlight).reasons == (
        gate.REASON_NOT_PUBLISHED,
        gate.REASON_NOT_VERIFIED,
        gate.REASON_NO_PUBLIC_SOURCE,
        gate.REASON_NO_APPROVED_TRANSLATION,
    )


def test_status_change_by_queryset_update_is_reflected_at_display_time():
    highlight = make_displayable_highlight(make_shrine())
    ShrineHighlight.objects.filter(pk=highlight.pk).update(publication_status="archived")
    assert _decide(highlight).displayable is False


# --- 現地で確認した日 ---------------------------------------------------------


def test_latest_observed_on_uses_newest_fact_ready_observation():
    sources = [
        make_source(source_type="user_observation", accessed_at=date(2026, 11, 1)),
        make_source(source_type="user_observation", accessed_at=date(2026, 11, 21)),
        make_source(
            source_type="user_observation",
            verification_status="draft",
            accessed_at=date(2026, 12, 1),
        ),
        make_source(accessed_at=date(2026, 12, 5)),  # 公式の出典の確認日は観察日に数えない
        make_source(source_type="user_observation", accessed_at=None),
    ]
    assert gate.latest_observed_on(sources) == date(2026, 11, 21)


def test_latest_observed_on_is_none_without_observation():
    assert gate.latest_observed_on([make_source()]) is None


# --- 位置の目安と承認の取り消し -----------------------------------------------


def test_location_hint_is_saved():
    highlight = make_highlight(make_shrine())
    text = make_translation(highlight, location_hint="鳥居をくぐって右手")
    text.refresh_from_db()
    assert text.location_hint == "鳥居をくぐって右手"


@pytest.mark.parametrize("field", ShrineHighlightTranslation.REVIEWED_CONTENT_FIELDS)
def test_editing_approved_content_returns_to_draft(field):
    text = make_translation(make_highlight(make_shrine()))
    setattr(text, field, getattr(text, field) + "（修正）")
    text.save()
    text.refresh_from_db()
    assert text.review_status == "draft"
    assert text.reviewed_at is None


def test_editing_content_and_keeping_approved_in_same_save_still_returns_to_draft():
    text = make_translation(make_highlight(make_shrine()))
    reloaded = ShrineHighlightTranslation.objects.get(pk=text.pk)
    reloaded.description = "書き換えた説明"
    reloaded.review_status = "approved"
    reloaded.save()
    reloaded.refresh_from_db()
    assert reloaded.review_status == "draft"


def test_saving_approved_without_content_change_keeps_approval():
    text = make_translation(make_highlight(make_shrine()))
    reviewed_at = text.reviewed_at
    text.save()
    text.refresh_from_db()
    assert text.review_status == "approved"
    assert text.reviewed_at == reviewed_at


def test_draft_can_be_edited_then_approved():
    text = make_translation(make_highlight(make_shrine()), review_status="draft")
    text.description = "下書きを直す"
    text.save()
    text.review_status = "approved"
    from django.utils import timezone

    text.reviewed_at = timezone.now()
    text.save()
    text.refresh_from_db()
    assert text.review_status == "approved"


def test_invalidated_translation_is_hidden_by_gate():
    highlight = make_displayable_highlight(make_shrine())
    text = highlight.translations.get(language_code="ja")
    text.name = "名前を直した"
    text.save()
    assert _decide(highlight).reasons == (gate.REASON_NO_APPROVED_TRANSLATION,)


# --- 管理画面の「表示条件」列 -------------------------------------------------


def test_admin_display_check_shows_each_language():
    highlight = make_displayable_highlight(make_shrine())
    model_admin = admin.site._registry[ShrineHighlight]
    obj = model_admin.get_queryset(request=None).get(pk=highlight.pk)
    assert model_admin.display_check(obj) == "ja: OK / en: no_approved_translation"
