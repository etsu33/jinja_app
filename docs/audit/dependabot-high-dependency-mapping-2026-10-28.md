# Dependabot High: Dependency Mapping Audit（2026-10-28）

## 1. Status

```text
RECORD TYPE   = audit-only（no dependency, lockfile or code change）
BASELINE      = origin/develop@1170b60（after PR #3370 DOMPurify, #3371 Pillow, #3372 Storybook）
TARGET        = 72 High Dependabot alerts（52 runtime / 20 development, as reported by Mother Ship）
DATA SOURCES  = pnpm 9.12.3 `pnpm audit --json`（GitHub Advisory Database via the npm registry）;
                pip-audit 2.x with the PyPI vulnerability service, on backend/requirements-dev.txt;
                pnpm-lock.yaml snapshots; npm / PyPI package metadata
NOT AVAILABLE = the Dependabot alert list itself（no Dependabot API tool in this session）
FINAL STATUS  = PR for Mother Ship; priorities are Mother Ship's decision; STOP
```

Evidence labels:

- **Lock**: read from `pnpm-lock.yaml`;
- **Registry**: npm or PyPI metadata;
- **Audit**: pnpm-audit or pip-audit output;
- **Code**: repository source;
- **Inferred**: a conclusion drawn from the above;
- **Unknown**.

## 2. Conclusion

1. **npm: 69 High advisory entries across 19 packages（Audit）.** Python adds 6 known vulnerabilities in Django and DRF.
   pip-audit gives no severity, so it is **Unknown** which of them Dependabot counts as High. 69 + Python is consistent
   with 72, but **the mapping to individual alert numbers is not verified**. §3 covers the scope mismatch.
2. **Only 3 npm packages are direct dependencies of the production Web app:** `axios`, `zod` and `sharp`, all in
   `apps/web` `dependencies`. Everything else is transitive.
   - Under Mobile `expo`, the affected packages are Expo CLI, config-plugin and Babel tooling, not app runtime code
     （Inferred）.
   - Everything else is Web or root dev, test, lint or Storybook tooling.
3. **57 of the 69 entries（83 %）need only a lockfile refresh:** the patched version is inside the requirer's declared
   range（Registry）. This covers `@xmldom/xmldom`（both families）, `fast-uri`, `undici`, `vite`, `brace-expansion`,
   `browserslist`, `compression`, `follow-redirects`, `source-map-js`, `axios` and `sharp`.
4. **The repository's own `pnpm.overrides` pin two vulnerable versions:**
   - `"lodash": "4.17.23"`（vulnerable ≤ 4.17.23; `@stoplight/spectral-core@1.22.0` even asks for `^4.18.1`）;
   - `"js-yaml": "4.1.1"`（vulnerable < 4.3.2）.

   These entries must change. A lockfile refresh alone cannot fix them.
5. **No fix exists inside the current dependency ranges for:**
   - **`zod@3.25.76`:** required by `@expo/cli`（`^3.25.76`, also in the latest 58.x）. The advisory has no 3.x patch.
   - **`webpack-dev-middleware@6.1.3`:** required by `@storybook/builder-webpack5`（`^6.1.2`, also in the latest
     10.6.5）. The only patch is 7.4.6, a major version.
   - **`node-forge`:** the advisory lists no patched version. However, **1.4.2（published 2026-10-27）contains the
     canonical-DigestInfo check that the advisory describes**（§8）.
6. **`@xmldom/xmldom` has two version families:**
   - `0.8.13`, via `@expo/plist@0.8.1`（`^0.8.8`）;
   - `0.9.10`, via `simple-plist → plist@3.1.1`（`^0.9.10`）.

   Both reach patched versions（0.8.15 / 0.9.12）within their ranges. Together they account for 19 of the 69 entries.

## 3. Method and count reconciliation

- `pnpm audit --json --audit-level high` reports `high: 70`; the High advisory entries number 69. Each entry is one
  advisory × one vulnerable version range. The difference of 1 is pnpm's metadata counting and was not investigated
  further.
- **Scope by manifest section**（the importer's `dependencies` vs `devDependencies` of the top-level parent）: **43
  runtime / 26 development**. Dependabot reports 52 / 20, a total 3 higher. Possible reasons, none verified:
  - Python alerts are counted as runtime;
  - Dependabot's scope inference differs for packages reachable from both sections;
  - the advisory database differs slightly between the npm audit endpoint and Dependabot.
- **Manifest "runtime" is not the same as production runtime.** `apps/mobile` lists `expo` in `dependencies`, so Expo
  CLI tooling counts as runtime.

  §4 therefore gives a separate *actual-use* classification.

