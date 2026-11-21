"""PR-1: foundation only; no publication gate, API, or composite FK."""

import pytest
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from temples.models import (
    Shrine,
    ShrineHighlight,
    ShrineHighlightHistory,
    ShrineHighlightSource,
    ShrineHighlightTranslation,
    ShrineHistory,
    ShrineKnowledgeSource,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def highlight():
    shrine = Shrine.objects.create(name_jp="Highlights試験", address="試験所在地")
    return ShrineHighlight.objects.create(
        shrine=shrine, stable_key="highlight-test", category="architecture"
    )


def translation(highlight, **kwargs):
    return ShrineHighlightTranslation.objects.create(
        highlight=highlight, language_code="ja", name="試験名称", **kwargs
    )


def history(shrine):
    return ShrineHistory.objects.create(
        shrine=shrine, history_type="historical_event", title="試験記録", content="テスト専用本文"
    )


def test_defaults_and_relations(highlight):
    text = translation(highlight)
    source = ShrineKnowledgeSource.objects.create(source_type="internal_research", title="試験資料")
    item = history(highlight.shrine)
    ShrineHighlightSource.objects.create(highlight=highlight, source=source)
    ShrineHighlightHistory.objects.create(
        highlight=highlight, history=item, shrine=highlight.shrine
    )
    assert highlight.publication_status == highlight.verification_status == "draft"
    assert highlight.confidence == ""
    assert highlight.verified_at is None
    assert text.review_status == "draft" and text.reviewed_at is None
    assert text.description == text.historical_connection == ""
    assert highlight.source_links.get().source == source
    assert highlight.history_links.get().history == item
    assert highlight.translations.get() == text
    assert highlight.created_at and highlight.updated_at and text.created_at and text.updated_at


@pytest.mark.parametrize(
    "category",
    [
        "architecture",
        "cultural_heritage",
        "nature",
        "ritual_festival",
        "historical_site",
        "experience",
    ],
)
def test_fixed_categories_are_accepted(highlight, category):
    item = ShrineHighlight.objects.create(
        shrine=highlight.shrine, stable_key=f"category-{category}", category=category
    )
    item.refresh_from_db()
    assert item.category == category
    assert set(ShrineHighlight.Category.values) == {
        "architecture",
        "cultural_heritage",
        "nature",
        "ritual_festival",
        "historical_site",
        "experience",
    }
    assert ShrineHighlight._meta.get_field("category").max_length == 50


@pytest.mark.parametrize("category", ["建築", "x", "unknown", "ARCHITECTURE"])
def test_undefined_category_is_rejected_by_django(highlight, category):
    highlight.category = category
    with pytest.raises(ValidationError) as error:
        highlight.save()
    assert "category" in error.value.message_dict


@pytest.mark.parametrize("category", ["建築", "x", "unknown", "ARCHITECTURE"])
def test_undefined_category_is_rejected_by_bulk_create(highlight, category):
    with transaction.atomic(), pytest.raises(IntegrityError, match="hl_category_valid"):
        ShrineHighlight.objects.bulk_create(
            [
                ShrineHighlight(
                    shrine=highlight.shrine, stable_key="invalid-category", category=category
                )
            ]
        )


@pytest.mark.parametrize("category", ["建築", "x", "unknown", "ARCHITECTURE"])
def test_undefined_category_is_rejected_by_queryset_update(highlight, category):
    with transaction.atomic(), pytest.raises(IntegrityError, match="hl_category_valid"):
        ShrineHighlight.objects.filter(pk=highlight.pk).update(category=category)


@pytest.mark.parametrize("field", ["stable_key", "category"])
@pytest.mark.parametrize("value", ["", " ", "\t\n", "\u3000"])
def test_blank_highlight_fields_rejected(highlight, field, value):
    setattr(highlight, field, value)
    with pytest.raises(ValidationError):
        highlight.save()


@pytest.mark.parametrize("value", ["", " ", "\t\n", "\u3000"])
def test_blank_name_rejected(highlight, value):
    with pytest.raises(ValidationError):
        ShrineHighlightTranslation.objects.create(
            highlight=highlight, language_code="ja", name=value
        )


@pytest.mark.parametrize("language", ["fr", "JA", "", "ja-JP"])
def test_language_rejected(highlight, language):
    with pytest.raises(ValidationError):
        ShrineHighlightTranslation.objects.create(
            highlight=highlight, language_code=language, name="x"
        )


def test_unique_stable_key_and_language(highlight):
    other = Shrine.objects.create(name_jp="別の試験神社")
    with pytest.raises(ValidationError):
        ShrineHighlight.objects.create(
            shrine=other, stable_key=highlight.stable_key, category="architecture"
        )
    translation(highlight)
    with pytest.raises(ValidationError):
        translation(highlight)
    ShrineHighlightTranslation.objects.create(highlight=highlight, language_code="en", name="Test")


@pytest.mark.parametrize("status", ["source_confirmed", "reviewed"])
def test_verification_timestamp_required(highlight, status):
    highlight.verification_status = status
    with pytest.raises(ValidationError):
        highlight.save()
    highlight.verified_at = timezone.now()
    highlight.save()


def test_review_timestamp_required(highlight):
    with pytest.raises(ValidationError):
        translation(highlight, review_status="approved")
    assert translation(highlight, review_status="approved", reviewed_at=timezone.now()).pk


@pytest.mark.parametrize(
    "field,value",
    [
        ("publication_status", "invalid"),
        ("verification_status", "invalid"),
        ("confidence", "invalid"),
        ("sort_order", -1),
        ("category", "x" * 51),
    ],
)
def test_invalid_highlight_fields(highlight, field, value):
    setattr(highlight, field, value)
    with pytest.raises(ValidationError):
        highlight.save()


@pytest.mark.parametrize(
    "field,value",
    [
        ("stable_key", " \t\n"),
        ("category", " \t\n"),
        ("publication_status", "invalid"),
        ("verification_status", "invalid"),
        ("confidence", "invalid"),
        ("verification_status", "reviewed"),
        ("sort_order", -1),
    ],
)
def test_highlight_constraints_survive_queryset_update(highlight, field, value):
    with transaction.atomic(), pytest.raises(IntegrityError):
        ShrineHighlight.objects.filter(pk=highlight.pk).update(**{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", " \t\n"),
        ("language_code", "fr"),
        ("review_status", "invalid"),
        ("review_status", "approved"),
    ],
)
def test_translation_constraints_survive_queryset_update(highlight, field, value):
    text = translation(highlight)
    with transaction.atomic(), pytest.raises(IntegrityError):
        ShrineHighlightTranslation.objects.filter(pk=text.pk).update(**{field: value})


@pytest.mark.parametrize("blank", ["\u3000", "\u00a0"])
def test_unicode_whitespace_is_rejected_by_postgres_checks(highlight, blank):
    text = translation(highlight)
    for model, pk, field in [
        (ShrineHighlight, highlight.pk, "stable_key"),
        (ShrineHighlight, highlight.pk, "category"),
        (ShrineHighlightTranslation, text.pk, "name"),
    ]:
        with transaction.atomic(), pytest.raises(IntegrityError):
            model.objects.filter(pk=pk).update(**{field: blank})


@pytest.mark.parametrize("value", ["", " ", "\t\n", "\u3000", "\xa0"])
@pytest.mark.parametrize("field", ["stable_key", "category", "name"])
def test_blank_constraints_on_postgresql(highlight, value, field):
    text = translation(highlight)
    model, pk = (
        (ShrineHighlightTranslation, text.pk)
        if field == "name"
        else (ShrineHighlight, highlight.pk)
    )
    with transaction.atomic(), pytest.raises(IntegrityError):
        model.objects.filter(pk=pk).update(**{field: value})


def test_uniqueness_survives_bulk_create(highlight):
    translation(highlight)
    with transaction.atomic(), pytest.raises(IntegrityError):
        ShrineHighlightTranslation.objects.bulk_create(
            [ShrineHighlightTranslation(highlight=highlight, language_code="ja", name="duplicate")]
        )
    with transaction.atomic(), pytest.raises(IntegrityError):
        ShrineHighlight.objects.bulk_create(
            [
                ShrineHighlight(
                    shrine=highlight.shrine,
                    stable_key=highlight.stable_key,
                    category="architecture",
                )
            ]
        )


def test_history_shrine_validation_on_create_and_save(highlight):
    other = Shrine.objects.create(name_jp="別の神社")
    wrong_history = history(other)
    with pytest.raises(ValidationError):
        ShrineHighlightHistory.objects.create(
            highlight=highlight, history=wrong_history, shrine=highlight.shrine
        )
    item = history(highlight.shrine)
    link = ShrineHighlightHistory.objects.create(
        highlight=highlight, history=item, shrine=highlight.shrine
    )
    link.shrine = other
    with pytest.raises(ValidationError):
        link.save()
    link.shrine = highlight.shrine
    link.history = wrong_history
    with pytest.raises(ValidationError):
        link.save()


def test_link_uniqueness_and_protected_targets(highlight):
    source = ShrineKnowledgeSource.objects.create(source_type="internal_research", title="試験")
    item = history(highlight.shrine)
    ShrineHighlightSource.objects.create(highlight=highlight, source=source)
    ShrineHighlightHistory.objects.create(
        highlight=highlight, history=item, shrine=highlight.shrine
    )
    for model, kwargs in [
        (ShrineHighlightSource, {"highlight": highlight, "source": source}),
        (
            ShrineHighlightHistory,
            {"highlight": highlight, "history": item, "shrine": highlight.shrine},
        ),
    ]:
        with transaction.atomic(), pytest.raises(IntegrityError):
            model.objects.bulk_create([model(**kwargs)])
    for obj in [source, item]:
        with transaction.atomic(), pytest.raises(ProtectedError):
            obj.delete()
        with transaction.atomic(), pytest.raises(ProtectedError):
            type(obj).objects.filter(pk=obj.pk).delete()


@pytest.mark.parametrize("status", ["published", "archived"])
@pytest.mark.parametrize("route", ["instance", "queryset", "cascade", "admin", "admin_bulk"])
def test_non_draft_delete_is_protected(highlight, status, route):
    # Keep the instance stale to prove that the receiver reads persisted state.
    ShrineHighlight.objects.filter(pk=highlight.pk).update(publication_status=status)
    text = translation(highlight)
    model_admin = admin.site._registry[ShrineHighlight]
    request = RequestFactory().post("/admin/temples/shrinehighlight/", {"post": "yes"})
    request.user = get_user_model().objects.create_superuser(username="hl-admin", password="unused")
    with transaction.atomic(), pytest.raises(ProtectedError):
        if route == "instance":
            highlight.delete()
        elif route == "queryset":
            ShrineHighlight.objects.filter(pk=highlight.pk).delete()
        elif route == "cascade":
            highlight.shrine.delete()
        elif route == "admin":
            model_admin.delete_model(request, highlight)
        else:
            model_admin.delete_queryset(request, ShrineHighlight.objects.all())
    assert ShrineHighlight.objects.filter(pk=highlight.pk).exists()
    assert ShrineHighlightTranslation.objects.filter(pk=text.pk).exists()
    assert Shrine.objects.filter(pk=highlight.shrine_id).exists()
    highlight.refresh_from_db()
    assert model_admin.has_delete_permission(request, highlight) is False


def test_mixed_bulk_delete_rolls_back_drafts(highlight):
    published = ShrineHighlight.objects.create(
        shrine=highlight.shrine,
        stable_key="published-test",
        category="architecture",
        publication_status="published",
    )
    with transaction.atomic(), pytest.raises(ProtectedError):
        ShrineHighlight.objects.filter(pk__in=[highlight.pk, published.pk]).delete()
    assert ShrineHighlight.objects.filter(pk__in=[highlight.pk, published.pk]).count() == 2


@pytest.mark.parametrize(
    "route", ["instance", "queryset", "cascade", "admin", "admin_bulk", "admin_action"]
)
def test_draft_delete_is_allowed_and_cleans_links(highlight, route, monkeypatch):
    source = ShrineKnowledgeSource.objects.create(source_type="internal_research", title="試験")
    ShrineHighlightSource.objects.create(highlight=highlight, source=source)
    translation(highlight)
    pk = highlight.pk
    model_admin = admin.site._registry[ShrineHighlight]
    request = RequestFactory().post("/admin/", {"post": "yes"})
    request.user = get_user_model().objects.create_superuser(username="hl-admin", password="unused")
    monkeypatch.setattr(model_admin, "message_user", lambda *args, **kwargs: None)
    try:
        if route == "instance":
            highlight.delete()
        elif route == "queryset":
            ShrineHighlight.objects.filter(pk=pk).delete()
        elif route == "cascade":
            highlight.shrine.delete()
        elif route == "admin":
            model_admin.delete_model(request, highlight)
        elif route == "admin_bulk":
            model_admin.delete_queryset(request, ShrineHighlight.objects.filter(pk=pk))
        else:
            delete_selected(model_admin, request, ShrineHighlight.objects.filter(pk=pk))
    finally:
        del model_admin.message_user
    assert not ShrineHighlight.objects.filter(pk=pk).exists()
    assert not ShrineHighlightTranslation.objects.filter(highlight_id=pk).exists()
    assert not ShrineHighlightSource.objects.filter(highlight_id=pk).exists()
    assert ShrineKnowledgeSource.objects.filter(pk=source.pk).exists()


@pytest.mark.parametrize("status", ["published", "archived"])
def test_admin_delete_selected_denies_non_draft(highlight, status):
    ShrineHighlight.objects.filter(pk=highlight.pk).update(publication_status=status)
    request = RequestFactory().post("/admin/", {"post": "yes"})
    request.user = get_user_model().objects.create_superuser(username="hl-admin", password="unused")
    from django.core.exceptions import PermissionDenied

    with pytest.raises(PermissionDenied):
        delete_selected(
            admin.site._registry[ShrineHighlight], request, ShrineHighlight.objects.all()
        )
    assert ShrineHighlight.objects.filter(pk=highlight.pk).exists()


def test_pr1_does_not_claim_composite_fk_enforcement(highlight):
    other = Shrine.objects.create(name_jp="別神社")
    item = history(other)
    # Deliberate isolated test: bulk_create bypasses clean. PR-2 must close this.
    ShrineHighlightHistory.objects.bulk_create(
        [ShrineHighlightHistory(highlight=highlight, history=item, shrine=highlight.shrine)]
    )
    assert highlight.history_links.count() == 1


@pytest.mark.parametrize("status", ["published", "archived"])
@pytest.mark.parametrize("bulk", [False, True])
def test_admin_http_cannot_delete_non_draft(highlight, admin_client, status, bulk):
    ShrineHighlight.objects.filter(pk=highlight.pk).update(publication_status=status)
    if bulk:
        url = reverse("admin:temples_shrinehighlight_changelist")
        payload = {"action": "delete_selected", "post": "yes", "_selected_action": [highlight.pk]}
    else:
        url = reverse("admin:temples_shrinehighlight_delete", args=[highlight.pk])
        payload = {"post": "yes"}
    response = admin_client.post(url, payload)
    assert response.status_code == 403
    assert ShrineHighlight.objects.filter(pk=highlight.pk).exists()


def test_existing_unlinked_knowledge_deletion_contract_is_unchanged(highlight):
    source = ShrineKnowledgeSource.objects.create(source_type="internal_research", title="試験")
    item = history(highlight.shrine)
    source_pk, history_pk = source.pk, item.pk
    source.delete()
    item.delete()
    assert not ShrineKnowledgeSource.objects.filter(pk=source_pk).exists()
    assert not ShrineHistory.objects.filter(pk=history_pk).exists()


def test_raw_sql_delete_is_outside_orm_guard(highlight):
    ShrineHighlight.objects.filter(pk=highlight.pk).update(publication_status="published")
    # No children: this documents the absence of a database DELETE trigger.
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM temples_shrinehighlight WHERE id = %s", [highlight.pk])
    assert not ShrineHighlight.objects.filter(pk=highlight.pk).exists()
