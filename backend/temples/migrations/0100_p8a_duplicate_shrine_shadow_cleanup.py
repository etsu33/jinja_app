"""P8-A — remove the three audited duplicate *shadow* Shrine rows.

`docs/audit/p8-identity-coordinate-remediation.md` §6-§8, §11-§14, §16-§19.

Three `place_ref`-only, zero-payload shadow rows are byte-for-byte (101/103)
or normalized (104) duplicates of a canonical primary and are removed here:

    shadow 101  ->  primary 22  (給田六所神社)
    shadow 103  ->  primary 21  (長太稲荷神社)
    shadow 104  ->  primary 49  (富岡八幡宮)

Two audited `ShrineInteractionLog` rows (operator `user_id=1`,
`action_type=detail_view`, `metadata.ctx=map`, created ~4 s after the shadow
rows during the map-resolve workflow) are **moved** to their primary before
deletion — `P8_USER_DATA_POLICY = MOVE_TO_PRIMARY`:

    il on shadow 101  ->  shrine_id 22
    il on shadow 103  ->  shrine_id 21

Mother Ship decisions (fixed): `P8_101_ACTION=REMOVE_SHADOW_TO_22`,
`P8_103_ACTION=REMOVE_SHADOW_TO_21`, `P8_104_ACTION=REMOVE_SHADOW_TO_49`,
`P8_USER_DATA_POLICY=MOVE_TO_PRIMARY`, `P8_COUNTER_POLICY=PRIMARY_ONLY`
(shadow counters are audited zero — never summed), `P8_DELIVERY=SPLIT_MIGRATIONS`,
`P8_A_PRESTATE_POLICY=FAIL_CLOSED`, `P8_C_DELIVERY_DESIGN=DESIGN_A_INDEPENDENT_P8C`.

**Design A coordinate ownership.** `temples.0099` (P8-C) is the ONLY migration
that mutates Shrine id 49's `latitude` / `longitude`. This migration **reads**
id 49's coordinate as a fail-closed PRE (it must already be the P8-C-corrected
`35.6717809, 139.799519`) and **never** writes it — not in forward, not in
reverse. If id 49 still holds the pre-P8-C value `35.6733, 139.7967`, 0099 has
not run in this lineage and P8-A raises (deploy order is
`0095 → 0096 → 0097 → 0098 → 0099 → 0100`).

**`P8_A_PRESTATE_POLICY = FAIL_CLOSED` — one atomic remediation unit.** No
mutation begins until every PRE condition for all three pairs *and* the
audited interaction-log state is verified. A failure on any PRE raises
`PreconditionViolation`; with `Migration.atomic` at its Django default
(`True`) the whole `RunPython` runs in one transaction, so nothing is
mutated and 0100 is not recorded as applied. There is no "repair", no
"guess", and no partial cleanup of one pair while another fails.

**Applicability boundary (proven symmetric — the only clean no-op).** A fresh
database / a migration-graph run before any `Shrine` seed has none of the
shadow rows.

- **Forward:** if none of pk 101 / 103 / 104 exist → clean no-op (the audited
  subject is genuinely absent). If **any** shadow row exists, all three must
  exist and the full fail-closed PRE applies.
- **Reverse:** decides *only* from observable state whether forward did the
  real work — the sole signal is the two moved interaction-log rows now on
  primaries 22 / 21 (exact `user_id` + `action_type` + `ctx` + `created_at`).
  If primaries 21 / 22 / 49 are not all present with their audited identity →
  clean no-op (fresh DB). If they are present but **no** moved il row is
  found and all shadows are absent → clean no-op (forward was a boundary
  no-op — there is nothing to restore). If **both** moved il rows are found
  and all shadows are absent → full restore. Any in-between (one il row, an
  unexpected count, a shadow pk already occupied) → `PreconditionViolation`.

This is exactly symmetric: the boundary no-op is reachable only when the
shadow rows are genuinely absent, and reverse can always tell "forward
mutated" (two il rows moved onto primaries) from "forward no-op'd" (no moved
il rows) purely from the database — no migration-owned persisted state.

**Reverse restoration** is from a static audited snapshot embedded below
(never from ephemeral `RunPython` forward state). It recreates the three
shadow rows at their original pks with their audited identity + coordinate +
`place_ref_id`, then moves the two il rows back. `Shrine.location` is not
restored (a cache column; deferred exactly as in `0091` / `0094` / `0098` /
`0099`).

**`place_ref` on the shadows: `DROP_SHADOW_ONLY`.** The audit only defines a
`place_ref` *transfer* to a primary as conditional on an explicit Mother Ship
decision, and none selects it. Deleting a shadow row simply orphans its
`place_ref` cache row (no FK points from `place_ref` back to `Shrine`);
reverse re-links the same `place_ref_id`. This migration performs **no**
`place_ref` merge.

`.only(...)` excludes `location` from every SELECT: production's
`temples_shrine.location` is a legacy `text` column while the historical model
declares a PostGIS `PointField`, so a bare `.filter(...)` raises
`GEOSException` before any row is touched (same guard as `0091` / `0094` /
`0098` / `0099`).

Scope: exactly shadow Shrine rows 101 / 103 / 104 and the two audited
`ShrineInteractionLog` rows. No change to primaries 21 / 22 / 49 (identity,
coordinate, `goriyaku`, `goriyaku_tags`, `ShrineDeity` / `ShrineHistory` /
`ShrineKnowledgeSource`), no id 105 change, no Recommendation / scoring code,
no counter aggregation, no other Shrine.
"""

