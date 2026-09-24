"""F-6D — attach the three audited PlaceRef rows to their canonical primary Shrine.

`docs/audit/place-id-shadow-identity-hardening.md` §14 (F-6B) / §16 (F-6C) / §18.

`temples.0100` (P8-A) deleted the three `place_ref`-only shadow Shrine rows but
deliberately performed **no** `place_ref` merge (`DROP_SHADOW_ONLY`), leaving
their `place_ref` cache rows orphaned. `F-6B` closed the runtime path that could
recreate a shadow from those orphans. This migration closes the data side by
binding each orphan to the primary that the P8-A audit already identified.

Mother Ship decisions (fixed):

    C1_BACKFILL_EXECUTION = YES
    C2_MAPPING_STORAGE    = MIGRATION_ONLY_DECISION_PROVENANCE
                            + Shrine.place_ref AS RUNTIME_SOURCE_OF_TRUTH
                            + NO_NEW_MAPPING_TABLE
    C3_ROLLBACK           = REVERSIBLE_F6D_MIGRATION
                            + RESTORE_PRE_F6D_ORPHAN_STATE
                            + KEEP_PLACE_REF_ROWS
                            + FAIL_CLOSED_ON_UNEXPECTED_STATE

**Identity authority.** The mapping below is the static audited P8-A mapping,
embedded here as this migration's own decision provenance. It is NOT derived at
runtime.

    IDENTITY_AUTHORITY          = Shrine.id
    PLACE_ID_IDENTITY_AUTHORITY = NO
    HEURISTIC_SELECTION         = PROHIBITED

`PlaceRef.name` / `address` / coordinates are never read to choose a Shrine.
No duplicate heuristic, no nearest-shrine search, no normalized-name match.

**One atomic three-pair unit.** Every PRE condition for all three pairs is
verified before the first mutation. A failure raises `PreconditionViolation`;
with `Migration.atomic` at its Django default (`True`) the whole `RunPython`
runs in one transaction, so nothing is mutated and 0114 is not recorded as
applied. There is no repair, no guess, and no partial binding of the pairs that
happen to pass.

    PARTIAL_MUTATION = PROHIBITED

**Fresh-lineage symmetric no-op.** The only clean no-op is a lineage in which
the **entire** audited F-6D subject is absent: all three primaries, all three
target PlaceRefs, all three historical shadow pks, and both audited interaction
events. Any partial absence is fail-closed. Re-running forward against the
already-forward state is therefore **not** an idempotent success — it raises,
exactly as 0100 does.

**Narrow updates.** Mutation uses `QuerySet.update(place_ref_id=...)`, never
`Model.save()`, so `updated_at` (`auto_now=True`) and every unrelated column stay
untouched.

    UPDATED_AT / LATITUDE / LONGITUDE / LOCATION / NAME / ADDRESS / GORIYAKU /
    KNOWLEDGE / INTERACTION_LOGS / PLACEREF_ROWS = IMMUTABLE

**`location` is never projected.** Production's `temples_shrine.location` is a
legacy `text` column while the historical model declares a PostGIS `PointField`,
so a bare `.filter(...)` raises `GEOSException` before any row is touched. Every
Shrine read here goes through `.only(...)` / `.values(...)` with an explicit
column list that excludes `location` (the same guard as 0091 / 0094 / 0098 /
0099 / 0100). The reverse partial-unique check reads `location IS NULL` through
raw SQL rather than loading the column.

Scope: exactly the `place_ref_id` column of Shrine 21 / 22 / 49. No PlaceRef row
is created, modified or deleted. No shadow row is recreated. No interaction log
is moved. `temples.0100` and `temples.0108` are not modified.
"""

from datetime import datetime

from django.db import migrations

#: Columns safe to project from `temples_shrine` (never `location`).
SHRINE_LOOKUP = (
    "id",
    "name_jp",
    "address",
    "latitude",
    "longitude",
    "place_ref_id",
)

