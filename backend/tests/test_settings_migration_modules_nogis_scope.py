# backend/tests/test_settings_migration_modules_nogis_scope.py
"""`temples.migrations_nogis` must stay a test/CI-only migration override.

`shrine_project/settings.py` builds `MIGRATION_MODULES["temples"]` from a
handful of environment-derived flags (`USE_GIS` / `USE_SQLITE` /
`DISABLE_GIS_FOR_TESTS` / `IS_PYTEST`). A prior version of that condition
(`not USE_GIS and not USE_SQLITE`, no `IS_PYTEST` scoping — commit
`d5655e17b`, 2026-03-16) meant a live, non-test process (including
Production) could be silently redirected to the `migrations_nogis` squashed
migration set merely by `USE_GIS` resolving falsy, with no test/CI
involvement at all. See `docs/audit/production-migration-modules-nogis-root-cause.md`
for the full incident writeup.

These tests exercise the real module-level branching in `settings.py` by
importing it fresh in a subprocess for each scenario (Django settings are
computed once per process and cached, so an in-process `override_settings`
cannot exercise this import-time logic). Each subprocess is given a
minimal, explicit environment — never the parent pytest process's own
environment — so a scenario meant to look like Production (no `IS_PYTEST`,
no `PYTEST_CURRENT_TEST`, no `"pytest"` in argv) actually behaves like one.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

_PROBE_SCRIPT = """
import json
import django
django.setup()
from django.conf import settings
print(json.dumps({
    "migration_modules_temples": settings.MIGRATION_MODULES.get("temples"),
    "migration_modules_has_temples_key": "temples" in settings.MIGRATION_MODULES,
    "use_gis": settings.USE_GIS,
    "use_sqlite": settings.USE_SQLITE,
    "engine": settings.DATABASES["default"]["ENGINE"],
}))
"""

_BASE_ENV = {
    "DJANGO_SETTINGS_MODULE": "shrine_project.settings",
    "PYTHONPATH": str(BACKEND_DIR),
    "DJANGO_SECRET_KEY": "test-secret-key-for-settings-probe-only",
    "DEBUG": "0",
    "ALLOWED_HOSTS": "localhost,127.0.0.1",
    "CSRF_TRUSTED_ORIGINS": "http://localhost:3000",
    "CORS_ALLOWED_ORIGINS": "http://localhost:3000",
    # Keep the OS/locale/PATH minimally sane without inheriting anything
    # pytest-specific (PYTEST_CURRENT_TEST in particular).
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": os.environ.get("HOME", "/root"),
    "LANG": os.environ.get("LANG", "C.UTF-8"),
}


def _run_settings_probe(extra_env: dict) -> dict:
    """Import `shrine_project.settings` fresh in a clean subprocess under
    exactly `_BASE_ENV` merged with `extra_env` (nothing else — explicitly
    NOT `os.environ.copy()` — so no ambient `IS_PYTEST` / `PYTEST_CURRENT_TEST`
    / pytest-ish `argv` leaks in from the parent test process), and return
    the probe script's reported settings as a dict.
    """
    env = {**_BASE_ENV, **extra_env}
    result = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"settings probe subprocess failed (exit={result.returncode}):\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# Item 3 — Production-like: USE_GIS=false, USE_SQLITE=false, pytest=false
# -> MIGRATION_MODULES['temples'] must not exist at all.
# ---------------------------------------------------------------------------
def test_production_like_use_gis_false_does_not_trigger_temples_override():
    result = _run_settings_probe(
        {
            "USE_GIS": "0",
            "USE_SQLITE": "0",
            "DISABLE_GIS_FOR_TESTS": "0",
            # Deliberately absent: IS_PYTEST, PYTEST_CURRENT_TEST. The probe
            # script's own argv contains no "pytest" substring either.
        }
    )
    assert result["use_gis"] is False
    assert result["use_sqlite"] is False
    assert result["migration_modules_has_temples_key"] is False
    assert result["migration_modules_temples"] is None
    assert result["engine"] == "django.db.backends.postgresql"


def test_production_like_with_disable_gis_for_tests_set_but_no_pytest_is_still_safe():
    """Even if `DISABLE_GIS_FOR_TESTS=1` is (mis)configured on a live,
    non-pytest process, the temples override must still not fire -- pytest
    involvement is required, not just the disable flag."""
    result = _run_settings_probe(
        {
            "USE_GIS": "0",
            "USE_SQLITE": "0",
            "DISABLE_GIS_FOR_TESTS": "1",
        }
    )
    assert result["migration_modules_has_temples_key"] is False
    assert result["migration_modules_temples"] is None


# ---------------------------------------------------------------------------
# Item 4 — Test: pytest=true, DISABLE_GIS_FOR_TESTS=true
# -> migrations_nogis remains available (unchanged behavior).
# ---------------------------------------------------------------------------
def test_pytest_with_disable_gis_for_tests_still_uses_migrations_nogis():
    result = _run_settings_probe(
        {
            "IS_PYTEST": "1",
            "USE_GIS": "0",
            "USE_SQLITE": "0",
            "DISABLE_GIS_FOR_TESTS": "1",
        }
    )
    assert result["migration_modules_has_temples_key"] is True
    assert result["migration_modules_temples"] == "temples.migrations_nogis"
    # DISABLE_GIS_FOR_TESTS also still forces USE_GIS off for this scenario
    # (unchanged from before this fix).
    assert result["use_gis"] is False
    assert result["engine"] == "django.db.backends.postgresql"


# ---------------------------------------------------------------------------
# Item 5 — GIS: USE_GIS=true -> normal migration lineage (temples key absent).
# ---------------------------------------------------------------------------
def test_use_gis_true_uses_normal_lineage_even_under_pytest():
    result = _run_settings_probe(
        {
            "IS_PYTEST": "1",
            "USE_GIS": "1",
            "USE_SQLITE": "0",
            "DISABLE_GIS_FOR_TESTS": "0",
        }
    )
    assert result["use_gis"] is True
    assert result["migration_modules_has_temples_key"] is False
    assert result["migration_modules_temples"] is None
    assert result["engine"] == "django.contrib.gis.db.backends.postgis"


def test_use_gis_true_uses_normal_lineage_outside_pytest_too():
    result = _run_settings_probe(
        {
            "USE_GIS": "1",
            "USE_SQLITE": "0",
            "DISABLE_GIS_FOR_TESTS": "0",
        }
    )
    assert result["migration_modules_has_temples_key"] is False
    assert result["engine"] == "django.contrib.gis.db.backends.postgis"


# ---------------------------------------------------------------------------
# Item 6 — USE_SQLITE=true existing behavior is unchanged: the temples
# override never fires for SQLite regardless of the other flags (SQLite has
# its own separate spatialite/sqlite3 engine selection, untouched by this
# fix). `IS_PYTEST=1` is never combined with `USE_SQLITE=1` here because
# settings.py itself hard-raises on that combination (pytest requires
# Postgres/PostGIS) -- that guard is exercised separately below.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("use_gis", ["0", "1"])
def test_use_sqlite_true_never_triggers_temples_override_outside_pytest(use_gis):
    result = _run_settings_probe(
        {
            "USE_GIS": use_gis,
            "USE_SQLITE": "1",
            "DISABLE_GIS_FOR_TESTS": "0",
        }
    )
    assert result["use_sqlite"] is True
    assert result["migration_modules_has_temples_key"] is False
    assert result["migration_modules_temples"] is None


def test_pytest_with_use_sqlite_still_raises_as_before():
    """Unrelated to this fix, but documents that `IS_PYTEST=1` +
    `USE_SQLITE=1` is structurally impossible (settings.py raises before
    either MIGRATION_MODULES branch is reached) -- so the `not USE_SQLITE`
    clause added to `TEMPLES_USE_NOGIS_MIGRATIONS` can never actually be
    the discriminating factor while `IS_PYTEST` is true; it exists purely
    as defense in depth, matching the module's own original design."""
    env = {
        **_BASE_ENV,
        "IS_PYTEST": "1",
        "USE_GIS": "0",
        "USE_SQLITE": "1",
        "DISABLE_GIS_FOR_TESTS": "1",
    }
    result = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "USE_SQLITE" in result.stderr
