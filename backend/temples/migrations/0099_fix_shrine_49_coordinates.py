"""P8-C — correct Shrine id 49 (富岡八幡宮)'s stored latitude / longitude.

`docs/audit/p8-identity-coordinate-remediation.md` §10, §16 (Design A).

The stored coordinate `(35.6733, 139.7967)` is a coarse manual seed roughly
**305.6 m NW** of the shrine's real location. The verified position
`(35.6717809, 139.799519)` is Google Place `ChIJK11I4BGJGGAR5mZswigcu58`'s
`place_of_worship` geocode for 富岡八幡宮 at the 江東区 `MUNICIPAL_OFFICIAL`
address `東京都江東区富岡1-20-3` — the same value stored on the duplicate
shadow row id 104, and 6.6 m from the published Wikipedia coordinate for the
shrine. `address` was always the canonical form and is **not** touched.

**Fail-closed — `P8_C_PRESTATE_POLICY = FAIL_CLOSED`.** When Shrine pk 49
*exists*, forward mutates **only if every approved PRE condition holds
exactly**: pk 49 present, `name_jp == "富岡八幡宮"`, `address` equals the
audited canonical address, `latitude == 35.6733` **and** `longitude ==
139.7967`. Any other observed state — the corrected coordinate already
present, a third coordinate, a renamed row, an unexpected address — raises
`PreconditionViolation` **before any write**. With `Migration.atomic` left at
its Django default (`True`) the whole `RunPython` runs in one transaction, so
a raised precondition leaves the row byte-unchanged and Django does **not**
record the migration as applied. There is deliberately **no**
"already-corrected → idempotent no-op" and **no** "mismatch → successful
no-op" path (mirrors `temples.0097`'s fail-closed precondition guard,
PR #2629; and `temples.0098`).

**Applicability boundary — genuinely absent subject only.** If *no* Shrine
pk 49 row exists at all (a fresh DB, or a migration-graph run before any
Shrine seed — the condition `test_d_fresh_db_with_no_shrine_70_is_a_noop`
covers for `temples.0094`), forward **and** reverse are both clean no-ops.
This is **exactly symmetric** — there is no row, so nothing changes in either
direction and no drift can be created — and it needs no persisted state.
"pk 49 exists holding the corrected coordinate" is **not** this boundary;
that is a `PreconditionViolation`.

**Reverse — Design A coordinate ownership.** P8-C is the **only** migration
that mutates id 49's `latitude` / `longitude` (a future P8-A may *read* them
for its own fail-closed validation but must never write them). Reverse
restores `(35.6733, 139.7967)` **only** from the exact corrected pair
`(35.6717809, 139.799519)`; a renamed row, an unexpected address, the old
coordinate already present, or any third coordinate raises
`PreconditionViolation` and overwrites nothing. Reverse relies solely on the
static audited constants below — never on ephemeral forward state (a
`RunPython` local does not survive to reverse).

`.only(...)` excludes `location` from the SELECT and the write: production's
`temples_shrine.location` is a legacy `text` column while the historical
model state declares a PostGIS `PointField`, so a bare `.filter(...)` runs
Django's geometry converter on the raw text and raises `GEOSException` before
any row is touched. Same guard as `0091` / `0094`.

Scope: **exactly Shrine pk 49**, fields `latitude` / `longitude` only
(`updated_at` is carried in `update_fields` exactly as `0094` does, since the
row genuinely changed). No change to `name_jp` / `address` / `place_ref` /
`goriyaku` / `goriyaku_tags` / `ShrineDeity` / `ShrineHistory` /
`ShrineKnowledgeSource` / counters / any other `Shrine`.
"""

from django.db import migrations

SHRINE_ID = 49
EXPECTED_NAME = "富岡八幡宮"
EXPECTED_ADDRESS = "東京都江東区富岡1-20-3"

OLD_LATITUDE = 35.6733
OLD_LONGITUDE = 139.7967
NEW_LATITUDE = 35.6717809
NEW_LONGITUDE = 139.799519

# Excludes `location` -- see module docstring.
LOOKUP_FIELDS = ("id", "name_jp", "address", "latitude", "longitude", "updated_at")


class PreconditionViolation(Exception):
    """Raised when Shrine pk 49 exists but does not match the approved P8-C
    PRE state for the direction being run (identity, address, or the exact
    expected coordinate). Always raised before any write; with
    `Migration.atomic` (default `True`) the migration is not recorded as
    applied. Mirrors `temples.0097`'s fail-closed precondition guard."""


def _load_shrine(Shrine):
    """The pk-49 row, or ``None`` when the subject is genuinely absent (the
    only clean-no-op state -- see module docstring)."""
    return Shrine.objects.only(*LOOKUP_FIELDS).filter(pk=SHRINE_ID).first()


def _assert_identity(shrine, *, direction):
    if shrine.name_jp != EXPECTED_NAME:
        raise PreconditionViolation(
            f"temples.0099 {direction}: Shrine pk {SHRINE_ID} name_jp is "
            f"{shrine.name_jp!r}, expected {EXPECTED_NAME!r} -- refusing to touch the wrong row"
        )
    if shrine.address != EXPECTED_ADDRESS:
        raise PreconditionViolation(
            f"temples.0099 {direction}: Shrine pk {SHRINE_ID} address is "
            f"{shrine.address!r}, expected {EXPECTED_ADDRESS!r} -- unexpected identity"
        )


def _assert_coordinate(shrine, expected_lat, expected_lng, *, direction):
    if shrine.latitude != expected_lat or shrine.longitude != expected_lng:
        raise PreconditionViolation(
            f"temples.0099 {direction}: Shrine pk {SHRINE_ID} coordinate is "
            f"({shrine.latitude!r}, {shrine.longitude!r}), expected "
            f"({expected_lat!r}, {expected_lng!r}) -- fail-closed, no silent skip"
        )


def fix_shrine_49_coordinates(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _load_shrine(Shrine)
    if shrine is None:
        return  # genuinely absent subject -> symmetric no-op (see module docstring)
    _assert_identity(shrine, direction="forward")
    _assert_coordinate(shrine, OLD_LATITUDE, OLD_LONGITUDE, direction="forward")
    shrine.latitude = NEW_LATITUDE
    shrine.longitude = NEW_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


def revert_shrine_49_coordinates(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _load_shrine(Shrine)
    if shrine is None:
        return  # genuinely absent subject -> symmetric no-op
    _assert_identity(shrine, direction="reverse")
    _assert_coordinate(shrine, NEW_LATITUDE, NEW_LONGITUDE, direction="reverse")
    shrine.latitude = OLD_LATITUDE
    shrine.longitude = OLD_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0098_remove_stray_test_source_id1"),
    ]

    operations = [
        migrations.RunPython(fix_shrine_49_coordinates, revert_shrine_49_coordinates),
    ]