# --- Static audited mapping (P8-A snapshot, docs/audit/p8-identity-coordinate-
# remediation.md §3.1-§3.5, re-confirmed by the F-6C Production PRE read). ---
PAIRS = [
    {
        "shrine_pk": 22,
        "place_ref_id": "ChIJl-MEepfxGGAR1Eo44p__GaE",
        "name_jp": "給田六所神社",
        "address": "日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        "coordinate": None,  # 座標は PRE で検査しない（0099 が所有する id 49 のみ検査）
    },
    {
        "shrine_pk": 21,
        "place_ref_id": "ChIJX19mq8nxGGARsA2kP4gX90M",
        "name_jp": "長太稲荷神社",
        "address": "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        "coordinate": None,
    },
    {
        "shrine_pk": 49,
        "place_ref_id": "ChIJK11I4BGJGGAR5mZswigcu58",
        "name_jp": "富岡八幡宮",
        "address": "東京都江東区富岡1-20-3",
        # P8-C (temples.0099) corrected value — READ here, never written.
        "coordinate": (35.6717809, 139.799519),
    },
]

PRIMARY_PKS = [p["shrine_pk"] for p in PAIRS]
TARGET_PLACE_REF_IDS = [p["place_ref_id"] for p in PAIRS]

#: P8-A shadow pks. 0100 deleted them; they must stay gone.
SHADOW_PKS = [101, 103, 104]

#: The two audited `ShrineInteractionLog` rows P8-A moved to their primary.
#: Searched GLOBALLY by this predicate first, then the owner is checked.
AUDITED_EVENTS = [
    {
        "label": "A",
        "user_id": 1,
        "action_type": "detail_view",
        "ctx": "map",
        "created_at": "2026-06-11T07:18:05.580624+00:00",
        "expected_shrine_pk": 22,
    },
    {
        "label": "B",
        "user_id": 1,
        "action_type": "detail_view",
        "ctx": "map",
        "created_at": "2026-06-11T08:00:22.085501+00:00",
        "expected_shrine_pk": 21,
    },
]


class PreconditionViolation(Exception):
    """Raised by forward or reverse when the database does not match the exact
    approved F-6D state. Always raised before any mutation; with
    `Migration.atomic` (default `True`) the whole `RunPython` transaction rolls
    back and 0114 is not recorded as applied. Mirrors the fail-closed guard of
    `temples.0097` / `0098` / `0099` / `0100`."""


def _err(detail):
    return PreconditionViolation(
        "[temples.0114 F-6D] PRESTATE_MISMATCH: "
        + detail
        + " — F6D_PRESTATE_POLICY = FAIL_CLOSED: one atomic three-pair unit, "
        "no repair, no guess, no partial binding. "
        "HEURISTIC_SELECTION = PROHIBITED."
    )


def _parse_ts(value):
    return datetime.fromisoformat(value)


def _meta_ctx(row):
    meta = row.metadata if isinstance(row.metadata, dict) else {}
    return meta.get("ctx")


def _load_shrine(Shrine, pk):
    """One Shrine projected WITHOUT `location` (legacy text column guard)."""
    return Shrine.objects.only(*SHRINE_LOOKUP).filter(pk=pk).first()


def _present_pks(Shrine, pks):
    return [pk for pk in pks if Shrine.objects.only("id").filter(pk=pk).exists()]


def _audited_logs_matching(ShrineInteractionLog, spec, *, shrine_id=None):
    """Every log row matching the canonical audited predicate
    (`user_id` + `action_type` + `metadata.ctx` + exact `created_at`).

    `shrine_id=None` searches **globally** — an audited event existing anywhere
    means the subject is not genuinely absent.
    """
    qs = ShrineInteractionLog.objects.filter(
        user_id=spec["user_id"],
        action_type=spec["action_type"],
        created_at=_parse_ts(spec["created_at"]),
    )
    if shrine_id is not None:
        qs = qs.filter(shrine_id=shrine_id)
    return [r for r in qs if _meta_ctx(r) == spec["ctx"]]


