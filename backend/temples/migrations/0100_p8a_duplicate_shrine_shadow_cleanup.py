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

**Applicability boundary — narrow, and identical in both directions (proven
symmetric).** The *only* clean no-op is a genuinely fresh / pre-seed lineage
in which the **entire audited P8-A subject is absent**:

- shadow pk 101, 103, 104 all absent, **and**
- primary pk 21, 22, 49 all absent, **and**
- neither audited interaction-log event exists **anywhere** (searched
  globally by `user_id` + `action_type` + `metadata.ctx` + exact
  `created_at`, not scoped to a shrine).

Any other state is `FAIL_CLOSED`:

- **Forward.** All shadows absent **but** any primary present → `RAISE`
  ("primaries-only" is not a fresh lineage and not a successful no-op). All
  shadows absent **but** an audited interaction event exists anywhere →
  `RAISE` (a successful no-op must not mask previously-moved or
  manually-altered state). All three shadows present → full PRE. A partial
  shadow set → `RAISE`.
- **Reverse.** Not the fresh boundary ⇒ the full audited post-forward shape
  must be *exactly* present: all three primaries present with their audited
  `name_jp` / `address`, id 49 at the P8-C-corrected coordinate, all three
  shadows absent, and **exactly one** audited moved interaction-log row on
  each of primary 22 / 21 (with none left on the original shadow). A missing
  or renamed primary, a wrong id 49 coordinate, a partial primary set, a
  missing/duplicated moved log, or an occupied shadow pk each `RAISE` — never
  a successful no-op (which would let Django unrecord 0100 while leaving the
  shadows deleted and the logs moved).

This is exactly symmetric: forward and reverse use the **same** fresh-lineage
predicate (shadows + primaries + audited events all absent), so the only
state where both no-op is the genuine fresh lineage; after a real forward the
post-forward shape is unambiguous and reverse fully restores.

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
PRIMARY_PKS = [p["primary_pk"] for p in PAIRS]
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


def _audited_logs_matching(ShrineInteractionLog, spec, *, shrine_id=None):
    """Every `ShrineInteractionLog` matching the stable audited predicate
    (`user_id` + `action_type` + `metadata.ctx` + exact `created_at`).

    `shrine_id=None` searches **globally** (used for fresh-lineage boundary
    detection — an audited event existing *anywhere* means the subject is not
    genuinely absent). Pass `shrine_id` to scope to one shrine.
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
    return any(
        _audited_logs_matching(ShrineInteractionLog, pair["il"])
        for pair in PAIRS
        if pair["il"] is not None
    )


def _present_pks(Shrine, pks):
    return [pk for pk in pks if Shrine.objects.filter(pk=pk).exists()]


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

    existing_shadows = _present_pks(Shrine, SHADOW_PKS)
    existing_primaries = _present_pks(Shrine, PRIMARY_PKS)
    audited_log_anywhere = _any_audited_log_anywhere(ShrineInteractionLog)

    if not existing_shadows:
        # Candidate for the ONLY clean no-op: a genuinely fresh / pre-seed
        # lineage where the ENTIRE audited P8-A subject is absent. "Primaries
        # only" (or any lingering audited interaction event) is NOT a
        # successful no-op — P8_A_PRESTATE_POLICY = FAIL_CLOSED.
        if existing_primaries:
            raise _err(
                f"no shadow rows present, but canonical primaries "
                f"{sorted(existing_primaries)} exist — 'primaries-only' is not a fresh "
                "lineage and not a successful no-op (a fresh lineage has shadows AND "
                "primaries AND both audited interaction events all absent)"
            )
        if audited_log_anywhere:
            raise _err(
                "no shadow rows present, but an audited interaction-log event exists "
                "somewhere (user_id + action_type + metadata.ctx + exact created_at) — "
                "refusing a successful no-op that would mask previously-moved or "
                "manually-altered state"
            )
        return  # genuinely fresh lineage: full audited subject absent -> clean no-op

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

    shadows_present = _present_pks(Shrine, SHADOW_PKS)
    primaries = {pk: _load_shrine(Shrine, pk) for pk in PRIMARY_PKS}
    primaries_present = [pk for pk, row in primaries.items() if row is not None]
    audited_log_anywhere = _any_audited_log_anywhere(ShrineInteractionLog)

    # ---- The ONLY clean no-op: a genuinely fresh / pre-seed lineage where the
    #      ENTIRE audited P8-A subject is absent (shadows AND primaries AND both
    #      audited interaction events). Anything else is FAIL_CLOSED. ----
    if not shadows_present and not primaries_present and not audited_log_anywhere:
        return

    # ---- FAIL_CLOSED reverse: the full audited post-forward state must be
    #      *exactly* present. A renamed / missing primary, a wrong id 49
    #      coordinate, a partial primary set, or a missing moved log all RAISE
    #      (never a successful no-op that would let Django unrecord 0100 while
    #      leaving shadows deleted and logs moved). ----
    for pair in PAIRS:
        _assert_primary_identity(primaries[pair["primary_pk"]], pair["primary"])
    _assert_primary_49_coordinate(primaries[49])

    if shadows_present:
        raise _err(
            f"reverse: shadow pk(s) {sorted(shadows_present)} already exist — refusing to "
            "recreate over an existing row (expected the post-forward shape: all shadows absent)"
        )

    # exactly one audited moved log on each of primary 22 / 21
    moved = {}
    for pair in PAIRS:
        if pair["il"] is None:
            continue
        moved[pair["shadow_pk"]] = _audited_logs_matching(
            ShrineInteractionLog, pair["il"], shrine_id=pair["primary_pk"]
        )
    n_moved = {k: len(v) for k, v in moved.items()}
    if any(v != 1 for v in n_moved.values()):
        raise _err(
            "reverse: expected exactly one audited moved interaction-log row on each of "
            f"primaries 22 / 21 (post-forward shape), found {n_moved} — cannot restore"
        )
    # and neither audited event may still exist on its original shadow
    for pair in PAIRS:
        if pair["il"] is None:
            continue
        stray = _audited_logs_matching(
            ShrineInteractionLog, pair["il"], shrine_id=pair["shadow_pk"]
        )
        if stray:
            raise _err(
                f"reverse: audited interaction event still present on shadow pk "
                f"{pair['shadow_pk']} — inconsistent with a completed forward"
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
    # (id 49's coordinate was already asserted == the P8-C-corrected value above;
    #  reverse never writes it — Design A: temples.0099 owns id 49's coordinate.)

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
