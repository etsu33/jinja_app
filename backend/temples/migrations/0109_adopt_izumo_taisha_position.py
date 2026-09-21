"""Adopt the audited Visitor / Navigation Anchor for 出雲大社 (Shrine pk=4).

Position provenance and Human QA are recorded in:
docs/audit/position-audit-v2/legacy-position-provenance-batch01.md

Production currently stores the legacy-untraced coordinate
(35.4016, 132.6853). Position Audit Batch 01 adopted the traceable Mapion
Shrine POI coordinate (35.40190463, 132.68547534), corroborated independently
by MapFan, with POSITION_STATUS=PASS.

This migration is deliberately narrow and fail-closed:

* only Shrine pk=4 is eligible;
* name_jp and address must match the audited identity exactly;
* forward requires the exact audited OLD coordinate;
* reverse requires the exact adopted NEW coordinate;
* any existing-but-unexpected state raises PreconditionViolation before write;
* a genuinely absent pk=4 row is a symmetric no-op.

Production's temples_shrine.location physical column was re-verified on
2026-09-21 as data_type=text / udt_name=text. The historical Django model
declares a GIS field, so selecting location can invoke a geometry converter
against legacy text and fail before mutation. The only() projection therefore
excludes location, and this migration does not write it.

Scope: latitude / longitude only. No identity, address, Seed, Recommendation,
Ranking, Concierge, Compass, or other Shrine data is changed.
"""

from django.db import migrations

SHRINE_ID = 4
EXPECTED_NAME = "出雲大社"
EXPECTED_ADDRESS = "島根県出雲市大社町杵築東195"

OLD_LATITUDE = 35.4016
OLD_LONGITUDE = 132.6853
NEW_LATITUDE = 35.40190463
NEW_LONGITUDE = 132.68547534

LOOKUP_FIELDS = ("id", "name_jp", "address", "latitude", "longitude", "updated_at")


class PreconditionViolation(Exception):
    """Raised when the existing Shrine does not match the audited PRE state."""


def _load_shrine(Shrine):
    return Shrine.objects.only(*LOOKUP_FIELDS).filter(pk=SHRINE_ID).first()


def _assert_identity(shrine, *, direction):
    if shrine.name_jp != EXPECTED_NAME:
        raise PreconditionViolation(
            f"temples.0109 {direction}: Shrine pk {SHRINE_ID} name_jp is "
            f"{shrine.name_jp!r}, expected {EXPECTED_NAME!r}"
        )
    if shrine.address != EXPECTED_ADDRESS:
        raise PreconditionViolation(
            f"temples.0109 {direction}: Shrine pk {SHRINE_ID} address is "
            f"{shrine.address!r}, expected {EXPECTED_ADDRESS!r}"
        )


def _assert_coordinate(shrine, expected_lat, expected_lng, *, direction):
    if shrine.latitude != expected_lat or shrine.longitude != expected_lng:
        raise PreconditionViolation(
            f"temples.0109 {direction}: Shrine pk {SHRINE_ID} coordinate is "
            f"({shrine.latitude!r}, {shrine.longitude!r}), expected "
            f"({expected_lat!r}, {expected_lng!r}); refusing unexpected state"
        )


def adopt_izumo_taisha_position(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _load_shrine(Shrine)
    if shrine is None:
        return

    _assert_identity(shrine, direction="forward")
    _assert_coordinate(shrine, OLD_LATITUDE, OLD_LONGITUDE, direction="forward")

    shrine.latitude = NEW_LATITUDE
    shrine.longitude = NEW_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


def revert_izumo_taisha_position(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _load_shrine(Shrine)
    if shrine is None:
        return

    _assert_identity(shrine, direction="reverse")
    _assert_coordinate(shrine, NEW_LATITUDE, NEW_LONGITUDE, direction="reverse")

    shrine.latitude = OLD_LATITUDE
    shrine.longitude = OLD_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("temples", "0108_remove_legacy_temples_models"),
    ]

    operations = [
        migrations.RunPython(adopt_izumo_taisha_position, revert_izumo_taisha_position),
    ]
