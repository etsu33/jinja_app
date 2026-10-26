# WS-04 MD-1 temporary edge diagnostic

A throwaway, standard-library-only HTTP service used once to check, on Render, whether two independent client networks
produce distinct client identities at the edge, and whether spoofed headers pass through. It is **not** part of
`jinja-backend` and must never be attached to the production service, database or secrets.

Design record: `docs/audit/ws04-throttle-client-identity-design-2026-10-25.md` §9–§10.

## What it returns

`GET /probe` returns JSON with:

- `key_id`: identifies the in-memory HMAC key generation（changes on every restart or free-instance spin-down）;
- `xff_entry_count` and header presence flags;
- `tokens`: a 16-hex-character truncated HMAC of each candidate identity（`CF-Connecting-IP`, `True-Client-IP`, and each
  `X-Forwarded-For` entry counted from the right）. Equal tokens mean equal values **within one `key_id` only**;
- `equal`: booleans comparing the candidates;
- `remote_addr_is_private`;
- `spoof_passthrough`（only with `?probe=<16-64 letters or digits>`）: whether each header equals the probe token.

It never returns or logs a raw address, header value, key or full HMAC. The access log is disabled.

## Deploy（owner action）

Reuse the existing isolated service `ws04-md1-header-probe-20261025`（`srv-dbespffb9u1s73ar5sn0`, Free, Singapore）. Do
not create another service. In its Settings, set:

| Setting | Value |
| --- | --- |
| Repository | `etsu33/jinja_app` |
| Branch | `fix/security-throttle-client-identity`（diagnostic committed at `c82ae64`） |
| Root Directory | `scripts/ws04_edge_diagnostic` |
| Language / Runtime | Python 3（code needs 3.7+; no dependencies） |
| Build Command | `true`（nothing to install） |
| Start Command | `python app.py`（binds `0.0.0.0:$PORT`, which Render supplies） |
| Health Check Path | `/healthz` |
| Instance Type | Free（unchanged） |
| Region | Singapore（unchanged） |
| Environment variables / secret files | none（remove any that exist） |
| Disk, database, environment group, custom domain | none |
| Auto-Deploy | Off（deploy once manually） |

Then Manual Deploy → Deploy latest commit, and check `GET /healthz` returns `{"ok": true}`. If the service runs on a
Docker runtime instead of Python, the language usually cannot be changed in place; stop and decide before recreating it.

## Measure（record only equalities, never tokens or addresses）

Do every step within **one** `key_id`. If `key_id` changes between responses, start again.

1. Mac, home / office network: open `https://<service>.onrender.com/probe` twice. Note whether
   `tokens.cf_connecting_ip` is the same in both（stability）.
2. iPhone, **Wi-Fi off**, cellular: open the same URL twice in Safari. Note stability, then whether the iPhone token
   equals the Mac token（separation）.
3. Mac, spoof checks（`T` = 20 random letters / digits）:
   - `curl -s -H "X-Forwarded-For: $T" -H "True-Client-IP: $T" "https://<service>.onrender.com/probe?probe=$T"`
   - `curl -s -o /dev/null -w "%{http_code}\n" -H "CF-Connecting-IP: $T" "https://<service>.onrender.com/probe?probe=$T"`
     （a 403 means the edge rejected the spoofed header）
4. Record: `key_id` unchanged（yes / no）; Mac stable; iPhone stable; Mac ≠ iPhone; `spoof_passthrough` booleans;
   `xff_entry_count`; presence flags; `remote_addr_is_private`; the edge response to a spoofed `CF-Connecting-IP`.
5. Delete the service immediately afterwards.

## Local checks

```bash
python3 -m unittest scripts/ws04_edge_diagnostic/test_app.py
```
