-- F-6C — Production fresh PRE verification for the explicit PlaceRef backfill
-- that a future F-6D migration would perform.
--
--   READ-ONLY. SELECT / WITH statements only.
--   No UPDATE / INSERT / DELETE / ALTER / CREATE / DROP.
--   No psql meta-command (the read-only guard splits on ';' and requires every
--   statement to start with an allowed read-only verb).
--
-- Gate contract:
--   docs/audit/place-id-shadow-identity-hardening.md  (F-6A §7 / F-6C)
--
-- Mother Ship decisions still pending:
--   C1_BACKFILL_EXECUTION = MOTHER_SHIP_DECISION_REQUIRED
--
-- Identity authority note:
--   PlaceRef.name / address / coordinates read in SECTION 2 are OBSERVATION
--   ONLY. They are NOT Shrine identity authority. The identity mapping
--   authority remains the audited explicit migration-0100 mapping:
--
--     ChIJl-MEepfxGGAR1Eo44p__GaE -> Shrine 22  (給田六所神社)
--     ChIJX19mq8nxGGARsA2kP4gX90M -> Shrine 21  (長太稲荷神社)
--     ChIJK11I4BGJGGAR5mZswigcu58 -> Shrine 49  (富岡八幡宮)
--
-- Run only through the sanctioned bridge:
--   scripts/migration_safety/readonly_query.sh \
--     ~/.config/kami-musubi/production-db.env DATABASE_URL \
--     scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql


-- =====================================================================
-- SECTION 0 — MIGRATION LEDGER
-- =====================================================================
-- 0100 applied?  current repository leaf applied?  anything newer than the
-- repository leaf?  any future F-6D migration already recorded?
--
-- CURRENT_REPOSITORY_LEAF is resolved from fresh develop before running and
-- is pinned here as a literal so the ledger check is reproducible:
--
--   EXPECTED_LEAF_NUMBER = 113
--   EXPECTED_LEAF_NAME   = 0113_adopt_usa_jingu_position
--
-- Drift detection does NOT rely on lexical comparison alone. A lexical
-- `name > '0113_adopt_usa_jingu_position'` misses two real branch shapes:
--
--   (a) a migration whose 4-digit prefix is HIGHER than the leaf but whose
--       full name sorts LOWER (e.g. '0114_add_x' > leaf lexically, but
--       '0200_a' vs a longer leaf name can invert depending on the suffix);
--   (b) an unknown SIBLING at the SAME number as the leaf
--       (e.g. '0113_something_else'), which never sorts above the leaf at
--       all and would be completely invisible to a lexical check.
--
-- Both are surfaced as explicit metrics and both gate F6D_PRE_ELIGIBLE.
-- A name that has no parseable 4-digit prefix is also unexpected and gates
-- (fail closed rather than silently ignoring it).

SELECT
    '0.1 migration_ledger' AS section,
    m.id,
    m.app,
    m.name,
    (substring(m.name from '^[0-9]{4}'))::int AS migration_number,
    m.applied
FROM django_migrations AS m
WHERE m.app = 'temples'
  AND (
        m.name = '0100_p8a_duplicate_shrine_shadow_cleanup'
     OR m.name = '0113_adopt_usa_jingu_position'
     OR m.name > '0113_adopt_usa_jingu_position'
     OR (substring(m.name from '^[0-9]{4}'))::int > 113
     OR ((substring(m.name from '^[0-9]{4}'))::int = 113
         AND m.name <> '0113_adopt_usa_jingu_position')
     OR substring(m.name from '^[0-9]{4}') IS NULL
  )
ORDER BY m.name;

-- 0.1b Every row that constitutes an UNKNOWN BRANCH, with the reason.
SELECT
    '0.1b unknown_migration_branch' AS section,
    m.name,
    (substring(m.name from '^[0-9]{4}'))::int AS migration_number,
    m.applied,
    CASE
        WHEN substring(m.name from '^[0-9]{4}') IS NULL
            THEN 'NO_NUMERIC_PREFIX'
        WHEN (substring(m.name from '^[0-9]{4}'))::int > 113
            THEN 'NUMBER_ABOVE_EXPECTED_LEAF'
        WHEN (substring(m.name from '^[0-9]{4}'))::int = 113
             AND m.name <> '0113_adopt_usa_jingu_position'
            THEN 'UNKNOWN_SAME_NUMBER_SIBLING'
        ELSE 'LEXICALLY_ABOVE_EXPECTED_LEAF'
    END AS drift_reason
