# ConciergeHandoffGrant — Exact Django Model Proposal

## 1. Status

```text
APPROACH                        = A（database-backed handoff grant; approved, G0）
EXACT SCHEMA                    = CONDITIONALLY APPROVED（M1–M6, G1）→ final schema diff（§3, §3.1）needs Mother Ship review
models.py / migrations          = UNCHANGED（no migration created or applied）
endpoints / UI / cookies / auth = UNCHANGED
consultation data               = UNCHANGED
PRODUCTION_SECURITY_E2E         = OPEN
REVIEW CORRECTIONS（rev 2）      = APPLIED（§1.1, §5.5, §7, §10.1, §11.1, §12, §13, §13.1）
REVOKED_REASON（rev 3）          = ADDED to the proposal（§3, §3.1, §5.4, §5.6, §5.7, §7, §9, §10, §11.0, §13.2）
CONSISTENCY FIX（rev 3.1）       = D1–D4 corrected（§1.1, §8, §11.3, §13, §13.1, §13.2）; no schema change
FINAL STATUS                    = STOP — awaiting Mother Ship final G1 schema approval
```

### 1.1 Approval gates（rev 3）

Approval of one gate does **not** imply approval of a later one.

| gate | scope | status |
| --- | --- | --- |
| G0 — requirements | approach A; 30-min expiry; single use; reissue revokes earlier open grants; no consultation deletion; no automatic transfer; a new table in principle | **APPROVED** |
| G1 — schema | the exact fields, constraints, index names and on-delete behaviour in §3, including the M1–M6 choices | **CONDITIONALLY APPROVED**: M1–M6 proposals approved on condition that `revoked_reason` is added under M3（done in rev 3）. The **final schema diff**（§3.1）**needs Mother Ship review**. Not final |
| G2 — migration | creating `0122_conciergehandoffgrant` in the repository | policy（M8）approved in principle. **Creating or applying the migration is NOT APPROVED**; requires final G1. A separate gate from G3 even if one PR carries both（§13, M8 note） |
| G3 — implementation | services, endpoints, BFF routes, UI, the retention-purge change（§10.1）and the shared prerequisites（M9） | policies M7, M9, M11 approved in principle（M10 is a separate PR）. **Runtime implementation is NOT APPROVED**; requires final G1 and G2 |
| G4 — product policy | logout rotation（P1）and lost-code recovery（P2）, §13.1 | **UNRESOLVED**; blocks G3 for the UI flow. **May also reopen G1**（rev 3.1, D1）: the final P1 policy may require an additional revocation reason or another schema change, which would need a new G1 review and a migration change. This record proposes no such value and does not choose P1（§13.1） |
| G5 — deployment | applying the migration to Production and enabling the flow | **NOT APPROVED**; requires G1–G4 and the Production QA plan |

Even a final G1 approval only makes §3 the target of a later migration PR. It does not authorize creating
that migration, writing endpoints or changing retention.

- Source of truth: `origin/develop@8640287`（rev 3）. `git diff 1465c5d 8640287 -- backend` is empty, so every
  fact in §2 still holds; the one new commit（#3314）is a docs-only mobile QA record. Django **5.2.16**
  （`backend/requirements.txt`）. `DEFAULT_AUTO_FIELD = BigAutoField`（`backend/shrine_project/settings.py:456`）.
  Latest migration: still `0121_shrine_fact_source_citation`.
- rev 3.1 base: `origin/develop@89f7f79`（#3315 merged）. `git diff 1465c5d 89f7f79 -- backend` is empty, and the
  latest migration is still `0121`. The merge of #3315 is **not** a Mother Ship G1 approval.
- Builds on `docs/audit/anonymous-handoff-code-db-lifecycle-audit-2026-10-22.md`（approach A, §4.2）. This
  record replaces its sketch with exact declarations.
- **Verification:** the model below was compiled and exercised in a **throwaway scratch Django project**
  outside the repository. It ran against the local PostgreSQL 16 test server, with a mirror of
  `ConciergeThread`'s ownership fields and constraint. 16 tests passed in rev 1; 25 tests passed in each of
  three variants in rev 2（§11.1）, against the rev 2 model. In rev 3, 22 tests passed against the rev 3
  model（§11.0）, three consecutive runs. The 25 rev 2 tests were **not** re-run against the rev 3 model. The
  scratch databases were dropped afterwards. Nothing ran against Production, and nothing in the repository
  changed except this file.
- Labels: **Fact** = verified in source or by that scratch run. **Inference** = reasoned, not executed.
  **Proposal** = for approval.

---

## 2. Current implementation（verified on develop）

| # | fact | location |
| --- | --- | --- |
| C1 | `ConciergeThread.user`: FK, `null=True`, `on_delete=CASCADE`, `related_name="concierge_threads"` | `backend/temples/models.py:1321-1327` |
| C2 | `anonymous_id`: `CharField(max_length=64, null=True, blank=True, db_index=True)` | `models.py:1328` |
| C3 | Ownership constraint `concierge_thread_user_or_anonymous_required`: `user IS NOT NULL OR anonymous_id IS NOT NULL`. It is declared with the **deprecated `check=`** keyword | `models.py:1353-1358`; migration `0078_conciergethread_anonymous_id_and_more.py` |
| C4 | No field for a handoff secret, expiry, consumption, revocation or attempts | `models.py:1320-1361` |
| C5 | `append_chat` is `@transaction.atomic` and locks the thread with `select_for_update()` | `backend/temples/services/concierge_history.py:349-375` |
| C6 | The anonymous `append_chat` branch matches `(id, anonymous_id)` without `user__isnull=True` | `concierge_history.py:371-375` |
| C7 | Guest retention deletes `user IS NULL` threads by `last_message_at` / `created_at` < cutoff（manual command, unscheduled） | `backend/temples/services/guest_data_retention.py:51-67` |
| C8 | Account deletion ends in `user.delete()`; threads CASCADE | `backend/users/services/account_deletion.py:372` |
| C9 | Other models use `condition=` and `__regex` checks（e.g. `models.py:847, 940`）. No model uses `db_default` | `models.py` |
| C10 | No test asserts C3 for `ConciergeThread`; an `IntegrityError` test exists only for `FeatureUsage` | `backend/temples/tests/services/test_guest_data_retention.py:310-323` |
| C11 | Production is PostgreSQL / PostGIS; the local fallback is SQLite | `settings.py:165-177` |
| C12 | `django.db.models.functions.Now()` compiles to `STATEMENT_TIMESTAMP()` on PostgreSQL | Django 5.2.16 source |
| C13 | Django 5.2 emits `RemovedInDjango60Warning` for `CheckConstraint(check=…)` | scratch run |

---

## 3. Proposed model（exact code）

Placement: `backend/temples/models.py`, directly after `ConciergeMessage`. The imports `timedelta`, `F`,
`Q` and `Now` are added only if not already present.