def _any_audited_log_anywhere(ShrineInteractionLog):
    return any(_audited_logs_matching(ShrineInteractionLog, spec) for spec in AUDITED_EVENTS)


def _assert_primary_identity(row, pair):
    pk = pair["shrine_pk"]
    if row is None:
        raise _err(f"canonical primary pk {pk} is missing")
    if row.name_jp != pair["name_jp"]:
        raise _err(f"primary pk {pk} name_jp is {row.name_jp!r}, expected {pair['name_jp']!r}")
    if row.address != pair["address"]:
        raise _err(f"primary pk {pk} address is {row.address!r}, expected {pair['address']!r}")
    if pair["coordinate"] is not None:
        got = (row.latitude, row.longitude)
        if got != pair["coordinate"]:
            raise _err(
                f"primary pk {pk} coordinate is {got!r}, expected the P8-C-corrected "
                f"{pair['coordinate']!r} (READ-only PRE; F-6D never writes it — "
                "temples.0099 owns id 49's coordinate)"
            )


def _assert_shadows_absent(Shrine, *, phase):
    present = _present_pks(Shrine, SHADOW_PKS)
    if present:
        raise _err(
            f"{phase}: historical P8-A shadow pk(s) {sorted(present)} exist again — "
            "0100 removed them and F-6D refuses to run against a reappeared shadow"
        )


def _assert_audited_events(ShrineInteractionLog, *, phase):
    for spec in AUDITED_EVENTS:
        rows = _audited_logs_matching(ShrineInteractionLog, spec)  # global
        if len(rows) != 1:
            raise _err(
                f"{phase}: audited interaction event {spec['label']} has {len(rows)} global "
                "matches (user_id + action_type + metadata.ctx + exact created_at), "
                "expected exactly 1"
            )
        row = rows[0]
        if row.shrine_id != spec["expected_shrine_pk"]:
            raise _err(
                f"{phase}: audited interaction event {spec['label']} is on shrine_id "
                f"{row.shrine_id}, expected its P8-A primary {spec['expected_shrine_pk']}"
            )


def _assert_targets_exist(PlaceRef):
    found = set(
        PlaceRef.objects.filter(pk__in=TARGET_PLACE_REF_IDS).values_list("pk", flat=True)
    )
    missing = [pid for pid in TARGET_PLACE_REF_IDS if pid not in found]
    if missing:
        raise _err(
            f"audited target place_ref row(s) {missing} do not exist in `place_ref` — "
            "F-6D never creates a PlaceRef"
        )


def _fresh_lineage(Shrine, PlaceRef, ShrineInteractionLog):
    """True only when the ENTIRE audited F-6D subject is absent."""
    return (
        not _present_pks(Shrine, PRIMARY_PKS)
        and not _present_pks(Shrine, SHADOW_PKS)
        and not PlaceRef.objects.filter(pk__in=TARGET_PLACE_REF_IDS).exists()
        and not _any_audited_log_anywhere(ShrineInteractionLog)
    )


def _assert_not_partially_absent(Shrine, PlaceRef, ShrineInteractionLog, *, phase):
    """Any partial absence of the subject is fail-closed."""
    primaries = _present_pks(Shrine, PRIMARY_PKS)
    targets = PlaceRef.objects.filter(pk__in=TARGET_PLACE_REF_IDS).count()
    if len(primaries) != len(PRIMARY_PKS):
        raise _err(
            f"{phase}: partial primary set present: {sorted(primaries)} of {PRIMARY_PKS} — "
            "F-6D is one atomic three-pair unit"
        )
    if targets != len(TARGET_PLACE_REF_IDS):
        raise _err(
            f"{phase}: only {targets} of {len(TARGET_PLACE_REF_IDS)} audited target "
            "place_ref rows exist"
        )


