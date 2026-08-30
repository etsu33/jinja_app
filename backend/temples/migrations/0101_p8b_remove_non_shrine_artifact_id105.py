"""P8-B — remove the non-shrine artefact `Shrine` row id 105 (広島市).

`docs/audit/p8-identity-coordinate-remediation.md` §9, §15, §19
(`P8_105_ACTION` — the audit's recommended `REMOVE_ARTIFACT`).

Production `Shrine` pk 105 is `name_jp = 広島市` ("Hiroshima City"),
`kind = shrine` (misclassified), `address = 日本、広島県広島市` (prefecture +
city only), whose `place_ref` Google-place `snapshot_json.types` are
**`["locality", "political"]`** — an administrative area, **not** a
`place_of_worship`. It carries **no** shrine data: 0 `ShrineDeity`, 0
`ShrineHistory`, 0 `ShrineKnowledgeSource` relation, 0 `goriyaku_tags`, empty
`goriyaku` / `history_theme` / `sajin` / `description`, all counters 0, no
`owner`, and **0** rows in every user-owned / analytics table referencing
`Shrine`. Re-confirmed by a read-only Production PRE read for this PR.

**Classification: `CONFIRMED_NON_SHRINE_ARTIFACT`. Recommendation impact:
NONE** — it holds 0 `goriyaku_tags`, and Recommendation scoring reads only the
`goriyaku_tags`-GID intersection; removing it changes no candidate
eligibility, `score_need`, C1, ranking, Need match, Lead, Reason, Concierge,
or Compass output.

**`P8_B_DELIVERY = REVERSIBLE_DATA_MIGRATION`, fail-closed.** No mutation
begins until every PRE condition is verified; a failure raises
`PreconditionViolation` and — with `Migration.atomic` at its Django default
(`True`) — the whole `RunPython` transaction rolls back and 0101 is not
recorded as applied. No repair, no guess, no partial relation cleanup.
(Same contract class as `temples.0097` / `0098` / `0099` / `0100`.)

Forward's PRE (when pk 105 exists) requires exact `pk` / `kind` / `name_jp` /
`address` / `latitude` / `longitude` (the last two match the static values
reverse restores); `place_ref_id` == the audited id **and** the `place_ref`
row's `snapshot_json` is a dict whose `types` is a **list** containing
`"locality"` and **not** `"place_of_worship"` (strict, unconditional — an
empty / missing / non-list `types` is a `PreconditionViolation`; locality is
never inferred from name / address / coordinates / place_ref id); every
semantic text field blank; every counter 0; no `owner`; and 0 rows in every
`Shrine`-FK relation table.

**`P8_B_PLACE_REF_POLICY = DROP_SHRINE_LINK_ONLY`.** Forward deletes only the
`Shrine` row; the standalone `place_ref` cache row
(`ChIJu0_z7giZWjURcvfBz1DO5Ac`) — a valid locality/political `PlaceRef`
object independent of the bogus `Shrine` — is **kept** (no FK points from
`place_ref` back to `Shrine`; deleting the `Shrine` simply orphans it).
Reverse re-links the exact same `place_ref_id`. This migration performs **no**
`PlaceRef` create, delete, or mutation, and does not touch the shared
`PlaceRef` architecture.

**Applicability boundary — narrowest observable, and symmetric.** The audit
subject is the pair *(the `Shrine` pk-105 artefact + its distinctive
locality `place_ref` cache row)* — the seed creates the `PlaceRef` ~0.5 s
before the `Shrine`, so a genuinely fresh / pre-seed lineage has **neither**.

- **Forward.** pk 105 **and** `place_ref` `ChIJu0_z7giZWjURcvfBz1DO5Ac`
  **both absent** → clean no-op (genuinely fresh lineage). pk 105 absent
  **but** that `place_ref` row **present** → `RAISE`: cannot distinguish a
  fresh lineage from a partially-cleaned / manually-altered persistent state
  (a *this-migration* forward can never produce that shape — Django does not
  re-run forward — so it is out-of-band and fail-closed). pk 105 present →
  full PRE (below) → delete.
- **Reverse.** pk 105 present → `RAISE` (would overwrite). pk 105 absent
  **and** the `place_ref` row present, unclaimed → restore the artefact from
  the static snapshot and re-link. pk 105 absent **and** the `place_ref` row
  present **but claimed by another `Shrine`** → `RAISE`. pk 105 absent
  **and** the `place_ref` row **also** absent → clean no-op: this observable
  state is byte-identical whether forward was the fresh-lineage no-op or
  forward really ran and the `place_ref` was then deleted out-of-band; in
  both, the artefact staying removed is the intended end state, so reverse
  fabricates nothing (neither the `Shrine` row nor a replacement `PlaceRef`).
  *(This is a deliberate symmetric-contract choice: forward's no-op leaves
  exactly "both absent", forward's real delete leaves "pk 105 absent +
  `place_ref` present" — two distinguishable states — and the only way to
  reach "both absent" after a recorded forward is external `PlaceRef`
  deletion, for which a no-op is safe and non-fabricating.)*

`.only(...)` excludes `location` from the `Shrine` SELECT (production's
`temples_shrine.location` is a legacy `text` column while the historical
model declares a PostGIS `PointField` — a bare `.filter(...)` raises
`GEOSException`; same guard as `0091` / `0094` / `0098` / `0099` / `0100`).
Deletion is a raw `DELETE ... WHERE id = 105` (PRE has proven zero child rows
in every table, so no Python cascade is needed — and raw SQL avoids Django's
deletion collector walking a relation whose column may be absent in a given
environment, e.g. `temples_conciergehistory.shrine_id`, and is fail-closed:
an unforeseen child row raises an FK violation rather than a silent cascade).

Scope: exactly `Shrine` pk 105. No change to ids 101 / 103 / 104, id 49's
coordinate, `temples.0100` behaviour, Recommendation scoring, Need mapping,
`GoriyakuTag` mappings, `PlaceRef` architecture, or any other `Shrine`.
"""

