"""Adopt the audited Visitor / Navigation Anchor for 春日大社 (Shrine pk=5).

Position provenance and Human QA are recorded in:
docs/audit/position-audit-v2/legacy-position-provenance-batch01.md

Production currently stores the legacy-untraced coordinate
(34.6814, 135.8481). Position Audit Batch 01 adopted the traceable MapFan
Shrine POI coordinate (34.6812901, 135.8482531), corroborated independently by
the 國學院大學デジタル・ミュージアム shrine reference database, with
POSITION_STATUS=PASS.

The adopted candidate is an explicit Kasuga Taisha Shrine POI, not a parking
area, bus stop, museum, botanical garden, or other auxiliary facility, so it is
explainable as a Shrine-level representative anchor. The unresolved official
short-link recorded in the audit is not a blocking conflict because the adopted
coordinate is independently reproducible from the recorded Primary Source.

This migration is deliberately narrow and fail-closed:

* only Shrine pk=5 is eligible;
* name_jp and address must match the audited identity exactly;
* forward requires the exact audited OLD coordinate;
* reverse requires the exact adopted NEW coordinate;
* any existing-but-unexpected state raises PreconditionViolation before write;
* a genuinely absent pk=5 row is a symmetric no-op.

Production's temples_shrine.location physical column is recorded as legacy
text while the historical Django model declares a GIS field, so selecting
location can invoke a geometry converter against legacy text and fail before
mutation. As in temples.0109 and temples.0110 the only() projection therefore
excludes location, and this migration does not write it.

Scope: latitude / longitude only. No identity, address, place_ref_id, Seed,
Recommendation, Ranking, Concierge, Compass, or other Shrine data is changed.
"""

from django.db import migrations

SHRINE_ID = 5
EXPECTED_NAME = "春日大社"
EXPECTED_ADDRESS = "奈良県奈良市春日野町160"

OLD_LATITUDE = 34.6814
OLD_LONGITUDE = 135.8481
NEW_LATITUDE = 34.6812901
NEW_LONGITUDE = 135.8482531

LOOKUP_FIELDS = ("id", "name_jp", "address", "latitude", "longitude", "updated_at")


class PreconditionViolation(Exception):
    """Raised when the existing Shrine does not match the audited PRE state."""


def _load_shrine(Shrine):
    return Shrine.objects.only(*LOOKUP_FIELDS).filter(pk=SHRINE_ID).first()


def _assert_identity(shrine, *, direction):
    if shrine.name_jp != EXPECTED_NAME:
        raise PreconditionViolation(
            f"temples.0111 {direction}: Shrine pk {SHRINE_ID} name_jp is "
            f"{shrine.name_jp!r}, expected {EXPECTED_NAME!r}"
        )
    if shrine.address != EXPECTED_ADDRESS:
        raise PreconditionViolation(
            f"temples.0111 {direction}: Shrine pk {SHRINE_ID} address is "
            f"{shrine.address!r}, expected {EXPECTED_ADDRESS!r}"
        )


def _assert_coordinate(shrine, expected_lat, expected_lng, *, direction):
    if shrine.latitude != expected_lat or shrine.longitude != expected_lng:
        raise PreconditionViolation(
            f"temples.0111 {direction}: Shrine pk {SHRINE_ID} coordinate is "
            f"({shrine.latitude!r}, {shrine.longitude!r}), expected "
            f"({expected_lat!r}, {expected_lng!r}); refusing unexpected state"
        )


def adopt_kasuga_taisha_position(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _load_shrine(Shrine)
    if shrine is None:
        return

    _assert_identity(shrine, direction="forward")
    _assert_coordinate(shrine, OLD_LATITUDE, OLD_LONGITUDE, direction="forward")

    shrine.latitude = NEW_LATITUDE
    shrine.longitude = NEW_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


def revert_kasuga_taisha_position(apps, schema_editor):
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
        ("temples", "0110_adopt_fushimi_inari_position"),
    ]

    operations = [
        migrations.RunPython(adopt_kasuga_taisha_position, revert_kasuga_taisha_position),
    ]
