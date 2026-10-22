# Production Concierge Thread Isolation E2E Evidence — 2026-10-22

## Scope

Documentation-only follow-up to merged PR #3309 (merge commit `1b384d9dcbd341803af940bfedc6e5d893a4cbb8`). This record separates observed frontend/API behavior from product decisions and remaining security QA. No production code, configuration, database, or consultation data changes.

## Evidence provided by Mother Ship

- Two authenticated QA account screenshots for the same URL path `/concierge?tid=92` on 2026-10-22 circa 17:01 JST. One screenshot shows consultation-specific recommendation content and another shows no consultation-specific recommendation content.
- Account identities differ per Mother's statement. The screenshots do not themselves contain sufficient account identification to independently bind each API request to its user.
- In the earlier `tid=88` investigation, a screenshot of an Incognito window showing consultation-specific content existed **before** PR #3309 was merged. That phenomenon was not conclusively explained by the confirmed local-cache defect. Do not carry forward a passing Incognito result from old tests.

## Production Render API evidence

For `GET /api/concierge-threads/92/` (JST, 2026-10-22):

| Time | HTTP |
| --- | --- |
| 17:01:02 | 200 |
| 17:01:07 | 200 |
| 17:01:19 | 404 |
| 17:01:23 | 404 |

These observations are consistent with the UI contrast (authorized content displayed versus denied/no-content view). The server access log does not independently identify the account behind each response. No raw requests, secrets, cookies, consultation text, account emails, or IPs are reproduced here.

## Assessment

- **UI account-separation smoke test:** PASS-equivalent based on Mother Ship screenshots and reported account switch.
- **API denial occurrence:** VERIFIED (404); other requests returned 200. Account-to-response association remains indirect.
- **Full cross-account authorization E2E:** NOT FORMALLY CLOSED pending bounded re-test.
- **Fresh Incognito unauthorized request after PR #3309:** NOT EXECUTED / NO PASS CLAIM.
- **Authenticated + signed anonymous-cookie on a shared browser:** PRODUCT-CONTRACT DECISION PENDING. Existing backend logic permits access to ownerless threads matching that browser's signed anonymous cookie, even when another authenticated account is active. This is not the same as authenticated account A's owned thread being shared with B.

## Mother Ship gate: anonymous cookie handling on shared devices

Unresolved policy question: should an anonymous consultation associated with a shared browser remain accessible after an account change, or should that association be isolated/cleared at an authentication boundary? No behavioral changes may be inferred or implemented from this record. Record an explicit Mother Ship decision and required guest-to-login preservation behavior before any change.

## Remaining QA (authorized test data only)

1. On confirmed production deployment containing PR #3309, open an owned test thread in account A. Expect content and a 200 for the detail API.
2. In a separately authenticated account B, open exactly the same A-owned test thread URL. Expect no A private content and a 404 for the detail API. Correlate requests by timestamp and browser Network status. Do not log personal content.
3. In a **new** Incognito window without login or previously created anonymous consultation, open the same URL. Expect 404 and no consultation-specific content. Confirm Network status, not merely UI appearance.
4. Independently confirm an anonymous visitor can reopen its own anonymous test consultation in the same browser identity.
5. Observe behavior after anonymous guest → login and account-switch on a shared test browser, and refer any desired policy change to Mother Ship.

## Gate status

```text
PR_3309 = MERGED
ACCOUNT_SEPARATION_UI_SMOKE = PASS_EQUIVALENT
DETAIL_API_200_AND_404 = OBSERVED
FRESH_INCOGNITO_PRODUCTION_QA = OPEN
ANONYMOUS_COOKIE_SHARED_DEVICE_POLICY = MOTHER_SHIP_DECISION_PENDING
PRODUCTION_SECURITY_E2E = OPEN
```

STOP: Do not mark formal security E2E closed or claim new Incognito verification until real evidence is recorded.