FROM django_migrations AS m
WHERE m.app = 'temples'
  AND (
        substring(m.name from '^[0-9]{4}') IS NULL
     OR (substring(m.name from '^[0-9]{4}'))::int > 113
     OR ((substring(m.name from '^[0-9]{4}'))::int = 113
         AND m.name <> '0113_adopt_usa_jingu_position')
     OR m.name > '0113_adopt_usa_jingu_position'
  )
ORDER BY m.name;

SELECT
    '0.2 migration_ledger_tail' AS section,
    m.name,
    m.applied
FROM django_migrations AS m
WHERE m.app = 'temples'
ORDER BY m.name DESC
LIMIT 10;

SELECT
    '0.3 migration_ledger_counts' AS section,
    count(*) FILTER (
        WHERE m.name = '0100_p8a_duplicate_shrine_shadow_cleanup'
    ) AS migration_0100_applied,
    count(*) FILTER (
        WHERE m.name = '0113_adopt_usa_jingu_position'
    ) AS current_parent_applied,
    count(*) FILTER (
        WHERE m.name > '0113_adopt_usa_jingu_position'
    ) AS production_has_unknown_newer_migration,
    count(*) FILTER (
        WHERE (substring(m.name from '^[0-9]{4}'))::int > 113
    ) AS migration_number_above_leaf_count,
    count(*) FILTER (
        WHERE (substring(m.name from '^[0-9]{4}'))::int = 113
          AND m.name <> '0113_adopt_usa_jingu_position'
    ) AS unknown_same_number_sibling_count,
    count(*) FILTER (
        WHERE substring(m.name from '^[0-9]{4}') IS NULL
    ) AS migration_name_unparseable_count,
    max((substring(m.name from '^[0-9]{4}'))::int) AS max_migration_number,
    count(*) FILTER (
        WHERE m.name ILIKE '%place_ref%backfill%'
           OR m.name ILIKE '%f6d%'
    ) AS future_f6d_already_recorded,
    count(*) AS temples_migration_rows
FROM django_migrations AS m
WHERE m.app = 'temples';


-- =====================================================================
-- SECTION 1 — PRIMARY SHRINES (21 / 22 / 49)
-- =====================================================================
-- Expected: exactly 3 rows, every place_ref_id NULL, identity as audited.
-- `location` is deliberately NOT selected: Production's temples_shrine.location
-- is a legacy text column while the model declares a PostGIS PointField, and a
-- bare select of it raises before any row is read (same guard as 0091 / 0094 /
-- 0098 / 0099 / 0100 which all use .only(...)).

SELECT
    '1.1 primary_shrines' AS section,
    s.id,
    s.name_jp,
    s.address,
    s.latitude,
    s.longitude,
    s.place_ref_id
FROM temples_shrine AS s
WHERE s.id IN (21, 22, 49)
ORDER BY s.id;

SELECT
    '1.2 primary_identity_match' AS section,
    s.id,
    (
        (s.id = 21
         AND s.name_jp = '長太稲荷神社'
         AND s.address = '日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０')
     OR (s.id = 22
         AND s.name_jp = '給田六所神社'
         AND s.address = '日本、〒157-0064 東京都世田谷区給田１丁目３−７')
     OR (s.id = 49
         AND s.name_jp = '富岡八幡宮'
         AND s.address = '東京都江東区富岡1-20-3'
         AND s.latitude = 35.6717809
         AND s.longitude = 139.799519)
    ) AS identity_matches_audited_snapshot,
    (s.place_ref_id IS NULL) AS place_ref_is_null
FROM temples_shrine AS s
WHERE s.id IN (21, 22, 49)
ORDER BY s.id;


