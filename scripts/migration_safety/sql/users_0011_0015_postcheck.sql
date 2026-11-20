-- SELECT-only. Safe to run against Production. Never write, never DDL.
--
-- Post-check after applying `users` 0011 -> 0015. Compare every number with the
-- output of `users_0011_0015_preflight.sql` saved just before `migrate`.
-- Selects internal ids and billing state only (no email / username / nickname /
-- birth fields / Stripe customer ids).
--
--   scripts/migration_safety/readonly_query.sh \
--     ~/.config/kami-musubi/production-db.env DATABASE_URL \
--     scripts/migration_safety/sql/users_0011_0015_postcheck.sql


-- ============================================================================
-- SECTION 0 -- Ledger
-- ============================================================================

-- 0-a. All five recorded, in order.
SELECT name, applied
FROM django_migrations
WHERE app = 'users' AND SUBSTRING(name FROM '^[0-9]{4}')::int >= 10
ORDER BY name;
-- Expected: 0010 .. 0015, six rows; 0011-0015 applied just now.

-- 0-b. Nothing from another app was applied in the same window.
--      Adjust the interval so it starts just before `migrate` was run.
SELECT app, name, applied
FROM django_migrations
WHERE applied >= now() - interval '2 hours'
ORDER BY applied;
-- Expected: only users 0011-0015.


-- ============================================================================
-- SECTION 1 -- Schema post-state
-- ============================================================================

-- 1-a. New columns exist.
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND ((table_name = 'users_userprofile' AND column_name IN ('legacy_premium_until', 'account_entitlement_disabled'))
    OR (table_name = 'users_premiumpasspurchase' AND column_name IN ('effective_period_end', 'environment')))
ORDER BY table_name, column_name;
-- Expected: 4 rows.

-- 1-b. New tables exist.
SELECT
  to_regclass('public.users_premiumsubscription') IS NOT NULL AS premiumsubscription_exists_expected_true,
  to_regclass('public.users_applestorekitreceipt') IS NOT NULL AS applestorekitreceipt_exists_expected_true;

-- 1-c. Constraints / partial unique indexes after 0015.
SELECT 'constraint' AS kind, conname AS name
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
  AND (conname LIKE 'uniq_premium_%' OR conname LIKE 'premium_%' OR conname = 'uniq_apple_storekit_receipt')
UNION ALL
SELECT 'index', indexname
FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'uniq_premium_%'
ORDER BY 1, 2;
-- Expected exactly these 7 rows:
--   constraint premium_pass_environment_matches_source
--   constraint premium_subscription_has_provider_id
--   constraint uniq_apple_storekit_receipt
--   index      uniq_premium_pass_apple_environment_id
--   index      uniq_premium_pass_non_apple_id
--   index      uniq_premium_subscription_apple_environment_id
--   index      uniq_premium_subscription_stripe_id
-- Must be ABSENT: uniq_premium_pass_purchase_source_external_id,
--   uniq_premium_subscription_apple_id.


-- ============================================================================
-- SECTION 2 -- Counts maintained (compare with preflight 2-a)
-- ============================================================================
SELECT
  (SELECT COUNT(*) FROM auth_user) AS auth_user_count,
  (SELECT COUNT(*) FROM users_userprofile) AS userprofile_count,
  (SELECT COUNT(*) FROM users_premiumpasspurchase) AS pass_purchase_count;
-- Expected: identical to preflight 2-a (none of the five migrations deletes rows).


-- ============================================================================
-- SECTION 3 -- 0011 effects (compare with preflight 3-E)
-- ============================================================================
SELECT
  (SELECT COUNT(*) FROM users_premiumpasspurchase
     WHERE effective_period_end IS DISTINCT FROM period_end_after)
    AS pass_effective_end_mismatch_expected_0,
  (SELECT COUNT(*) FROM users_userprofile WHERE legacy_premium_until IS NOT NULL)
    AS legacy_premium_until_non_null_expected_eq_preflight_e2,
  (SELECT COUNT(*) FROM users_userprofile
     WHERE stripe_subscription_id = '' AND stripe_price_id = ''
       AND (current_period_end IS NOT NULL OR subscription_status <> 'inactive' OR cancel_at_period_end))
    AS no_subscription_profile_not_reset_expected_0,
  (SELECT COUNT(*) FROM users_userprofile WHERE account_entitlement_disabled)
    AS account_entitlement_disabled_expected_0;
-- legacy_premium_until_non_null may be HIGHER than preflight e2 only if the
-- application wrote new rows after the migration; it must never be lower.


-- ============================================================================
-- SECTION 4 -- 0013 effects (compare with preflight 4-E / 4-P)
-- ============================================================================

-- 4-a. Every Stripe-subscribed profile has exactly one matching row.
SELECT
  (SELECT COUNT(*) FROM users_userprofile u
     WHERE u.stripe_subscription_id <> '' AND u.stripe_price_id <> ''
       AND NOT EXISTS (
         SELECT 1 FROM users_premiumsubscription s
         WHERE s.source = 'stripe'
           AND s.external_subscription_id = u.stripe_subscription_id
           AND s.user_id = u.user_id
           AND s.product_id = u.stripe_price_id))
    AS subscribed_profile_without_matching_row_expected_0,
  (SELECT COUNT(*) FROM users_premiumsubscription s
     WHERE s.source = 'stripe'
       AND NOT EXISTS (
         SELECT 1 FROM users_userprofile u
         WHERE u.stripe_subscription_id = s.external_subscription_id AND u.user_id = s.user_id))
    AS stripe_row_without_matching_profile_expected_0;

-- 4-b. Distribution of inserted rows (compare with preflight 4-E).
SELECT source, status, (current_period_end > now()) AS period_end_in_future,
       auto_renew_enabled, environment, COUNT(*) AS rows
FROM users_premiumsubscription
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1, 2, 3, 4, 5;
-- Expected: source = 'stripe' only, environment = 'unknown', counts equal to
-- preflight 4-E (period_end_in_future may differ if a deadline passed between
-- the two runs).

-- 4-c. Entitlement parity per subscribed profile: was Premium before <=> is
-- Premium now. Expected: 0 rows.
SELECT u.id AS profile_id, u.user_id, u.subscription_status, u.current_period_end,
       s.status AS new_status
FROM users_userprofile u
JOIN users_premiumsubscription s
  ON s.source = 'stripe' AND s.external_subscription_id = u.stripe_subscription_id
WHERE (btrim(u.subscription_status) <> 'canceled'
       AND CASE WHEN u.current_period_end IS NOT NULL THEN u.current_period_end > now()
                ELSE btrim(u.subscription_status) IN ('active', 'trialing') END)
  IS DISTINCT FROM
      (s.status IN ('active', 'grace') AND s.current_period_end IS NOT NULL AND s.current_period_end > now());


-- ============================================================================
-- SECTION 5 -- 0014 / 0015 effects
-- ============================================================================
SELECT
  (SELECT COUNT(*) FROM users_applestorekitreceipt) AS apple_receipts_expected_0,
  (SELECT COUNT(*) FROM users_premiumsubscription WHERE source = 'apple') AS apple_subscriptions_expected_0,
  (SELECT COUNT(*) FROM users_premiumpasspurchase WHERE source = 'apple') AS apple_passes_expected_0,
  (SELECT COUNT(*) FROM users_premiumpasspurchase WHERE source <> 'apple' AND environment <> '')
    AS non_apple_pass_with_environment_expected_0;
-- Non-zero Apple counts are fine ONLY if the app recorded new Apple purchases
-- after the migration; check `created_at` before treating them as a failure.