from django.db import migrations

ARTIFACT_ID = 105
ARTIFACT_KIND = "shrine"  # audited misclassified value
ARTIFACT_NAME = "広島市"
ARTIFACT_ADDRESS = "日本、広島県広島市"
ARTIFACT_LAT = 34.3852894
ARTIFACT_LNG = 132.4553055
ARTIFACT_PLACE_REF_ID = "ChIJu0_z7giZWjURcvfBz1DO5Ac"
# the distinguishing Google-place type — the artefact is a locality, never a
# place_of_worship. A future legitimate Shrine accidentally re-using pk 105
# would carry a place_of_worship place_ref (or none), not this.
PLACE_REF_LOCALITY_TOKEN = "locality"
PLACE_REF_FORBIDDEN_TOKEN = "place_of_worship"

# `.only(...)` field set — never includes `location` (see docstring).
SHRINE_LOOKUP = (
    "id",
    "kind",
    "name_jp",
    "address",
    "latitude",
    "longitude",
    "place_ref_id",
    "history_theme",
    "goriyaku",
    "sajin",
    "description",
    "views_30d",
    "favorites_30d",
    "popular_score",
    "last_popular_calc_at",
    "owner_id",
    "updated_at",
)

# Shrine FK / relation tables to assert zero on (name -> how to count).
# `temples_like` / `temples_rankinglog` / `temples_conciergehistory` are absent
# in Production but present in the GIS migration-chain test DB — each is
# checked only if its table exists.
_RELATION_TABLES = (
    ("temples_shrinedeity", "shrine_id"),
    ("temples_shrinehistory", "shrine_id"),
    ("temples_shrine_goriyaku_tags", "shrine_id"),
    ("temples_shrine_deities", "shrine_id"),  # ORM-less legacy M2M
    ("temples_favorite", "shrine_id"),
    ("temples_visit", "shrine_id"),
    ("temples_shrinereflection", "shrine_id"),
    ("temples_goshuin", "shrine_id"),
    ("temples_shrineinteractionlog", "shrine_id"),
    ("temples_actionevent", "shrine_id"),
    ("temples_conciergethread", "main_shrine_id"),
    ("temples_like", "shrine_id"),
    ("temples_rankinglog", "shrine_id"),
    ("temples_conciergehistory", "shrine_id"),
)


class PreconditionViolation(Exception):
    """Raised by forward or reverse when the database does not match the exact
    approved P8-B PRE state. Always raised before any mutation; with
    `Migration.atomic` (default `True`) the whole `RunPython` transaction rolls
    back and 0101 is not recorded as applied."""


def _err(detail):
    return PreconditionViolation(
        "[temples.0101 P8-B] PRESTATE_MISMATCH: "
        + detail
        + " — P8-B is a fail-closed, reversible, single-row artefact removal; "
        "no repair, no guess, no partial cleanup."
    )


def _load_artifact(Shrine):
    return Shrine.objects.only(*SHRINE_LOOKUP).filter(pk=ARTIFACT_ID).first()


def _blank(value):
    return not (value or "").strip()


