# ConciergeHandoffGrant — Exact Django Model Proposal

## 1. Status

```text
APPROACH                        = A（database-backed handoff grant; approved in principle）
EXACT SCHEMA                    = PROPOSED（this record）→ Mother Ship approval required（§13）
models.py / migrations          = UNCHANGED（no migration created or applied）
endpoints / UI / cookies / auth = UNCHANGED
consultation data               = UNCHANGED
PRODUCTION_SECURITY_E2E         = OPEN
REVIEW CORRECTIONS（rev 2）      = APPLIED（§1.1, §5.5, §7, §10.1, §11.1, §12, §13, §13.1）
FINAL STATUS                    = STOP — awaiting Mother Ship review
```

### 1.1 Approval gates（rev 2）

Approval of one gate does **not** imply approval of a later one.

| gate | scope | status |
| --- | --- | --- |
| G0 — requirements | approach A; 30-min expiry; single use; reissue revokes earlier open grants; no consultation deletion; no automatic transfer; a new table in principle | **APPROVED**（task brief） |
| G1 — schema | the exact fields, constraints, index names and on-delete behaviour in §3, including the M1–M7 choices | **NOT APPROVED** |
| G2 — migration | creating `0122_conciergehandoffgrant` in the repository | **NOT APPROVED**; requires G1 |
| G3 — implementation | services, endpoints, BFF routes, UI, the retention-purge change（§10.1）and the shared prerequisites（M9） | **NOT APPROVED**; requires G1 and G2 |
| G4 — product policy | logout rotation（P1）and lost-code recovery（P2）, §13.1 | **UNRESOLVED**; blocks G3 for the UI flow |
| G5 — deployment | applying the migration to Production and enabling the flow | **NOT APPROVED**; requires G1–G4 and the Production QA plan |

An approved schema（G1）only makes §3 the target of a later migration PR. It does not authorize creating that
migration, writing endpoints or changing retention.

- Source of truth: `origin/develop@1465c5d`（includes #3313）. Django **5.2.16**（`backend/requirements.txt`）.
  `DEFAULT_AUTO_FIELD = BigAutoField`（`backend/shrine_project/settings.py:456`）. Latest migration:
  `0121_shrine_fact_source_citation`.
- Builds on `docs/audit/anonymous-handoff-code-db-lifecycle-audit-2026-10-22.md`（approach A, §4.2）. This
  record replaces its sketch with exact declarations.
