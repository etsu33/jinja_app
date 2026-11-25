"""Report the PostgreSQL role names of Django's configured database connection.

One-shot, read-only diagnostic. It runs exactly one statement through the
`default` connection:

    SELECT current_user, session_user

and prints exactly one line:

    [db-role-probe] current_user=<role> session_user=<role>

Nothing else is printed: no connection URL, host, port, database name, user
option or password. If the probe fails, only the exception class name is
printed (`[db-role-probe] status=error error_type=<ClassName>`), because
driver error messages can contain the host and database name.

Not run automatically. `start.sh` calls it only when
`RUN_DB_ROLE_PROBE_ON_START=1`, and a failure there does not abort startup.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

MARKER = "[db-role-probe]"
PROBE_SQL = "SELECT current_user, session_user"


def probe_db_role(connection) -> tuple[str, str]:
    """Run the single read-only probe statement and return (current_user, session_user)."""
    with connection.cursor() as cursor:
        cursor.execute(PROBE_SQL)
        current_user, session_user = cursor.fetchone()
    return str(current_user), str(session_user)


class Command(BaseCommand):
    help = "Print current_user and session_user of the default database connection (read-only)."

    requires_system_checks: list[str] = []

    def handle(self, *args, **options):
        try:
            current_user, session_user = probe_db_role(connections["default"])
        except Exception as exc:  # noqa: BLE001 - only the class name may be printed
            self.stdout.write(f"{MARKER} status=error error_type={type(exc).__name__}")
            # `from None` drops the chained driver message (it may carry host / database name).
            raise CommandError("db role probe failed") from None
        self.stdout.write(f"{MARKER} current_user={current_user} session_user={session_user}")
