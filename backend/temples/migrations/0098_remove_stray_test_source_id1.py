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
  `ShrineDeity ↔ Source` M2M relations AND delete the Source row.
- `P6_DELIVERY             = REVERSIBLE_DATA_MIGRATION` — this scoped
  `RunPython`.
- `P6_SEED_FIX             = BUNDLED_WITH_MIGRATION_PR` — `src-999004` and its
  two `source_keys` references are removed from `batch_1_7_seed.json` in the
  same PR so a future `import_shrine_knowledge` cannot recreate it.

**`P6_0098_PRESTATE_POLICY = FAIL_CLOSED`.** This migration is a scoped
remediation for exactly **one** audited Production shape. Without persistent
migration-owned state, deleting the Source row makes "the Source was absent
before forward" and "the Source existed and forward deleted it" indistinguish-
able at reverse time. So:

- **Applicability boundary — the only clean no-op.** If `Shrine` pk 1 does
  **not exist at all** (a fresh/empty database being migrated from scratch, or
  any database that does not contain this subject), forward and reverse are
  both a clean no-op. `migrate` on an empty database still succeeds.
- **Once a `Shrine` pk 1 row exists**, forward asserts the **complete** PRE
  contract below and **raises** (`RuntimeError`, "PRESTATE_MISMATCH") on any
  deviation — including a renamed / `place_ref`-set pk-1 row, a missing/extra
  target deity, zero or multiple Source matches, a missing target relation, or
  the Source being referenced by anything other than exactly the two target
  deities. The exception aborts the migration transaction so 0098 is **not**
  recorded as applied. There is no "repair" or "guess" path.
- Therefore, on a database that has `Shrine` pk 1, a **recorded/applied 0098
  implies the exact reversible PRE contract held**, and `restore_stray_source`
  restores that single reviewed state exactly.

**Exact PRE contract** (checked once a `Shrine` pk 1 row exists; all must hold
before any mutation):

1. The `Shrine` pk 1 row has `name_jp = 明治神宮` and `place_ref_id IS NULL`.
2. Exactly **one** `ShrineKnowledgeSource` matches the full semantic identity
   (`source_type` + `title` + `publisher` + `url=""` + `bibliography` — never
   pk; Production pk 2, local dev pk 999004).
3. Exactly the two `ShrineDeity` rows `明治天皇` and `昭憲皇太后` exist on
   `shrine_id = 1` (no missing, no duplicate/extra display_name).
4. **Both** of those deities already cite the target Source, and the target
   Source is cited by **only** those two relations (no third deity, no
   history) — so the row is safely deletable and the state is exactly
   reversible.

`.only(...)` excludes `location` (the 0091 / 0094 legacy `text`-column
GEOSException guard).

**Reverse** runs only after a forward that either applied the audited
remediation or was a clean no-op, so it restores **only** when it can see the
audited 明治神宮 Knowledge shape (Shrine pk 1 = 明治神宮 / no `place_ref`, and
exactly the two target deities); on any other database — a fresh DB, a
partially-shaped DB, or a full temples migration-chain reversal in
tests/tooling — reverse is a clean no-op and never fabricates the stray
Source. It raises only on genuine ambiguity (more than one Source already
matches the semantic identity). When it does restore, it reuses an equivalent
Source row if exactly one is present (never duplicating), else recreates it
from the reviewed seed values, then re-links exactly the two named deities.
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
_TARGET_DEITY_NAME_SET = frozenset(TARGET_DEITY_NAMES)


def _prestate_error(detail):
    return RuntimeError(
        "[temples.0098] PRESTATE_MISMATCH: "
        + detail
        + " — 0098 is a fail-closed scoped remediation for one audited "
        "Production state (P6_0098_PRESTATE_POLICY = FAIL_CLOSED). It does not "
        "repair or guess at unexpected state; the transaction is aborted so "
        "0098 is not recorded as applied."
    )


def _shrine1_present(Shrine):
    """True iff this database has a Shrine pk 1 row at all (the applicability
    boundary: a fresh/empty DB has none → the migration is a clean no-op)."""
    return Shrine.objects.filter(pk=TARGET_SHRINE_ID).exists()


def _matched_shrine(Shrine):
    """The Shrine pk 1 row iff it is 明治神宮 with no place_ref, else None."""
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


