"""Offline propagation tests: DATABASE_URL TLS query options → Django settings → psycopg connect kwargs.

Scope and limits:
- Synthetic URLs only (`.invalid` host, fake password); no network, no database, no real credential.
- psycopg's `connect` is replaced with a recorder that raises before any socket is opened.
- These tests prove only that `sslmode` / `sslrootcert` reach the driver unchanged. They do **not** prove that a
  certificate or hostname was verified on a real connection; that is libpq's job at handshake time, and
  `report_db_tls` deliberately reports `certificate_verified=unknown hostname_verified=unknown`.
- Assertion messages never include the URL or the password: comparisons go through `_safe()`.
"""

from __future__ import annotations

from urllib.parse import quote

import dj_database_url
import pytest
import shrine_project.settings as project_settings
from django.db import connections as django_connections
from django.db.backends.postgresql import base as pg_base
from temples.management.commands import report_db_tls

SYNTHETIC_PASSWORD = "SYNTHETIC-NOT-A-SECRET-7f3a"
SYNTHETIC_USER = "synthetic_user"
SYNTHETIC_HOST = "db.example.invalid"
CA_PATH = "/synthetic/certs/provider-root.pem"
VALID_SSLMODES = report_db_tls.VALID_SSLMODES


def _url(*, scheme: str = "postgres", query: str = "") -> str:
    base = f"{scheme}://{SYNTHETIC_USER}:{SYNTHETIC_PASSWORD}@{SYNTHETIC_HOST}:6543/synthetic_db"
    return f"{base}?{query}" if query else base


def _safe(mapping: dict) -> dict:
    """Copy without credentials, for assertion messages."""
    redacted = {}
    for key, value in mapping.items():
        if key.lower() in {"password", "passwd"}:
            redacted[key] = "<redacted>"
        elif isinstance(value, dict):
            redacted[key] = _safe(value)
        else:
            redacted[key] = value
    return redacted


def tls_option_status(options: dict) -> dict[str, str]:
    """Explicit status for the two TLS options: missing / invalid / the value (path presence only)."""
    mode = options.get("sslmode")
    if mode is None:
        mode_status = "MISSING"
    elif mode not in VALID_SSLMODES:
        mode_status = "INVALID"
    else:
        mode_status = mode
    root = options.get("sslrootcert")
    root_status = "MISSING" if not root else "PRESENT"
    return {"sslmode": mode_status, "sslrootcert": root_status}


@pytest.fixture
def build_with(monkeypatch):
    """Run the real `settings.build_database_config()` against a synthetic DATABASE_URL (module globals only)."""

    def _build(url: str | None, *, debug: bool = False, use_gis: bool = False) -> dict:
        monkeypatch.setattr(project_settings, "DATABASE_URL", url)
        monkeypatch.setattr(project_settings, "USE_SQLITE", False)
        monkeypatch.setattr(project_settings, "DEBUG", debug)
        monkeypatch.setattr(project_settings, "USE_GIS", use_gis)
        return project_settings.build_database_config()

    return _build


@pytest.fixture
def recorded_connect(monkeypatch):
    """Replace psycopg.connect as used by Django's backend; record kwargs, never open a socket."""
    calls: list[dict] = []

    class _Stop(Exception):
        pass

    def fake_connect(*args, **kwargs):
        calls.append(dict(kwargs))
        raise _Stop("connect intercepted by test")

    monkeypatch.setattr(pg_base.Database, "connect", fake_connect)
    return calls, _Stop


def _driver_kwargs(db_config: dict, recorded_connect) -> dict:
    """Drive Django's real PostgreSQL backend up to psycopg.connect and return the kwargs it passed."""
    calls, stop = recorded_connect
    full = django_connections.configure_settings({"default": dict(db_config)})["default"]
    full["ENGINE"] = "django.db.backends.postgresql"  # plain backend: no GDAL needed offline
    wrapper = pg_base.DatabaseWrapper(full, alias="tls_propagation")
    with pytest.raises(stop):
        wrapper.get_new_connection(wrapper.get_connection_params())
    assert len(calls) == 1
    return calls[0]


