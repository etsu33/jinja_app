"""Remove unsupported Recommendation Evidence M2M tags from shrine ids 21 / 22.

P5-DATA — `docs/audit/p5-id21-id22-tag-reconciliation.md`, following the merged
P5 preflight (`docs/audit/p5-id21-id22-current-state-evidence.md`) and the
FINAL Mother Ship decisions P5-1..P5-5.

These `goriyaku_tags` relations were **hand-set** by migration 0091 as a LEGACY
"reason fill" for two zero/weak-Knowledge local shrines — from a hard-coded name
list, **not** parse-derived, **not** backed by any reviewed Source. Under the
current Recommendation Evidence Review Contract their eligibility is `UNKNOWN`
(no reviewed Source states the benefit). This migration removes them so that
current Recommendation Evidence reflects current reviewed evidence.

**This is NOT a factual/metaphysical denial of shrine tradition.** It only means
KAMI MUSUBI's current reviewed evidence is insufficient to use these labels as
Recommendation Evidence. A future reviewed Source discovery may re-activate them
in a separate task.

Removed:

- id 21 長太稲荷神社: `商売繁盛`, `五穀豊穣`  (Decision P5-1)   + `地域安泰` if present (Decision P5-3)
- id 22 給田六所神社: `家内安全`              (Decision P5-2)   + `地域安泰` if present (Decision P5-3)

Explicitly **NOT** changed (Decision P5-4): `Shrine.goriyaku` raw prose,
`Shrine.history_theme`. Also unchanged: every `ShrineDeity` / `ShrineHistory` /
`ShrineKnowledgeSource` row and field, the `GoriyakuTag` master taxonomy,
`NEED_TO_GORIYAKU_IDS`, and all Recommendation / ranking / scoring code.

**Local/Production reproducibility.** The local dev DB (`jinja_db`) carries a
drifted 46-row `GoriyakuTag` table while Production has the clean 39-row master,
so PKs differ per label (`商売繁盛` = 4 in Production, 17 locally). Tags are
therefore matched by **exact canonical name**, never by PK. `地域安泰` is a
legacy label **absent from the Production master** — matching it by name makes
its cleanup a safe no-op in Production and an actual removal in the drifted
local DB, converging both environments.

Scope: **exactly shrine ids 21 and 22**, catalog rows only (`place_ref_id IS
NULL`); the `place_ref`-set duplicate shadow rows (103 / 101) are never touched.
Deterministic, idempotent, reversible (0090 / 0091 / 0094 / 0095 pattern). No
`get_or_create`; a missing tag name is simply skipped in both directions.
"""

from django.db import migrations
from django.db.models import F

SHRINE_LOOKUP_FIELDS = ("id", "name_jp", "place_ref_id", "updated_at")

# (shrine pk, expected name_jp, [canonical/legacy tag names to remove])
RECONCILE = [
    (21, "長太稲荷神社", ["商売繁盛", "五穀豊穣", "地域安泰"]),
    (22, "給田六所神社", ["家内安全", "地域安泰"]),
]


def _target_shrine(Shrine, pk, expected_name):
    """The catalog row for this shrine (pk + exact name + no place_ref).

    A mismatch (renamed row, or only a `place_ref`-set duplicate present) makes
    that shrine a no-op — the duplicate shadow rows 103 / 101 are never hit.
    """
    return (
        Shrine.objects.only(*SHRINE_LOOKUP_FIELDS)
        .filter(pk=pk, name_jp=expected_name, place_ref_id__isnull=True)
        .order_by(F("place_ref_id").asc(nulls_first=True), "id")
        .first()
    )


def _tags_by_name(GoriyakuTag, names):
    """Existing GoriyakuTag rows for `names`, matched by exact name (never PK).

    Names with no row (e.g. `地域安泰` in Production) are simply absent from the
    result — never created.
    """
    return list(GoriyakuTag.objects.filter(name__in=names))


def reconcile_forward(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    for pk, expected_name, remove_names in RECONCILE:
        shrine = _target_shrine(Shrine, pk, expected_name)
        if shrine is None:
            continue
        tags = _tags_by_name(GoriyakuTag, remove_names)
        if tags:
            shrine.goriyaku_tags.remove(*tags)  # no-op for a tag not attached


def reconcile_reverse(apps, schema_editor):
    """Re-attach exactly the relations this migration is designed to remove,
    for every name whose `GoriyakuTag` exists in this environment.

    A tag absent from the environment (`地域安泰` in Production) is skipped —
    never created.
    """
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    for pk, expected_name, remove_names in RECONCILE:
        shrine = _target_shrine(Shrine, pk, expected_name)
        if shrine is None:
            continue
        tags = _tags_by_name(GoriyakuTag, remove_names)
        if tags:
            shrine.goriyaku_tags.add(*tags)  # no-op for a tag already attached


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0096_source_backfill_id10_id22"),
    ]

    operations = [
        migrations.RunPython(reconcile_forward, reconcile_reverse),
    ]