def _column_exists(cur, table, column):
    """True only if `table.column` exists. Some models declare a `Shrine` FK
    whose column is not present in every environment's schema (e.g.
    `temples_conciergehistory.shrine_id` in the GIS migration chain); such a
    relation cannot hold a row and is skipped."""
    cur.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s AND column_name=%s",
        [table, column],
    )
    return cur.fetchone() is not None


def _assert_all_relations_zero(schema_editor):
    with schema_editor.connection.cursor() as cur:
        for table, col in _RELATION_TABLES:
            if not _column_exists(cur, table, col):
                continue
            cur.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {col} = %s", [ARTIFACT_ID]
            )
            n = cur.fetchone()[0]
            if n:
                raise _err(
                    f"Shrine pk {ARTIFACT_ID} has {n} unexpected row(s) in {table} "
                    f"({col}) — refusing to delete an artefact that has relations "
                    "(P8-B never migrates, aggregates, or reassigns relation data)"
                )


def _place_ref_row(PlaceRef):
    return PlaceRef.objects.filter(pk=ARTIFACT_PLACE_REF_ID).first()


def _assert_artifact_identity(row):
    if row.kind != ARTIFACT_KIND:
        raise _err(f"Shrine pk {ARTIFACT_ID} kind is {row.kind!r}, expected {ARTIFACT_KIND!r}")
    if row.name_jp != ARTIFACT_NAME:
        raise _err(f"Shrine pk {ARTIFACT_ID} name_jp is {row.name_jp!r}, expected {ARTIFACT_NAME!r}")
    if row.address != ARTIFACT_ADDRESS:
        raise _err(f"Shrine pk {ARTIFACT_ID} address is {row.address!r}, expected {ARTIFACT_ADDRESS!r}")
    if row.latitude != ARTIFACT_LAT or row.longitude != ARTIFACT_LNG:
        raise _err(
            f"Shrine pk {ARTIFACT_ID} coordinate is ({row.latitude!r}, {row.longitude!r}), "
            f"expected the audited ({ARTIFACT_LAT!r}, {ARTIFACT_LNG!r}) — reverse restores "
            "exactly these static values"
        )
    if row.place_ref_id != ARTIFACT_PLACE_REF_ID:
        raise _err(
            f"Shrine pk {ARTIFACT_ID} place_ref_id is {row.place_ref_id!r}, expected "
            f"{ARTIFACT_PLACE_REF_ID!r} (the audited locality/political PlaceRef)"
        )
    if not (_blank(row.goriyaku) and _blank(row.history_theme) and _blank(row.sajin) and _blank(row.description)):
        raise _err(
            f"Shrine pk {ARTIFACT_ID} has non-empty semantic text "
            f"(goriyaku={row.goriyaku!r}, history_theme={row.history_theme!r}, "
            f"sajin={row.sajin!r}, description={row.description!r})"
        )
    if row.views_30d or row.favorites_30d or row.popular_score or row.last_popular_calc_at is not None:
        raise _err(
            f"Shrine pk {ARTIFACT_ID} has a non-zero counter "
            f"(views_30d={row.views_30d}, favorites_30d={row.favorites_30d}, "
            f"popular_score={row.popular_score}, last_popular_calc_at={row.last_popular_calc_at!r})"
        )
    if row.owner_id is not None:
        raise _err(f"Shrine pk {ARTIFACT_ID} has an owner (owner_id={row.owner_id!r})")


def _assert_place_ref_is_the_locality_artifact(PlaceRef):
    """Strict, unconditional PlaceRef type validation (P8-B F1).

    The audited artefact's Google-place must be a locality. Missing or
    malformed type evidence is **not** acceptable for a fail-closed
    deletion — `snapshot_json` must be a dict whose `types` is a list that
    contains `"locality"` and does **not** contain `"place_of_worship"`.
    Locality is never inferred from name / address / coordinates / place_ref id.
    """
    pr = _place_ref_row(PlaceRef)
    if pr is None:
        raise _err(
            f"the audited PlaceRef {ARTIFACT_PLACE_REF_ID!r} does not exist — cannot "
            "confirm Shrine pk 105 is the locality artefact"
        )
    snap = pr.snapshot_json
    if not isinstance(snap, dict):
        raise _err(
            f"PlaceRef {ARTIFACT_PLACE_REF_ID!r} snapshot_json is "
            f"{type(snap).__name__} (expected a dict with a 'types' list) — "
            "missing/malformed type evidence is not acceptable for a fail-closed delete"
        )
    types = snap.get("types")
    if not isinstance(types, list):
        raise _err(
            f"PlaceRef {ARTIFACT_PLACE_REF_ID!r} snapshot_json['types'] is "
            f"{'absent' if types is None else type(types).__name__} — expected a list "
            f"containing {PLACE_REF_LOCALITY_TOKEN!r}"
        )
    if PLACE_REF_FORBIDDEN_TOKEN in types:
        raise _err(
            f"PlaceRef {ARTIFACT_PLACE_REF_ID!r} types {types!r} include "
            f"{PLACE_REF_FORBIDDEN_TOKEN!r} — this is a place of worship, not the "
            "audited locality artefact; refusing to delete"
        )
    if PLACE_REF_LOCALITY_TOKEN not in types:
        raise _err(
            f"PlaceRef {ARTIFACT_PLACE_REF_ID!r} types {types!r} do not include "
            f"{PLACE_REF_LOCALITY_TOKEN!r} — not the audited locality artefact shape"
        )
    return pr


