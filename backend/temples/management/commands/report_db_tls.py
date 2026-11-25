"""Opt-in, read-only, credential-safe TLS probe for Django's actual DB connection.

Does not issue SQL. Only touches the existing Django default connection and libpq metadata.
No URL, host, username, project ref, DB name, exceptions or connection info are emitted.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

MARKER = "[db-tls-probe]"
VALID_SSLMODES = frozenset({"disable", "allow", "prefer", "require", "verify-ca", "verify-full"})


def inspect_tls(connection) -> tuple[str, str, str]:
    """Return strictly allowlisted status tokens; never return libpq connection.info."""
    if connection.vendor != "postgresql":
        raise ValueError("unsupported backend")
    connection.ensure_connection()
    raw = connection.connection
    pgconn = getattr(raw, "pgconn", None)
    if pgconn is None:
        raise ValueError("no psycopg pgconn")
    active = getattr(pgconn, "ssl_in_use", None)
    if active is not True and active is not False:
        raise ValueError("TLS status unavailable")
    mode = connection.settings_dict.get("OPTIONS", {}).get("sslmode")
    if mode not in VALID_SSLMODES:
        mode = "unspecified"
    protocol = "unknown"
    if active:
        ssl_attribute = getattr(pgconn, "ssl_attribute", None)
        if callable(ssl_attribute):
            value = ssl_attribute(b"protocol")
            if isinstance(value, bytes):
                value = value.decode("ascii", errors="ignore")
            if value in {"TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3", "SSLv3"}:
                protocol = value
    return ("true" if active else "false"), protocol, mode


class Command(BaseCommand):
    help = "Report the TLS state of Django's default PostgreSQL connection (no SQL, no secrets)."
    requires_system_checks = []

    def handle(self, *args, **kwargs):
        try:
            active, protocol, mode = inspect_tls(connections["default"])
        except Exception as exc:
            self.stdout.write(f"{MARKER} status=error error_type={type(exc).__name__}")
            raise CommandError("db TLS probe failed") from None
        self.stdout.write(
            f"{MARKER} ssl_in_use={active} protocol={protocol} sslmode={mode} "
            "certificate_verified=unknown hostname_verified=unknown"
        )