-- =====================================================================
-- SECTION 2 — TARGET PLACEREFS
-- =====================================================================
-- Expected: exactly 3 rows.
--
-- OBSERVATION ONLY — these values are NOT Shrine identity authority.
--
-- snapshot_json is reported as (size, top-level key count, md5 of its text
-- form) rather than dumped raw: the raw Google Places payload is several KB
-- per row and would make the aligned psql output unreadable. The md5 makes
-- the value reproducible and comparable across runs without printing it.

SELECT
    '2.1 target_place_refs' AS section,
    p.place_id,
    p.name,
    p.address,
    p.latitude,
    p.longitude,
    p.synced_at,
    (p.snapshot_json IS NOT NULL) AS snapshot_json_present,
    length(p.snapshot_json::text) AS snapshot_json_text_length,
    md5(p.snapshot_json::text) AS snapshot_json_md5
FROM place_ref AS p
WHERE p.place_id IN (
    'ChIJX19mq8nxGGARsA2kP4gX90M',
    'ChIJl-MEepfxGGAR1Eo44p__GaE',
    'ChIJK11I4BGJGGAR5mZswigcu58'
)
ORDER BY p.place_id;

SELECT
    '2.2 target_place_ref_count' AS section,
    count(*) AS target_place_ref_count
FROM place_ref AS p
WHERE p.place_id IN (
    'ChIJX19mq8nxGGARsA2kP4gX90M',
    'ChIJl-MEepfxGGAR1Eo44p__GaE',
    'ChIJK11I4BGJGGAR5mZswigcu58'
);


-- =====================================================================
-- SECTION 3 — CLAIM CHECK
-- =====================================================================
-- Any Shrine already pointing at one of the three targets.
-- Expected: 0 rows. Any row => F6D_PRODUCTION_PRE = STOP.

SELECT
    '3.1 target_place_ref_claims' AS section,
    s.id AS shrine_id,
    s.name_jp,
    s.place_ref_id
FROM temples_shrine AS s
WHERE s.place_ref_id IN (
    'ChIJX19mq8nxGGARsA2kP4gX90M',
    'ChIJl-MEepfxGGAR1Eo44p__GaE',
    'ChIJK11I4BGJGGAR5mZswigcu58'
)
ORDER BY s.id;


-- =====================================================================
-- SECTION 4 — HISTORICAL SHADOW CHECK
-- =====================================================================
-- Expected: 0 rows. Any row => POST_0100_STATE_DRIFT = YES and
-- F6D_PRODUCTION_PRE = STOP.

SELECT
    '4.1 historical_shadow_rows' AS section,
    s.id,
    s.name_jp,
    s.address,
    s.place_ref_id
FROM temples_shrine AS s
WHERE s.id IN (101, 103, 104)
ORDER BY s.id;


-- =====================================================================
-- SECTION 5 — AUDITED INTERACTION EVENTS
-- =====================================================================
-- Searched GLOBALLY by the canonical predicate
-- (user_id + action_type + metadata.ctx + exact created_at) first, NOT scoped
-- to a shrine — exactly as migration 0100's reverse does. Then the owner is
-- compared against the expected primary.
--
--   Event A  created_at 2026-06-11T07:18:05.580624+00:00 -> shrine_id 22
--   Event B  created_at 2026-06-11T08:00:22.085501+00:00 -> shrine_id 21

SELECT
    '5.1 audited_interaction_events' AS section,
    CASE
        WHEN l.created_at = TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00' THEN 'A'
        ELSE 'B'
    END AS event_label,
    l.id AS interaction_log_id,
    l.user_id,
    l.action_type,
    l.metadata ->> 'ctx' AS metadata_ctx,
    l.created_at,
    l.shrine_id AS current_shrine_id,
    CASE
        WHEN l.created_at = TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00' THEN 22
        ELSE 21
    END AS expected_shrine_id
FROM temples_shrineinteractionlog AS l
WHERE l.user_id = 1
  AND l.action_type = 'detail_view'
  AND l.metadata ->> 'ctx' = 'map'
  AND l.created_at IN (
        TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00',
        TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
  )