```python
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now

HANDOFF_GRANT_TTL = timedelta(minutes=30)
HANDOFF_GRANT_MAX_FAILED_ATTEMPTS = 5  # Mother Ship decision M2


class HandoffGrantRevokedReason(models.TextChoices):
    """ConciergeHandoffGrant.revoked_reason の値。期限切れは revoke ではない（§5.6）。"""

    REISSUED = "reissued", "reissued"
    CANCELLED = "cancelled", "cancelled"
    LOCKED_OUT = "locked_out", "locked out"


class ConciergeHandoffGrant(models.Model):
    """匿名相談 thread を認証済み account へ引き継ぐための、使い捨ての権限。

    secret そのものは保存しない。selector で行を引き、verifier の SHA-256 を照合する。
    行の削除や失効で thread が消えることはない（FK は grant → thread の向き）。
    docs/audit/concierge-handoff-grant-schema-proposal.md
    """

    id = models.BigAutoField(primary_key=True)
    thread = models.ForeignKey(
        "ConciergeThread",
        on_delete=models.CASCADE,
        related_name="handoff_grants",
    )
    selector = models.CharField(max_length=16, unique=True)
    verifier_hash = models.CharField(max_length=64)
    anon_binding = models.CharField(max_length=64)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    expires_at = models.DateTimeField(db_default=Now() + HANDOFF_GRANT_TTL, editable=False)
    consumed_at = models.DateTimeField(null=True, blank=True)
    consumed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(
        max_length=16,
        choices=HandoffGrantRevokedReason.choices,
        null=True,
        blank=True,
    )
    failed_attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["thread"],
                condition=Q(consumed_at__isnull=True, revoked_at__isnull=True),
                name="concierge_handoff_one_open_grant_per_thread",
            ),
            models.CheckConstraint(
                condition=Q(consumed_at__isnull=True) | Q(revoked_at__isnull=True),
                name="concierge_handoff_not_consumed_and_revoked",
            ),
            models.CheckConstraint(
                condition=Q(consumed_by__isnull=True) | Q(consumed_at__isnull=False),
                name="concierge_handoff_consumer_requires_consumed_at",
            ),
            models.CheckConstraint(
                condition=Q(expires_at__gt=F("created_at"))
                & Q(expires_at__lte=F("created_at") + HANDOFF_GRANT_TTL),
                name="concierge_handoff_ttl_bounds",
            ),
            models.CheckConstraint(
                condition=Q(consumed_at__isnull=True)
                | (Q(consumed_at__gte=F("created_at")) & Q(consumed_at__lt=F("expires_at"))),
                name="concierge_handoff_consumed_within_ttl",
            ),
            models.CheckConstraint(
                condition=Q(revoked_at__isnull=True) | Q(revoked_at__gte=F("created_at")),
                name="concierge_handoff_revoked_after_created",
            ),
            models.CheckConstraint(
                condition=(Q(revoked_at__isnull=True) & Q(revoked_reason__isnull=True))
                | (Q(revoked_at__isnull=False) & Q(revoked_reason__isnull=False)),
                name="concierge_handoff_revoked_reason_pairing",
            ),
            models.CheckConstraint(
                condition=Q(revoked_reason__isnull=True)
                | Q(revoked_reason__in=HandoffGrantRevokedReason.values),
                name="concierge_handoff_revoked_reason_values",
            ),
            models.CheckConstraint(
                condition=Q(failed_attempts__lte=HANDOFF_GRANT_MAX_FAILED_ATTEMPTS),
                name="concierge_handoff_failed_attempts_cap",
            ),
            models.CheckConstraint(
                condition=Q(failed_attempts__lt=HANDOFF_GRANT_MAX_FAILED_ATTEMPTS)
                | (
                    Q(revoked_reason__isnull=False)
                    & Q(revoked_reason=HandoffGrantRevokedReason.LOCKED_OUT)
                ),
                name="concierge_handoff_lockout_requires_locked_out_reason",
            ),
            models.CheckConstraint(
                condition=Q(revoked_reason__isnull=True)
                | Q(
                    revoked_reason__in=[
                        HandoffGrantRevokedReason.REISSUED,
                        HandoffGrantRevokedReason.CANCELLED,
                    ]
                )
                | (
                    Q(failed_attempts=HANDOFF_GRANT_MAX_FAILED_ATTEMPTS)
                    & Q(revoked_at__lt=F("expires_at"))
                ),
                name="concierge_handoff_locked_out_requires_cap_within_ttl",
            ),
            models.CheckConstraint(
                condition=Q(selector__regex=r"^[0-9A-HJKMNP-TV-Z]{16}$"),
                name="concierge_handoff_selector_format",
            ),
            models.CheckConstraint(
                condition=Q(verifier_hash__regex=r"^[0-9a-f]{64}$")
                & Q(anon_binding__regex=r"^[0-9a-f]{64}$"),
                name="concierge_handoff_digest_format",
            ),
        ]
        indexes = [
            models.Index(fields=["expires_at"], name="concierge_handoff_expires_idx"),
        ]

    def __str__(self) -> str:
        return f"HandoffGrant #{self.pk}"
```

- No `ordering`（none needed; avoids implicit sorts on lock queries）.
- `db_table` is the default `temples_conciergehandoffgrant`. All names are ≤ 63 characters（the longest,
  `concierge_handoff_lockout_requires_locked_out_reason` and
  `concierge_handoff_locked_out_requires_cap_within_ttl`, are 52）.
- `HandoffGrantRevokedReason` is at module level, not nested in the model: a class nested in the model body
  is not in scope inside `class Meta`（verified: `NameError` in the scratch run）.

### 3.1 Field and constraint diff, rev 2 → rev 3（for the final G1 review）

```diff
+class HandoffGrantRevokedReason(models.TextChoices):
+    REISSUED = "reissued", "reissued"
+    CANCELLED = "cancelled", "cancelled"
+    LOCKED_OUT = "locked_out", "locked out"

     revoked_at = models.DateTimeField(null=True, blank=True)
+    revoked_reason = models.CharField(
+        max_length=16, choices=HandoffGrantRevokedReason.choices, null=True, blank=True,
+    )
     failed_attempts = models.PositiveSmallIntegerField(default=0)

+    CheckConstraint  concierge_handoff_revoked_reason_pairing
+    CheckConstraint  concierge_handoff_revoked_reason_values
-    CheckConstraint  concierge_handoff_lockout_requires_revoked
+    CheckConstraint  concierge_handoff_lockout_requires_locked_out_reason
+    CheckConstraint  concierge_handoff_locked_out_requires_cap_within_ttl
```

Generated PostgreSQL（`sqlmigrate`, scratch run）:

```sql
CONSTRAINT "concierge_handoff_revoked_reason_pairing" CHECK ((("revoked_at" IS NULL AND "revoked_reason" IS NULL)
  OR ("revoked_at" IS NOT NULL AND "revoked_reason" IS NOT NULL)))
CONSTRAINT "concierge_handoff_revoked_reason_values" CHECK (("revoked_reason" IS NULL
  OR "revoked_reason" IN ('reissued', 'cancelled', 'locked_out')))
CONSTRAINT "concierge_handoff_lockout_requires_locked_out_reason" CHECK (("failed_attempts" < 5
  OR ("revoked_reason" IS NOT NULL AND "revoked_reason" = 'locked_out')))
CONSTRAINT "concierge_handoff_locked_out_requires_cap_within_ttl" CHECK (("revoked_reason" IS NULL
  OR "revoked_reason" IN ('reissued', 'cancelled') OR ("failed_attempts" = 5 AND "revoked_at" < ("expires_at"))))
```

| change | constraint | why |
| --- | --- | --- |
| added | `revoked_reason_pairing` | `revoked_at` and `revoked_reason` are both NULL or both set. Every revoked row says why; no reason without a revocation |
| added | `revoked_reason_values` | only the three values. Django `choices` are not enforced by the database. Logically implied by the two lockout checks below, but kept so a bad value fails with a direct name |
| replaced | `lockout_requires_revoked` → `lockout_requires_locked_out_reason` | 5 failures ⇒ reason is `locked_out`（and so, by pairing, `revoked_at` is set）. Stricter than rev 2: a 5-failure row revoked as `reissued` or `cancelled` is rejected. The explicit `IS NOT NULL` guard is required: without it, a NULL reason makes the expression NULL, and a CHECK accepts NULL |
| added | `locked_out_requires_cap_within_ttl` | `locked_out` ⇒ `failed_attempts = 5` and `revoked_at < expires_at`. Lockout can happen only while the grant is live, because expired grants do not count failures（§9） |
| unchanged | the other 8 checks, the partial unique constraint and the index | the partial unique index still keys on `revoked_at IS NULL`; with pairing, that is the same as `revoked_reason IS NULL` |

Constraint count: 1 partial unique + 12 checks（rev 2: 1 + 9）, plus the `selector` unique, 1 named index and the
automatic FK and `_like` indexes.

---

## 4. Field-by-field

| field | declaration | why |
| --- | --- | --- |
| `id` | `BigAutoField(primary_key=True)` | matches `DEFAULT_AUTO_FIELD`; explicit so the lock-order contract can refer to it |
| `thread` | FK → `ConciergeThread`, `CASCADE`, `related_name="handoff_grants"` | The FK points grant → thread, so deleting or revoking a grant never deletes a consultation. When a thread is deleted（guest retention C7, account deletion C8）its grants go with it. `PROTECT` would block both existing deletion paths |
| `selector` | `CharField(16)`, `unique=True`, Crockford Base32 uppercase（check） | public lookup key: 10 random bytes（80 bits）. Unique index for O(log n) lookup; not secret |
| `verifier_hash` | `CharField(64)`, lowercase hex（check） | `sha256(verifier).hexdigest()` of a 32-byte `secrets.token_bytes` verifier. With 256-bit entropy a fast hash is sufficient; compared with `hmac.compare_digest` |
| `anon_binding` | `CharField(64)`, lowercase hex（check） | `salted_hmac("temples.concierge.handoff.anon_binding", A, algorithm="sha256").hexdigest()`. Binds the grant to anonymous id A without storing A |
| `created_at` | `DateTimeField(db_default=Now(), editable=False)` | Set by the **database clock**（`STATEMENT_TIMESTAMP()`）, so application hosts with skewed clocks cannot shift the window |
| `expires_at` | `DateTimeField(db_default=Now() + TTL, editable=False)` | Same statement timestamp, so `expires_at - created_at = 30 min` exactly（verified）. Enforced by `concierge_handoff_ttl_bounds` |
| `consumed_at` | nullable `DateTimeField` | set once, with `Now()`, in the claim transaction |
| `consumed_by` | FK → user, `SET_NULL`, nullable, `related_name="+"` | Who claimed. `SET_NULL` keeps account deletion unblocked. In practice the row disappears first through `thread → CASCADE`, because the consumer owns the thread（verified）. The invariant and the alternatives are in §5.5（M6） |
| `revoked_at` | nullable `DateTimeField` | Set, with `Now()`, by reissue, explicit cancel or lockout, always together with `revoked_reason`. **Never set by expiry**（§5.6） |
| `revoked_reason` | nullable `CharField(16)`, `choices=HandoffGrantRevokedReason`（rev 3, M3） | Why the grant was revoked: `reissued`, `cancelled` or `locked_out`. NULL exactly when `revoked_at` is NULL（`revoked_reason_pairing`）. NULL rather than `""` so the pairing reads as `IS NULL` on both columns; the repo's optional `CharField`s mostly use `blank=True, default=""`, so this is a review item（Q1, §13.2）. Not PII |
| `failed_attempts` | `PositiveSmallIntegerField(default=0)` | Verification failures on this grant while it is live. Capped and tied to `locked_out` by three checks（§9） |

