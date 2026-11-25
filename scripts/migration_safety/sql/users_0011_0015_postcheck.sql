-- SELECT-only. Safe to run against Production.
--
-- users 0011-0015 post-apply verification. Pair with
-- users_0011_0015_preflight.sql: the INFO rows here must match the
-- preflight's "5 expect" rows recorded just before migrating.
--
-- ONE statement on purpose (the Supabase SQL Editor shows the last result
-- only). Columns: section, check_name, actual, expected, verdict.
-- Only counts and fixed labels are printed; no personal values.
--
-- Note: 0011 changes UserProfile semantics. Rows 31-33 compare the new
-- columns against each other, not against the old values (the old values
-- are in the CSV backup taken before migrating).
WITH
ledger AS (
    SELECT name FROM django_migrations WHERE app = 'users'
),
checks (ord, section, check_name, actual, expected) AS (
    SELECT 1, '0 ledger', 'users latest applied migration',
        coalesce((SELECT max(name) FROM ledger), '(none)'), '0015_apple_billing_environments'
    UNION ALL SELECT 2, '0 ledger', 'users 0011-0015 rows in django_migrations',
        (SELECT count(*) FROM ledger WHERE name >= '0011')::text, '5'
    UNION ALL SELECT 3, '0 schema', 'new tables present',
        ((to_regclass('public.users_premiumsubscription') IS NOT NULL)::int
         + (to_regclass('public.users_applestorekitreceipt') IS NOT NULL)::int)::text, '2'
    UNION ALL SELECT 4, '0 schema', 'new columns present',
        (SELECT count(*) FROM information_schema.columns
          WHERE table_schema = 'public'
            AND ((table_name = 'users_userprofile'
                  AND column_name IN ('legacy_premium_until', 'account_entitlement_disabled'))
              OR (table_name = 'users_premiumpasspurchase'
                  AND column_name IN ('effective_period_end', 'environment'))))::text, '4'
    UNION ALL SELECT 5, '0 schema', 'new unique indexes present',
        (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = 'public' AND c.relname IN (
            'uniq_premium_subscription_stripe_id',
            'uniq_premium_subscription_apple_environment_id',
            'uniq_apple_storekit_receipt',
            'uniq_premium_pass_non_apple_id',
            'uniq_premium_pass_apple_environment_id'))::text, '5'
    UNION ALL SELECT 6, '0 schema', 'new check constraints present',
        (SELECT count(*) FROM pg_constraint
          WHERE conname IN ('premium_subscription_has_provider_id',
                            'premium_pass_environment_matches_source'))::text, '2'
    UNION ALL SELECT 7, '0 schema', 'removed constraints still present',
        ((SELECT count(*) FROM pg_constraint
           WHERE conname = 'uniq_premium_pass_purchase_source_external_id')
         + (SELECT count(*) FROM pg_class WHERE relname = 'uniq_premium_subscription_apple_id'))::text, '0'

    -- 0011 effects
    UNION ALL SELECT 21, '1 users.0011', 'Pass purchases with effective_period_end <> period_end_after',
        (SELECT count(*) FROM users_premiumpasspurchase
          WHERE effective_period_end IS DISTINCT FROM period_end_after)::text, '0'
    UNION ALL SELECT 22, '1 users.0011', 'profiles without Stripe ids still holding deadline/status/cancel',
        (SELECT count(*) FROM users_userprofile
          WHERE stripe_subscription_id = '' AND stripe_price_id = ''
            AND (current_period_end IS NOT NULL OR subscription_status <> 'inactive'
                 OR cancel_at_period_end))::text, '0'
    UNION ALL SELECT 23, '1 users.0011', 'Pass users with legacy_premium_until set',
        (SELECT count(*) FROM users_userprofile
          WHERE legacy_premium_until IS NOT NULL
            AND user_id IN (SELECT user_id FROM users_premiumpasspurchase))::text, '0'
    UNION ALL SELECT 24, '1 users.0011', 'profiles with account_entitlement_disabled = true',
        (SELECT count(*) FROM users_userprofile WHERE account_entitlement_disabled)::text, '0'

    -- 0013 effects
    UNION ALL SELECT 31, '2 users.0013', 'Stripe-id profiles without a matching PremiumSubscription',
        (SELECT count(*) FROM users_userprofile p
          WHERE p.stripe_subscription_id <> ''
            AND NOT EXISTS (SELECT 1 FROM users_premiumsubscription s
                             WHERE s.source = 'stripe'
                               AND s.external_subscription_id = p.stripe_subscription_id
                               AND s.user_id = p.user_id
                               AND s.product_id = p.stripe_price_id))::text, '0'

    -- 0015 effects
    UNION ALL SELECT 41, '4 users.0015', 'non-apple Pass purchases with environment <> empty',
        (SELECT count(*) FROM users_premiumpasspurchase
          WHERE source <> 'apple' AND environment <> '')::text, '0'

    -- compare with preflight "5 expect"
    UNION ALL SELECT 51, '5 compare', 'profiles total',
        (SELECT count(*) FROM users_userprofile)::text, NULL
    UNION ALL SELECT 52, '5 compare', 'Pass purchases total',
        (SELECT count(*) FROM users_premiumpasspurchase)::text, NULL
    UNION ALL SELECT 53, '5 compare', 'Pass purchases by source',
        coalesce((SELECT string_agg(source || '=' || n, ', ' ORDER BY source)
                  FROM (SELECT source, count(*) AS n FROM users_premiumpasspurchase
                        GROUP BY source) s), '(none)'), NULL
    UNION ALL SELECT 54, '5 compare', 'Pass users',
        (SELECT count(DISTINCT user_id) FROM users_premiumpasspurchase)::text, NULL
    UNION ALL SELECT 55, '5 compare', 'profiles without Stripe ids',
        (SELECT count(*) FROM users_userprofile
          WHERE stripe_subscription_id = '' AND stripe_price_id = '')::text, NULL
    UNION ALL SELECT 56, '5 compare', 'profiles with legacy_premium_until (= preflight row "non-Pass with deadline")',
        (SELECT count(*) FROM users_userprofile WHERE legacy_premium_until IS NOT NULL)::text, NULL
    UNION ALL SELECT 57, '5 compare', 'profiles with future legacy_premium_until (= preflight "legacy Premium now")',
        (SELECT count(*) FROM users_userprofile WHERE legacy_premium_until > now())::text, NULL
    UNION ALL SELECT 58, '5 compare', 'Stripe PremiumSubscription rows (= preflight "0013 will create")',
        (SELECT count(*) FROM users_premiumsubscription WHERE source = 'stripe')::text, NULL
    UNION ALL SELECT 59, '5 compare', 'evaluated at (UTC)',
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
