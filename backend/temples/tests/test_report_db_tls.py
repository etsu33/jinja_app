"""Safe, offline mock tests for the TLS probe; never connect to Production."""
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.management.commands import report_db_tls as mod


class Connection:
    vendor = "postgresql"

    def __init__(self, active=True, protocol=b"TLSv1.3", mode="require"):
        self.pgconn = SimpleNamespace(ssl_in_use=active, ssl_attribute=lambda _: protocol)
        self.connection = SimpleNamespace(pgconn=self.pgconn)
        self.settings_dict = {"OPTIONS": {"sslmode": mode}}
        self.called = False

    def ensure_connection(self):
        self.called = True


def test_tls_true_and_mode():
    c = Connection()
    assert mod.inspect_tls(c) == ("true", "TLSv1.3", "require")
    assert c.called


def test_tls_false():
    assert mod.inspect_tls(Connection(active=False)) == ("false", "unknown", "require")


def test_mode_unset_is_unspecified():
    assert mod.inspect_tls(Connection(mode=None))[2] == "unspecified"


def test_unknown_protocol_redacted():
    assert mod.inspect_tls(Connection(protocol=b"secret-host:password"))[1] == "unknown"


def test_missing_pgconn_fails_closed():
    c = Connection()
    c.connection = SimpleNamespace()
    with pytest.raises(ValueError):
        mod.inspect_tls(c)


def test_non_postgresql_fails_closed():
    c = Connection()
    c.vendor = "sqlite"
    with pytest.raises(ValueError):
        mod.inspect_tls(c)


def test_error_never_leaks_driver_exception(monkeypatch):
    class BadConnection(Connection):
        def ensure_connection(self):
            raise RuntimeError("password secret host private.example")

    monkeypatch.setattr(mod, "connections", {"default": BadConnection()})
    output = StringIO()
    with pytest.raises(CommandError) as e:
        call_command("report_db_tls", stdout=output)
    assert output.getvalue().strip() == "[db-tls-probe] status=error error_type=RuntimeError"
    assert "secret" not in str(e.value)
    assert e.value.__cause__ is None


def test_command_output_is_allowlisted(monkeypatch):
    monkeypatch.setattr(mod, "connections", {"default": Connection()})
    output = StringIO()
    call_command("report_db_tls", stdout=output)
    assert output.getvalue().strip() == (
        "[db-tls-probe] ssl_in_use=true protocol=TLSv1.3 sslmode=require "
        "certificate_verified=unknown hostname_verified=unknown"
    )