**Index on `expires_at`:** used by the grant retention purge（§10）. `thread_id` and `consumed_by_id` get
Django's automatic FK indexes. The FK index on `thread_id` serves cascade deletes; the partial unique index
does not cover closed rows. A unique `CharField` also makes Django add a `varchar_pattern_ops` `_like`
index on `selector`. It is unused but harmless; removing it would need custom SQL, so it is not proposed.

---

## 5. Constraints and validation

### 5.1 Compatibility with the `ConciergeThread` ownership constraint（item 1）

- The grant table adds no column to `ConciergeThread` and no constraint on it.
- The only thread write in the handoff is
  `UPDATE … SET user_id = U, anonymous_id = NULL WHERE id = T AND user_id IS NULL AND anonymous_id = A`.
- After it: `user IS NOT NULL` → `concierge_thread_user_or_anonymous_required` holds.
- **Verified:** `test_transfer_satisfies_thread_constraint` passes, and clearing `user` afterwards raises
  `IntegrityError`.

### 5.2 At most one open grant per thread（item 2）

`concierge_handoff_one_open_grant_per_thread` compiles to:

```sql
CREATE UNIQUE INDEX concierge_handoff_one_open_grant_per_thread
  ON temples_conciergehandoffgrant (thread_id)
  WHERE (consumed_at IS NULL AND revoked_at IS NULL);
```

- "Open" means **unconsumed and unrevoked**. An expired but unrevoked row still counts as open. Reissue
  therefore revokes it, with `revoked_reason = 'reissued'`, in the same transaction before inserting（§7）.
- **Verified:** inserting a second open grant raises `IntegrityError`; revoke-then-insert in one
  transaction succeeds.

### 5.3 Why expiry cannot be in a static partial unique constraint（item 3）

- **Fact（verified）:** PostgreSQL rejects `… WHERE expires_at > now()` with "functions in index predicate
  must be marked IMMUTABLE". `now()` and `STATEMENT_TIMESTAMP()` are `STABLE`, not `IMMUTABLE`.
- Even if allowed, a partial index predicate is evaluated **when a row is written**, not when it is
  queried. A row would never leave the index as time passes, so "unexpired" cannot be maintained by an
  index.
- **Therefore:** expiry is checked at claim time（`expires_at > Now()` in a statement after the locks are
  held）. The database also enforces it independently: `concierge_handoff_consumed_within_ttl` rejects any
  `consumed_at ≥ expires_at`. A claim after expiry fails even if application code forgot the check.

### 5.4 State combinations（item 4）

| state | `consumed_at` | `consumed_by` | `revoked_at` | `revoked_reason` | `failed_attempts` | allowed |
| --- | --- | --- | --- | --- | --- | --- |
| open, live（`expires_at > now`） | NULL | NULL | NULL | NULL | 0–4 | ✓ |
| open, expired by time（unusable, §5.6） | NULL | NULL | NULL | NULL | 0–4 | ✓ |
| consumed | set（< `expires_at`） | set, or NULL after consumer deletion | NULL | NULL | 0–4 | ✓ |
| revoked by reissue | NULL | NULL | set（may be > `expires_at`） | `reissued` | 0–4 | ✓ |
| revoked by cancel | NULL | NULL | set（may be > `expires_at`） | `cancelled` | 0–4 | ✓ |
| locked out | NULL | NULL | set（< `expires_at`） | `locked_out` | 5 | ✓ |
| consumed **and** revoked | set | — | set | set | — | ✗ `not_consumed_and_revoked` |
| consumer without consumption | NULL | set | — | — | — | ✗ `consumer_requires_consumed_at` |
| revoked without a reason | — | — | set | NULL | — | ✗ `revoked_reason_pairing` |
| reason without a revocation | — | — | NULL | set | — | ✗ `revoked_reason_pairing` |
| unknown reason（e.g. `expired`, `""`） | — | — | set | other | — | ✗ `revoked_reason_values`（or a lockout check, whichever PostgreSQL evaluates first） |
| 5 failures, still open | NULL | NULL | NULL | NULL | 5 | ✗ `lockout_requires_locked_out_reason` |
| 5 failures, reason `reissued` / `cancelled` | NULL | NULL | set | `reissued` / `cancelled` | 5 | ✗ `lockout_requires_locked_out_reason` |
| `locked_out` with fewer than 5 failures | NULL | NULL | set | `locked_out` | 0–4 | ✗ `locked_out_requires_cap_within_ttl` |
| `locked_out` at or after expiry | NULL | NULL | ≥ `expires_at` | `locked_out` | 5 | ✗ `locked_out_requires_cap_within_ttl` |
| > 5 failures | — | — | — | — | ≥ 6 | ✗ `failed_attempts_cap` |
| TTL ≠ (0, 30 min] | — | — | — | — | — | ✗ `ttl_bounds` |
| consumed at or after expiry, or before creation | — | — | — | — | — | ✗ `consumed_within_ttl` |
| revoked before creation | — | — | — | — | — | ✗ `revoked_after_created` |
| malformed selector or digest | — | — | — | — | — | ✗ format checks |

The rev 2 rows were exercised against PostgreSQL in rev 2（`test_invalid_states`, `test_valid_states`）. The
rows involving `revoked_reason` were exercised in rev 3（`test_invalid_reason_states`,
`test_valid_reason_states`, `test_locked_out_at_or_after_expiry_rejected`,
`test_reissue_or_cancel_after_expiry_allowed`; §11.0）.

### 5.5 `consumed_at` / `consumed_by` invariant and account deletion（rev 2）

**Invariant in §3（variant V1）:** `consumed_by IS NOT NULL ⇒ consumed_at IS NOT NULL`, enforced by
`concierge_handoff_consumer_requires_consumed_at`. The reverse is **not** enforced. A row with `consumed_at`
set and `consumed_by` NULL means "consumed by an account that no longer exists".

**When that state can occur（verified by source and test）:**

- A claim makes the consumer the owner of the grant's thread（§6 steps 6–7）. No code path moves a thread
  from one user to another. So every consumed grant belongs to a thread that its consumer owns.
- Deleting that account deletes the thread（`ConciergeThread.user` CASCADE）, and the thread deletes its
  grants（`thread` CASCADE）.
- **Fact（Django 5.2.16 `Collector.delete`）:** the order is *fast deletes → field updates（SET_NULL）→
  instance deletes*. The grant has no dependents and no delete signals, so it is fast-deleted through the
  thread **before** the `SET_NULL` update runs. That update then matches no rows.
- **Verified:** `test_account_deletion_with_consumed_grant` deletes the consumer without error, and the
  thread and grant are gone.
- **Therefore:** under current code paths, `consumed_at` set with `consumed_by` NULL is not reached. The
  constraint permits it only so that account deletion can never be blocked.

**Variants for Mother Ship（M6; not approved）:**

| variant | constraint | `consumed_by` on_delete | account deletion | verified |
| --- | --- | --- | --- | --- |
| **V1**（in §3） | one-directional | `SET_NULL` | never blocked, whatever the collector order | ✓ passes |
| V2 | strict: `(consumed_at IS NULL) = (consumed_by IS NULL)` | `CASCADE` | consumed grants are deleted with the account | ✓ passes; rejects consumed without consumer |
| V3 | strict | `SET_NULL` | passes **today** only because of fast-delete ordering. If a delete signal or a dependent is ever added to the grant, the `SET_NULL` update would run first and violate the CHECK, **blocking account deletion** | ✓ passes today; **fragile — not proposed** |

The three variants were run with the same 25 tests on PostgreSQL（§11.1）. `revoked_reason` does not change
this analysis: a consumed row always has `revoked_reason` NULL, and `SET_NULL` on `consumed_by` does not touch
it.

### 5.6 Revocation reasons and expiry（rev 3, M3）

**Allowed values**（`HandoffGrantRevokedReason`）:

| value | written by | condition |
| --- | --- | --- |
| `reissued` | issuance on a thread that still has an open grant（§7） | the open grant, live **or expired**, is closed so the new one can be inserted |
| `cancelled` | explicit guest cancellation（§7） | the guest closes their own open grant, live or expired |
| `locked_out` | the failure recorder, on the 5th counted failure（§9） | only while the grant is live; `failed_attempts` becomes 5 in the same statement |

**Expiry is not a revocation.** An expired grant is **not** marked revoked. It only becomes unusable by time:

- Nothing writes to a grant when it expires. There is no scheduler, and none is proposed.
- "Expired" is derived: `expires_at <= Now()`, evaluated in the statement that needs it（claim §6 step 5,
  failure recorder §9, retention §10.1）.
- An expired, never-closed row stays `revoked_at = NULL, revoked_reason = NULL`. There is deliberately **no**
  `expired` value; the values check rejects it.