ORDER BY l.created_at;

SELECT
    '5.2 audited_interaction_event_counts' AS section,
    count(*) FILTER (
        WHERE l.created_at = TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00'
    ) AS event_a_global_match_count,
    count(*) FILTER (
        WHERE l.created_at = TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00'
          AND l.shrine_id = 22
    ) AS event_a_on_expected_primary,
    count(*) FILTER (
        WHERE l.created_at = TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
    ) AS event_b_global_match_count,
    count(*) FILTER (
        WHERE l.created_at = TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
          AND l.shrine_id = 21
    ) AS event_b_on_expected_primary
FROM temples_shrineinteractionlog AS l
WHERE l.user_id = 1
  AND l.action_type = 'detail_view'
  AND l.metadata ->> 'ctx' = 'map'
  AND l.created_at IN (
        TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00',
        TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
  );


-- =====================================================================
-- SECTION 6 — MACHINE-READABLE GATE SUMMARY
-- =====================================================================
-- Every individual metric is reported alongside the boolean, so a failure is
-- never hidden behind F6D_PRE_ELIGIBLE alone.

WITH primaries AS (
    SELECT
        s.id,
        s.name_jp,
        s.address,
        s.latitude,
        s.longitude,
        s.place_ref_id
    FROM temples_shrine AS s
    WHERE s.id IN (21, 22, 49)
),
primary_stats AS (
    SELECT
        count(*) AS primary_count,
        count(*) FILTER (
            WHERE (p.id = 21
                   AND p.name_jp = '長太稲荷神社'
                   AND p.address = '日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０')
               OR (p.id = 22
                   AND p.name_jp = '給田六所神社'
                   AND p.address = '日本、〒157-0064 東京都世田谷区給田１丁目３−７')
               OR (p.id = 49
                   AND p.name_jp = '富岡八幡宮'
                   AND p.address = '東京都江東区富岡1-20-3'
                   AND p.latitude = 35.6717809
                   AND p.longitude = 139.799519)
        ) AS primary_identity_match_count,
        count(*) FILTER (WHERE p.place_ref_id IS NOT NULL) AS primary_place_ref_nonnull
    FROM primaries AS p
),
target_stats AS (
    SELECT count(*) AS target_place_ref_count
    FROM place_ref AS p
    WHERE p.place_id IN (
        'ChIJX19mq8nxGGARsA2kP4gX90M',
        'ChIJl-MEepfxGGAR1Eo44p__GaE',
        'ChIJK11I4BGJGGAR5mZswigcu58'
    )
),
claim_stats AS (
    SELECT count(*) AS target_place_ref_claim_count
    FROM temples_shrine AS s
    WHERE s.place_ref_id IN (
        'ChIJX19mq8nxGGARsA2kP4gX90M',
        'ChIJl-MEepfxGGAR1Eo44p__GaE',
        'ChIJK11I4BGJGGAR5mZswigcu58'
    )
),
shadow_stats AS (
    SELECT count(*) AS shadow_count
    FROM temples_shrine AS s
    WHERE s.id IN (101, 103, 104)
),
event_stats AS (
    SELECT
        count(*) FILTER (
            WHERE l.created_at = TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00'
        ) AS event_a_count,
        count(*) FILTER (
            WHERE l.created_at = TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00'
              AND l.shrine_id <> 22
        ) AS event_a_wrong_owner,
        count(*) FILTER (
            WHERE l.created_at = TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
        ) AS event_b_count,
        count(*) FILTER (
            WHERE l.created_at = TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
              AND l.shrine_id <> 21
        ) AS event_b_wrong_owner
    FROM temples_shrineinteractionlog AS l
    WHERE l.user_id = 1
      AND l.action_type = 'detail_view'
      AND l.metadata ->> 'ctx' = 'map'
      AND l.created_at IN (
            TIMESTAMPTZ '2026-06-11T07:18:05.580624+00:00',
            TIMESTAMPTZ '2026-06-11T08:00:22.085501+00:00'
      )
),
ledger_stats AS (
    SELECT
        count(*) FILTER (
            WHERE m.name = '0100_p8a_duplicate_shrine_shadow_cleanup'
        ) AS migration_0100_applied,
        count(*) FILTER (
            WHERE m.name = '0113_adopt_usa_jingu_position'
        ) AS current_parent_applied,
        count(*) FILTER (
            WHERE m.name > '0113_adopt_usa_jingu_position'
        ) AS production_has_unknown_newer_migration,
        count(*) FILTER (
            WHERE (substring(m.name from '^[0-9]{4}'))::int > 113
        ) AS migration_number_above_leaf_count,
        count(*) FILTER (
            WHERE (substring(m.name from '^[0-9]{4}'))::int = 113
              AND m.name <> '0113_adopt_usa_jingu_position'
        ) AS unknown_same_number_sibling_count,
        count(*) FILTER (
            WHERE substring(m.name from '^[0-9]{4}') IS NULL
        ) AS migration_name_unparseable_count,
        count(*) FILTER (
            WHERE m.name ILIKE '%place_ref%backfill%'
               OR m.name ILIKE '%f6d%'
        ) AS future_f6d_already_recorded
    FROM django_migrations AS m
    WHERE m.app = 'temples'
)
SELECT
    '6.1 F6D_PRE_GATE_SUMMARY' AS section,
    ps.primary_count                                AS primary_count,
    ps.primary_identity_match_count                 AS primary_identity_match_count,
    ps.primary_place_ref_nonnull                    AS primary_place_ref_nonnull,
    ts.target_place_ref_count                       AS target_place_ref_count,
    cs.target_place_ref_claim_count                 AS target_place_ref_claim_count,
    sh.shadow_count                                 AS shadow_count,
    (es.event_a_count + es.event_b_count)           AS audited_event_exact_count,
    (es.event_a_wrong_owner + es.event_b_wrong_owner) AS audited_event_wrong_owner_count,
    (ls.migration_0100_applied = 1)                 AS migration_0100_applied,
    (ls.current_parent_applied = 1)                 AS current_parent_applied,
    (ls.production_has_unknown_newer_migration > 0) AS production_has_unknown_newer_migration,
    113                                             AS expected_leaf_number,
    '0113_adopt_usa_jingu_position'                 AS expected_leaf_name,
    ls.migration_number_above_leaf_count            AS migration_number_above_leaf_count,
    ls.unknown_same_number_sibling_count            AS unknown_same_number_sibling_count,
    ls.migration_name_unparseable_count             AS migration_name_unparseable_count,
    (
        ls.production_has_unknown_newer_migration > 0
        OR ls.migration_number_above_leaf_count > 0
        OR ls.unknown_same_number_sibling_count > 0
        OR ls.migration_name_unparseable_count > 0
    )                                               AS unknown_migration_branch_detected,
    (ls.future_f6d_already_recorded > 0)            AS future_f6d_already_recorded,
    (
        ps.primary_count = 3
        AND ps.primary_identity_match_count = 3
        AND ps.primary_place_ref_nonnull = 0
        AND ts.target_place_ref_count = 3
        AND cs.target_place_ref_claim_count = 0
        AND sh.shadow_count = 0
        AND es.event_a_count = 1
        AND es.event_b_count = 1
        AND es.event_a_wrong_owner = 0
        AND es.event_b_wrong_owner = 0
        AND ls.migration_0100_applied = 1
        AND ls.current_parent_applied = 1
        AND ls.production_has_unknown_newer_migration = 0
        AND ls.migration_number_above_leaf_count = 0
        AND ls.unknown_same_number_sibling_count = 0
        AND ls.migration_name_unparseable_count = 0
        AND ls.future_f6d_already_recorded = 0
    )                                               AS f6d_pre_eligible
FROM primary_stats AS ps
CROSS JOIN target_stats AS ts
CROSS JOIN claim_stats AS cs
CROSS JOIN shadow_stats AS sh
CROSS JOIN event_stats AS es
CROSS JOIN ledger_stats AS ls;
