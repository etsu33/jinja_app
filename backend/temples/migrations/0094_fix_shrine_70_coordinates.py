"""Correct shrine_id=70 (多摩川浅間神社)'s stored latitude/longitude.

docs/audit/shrine-70-coordinate-correction.md: the previously stored
coordinates (35.5898, 139.6688) resolve to a nearby bakery
(リトルマーメイド多摩川店), roughly 250m from the actual shrine -- not the
shrine itself. `address` was always correct and is untouched here.

This migration deliberately excludes `location` from both the SELECT and
the write, mirroring the established, already-tested pattern in
0091_fill_missing_local_shrine_reason_facts.py: production's
`temples_shrine.location` column is a legacy `text` type, while every
migration's historical model state declares it as a PostGIS `PointField`
(confirmed against a restored production dump,
docs/audit/temples-0091-production-remediation.md Section 2). Selecting
`location` without `.only()` triggers Django's GeometryField converter on
the raw text value and raises GEOSException before any row is touched.
`location` resync for this row is intentionally deferred (see the
evidence doc's Section on Location Synchronization) -- the reported bug
(Shrine Detail address / Google Maps Route destination) depends only on
`latitude`/`longitude`, both of which the frontend reads directly from
the API response, never through `location`.
"""

from django.db import migrations

SHRINE_ID = 70
EXPECTED_NAME = "多摩川浅間神社"
EXPECTED_ADDRESS = "東京都大田区田園調布1-55-12"

OLD_LATITUDE = 35.5898
OLD_LONGITUDE = 139.6688
NEW_LATITUDE = 35.5875263
NEW_LONGITUDE = 139.6687549

# Excludes `location` -- see module docstring.
LOOKUP_FIELDS = ("id", "name_jp", "address", "latitude", "longitude", "updated_at")


def _target_shrine(Shrine):
    """Match by stable identity (pk), with a defensive name/address guard
    so this migration becomes a no-op (rather than touching the wrong row)
    if shrine_id=70 no longer refers to this specific shrine in a given
    environment."""
    shrine = Shrine.objects.only(*LOOKUP_FIELDS).filter(pk=SHRINE_ID).first()
    if shrine is None:
        return None
    if shrine.name_jp != EXPECTED_NAME or shrine.address != EXPECTED_ADDRESS:
        return None
    return shrine


def fix_shrine_70_coordinates(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _target_shrine(Shrine)
    if shrine is None:
        return
    shrine.latitude = NEW_LATITUDE
    shrine.longitude = NEW_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


def revert_shrine_70_coordinates(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    shrine = _target_shrine(Shrine)
    if shrine is None:
        return
    shrine.latitude = OLD_LATITUDE
    shrine.longitude = OLD_LONGITUDE
    shrine.save(update_fields=["latitude", "longitude", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("temples", "0093_shrine_knowledge_model_foundation"),
    ]

    operations = [
        migrations.RunPython(fix_shrine_70_coordinates, revert_shrine_70_coordinates),
    ]