- It still counts as "open" for the partial unique index（§5.2）. A later issuance on that thread revokes it with
  `reissued`, so `revoked_at > expires_at` is legitimate for `reissued` and `cancelled`.
- `locked_out` can never follow expiry, because expired grants do not count failures（§9）. The database
  enforces this with `revoked_at < expires_at`（`locked_out_requires_cap_within_ttl`）.

Why not mark expiry: it would need a periodic job, add writes for every unused code and make a row's state
depend on whether that job ran. Time-based unusability is already enforced by the database
（`consumed_within_ttl`）. Reporting "how many codes expired unused" needs no extra column:
`consumed_at IS NULL AND revoked_at IS NULL AND expires_at <= now`.

**Write rules（all transitions are one-way）:**

- `revoked_at` and `revoked_reason` are always written together, by one `UPDATE`, with
  `WHERE consumed_at IS NULL AND revoked_at IS NULL`. A closed row matches 0 rows, so a reason is never
  overwritten（e.g. a lockout stays `locked_out` after a later reissue）.
- No code path clears `revoked_at` or `revoked_reason`.
- **Limitation:** the database does not stop a hand-written `UPDATE` from changing one valid reason to another
  （e.g. `reissued` → `cancelled`）on an already revoked row. That would need a trigger, which is not proposed
  （Q3, §13.2）.

### 5.7 State-transition table（rev 3）

States: **OPEN-LIVE**, **OPEN-EXPIRED**（derived from time, no write）, **CONSUMED**, **REVOKED/reissued**,
**REVOKED/cancelled**, **REVOKED/locked_out**. CONSUMED and every REVOKED state are terminal.

| # | from | event | guard（checked after the thread lock） | write | to |
| --- | --- | --- | --- | --- | --- |
| T1 | — | issuance | thread `user IS NULL AND anonymous_id = A`; no open grant | `INSERT`（DB sets `created_at`, `expires_at`） | OPEN-LIVE |
| T2 | OPEN-LIVE / OPEN-EXPIRED | issuance（reissue） | same as T1 | `UPDATE … SET revoked_at = Now(), revoked_reason = 'reissued'`, then `INSERT` | REVOKED/reissued（+ a new OPEN-LIVE） |
| T3 | OPEN-LIVE / OPEN-EXPIRED | explicit cancel | thread `user IS NULL AND anonymous_id = A`; grant belongs to the thread | `UPDATE … SET revoked_at = Now(), revoked_reason = 'cancelled'` | REVOKED/cancelled |
| T4 | OPEN-LIVE（0–3 failures） | counted failure | live; open | `failed_attempts + 1` | OPEN-LIVE |
| T5 | OPEN-LIVE（4 failures） | counted failure | live; open | `failed_attempts = 5, revoked_at = Now(), revoked_reason = 'locked_out'`（one statement） | REVOKED/locked_out |
| T6 | OPEN-LIVE | claim | verifier and binding match; live; thread anonymous with A | `consumed_at = Now(), consumed_by = U`; thread → U | CONSUMED |
| T7 | OPEN-LIVE | time passes `expires_at` | — | **none** | OPEN-EXPIRED |
| T8 | OPEN-EXPIRED | claim, or a failure | — | **none**; claim → 404; failure not counted | OPEN-EXPIRED |
| T9 | CONSUMED / any REVOKED | claim, cancel, reissue, failure | — | **none**（0 rows match）; claim → 404, or idempotent 200 for the same consumer（§6） | unchanged |
| T10 | any | thread deleted（retention, account deletion） | — | grant row deleted（`thread` CASCADE） | — |
| T11 | CONSUMED | consumer account deleted | — | in practice T10 first（§5.5）; otherwise `consumed_by = NULL` | CONSUMED |
| T12 | any closed or expired | grant retention（M5） | `expires_at < now − 30 days` | row deleted | — |

T9 for reissue on a CONSUMED grant cannot be reached anyway: the thread is owned, so issuance stops at the
guard.

---

## 6. Transaction contract（item 5）

Claim, in one `transaction.atomic()`:

1. `SELECT thread_id FROM grant WHERE selector = :s`（no lock; only to find the thread）. If there is no
   row → 404.
2. `SELECT … FROM conciergethread WHERE id = :T FOR UPDATE`（thread lock）.
3. `SELECT … FROM grant WHERE id = :g FOR UPDATE`（grant lock）.
4. Verify in constant time:
   - `compare_digest(sha256(verifier), verifier_hash)`;
   - `compare_digest(hmac(A_current), anon_binding)`.

   Any mismatch → leave this transaction（no write）, then record a failure（§9）→ 404.
5. Check `consumed_at IS NULL AND revoked_at IS NULL AND expires_at > Now()` and `thread.user_id IS NULL`.
   This is a new statement after the locks, so `STATEMENT_TIMESTAMP()` is fresh.
   - If the thread is already owned by the requesting user and `consumed_by = U` → idempotent 200. This
     is decided **only after** step 4 succeeded.
   - Any other failed check → 404.
6. `UPDATE grant SET consumed_at = Now(), consumed_by = U WHERE id = :g AND consumed_at IS NULL AND
   revoked_at IS NULL`, expecting 1 row.
7. `UPDATE conciergethread SET user_id = U, anonymous_id = NULL WHERE id = :T AND user_id IS NULL AND
   anonymous_id = :A`, expecting 1 row.
8. If either count is ≠ 1 → `set_rollback(True)` → 404. Otherwise commit → 200.

Both writes commit together or not at all. Step 7 also closes C6 for the claimed row: `anonymous_id` is now
NULL. The `user__isnull=True` filter in `append_chat` is still proposed（M9）.

---

## 7. Lock order（item 6）

**Global rule: `ConciergeThread` row first, then `ConciergeHandoffGrant` rows**（ascending `id` if several）.

| operation | locks, in order | statements |
| --- | --- | --- |
| issuance / reissue | thread `FOR UPDATE`（re-check `user IS NULL AND anonymous_id = A`）→ open grants via `UPDATE … SET revoked_at = Now(), revoked_reason = 'reissued'` | revoke the open grants（live or expired）, then `INSERT` the new grant. Issuance and reissue are one operation; "reissue" is the case where the `UPDATE` matched a row |
| explicit revocation（guest cancel） | thread `FOR UPDATE`（same re-check）→ grant | `UPDATE … SET revoked_at = Now(), revoked_reason = 'cancelled' WHERE id = :g AND thread_id = :T AND consumed_at IS NULL AND revoked_at IS NULL` |
| consumption | thread → grant | §6 |
| failure recording | grant only, one statement, its own transaction | §9（may write `revoked_reason = 'locked_out'`）. It holds no other lock, so it cannot form a cycle |
| `append_chat`（existing, C5） | thread only | unchanged |
| guest retention purge（**proposed change**, §10.1） | threads `FOR UPDATE SKIP LOCKED` → grants | re-check after the lock, then delete grants, then threads |
| guest retention purge（**current code**, C7） | none first. The collector deletes grants, then the thread | **reverse order**. Deadlock reproduced（§11.1, `test_legacy_reverse_order_can_deadlock`） |
| account deletion（existing, C8） | user → threads → grants（collector） | does not contend with claims: a user-owned thread has no open grant（§5.5） |

### 7.1 Deadlock and lock-failure handling（rev 2; proposal, not approved）

- **With the proposed purge**, every operation that touches both tables locks the thread first. The only
  grant-only statement is the failure recorder: a single row, holding no other lock. So no lock cycle is
  possible among the operations in this table.
  - **Verified:** 5 repeated claim-vs-purge races, with no deadlock.
  - The current purge order does deadlock（PostgreSQL `40P01`）.
- **The claim still treats `OperationalError`（deadlock `40P01`, lock timeout `55P03`）as fail closed:**
  - the transaction rolls back, so nothing is consumed or transferred;
  - the grant stays open, so the user can retry within the TTL;
  - the server does not retry automatically.

  The HTTP response for this case（a uniform 404, or a retryable 503）is **M11**（not approved）.
- **Purge:** on `OperationalError` the batch rolls back. Nothing is deleted, the error count is reported
  （no PII）, and the command is re-run later.
- **Account deletion racing a claim by the same user:** the claim's thread UPDATE adds a FK reference to a
  user row being deleted. The FK is `DEFERRABLE INITIALLY DEFERRED`, so whichever transaction commits second
  fails: either the claim at commit with an FK violation, or the deletion. Nothing partial persists
  （inference; listed for the implementation tests）.

---

## 8. Concurrency（item 7）

**Not every scenario below is verified**（rev 3.1, D2）. The "evidence" column uses three labels:

- **Scratch-verified:** run with concurrent connections on PostgreSQL 16 in the throwaway scratch project
  （mirror `ConciergeThread`, scratch services; §11.0, §11.1）. The model version is named.
- **Reasoned:** derived from the lock order and PostgreSQL semantics; no concurrent test was run.
- **Integration: not tested** applies to **every** row. Nothing here has run against the real `temples`
  models, services or endpoints（§11.3）.

