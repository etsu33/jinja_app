# backend/temples/tests/test_gis_knowledge_seed_shrine_identity.py
"""Regression test: `temples.services.knowledge_seed.resolve_shrine` must not
raise GEOSException under the confirmed production schema drift.

Production's `temples_shrine.location` column is a legacy `text` field, but
the live `Shrine` model declares it as a PostGIS `PointField` (see
docs/audit/temples-0091-production-remediation.md for how this was first
found and fixed for migration 0091). `resolve_shrine` initially repeated the
same mistake — a `Shrine.objects.filter(name_jp=...)` with no `.only()`
selects every column, including `location`, and crashes on the drifted
value. This was caught by running the real `import_shrine_knowledge` command
against a restored production dump (Knowledge Production Import Foundation,
docs/audit/knowledge-production-import-foundation.md) before ever touching
production, and fixed by excluding `location` from the SELECT the same way
migration 0091 was fixed.

Only runs under GIS (module-level skip below) — under `USE_GIS=0` `location`
is a genuine `TextField` with no drift to reproduce.
"""

import os

import pytest
from django.db import connection

from temples.models import Shrine
from temples.services.knowledge_seed import resolve_shrine

if os.getenv("USE_GIS") != "1":
    pytest.skip("GIS disabled by env", allow_module_level=True)


@pytest.mark.django_db(transaction=True)
def test_resolve_shrine_does_not_raise_under_text_location_drift():
    shrine = Shrine.objects.create(name_jp="識別テスト神社", kind="shrine", address="住所123")

    with connection.cursor() as cur:
        # The GiST index on `location` has no default operator class for
        # `text`, so it must be dropped before the type change (and rebuilt
        # after) to simulate the drift without an unrelated index error.
        cur.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'temples_shrine' AND indexdef ILIKE '%% USING gist (location)%%'"
        )
        gist_index_names = [row[0] for row in cur.fetchall()]
        for index_name in gist_index_names:
            cur.execute(f'DROP INDEX "{index_name}";')

        cur.execute('ALTER TABLE temples_shrine ALTER COLUMN "location" TYPE text USING NULL;')
        cur.execute(
            'UPDATE temples_shrine SET "location" = %s WHERE id = %s;',
            ["not-a-valid-wkb-value", shrine.id],
        )

    try:
        result = resolve_shrine("識別テスト神社", "住所123")
    finally:
        with connection.cursor() as cur:
            cur.execute(
                'ALTER TABLE temples_shrine ALTER COLUMN "location" TYPE geometry(Point,4326) '
                "USING NULL;"
            )
            for index_name in gist_index_names:
                cur.execute(f'CREATE INDEX "{index_name}" ON temples_shrine USING gist (location);')

    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.id == shrine.id