## 4. Package matrix（npm）

Usage classes:

- **WEB-PROD**: in the Next.js production server or client bundle;
- **WEB-BUILD**: in the Web production build chain;
- **MOBILE-TOOL**: Expo CLI, prebuild or Babel, not in the app bundle;
- **DEV**: lint, test, Storybook, OpenAPI or markdown tooling.

| package | installed（Lock） | patched | entries | direct? | immediate requirer（declared range） | top-level parents | manifest scope | actual use（Inferred） | fix path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `@xmldom/xmldom` | 0.8.13, 0.9.10 | 0.8.15 / 0.9.12 | 19 | no | `@expo/plist@0.8.1`（^0.8.8）; `plist@3.1.1`（^0.9.10）← `simple-plist` | `apps/mobile`: expo and expo-* | runtime | MOBILE-TOOL（iOS plist handling in prebuild / config plugins） | lockfile refresh |
| `axios` | 1.19.0 | 1.20.0 | 7 | **yes**（`apps/web` deps `^1.18.1`） | — | apps/web | runtime | **WEB-PROD**（client-side API modules, Code） | lockfile refresh（spec unchanged） |
| `follow-redirects` | 1.16.0 | 1.16.1 | 2 | no | `axios@1.19.0`（^1.16.0） | apps/web: axios | runtime | Node adapter only. No server import of axios found, so practically unused in production（Inferred） | lockfile refresh（with axios） |
| `zod` | 4.4.3, 3.25.76 | 4.6.6 | 1 | **yes**（`apps/web` deps `^4.4.3`） | 4.4.3: apps/web + `eslint-plugin-react-hooks`（^3.25.0 \|\| ^4）; 3.25.76: `@expo/cli`（^3.25.76） | apps/web, root / web lint, apps/mobile expo | runtime | 4.x: **WEB-PROD**（`lib/schemas/api.ts`, API route）; 3.x: MOBILE-TOOL | 4.x: lockfile refresh. 3.x: **no fix**（Expo CLI requires 3.x even in 58.x） |
| `sharp` | 0.35.3（next uses 0.35.5） | 0.35.5 | 2 | **yes**（`apps/web` deps `^0.35.0`） | `minimizer-webpack-plugin@5.13.0`（Storybook）; next uses its own `sharp@0.35.5` | apps/web | runtime | next/image uses next's 0.35.5（Inferred）. The direct 0.35.3 is not imported by app code（Code） | lockfile refresh |
| `brace-expansion` | 5.0.5 | 5.0.11 | 5 | no | `minimatch@10.2.3`（^5.0.2）; minimatch is **pinned by override** | lint, Expo tooling, Storybook, many | runtime | DEV / MOBILE-TOOL | lockfile refresh（override unchanged） |
| `js-yaml` | 4.1.1 | 4.3.2 | 3 | no | `@eslint/eslintrc`, `@expo/xcpretty`, `cosmiconfig`, `markdownlint-cli`（~4.1.1, which 4.3.2 is outside; an override forces it anyway）; **override pins 4.1.1** | lint, Expo, Storybook | runtime | DEV / MOBILE-TOOL | **change the override** |
| `browserslist` | 4.28.5 | 4.28.7 | 2 | no | `@babel/helper-compilation-targets@7.29.7`（^4.24.0）, `update-browserslist-db@1.2.3` | apps/mobile Babel presets | runtime | MOBILE-TOOL | lockfile refresh |
| `compression` | 1.8.1 | 1.8.2 | 1 | no | `@expo/cli@57.0.32`（^1.7.4） | apps/mobile expo | runtime | MOBILE-TOOL（Expo dev server） | lockfile refresh |
| `node-forge` | 1.4.0 | **none listed** | 1 | no | `@expo/cli`, `@expo/code-signing-certificates@0.0.6`（^1.3.3） | apps/mobile expo | runtime | MOBILE-TOOL（dev HTTPS / update code signing） | §8 |
| `fast-uri` | 3.1.0 | 3.1.7 | 8 | no | `ajv@8.18.0`（^3.0.1）; ajv is pinned by override | root `@stoplight/spectral-cli`, web Storybook | development | DEV | lockfile refresh |
| `undici` | 7.28.0 | 7.30.1 | 7 | no | `jsdom@29.1.1`（^7.25.0） | web / mobile vitest, jsdom | development | DEV（tests only） | lockfile refresh |
| `vite` | 7.3.1 | 7.3.7 | 3 | no | `vitest@4.1.10`（^6 \|\| ^7 \|\| ^8）, `@vitejs/plugin-react`, `vite-tsconfig-paths`（*） | vitest, root / web vite-tsconfig-paths | development | DEV（tests; the Next build does not use Vite） | lockfile refresh |
| `source-map-js` | 1.2.1 | 1.2.2 | 1 | no | `@tailwindcss/node@4.3.3`（^1.2.1）, `css-tree`, `magicast` | web tailwind / vitest / jsdom | development | WEB-BUILD（Tailwind） / DEV | lockfile refresh |
| `lodash` | 4.17.23 | 4.18.0（4.18.1 is out） | 1 | no | spectral（`^4.18.1`!）, `html-webpack-plugin`, `ts-prune`; **override pins 4.17.23** | root spectral, web Storybook, ts-prune | development | DEV | **change the override** |
| `linkify-it` | 5.0.0 | 5.0.2 | 2 | no | `markdown-it@14.1.1` | root `markdownlint-cli` | development | DEV | markdownlint-cli upgrade or override |
| `markdown-it` | 14.1.1 | 14.3.3 | 2 | no | `markdownlint-cli@0.47.0`（~14.1.0） | root `markdownlint-cli` | development | DEV | markdownlint-cli 0.50.0（markdown-it ~15）or override |
| `smol-toml` | 1.5.2 | 1.7.1 | 1 | no | `markdownlint-cli@0.47.0`（~1.5.2） | root `markdownlint-cli` | development | DEV | same |
| `webpack-dev-middleware` | 6.1.3 | 7.4.6 | 1 | no | `@storybook/builder-webpack5@10.6.2`（^6.1.2, also in 10.6.5） | web Storybook | development | DEV（`storybook dev` only） | **no in-range fix**: a major override, or accept the risk |

