-- SELECT-only. Safe to run against Production. Never write, never DDL.
--
-- Preflight for applying `users` migrations 0011 -> 0012 -> 0013 -> 0014 -> 0015
-- IN SEQUENCE. This file is scoped to exactly those five migrations and is
-- SEPARATE from `pre_migration_snapshot.sql` / `post_migration_verification.sql`
-- (historical runbook for `users 0006` / `temples 0090-0093`) and from
-- `temples_0095_0098_preflight.sql`.
--
-- Each section derives its precondition directly from that migration's own
-- `forward` implementation (backend/users/migrations/00xx_*.py) -- nothing here
-- is guessed. Sections 3-R, 4-R and 5-R are "would RAISE" conditions: 0011,
-- 0013 and 0015 contain RunPython code that raises RuntimeError instead of
-- guessing, and a raise rolls back THAT migration only (each migration is its
-- own transaction on PostgreSQL); the migrations before it stay applied.
--
-- `now()` here is the time this file runs. 0013 uses `timezone.now()` at the
-- time `migrate` runs, so re-run Section 4 immediately before `migrate`.
--
-- Output of Sections 3-P and 4-P lists billing rows by internal ids only
-- (profile id, user id, status, dates). It never selects email, username,
-- nickname, birth fields or Stripe customer ids. Keep the output outside the
-- repository: it is the pre-image used for manual recovery.
--
-- How to run (never paste a credential into chat; see README.md "Credential
-- Bridge"):
--   scripts/migration_safety/readonly_query.sh \
--     ~/.config/kami-musubi/production-db.env DATABASE_URL \
--     scripts/migration_safety/sql/users_0011_0015_preflight.sql


-- ============================================================================
-- SECTION 0 -- Migration ledger state
-- ============================================================================

-- 0-a. users 0010 applied; 0011-0015 NOT applied.
SELECT
  EXISTS (SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0010_premium_pass_purchase')
    AS users_0010_applied_expected_true,
  EXISTS (SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0011_separate_premium_entitlements')
    AS users_0011_applied_expected_false,
  EXISTS (SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0012_premium_subscription')
    AS users_0012_applied_expected_false,
  EXISTS (SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0013_backfill_stripe_premium_subscriptions')
    AS users_0013_applied_expected_false,
  EXISTS (SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0014_apple_storekit_receipt')
    AS users_0014_applied_expected_false,
  EXISTS (SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0015_apple_billing_environments')
    AS users_0015_applied_expected_false;
-- Expected: 0010 = true, the other five = false. Otherwise STOP and re-derive.

-- 0-b. STOP check: any `users` migration numbered above 0010 already applied?
SELECT name, applied
FROM django_migrations
WHERE app = 'users'
  AND SUBSTRING(name FROM '^[0-9]{4}')::int > 10
ORDER BY name;
-- Expected: 0 rows.

-- 0-c. Recent `users` ledger tail, for the audit trail.
SELECT name, applied
FROM django_migrations
WHERE app = 'users'
ORDER BY applied DESC
LIMIT 6;


-- ============================================================================
-- SECTION 1 -- Schema pre-state (drift check)
-- The ledger says 0011-0015 are unapplied; confirm the schema agrees, so that
-- AddField / CreateModel / AddConstraint will not collide with something that
-- already exists (cf. the temples lineage drift in
-- docs/audit/production-migration-execution-gate.md Phase 3).
-- ============================================================================

-- 1-a. Columns 0011 / 0015 will ADD must NOT exist yet.
SELECT
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'public' AND table_name = 'users_userprofile'
            AND column_name = 'legacy_premium_until') AS profile_legacy_premium_until_exists_expected_false,
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'public' AND table_name = 'users_userprofile'
            AND column_name = 'account_entitlement_disabled') AS profile_account_entitlement_disabled_exists_expected_false,
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'public' AND table_name = 'users_premiumpasspurchase'
            AND column_name = 'effective_period_end') AS pass_effective_period_end_exists_expected_false,
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'public' AND table_name = 'users_premiumpasspurchase'
            AND column_name = 'environment') AS pass_environment_exists_expected_false;
-- Expected: all four = false.

-- 1-b. Tables 0012 / 0014 will CREATE must NOT exist yet.
SELECT
  to_regclass('public.users_premiumsubscription') IS NOT NULL AS premiumsubscription_table_exists_expected_false,
  to_regclass('public.users_applestorekitreceipt') IS NOT NULL AS applestorekitreceipt_table_exists_expected_false;
-- Expected: both = false.

-- 1-c. Columns the five migrations READ must exist (0005 / 0009 / 0010 shape).
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    (table_name = 'users_userprofile' AND column_name IN (
      'user_id', 'current_period_end', 'stripe_price_id', 'stripe_subscription_id',
      'subscription_status', 'cancel_at_period_end'))
    OR (table_name = 'users_premiumpasspurchase' AND column_name IN (
      'user_id', 'source', 'external_id', 'period_end_before', 'period_end_after',
      'status', 'refunded_at', 'created_at'))
  )
ORDER BY table_name, column_name;
-- Expected: 14 rows. current_period_end / period_end_before / refunded_at
-- nullable = YES; the stripe_* / subscription_status / source / status /
-- external_id / period_end_after / created_at columns nullable = NO.

-- 1-d. Constraint 0015 will REMOVE must exist; the ones 0012/0014/0015 will ADD
-- must not. Conditional UniqueConstraints are created as partial UNIQUE INDEXes
-- (not pg_constraint rows), so look in both places.
SELECT 'constraint' AS kind, conname AS name
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND conname IN (
  'uniq_premium_pass_purchase_source_external_id', 'premium_pass_environment_matches_source',
  'premium_subscription_has_provider_id', 'uniq_apple_storekit_receipt')
UNION ALL
SELECT 'index', indexname
FROM pg_indexes
WHERE schemaname = 'public' AND indexname IN (
  'uniq_premium_pass_non_apple_id', 'uniq_premium_pass_apple_environment_id',
  'uniq_premium_subscription_stripe_id', 'uniq_premium_subscription_apple_id',
  'uniq_premium_subscription_apple_environment_id')
ORDER BY 1, 2;
-- Expected: exactly 1 row, constraint `uniq_premium_pass_purchase_source_external_id`.


-- ============================================================================
-- SECTION 2 -- Baseline counts (record these; the post-check compares to them)
-- ============================================================================

-- 2-a. Row counts.
SELECT
  (SELECT COUNT(*) FROM auth_user) AS auth_user_count,
  (SELECT COUNT(*) FROM users_userprofile) AS userprofile_count,
  (SELECT COUNT(*) FROM users_premiumpasspurchase) AS pass_purchase_count;

-- 2-b. Profile billing state distribution.
SELECT
  subscription_status,
  (stripe_subscription_id <> '') AS has_subscription_id,
  (stripe_price_id <> '') AS has_price_id,
  cancel_at_period_end,
  (current_period_end IS NOT NULL) AS has_period_end,
  (current_period_end > now()) AS period_end_in_future,
  COUNT(*) AS profiles
FROM users_userprofile
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY profiles DESC, 1;

-- 2-c. Pass purchase distribution.
SELECT source, status, (refunded_at IS NOT NULL) AS has_refunded_at, COUNT(*) AS purchases
FROM users_premiumpasspurchase
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;


-- ============================================================================
-- SECTION 3 -- 0011_separate_premium_entitlements (AddField x3 + RunPython)
-- Forward `separate_entitlements` RAISES (whole 0011 rolls back, nothing
-- changes) if any 3-R count below is non-zero. If all are zero it WRITES the
-- rows counted in 3-E.
-- "without_subscription" = stripe_subscription_id = '' AND stripe_price_id = ''.
-- "pass user" = a user_id that appears in users_premiumpasspurchase.
-- ============================================================================

-- 3-R. Raise conditions. Expected: every column = 0.
WITH chain AS (
  SELECT
    p.*,
    ROW_NUMBER() OVER w AS rn,
    LAG(p.period_end_after) OVER w AS previous_end,
    LAST_VALUE(p.period_end_after) OVER (
      PARTITION BY p.user_id ORDER BY p.created_at, p.id
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS last_end,
    COUNT(*) OVER (PARTITION BY p.user_id) AS n
  FROM users_premiumpasspurchase p
  WINDOW w AS (PARTITION BY p.user_id ORDER BY p.created_at, p.id)
)
SELECT
  (SELECT COUNT(*) FROM users_premiumpasspurchase p
     WHERE NOT EXISTS (SELECT 1 FROM users_userprofile u WHERE u.user_id = p.user_id))
    AS r1_pass_without_profile,
  (SELECT COUNT(*) FROM users_userprofile u
     WHERE u.user_id IN (SELECT user_id FROM users_premiumpasspurchase)
       AND (u.stripe_subscription_id <> '' OR u.stripe_price_id <> '' OR u.cancel_at_period_end))
    AS r2_pass_user_with_subscription_evidence,
  (SELECT COUNT(*) FROM chain
     WHERE rn = 1 AND period_end_before IS NOT NULL AND period_end_before > created_at)
    AS r3_first_pass_preceded_by_deadline,
  (SELECT COUNT(*) FROM chain
     WHERE rn > 1 AND period_end_before IS DISTINCT FROM previous_end)
    AS r4_pass_chain_broken,
  (SELECT COUNT(*) FROM chain
     WHERE status <> 'completed' OR refunded_at IS NOT NULL)
    AS r5_pass_not_completed_or_refunded,
  (SELECT COUNT(DISTINCT c.user_id) FROM chain c
     JOIN users_userprofile u ON u.user_id = c.user_id
     WHERE c.rn = c.n AND c.last_end IS DISTINCT FROM u.current_period_end)
    AS r6_pass_end_differs_from_profile_deadline,
  (SELECT COUNT(*) FROM users_userprofile
     WHERE stripe_subscription_id = '' AND stripe_price_id = '' AND cancel_at_period_end)
    AS r7_cancel_scheduled_without_subscription_ids;
-- r2 and r3-r6 are only reached for profiles of pass users; r7 for all.
-- NOTE: Python stops at the first failure; this counts every failing row.

-- 3-E. Rows 0011 WILL WRITE if 3-R is all zero.
SELECT
  (SELECT COUNT(*) FROM users_premiumpasspurchase)
    AS e1_pass_rows_effective_period_end_set,
  (SELECT COUNT(*) FROM users_userprofile
     WHERE stripe_subscription_id = '' AND stripe_price_id = ''
       AND user_id NOT IN (SELECT user_id FROM users_premiumpasspurchase)
       AND current_period_end IS NOT NULL)
    AS e2_profiles_getting_legacy_premium_until_non_null,
  (SELECT COUNT(*) FROM users_userprofile
     WHERE stripe_subscription_id = '' AND stripe_price_id = ''
       AND user_id NOT IN (SELECT user_id FROM users_premiumpasspurchase)
       AND current_period_end > now())
    AS e2a_of_which_still_premium_now,
  (SELECT COUNT(*) FROM users_userprofile
     WHERE stripe_subscription_id = '' AND stripe_price_id = '')
    AS e3_profiles_reset_to_inactive_null_deadline,
  (SELECT COUNT(*) FROM users_userprofile
     WHERE stripe_subscription_id = '' AND stripe_price_id = ''
       AND (current_period_end IS NOT NULL OR subscription_status <> 'inactive'))
    AS e3a_of_which_value_actually_changes;
-- e3 includes pass users: their shared deadline is cleared and moved to
-- users_premiumpasspurchase.effective_period_end (e1).

-- 3-P. Pre-image of every profile 0011 will change (recovery reference).
-- 0011's reverse cannot restore subscription_status exactly (it writes
-- 'active'), so this output -- together with the dump -- is the record.
SELECT
  u.id AS profile_id,
  u.user_id,
  u.subscription_status,
  u.current_period_end,
  u.cancel_at_period_end,
  (u.user_id IN (SELECT user_id FROM users_premiumpasspurchase)) AS is_pass_user
FROM users_userprofile u
WHERE u.stripe_subscription_id = '' AND u.stripe_price_id = ''
  AND (u.current_period_end IS NOT NULL OR u.subscription_status <> 'inactive' OR u.cancel_at_period_end)
ORDER BY u.id;


-- ============================================================================
-- SECTION 4 -- 0013_backfill_stripe_premium_subscriptions (RunPython only)
-- Candidates = profiles NOT (subscription_id = '' AND price_id = '' AND
-- cancel_at_period_end = false). 0011 never touches profiles that have a
-- subscription or price id, so reading the current rows gives the same
-- candidate set 0013 will see. 0012 creates the target table empty, so no
-- "existing row conflicts" branch can be reached on this first apply.
-- ============================================================================

-- 4-R. Raise conditions. Expected: every column = 0.
-- Whitespace set = what Python str.strip() removes for ASCII.
WITH cand AS (
  SELECT
    u.*,
    btrim(u.subscription_status, E' \t\n\r\x0b\x0c') AS old_status,
    CASE btrim(u.subscription_status, E' \t\n\r\x0b\x0c')
      WHEN 'active' THEN 'active'      WHEN 'trialing' THEN 'active'
      WHEN 'grace' THEN 'grace'
      WHEN 'past_due' THEN 'billing_retry' WHEN 'unpaid' THEN 'billing_retry'
      WHEN 'billing_retry' THEN 'billing_retry'
      WHEN '' THEN 'expired'           WHEN 'inactive' THEN 'expired'
      WHEN 'incomplete' THEN 'expired' WHEN 'incomplete_expired' THEN 'expired'
      WHEN 'expired' THEN 'expired'
      WHEN 'canceled' THEN 'revoked'   WHEN 'revoked' THEN 'revoked'
    END AS new_status,
    (u.current_period_end IS NOT NULL AND u.current_period_end > now()) AS future_end
  FROM users_userprofile u
  WHERE NOT (u.stripe_subscription_id = '' AND u.stripe_price_id = '' AND u.cancel_at_period_end = false)
),
judged AS (
  SELECT
    cand.*,
    (old_status <> 'canceled' AND CASE WHEN current_period_end IS NOT NULL THEN future_end
                                       ELSE old_status IN ('active', 'trialing') END) AS legacy_active,
    (new_status IN ('active', 'grace') AND future_end) AS normalized_active
  FROM cand
)
SELECT
  COUNT(*) AS candidates,
  COUNT(*) FILTER (WHERE stripe_subscription_id <> btrim(stripe_subscription_id, E' \t\n\r\x0b\x0c')
                      OR stripe_price_id <> btrim(stripe_price_id, E' \t\n\r\x0b\x0c'))
    AS r1_malformed_identifier_whitespace,
  COUNT(*) FILTER (WHERE stripe_price_id <> '' AND stripe_subscription_id = '')
    AS r2_price_without_subscription,
  COUNT(*) FILTER (WHERE stripe_subscription_id <> '' AND stripe_price_id = '')
    AS r3_subscription_without_price,
  COUNT(*) FILTER (WHERE stripe_subscription_id = '' AND stripe_price_id = '')
    AS r4_cancel_scheduled_without_identity,
  (SELECT COUNT(*) FROM (
     SELECT stripe_subscription_id FROM cand WHERE stripe_subscription_id <> ''
     GROUP BY 1 HAVING COUNT(*) > 1) d)
    AS r5_subscription_id_on_multiple_profiles,
  COUNT(*) FILTER (WHERE stripe_subscription_id <> '' AND stripe_price_id <> '' AND new_status IS NULL)
    AS r6_unmapped_status,
  COUNT(*) FILTER (WHERE stripe_subscription_id <> '' AND stripe_price_id <> '' AND new_status IS NOT NULL
                     AND legacy_active IS DISTINCT FROM normalized_active)
    AS r7_entitlement_parity_mismatch
FROM judged;
-- r4 can only be non-zero if 0011's r7 is also non-zero (0011 raises first).

-- 4-E. Rows 0013 WILL INSERT into users_premiumsubscription, by resulting status.
WITH cand AS (
  SELECT
    u.*,
    CASE btrim(u.subscription_status, E' \t\n\r\x0b\x0c')
      WHEN 'active' THEN 'active'      WHEN 'trialing' THEN 'active'
      WHEN 'grace' THEN 'grace'
      WHEN 'past_due' THEN 'billing_retry' WHEN 'unpaid' THEN 'billing_retry'
      WHEN 'billing_retry' THEN 'billing_retry'
      WHEN '' THEN 'expired'           WHEN 'inactive' THEN 'expired'
      WHEN 'incomplete' THEN 'expired' WHEN 'incomplete_expired' THEN 'expired'
      WHEN 'expired' THEN 'expired'
      WHEN 'canceled' THEN 'revoked'   WHEN 'revoked' THEN 'revoked'
    END AS new_status
  FROM users_userprofile u
  WHERE u.stripe_subscription_id <> '' AND u.stripe_price_id <> ''
)
SELECT
  new_status,
  (current_period_end > now()) AS period_end_in_future,
  (NOT cancel_at_period_end) AS auto_renew_enabled,
  COUNT(*) AS rows_to_insert
FROM cand
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
-- Sum of rows_to_insert = rows expected in users_premiumsubscription after 0013
-- (only if 4-R is all zero).

-- 4-P. Per-row pre-image of the 0013 candidates (recovery / post-check reference).
SELECT
  u.id AS profile_id,
  u.user_id,
  u.subscription_status,
  u.current_period_end,
  u.cancel_at_period_end,
  LEFT(u.stripe_subscription_id, 8) AS subscription_id_prefix
FROM users_userprofile u
WHERE NOT (u.stripe_subscription_id = '' AND u.stripe_price_id = '' AND u.cancel_at_period_end = false)
ORDER BY u.id;


-- ============================================================================
-- SECTION 5 -- 0014 (CreateModel + noop forward) / 0015 (AddField, RunPython,
-- constraints)
-- 0014's forward does nothing besides creating an empty table (1-b).
-- 0015's `backfill_apple_pass_environments` RAISES for every Apple Pass row,
-- because the receipts table 0014 just created is empty.
-- ============================================================================

-- 5-R. Raise / constraint conditions. Expected: every column = 0.
SELECT
  (SELECT COUNT(*) FROM users_premiumpasspurchase WHERE source = 'apple')
    AS r1_apple_pass_rows_would_raise,
  (SELECT COUNT(*) FROM (
     SELECT source, external_id FROM users_premiumpasspurchase
     WHERE source <> 'apple' GROUP BY 1, 2 HAVING COUNT(*) > 1) d)
    AS r2_duplicate_non_apple_external_id;

-- 5-a. Pass sources present (anything other than 'stripe' is worth a look).
SELECT source, COUNT(*) AS purchases
FROM users_premiumpasspurchase
GROUP BY source
ORDER BY source;
