from django.db import migrations
from django.db.models import F

# Only the columns this migration actually reads/writes. In particular this
# excludes `location`: on production the column is a legacy `text` field
# (pre-PostGIS import path), while the historical model state for this
# migration declares it as a PostGIS `PointField`. Selecting it triggers the
# GeometryField converter on every row fetch and raises GEOSException before
# any row is ever touched, even though this migration never reads or writes
# location. `.only()` keeps it out of the generated SELECT entirely.
SHRINE_LOOKUP_FIELDS = ("id", "name_jp", "history_theme", "goriyaku", "place_ref_id", "updated_at")


def _resolve_target_shrine(Shrine, name):
    """Find the single canonical shrine row for `name`.

    A few shrine names (including both names this migration targets) have
    accidental duplicate rows: the original catalog row (no `place_ref_id`)
    plus a later row created by the map "resolve"/Google Places flow (always
    has a `place_ref_id`). `Shrine.Meta.ordering` is `-updated_at`, so a bare
    `.first()` deterministically but silently picks the *duplicate* (more
    recently touched) row instead of the catalog row this migration is meant
    to enrich. Ordering explicitly by `place_ref_id IS NULL` first, then `id`,
    selects the original catalog row when a duplicate exists, and is a no-op
    when it doesn't (single match either way).
    """
    return (
        Shrine.objects.filter(name_jp=name)
        .only(*SHRINE_LOOKUP_FIELDS)
        .order_by(F("place_ref_id").asc(nulls_first=True), "id")
        .first()
    )


def fill_missing_local_shrine_reason_facts(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    updates = [
        {
            "name": "長太稲荷神社",
            "history_theme": "守り",
            "goriyaku": "地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。",
            "tags": ["商売繁盛", "五穀豊穣", "地域安泰"],
        },
        {
            "name": "給田六所神社",
            "history_theme": "守り",
            "goriyaku": "地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。",
            "tags": ["地域安泰", "家内安全"],
        },
    ]

    for item in updates:
        shrine = _resolve_target_shrine(Shrine, item["name"])
        if shrine is None:
            continue

        shrine.history_theme = item["history_theme"]
        shrine.goriyaku = item["goriyaku"]
        shrine.save(update_fields=["history_theme", "goriyaku", "updated_at"])

        tags = list(GoriyakuTag.objects.filter(name__in=item["tags"]))
        if tags:
            shrine.goriyaku_tags.add(*tags)


def reverse_fill_missing_local_shrine_reason_facts(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    names = ["長太稲荷神社", "給田六所神社"]
    tag_names = ["商売繁盛", "五穀豊穣", "地域安泰", "家内安全"]

    tags = list(GoriyakuTag.objects.filter(name__in=tag_names))

    for name in names:
        shrine = _resolve_target_shrine(Shrine, name)
        if shrine is None:
            continue

        shrine.history_theme = ""
        shrine.goriyaku = ""
        shrine.save(update_fields=["history_theme", "goriyaku", "updated_at"])

        if tags:
            shrine.goriyaku_tags.remove(*tags)


class Migration(migrations.Migration):
    dependencies = [
        ("temples", "0090_add_rest_healing_tag_to_silent_shrines"),
    ]

    operations = [
        migrations.RunPython(
            fill_missing_local_shrine_reason_facts,
            reverse_fill_missing_local_shrine_reason_facts,
        ),
    ]