def _models(apps):
    return {name: apps.get_model("temples", name) for name in ("Shrine", "PlaceRef")}


def remove_artifact_forward(apps, schema_editor):
    m = _models(apps)
    Shrine = m["Shrine"]
    PlaceRef = m["PlaceRef"]

    row = _load_artifact(Shrine)
    place_ref_present = _place_ref_row(PlaceRef) is not None

    if row is None:
        # ---- applicability boundary ----
        if not place_ref_present:
            return  # genuinely fresh / pre-seed lineage: neither artefact nor its place_ref
        raise _err(
            f"Shrine pk {ARTIFACT_ID} is absent but its audited PlaceRef "
            f"{ARTIFACT_PLACE_REF_ID!r} is present — cannot distinguish a fresh lineage "
            "from a partially-cleaned / manually-altered persistent state (this "
            "migration's forward never produces that shape)"
        )

    # ---- Shrine pk 105 exists: full fail-closed PRE, then delete ----
    _assert_artifact_identity(row)
    _assert_place_ref_is_the_locality_artifact(PlaceRef)
    _assert_all_relations_zero(schema_editor)

    with schema_editor.connection.cursor() as cur:
        cur.execute("DELETE FROM temples_shrine WHERE id = %s", [ARTIFACT_ID])
    # DROP_SHRINE_LINK_ONLY: the place_ref row is intentionally left in place.


def restore_artifact_reverse(apps, schema_editor):
    m = _models(apps)
    Shrine = m["Shrine"]
    PlaceRef = m["PlaceRef"]

    existing = Shrine.objects.only("id").filter(pk=ARTIFACT_ID).first()
    pr = _place_ref_row(PlaceRef)

    if existing is None and pr is None:
        return  # forward was the fresh-lineage no-op -> nothing to restore (symmetric)

    if existing is not None:
        raise _err(
            f"reverse: Shrine pk {ARTIFACT_ID} already exists — refusing to recreate over "
            "an existing row"
        )
    if pr is None:
        raise _err(
            f"reverse: the audited PlaceRef {ARTIFACT_PLACE_REF_ID!r} is missing — cannot "
            "restore the artefact's O2O link (P8-B never deletes the PlaceRef; its absence "
            "means external tampering)"
        )
    claimed = list(
        Shrine.objects.filter(place_ref_id=ARTIFACT_PLACE_REF_ID)
        .exclude(pk=ARTIFACT_ID)
        .values_list("id", flat=True)
    )
    if claimed:
        raise _err(
            f"reverse: PlaceRef {ARTIFACT_PLACE_REF_ID!r} is already claimed by another "
            f"Shrine row {claimed} — refusing to overwrite / duplicate the O2O link"
        )

    # ---- restore exactly the audited artefact snapshot ----
    Shrine.objects.create(
        id=ARTIFACT_ID,
        kind=ARTIFACT_KIND,
        name_jp=ARTIFACT_NAME,
        address=ARTIFACT_ADDRESS,
        latitude=ARTIFACT_LAT,
        longitude=ARTIFACT_LNG,
        place_ref_id=ARTIFACT_PLACE_REF_ID,
        goriyaku="",
        sajin="",
        description="",
        history_theme="",
        location=None,  # cache column, deferred (as 0091 / 0094 / 0098 / 0099 / 0100)
    )
    # No GoriyakuTag / Knowledge / user / counter / PlaceRef creation.


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0100_p8a_duplicate_shrine_shadow_cleanup"),
    ]

    operations = [
        migrations.RunPython(remove_artifact_forward, restore_artifact_reverse),
    ]
