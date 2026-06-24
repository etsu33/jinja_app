# Security Alerts Triage

## Purpose

This document records Dependabot alerts that remain open after dependency updates, and why they are currently deferred.

## Current status

As of the latest triage, High alerts were reduced from 10 to 5.

## Resolved or reduced

- Updated frontend dependencies via `pnpm up`.
- Updated backend dependencies:
  - Django `5.2.12` → `5.2.13`
  - Pillow `12.1.1` → `12.2.0`
- Confirmed:
  - `pnpm --filter ./apps/web test:contract`
  - `python manage.py check`
  - eslint

## Remaining High alerts

| Package | Alert | Source | Classification | Status |
|---|---|---|---|---|
| Next.js | Denial of Service with Server Components | `apps/web/package.json` / `pnpm-lock.yaml` | frontend dependency | Next.js is already `16.2.1`; no local diff from update command. Pending GitHub recalculation or upstream advisory state. |
| Next.js | Denial of Service with Server Components | `pnpm-lock.yaml` | frontend dependency | Same as above. |
| lodash | Code Injection via `_.template` imports key names | `pnpm-lock.yaml` | dev dependency | Pulled through `@stoplight/spectral-cli`; no newer `@stoplight/spectral-cli` available. Deferred as upstream dependency. |
| Vite | `server.fs.deny` bypassed with queries | `pnpm-lock.yaml` | dev dependency | Pulled through `vite-tsconfig-paths` peer dependency; no update available. Deferred as dev-only exposure. |
| Vite | Arbitrary File Read via Dev Server WebSocket | `pnpm-lock.yaml` | dev dependency | Same as above. |

## Policy

- Do not mix security dependency updates with product UI or feature changes.
- Resolve production runtime dependencies first.
- Defer dev-only alerts when no upstream fix is available, but keep them documented.
- Recheck Dependabot alerts after every dependency update PR is merged.

## Next review

Recheck after either:

- GitHub recalculates Dependabot alerts for the latest `develop`.
- A new version of `@stoplight/spectral-cli`, `vite-tsconfig-paths`, or Next.js is available.
