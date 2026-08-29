"""Remove the stray `user_observation` test Source from Shrine id 1 (明治神宮).

P6-DATA — `docs/audit/p6-id1-user-observation-data-review.md`.

The Full Shrine Fact Integrity Audit found one fabricated placeholder
`ShrineKnowledgeSource` (`title = テスト神社 境内案内板`, `source_type =
user_observation`, no URL) that shipped inside `batch_1_7_seed.json` as
`src-999004` and was imported to Production 2026-08-10, attached to the two
明治神宮 enshrined-deity Facts (`明治天皇`, `昭憲皇太后`) alongside the genuine
`shrine_official` Source. It supports nothing real and is served as a bogus
citation on 明治神宮's Shrine Detail page.

**Mother Ship decisions (final, P6-DATA):**

- `P6_TARGET_SOURCE_STATUS = REMOVE`
- `P6_REMOVAL_SCOPE        = SOURCE_AND_RELATIONS` — remove the two
  `ShrineDeity ↔ Source` M2M relations AND delete the Source row **iff** it is
  then unreferenced by any deity/history.
- `P6_DELIVERY             = REVERSIBLE_DATA_MIGRATION` — this scoped
  `RunPython`.
- `P6_SEED_FIX             = BUNDLED_WITH_MIGRATION_PR` — `src-999004` and its
  two `source_keys` references are removed from `batch_1_7_seed.json` in the
  same PR so a future `import_shrine_knowledge` cannot recreate it.

Scope: **exactly Shrine id 1**, and **exactly** the one Source matched by its
full semantic identity, and **exactly** the `明治天皇` / `昭憲皇太后` relations.
Nothing else — the genuine `shrine_official` Source
(`https://www.meijijingu.or.jp/about/`), every other Source, every Fact, and
every other shrine are untouched.

**Identity, never pk.** The Source pk differs by environment (Production 2,
local dev 999004). Match is by `source_type` + `title` + `publisher` + `url=""`
+ `bibliography` — all five. A shrine-identity mismatch, zero matches, more
than one match, or any semantic-field drift makes the migration a safe no-op
(mirrors 0095 / 0096: "act only when the current state is exactly what is
expected"). `.only(...)` excludes `location` (the 0091 / 0094 legacy
`text`-column GEOSException guard).

Deterministic, idempotent, reversible. Reverse recreates the Source with the
reviewed seed field values (only if absent) and re-links **only** the two
named deities — never by pk, never duplicating an equivalent row.
"""

from django.db import migrations
from django.db.models import F

SHRINE_LOOKUP_FIELDS = ("id", "name_jp", "place_ref_id", "updated_at")

TARGET_SHRINE_ID = 1
TARGET_SHRINE_NAME = "明治神宮"

# Full semantic identity of the stray Source (never its pk).
STRAY_SOURCE = {
    "source_type": "user_observation",
    "title": "テスト神社 境内案内板",
    "publisher": "テスト神社",
    "url": "",
    "bibliography": "テスト神社境内案内板（2026-08-01現地確認）",
}

# Reviewed seed field values, used by reverse to recreate the row if absent.
# (Matches `src-999004` in backend/temples/data/knowledge_seeds/batch_1_7_seed.json.)
STRAY_SOURCE_SEED = {
    **STRAY_SOURCE,
    "accessed_at": None,
    "verified_at": "2026-08-01T07:30:00+00:00",
    "verification_status": "source_confirmed",
    "confidence": "medium",
    "language": "ja",
    "note": "",
}

# The exact deity Facts the stray Source was attached to on Shrine id 1.
TARGET_DEITY_NAMES = ["明治天皇", "昭憲皇太后"]


def _target_shrine(Shrine):
    """The 明治神宮 catalog row (pk + exact name + no place_ref); else None."""
    return (
        Shrine.objects.only(*SHRINE_LOOKUP_FIELDS)
        .filter(
            pk=TARGET_SHRINE_ID,
            name_jp=TARGET_SHRINE_NAME,
            place_ref_id__isnull=True,
        )
        .order_by(F("place_ref_id").asc(nulls_first=True), "id")
        .first()
    )


def _find_stray_sources(ShrineKnowledgeSource):
    """All Sources matching the full semantic identity (never pk)."""
    return list(ShrineKnowledgeSource.objects.filter(**STRAY_SOURCE))


def _target_deities(ShrineDeity):
    return list(
        ShrineDeity.objects.filter(
            shrine_id=TARGET_SHRINE_ID, display_name__in=TARGET_DEITY_NAMES
        )
    )


def remove_stray_source(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineDeity = apps.get_model("temples", "ShrineDeity")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    if _target_shrine(Shrine) is None:
        return  # shrine identity mismatch → safe no-op

    matches = _find_stray_sources(ShrineKnowledgeSource)
    if len(matches) != 1:
        return  # zero matches (already clean) or >1 (ambiguous) → safe no-op

    src = matches[0]

    # Remove ONLY the approved 明治天皇 / 昭憲皇太后 relations, and only where
    # the relation actually exists.
    for deity in _target_deities(ShrineDeity):
        if deity.sources.filter(pk=src.pk).exists():
            deity.sources.remove(src)

    # SOURCE_AND_RELATIONS: delete the row only once nothing references it.
    if not src.deities.exists() and not src.histories.exists():
        src.delete()


def restore_stray_source(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineDeity = apps.get_model("temples", "ShrineDeity")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    if _target_shrine(Shrine) is None:
        return  # shrine identity mismatch → safe no-op

    matches = _find_stray_sources(ShrineKnowledgeSource)
    if len(matches) > 1:
        return  # ambiguous → do not guess

    if matches:
        src = matches[0]  # reuse — never create a duplicate
    else:
        src = ShrineKnowledgeSource.objects.create(**STRAY_SOURCE_SEED)

    # Re-link ONLY the two named deities on Shrine id 1 (never by pk).
    for deity in _target_deities(ShrineDeity):
        deity.sources.add(src)  # no-op if already linked


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0097_p5_id21_id22_tag_reconciliation"),
    ]

    operations = [
        migrations.RunPython(remove_stray_source, restore_stray_source),
    ]