# --------------------------------------------------------------------------- #
# 1-3: URL → dj_database_url → settings.build_database_config()
# --------------------------------------------------------------------------- #


def test_dj_database_url_preserves_sslmode_verify_full():
    parsed = dj_database_url.parse(_url(query="sslmode=verify-full"))
    assert parsed["OPTIONS"].get("sslmode") == "verify-full", _safe(parsed)


def test_settings_keep_both_tls_options_and_connect_timeout(build_with):
    cfg = build_with(_url(query=f"sslmode=verify-full&sslrootcert={quote(CA_PATH, safe='')}"))

    assert cfg["OPTIONS"].get("sslmode") == "verify-full", _safe(cfg)
    assert cfg["OPTIONS"].get("sslrootcert") == CA_PATH, _safe(cfg)  # URL-encoded path is decoded
    assert cfg["OPTIONS"].get("connect_timeout") == 5, _safe(cfg)
    assert cfg["ENGINE"] == "django.db.backends.postgresql"
    assert cfg["CONN_MAX_AGE"] == 600  # DEBUG=False


def test_connect_timeout_in_url_is_not_overridden(build_with):
    cfg = build_with(_url(query="sslmode=require&connect_timeout=11"))
    assert str(cfg["OPTIONS"].get("connect_timeout")) == "11", _safe(cfg)


def test_postgis_scheme_keeps_tls_options(build_with):
    cfg = build_with(
        _url(scheme="postgis", query=f"sslmode=verify-full&sslrootcert={CA_PATH}"), use_gis=True
    )
    assert cfg["ENGINE"] == "django.contrib.gis.db.backends.postgis"
    assert tls_option_status(cfg["OPTIONS"]) == {"sslmode": "verify-full", "sslrootcert": "PRESENT"}


# --------------------------------------------------------------------------- #
# 4: settings → Django PostgreSQL backend → psycopg.connect kwargs
# --------------------------------------------------------------------------- #


def test_backend_passes_both_tls_options_to_psycopg(build_with, recorded_connect):
    cfg = build_with(_url(query=f"sslmode=verify-full&sslrootcert={CA_PATH}"))

    kwargs = _driver_kwargs(cfg, recorded_connect)

    assert kwargs.get("sslmode") == "verify-full", _safe(kwargs)
    assert kwargs.get("sslrootcert") == CA_PATH, _safe(kwargs)
    assert kwargs.get("connect_timeout") == 5, _safe(kwargs)
    assert kwargs.get("host") == SYNTHETIC_HOST


# --------------------------------------------------------------------------- #
# 5: missing options are reported as MISSING, not assumed
# --------------------------------------------------------------------------- #


def test_url_without_tls_options_is_reported_missing_end_to_end(build_with, recorded_connect):
    """Current repository default: settings add no TLS option (libpq then uses its own default)."""
    cfg = build_with(_url())
    kwargs = _driver_kwargs(cfg, recorded_connect)

    assert tls_option_status(cfg["OPTIONS"]) == {"sslmode": "MISSING", "sslrootcert": "MISSING"}
    assert tls_option_status(kwargs) == {"sslmode": "MISSING", "sslrootcert": "MISSING"}
    assert "sslmode" not in kwargs and "sslrootcert" not in kwargs, _safe(kwargs)


def test_sslmode_without_rootcert_is_partial(build_with):
    cfg = build_with(_url(query="sslmode=verify-full"))
    assert tls_option_status(cfg["OPTIONS"]) == {"sslmode": "verify-full", "sslrootcert": "MISSING"}


def test_db_env_fallback_path_has_no_tls_options(build_with):
    """Without DATABASE_URL, the DB_* fallback builds OPTIONS with connect_timeout only."""
    cfg = build_with(None)
    assert cfg["OPTIONS"] == {"connect_timeout": 5}, _safe(cfg)
    assert tls_option_status(cfg["OPTIONS"])["sslmode"] == "MISSING"