The per-advisory list（69 rows, with GHSA identifiers and parents）is in §11.

## 5. `@xmldom/xmldom`: two version families

| family | installed | requirer chain（Lock） | declared range | patched | entries |
| --- | --- | --- | --- | --- | --- |
| 0.8.x | 0.8.13 | `@expo/cli@57.0.32` / `@expo/config-plugins@57.0.11` → `@expo/plist@0.8.1` → `@xmldom/xmldom` | `^0.8.8` | 0.8.15（2026-08-21） | 8 |
| 0.9.x | 0.9.10 | `@expo/config-plugins` → `simple-plist@1.3.1` → `plist@3.1.1` → `@xmldom/xmldom` | `^0.9.10` | 0.9.12（2026-08-21） | 11 |

- Both fixes are patch releases within the declared ranges. No override is needed.
- The two families must not be merged: an override such as `"@xmldom/xmldom": "0.9.12"` would push 0.9 into
  `@expo/plist`, which declares `^0.8.8`.
- If an override is chosen, use the scoped forms `@expo/plist>@xmldom/xmldom` and `plist>@xmldom/xmldom`.

## 6. Repository overrides that keep vulnerable versions

| override（root `package.json`） | effect | needed change |
| --- | --- | --- |
| `"lodash": "4.17.23"` | Every lodash resolves to 4.17.23（vulnerable ≤ 4.17.23）, even where the requirer asks for `^4.18.1` | 4.18.1 |
| `"js-yaml": "4.1.1"` | Every js-yaml resolves to 4.1.1（vulnerable < 4.3.2）, including `markdownlint-cli 0.50.0`, which wants `~5.5.0` | ≥ 4.3.2; decide whether the 5.x consumers need a scoped exception |
| `"minimatch": "10.2.3"` | Not vulnerable itself; it keeps brace-expansion on the 5.x line. Its range `^5.0.2` allows 5.0.11 | none required |
| `"ajv@^8.0.0": "8.18.0"` | Not vulnerable itself; its range `^3.0.1` allows fast-uri 3.1.7 | none required |

These overrides were security pins that are now outdated. Changing them affects every consumer in the workspace,
including Mobile tooling.

## 7. Compatibility constraints