| race | outcome | evidence |
| --- | --- | --- |
| concurrent issuance（two tabs） | serialized on the thread lock. The second revokes the first's grant（`reissued`）and inserts. Exactly one open grant remains, with 2 rows in total | scratch-verified on the **rev 1** model（`test_concurrent_issuance`）. The `reissued` value in this race is **reasoned**; rev 3 tested reissue only sequentially（`test_reissue_sets_reissued`） |
| 5th failure vs reissue（rev 3） | both `UPDATE`s filter on `revoked_at IS NULL`; under READ COMMITTED the second re-evaluates the filter on the new row version and matches 0 rows. Exactly one writer closes the grant, and the reason matches that writer: `locked_out` with 5 failures, or `reissued` with 4 | scratch-verified on the **rev 3** model, 5 races（`test_fifth_failure_vs_reissue`） |
| cancel vs reissue（rev 3） | serialized on the thread lock. Exactly one closes the grant; the reason is `cancelled` or `reissued` | scratch-verified on the **rev 3** model, 5 races（`test_cancel_vs_reissue`） |
| concurrent failures（rev 3） | 12 concurrent failures update exactly 5 times; the grant ends `locked_out` | scratch-verified on the **rev 3** model（`test_concurrent_failures_lock_out_once`） |
| reissue vs claim | serialized on the thread lock. Claim first → the thread is owned → reissue finds `user IS NULL` false → no grant. Reissue first → the old grant is revoked → claim 404, the thread stays anonymous. At most one open grant either way | scratch-verified on the **rev 1** model（`test_reissue_vs_claim_concurrent`）; `revoked_reason` not asserted |
| double claim（same or different users） | the second waits on the thread lock, then sees the grant consumed and the thread owned → 404, or idempotent 200 for the same user. Exactly one `consumed_at` | scratch-verified on the **rev 1** model（`test_double_claim_concurrent`） |
| claim vs purge | §7.1, §10.1 | scratch-verified on the **rev 2** model（§11.1 rev 2 table）; the real purge service is not changed or tested |
| claim vs guest `append_chat` | both take the thread lock first. Claim first → the append's `(id, anonymous_id = A)` re-check finds no row → the existing path creates a new anonymous thread. Append first → the claim transfers the thread including the new message | **reasoned** from C5 only; never run, not even in scratch |
| claim near expiry while waiting on a lock | the expiry check runs in a statement after the lock（fresh timestamp）. `consumed_within_ttl` rejects any consumption at or after `expires_at` | **reasoned** for the race. Only the constraint itself is scratch-verified, sequentially（rev 1 `test_invalid_states`, `test_expired_grant_rejected`） |
| account deletion vs claim by the same user | §7.1 last bullet | **reasoned**; never run |

---

## 9. Failed attempts（item 8）

**What counts as a failure:**

- **Counted:** a selector matches but the verifier hash does not match, or the anonymous binding does not
  match.
- **Not counted:**
  - an unknown selector, because there is no row to count. That case relies on throttling and on 80-bit
    selector entropy.
  - an already consumed, revoked or expired grant. The response is a 404 without counting.

**How it is recorded:** one statement, in its own transaction, after the claim transaction ended without
writing.

```python
lockout = When(failed_attempts__gte=MAX - 1, then=Now())
ConciergeHandoffGrant.objects.filter(
    pk=grant_id,
    consumed_at__isnull=True,
    revoked_at__isnull=True,
    expires_at__gt=Now(),  # rev 3: an expired grant is not counted
).update(
    failed_attempts=F("failed_attempts") + 1,
    revoked_at=Case(lockout, default=Value(None)),
    revoked_reason=Case(
        When(failed_attempts__gte=MAX - 1, then=Value(HandoffGrantRevokedReason.LOCKED_OUT)),
        default=Value(None),
    ),
)
```

- The 5th failure sets `revoked_at` and `revoked_reason = 'locked_out'` in the same statement. Later failures
  match 0 rows.
- **rev 3 correction:** the rev 2 recorder filtered only on `consumed_at` / `revoked_at`. The claim verifies the
  secret（§6 step 4）before it checks expiry（step 5）, so a wrong code on an expired grant would have been
  counted, contradicting "expired → not counted" above. The filter now includes `expires_at > Now()`. Because
  `Now()` is one statement timestamp, a lockout always has `revoked_at < expires_at`, which
  `locked_out_requires_cap_within_ttl` enforces.
- **Verified（rev 2 model）:** 7 sequential failures leave `[1,1,1,1,1,0,0]` rows updated, with
  `failed_attempts = 5` and the grant revoked. 12 concurrent failures never exceed 5.
- **Verified（rev 3 model, §11.0）:** the same sequence ends with `revoked_reason = 'locked_out'` and
  `revoked_at < expires_at`. 12 concurrent failures update exactly 5 times. A failure on an expired grant
  updates 0 rows and leaves it unrevoked. A failure on a `reissued` grant updates 0 rows and keeps the reason.
- The cap and its link to the reason are also enforced by the database（`failed_attempts_cap`,
  `lockout_requires_locked_out_reason`, `locked_out_requires_cap_within_ttl`）.
- A binding mismatch counts, as proposed in M2（conditionally approved under G1, not final）.

---

## 10. Existing consultations, migration and retention（item 9）

- **Existing anonymous consultations:**
  - No backfill and no data migration. Grants are created only by an explicit guest issuance.
  - No thread changes at deployment.
  - A claimed thread leaves the guest retention set（C7）and is later subject to account deletion（C8）.
- **Migration operations proposal**（rev 3; not created, not approved — G2）:

  ```text
  backend/temples/migrations/0122_conciergehandoffgrant.py
    dependencies: ("temples", "0121_shrine_fact_source_citation"), swappable AUTH_USER_MODEL
    operations（as `makemigrations` generated them in the scratch run）:
      CreateModel("ConciergeHandoffGrant",
                  fields = id, selector, verifier_hash, anon_binding, created_at, expires_at,
                           consumed_at, revoked_at, revoked_reason, failed_attempts,
                           consumed_by, thread)
      AddIndex      concierge_handoff_expires_idx
      AddConstraint × 13, in §3 order:
                    one_open_grant_per_thread, not_consumed_and_revoked,
                    consumer_requires_consumed_at, ttl_bounds, consumed_within_ttl,
                    revoked_after_created, revoked_reason_pairing, revoked_reason_values,
                    failed_attempts_cap, lockout_requires_locked_out_reason,
                    locked_out_requires_cap_within_ttl, selector_format, digest_format
    reverse: DeleteModel  →  drops only grant rows; no consultation data is touched
  ```

  - `revoked_reason` is part of the initial `CreateModel`. Because `0122` does not exist yet, there is no
    `AddField` and no backfill. `HandoffGrantRevokedReason` is not referenced by the migration: the migration
    stores the literal `choices` list and the literal SQL values.
  - Adding or renaming a reason value later is a migration: `choices` changes（state only）and
    `revoked_reason_values` / `locked_out_requires_cap_within_ttl` are dropped and re-added.
  - On an empty new table, the `CREATE INDEX` and `ADD CONSTRAINT` statements need no backfill and lock
    only the new table.
  - The only lock on an existing table is the FK creation. The FKs to `temples_conciergethread` and
    `auth_user` are `DEFERRABLE INITIALLY DEFERRED`, and adding them takes a `SHARE ROW EXCLUSIVE` lock on
    the referenced tables for a short time（inference; measure in the implementation PR）.
  - `CASCADE` is ORM-level. The database FK has no `ON DELETE`, so a raw SQL thread delete with live
    grants fails instead of orphaning them（fail closed）.

### 10.1 Guest retention with an unexpired grant（rev 2; proposal, not approved — M7）

- **Problem:** the current `expired_anonymous_threads` selects `user IS NULL` threads whose
  `last_message_at` / `created_at` is older than the cutoff. Issuing a grant touches neither, so a guest who
  issues a code on a 90-day-old thread could have that thread purged mid-handoff.
- **Proposed rule:** a thread with an **open and unexpired** grant
  （`consumed_at IS NULL AND revoked_at IS NULL AND expires_at > now`）is **not** a retention candidate in
  that run.
  - The protection lasts at most the 30-minute TTL. It extends no other retention.
  - A thread whose grants are all expired, consumed or revoked is treated as today. Its grant rows go with
    it（CASCADE）.
- **Proposed purge procedure（one batch, one transaction）:**

  ```python
  open_live = ConciergeHandoffGrant.objects.filter(
      thread=OuterRef("pk"), consumed_at__isnull=True, revoked_at__isnull=True, expires_at__gt=Now()
  )
  ids = list(
      expired_anonymous_threads(cutoff=cutoff)
      .filter(~Exists(open_live))
      .order_by("pk")
      .select_for_update(skip_locked=True)      # 1. thread locks first; skip busy threads
      .values_list("pk", flat=True)
  )
  ids = list(                                     # 2. re-check after the lock（new statement snapshot）
      ConciergeThread.objects.filter(pk__in=ids, user__isnull=True)
      .filter(~Exists(open_live))
      .values_list("pk", flat=True)
  )
  # 3. dependents（logs, messages, grants）, then the threads, in this transaction
  ```

