"""Local checks for the WS-04 edge diagnostic（stdlib only）: python -m unittest scripts/ws04_edge_diagnostic/test_app.py"""

import io
import json
import sys
import threading
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app  # noqa: E402

CLIENT_A = "203.0.113.10"
CLIENT_B = "198.51.100.20"
PROXY_1 = "10.1.2.3"
PROXY_2 = "10.4.5.6"
PROBE = "abcdefghij0123456789"


def headers(**kv):
    m = Message()
    for k, v in kv.items():
        m[k.replace("_", "-")] = v
    return m


class BuildReportTests(unittest.TestCase):
    def test_same_client_gives_a_stable_token(self):
        h = headers(CF_Connecting_IP=CLIENT_A, X_Forwarded_For=f"{CLIENT_A}, {PROXY_1}")
        r1 = app.build_report(h, PROXY_2, None)
        r2 = app.build_report(h, PROXY_2, None)
        self.assertEqual(r1["tokens"]["cf_connecting_ip"], r2["tokens"]["cf_connecting_ip"])
        self.assertEqual(r1["key_id"], r2["key_id"])

    def test_different_clients_give_different_tokens(self):
        ra = app.build_report(headers(CF_Connecting_IP=CLIENT_A), PROXY_1, None)
        rb = app.build_report(headers(CF_Connecting_IP=CLIENT_B), PROXY_1, None)
        self.assertNotEqual(ra["tokens"]["cf_connecting_ip"], rb["tokens"]["cf_connecting_ip"])

    def test_no_raw_address_or_header_value_is_returned(self):
        h = headers(
            CF_Connecting_IP=CLIENT_A,
            True_Client_IP=CLIENT_A,
            X_Real_IP=CLIENT_A,
            X_Forwarded_For=f"{PROBE}, {CLIENT_A}, {PROXY_1}, {PROXY_2}",
        )
        body = json.dumps(app.build_report(h, PROXY_2, PROBE))
        for raw in (CLIENT_A, PROXY_1, PROXY_2, PROBE):
            self.assertNotIn(raw, body)

    def test_reports_structure_and_xff_positions(self):
        h = headers(CF_Connecting_IP=CLIENT_A, X_Forwarded_For=f"{PROBE}, {CLIENT_A}, {PROXY_1}, {PROXY_2}")
        r = app.build_report(h, "10.9.9.9", None)
        self.assertEqual(r["xff_entry_count"], 4)
        self.assertEqual(r["equal"]["cf_connecting_ip_eq_xff_from_right"], [False, False, True, False])
        self.assertTrue(r["remote_addr_is_private"])
        self.assertNotIn("spoof_passthrough", r)

    def test_spoof_probe_detection(self):
        h = headers(CF_Connecting_IP=CLIENT_A, True_Client_IP=PROBE, X_Forwarded_For=f"{PROBE}, {CLIENT_A}")
        sp = app.build_report(h, PROXY_1, PROBE)["spoof_passthrough"]
        self.assertEqual(
            sp,
            {
                "cf_connecting_ip": False,
                "true_client_ip": True,
                "x_real_ip": False,
                "xff_leftmost": True,
                "xff_any_entry": True,
            },
        )

    def test_invalid_probe_is_ignored(self):
        r = app.build_report(headers(), None, "short")
        self.assertIsInstance(r["spoof_passthrough"], str)

    def test_missing_headers_are_safe(self):
        r = app.build_report(headers(), None, None)
        self.assertEqual(r["xff_entry_count"], 0)
        self.assertIsNone(r["tokens"]["cf_connecting_ip"])
        self.assertEqual(r["tokens"]["xff_from_right"], [])
        self.assertIsNone(r["remote_addr_is_private"])


class ServerTests(unittest.TestCase):
    def test_http_server_returns_json_and_writes_no_log(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        port = server.server_address[1]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/probe?probe={PROBE}",
                headers={"X-Forwarded-For": f"{PROBE}, {CLIENT_A}"},
            )
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode()
                self.assertEqual(resp.headers["Cache-Control"], "no-store")
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(f"http://127.0.0.1:{port}/other")
            server.shutdown()
            server.server_close()
        self.assertNotIn(CLIENT_A, body)
        self.assertNotIn(PROBE, body)
        self.assertEqual(json.loads(body)["xff_entry_count"], 2)
        self.assertEqual(out.getvalue() + err.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