| item | current | target | constraint（Registry / Code） | risk |
| --- | --- | --- | --- | --- |
| Django | 5.2.16 | 5.2.17 | Patch release on the 5.2 LTS line. pip-audit: GHSA-q238-5cxm-5c9h（CVE-2026-15830）and GHSA-wvqv-fj8w-qmhm（CVE-2026-15307） | low; still the full backend suite |
| DRF | 3.17.2 | 3.18.2 | Requires `django>=5.2`; supports Django 5.2 / 6.0 / 6.1 and Python ≥ 3.10. Fixes GHSA-33wh-fxxf-88vv, GHSA-3547-9m27-7rxg and GHSA-xw6w-gcfp-cf8m. **Minor upgrade** | **medium**: WS-04 throttling relies on DRF's permission-before-throttle order and on `ScopedRateThrottle` internals（see the FU-1 / P2 audits）; serializer and validation behaviour |
| simplejwt / django-filter / drf-spectacular | 5.5.1 / 26.1 / 0.29.0 | unchanged | simplejwt needs `djangorestframework>=3.14`; django-filter needs `Django>=5.2`; drf-spectacular needs `djangorestframework>=3.10.3`. No declared conflict with DRF 3.18 | low; check OpenAPI generation |
| axios | ^1.18.1 → 1.19.0 | 1.20.0 | Same minor line. 7 advisories, all fixed in 1.20.0 | low–medium; client API calls, interceptors, refresh logic |
| sharp | ^0.35.0 → 0.35.3（direct）; next uses 0.35.5 | 0.35.5 | next 16.4.1 already requires `^0.35.5` | low; next/image is unaffected（already 0.35.5） |
| zod | 4.4.3（web）, 3.25.76（Expo CLI） | 4.6.6 | Web: same major. Expo CLI: requires 3.x even in 58.1.16 | Web: medium（schemas in `lib/schemas/api.ts`, API route validation）. Expo CLI: no fix |
| undici | 7.28.0 | 7.30.1 | `jsdom@29.1.1` requires `^7.25.0`. Not a direct dependency; Next does not use this copy（Lock） | low; test-only |

## 8. `node-forge`（no patched version listed）

- **Advisory:** GHSA-86w9-cpqp-85rv, "RSA PKCS#1 v1.5 signature verification accepts extra nested DigestAlgorithm
  elements", vulnerable `<=1.4.0`, patched `<0.0.0`（none）. The advisory was last updated 2026-10-01（Audit）.
- **Installed:** 1.4.0, required by `@expo/cli@57.0.32` and `@expo/code-signing-certificates@0.0.6`, both declaring
  `^1.3.3`.
- **Use:** Expo CLI development HTTPS and update code signing（MOBILE-TOOL）. The Mobile app does not use it at
  runtime, and neither does Web（Inferred）.
- **New releases:** 1.4.1 and **1.4.2** were published **2026-10-27**. A diff of `lib/rsa.js` 1.4.0 → 1.4.2 adds
  `_encodeDigestInfo` and a check that **rejects non-canonical DigestInfo**（"require a canonical DER DigestInfo
  (RFC 8017 8.2.2)… extra elements…"）. That is the advisory's flaw.
  - **Also changed in 1.4.2:** `asn1`, `cipher`, `cipherModes`, `http`, `jsbn`, `pbe`, `pem`, `pkcs12`, `tls` and
    `x509`. Those changes are not reviewed here.
- **Assessment:**
  - 1.4.2 is within `^1.3.3`, so a lockfile refresh can adopt it.
  - Dependabot will likely keep the alert open until the advisory lists a patched version（Inferred）.
  - **Options for Mother Ship:** adopt 1.4.2 now; dismiss the alert as "tolerable risk"（dev tooling only）; or wait
    for the advisory to be updated.

## 9. PR split proposal（independent, minimal; no order decided here）

