-- SELECT-only. Safe to run against Production.
--
-- users 0011 -> 0012 -> 0013 -> 0014 -> 0015 Production-apply preflight.
-- Use this immediately before applying those five, and only those five.
--
-- Written as ONE statement on purpose: the Supabase SQL Editor shows the
-- result of the last statement only, so every check is one output row.
-- Columns: section, check_name, actual, expected, verdict.
--   verdict = PASS / FAIL / INFO.  Any FAIL -> STOP, do not migrate.
-- Every value is a count or a fixed label. No user id, email, Stripe id or
-- other personal value is printed, so the output may be shared as-is.
--
-- Each FAIL row mirrors one RuntimeError condition in the migration code
-- (backend/users/migrations/0011, 0013, 0015). 0012 and 0014 only create
-- tables. Checks for 0013 are evaluated on current data: 0011 only rewrites
-- profiles with no Stripe ids, which 0013 never reads.
--
-- Before pasting into the Dashboard, run locally (no credential involved):
--   python3 scripts/migration_safety/guard.py check-readonly-sql \
--     scripts/migration_safety/sql/users_0011_0015_preflight.sql
WITH
ledger AS (
    SELECT name FROM django_migrations WHERE app = 'users'
),
prof AS (
    SELECT
        user_id,
        stripe_subscription_id AS sub,
        stripe_price_id AS price,
        cancel_at_period_end AS cancel,
        current_period_end AS period_end,
        regexp_replace(subscription_status, '^[[:space:]]+|[[:space:]]+$', '', 'g') AS status_stripped
    FROM users_userprofile
),
pass_users AS (
    SELECT DISTINCT user_id FROM users_premiumpasspurchase
),
chain AS (
    SELECT
        p.user_id,
        p.created_at,
        p.period_end_before,
        p.period_end_after,
        p.status,
        p.refunded_at,
        row_number() OVER w AS seq,
        lag(p.period_end_after) OVER w AS prev_after,
        row_number() OVER (PARTITION BY p.user_id ORDER BY p.created_at DESC, p.id DESC) AS rev_seq
    FROM users_premiumpasspurchase p
    WINDOW w AS (PARTITION BY p.user_id ORDER BY p.created_at, p.id)
),
-- 0013 reads profiles that still have a Stripe id after 0011.
stripe_candidates AS (
    SELECT * FROM prof WHERE NOT (sub = '' AND price = '' AND cancel = false)
),
parity AS (
    SELECT
        status_stripped,
        (period_end IS NOT NULL AND period_end > now()) AS future_end,
        period_end
    FROM stripe_candidates
),
checks (ord, section, check_name, actual, expected) AS (
    -- Section 0: ledger and schema position
    SELECT 1, '0 ledger', 'users latest applied migration',
        coalesce((SELECT max(name) FROM ledger), '(none)'), '0010_premium_pass_purchase'
    UNION ALL SELECT 2, '0 ledger', 'users 0011-0015 rows already in django_migrations',
        (SELECT count(*) FROM ledger WHERE name >= '0011')::text, '0'
    UNION ALL SELECT 3, '0 schema', 'users_premiumsubscription exists',
        (to_regclass('public.users_premiumsubscription') IS NOT NULL)::text, 'false'
    UNION ALL SELECT 4, '0 schema', 'users_applestorekitreceipt exists',
        (to_regclass('public.users_applestorekitreceipt') IS NOT NULL)::text, 'false'
    UNION ALL SELECT 5, '0 schema', 'columns to be added already present',
        (SELECT count(*) FROM information_schema.columns
          WHERE table_schema = 'public'
            AND ((table_name = 'users_userprofile'
                  AND column_name IN ('legacy_premium_until', 'account_entitlement_disabled'))
              OR (table_name = 'users_premiumpasspurchase'
                  AND column_name IN ('effective_period_end', 'environment'))))::text, '0'
    UNION ALL SELECT 6, '0 schema', 'constraint/index names to be created already taken',
        (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = 'public' AND c.relname IN (
            'uniq_premium_subscription_stripe_id',
            'uniq_premium_subscription_apple_id',
            'uniq_premium_subscription_apple_environment_id',
            'uniq_apple_storekit_receipt',
            'uniq_premium_pass_non_apple_id',
            'uniq_premium_pass_apple_environment_id'))::text
        || '+' ||
        (SELECT count(*) FROM pg_constraint
          WHERE conname IN ('premium_subscription_has_provider_id',
                            'premium_pass_environment_matches_source'))::text, '0+0'
    UNION ALL SELECT 7, '0 schema', 'constraint removed by 0015 present (uniq_premium_pass_purchase_source_external_id)',
        (SELECT count(*) FROM pg_constraint
          WHERE conname = 'uniq_premium_pass_purchase_source_external_id')::text, '1'

    -- Section 1: 0011 separate_entitlements (fail-closed)
    UNION ALL SELECT 11, '1 users.0011', 'Pass purchases whose user has no profile',
        (SELECT count(*) FROM pass_users pu
          WHERE NOT EXISTS (SELECT 1 FROM prof WHERE prof.user_id = pu.user_id))::text, '0'
    UNION ALL SELECT 12, '1 users.0011', 'Pass users with Stripe id or cancel_at_period_end',
        (SELECT count(*) FROM prof JOIN pass_users USING (user_id)
          WHERE sub <> '' OR price <> '' OR cancel)::text, '0'
    UNION ALL SELECT 13, '1 users.0011', 'first Pass purchase with period_end_before > created_at',
        (SELECT count(*) FROM chain
          WHERE seq = 1 AND period_end_before IS NOT NULL
            AND period_end_before > created_at)::text, '0'
    UNION ALL SELECT 14, '1 users.0011', 'Pass purchase whose period_end_before breaks the chain',
        (SELECT count(*) FROM chain
          WHERE seq > 1 AND period_end_before IS DISTINCT FROM prev_after)::text, '0'
    UNION ALL SELECT 15, '1 users.0011', 'Pass purchase not completed or with refunded_at',
        (SELECT count(*) FROM chain c JOIN prof USING (user_id)
          WHERE c.status <> 'completed' OR c.refunded_at IS NOT NULL)::text, '0'
    UNION ALL SELECT 16, '1 users.0011', 'Pass users whose last period_end_after differs from profile deadline',
        (SELECT count(*) FROM chain c JOIN prof USING (user_id)
          WHERE c.rev_seq = 1 AND c.period_end_after IS DISTINCT FROM prof.period_end)::text, '0'
    UNION ALL SELECT 17, '1 users.0011', 'profiles without Stripe ids but cancel_at_period_end = true',
        (SELECT count(*) FROM prof WHERE sub = '' AND price = '' AND cancel)::text, '0'

    -- Section 2: 0013 backfill_stripe_subscriptions (fail-closed)
    UNION ALL SELECT 21, '2 users.0013', 'Stripe ids with leading/trailing whitespace',
        (SELECT count(*) FROM stripe_candidates
          WHERE sub ~ '^[[:space:]]|[[:space:]]$' OR price ~ '^[[:space:]]|[[:space:]]$')::text, '0'
    UNION ALL SELECT 22, '2 users.0013', 'price id without subscription id',
        (SELECT count(*) FROM stripe_candidates WHERE price <> '' AND sub = '')::text, '0'
    UNION ALL SELECT 23, '2 users.0013', 'subscription id without price id',
        (SELECT count(*) FROM stripe_candidates WHERE sub <> '' AND price = '')::text, '0'
    UNION ALL SELECT 24, '2 users.0013', 'subscription ids shared by multiple profiles',
        (SELECT count(*) FROM (SELECT sub FROM stripe_candidates WHERE sub <> ''
                               GROUP BY sub HAVING count(*) > 1) d)::text, '0'
    UNION ALL SELECT 25, '2 users.0013', 'subscription_status with no mapping',
        (SELECT count(*) FROM stripe_candidates
          WHERE status_stripped NOT IN ('active', 'trialing', 'grace', 'past_due', 'unpaid',
                'billing_retry', '', 'inactive', 'incomplete', 'incomplete_expired',
                'expired', 'canceled', 'revoked'))::text, '0'
    UNION ALL SELECT 26, '2 users.0013', 'entitlement parity mismatch (legacy vs normalized, at now())',
        (SELECT count(*) FROM parity
          WHERE (status_stripped <> 'canceled'
                 AND CASE WHEN period_end IS NOT NULL THEN future_end
                          ELSE status_stripped IN ('active', 'trialing') END)
             IS DISTINCT FROM
                (status_stripped IN ('active', 'trialing', 'grace') AND future_end))::text, '0'

    -- Section 3: 0014 creates users_applestorekitreceipt only (see Section 0)

    -- Section 4: 0015 backfill_apple_pass_environments (fail-closed)
    UNION ALL SELECT 41, '4 users.0015', 'Pass purchases with source = apple (receipt table is empty before 0014)',
        (SELECT count(*) FROM users_premiumpasspurchase WHERE source = 'apple')::text, '0'

    -- Section 5: expected effects, recorded for post-migration comparison
    UNION ALL SELECT 51, '5 expect', 'profiles total',
        (SELECT count(*) FROM prof)::text, NULL
    UNION ALL SELECT 52, '5 expect', 'Pass purchases total (0011 sets effective_period_end)',
        (SELECT count(*) FROM users_premiumpasspurchase)::text, NULL
    UNION ALL SELECT 53, '5 expect', 'Pass purchases by source',
        coalesce((SELECT string_agg(source || '=' || n, ', ' ORDER BY source)
                  FROM (SELECT source, count(*) AS n FROM users_premiumpasspurchase
                        GROUP BY source) s), '(none)'), NULL
    UNION ALL SELECT 54, '5 expect', 'Pass users',
        (SELECT count(*) FROM pass_users)::text, NULL
    UNION ALL SELECT 55, '5 expect', 'profiles without Stripe ids (0011 clears deadline/status)',
        (SELECT count(*) FROM prof WHERE sub = '' AND price = '')::text, NULL
    UNION ALL SELECT 56, '5 expect', 'of which non-Pass with deadline (0011 moves to legacy_premium_until)',
        (SELECT count(*) FROM prof
          WHERE sub = '' AND price = '' AND period_end IS NOT NULL
            AND user_id NOT IN (SELECT user_id FROM pass_users))::text, NULL
    UNION ALL SELECT 57, '5 expect', 'of which non-Pass with future deadline (legacy Premium now)',
        (SELECT count(*) FROM prof
          WHERE sub = '' AND price = '' AND period_end > now()
            AND user_id NOT IN (SELECT user_id FROM pass_users))::text, NULL
    UNION ALL SELECT 58, '5 expect', 'Stripe subscriptions 0013 will create',
        (SELECT count(*) FROM stripe_candidates)::text, NULL
    UNION ALL SELECT 59, '5 expect', 'evaluated at (UTC)',
        to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'), NULL
)
SELECT
    section,
    check_name,
    actual,
    expected,
    CASE WHEN expected IS NULL THEN 'INFO'
         WHEN actual = expected THEN 'PASS'
         ELSE 'FAIL' END AS verdict
FROM checks
ORDER BY ord
