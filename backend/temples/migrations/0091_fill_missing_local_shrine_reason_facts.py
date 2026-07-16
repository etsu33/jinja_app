from django.db import migrations


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
        shrine = Shrine.objects.filter(name_jp=item["name"]).first()
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

    for shrine in Shrine.objects.filter(name_jp__in=names):
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