- **Verification:** the model below was compiled and exercised in a **throwaway scratch Django project**
  outside the repository. It ran against the local PostgreSQL 16 test server, with a mirror of
  `ConciergeThread`'s ownership fields and constraint. 16 tests passed in rev 1; 25 tests passed in each of
  three variants in rev 2（§11.1）. The scratch databases
  were dropped afterwards. Nothing ran against Production, and nothing in the repository changed except
  this file.
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
                condition=Q(failed_attempts__lte=HANDOFF_GRANT_MAX_FAILED_ATTEMPTS),
                name="concierge_handoff_failed_attempts_cap",
            ),
            models.CheckConstraint(
                condition=Q(failed_attempts__lt=HANDOFF_GRANT_MAX_FAILED_ATTEMPTS)
                | Q(revoked_at__isnull=False),
                name="concierge_handoff_lockout_requires_revoked",
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
- `db_table` is the default `temples_conciergehandoffgrant`. All names are ≤ 63 characters.

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
| `revoked_at` | nullable `DateTimeField` | Set by reissue, explicit cancel or lockout. There is no reason column（decision M3） |
| `failed_attempts` | `PositiveSmallIntegerField(default=0)` | Verification failures on this grant. Capped by two checks（§9） |

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
  therefore revokes it in the same transaction before inserting（§7）.
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

| state | `consumed_at` | `consumed_by` | `revoked_at` | `failed_attempts` | allowed |
| --- | --- | --- | --- | --- | --- |
| open（may be expired by time） | NULL | NULL | NULL | 0–4 | ✓ |
| consumed | set（< `expires_at`） | set, or NULL after consumer deletion | NULL | 0–4 | ✓ |
| revoked（reissue / cancel） | NULL | NULL | set | 0–4 | ✓ |
| locked out | NULL | NULL | set | 5 | ✓ |
| consumed **and** revoked | set | — | set | — | ✗ `not_consumed_and_revoked` |
| consumer without consumption | NULL | set | — | — | ✗ `consumer_requires_consumed_at` |
| 5 failures, still open | NULL | NULL | NULL | 5 | ✗ `lockout_requires_revoked` |
| > 5 failures | — | — | — | ≥ 6 | ✗ `failed_attempts_cap` |
| TTL ≠ (0, 30 min] | — | — | — | — | ✗ `ttl_bounds` |
| consumed at or after expiry, or before creation | — | — | — | — | ✗ `consumed_within_ttl` |
| revoked before creation | — | — | — | — | ✗ `revoked_after_created` |
| malformed selector or digest | — | — | — | — | ✗ format checks |

All rows above were exercised against PostgreSQL（`test_invalid_states`, `test_valid_states`）.

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

The three variants were run with the same 25 tests on PostgreSQL（§11.1）.

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
| issuance / reissue | thread `FOR UPDATE`（re-check `user IS NULL AND anonymous_id = A`）→ open grants via `UPDATE … SET revoked_at = Now()` | revoke the open grants, then `INSERT` the new grant |
| explicit revocation（guest cancel） | thread `FOR UPDATE` → grant | `UPDATE … SET revoked_at = Now() WHERE id = :g AND consumed_at IS NULL AND revoked_at IS NULL` |
| consumption | thread → grant | §6 |
| failure recording | grant only, one statement, its own transaction | §9. It holds no other lock, so it cannot form a cycle |
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

All rows below were verified with two concurrent connections on PostgreSQL（§11.1）.

| race | outcome |
| --- | --- |
| concurrent issuance（two tabs） | serialized on the thread lock. The second revokes the first's grant and inserts. Exactly one open grant remains, with 2 rows in total |
| reissue vs claim | serialized on the thread lock. Claim first → the thread is owned → reissue finds `user IS NULL` false → no grant. Reissue first → the old grant is revoked → claim 404, the thread stays anonymous. At most one open grant either way |
| double claim（same or different users） | the second waits on the thread lock, then sees the grant consumed and the thread owned → 404, or idempotent 200 for the same user. Exactly one `consumed_at` |
| claim vs guest `append_chat` | both take the thread lock first. Claim first → the append's `(id, anonymous_id = A)` re-check finds no row → the existing path creates a new anonymous thread. Append first → the claim transfers the thread including the new message（inference from C5; listed for the implementation tests） |
| claim near expiry while waiting on a lock | the expiry check runs in a statement after the lock（fresh timestamp）. `consumed_within_ttl` rejects any consumption at or after `expires_at` |

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
ConciergeHandoffGrant.objects.filter(
    pk=grant_id, consumed_at__isnull=True, revoked_at__isnull=True
).update(
    failed_attempts=F("failed_attempts") + 1,
    revoked_at=Case(When(failed_attempts__gte=MAX - 1, then=Now()), default=Value(None)),
)
```

- The 5th failure sets `revoked_at` in the same statement. Later failures match 0 rows.
- **Verified:** 7 sequential failures leave `[1,1,1,1,1,0,0]` rows updated, with `failed_attempts = 5` and
  the grant revoked. 12 concurrent failures never exceed 5.
- The cap is also enforced by the database（`failed_attempts_cap`, `lockout_requires_revoked`）.
- **Open question for Mother Ship:** whether a binding mismatch should count. It does in this proposal
  （M2）.

---

## 10. Existing consultations, migration and retention（item 9）

- **Existing anonymous consultations:**
  - No backfill and no data migration. Grants are created only by an explicit guest issuance.
  - No thread changes at deployment.
  - A claimed thread leaves the guest retention set（C7）and is later subject to account deletion（C8）.
- **Migration operations proposal**（not created）:

  ```text
  backend/temples/migrations/0122_conciergehandoffgrant.py
    dependencies: ("temples", "0121_shrine_fact_source_citation"), swappable AUTH_USER_MODEL
    operations:
      CreateModel("ConciergeHandoffGrant", fields=[…§3…], options={constraints, indexes})
    reverse: DeleteModel  →  drops only grant rows; no consultation data is touched
  ```

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

---

## 11. PostgreSQL test matrix（item 10）

### 11.1 Already run in the scratch project（PostgreSQL 16, Django 5.2.16）

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

- All of §11.1 against the real `temples` models and migration `0122`.
- `ConciergeThread` ownership constraint test（closes C10）.
- `makemigrations --check` is clean. The migration applies forward and backward on a copy of the test DB.
- Claim racing `append_chat`, both orders（§8 row 4）.
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

Already approved（G0）: approach A, a 30-minute expiry, single use, reissue revokes earlier open grants, no
consultation deletion, no automatic transfer, and a new table in principle. Everything below is
**unapproved**. The "proposal" column is input for review, not a decision.

| id | decision | gate | proposal | status |
| --- | --- | --- | --- | --- |
| M1 | Exact schema in §3（fields, constraints, names, `db_default` vs `timezone.now`） | G1 | §3 as written | **UNAPPROVED** |
| M2 | Failure cap value（fixed in the migration）and whether a binding mismatch counts | G1 | 5; counts | **UNAPPROVED** |
| M3 | Add a `revoked_reason`（reissue / cancel / lockout）field | G1 | not added | **UNAPPROVED** |
| M4 | Selector 80 bits / verifier 256 bits / user-facing code format | G1 | as proposed | **UNAPPROVED** |
| M5 | Grant row retention period（also the provenance audit trail） | G1 / G3 | 30 days after expiry | **UNAPPROVED** |
| M6 | Consumer invariant variant V1 / V2（§5.5）; V3 not offered | G1 | V1 | **UNAPPROVED** |
| M7 | Retention with open grants: skip with `SKIP LOCKED` + re-check（§10.1）, or refuse issuance past the cutoff | G3 | skip | **UNAPPROVED** |
| M8 | Migration timing: `0122` with the endpoints in one PR, or alone first | G2 | together | **UNAPPROVED** |
| M9 | Shared prerequisites in the same PR or separately: `append_chat` filter（C6）, detail-view fallback removal, X1 | G3 | open | **UNAPPROVED** |
| M10 | Fix F1（`check=` → `condition=`）as a separate PR | separate | separate | **UNAPPROVED** |
| M11（rev 2） | Claim response on deadlock / lock timeout: uniform 404 or retryable 503（§7.1） | G3 | open | **UNAPPROVED** |

### 13.1 Unresolved product-policy gates（G4; rev 2）

These are product policy, not schema. This record does not choose them.

| id | question | options documented earlier | consequence for this schema |
| --- | --- | --- | --- |
| P1 — logout rotation | At logout, rotate the anonymous id A（L1）or keep it（L2）? | L1: the next guest on the browser cannot read earlier guest threads, but every grant bound to the old A becomes unusable（`anon_binding` mismatch）. L2: the reverse | none: `anon_binding` works with either. L1 makes every logout an implicit revocation of all open grants for that browser |
| P2 — lost-code recovery | What can a user who lost the code do? | (a) as a guest with the same A: reissue（revokes the old grant）. (b) after login: nothing through the handoff, because issuing while authenticated would be a cookie-only transfer path. (c) any account-side recovery requires a new proof factor, which does not exist today | none for (a) or (b). (c) would need a new contract and possibly schema |
| P1 × P2 | With L1, a user who logs in and then loses the code cannot return as the same guest | — | the consultation stays anonymous and is **not** deleted; it becomes unreachable from that browser |

G3 for the user-facing flow stays blocked until P1 and P2 are decided.

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
