"""TLS self-observation of the exact connection used by `evidence_coverage_audit`.

Mother Ship decision (2026-11-02): AUDIT_TLS_EVIDENCE_IMPLEMENTATION = IN_TRANSACTION_SELF_OBSERVATION.
Readiness doc: `docs/audit/evidence-coverage-production-readiness-2026-11-01.md` §9.

What is observed, and from where (never from Django settings):

- `effective_sslmode`: the `sslmode` keyword of the live libpq connection (`PQconninfo` via
  `pgconn.info`). This is the value the connection was actually opened with, including libpq defaults
  and `PG*` environment variables. Only the mode token is kept.
- `sslrootcert_configured`: whether the live connection has a non-empty `sslrootcert` option.
  Presence only; the path is never read into the result.
- `client_ssl_in_use`: `pgconn.ssl_in_use` of the same connection (client-to-server leg).
- `server_pg_stat_ssl`: `pg_stat_ssl.ssl` for `pg_backend_pid()`, queried in the audit's own read-only
  transaction (inside a savepoint, so an error cannot abort the transaction). Through a pooler this
  describes the server-side session, **not** the client-to-pooler leg.
- `connection_correlation`: whether the audit finished on the same driver connection object that
  was observed (object identity; no PID or address is recorded).

Limits:
- These are observations. `verify_full_observed=true` means the live connection was opened with
  `sslmode=verify-full`; per libpq's documented behaviour a successful connection then implies chain and
  hostname checks, but this module does not itself verify certificates or hostnames.
- A pooler cannot be detected here (`pooler_detection=unknown`).
- No G-6 / G-7 gate is evaluated or passed here (`gate_evaluation=not_evaluated`).

Redaction: only the allowlisted tokens below leave this module. Never connection strings, passwords,
hostnames, users, project references, certificate paths, backend PIDs or exception text.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

VALID_SSLMODES = frozenset({"disable", "allow", "prefer", "require", "verify-ca", "verify-full"})
UNKNOWN = "unknown"

_PG_STAT_SSL_SQL = "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"


def _tri(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return UNKNOWN


def _raw_connection(conn) -> Any:
    return getattr(conn, "connection", None)


def _pgconn(raw) -> Any:
    return getattr(raw, "pgconn", None) if raw is not None else None


def _conninfo_option(pgconn, keyword: bytes) -> tuple[bool, str | None]:
    """(available, value) for one live libpq conninfo keyword. Never raises; never returns other keys."""
    if pgconn is None:
        return False, None
    try:
        options = pgconn.info
    except Exception:  # noqa: BLE001 - unavailable metadata is UNKNOWN, not an error
        return False, None
    if options is None:
        return False, None
    try:
        for option in options:
            if getattr(option, "keyword", None) == keyword:
                raw_value = getattr(option, "val", None)
                if raw_value is None:
                    return True, None
                if isinstance(raw_value, bytes):
                    return True, raw_value.decode("utf-8", errors="replace")
                return True, str(raw_value)
    except Exception:  # noqa: BLE001
        return False, None
    return False, None


def _effective_sslmode(pgconn) -> str:
    available, value = _conninfo_option(pgconn, b"sslmode")
    if not available or value not in VALID_SSLMODES:
        return UNKNOWN
    return value


def _sslrootcert_configured(pgconn) -> str:
    available, value = _conninfo_option(pgconn, b"sslrootcert")
    if not available:
        return UNKNOWN
    return "yes" if value else "no"


def _server_pg_stat_ssl(conn) -> str:
    """`pg_stat_ssl.ssl` for this backend, in the caller's transaction. Errors and no row are UNKNOWN."""
    try:
        with transaction.atomic(
            using=conn.alias
        ):  # savepoint: an error must not abort the audit txn
            with conn.cursor() as cursor:
                cursor.execute(_PG_STAT_SSL_SQL)
                rows = cursor.fetchall()
    except (
        Exception
    ):  # noqa: BLE001 - unavailable / denied / error -> UNKNOWN (fail closed upstream)
        return UNKNOWN
    if len(rows) != 1:
        return UNKNOWN
    return _tri(rows[0][0])


def _consistency(client: str, server: str) -> str:
    if UNKNOWN in (client, server):
        return UNKNOWN
    if client == server:
        # Agreement does not exclude a pooler: the two values may describe different legs.
        return "consistent"
    return "contradictory"


def collect_tls_evidence(conn) -> tuple[dict[str, str], Any]:
    """Observe TLS on `conn` (must be the audit's connection, inside its read-only transaction).

    Returns (redacted evidence, opaque handle for `confirm_same_connection`). The handle is the driver
    connection object; it must never be serialized.
    """
    raw = _raw_connection(conn)
    pgconn = _pgconn(raw)
    effective = _effective_sslmode(pgconn)
    client = _tri(getattr(pgconn, "ssl_in_use", None)) if pgconn is not None else UNKNOWN
    server = _server_pg_stat_ssl(conn) if raw is not None else UNKNOWN
    evidence = {
        "collection": "in_transaction_self_observation",
        "effective_sslmode": effective,
        "verify_full_observed": (
            UNKNOWN if effective == UNKNOWN else ("true" if effective == "verify-full" else "false")
        ),
        "sslrootcert_configured": _sslrootcert_configured(pgconn),
        "client_ssl_in_use": client,
        "server_pg_stat_ssl": server,
        "server_scope": "backend_session",
        "pooler_detection": UNKNOWN,
        "client_server_consistency": _consistency(client, server),
        "connection_correlation": UNKNOWN if raw is None else "pending",
        "certificate_verified": UNKNOWN,
        "hostname_verified": UNKNOWN,
        "gate_evaluation": "not_evaluated",
    }
    return evidence, raw


def confirm_same_connection(conn, handle: Any, evidence: dict[str, str]) -> dict[str, str]:
    """Mark whether the audit ended on the same driver connection object that was observed."""
    result = dict(evidence)
    if handle is None:
        result["connection_correlation"] = UNKNOWN
    elif _raw_connection(conn) is handle:
        result["connection_correlation"] = "same_connection"
    else:
        result["connection_correlation"] = "mismatch"
    return result


def production_tls_problems(evidence: dict[str, str]) -> list[str]:
    """Fail-closed reasons for production-readonly. Empty list means no TLS reason to stop here.

    This is not a G-6 PASS: certificate / hostname verification and pooler legs stay unverified.
    """
    problems = []
    if evidence.get("verify_full_observed") != "true":
        problems.append("effective_sslmode_not_verify_full")
    if evidence.get("sslrootcert_configured") != "yes":
        problems.append("sslrootcert_not_configured")
    if evidence.get("client_ssl_in_use") != "true":
        problems.append("client_ssl_not_in_use")
    if evidence.get("server_pg_stat_ssl") != "true":
        problems.append("pg_stat_ssl_not_true")
    if evidence.get("client_server_consistency") == "contradictory":
        problems.append("client_server_contradiction")
    if evidence.get("connection_correlation") not in ("pending", "same_connection"):
        problems.append("connection_not_correlated")
    return problems
