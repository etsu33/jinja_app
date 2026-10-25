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

1. Render dashboard → New → Web Service → this repository, branch `fix/security-throttle-client-identity`.
2. Root directory `scripts/ws04_edge_diagnostic`, runtime Python, build command `true`（nothing to install）, start command
   `python app.py`.
3. Instance type **Free**. No environment variables. No custom domain. Same region as `jinja-backend` if known.
4. Do not connect it to any database, disk, secret group or production environment group.

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
