"""WS-04 MD-1 temporary edge diagnostic.

NOT part of jinja-backend. Deploy only as a throwaway Render free web service, measure, then delete it
（docs/audit/ws04-throttle-client-identity-design-2026-10-25.md §10）.

Privacy rules:
- No raw IP address, header value, key or full HMAC is ever returned or logged.
- Candidate client identities are reduced to a truncated HMAC under a key generated in memory at process start.
  The key is never persisted or logged; a restart（including a free-instance spin-down）creates a new key and a new
  `key_id`, so tokens cannot be compared across key generations and do not form a long-lived identifier.
- The access log is disabled.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

_KEY = secrets.token_bytes(32)
KEY_ID = secrets.token_hex(4)
TOKEN_HEX_LEN = 16
_PROBE_RE = re.compile(r"^[A-Za-z0-9]{16,64}$")


def comparison_token(value: str | None) -> str | None:
    """Truncated HMAC of a candidate identity. Equal tokens ⇔ equal values within one key generation."""
    if not value or not value.strip():
        return None
    return hmac.new(_KEY, value.strip().encode("utf-8"), hashlib.sha256).hexdigest()[:TOKEN_HEX_LEN]


def _split_xff(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _is_private(addr: str | None) -> bool | None:
    if not addr:
        return None
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return None
    return ip.is_private or ip.is_loopback or ip.is_link_local


def build_report(headers, remote_addr: str | None, probe: str | None) -> dict:
    """Build the response from request headers. `headers` is any case-insensitive mapping with `.get`."""
    xff = _split_xff(headers.get("X-Forwarded-For"))
    cf = (headers.get("CF-Connecting-IP") or "").strip() or None
    tci = (headers.get("True-Client-IP") or "").strip() or None
    xff_from_right = list(reversed(xff))

    report: dict = {
        "key_id": KEY_ID,
        "xff_entry_count": len(xff),
        "present": {
            "cf_connecting_ip": cf is not None,
            "true_client_ip": tci is not None,
            "x_real_ip": bool((headers.get("X-Real-IP") or "").strip()),
        },
        "tokens": {
            "cf_connecting_ip": comparison_token(cf),
            "true_client_ip": comparison_token(tci),
            "xff_from_right": [comparison_token(x) for x in xff_from_right],
        },
        "equal": {
            "cf_connecting_ip_eq_true_client_ip": (cf == tci) if cf and tci else None,
            "cf_connecting_ip_eq_xff_from_right": [cf == x for x in xff_from_right] if cf else [],
        },
        "remote_addr_is_private": _is_private(remote_addr),
    }

    if probe is not None and _PROBE_RE.match(probe):
        report["spoof_passthrough"] = {
            "cf_connecting_ip": cf == probe,
            "true_client_ip": tci == probe,
            "x_real_ip": (headers.get("X-Real-IP") or "").strip() == probe,
            "xff_leftmost": bool(xff) and xff[0] == probe,
            "xff_any_entry": probe in xff,
        }
    elif probe is not None:
        report["spoof_passthrough"] = "ignored: probe must be 16-64 ASCII letters or digits"

    return report


class Handler(BaseHTTPRequestHandler):
    server_version = "ws04-edge-diagnostic"
    sys_version = ""

    def log_message(self, format, *args):  # noqa: A002 — access log disabled on purpose
        return

    def _send(self, status: int, body: dict) -> None:
        data = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        parts = urlsplit(self.path)
        if parts.path == "/healthz":
            self._send(200, {"ok": True})
            return
        if parts.path != "/probe":
            self._send(404, {"detail": "not found"})
            return
        probe = parse_qs(parts.query).get("probe", [None])[0]
        self._send(200, build_report(self.headers, self.client_address[0], probe))


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