- **Why the re-check is required:** the first statement's `NOT EXISTS` uses that statement's snapshot. A
  claim or issuance that committed before the lock was taken is seen only by a later statement. After the
  lock, no new grant can be issued for these threads, because issuance locks the thread first and waits.
- **Why `SKIP LOCKED`:** a thread being claimed, issued or appended（`append_chat`）right now is left for the
  next run instead of waiting or deadlocking. A purge never deletes a thread that another transaction holds.
- **Alternative（also M7）:** refuse issuance for threads already past the retention cutoff. This is simpler
  in the purge, but it blocks legitimate old consultations from being saved.
- **Counting:** the existing `collect_expired_counts` dry-run would need the same filter, so the dry run and
  the real purge agree. That is an implementation change（G3）.

### 10.2 Grant retention

- **Grant retention（proposal; M5）:**
  - Purge grant rows where `expires_at < now() − 30 days`, whether consumed, revoked or expired. This would
    extend the existing manual `purge_expired_guest_data` command（counts only, no PII）.
  - Grant rows hold no consultation content. `anon_binding` is a keyed hash. A consumed row is the only
    remaining record of where a claimed thread came from（the thread's `anonymous_id` is set to NULL）, so
    the retention period is also an audit-trail decision.
  - **rev 3:** `revoked_reason` changes neither the retention rule nor deletion behaviour. It is purged with
    its row on the same `expires_at` rule, whatever the reason. It is a fixed enum value, not PII. A
    `locked_out` row is the only stored evidence of a guessing attempt on that grant, so M5 also sets how long
    that evidence is kept. Retention by reason（e.g. keeping `locked_out` longer）is **not** proposed.
- **Deletion behaviour（unchanged by rev 3）:** deleting a grant never deletes a thread; deleting a thread
  deletes its grants（`thread` CASCADE）; deleting the consumer sets `consumed_by` NULL or, in practice,
  removes the row with the thread first（§5.5）. Revocation of any reason is an `UPDATE`, never a `DELETE`.
  Verified on the rev 3 model（`test_deletion_unchanged`, `test_consumer_account_deletion`）.

---

## 11. PostgreSQL test matrix（item 10）

### 11.0 rev 3: revocation-reason tests, run in the scratch project（PostgreSQL 16, Django 5.2.16）

- Model: exactly §3（V1）, with a mirror of `ConciergeThread`'s ownership fields and constraint. Scratch
  services implement §6, §7 and §9 as written.
- Result: **22/22 passed**, three consecutive runs, with `DeprecationWarning` treated as an error.
- Not re-run: the 25 rev 2 tests（§11.1）. They target the rev 2 model, and the implementation PR runs them
  again against the real model（§11.2）.

| test | proves |
| --- | --- |
| `test_invalid_reason_states` | 9 invalid combinations → `IntegrityError` naming the expected check: revoked without reason; reason without revocation; `expired`; `""`; 5 failures with `reissued`; 5 failures with `cancelled`; 5 failures still open; `locked_out` with 4 failures; consumed and revoked |
| `test_locked_out_at_or_after_expiry_rejected` | `locked_out` with `revoked_at ≥ expires_at` → `locked_out_requires_cap_within_ttl` |
| `test_valid_reason_states` | open; consumed; `reissued` and `cancelled` with 0–4 failures; `locked_out` with 5 |
| `test_reissue_or_cancel_after_expiry_allowed` | `reissued` / `cancelled` with `revoked_at > expires_at` are accepted（§5.6） |
| `test_issue_open_has_no_reason` | T1: a new grant has `revoked_at` and `revoked_reason` NULL |
| `test_reissue_sets_reissued` | T2: the old grant becomes `reissued`; the new one is open |
| `test_reissue_of_expired_open_grant` | T2 on OPEN-EXPIRED: `reissued`, `revoked_at > expires_at` |
| `test_cancel_sets_cancelled_once` | T3; a second cancel matches 0 rows and keeps the first `revoked_at` |
| `test_cancel_wrong_anon_is_noop` | T3 guard: another anonymous id cannot cancel |
| `test_fifth_failure_locks_out` | T4/T5: `[1,1,1,1,1,0,0]`; `locked_out`; `revoked_at < expires_at` |
| `test_failure_on_expired_grant_not_counted` | T8: 0 rows; `failed_attempts` stays 0; not revoked |
| `test_failure_after_reissue_or_cancel_not_counted` | T9: 0 rows; reason stays `reissued` |
| `test_reissue_after_lockout_keeps_locked_out` | T9: reissue revokes nothing; the old reason stays `locked_out` |
| `test_partial_failures_then_reissue` | 3 failures then reissue → `reissued` with `failed_attempts = 3` |
| `test_expired_grant_is_not_revoked_by_time` | T7/T8: claim after expiry → 404; `revoked_at`, `revoked_reason`, `consumed_at` stay NULL; the thread stays anonymous |
| `test_claim_leaves_reason_null` | T6 then T9: consumed, reason NULL; cancel and failure then match 0 rows |
| `test_claim_of_revoked_grant_404_for_each_reason` | claims on `reissued`, `cancelled` and `locked_out` grants → 404; the thread stays anonymous |
| `test_deletion_unchanged` | T10: deleting a grant keeps the thread; deleting the thread removes its grants |
| `test_consumer_account_deletion` | T11 under V1 |
| `test_concurrent_failures_lock_out_once` | 12 concurrent failures → exactly 5 updates; `locked_out` |
| `test_fifth_failure_vs_reissue` | 5 races: exactly one writer closes the grant; reason and `failed_attempts` match the winner; one open grant remains |
| `test_cancel_vs_reissue` | 5 races: exactly one closes the grant with its own reason |

Scratch-run observation: a value outside the enum violates both `revoked_reason_values` and a lockout check.
PostgreSQL reports the first failing check it evaluates, so tests for that case must accept either name.

### 11.1 Already run in the scratch project（PostgreSQL 16, Django 5.2.16; rev 1 and rev 2 models）

- rev 1: 16/16 passed.
- rev 2: 25/25 passed in each of the three §5.5 variants（V1 / V2 / V3）.

The additional tests in rev 2:

| test | proves |
| --- | --- |
| `test_purge_skips_old_thread_with_unexpired_open_grant` | §10.1 rule: a 200-day-old guest thread with a live grant survives the purge |
| `test_purge_deletes_old_thread_whose_grant_expired_or_closed` | an expired grant gives no protection; the thread and its grants are removed |
| `test_claim_holding_thread_lock_is_skipped_by_purge` | `SKIP LOCKED`: a transaction holding the thread（e.g. `append_chat`）makes the purge skip it |
| `test_claim_racing_purge_with_live_grant_claim_wins` | the claim holds the thread while the purge runs → the purge deletes nothing and the claim transfers |
| `test_issuance_waits_for_purge_then_404` | the purge holds the thread → issuance waits, then finds no thread → no grant; no orphan |
| `test_proposed_order_no_deadlock_repeated` | 5 claim-vs-purge races with the proposed order → no `40P01` |
| `test_legacy_reverse_order_can_deadlock` | the current order（grants first, no thread lock）**does** deadlock against a claim |
| `test_account_deletion_with_consumed_grant` | account deletion after a claim succeeds; the thread and grant are removed（§5.5） |
| `test_consumed_at_without_consumer` | V1 allows it; V2 / V3 reject it |

The rev 1 tests:

| test | proves |
| --- | --- |
| `test_db_defaults_returned_and_ttl_exact` | DB defaults are returned on insert; `expires_at - created_at = 30 min` |
| `test_one_open_grant_per_thread` | partial unique index |
| `test_reissue_revoke_then_insert_same_tx` | the reissue pattern passes the constraint |
| `test_invalid_states` | 10 invalid combinations → `IntegrityError` |
| `test_valid_states` | open → lockout; revoked → new; consumed |
| `test_transfer_satisfies_thread_constraint` | §5.1 |
| `test_claim_happy_and_replay` | claim, idempotent same user, 404 for another user |
| `test_double_claim_concurrent` | exactly one consumption |
| `test_reissue_vs_claim_concurrent` | one winner; ≤ 1 open grant |
| `test_concurrent_issuance` | ≤ 1 open grant; serialized |
| `test_expired_grant_rejected` | the thread stays anonymous |
| `test_delete_semantics` | deleting a grant keeps the thread; deleting the thread removes its grants |
| `test_consumer_deletion_cascades_via_thread` | account deletion removes the claimed thread and its grant |
| `test_now_in_partial_index_predicate_rejected` | §5.3（IMMUTABLE error） |
| `test_failures_cap_and_lock` | sequential cap |
| `test_concurrent_failures_never_exceed_cap` | concurrent cap |

### 11.2 Required in the implementation PR（in `backend/temples/tests/`, on PostgreSQL）

- All of §11.0 and §11.1 against the real `temples` models and migration `0122`. Rev 2 tests that assert
  `lockout_requires_revoked` change to the rev 3 constraint names, and every revocation in them also asserts
  the expected `revoked_reason`.
- Revocation-reason tests through the real services and endpoints（not only the model）: issuance on a thread
  with an open grant writes `reissued`; the cancel endpoint writes `cancelled`; the 5th counted failure from
  the claim endpoint writes `locked_out`; an expired grant answered with a wrong code is neither counted nor
  revoked.
