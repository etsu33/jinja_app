from django.db import migrations


SILENT_SHRINE_NAMES = [
    "筑波山神社",
    "榛名神社",
    "森戸大明神",
    "武蔵御嶽神社",
]

REST_HEALING_TAG_ID = 43


def add_rest_healing_tag_to_silent_shrines(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    try:
        tag = GoriyakuTag.objects.get(id=REST_HEALING_TAG_ID)
    except GoriyakuTag.DoesNotExist:
        return

    shrines = Shrine.objects.filter(
        history_theme="静寂",
        name_jp__in=SILENT_SHRINE_NAMES,
    )

    for shrine in shrines:
        shrine.goriyaku_tags.add(tag)


def remove_rest_healing_tag_from_silent_shrines(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    try:
        tag = GoriyakuTag.objects.get(id=REST_HEALING_TAG_ID)
    except GoriyakuTag.DoesNotExist:
        return

    shrines = Shrine.objects.filter(
        history_theme="静寂",
        name_jp__in=SILENT_SHRINE_NAMES,
    )

    for shrine in shrines:
        shrine.goriyaku_tags.remove(tag)


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0089_actionevent"),
    ]

    operations = [
        migrations.RunPython(
            add_rest_healing_tag_to_silent_shrines,
            remove_rest_healing_tag_from_silent_shrines,
        ),
    ]