def _models(apps):
    return (
        apps.get_model("temples", "Shrine"),
        apps.get_model("temples", "PlaceRef"),
        apps.get_model("temples", "ShrineInteractionLog"),
    )


# --------------------------------------------------------------------------- #
# forward
# --------------------------------------------------------------------------- #
def backfill_forward(apps, schema_editor):
    Shrine, PlaceRef, ShrineInteractionLog = _models(apps)

    if _fresh_lineage(Shrine, PlaceRef, ShrineInteractionLog):
        return  # genuinely fresh lineage: the whole audited subject is absent

    # ---- Phase 1: validate every PRE (no mutation) ----
    _assert_not_partially_absent(Shrine, PlaceRef, ShrineInteractionLog, phase="forward")
    _assert_targets_exist(PlaceRef)
    _assert_shadows_absent(Shrine, phase="forward")

    for pair in PAIRS:
        row = _load_shrine(Shrine, pair["shrine_pk"])
        _assert_primary_identity(row, pair)
        if row.place_ref_id is not None:
            raise _err(
                f"primary pk {pair['shrine_pk']} already has place_ref_id "
                f"{row.place_ref_id!r} — expected NULL. Re-running F-6D forward against "
                "the already-forward state is not an idempotent success"
            )

    claimed = list(
        Shrine.objects.only("id", "place_ref_id")
        .filter(place_ref_id__in=TARGET_PLACE_REF_IDS)
        .values_list("id", "place_ref_id")
    )
    if claimed:
        raise _err(
            f"audited target place_ref id(s) are already claimed by another Shrine row: "
            f"{claimed}"
        )

    _assert_audited_events(ShrineInteractionLog, phase="forward")

    # ---- Phase 2: mutate (reached only if every PRE passed) ----
    # Narrow UPDATE only: `updated_at` (auto_now) and every unrelated column stay
    # untouched. Never `Model.save()`.
    for pair in PAIRS:
        updated = Shrine.objects.filter(pk=pair["shrine_pk"]).update(
            place_ref_id=pair["place_ref_id"]
        )
        if updated != 1:
            raise _err(
                f"forward: UPDATE on primary pk {pair['shrine_pk']} affected {updated} rows, "
                "expected exactly 1"
            )

    # ---- Phase 3: POST verification (whole expected post-state) ----
    for pair in PAIRS:
        row = _load_shrine(Shrine, pair["shrine_pk"])
        if row is None or row.place_ref_id != pair["place_ref_id"]:
            raise _err(
                f"forward POST: primary pk {pair['shrine_pk']} place_ref_id is "
                f"{getattr(row, 'place_ref_id', None)!r}, expected {pair['place_ref_id']!r}"
            )
    _assert_targets_exist(PlaceRef)
    _assert_shadows_absent(Shrine, phase="forward POST")
    _assert_audited_events(ShrineInteractionLog, phase="forward POST")


# --------------------------------------------------------------------------- #
# reverse
# --------------------------------------------------------------------------- #
def _partial_unique_conflict(schema_editor, pair):
    """Would setting this primary's `place_ref_id` back to NULL collide?

    Two partial unique constraints apply only to rows whose `place_ref` IS NULL:

        uq_shrine_name_loc                fields (name_jp, address, location)
                                          where location IS NOT NULL AND place_ref IS NULL
        uq_shrine_name_addr_when_loc_null fields (name_jp, address)
                                          where location IS NULL AND place_ref IS NULL

    Releasing `place_ref` therefore moves the row INTO both partial indexes, so a
    pre-existing NULL-place_ref row with the same identity would violate them.

    `location` is compared **only** as `IS NULL` / `IS NOT NULL` in raw SQL. The
    column is never loaded through the historical GIS ORM model, so the geometry
    converter is never invoked against Production's legacy `text` column.
    """
    with schema_editor.connection.cursor() as cur:
        cur.execute(
            """
            SELECT other.id
            FROM temples_shrine AS other
            JOIN temples_shrine AS target ON target.id = %s
            WHERE other.id <> target.id
              AND other.place_ref_id IS NULL
              AND other.name_jp = target.name_jp
              AND other.address = target.address
              AND (
                    (other.location IS NULL AND target.location IS NULL)
                 OR (other.location IS NOT NULL AND target.location IS NOT NULL
                     AND other.location = target.location)
              )
            ORDER BY other.id
            """,
            [pair["shrine_pk"]],
        )
        return [r[0] for r in cur.fetchall()]


