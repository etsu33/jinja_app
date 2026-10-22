# ConciergeHandoffGrant — Exact Django Model Proposal

## 1. Status

```text
APPROACH                        = A（database-backed handoff grant; approved in principle）
EXACT SCHEMA                    = PROPOSED（this record）→ Mother Ship approval required（§13）
models.py / migrations          = UNCHANGED（no migration created or applied）
endpoints / UI / cookies / auth = UNCHANGED
consultation data               = UNCHANGED
PRODUCTION_SECURITY_E2E         = OPEN
```

- Source of truth: `origin/develop@1465c5d`（includes #3313）. Django **5.2.16**（`backend/requirements.txt`）.
  `DEFAULT_AUTO_FIELD = BigAutoField`（`backend/shrine_project/settings.py:456`）. Latest migration:
  `0121_shrine_fact_source_citation`.
- Builds on `docs/audit/anonymous-handoff-code-db-lifecycle-audit-2026-10-22.md`（approach A, §4.2）. This
  record replaces its sketch with exact declarations.
- **Verification:** the model below was compiled and exercised in a **throwaway scratch Django project**
  outside the repository. It ran against the local PostgreSQL 16 test server, with a mirror of
  `ConciergeThread`'s ownership fields and constraint. 16 tests passed（§11.1）. The scratch databases
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
| `consumed_by` | FK → user, `SET_NULL`, nullable, `related_name="+"` | Who claimed. `SET_NULL` keeps account deletion unblocked. In practice the row disappears first through `thread → CASCADE`, because the consumer owns the thread（verified） |
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
| guest retention / account deletion（existing, C7 / C8） | Django's collector deletes **grants before the thread** | **reverse order**（finding F3, §12） |

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
- **Grant retention（proposal; M5）:**
  - Purge grant rows where `expires_at < now() − 30 days`, whether consumed, revoked or expired. This would
    extend the existing manual `purge_expired_guest_data` command（counts only, no PII）.
  - Grant rows hold no consultation content. `anon_binding` is a keyed hash. A consumed row is the only
    remaining record of where a claimed thread came from（the thread's `anonymous_id` is set to NULL）, so
    the retention period is also an audit-trail decision.

---

## 11. PostgreSQL test matrix（item 10）

### 11.1 Already run in the scratch project（PostgreSQL 16, Django 5.2.16; 16/16 passed）

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
- Guest retention purge with an open grant on an old thread（F3/M7 behavior, once decided）.
- No consultation row is deleted by any handoff operation（row counts before and after）.
- SQLite is **not** sufficient for the concurrency tests（database-level locking）. They must run on
  PostgreSQL in CI.

---

## 12. Review findings and security limitations

| id | finding | severity / handling |
| --- | --- | --- |
| F1 | `ConciergeThread` uses the deprecated `CheckConstraint(check=…)`（C3, C13）; it will break on Django 6.0 | outside this scope; separate change. The proposal uses `condition=` |
| F2 | No test covers the thread ownership constraint（C10） | add in the implementation PR |
| F3 | Guest retention and account deletion delete grants before the thread, the **reverse of §7's lock order**. A purge racing a claim on the same thread can deadlock. PostgreSQL aborts one transaction, which fails closed | M7: have the purge lock threads first（`select_for_update`）or skip threads with an open, unexpired grant |
| F4 | Retention keys on `last_message_at` / `created_at`. Issuing a grant does not touch them, so a 90-day-old guest thread can be purged while its grant is open | M7 |
| F5 | This would be the first `db_default` use in the repository（C9） | it keeps a single clock source; the alternative is `default=timezone.now`（application clock） |
| F6 | The `_like` index on `selector` is unused | accept（harmless） |

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

| id | decision | proposal |
| --- | --- | --- |
| M1 | Approve the exact schema in §3（fields, constraints, names, `db_default`） | — |
| M2 | Failure cap value（fixed in the migration）and whether a binding mismatch counts | 5; counts |
| M3 | Add a `revoked_reason`（reissue / cancel / lockout）field | not added; ask before adding |
| M4 | Selector length 80 bits / verifier 256 bits / user-facing code format | as proposed |
| M5 | Grant row retention period（also the provenance audit trail） | 30 days after expiry |
| M6 | `consumed_by` `SET_NULL`（vs `CASCADE`） | `SET_NULL` |
| M7 | Retention purge behavior with open grants（F3, F4） | lock threads first and skip open, unexpired grants |
| M8 | Migration timing: ship `0122` with the endpoints in one PR, or alone first | together, behind the existing STOP rules |
| M9 | Ship the shared prerequisites in the same PR or separately: `append_chat` filter（C6）, detail-view fallback removal, X1 | open |
| M10 | Fix F1（`check=` → `condition=` on `ConciergeThread`）as a separate PR | separate |

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
