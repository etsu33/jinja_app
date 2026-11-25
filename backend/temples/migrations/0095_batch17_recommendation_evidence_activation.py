"""Activate reviewed Recommendation Evidence for the three Batch 17 shrines.

P3 — `docs/audit/batch17-recommendation-evidence-review.md`.

Scope: **only** shrine ids 107 (建部大社) and 108 (波上宮). Shrine 106
(北海道神宮) is intentionally NOT touched — its only recorded Source
(`hokkaidojingu.or.jp`) could not be re-fetched this session (expired TLS
certificate), so every candidate stayed `UNKNOWN` and no PASS exists.

For 107 and 108 this writes ONLY the `PASS` canonical `goriyaku` labels
established by the contract-driven review (`recommendation-evidence-review-contract.md`)
against the shrines' own official Sources, and the matching existing
`GoriyakuTag` M2M links. No `HOLD` / `UNKNOWN` / `NO_EVIDENCE` candidate is
written. No new `GoriyakuTag` is created (labels are resolved by name against
the current 39-row master; a missing label makes the whole migration a
no-op). No Knowledge Fact, `verification_status`, `confidence`, disputed
status, `NEED_TO_GORIYAKU_IDS`, or any other shrine is modified.

Defensive, idempotent, reversible — mirrors the established pattern of
`0090_add_rest_healing_tag_to_silent_shrines` and
`0094_fix_shrine_70_coordinates`:

- each shrine is matched by pk **and** guarded by expected name_jp + address;
  a mismatch makes that shrine a no-op (never touch the wrong row);
- forward only acts when the shrine's `goriyaku` is empty AND it has zero
  `goriyaku_tags` (so a re-run, or a shrine already activated another way,
  is a no-op — `BATCH17_TARGET_STATE_DRIFT` self-guard);
- reverse only acts when the current state is exactly what forward wrote
  (never clobber a later edit).
"""

from django.db import migrations

# (pk, expected name_jp, expected address, ordered PASS labels)
# Labels are ordered strongest-Source-evidence-first (contract §4). Every
# label is an exact `GoriyakuTag.name` in the current 39-row master; the
# `・` delimiter matches `backfill_goriyaku_tags.parse_goriyaku`.
BATCH17_ACTIVATION = [
    (
        107,
        "建部大社",
        "滋賀県大津市神領1-16-1",
        ["開運", "厄除け", "出世運", "勝運", "縁結び", "商売繁盛", "家内安全", "病気平癒"],
    ),
    (
        108,
        "波上宮",
        "沖縄県那覇市若狭1-25-11",
        ["海上安全", "家内安全", "商売繁盛", "厄除け", "安産", "交通安全", "合格祈願", "心願成就"],
    ),
]

GORIYAKU_DELIMITER = "・"

# Excludes `location` from the SELECT: in production `temples_shrine.location`
# is a legacy `text` column while the historical model state declares it as a
# PostGIS `PointField`, so a bare `.filter(...)` raises GEOSException before any
# row is touched. Same guard as 0091 / 0094.
LOOKUP_FIELDS = ("id", "name_jp", "address", "goriyaku", "updated_at")


def _resolve_labels(GoriyakuTag, labels):
    """Resolve every label to an existing GoriyakuTag by exact name.

    Returns the list of tag rows in `labels` order, or None if any label is
    absent from the current master (→ caller makes the migration a no-op;
    never create a tag)."""
    tags = []
    for name in labels:
        tag = GoriyakuTag.objects.filter(name=name).first()
        if tag is None:
            return None
        tags.append(tag)
    return tags


def _target_shrine(Shrine, pk, expected_name, expected_address):
    shrine = Shrine.objects.only(*LOOKUP_FIELDS).filter(pk=pk).first()
    if shrine is None:
        return None
    if shrine.name_jp != expected_name or shrine.address != expected_address:
        return None
    return shrine


def activate_batch17_evidence(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    for pk, expected_name, expected_address, labels in BATCH17_ACTIVATION:
        shrine = _target_shrine(Shrine, pk, expected_name, expected_address)
        if shrine is None:
            continue
        # BATCH17_TARGET_STATE_DRIFT self-guard: only activate an untouched row.
        if (shrine.goriyaku or "").strip() != "":
            continue
        if shrine.goriyaku_tags.exists():
            continue

        tags = _resolve_labels(GoriyakuTag, labels)
        if tags is None:
            continue  # master drift → no-op, never get_or_create

        shrine.goriyaku = GORIYAKU_DELIMITER.join(labels)
        shrine.save(update_fields=["goriyaku", "updated_at"])
        shrine.goriyaku_tags.set(tags)


def deactivate_batch17_evidence(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    for pk, expected_name, expected_address, labels in BATCH17_ACTIVATION:
        shrine = _target_shrine(Shrine, pk, expected_name, expected_address)
        if shrine is None:
            continue

        expected_goriyaku = GORIYAKU_DELIMITER.join(labels)
        if (shrine.goriyaku or "") != expected_goriyaku:
            continue  # not the state we wrote → leave it alone

        tags = _resolve_labels(GoriyakuTag, labels)
        expected_ids = {t.id for t in tags} if tags is not None else None
        current_ids = set(shrine.goriyaku_tags.values_list("id", flat=True))
        if expected_ids is None or current_ids != expected_ids:
            continue

        shrine.goriyaku = ""
        shrine.save(update_fields=["goriyaku", "updated_at"])
        shrine.goriyaku_tags.clear()


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0094_fix_shrine_70_coordinates"),
    ]

    operations = [
        migrations.RunPython(activate_batch17_evidence, deactivate_batch17_evidence),
    ]
