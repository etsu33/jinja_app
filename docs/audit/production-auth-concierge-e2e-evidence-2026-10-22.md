# Production auth and concierge browser E2E evidence (2026-10-22)

## Purpose and evidence boundary
Read-only documentation of a Mother Ship-executed browser smoke test on the production web deployment. Evidence: three user-supplied screenshots for Vercel project view, concierge request in progress, and resulting recommendation (2026-10-22); additional user-supplied screenshot showing the signed-in My Page after logout and subsequent login (2026-10-22). The screenshots remain conversation attachments, not files in this repository. No login credentials, email address, session tokens, browser cookies or full consultation text are copied here.

## Observed behavior

| Check | Result | Basis |
| --- | --- | --- |
| Web frontend opens | PASS | Vercel production web URL shown in browser screenshot |
| Signed-in My Page UI | PASS (screen/UI evidence) | My Page account card and Logout visible |
| Concierge submission | PASS (user report + UI evidence) | Browser shows the entered theme followed by a result |
| Concierge recommendation UI | PASS | Shrine candidate and reason/action areas visible |
| Thread id issued | OBSERVED | Result page URL shows `tid=85` (test thread, not a protected credential) |
| Recent consultation on My Page | PASS | My Page Recent Consultations card displays the same consultation theme |
| Logout then login followed by recent consultation re-display | PASS (Mother Ship operation report plus screenshot) | Mother Ship explicitly states logout/re-login and shows resulting My Page |
| Saved shrine card reappears | OBSERVED | My Page saved-shrine section displays one shrine |
| Opening consultation detail again | NOT_VERIFIED | No post-login detail-view screenshot |
| Cross-account thread isolation | NOT_VERIFIED | No second-user access-control QA |
| API request tracing / DB persistence mechanism | NOT_VERIFIED IN THIS AUDIT | UI continuity is evidenced; implementation mechanism not independently instrumented |

No blanket claim is made about production authentication security, data isolation, performance, or complete concierge quality. A working personal-history display after logging back in is evidence of user-visible persistence across auth sessions, not proof of every DB invariant.

## Follow-ups
1. Open the persisted consultation after login and verify recommendation detail rendering.
2. Using an authorized separate QA account, verify that accessing another user's consultation thread does not expose it. Do not publish tokens, IDs tied to real users, cookies, or response bodies.
3. Record only observed statuses/timestamps in a separate closure audit if these QA checks pass.

```text
PRODUCTION_WEB_RENDER = PASS
LOGIN_UI_PRESENT = PASS
CONCIERGE_RESULT_RENDER = PASS
CONSULTATION_VISIBLE_AFTER_RELOGIN = PASS (MOTHER_SHIP_REPORT + SCREENSHOT)
SAVED_SHRINE_VISIBLE_AFTER_RELOGIN = OBSERVED
THREAD_DETAIL_REOPEN = NOT_VERIFIED
CROSS_ACCOUNT_ACCESS_CONTROL = NOT_VERIFIED
SOURCE_DB_RUNTIME_WRITES_IN_THIS_PR = NONE
```