| PR | scope | entries（npm） | change | regression and verification gate |
| --- | --- | --- | --- | --- |
| **H-1 Mobile Expo tooling refresh** | `@xmldom/xmldom`（both families）, `browserslist`, `compression`, `brace-expansion` | 27 | lockfile refresh only（`pnpm update --depth Infinity <pkgs>`, ranges unchanged） | Mobile: `tsc`, vitest; `expo config` / `expo prebuild --no-install` dry run（plist handling）; confirm no versions change outside the targets |
| **H-2 Web runtime: axios + follow-redirects** | `axios`, `follow-redirects` | 9 | refresh to 1.20.0 / 1.16.1 | web vitest（API client, interceptors, refresh）, `tsc`, lint, `next build`; Preview smoke test of login and API calls |
| **H-3 Web runtime: zod 4.x** | `zod` 4.4.3 → 4.6.6（web and eslint-plugin-react-hooks） | 1（partial） | refresh; `apps/web` spec optionally `^4.6.6` | web vitest（schemas, API route validation）, `tsc`, `next build` |
| **H-4 sharp alignment** | `sharp` 0.35.3 → 0.35.5 | 2 | refresh | `next build`; image optimisation smoke test; Storybook build |
| **H-5 Test tooling** | `undici`, `vite`, `source-map-js` | 11 | refresh | full web and mobile vitest; Storybook build（source-map-js via Tailwind）; `next build`（Tailwind） |
| **H-6 Override corrections** | `lodash` 4.18.1, `js-yaml` ≥ 4.3.2 | 4 | edit `pnpm.overrides` | lint（eslintrc）, `pnpm audit:openapi` / spectral, Storybook build, `ts-prune`, markdownlint, Mobile iOS tooling（xcpretty）; affects every workspace |
| **H-7 Lint / docs tooling** | `markdownlint-cli` → 0.50.0, or scoped overrides for `linkify-it` / `markdown-it` / `smol-toml`; `fast-uri` refresh | 13 | dev dependency bump or overrides; depends on the H-6 js-yaml decision | markdownlint over the repository docs, spectral lint |
| **H-8 Backend: Django 5.2.17** | `Django` | Python | pin bump | full backend suite（Python 3.11, Postgres）, `manage.py check`, `migrate --plan` |
| **H-9 Backend: DRF 3.18.2** | `djangorestframework` | Python | **minor** bump | full backend suite; WS-04 throttle and permission tests; OpenAPI generation; auth / JWT flows |
| **H-10 Risk decisions（no code）** | `zod@3`（Expo CLI）, `webpack-dev-middleware`（Storybook）, `node-forge` | 2（plus the zod 3.x part of H-3's entry） | accept and dismiss with a reason, wait for upstream, or a major override | Mother Ship decision; record the rationale |

Notes:

- H-8 and H-9 are separate so that the minor DRF bump can be reverted alone.
- H-1 and H-6 both touch Mobile tooling. Keep them separate so that a Mobile build problem is easy to trace.
- The entry counts above sum to 69: H-1 27, H-2 9, H-3 1, H-4 2, H-5 11, H-6 4, H-7 13, H-10 2.
- Each PR should show, as in #3370 and #3372, that unrelated lockfile changes are explained or reverted, and that
  `pnpm install --lockfile-only` and `--frozen-lockfile` pass.

## 10. Uncertainties and verification gates

**Uncertainties:**

- **Alert mapping:** the Dependabot alert numbers, and how the 72 split between npm and Python, are not verified
  （no API access）. Before closing a PR, read the Dependabot list and confirm that the expected alerts close.
- **Python severity:** which Django / DRF findings Dependabot rates High is **Unknown**.
- **Scope counts:** 43 / 26（manifest）vs 52 / 20（Dependabot）is **unexplained**.
- **Usage classes:** these come from requirer chains and code search（Inferred）, not from bundle analysis. A bundle
  analysis of `next build`（e.g. `@next/bundle-analyzer`）would confirm that `follow-redirects` and the dev packages
  are absent from production output.
- **node-forge:** only the 1.4.2 change to `rsa.js` was reviewed.

**Recommended gates for every remediation PR:**

- `pnpm install --frozen-lockfile`;
- web `tsc`, lint, vitest and `next build`;
- mobile `tsc` and vitest, when Mobile tooling changes;
- Storybook build, when the Storybook tree changes;
- the full backend suite for Python PRs;
- an explained lockfile diff;
- `pnpm audit --audit-level high` before and after, showing only the targeted entries removed.

**Out of scope:**

- Goshuin feature and upload QA, which remain STOP;
- shrine data and recommendation logic, which are untouched.

## 11. Appendix: High advisory entries（npm, 69）

Generated from `pnpm audit --json --audit-level high` on `origin/develop@1170b60`. Section codes: `dep` =
`dependencies`, `dev` = `devDependencies`. The parent list is truncated after four entries.