- No code path writes `revoked_at` without `revoked_reason`（grep and a test per writer）.
- `ConciergeThread` ownership constraint test（closes C10）.
- `makemigrations --check` is clean. The migration applies forward and backward on a copy of the test DB.
- Claim racing `append_chat`, both orders（§8, "claim vs guest `append_chat`"）.
- Verifier and binding mismatch → failure counted. Unknown selector → not counted. Expired → not counted.
- **Purge racing an active handoff grant**（precise specification, rev 2）:
  - **Setup:** a `ConciergeThread(user=None, anonymous_id=A)` with `created_at` and `last_message_at` 200
    days ago; one open grant G with `expires_at = now + 30 min`; a user U; the real
    `purge_expired_guest_data` service with cutoff = 90 days.
  - **Case 1 — live grant protects:** run the purge alone. Assert the thread, its messages and G still
    exist, and the purge report count for `ConciergeThread` is 0.
  - **Case 2 — claim holds the lock:** thread A opens a transaction, locks the thread
    （`select_for_update`）and sleeps 0.6 s before finishing the claim. Thread B starts the purge 0.2 s
    later. Assert:
    - B returns without waiting, with 0 deleted;
    - A returns 200;
    - the thread now has `user = U` and `anonymous_id = NULL`;
    - G has `consumed_at` set;
    - no `OperationalError` occurred.
  - **Case 3 — purge holds the lock:** make G expired（`created_at` and `expires_at` minus 1 h）. Thread A
    runs the purge and sleeps 0.6 s after locking. Thread B issues a new grant 0.2 s later. Assert:
    - A deleted the thread and G;
    - B waited and then returned "no thread", with no grant row;
    - nothing was orphaned.
  - **Case 4 — no deadlock:** repeat case 2 with an expired G five times, both sides delaying 0.3 s while
    holding their first lock. Assert no `40P01`.
  - **Control:** the pre-change purge order reproduces `40P01` against a claim. This documents why the
    change is required; it is not run as a permanent CI test.
  - Each case uses separate DB connections（`TransactionTestCase` + threads, closing connections）and
    must run on PostgreSQL.
- Account deletion with a consumed grant, under the chosen §5.5 variant.
- No consultation row is deleted by any handoff operation（row counts before and after）.
- SQLite is **not** sufficient for the concurrency tests（database-level locking）. They must run on
  PostgreSQL in CI.

### 11.3 Outstanding real-project integration verification（rev 3.1, D4）

Every item below is **NOT VERIFIED** in the real project. Scratch results（§11.0, §11.1）show that the schema
design and the documented transitions are consistent with each other. They are **not** evidence that the
real models, migration, services or CI behave this way, and must not be reported as such. Each item is
closed only by a test or check in the repository, in the PR its gate allows（G2 / G3）.

| # | item | scratch evidence（design only） | real-project verification required | gate |
| --- | --- | --- | --- | --- |
| I1 | Real Django models and migration generation: §3 placed in `backend/temples/models.py`; `0122` generated from the real migration state（dependency on `0121`, swappable `AUTH_USER_MODEL`, field order, 13 `AddConstraint`, 1 `AddIndex`）; forward and backward apply | `makemigrations` and `sqlmigrate` on the scratch project | the generated file matches §10; `migrate` forward / backward on a test DB | G2 |
| I2 | `makemigrations --check` clean after `0122` | none | the CI "Check Django schema drift" step passes | G2 |
| I3 | PostgreSQL **and** PostGIS CI: the `postgres` no-GIS unit job and the `postgis` integration job in `backend-tests.yml` | plain `django.db.backends.postgresql` only; the PostGIS backend never ran | §11.0–§11.2 pass in both jobs; the constraint SQL is identical under the PostGIS backend | G2 / G3 |
| I4 | pytest-django integration: tests live in `backend/temples/tests/`, run under the repo's `pytest` configuration; concurrency tests with `transaction=True` / `TransactionTestCase`, threads and connection closing | Django's own test runner, not pytest | the tests pass under `python -m pytest` in CI, repeatably | G3 |
| I5 | Real authentication and handoff services: issuance, reissue, cancel, claim and the failure recorder as real services and endpoints; every writer sets `revoked_at` and `revoked_reason` together | scratch services written for this record | §11.2 revocation-reason tests through the real endpoints; one test per writer | G3 |
| I6 | Claim vs anonymous `append_chat`, both orders | **none**（reasoned only, §8） | concurrent test against the real `append_chat`（C5, C6） | G3 |
| I7 | Guest retention and account deletion: the real `purge_expired_guest_data` with the §10.1 change; the real `account_deletion` path with the real `User` model and all its dependents（§5.5 relies on collector ordering） | rev 2 purge races and rev 1 / rev 3 deletion tests on mirror models | §11.2 purge cases 1–4; account deletion with a consumed grant under the chosen §5.5 variant; consultation row counts unchanged | G3 |
| I8 | Lock order and transaction behaviour: thread → grant in every real code path; claim rollback on `OperationalError`; the M11 response; account deletion racing a claim（§7.1） | rev 2 deadlock reproduction and no-deadlock repeats on scratch code | lock-order tests on the real services; `40P01` / `55P03` handling; the §7.1 FK race | G3 |
| I9 | Failed-attempt expiry guard: the real recorder filters on `expires_at > Now()`. The database enforces this only at lockout（`locked_out_requires_cap_within_ttl`）; failures 1–4 on an expired grant are blocked by application code alone | `test_failure_on_expired_grant_not_counted` on the scratch recorder | endpoint-level test: a wrong code on an expired grant leaves `failed_attempts` and `revoked_*` unchanged | G3 |
| I10 | Security regression tests: no cookie-only transfer path; uniform 404 bodies for unknown, wrong, expired, consumed and revoked codes; no automatic ownership transfer; no consultation deletion by any handoff operation; throttling on unknown selectors; existing concierge history authorization tests still pass | none | security tests in the implementation PR, plus the existing suites green | G3 |

---

## 12. Review findings and security limitations

| id | finding | rev 2 status |
| --- | --- | --- |
| F1 | `ConciergeThread` uses the deprecated `CheckConstraint(check=…)`（C3, C13）; it will break on Django 6.0 | **UNRESOLVED**, out of scope. A separate PR is proposed（M10）; the proposal itself uses `condition=` |
| F2 | No test covers the thread ownership constraint（C10） | **UNRESOLVED**; the test is specified in §11.2 for the implementation PR（G3） |
| F3 | Purge vs claim lock order is reversed in the current purge | **RESOLVED in design**（§7, §7.1, §10.1）. Deadlock reproduced and the fix verified in scratch. Implementation is still unapproved（G3, M7） |
| F4 | An old guest thread can be purged while its grant is unexpired | **RESOLVED in design**（§10.1 rule）. Unapproved（M7） |
| F5 | This would be the first `db_default` use in the repository（C9） | **OPEN** for schema review（M1）; the alternative is `default=timezone.now`（application clock） |
| F6 | The `_like` index on `selector` is unused | **ACCEPTED as harmless**, pending M1 |
| F7（rev 2） | The `consumed_at` / `consumed_by` invariant was one-directional without stated semantics | **RESOLVED in documentation**（§5.5）. Variant choice unapproved（M6） |
| F8（rev 2） | The strict invariant combined with `SET_NULL`（V3）relies on Django's fast-delete ordering and could block account deletion if the model changes | **RESOLVED in documentation**; V3 is not proposed |
| F9（rev 2） | Schema approval and implementation approval were not separated | **RESOLVED**（§1.1 gates G0–G5） |
| F10（rev 2） | Logout rotation and lost-code recovery were left as recommendations | **RESOLVED in documentation** as unresolved policy gates（§13.1）; the policy itself is unresolved |
| F11（rev 3） | The rev 2 failure recorder did not filter on expiry, so a wrong code on an expired grant was counted and could lock it out, contradicting §9 "expired → not counted" | **RESOLVED in design**（§9 filter `expires_at > Now()`, enforced by `locked_out_requires_cap_within_ttl`）. Verified in scratch |
| F12（rev 3） | Once a row is revoked, the database does not stop a manual `UPDATE` from swapping one valid reason for another | **OPEN**（Q3）. All application writers filter on `revoked_at IS NULL`; a trigger is not proposed |

Security limitations:

- **Possession is not identity.** Browser plus code is not proof of the same human（earlier audits, RR7）.
- **`SECRET_KEY` rotation** changes every `anon_binding` → all open grants fail（fail closed）. The project
  sets no `SECRET_KEY_FALLBACKS`.
- **DB dump exposure:** `verifier_hash` is useless without the 256-bit verifier. `anon_binding` needs the key
  to link back to A. `selector` is not secret.
- **Unknown-selector guessing is not counted per grant.** Throttles are per process（`LocMemCache`）, so
  safety rests on the selector + verifier entropy.
- **Timing:** a known selector vs an unknown one may differ in latency. The response body is identical.

---

## 13. Remaining Mother Ship decisions

Approved（G0）: approach A, a 30-minute expiry, single use, reissue revokes earlier open grants, no
consultation deletion, no automatic transfer, and a new table in principle.