def backfill_reverse(apps, schema_editor):
    Shrine, PlaceRef, ShrineInteractionLog = _models(apps)

    if _fresh_lineage(Shrine, PlaceRef, ShrineInteractionLog):
        return  # symmetric with forward: the whole audited subject is absent

    # ---- A / B / C / D / E / F: the full audited post-forward shape ----
    _assert_not_partially_absent(Shrine, PlaceRef, ShrineInteractionLog, phase="reverse")
    _assert_targets_exist(PlaceRef)
    _assert_shadows_absent(Shrine, phase="reverse")

    for pair in PAIRS:
        row = _load_shrine(Shrine, pair["shrine_pk"])
        _assert_primary_identity(row, pair)
        if row.place_ref_id != pair["place_ref_id"]:
            raise _err(
                f"reverse: primary pk {pair['shrine_pk']} place_ref_id is "
                f"{row.place_ref_id!r}, expected its F-6D value {pair['place_ref_id']!r} "
                "(post-forward shape). Re-running reverse after a successful reverse is "
                "not an idempotent success"
            )

    _assert_audited_events(ShrineInteractionLog, phase="reverse")

    # ---- G: releasing place_ref must not violate the partial unique indexes ----
    for pair in PAIRS:
        conflicts = _partial_unique_conflict(schema_editor, pair)
        if conflicts:
            raise _err(
                f"reverse: setting primary pk {pair['shrine_pk']} place_ref_id back to NULL "
                f"would collide with existing place_ref-less Shrine row(s) {conflicts} on the "
                "partial unique constraints uq_shrine_name_loc / "
                "uq_shrine_name_addr_when_loc_null"
            )

    # ---- restore: release only the three F-6D links ----
    for pair in PAIRS:
        updated = Shrine.objects.filter(
            pk=pair["shrine_pk"], place_ref_id=pair["place_ref_id"]
        ).update(place_ref_id=None)
        if updated != 1:
            raise _err(
                f"reverse: UPDATE on primary pk {pair['shrine_pk']} affected {updated} rows, "
                "expected exactly 1"
            )

    # ---- reverse POST: PRE_F6D_ORPHAN_STATE ----
    for pair in PAIRS:
        row = _load_shrine(Shrine, pair["shrine_pk"])
        if row is None or row.place_ref_id is not None:
            raise _err(
                f"reverse POST: primary pk {pair['shrine_pk']} place_ref_id is "
                f"{getattr(row, 'place_ref_id', None)!r}, expected NULL"
            )
    _assert_targets_exist(PlaceRef)  # PlaceRef rows are kept, now orphaned again
    still_claimed = list(
        Shrine.objects.only("id", "place_ref_id")
        .filter(place_ref_id__in=TARGET_PLACE_REF_IDS)
        .values_list("id", "place_ref_id")
    )
    if still_claimed:
        raise _err(
            f"reverse POST: audited target place_ref id(s) are still claimed: {still_claimed}"
        )
    _assert_shadows_absent(Shrine, phase="reverse POST")
    _assert_audited_events(ShrineInteractionLog, phase="reverse POST")


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0113_adopt_usa_jingu_position"),
    ]

    operations = [
        migrations.RunPython(backfill_forward, backfill_reverse),
    ]