| # | package | advisory | installed | vulnerable | patched | top-level parents（importer:package[section]） |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `@xmldom/xmldom` | GHSA-27p8-2357-5qqv | 0.9.10 | `>=0.9.0 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 2 | `@xmldom/xmldom` | GHSA-27p8-2357-5qqv | 0.8.13 | `>=0.7.0 <=0.8.14` | `>=0.8.15` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 3 | `@xmldom/xmldom` | GHSA-3px3-54cx-rmw9 | 0.9.10 | `>=0.9.0 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 4 | `@xmldom/xmldom` | GHSA-4w3w-2rp5-g8jm | 0.8.13 | `>=0.7.0 <=0.8.13` | `>=0.8.14` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 5 | `@xmldom/xmldom` | GHSA-4w3w-2rp5-g8jm | 0.9.10 | `>=0.9.0 <=0.9.10` | `>=0.9.11` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 6 | `@xmldom/xmldom` | GHSA-6mj3-qw4j-hgrw | 0.9.10 | `>=0.9.0-beta.1 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 7 | `@xmldom/xmldom` | GHSA-8344-3jmq-59r6 | 0.9.10 | `>=0.9.0 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 8 | `@xmldom/xmldom` | GHSA-8344-3jmq-59r6 | 0.8.13 | `>=0.7.0 <=0.8.14` | `>=0.8.15` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 9 | `@xmldom/xmldom` | GHSA-93r5-fhx6-vmg9 | 0.9.10 | `>=0.9.0 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 10 | `@xmldom/xmldom` | GHSA-93r5-fhx6-vmg9 | 0.8.13 | `>=0.7.0 <=0.8.14` | `>=0.8.15` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 11 | `@xmldom/xmldom` | GHSA-965w-775f-mr7g | 0.9.10 | `>=0.9.0 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 12 | `@xmldom/xmldom` | GHSA-965w-775f-mr7g | 0.8.13 | `>=0.7.0 <=0.8.14` | `>=0.8.15` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 13 | `@xmldom/xmldom` | GHSA-c7q8-3ch8-vqpv | 0.9.10 | `>=0.9.0 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 14 | `@xmldom/xmldom` | GHSA-c7q8-3ch8-vqpv | 0.8.13 | `>=0.7.0 <=0.8.14` | `>=0.8.15` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 15 | `@xmldom/xmldom` | GHSA-g53g-w8rj-fmg7 | 0.9.10 | `>=0.9.0-beta.9 <=0.9.10` | `>=0.9.11` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 16 | `@xmldom/xmldom` | GHSA-vr34-hp96-76pp | 0.9.10 | `>=0.9.10 <=0.9.11` | `>=0.9.12` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 17 | `@xmldom/xmldom` | GHSA-w2rr-34g9-rvrj | 0.8.13 | `>=0.7.0 <=0.8.13` | `>=0.8.14` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 18 | `@xmldom/xmldom` | GHSA-w2rr-34g9-rvrj | 0.9.10 | `>=0.9.0 <=0.9.10` | `>=0.9.11` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 19 | `@xmldom/xmldom` | GHSA-x4fp-j954-r2f4 | 0.8.13 | `>=0.7.0 <=0.8.14` | `>=0.8.15` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:expo-splash-screen[dep] …(+9) |
| 20 | `axios` | GHSA-3pq3-5fj3-cg6v | 1.19.0 | `>=1.13.0 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 21 | `axios` | GHSA-542g-h47m-68v8 | 1.19.0 | `>=1.13.0 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 22 | `axios` | GHSA-c29m-xwm3-cm6r | 1.19.0 | `>=1.16.1 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 23 | `axios` | GHSA-m8m8-qj5v-23w3 | 1.19.0 | `>=1.15.2 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 24 | `axios` | GHSA-mghh-pgcx-3jjj | 1.19.0 | `>=1.15.0 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 25 | `axios` | GHSA-r4gj-5m52-g5wh | 1.19.0 | `>=1.17.0 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 26 | `axios` | GHSA-x97p-jq2g-jp4f | 1.19.0 | `>=1.15.1 <1.20.0` | `>=1.20.0` | apps/web:axios[dep] |
| 27 | `brace-expansion` | GHSA-3jxr-9vmj-r5cp | 5.0.5 | `>=3.0.0 <5.0.7` | `>=5.0.7` | apps/mobile:expo-router[dep], apps/web:eslint-config-next[dev], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep] …(+26) |
| 28 | `brace-expansion` | GHSA-6j4f-fj2g-mc7p | 5.0.5 | `>=4.0.0 <5.0.10` | `>=5.0.10` | apps/mobile:expo-router[dep], apps/web:eslint-config-next[dev], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep] …(+26) |
| 29 | `brace-expansion` | GHSA-mh99-v99m-4gvg | 5.0.5 | `>=4.0.0 <5.0.8` | `>=5.0.8` | apps/mobile:expo-router[dep], apps/web:eslint-config-next[dev], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep] …(+26) |
| 30 | `brace-expansion` | GHSA-qhr7-859c-m2p7 | 5.0.5 | `>=4.0.0 <5.0.11` | `>=5.0.11` | apps/mobile:expo-router[dep], apps/web:eslint-config-next[dev], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep] …(+26) |
| 31 | `brace-expansion` | GHSA-rgw5-rvv9-x895 | 5.0.5 | `>=4.0.0 <5.0.9` | `>=5.0.9` | apps/mobile:expo-router[dep], apps/web:eslint-config-next[dev], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep] …(+26) |
| 32 | `browserslist` | GHSA-73wf-gq98-2v4g | 4.28.5 | `<=4.28.6` | `>=4.28.7` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:posthog-react-native[dep] …(+22) |
| 33 | `browserslist` | GHSA-c83g-rgw3-j3cx | 4.28.5 | `<=4.28.6` | `>=4.28.7` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:posthog-react-native[dep] …(+22) |
| 34 | `compression` | GHSA-vc2v-76pw-4v95 | 1.8.1 | `<1.8.2` | `>=1.8.2` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:@expo/vector-icons[dep] …(+9) |
| 35 | `fast-uri` | GHSA-4c8g-83qw-93j6 | 3.1.0 | `>=3.0.0 <3.1.3` | `>=3.1.3` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 36 | `fast-uri` | GHSA-7p8r-x3mc-p8w7 | 3.1.0 | `>=3.0.0 <3.1.5` | `>=3.1.5` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 37 | `fast-uri` | GHSA-f65p-4m7j-42xc | 3.1.0 | `>=3.0.0 <3.1.6` | `>=3.1.6` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 38 | `fast-uri` | GHSA-jqff-g426-hqxp | 3.1.0 | `>=3.0.0 <3.1.6` | `>=3.1.6` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 39 | `fast-uri` | GHSA-q3j6-qgpj-74h6 | 3.1.0 | `>=3.0.0 <=3.1.0` | `>=3.1.1` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 40 | `fast-uri` | GHSA-qw65-cvwx-89v3 | 3.1.0 | `>=3.0.0 <3.1.7` | `>=3.1.7` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 41 | `fast-uri` | GHSA-v2hh-gcrm-f6hx | 3.1.0 | `>=3.0.0 <=3.1.3` | `>=3.1.4` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 42 | `fast-uri` | GHSA-v39h-62p7-jpjc | 3.1.0 | `>=3.0.0 <=3.1.1` | `>=3.1.2` | apps/web:@storybook/nextjs[dev], .:@stoplight/spectral-cli[dev] |
| 43 | `follow-redirects` | GHSA-8r9p-f939-6h3c | 1.16.0 | `>=1.16.0 <1.16.1` | `>=1.16.1` | apps/web:axios[dep] |
| 44 | `follow-redirects` | GHSA-q3jh-wrc6-jgq8 | 1.16.0 | `>=1.16.0 <1.16.1` | `>=1.16.1` | apps/web:axios[dep] |
| 45 | `js-yaml` | GHSA-2883-xcg3-v3hh | 4.1.1 | `>=4.0.0 <4.3.2` | `>=4.3.2` | apps/web:eslint-config-next[dev], .:typescript-eslint[dev], apps/web:typescript-eslint[dev], apps/mobile:expo-router[dep] …(+24) |
| 46 | `js-yaml` | GHSA-52cp-r559-cp3m | 4.1.1 | `>=4.0.0 <4.3.0` | `>=4.3.0` | apps/web:eslint-config-next[dev], .:typescript-eslint[dev], apps/web:typescript-eslint[dev], apps/mobile:expo-router[dep] …(+24) |
| 47 | `js-yaml` | GHSA-5p4m-2wfm-xmqj | 4.1.1 | `>=4.0.0 <4.3.1` | `>=4.3.1` | apps/web:eslint-config-next[dev], .:typescript-eslint[dev], apps/web:typescript-eslint[dev], apps/mobile:expo-router[dep] …(+24) |
| 48 | `linkify-it` | GHSA-22p9-wv53-3rq4 | 5.0.0 | `<=5.0.0` | `>=5.0.1` | .:markdownlint-cli[dev] |
| 49 | `linkify-it` | GHSA-v245-v573-v5vm | 5.0.0 | `<=5.0.1` | `>=5.0.2` | .:markdownlint-cli[dev] |
| 50 | `lodash` | GHSA-r5fr-rjxr-66jc | 4.17.23 | `>=4.0.0 <=4.17.23` | `>=4.18.0` | .:@stoplight/spectral-cli[dev], apps/web:@storybook/nextjs[dev], apps/web:ts-prune[dev] |
| 51 | `markdown-it` | GHSA-gfr2-rv44-r23c | 14.1.1 | `>=14.1.0 <14.3.3` | `>=14.3.3` | .:markdownlint-cli[dev] |
| 52 | `markdown-it` | GHSA-r7fv-28h4-cvq7 | 14.1.1 | `<14.3.2` | `>=14.3.2` | .:markdownlint-cli[dev] |
| 53 | `node-forge` | GHSA-86w9-cpqp-85rv | 1.4.0 | `<=1.4.0` | `<0.0.0` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], apps/mobile:@expo/vector-icons[dep] …(+9) |
| 54 | `sharp` | GHSA-rgj7-g3m4-5g8c | 0.35.3 | `<0.35.4` | `>=0.35.4` | apps/web:@storybook/nextjs[dev], apps/web:sharp[dep] |
| 55 | `sharp` | GHSA-wq5f-xc86-pv6w | 0.35.3 | `<0.35.5` | `>=0.35.5` | apps/web:@storybook/nextjs[dev], apps/web:sharp[dep] |
| 56 | `smol-toml` | GHSA-7w5x-hrqm-74c2 | 1.5.2 | `<=1.7.0` | `>=1.7.1` | .:markdownlint-cli[dev] |
| 57 | `source-map-js` | GHSA-68fv-2mgg-jv7q | 1.2.1 | `>=1.0.0 <1.2.2` | `>=1.2.2` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:vitest[dev], apps/web:jsdom[dev] …(+1) |
| 58 | `undici` | GHSA-2m5v-pch6-74hx | 7.28.0 | `>=7.0.0 <7.30.1` | `>=7.30.1` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 59 | `undici` | GHSA-4cwx-7wf7-3272 | 7.28.0 | `>=7.0.0 <7.29.0` | `>=7.29.0` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 60 | `undici` | GHSA-4w7w-5xrc-9h26 | 7.28.0 | `>=7.0.0 <7.30.1` | `>=7.30.1` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 61 | `undici` | GHSA-qrxm-fqhp-jwvm | 7.28.0 | `>=7.0.0 <7.30.1` | `>=7.30.1` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 62 | `undici` | GHSA-rfgv-xxqx-mfg5 | 7.28.0 | `>=7.0.0 <7.29.1` | `>=7.29.1` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 63 | `undici` | GHSA-w293-vg96-wgc3 | 7.28.0 | `>=7.24.1 <7.29.1` | `>=7.29.1` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 64 | `undici` | GHSA-xjj6-f33q-929c | 7.28.0 | `>=7.18.0 <7.30.1` | `>=7.30.1` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:jsdom[dev], apps/web:vitest[dev] |
| 65 | `vite` | GHSA-587h-7wmj-h5pm | 7.3.1 | `>=7.0.0 <=7.3.6` | `>=7.3.7` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:vitest[dev], .:vite-tsconfig-paths[dev] …(+2) |
| 66 | `vite` | GHSA-p9ff-h696-f583 | 7.3.1 | `>=7.0.0 <=7.3.1` | `>=7.3.2` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:vitest[dev], .:vite-tsconfig-paths[dev] …(+2) |
| 67 | `vite` | GHSA-v2wj-q39q-566r | 7.3.1 | `>=7.1.0 <=7.3.1` | `>=7.3.2` | apps/mobile:vitest[dev], apps/web:@vitest/coverage-v8[dev], apps/web:vitest[dev], .:vite-tsconfig-paths[dev] …(+2) |
| 68 | `webpack-dev-middleware` | GHSA-g84c-rxfj-3j2c | 6.1.3 | `<7.4.5` | `>=7.4.6` | apps/web:@storybook/nextjs[dev] |
| 69 | `zod` | GHSA-mrhx-c7xc-m3w5 | 3.25.76, 4.4.3 | `<4.6.6` | `>=4.6.6` | apps/mobile:expo-router[dep], apps/mobile:@expo/metro-runtime[dep], apps/mobile:expo-image-picker[dep], .:eslint-plugin-react-hooks[dev] …(+13) |

**Python（pip-audit, PyPI vulnerability service, `backend/requirements-dev.txt`）:**

| package | installed | id | aliases | fix versions |
| --- | --- | --- | --- | --- |
| Django | 5.2.16 | PYSEC-2026-3717 | CVE-2026-15830, GHSA-q238-5cxm-5c9h | 5.2.17, 6.0.8, 6.1.1 |
| Django | 5.2.16 | PYSEC-2026-4035 | CVE-2026-15307, GHSA-wvqv-fj8w-qmhm | 5.2.17, 6.0.8 |
| djangorestframework | 3.17.2 | CVE-2026-114138 | GHSA-33wh-fxxf-88vv | 3.18.2 |
| djangorestframework | 3.17.2 | CVE-2026-114136 | GHSA-3547-9m27-7rxg | 3.18.2 |
| djangorestframework | 3.17.2 | CVE-2026-114137 | GHSA-xw6w-gcfp-cf8m | 3.18.2 |

pip-audit printed PYSEC-2026-3717 twice, with two fix lists; it is one vulnerability.