def _matched_shrine_or_error(Shrine):
    """Forward guard: assumes `_shrine1_present` already returned True, so a
    non-match here is corruption of the audited subject → fail closed."""
    shrine = _matched_shrine(Shrine)
    if shrine is None:
        raise _prestate_error(
            "the Shrine pk=1 row is not 明治神宮 with place_ref_id IS NULL "
            "(renamed, or a map-resolve duplicate row)"
        )
    return shrine


def _target_deities(ShrineDeity):
    return list(
        ShrineDeity.objects.filter(
            shrine_id=TARGET_SHRINE_ID, display_name__in=TARGET_DEITY_NAMES
        )
    )


def _one_stray_source_or_error(ShrineKnowledgeSource):
    matches = list(ShrineKnowledgeSource.objects.filter(**STRAY_SOURCE))
    if len(matches) == 0:
        raise _prestate_error(
            "no ShrineKnowledgeSource matches the stray Source's full semantic "
            "identity (source_type=user_observation, title='テスト神社 境内案内板', "
            "publisher='テスト神社', url='', "
            "bibliography='テスト神社境内案内板（2026-08-01現地確認）')"
        )
    if len(matches) > 1:
        raise _prestate_error(
            f"{len(matches)} ShrineKnowledgeSource rows match the stray Source's "
            "full semantic identity (expected exactly 1)"
        )
    return matches[0]


def _two_target_deities_or_error(ShrineDeity):
    deities = _target_deities(ShrineDeity)
    names = [d.display_name for d in deities]
    if len(deities) != 2 or frozenset(names) != _TARGET_DEITY_NAME_SET:
        raise _prestate_error(
            "expected exactly the two ShrineDeity rows 明治天皇 and 昭憲皇太后 on "
            f"shrine_id=1, found display_names={sorted(names)!r}"
        )
    return deities


def remove_stray_source(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineDeity = apps.get_model("temples", "ShrineDeity")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    if not _shrine1_present(Shrine):
        return  # empty / non-subject database → clean no-op

    # ---- Shrine pk 1 exists: verify the COMPLETE PRE state; raise on any gap.
    _matched_shrine_or_error(Shrine)
    src = _one_stray_source_or_error(ShrineKnowledgeSource)
    deities = _two_target_deities_or_error(ShrineDeity)

    for deity in deities:
        if not deity.sources.filter(pk=src.pk).exists():
            raise _prestate_error(
                f"ShrineDeity '{deity.display_name}' (shrine_id=1) does not cite "
                "the stray Source (expected both target deities to cite it)"
            )

    # The stray Source must be referenced by ONLY those two relations, so the
    # row is safely deletable and the state is exactly reversible.
    if src.deities.count() != 2 or src.histories.exists():
        raise _prestate_error(
            "the stray Source is referenced by relations other than exactly the "
            "two target deity Facts (a third deity or a history cites it)"
        )

    # ---- PRE state confirmed; only now mutate ----
    for deity in deities:
        deity.sources.remove(src)

    if not src.deities.exists() and not src.histories.exists():
        src.delete()


def restore_stray_source(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineDeity = apps.get_model("temples", "ShrineDeity")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    # Reverse only ever runs after a forward that either applied the audited
    # remediation or was a clean no-op (fail-closed forward rejects everything
    # else). So reverse restores **only** when it can see the audited 明治神宮
    # Knowledge shape; on any other database it is a clean no-op (it must not
    # fabricate the stray Source onto an unrelated / partially-shaped DB —
    # e.g. during a full temples migration-chain reversal in tests/tooling).
    shrine = _matched_shrine(Shrine)
    if shrine is None:
        return
    deities = _target_deities(ShrineDeity)
    if len(deities) != 2 or frozenset(d.display_name for d in deities) != _TARGET_DEITY_NAME_SET:
        return

    matches = list(ShrineKnowledgeSource.objects.filter(**STRAY_SOURCE))
    if len(matches) > 1:
        # genuine ambiguity — do not guess which row to re-link
        raise _prestate_error(
            f"reverse found {len(matches)} ShrineKnowledgeSource rows matching "
            "the stray Source's semantic identity (expected 0 or 1)"
        )
    src = matches[0] if matches else ShrineKnowledgeSource.objects.create(**STRAY_SOURCE_SEED)

    for deity in deities:
        deity.sources.add(src)  # idempotent; never duplicates a link


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0097_p5_id21_id22_tag_reconciliation"),
    ]

    operations = [
        migrations.RunPython(remove_stray_source, restore_stray_source),
    ]
