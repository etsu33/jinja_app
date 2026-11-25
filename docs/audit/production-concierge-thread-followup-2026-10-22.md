# Production concierge history follow-up — 2026-10-22

## Evidence
- Mother Ship provided screenshots of a new concierge consultation and a My Page history screen from the production web application, captured about 12:45–12:46 JST.
- The recent consultation appears in the My Page list; older consultations and saved shrines are also visible. Screenshots do not independently show that the recent consultation's **detail** was reopened after logout/re-login, nor establish whether screens represent different accounts.
- Render application access logs for 12:42–12:47 JST include:
  - 12:42:03 `GET /api/concierge-threads/` → 401 (unauthorized)
  - 12:45:33 `GET /api/concierge-threads/` → 200
  - 12:45:59 `GET /api/concierge-threads/86/` → 200
  - 12:46:01 `GET /api/concierge-threads/28/` → 200
  - 12:46:40 `GET /api/concierge-threads/` → 200
- Access logs give response statuses, **not** independently verified identities of the users making those requests. A 401 on the history list tests unauthenticated behavior, **not** cross-account thread isolation.
- The current source implementation for `ConciergeThreadDetailView` uses a logged-in-user filter, or anonymous_id filter for anonymous threads, then returns 404 when neither matches. Source inspection is *not* production evidence that a separately authenticated user cannot access another user's thread.
- These are observations only. No credentials, account emails, tokens, cookies, personally identifying account details, or detailed consultations are added to the repository.

## Gate results
```text
RECENT_CONSULTATION_MY_PAGE_LIST = PASS (USER_SCREENSHOT)
HISTORY_DETAIL_API_RESPONDED_200 = PASS (RENDER_LOGS; USER ID UNVERIFIED)
DETAIL_REOPEN_AFTER_RELOGIN = NOT_VERIFIED
OTHER_QA_ACCOUNT_THREAD_ACCESS_DENIED = NOT_VERIFIED
PRODUCTION_SECURITY_E2E_FORMAL_CLOSURE = NOT_AUTHORIZED
RUNTIME_DB_OR_ACCOUNT_WRITES_BY_THIS_PR = NONE
```

## Follow-up
1. From the intended QA account, log out, log back in, and open the **same consultation detail** via My Page, then record a screenshot with only non-sensitive information visible.
2. Using a *separate, authorized QA account*, attempt to open the first QA account's own test consultation detail; expected outcome: no consultation data returned (404 or equivalent denial). Record response status only. Do not use real user consultation IDs, share credentials, or treat absence of a listing as proof of detail isolation.
3. Decide closure only after these independent checks pass.