# --------------------------------------------------------------------------- #
# 6: invalid / unsupported values are not reported as verified
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad_mode", ["verify_full", "VERIFY-FULL", "strict", ""])
def test_invalid_sslmode_is_passed_through_unchanged_and_flagged(
    bad_mode, build_with, recorded_connect
):
    """Neither dj_database_url nor Django validates sslmode; libpq would reject it at connect time."""
    cfg = build_with(_url(query=f"sslmode={bad_mode}"))
    kwargs = _driver_kwargs(cfg, recorded_connect)

    if bad_mode == "":
        assert tls_option_status(kwargs)["sslmode"] in {"MISSING", "INVALID"}
    else:
        assert kwargs.get("sslmode") == bad_mode, _safe(kwargs)
        assert tls_option_status(kwargs)["sslmode"] == "INVALID"


class _ProbeConnection:
    vendor = "postgresql"

    def __init__(self, options: dict, *, ssl_in_use: bool):
        self.settings_dict = {"OPTIONS": options}
        self._ssl = ssl_in_use

    def ensure_connection(self):
        class _PgConn:
            ssl_in_use = self._ssl

            @staticmethod
            def ssl_attribute(_name):
                return b"TLSv1.3"

        self.connection = type("Raw", (), {"pgconn": _PgConn()})()


@pytest.mark.parametrize(
    "options, ssl_in_use, expected_mode",
    [
        ({"sslmode": "verify-full", "sslrootcert": CA_PATH}, True, "verify-full"),
        ({"sslmode": "verify_full"}, True, "unspecified"),
        ({}, True, "unspecified"),
        ({"sslmode": "disable"}, False, "disable"),
    ],
)
def test_probe_never_claims_verification(options, ssl_in_use, expected_mode, monkeypatch):
    active, _protocol, mode = report_db_tls.inspect_tls(
        _ProbeConnection(options, ssl_in_use=ssl_in_use)
    )
    assert mode == expected_mode
    assert active == ("true" if ssl_in_use else "false")

    # the command line always says verification is unknown, whatever the configured mode
    monkeypatch.setattr(
        report_db_tls, "connections", {"default": _ProbeConnection(options, ssl_in_use=ssl_in_use)}
    )
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    call_command("report_db_tls", stdout=out)
    line = out.getvalue().strip()
    assert "certificate_verified=unknown" in line
    assert "hostname_verified=unknown" in line
    assert "verified=true" not in line


# --------------------------------------------------------------------------- #
# 7: failures never expose credentials
# --------------------------------------------------------------------------- #


def test_safe_helper_redacts_password_in_nested_settings(build_with):
    cfg = build_with(_url(query="sslmode=require"))
    rendered = repr(_safe(cfg))
    assert SYNTHETIC_PASSWORD not in rendered
    assert "<redacted>" in rendered


def test_failed_assertion_message_does_not_contain_credentials(build_with):
    cfg = build_with(_url(query="sslmode=require"))
    with pytest.raises(AssertionError) as excinfo:
        assert cfg["OPTIONS"].get("sslmode") == "verify-full", _safe(cfg)
    message = str(excinfo.value)
    assert SYNTHETIC_PASSWORD not in message
    assert _url() not in message


def test_probe_error_output_does_not_contain_credentials(monkeypatch):
    class _Failing:
        vendor = "postgresql"
        settings_dict = {"OPTIONS": {"sslmode": "verify-full"}}

        def ensure_connection(self):
            raise RuntimeError(
                f"could not connect: password={SYNTHETIC_PASSWORD} host={SYNTHETIC_HOST}"
            )

    monkeypatch.setattr(report_db_tls, "connections", {"default": _Failing()})
    from io import StringIO

    from django.core.management import call_command
    from django.core.management.base import CommandError

    out = StringIO()
    with pytest.raises(CommandError) as excinfo:
        call_command("report_db_tls", stdout=out)
    for text in (out.getvalue(), str(excinfo.value)):
        assert SYNTHETIC_PASSWORD not in text
        assert SYNTHETIC_HOST not in text
