"""見どころへのアンサー（ShrineHighlightAnswer）：モデル・承認の取り消し・公開判定・管理画面。"""

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from temples.domain.need_tags import NEED_TAGS
from temples.models import ShrineHighlightAnswer
from temples.services import highlight_publication as gate
from temples.tests.highlight_factories import (
    make_answer,
    make_displayable_highlight,
    make_highlight,
    make_shrine,
    make_translation,
)

pytestmark = pytest.mark.django_db


def _reload(answer):
    return (
        ShrineHighlightAnswer.objects.select_related("highlight")
        .prefetch_related("highlight__translations", "highlight__source_links__source")
        .get(pk=answer.pk)
    )


# --- モデル -------------------------------------------------------------------


@pytest.mark.parametrize("need_tag", NEED_TAGS)
def test_every_need_tag_can_be_saved(need_tag):
    answer = make_answer(make_displayable_highlight(make_shrine()), need_tag=need_tag)
    assert answer.pk


def test_unknown_need_tag_is_rejected():
    with pytest.raises(ValidationError):
        make_answer(make_displayable_highlight(make_shrine()), need_tag="performing_arts")


def test_same_highlight_need_and_language_is_unique():
    highlight = make_displayable_highlight(make_shrine())
    make_answer(highlight)
    with pytest.raises((ValidationError, IntegrityError)), transaction.atomic():
        make_answer(highlight)


def test_same_text_can_exist_for_another_need_or_language():
    highlight = make_displayable_highlight(make_shrine())
    make_answer(highlight, need_tag="career")
    make_answer(highlight, need_tag="mental")
    make_answer(highlight, need_tag="career", language_code="en", answer_text="It may echo.")
    assert highlight.answers.count() == 3


@pytest.mark.parametrize("text", ["", "   ", "　"])
def test_blank_answer_text_is_rejected(text):
    with pytest.raises(ValidationError):
        make_answer(make_displayable_highlight(make_shrine()), answer_text=text)


def test_approved_requires_reviewed_at():
    highlight = make_displayable_highlight(make_shrine())
    with pytest.raises(ValidationError):
        ShrineHighlightAnswer.objects.create(
            highlight=highlight,
            need_tag="career",
            language_code="ja",
            answer_text="文",
            review_status="approved",
        )


def test_answers_are_deleted_with_draft_highlight():
    highlight = make_highlight(make_shrine(), publication_status="draft")
    make_answer(highlight)
    highlight.delete()
    assert ShrineHighlightAnswer.objects.count() == 0


# --- 承認の取り消し -----------------------------------------------------------


def test_editing_approved_text_returns_to_draft():
    answer = make_answer(make_displayable_highlight(make_shrine()))
    answer.answer_text = "書き換えた文"
    answer.save()
    answer.refresh_from_db()
    assert answer.review_status == "draft"
    assert answer.reviewed_at is None


def test_saving_approved_without_change_keeps_approval():
    answer = make_answer(make_displayable_highlight(make_shrine()))
    answer.save()
    answer.refresh_from_db()
    assert answer.review_status == "approved"


def test_changing_need_tag_alone_keeps_approval():
    # 相談の種類の付け替えは文章の変更ではない（文は同じ）。承認は文に対して行う。
    answer = make_answer(make_displayable_highlight(make_shrine()), need_tag="career")
    answer.need_tag = "mental"
    answer.save()
    answer.refresh_from_db()
    assert answer.review_status == "approved"


def test_translation_invalidation_still_works_after_refactor():
    highlight = make_highlight(make_shrine())
    text = make_translation(highlight)
    text.description = "直した"
    text.save()
    text.refresh_from_db()
    assert text.review_status == "draft"


# --- 公開判定 -----------------------------------------------------------------


def test_answer_on_displayable_highlight_is_displayable():
    answer = make_answer(make_displayable_highlight(make_shrine()))
    decision = gate.decide_answer_publication(_reload(answer), "ja")
    assert decision.displayable is True


@pytest.mark.parametrize("status", ["draft", "rejected"])
def test_unapproved_answer_is_hidden(status):
    answer = make_answer(make_displayable_highlight(make_shrine()), review_status=status)
    assert gate.decide_answer_publication(_reload(answer), "ja").reasons == (
        gate.REASON_ANSWER_NOT_APPROVED,
    )


def test_answer_is_hidden_when_highlight_is_not_published():
    highlight = make_highlight(make_shrine(), publication_status="draft")
    make_translation(highlight)
    from temples.tests.highlight_factories import link_source, make_source

    link_source(highlight, make_source())
    answer = make_answer(highlight)
    assert gate.decide_answer_publication(_reload(answer), "ja").reasons == (
        gate.REASON_HIGHLIGHT_NOT_DISPLAYABLE,
    )


def test_answer_language_must_match_requested_language():
    answer = make_answer(make_displayable_highlight(make_shrine()), language_code="ja")
    reasons = gate.decide_answer_publication(_reload(answer), "en").reasons
    assert gate.REASON_ANSWER_LANGUAGE_MISMATCH in reasons


def test_english_answer_needs_english_highlight_translation():
    highlight = make_displayable_highlight(make_shrine())  # 日本語の翻訳だけ
    answer = make_answer(highlight, language_code="en", answer_text="It may echo your feeling.")
    assert gate.decide_answer_publication(_reload(answer), "en").reasons == (
        gate.REASON_HIGHLIGHT_NOT_DISPLAYABLE,
    )


# --- 管理画面 -----------------------------------------------------------------


def test_admin_answer_display_check():
    shown = make_answer(make_displayable_highlight(make_shrine("見どころ試験神社A")))
    hidden = make_answer(
        make_displayable_highlight(make_shrine("見どころ試験神社B")), review_status="draft"
    )
    model_admin = admin.site._registry[ShrineHighlightAnswer]
    qs = model_admin.get_queryset(request=None)
    assert model_admin.display_check(qs.get(pk=shown.pk)) == "OK"
    assert model_admin.display_check(qs.get(pk=hidden.pk)) == "answer_not_approved"


def test_highlight_admin_has_answer_inline():
    from temples.models import ShrineHighlight

    model_admin = admin.site._registry[ShrineHighlight]
    assert any(inline.model is ShrineHighlightAnswer for inline in model_admin.inlines)