Rev 3 status as recorded from the Mother Ship decisions. **Conditional or in-principle approval is not final
approval.** No row below authorizes a migration or runtime code.

| id | decision | gate | proposal | status |
| --- | --- | --- | --- | --- |
| M1 | Exact schema in §3（fields, constraints, names, `db_default` vs `timezone.now`） | G1 | §3 as written | **CONDITIONALLY APPROVED**; final schema diff（§3.1）under review |
| M2 | Failure cap value（fixed in the migration）and whether a binding mismatch counts | G1 | 5; counts | **CONDITIONALLY APPROVED** |
| M3 | Add a `revoked_reason`（reissue / cancel / lockout）field | G1 | **added in rev 3**: §3, §3.1, §5.6, §5.7 | **CONDITIONALLY APPROVED**, with `revoked_reason` required; exact declaration under review（Q1–Q4） |
| M4 | Selector 80 bits / verifier 256 bits / user-facing code format | G1 | as proposed | **CONDITIONALLY APPROVED** |
| M5 | Grant row retention period（also the provenance and lockout audit trail） | G1 / G3 | 30 days after expiry, whatever the reason | **CONDITIONALLY APPROVED** |
| M6 | Consumer invariant variant V1 / V2（§5.5）; V3 not offered | G1 | V1 | **CONDITIONALLY APPROVED** |
| M7 | Retention with open grants: skip with `SKIP LOCKED` + re-check（§10.1）, or refuse issuance past the cutoff | G3 | skip | **APPROVED IN PRINCIPLE**（policy）; implementation not approved |
| M8 | Migration timing: `0122` with the endpoints in one PR, or alone first | G2 / G3 | together | **APPROVED IN PRINCIPLE**（policy）; creating / applying the migration not approved. PR layout consequences below; the layout is not chosen here（Q8） |
| M9 | Shared prerequisites in the same PR or separately: `append_chat` filter（C6）, detail-view fallback removal, X1 | G3 | open | **APPROVED IN PRINCIPLE**; the bundling choice is still open（Q5） |
| M10 | Fix F1（`check=` → `condition=`）as a separate PR | separate | separate | **APPROVED IN PRINCIPLE**; that PR is not created |
| M11（rev 2） | Claim response on deadlock / lock timeout: uniform 404 or retryable 503（§7.1） | G3 | open | **APPROVED IN PRINCIPLE**; 404 vs 503 is still open（Q6） |

**M8 note — PR layout vs approval gates（rev 3.1, D3）.** This note records consequences only. It does not
change M8's recorded status and does not choose between one PR and two.

- **G2 and G3 stay separate approval gates whatever the PR layout.** One PR containing `0122` and the
  endpoints needs **both** approvals before that PR may be created or merged. Approving one gate never implies the
  other（§1.1）.
- **Consequences of one PR（migration + endpoints）:**
  - The migration cannot land before G3 is approved, so G2 cannot be used on its own.
  - If the PR includes the user-facing flow, it also waits on G4（P1, P2）. If P1 then needs a schema change
    （§13.1, D1）, that change goes into the same PR before merge, together with a new G1 review.
  - The table never exists without code that writes to it, and there is no window in which an empty table is
    deployed with no writer.
  - Reverting the PR reverts both. The migration's reverse drops only grant rows（§10）, so a revert loses
    issued grants but no consultation data.
  - The review covers schema, services, endpoints and tests at once, so it is larger.
- **Consequences of two PRs（migration first, then endpoints）:**
  - G2 can be exercised alone. The migration can be reviewed and applied to CI and test databases first.
  - The table exists, empty and unused, until the G3 PR lands.
  - A schema change that P1 later requires becomes a second migration（`0123` or later）instead of an edit
    to an unmerged `0122`.
  - The implementation PR still needs its own G3 approval and depends on the migration PR being merged.
- Whether the in-principle approval of M8 covers the "together" layout specifically, and how G2 and G3 are
  sequenced in practice, is left to Mother Ship（Q8）.

### 13.1 Unresolved product-policy gates（G4; rev 2）

These are product policy, not schema. This record does not choose them.

| id | question | options documented earlier | consequence for this schema |
| --- | --- | --- | --- |
| P1 — logout rotation | At logout, rotate the anonymous id A（L1）or keep it（L2）? | L1: the next guest on the browser cannot read earlier guest threads, but every grant bound to the old A becomes unusable（`anon_binding` mismatch）. L2: the reverse | **Under the current schema, neither option needs a change**: `anon_binding` works with either. L1 makes every open grant for that browser unusable at logout; that is not recorded as a revocation, and the rows stay open, unusable, until they expire（§5.6）. **But the final P1 policy may require an additional revocation reason or another schema change**（rev 3.1, D1）, for example if logout invalidation must be recorded on the grant row or must close grants before expiry. That would reopen G1（§1.1）and change `0122`. No value is proposed here（Q2） |
| P2 — lost-code recovery | What can a user who lost the code do? | (a) as a guest with the same A: reissue（revokes the old grant as `reissued`）. (b) after login: nothing through the handoff, because issuing while authenticated would be a cookie-only transfer path. (c) any account-side recovery requires a new proof factor, which does not exist today | none for (a) or (b). (c) would need a new contract and possibly schema |
| P1 × P2 | With L1, a user who logs in and then loses the code cannot return as the same guest | — | the consultation stays anonymous and is **not** deleted; it becomes unreachable from that browser |

G3 for the user-facing flow stays blocked until P1 and P2 are decided. Whether final G1 may be granted before
P1 is decided is a Mother Ship decision（Q7, §13.2）. Either way, a schema change that P1 later requires needs its
own G1 review（rev 3.1, D1）.

### 13.2 Mother Ship review checklist for final G1（rev 3）

Each item needs an explicit yes / no. Final G1 is granted only when all are answered.

**Schema diff（§3.1）**

- [ ] `revoked_reason` declaration: `CharField(max_length=16, choices=HandoffGrantRevokedReason.choices,
      null=True, blank=True)`
- [ ] **Q1** — NULL（proposed）rather than `""` for "not revoked"
- [ ] **Q2** — exactly three values, spelled `reissued`, `cancelled`, `locked_out`. No `expired` value. No
      value for logout rotation（P1 L1 makes grants unusable through `anon_binding` mismatch without writing
      to them; if P1 later requires a write, adding a value is a new migration）
- [ ] `revoked_reason_pairing`: `revoked_at` and `revoked_reason` are both NULL or both set
- [ ] `revoked_reason_values`: kept although implied by the two lockout checks
- [ ] `lockout_requires_revoked` replaced by `lockout_requires_locked_out_reason`（stricter）
- [ ] `locked_out_requires_cap_within_ttl`: `locked_out` ⇒ 5 failures and `revoked_at < expires_at`
- [ ] **Q3** — no trigger to freeze `revoked_reason` once set（F12）
- [ ] **Q4** — `HandoffGrantRevokedReason` at module level, not nested
- [ ] all other fields, constraints, index names and on-delete behaviour unchanged from rev 2

**Semantics**

- [ ] Expiry is not a revocation: expired grants stay `revoked_at = NULL`, unusable by time only（§5.6）
- [ ] `reissued` / `cancelled` may have `revoked_at > expires_at`（closing an expired open row）
- [ ] Failures on an expired grant are not counted（F11 correction, §9）
- [ ] The state-transition table T1–T12（§5.7）is the contract for the implementation PR
- [ ] 30-minute TTL and single use unchanged（`ttl_bounds`, `consumed_within_ttl`, partial unique index）

**Retention and deletion**

- [ ] M5 applies to every reason alike; no per-reason retention
- [ ] Revocation is always an `UPDATE`; deletion behaviour unchanged（§10.2）

**Migration（proposal only）**

- [ ] `0122` would be a single `CreateModel` with `revoked_reason` inline, 1 `AddIndex` and 13
      `AddConstraint`（§10）. Approving this list does not authorize creating the file（G2）

**Still open after G1**

- [ ] **Q5** — M9 bundling（same PR as the endpoints, or separate）
- [ ] **Q6** — M11 response on deadlock / lock timeout: 404 or 503
- [ ] P1 logout rotation and P2 lost-code recovery（G4）. The final P1 policy may require an additional
      revocation reason or another schema change, which would reopen G1（§1.1, §13.1; rev 3.1, D1）
- [ ] **Q7**（rev 3.1）— whether final G1 may be granted before P1 is decided
- [ ] **Q8**（rev 3.1）— whether M8's in-principle approval covers the one-PR layout, and how G2 and G3 are
      sequenced（M8 note, §13）
- [ ] The §11.3 integration items I1–I10 are open. They are gated by G2 / G3, not by G1, and scratch results
      do not close them

---

## 14. Not done

```text
backend/temples/models.py            UNCHANGED
migrations                           NONE CREATED / NONE APPLIED
endpoints / UI / cookies / auth      UNCHANGED
consultation data                    UNCHANGED（none deleted or reassigned）
ranking / shrine data / billing      UNCHANGED
Production                           NOT CONTACTED
PRODUCTION_SECURITY_E2E              OPEN
```