from datetime import datetime

from django.db import migrations

SHRINE_LOOKUP = (
    "id",
    "name_jp",
    "address",
    "latitude",
    "longitude",
    "place_ref_id",
    "history_theme",
    "goriyaku",
    "views_30d",
    "favorites_30d",
    "popular_score",
    "last_popular_calc_at",
    "updated_at",
)

# P8-C (temples.0099) corrected value for Shrine id 49 — READ here, never written.
PRIMARY_49_CORRECTED_COORD = (35.6717809, 139.799519)
PRIMARY_49_PRE_P8C_COORD = (35.6733, 139.7967)

# --- Static audited snapshot (docs/audit/p8-identity-coordinate-remediation.md
# §3.1-§3.5, re-confirmed by a read-only Production PRE read for this PR). ---
PAIRS = [
    {
        "shadow_pk": 101,
        "primary_pk": 22,
        "shadow": {
            "id": 101,
            "kind": "shrine",
            "name_jp": "給田六所神社",
            "address": "日本、〒157-0064 東京都世田谷区給田１丁目３−７",
            "latitude": 35.662443,
            "longitude": 139.5920237,
            "place_ref_id": "ChIJl-MEepfxGGAR1Eo44p__GaE",
        },
        "primary": {
            "id": 22,
            "name_jp": "給田六所神社",
            "address": "日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        },
        "il": {
            "user_id": 1,
            "action_type": "detail_view",
            "ctx": "map",
            "created_at": "2026-06-11T07:18:05.580624+00:00",
        },
    },
    {
        "shadow_pk": 103,
        "primary_pk": 21,
        "shadow": {
            "id": 103,
            "kind": "shrine",
            "name_jp": "長太稲荷神社",
            "address": "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
            "latitude": 35.660614,
            "longitude": 139.6017688,
            "place_ref_id": "ChIJX19mq8nxGGARsA2kP4gX90M",
        },
        "primary": {
            "id": 21,
            "name_jp": "長太稲荷神社",
            "address": "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        },
        "il": {
            "user_id": 1,
            "action_type": "detail_view",
            "ctx": "map",
            "created_at": "2026-06-11T08:00:22.085501+00:00",
        },
    },
    {
        "shadow_pk": 104,
        "primary_pk": 49,
        "shadow": {
            "id": 104,
            "kind": "shrine",
            "name_jp": "富岡八幡宮",
            "address": "日本、〒135-0047 東京都江東区富岡１丁目２０−３",
            "latitude": 35.6717809,
            "longitude": 139.799519,
            "place_ref_id": "ChIJK11I4BGJGGAR5mZswigcu58",
        },
        "primary": {
            "id": 49,
            "name_jp": "富岡八幡宮",
            "address": "東京都江東区富岡1-20-3",
        },
        "il": None,  # id 104 has no audited user-owned row
    },
]

SHADOW_PKS = [p["shadow_pk"] for p in PAIRS]
SHADOW_PLACE_REF_IDS = [p["shadow"]["place_ref_id"] for p in PAIRS]


class PreconditionViolation(Exception):
    """Raised by forward or reverse when the database does not match the exact
    approved P8-A PRE state. Always raised before any mutation; with
    `Migration.atomic` (default `True`) the whole `RunPython` transaction rolls
    back and 0100 is not recorded as applied. Mirrors the fail-closed guard of
    `temples.0097` / `0098` / `0099`."""


def _err(detail):
    return PreconditionViolation(
        "[temples.0100 P8-A] PRESTATE_MISMATCH: "
        + detail
        + " — P8_A_PRESTATE_POLICY = FAIL_CLOSED: one atomic remediation unit, "
        "no repair, no guess, no partial cleanup."
    )


def _parse_ts(value):
    return datetime.fromisoformat(value)


def _blank(value):
    return not (value or "").strip()


def _meta_ctx(row):
    meta = row.metadata if isinstance(row.metadata, dict) else {}
    return meta.get("ctx")


def _load_shrine(Shrine, pk):
    return Shrine.objects.only(*SHRINE_LOOKUP).filter(pk=pk).first()


def _assert_shadow_identity(shadow_row, snap):
    pk = snap["id"]
    if shadow_row.name_jp != snap["name_jp"]:
        raise _err(f"shadow pk {pk} name_jp is {shadow_row.name_jp!r}, expected {snap['name_jp']!r}")
    if shadow_row.address != snap["address"]:
        raise _err(f"shadow pk {pk} address is {shadow_row.address!r}, expected {snap['address']!r}")
    if shadow_row.latitude != snap["latitude"] or shadow_row.longitude != snap["longitude"]:
        raise _err(
            f"shadow pk {pk} coordinate is ({shadow_row.latitude!r}, {shadow_row.longitude!r}), "
            f"expected ({snap['latitude']!r}, {snap['longitude']!r})"
        )
    if shadow_row.place_ref_id != snap["place_ref_id"]:
        raise _err(
            f"shadow pk {pk} place_ref_id is {shadow_row.place_ref_id!r}, "
            f"expected {snap['place_ref_id']!r}"
        )


def _assert_primary_identity(primary_row, prim):
    pk = prim["id"]
    if primary_row is None:
        raise _err(f"canonical primary pk {pk} is missing")
    if primary_row.name_jp != prim["name_jp"]:
        raise _err(f"primary pk {pk} name_jp is {primary_row.name_jp!r}, expected {prim['name_jp']!r}")
    if primary_row.address != prim["address"]:
        raise _err(f"primary pk {pk} address is {primary_row.address!r}, expected {prim['address']!r}")


def _assert_primary_49_coordinate(primary_49):
    got = (primary_49.latitude, primary_49.longitude)
    if got == PRIMARY_49_CORRECTED_COORD:
        return
    if got == PRIMARY_49_PRE_P8C_COORD:
        raise _err(
            "Shrine id 49 still holds the pre-P8-C coordinate (35.6733, 139.7967) — "
            "temples.0099 (P8-C) has not run in this lineage. Deploy order is "
            "0095 -> 0096 -> 0097 -> 0098 -> 0099 -> 0100. P8-A never applies the "
            "coordinate correction itself (Design A: 0099 owns id 49's coordinate)"
        )
    raise _err(
        f"Shrine id 49 coordinate is {got!r}, expected the P8-C-corrected "
        f"{PRIMARY_49_CORRECTED_COORD!r} (READ-only PRE; P8-A never writes it)"
    )


def _legacy_shrine_deities_count(schema_editor, shadow_pk):
    """Rows in the ORM-less legacy `temples_shrine_deities` M2M table for a
    shadow (audited 0 everywhere). Returns 0 if the table is absent."""
    with schema_editor.connection.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='temples_shrine_deities'"
        )
        if cur.fetchone() is None:
            return 0
        cur.execute(
            "SELECT COUNT(*) FROM temples_shrine_deities WHERE shrine_id = %s", [shadow_pk]
        )
        return cur.fetchone()[0]


def _assert_shadow_zero_payload(models_, schema_editor, shadow_row):
    Shrine = models_["Shrine"]
    ShrineDeity = models_["ShrineDeity"]
    ShrineHistory = models_["ShrineHistory"]
    Favorite = models_["Favorite"]
    Visit = models_["Visit"]
    ShrineReflection = models_["ShrineReflection"]
    Goshuin = models_["Goshuin"]
    ActionEvent = models_["ActionEvent"]
    ConciergeThread = models_["ConciergeThread"]
    pk = shadow_row.id

    # semantic payload
    if not _blank(shadow_row.goriyaku):
        raise _err(f"shadow pk {pk} has non-empty goriyaku {shadow_row.goriyaku!r}")
    if not _blank(shadow_row.history_theme):
        raise _err(f"shadow pk {pk} has non-empty history_theme {shadow_row.history_theme!r}")
    reload_with_m2m = Shrine.objects.only("id").filter(pk=pk).first()  # .only() -> no `location`
    if reload_with_m2m.goriyaku_tags.exists():
        raise _err(f"shadow pk {pk} has goriyaku_tags (expected none)")
    for model, label in ((ShrineDeity, "ShrineDeity"), (ShrineHistory, "ShrineHistory")):
        n = model.objects.filter(shrine_id=pk).count()
        if n:
            raise _err(f"shadow pk {pk} has {n} {label} row(s) (expected 0)")
    if _legacy_shrine_deities_count(schema_editor, pk):
        raise _err(f"shadow pk {pk} has legacy temples_shrine_deities rows (expected 0)")

    # user-owned references (Production-present Shrine FK tables)
    for qs, label in (
        (Favorite.objects.filter(shrine_id=pk), "Favorite"),
        (Visit.objects.filter(shrine_id=pk), "Visit"),
        (ShrineReflection.objects.filter(shrine_id=pk), "ShrineReflection"),
        (Goshuin.objects.filter(shrine_id=pk), "Goshuin"),
        (ActionEvent.objects.filter(shrine_id=pk), "ActionEvent"),
        (ConciergeThread.objects.filter(main_shrine_id=pk), "ConciergeThread.main_shrine"),
    ):
        n = qs.count()
        if n:
            raise _err(
                f"shadow pk {pk} has {n} unexpected {label} row(s) — refusing to "
                "cascade-delete user-owned data (P8_A_PRESTATE_POLICY = FAIL_CLOSED)"
            )

    # counters (P8_COUNTER_POLICY = PRIMARY_ONLY — shadow counters are audited 0
    # and are never summed into a primary; a non-zero here is unexpected state).
    if (
        shadow_row.views_30d
        or shadow_row.favorites_30d
        or shadow_row.popular_score
        or shadow_row.last_popular_calc_at is not None
    ):
        raise _err(
            f"shadow pk {pk} has a non-zero counter "
            f"(views_30d={shadow_row.views_30d}, favorites_30d={shadow_row.favorites_30d}, "
            f"popular_score={shadow_row.popular_score}, "
            f"last_popular_calc_at={shadow_row.last_popular_calc_at!r}) — P8-A does not "
            "aggregate counters"
        )


def _audited_il_or_error(ShrineInteractionLog, shadow_pk, spec):
    """The single audited interaction-log row on a shadow, or raise.

    Requires exactly one `ShrineInteractionLog` for the shadow and that it
    matches the audited semantic predicate (user_id + action_type + ctx +
    exact created_at) — an extra/missing/mismatched row is fail-closed.
    """
    rows = list(ShrineInteractionLog.objects.filter(shrine_id=shadow_pk))
    if len(rows) != 1:
        raise _err(
            f"shadow pk {shadow_pk} has {len(rows)} ShrineInteractionLog row(s), "
            "expected exactly 1 audited row"
        )
    row = rows[0]
    want_ts = _parse_ts(spec["created_at"])
    if (
        row.user_id != spec["user_id"]
        or row.action_type != spec["action_type"]
        or _meta_ctx(row) != spec["ctx"]
        or row.created_at != want_ts
    ):
        raise _err(
            f"shadow pk {shadow_pk} ShrineInteractionLog pk {row.pk} does not match the "
            f"audited predicate (user_id={spec['user_id']}, action_type={spec['action_type']!r}, "
            f"metadata.ctx={spec['ctx']!r}, created_at={want_ts.isoformat()}): got "
            f"user_id={row.user_id}, action_type={row.action_type!r}, ctx={_meta_ctx(row)!r}, "
            f"created_at={row.created_at.isoformat()}"
        )
    return row


def _models(apps):
    return {
        name: apps.get_model("temples", name)
        for name in (
            "Shrine",
            "ShrineDeity",
            "ShrineHistory",
            "ShrineKnowledgeSource",
            "ShrineInteractionLog",
            "Favorite",
            "Visit",
            "ShrineReflection",
            "Goshuin",
            "ActionEvent",
            "ConciergeThread",
            "PlaceRef",
        )
    }


def cleanup_forward(apps, schema_editor):
    m = _models(apps)
    Shrine = m["Shrine"]
    ShrineInteractionLog = m["ShrineInteractionLog"]

    existing_shadows = [pk for pk in SHADOW_PKS if Shrine.objects.filter(pk=pk).exists()]
    if not existing_shadows:
        return  # applicability boundary: audited subject genuinely absent -> clean no-op

    if len(existing_shadows) != len(SHADOW_PKS):
        raise _err(
            f"partial shadow set present: {sorted(existing_shadows)} of {SHADOW_PKS} — "
            "P8-A is one atomic remediation unit, refusing to run against a partial state"
        )

    # ---- Phase 1: validate every PRE (no mutation) ----
    matched_il = {}
    for pair in PAIRS:
        shadow_row = _load_shrine(Shrine, pair["shadow_pk"])
        _assert_shadow_identity(shadow_row, pair["shadow"])

        primary_row = _load_shrine(Shrine, pair["primary_pk"])
        _assert_primary_identity(primary_row, pair["primary"])
        if pair["primary_pk"] == 49:
            _assert_primary_49_coordinate(primary_row)

        _assert_shadow_zero_payload(m, schema_editor, shadow_row)

        if pair["il"] is None:
            n = ShrineInteractionLog.objects.filter(shrine_id=pair["shadow_pk"]).count()
            if n:
                raise _err(
                    f"shadow pk {pair['shadow_pk']} has {n} ShrineInteractionLog row(s), "
                    "expected 0 (no audited user-owned data)"
                )
        else:
            matched_il[pair["shadow_pk"]] = _audited_il_or_error(
                ShrineInteractionLog, pair["shadow_pk"], pair["il"]
            )

    # ---- Phase 2: mutate (reached only if every PRE passed) ----
    for pair in PAIRS:
        if pair["il"] is None:
            continue
        il_row = matched_il[pair["shadow_pk"]]
        ShrineInteractionLog.objects.filter(pk=il_row.pk).update(shrine_id=pair["primary_pk"])

    # Raw DELETE by pk. PRE has proven every shadow has zero child rows in every
    # table, so this needs no Python cascade — and using raw SQL (a) avoids
    # Django's deletion collector walking model relations whose column may not
    # exist in a given environment (e.g. `temples_conciergehistory.shrine_id`),
    # and (b) is fail-closed: an unforeseen child row raises an FK violation
    # rather than being silently cascade-deleted.
    with schema_editor.connection.cursor() as cur:
        for pk in SHADOW_PKS:
            cur.execute("DELETE FROM temples_shrine WHERE id = %s", [pk])


def cleanup_reverse(apps, schema_editor):
    m = _models(apps)
    Shrine = m["Shrine"]
    ShrineInteractionLog = m["ShrineInteractionLog"]
    PlaceRef = m["PlaceRef"]

    # primaries present with audited identity?
    primaries = {}
    for pair in PAIRS:
        primaries[pair["primary_pk"]] = _load_shrine(Shrine, pair["primary_pk"])
    primaries_ok = True
    for pair in PAIRS:
        row = primaries[pair["primary_pk"]]
        if row is None or row.name_jp != pair["primary"]["name_jp"] or row.address != pair["primary"]["address"]:
            primaries_ok = False
            break
    if not primaries_ok:
        return  # fresh DB / primaries absent -> nothing to restore (symmetric no-op)

    # find the two moved interaction-log rows on the primaries
    moved = {}
    for pair in PAIRS:
        if pair["il"] is None:
            continue
        want_ts = _parse_ts(pair["il"]["created_at"])
        rows = [
            r
            for r in ShrineInteractionLog.objects.filter(
                shrine_id=pair["primary_pk"],
                user_id=pair["il"]["user_id"],
                action_type=pair["il"]["action_type"],
                created_at=want_ts,
            )
            if _meta_ctx(r) == pair["il"]["ctx"]
        ]
        moved[pair["shadow_pk"]] = rows

    shadows_present = [pk for pk in SHADOW_PKS if Shrine.objects.filter(pk=pk).exists()]
    n_moved = {k: len(v) for k, v in moved.items()}

    if all(v == 0 for v in n_moved.values()) and not shadows_present:
        return  # forward was a boundary no-op -> nothing to restore (symmetric)

    if any(v != 1 for v in n_moved.values()):
        raise _err(
            f"reverse: expected exactly one moved interaction-log row per audited shadow, "
            f"found {n_moved} on primaries 22/21 — ambiguous, refusing to guess"
        )
    if shadows_present:
        raise _err(
            f"reverse: shadow pk(s) {sorted(shadows_present)} already exist — refusing to "
            "recreate over an existing row"
        )

    # ---- fail-closed reverse PRE for the full-restore path ----
    if PlaceRef.objects.filter(pk__in=SHADOW_PLACE_REF_IDS).count() != len(SHADOW_PLACE_REF_IDS):
        raise _err(
            "reverse: one or more audited shadow place_ref rows no longer exist in "
            f"`place_ref` ({SHADOW_PLACE_REF_IDS}); cannot restore the shadow O2O link"
        )
    claimed = list(
        Shrine.objects.filter(place_ref_id__in=SHADOW_PLACE_REF_IDS).values_list(
            "id", "place_ref_id"
        )
    )
    if claimed:
        raise _err(
            f"reverse: shadow place_ref id(s) are already claimed by another Shrine row: "
            f"{claimed}"
        )
    p49 = primaries[49]
    if (p49.latitude, p49.longitude) != PRIMARY_49_CORRECTED_COORD:
        raise _err(
            f"reverse: Shrine id 49 coordinate is {(p49.latitude, p49.longitude)!r}, expected "
            f"the P8-C-corrected {PRIMARY_49_CORRECTED_COORD!r} — reverse does not touch id 49's "
            "coordinate and will not restore into an inconsistent state"
        )

    # ---- restore: recreate the three shadow rows from the static snapshot ----
    for pair in PAIRS:
        snap = pair["shadow"]
        Shrine.objects.create(
            id=snap["id"],
            kind=snap["kind"],
            name_jp=snap["name_jp"],
            address=snap["address"],
            latitude=snap["latitude"],
            longitude=snap["longitude"],
            place_ref_id=snap["place_ref_id"],
            location=None,  # cache column, deferred (as 0091 / 0094 / 0098 / 0099)
        )

    # ---- move the two interaction-log rows back to their original shadow ----
    for pair in PAIRS:
        if pair["il"] is None:
            continue
        il_row = moved[pair["shadow_pk"]][0]
        ShrineInteractionLog.objects.filter(pk=il_row.pk).update(shrine_id=pair["shadow_pk"])


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0099_fix_shrine_49_coordinates"),
    ]

    operations = [
        migrations.RunPython(cleanup_forward, cleanup_reverse),
    ]
