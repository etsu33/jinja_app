# Billing Sandbox Price 780 Alignment Audit

## Status

```text
AUDIT_DATE = 2026-09-24
SCOPE = Stripe Sandbox / Render configuration alignment only
CANONICAL_BETA_EARLY_USER_PRICE = 780 JPY / month
CONFIGURATION_LEVEL_QA = PASS
ROLLBACK_PRICE_ID_RECORDED = PASS
CHECKOUT_RUNTIME_E2E = NOT_EXECUTED
WEBHOOK_ENTITLEMENT_E2E = NOT_EXECUTED
PRODUCTION_WRITE = NONE_BY_THIS_QA
LIVE_MODE_CHANGE = NONE
```

This audit records the external configuration alignment for KAMI MUSUBI Premium billing.

Mother Ship has fixed the beta Early User price at **780 JPY / month**. The recurring value under test is Premium access for Concierge, Deep Meaning, Reflection, Compass, and Weekly Compass.

This change does not modify recommendation logic, Concierge logic, backend billing logic, API contracts, DB schema, ranking, worldview UI, or mobile.

---

## 1. Canonical price

The canonical beta Early User price is:

```text
Premium = 780 JPY / month
```

Repository-side checks confirmed that the Web Premium upgrade UI and Terms already display 780 JPY / month.

Therefore this task aligns Stripe Sandbox and Render configuration to the existing product/UI contract rather than changing application pricing logic.

---

## 2. Stripe Sandbox Price

A new recurring Price was created under the existing Premium product in Stripe Sandbox.

```text
MODE = Sandbox / Test
CURRENCY = JPY
UNIT_AMOUNT = 780
INTERVAL = month
PRICE_ID = price_1UJBp0K6oORw8IU8VzEqunrt
```

The existing **500 JPY / month** Sandbox Price was intentionally retained during the cutover.

It was not deleted or archived during this task.

### Rollback note

The rollback object is the retained 500 JPY / month Price under the same Premium Sandbox product.

```text
ROLLBACK_PRICE = 500 JPY / month
ROLLBACK_PRICE_ID = price_1T3vXgK6oORw8IU8mmYrl8X1
ROLLBACK_PRICE_STATUS = RETAINED
```

The rollback Price was not deleted or archived during this task. If rollback is required, the retained 500 JPY / month Sandbox Price above is the configuration target.

No Live Price was created.

---

## 3. Render configuration

Target service:

```text
WORKSPACE = エツ's workspace
SERVICE = jinja-backend
BRANCH = develop
HEALTH_CHECK_PATH = /healthz/
```

Configuration after alignment:

```text
BILLING_PROVIDER = stripe
STRIPE_PRICE_ID = price_1UJBp0K6oORw8IU8VzEqunrt
STRIPE_PREMIUM_PRICE_ID = not present in the Render environment list during QA
```

The repository billing checkout implementation resolves the Stripe Price ID in this order:

```text
STRIPE_PREMIUM_PRICE_ID
-> fallback to STRIPE_PRICE_ID
```

Because no Render `STRIPE_PREMIUM_PRICE_ID` override was present during QA, the effective configured checkout Price resolves to:

```text
price_1UJBp0K6oORw8IU8VzEqunrt
```

### Secret handling

`STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` were not changed.

The existing Stripe secret key is the pre-existing **test-mode key** confirmed for this task. Its value is intentionally not recorded here.

No secret values are included in this document.

---

## 4. Deploy result

### First deploy attempt

The first Render deployment after the environment change used:

```text
DEPLOY_ID = dep-daqhjkgu01pc7386vr40
SOURCE_COMMIT = 644675a8478c2607a211fa5803bb3f4cc461a992
RESULT = update_failed
FAILURE = port scan / deploy timeout
```

Observed application startup evidence before failure:

```text
gunicorn bound to 0.0.0.0:10000
migration execution skipped
production bootstrap skipped
```

The previous live instance continued returning HTTP 200 from `/healthz/`.

### Single retry

One retry was performed under the same backend runtime configuration.

The retry used a newer `develop` commit because docs-only changes had landed between attempts:

```text
DEPLOY_ID = dep-daqhtkm7bikc738j2jjg
SOURCE_COMMIT = 963bd7f318b0b6963b1f5dc9cf420ca74c676bf8
RESULT = live
```

The commit difference introduced no backend runtime change relevant to billing or port binding.

Successful startup evidence:

```text
HEAD / = 200
GET /healthz/ = 200
Render status = live
Primary URL = https://jinja-backend.onrender.com
```

The first port-detection failure did not reproduce on the single retry and is therefore recorded as a transient Render deployment failure for this audit.

---

## 5. Migration / production-write boundary

During both deployment attempts:

```text
0115_canonical_anchor_schema_foundation = NOT APPLIED
RUN_MIGRATIONS_ON_START = skipped
Production data bootstrap = skipped
```

No migration or intentional Production DB write was performed as part of this billing alignment QA.

---

## 6. Configuration-level Checkout QA

The following configuration path is verified:

```text
Stripe Sandbox Premium Price
  780 JPY / month
  price_1UJBp0K6oORw8IU8VzEqunrt
        |
        v
Render jinja-backend
  BILLING_PROVIDER=stripe
  STRIPE_PRICE_ID=price_1UJBp0K6oORw8IU8VzEqunrt
        |
        v
backend billing checkout price resolution
  effective Price ID = price_1UJBp0K6oORw8IU8VzEqunrt
```

Result:

```text
STRIPE_SANDBOX_PRICE = PASS
RENDER_PRICE_ID_MATCH = PASS
BILLING_PROVIDER = PASS
TEST_MODE_BOUNDARY = PASS
BACKEND_DEPLOY = PASS
BACKEND_HEALTH = PASS
WEB_UI_PRICE_780 = PASS
TERMS_PRICE_780 = PASS
CONFIGURATION_LEVEL_CHECKOUT_PRICE = PASS
ROLLBACK_PRICE_REFERENCE = PASS
```

This proves the configuration path used to create a Checkout Session resolves to the new 780 JPY/month Sandbox Price.

It does **not** prove a real Checkout Session, webhook, entitlement update, or Customer Portal flow end to end.

---

## 7. Production write gate

Per Mother Ship boundary, the following were intentionally not executed:

```text
REAL_USER_CHECKOUT = NOT_EXECUTED
STRIPE_WEBHOOK_E2E = NOT_EXECUTED
ENTITLEMENT_WRITE_QA = NOT_EXECUTED
CUSTOMER_PORTAL_E2E = NOT_EXECUTED
```

Reason:

```text
PRODUCTION_WRITE_GATE
```

A Checkout / webhook flow against the production backend may update `UserProfile` subscription state. That QA requires explicit Mother Ship approval before execution.

---

## 8. Scope integrity

No changes were made to:

- Stripe Live Mode
- Live Price objects
- Live webhook configuration
- `BILLING_PROVIDER`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- Recommendation
- Concierge logic
- backend billing logic
- API contract
- DB schema
- ranking
- worldview UI
- mobile

---

## 9. Current gate

```text
SANDBOX_PRICE_ALIGNMENT = PASS
CONFIGURATION_LEVEL_QA = PASS
BACKEND_HEALTH = PASS
CHECKOUT_RUNTIME_E2E = BLOCKED_BY_PRODUCTION_WRITE_GATE
MERGE = MOTHER_SHIP_DECISION
LIVE_MODE_MIGRATION = NOT_AUTHORIZED
```

The next allowed repository step is to preserve this audit evidence in the PR.

Runtime Checkout / webhook / entitlement verification must remain stopped until Mother Ship explicitly approves Production-write QA.
