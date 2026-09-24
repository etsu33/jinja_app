-- F-6D — Production POST verification for the explicit PlaceRef backfill
-- performed by `temples.0114_f6d_explicit_place_ref_backfill`.
--
--   READ-ONLY. SELECT / WITH statements only.
--   No UPDATE / INSERT / DELETE / ALTER / CREATE / DROP.
--   No psql meta-command (the read-only guard splits on ';' and requires every
--   statement to start with an allowed read-only verb).
--
-- Gate contract:
--   docs/audit/place-id-shadow-identity-hardening.md  (F-6D Production Apply Gate)
--
-- Relationship to the PRE file:
--   scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql is the
--   PINNED pre-F6D evidence and is deliberately NOT edited. It pins
--   EXPECTED_LEAF = 0113 and therefore reports `f6d_pre_eligible = false`
--   once 0114 exists — that is correct pre-F6D-gate behaviour, not drift.
--   This file is its post-apply counterpart and pins EXPECTED_LEAF = 0114.
--
-- Identity authority note:
--   PlaceRef.name / address / coordinates read in SECTION 2 are OBSERVATION
--   ONLY. They are NOT Shrine identity authority and are NOT used to decide
--   or confirm any mapping. The mapping authority is the static audited P8-A
--   mapping that migration 0114 carries as its own decision provenance:
--
--     ChIJl-MEepfxGGAR1Eo44p__GaE -> Shrine 22  (給田六所神社)
--     ChIJX19mq8nxGGARsA2kP4gX90M -> Shrine 21  (長太稲荷神社)
--     ChIJK11I4BGJGGAR5mZswigcu58 -> Shrine 49  (富岡八幡宮)
--
--   IDENTITY_AUTHORITY          = Shrine.id
--   PLACE_ID_IDENTITY_AUTHORITY = NO
--   HEURISTIC_SELECTION         = PROHIBITED
--
-- `temples_shrine.location` is deliberately NEVER selected: Production's
-- column is a legacy `text` column while the model declares a PostGIS
-- PointField, and a bare select of it raises before any row is read (same
-- guard as 0091 / 0094 / 0098 / 0099 / 0100 / 0114).
--
-- Run only through the sanctioned bridge:
--   scripts/migration_safety/readonly_query.sh \
--     ~/.config/kami-musubi/production-db.env DATABASE_URL \
--     scripts/migration_safety/sql/f6d_place_ref_backfill_postcheck.sql


-- =====================================================================
-- SECTION 0 — MIGRATION LEDGER
-- =====================================================================
-- Expected after the Gate has been executed:
--
--   EXPECTED_LEAF_NUMBER = 114
--   EXPECTED_LEAF_NAME   = 0114_f6d_explicit_place_ref_backfill
--
--   * exactly ONE applied row named 0114_f6d_explicit_place_ref_backfill
--   * temples' latest migration IS that row
--   * no migration with a numeric prefix ABOVE 114
--   * no UNKNOWN SIBLING at numeric prefix 114
--   * no name without a parseable 4-digit prefix
--
-- Drift detection does not rely on lexical comparison alone. A lexical
-- `name > '0114_f6d_explicit_place_ref_backfill'` misses two real branch
-- shapes:
--
--   (a) a migration whose 4-digit prefix is higher than the leaf but whose
--       full name can sort lower depending on the suffix;
--   (b) an unknown SIBLING at the SAME number as the leaf
--       (e.g. '0114_something_else'), which never sorts above the leaf at
--       all and would be completely invisible to a lexical check.
--
-- Both are surfaced as explicit metrics and both gate F6D_POST_VERIFIED.
-- A name with no parseable 4-digit prefix also gates (fail closed rather
-- than silently ignoring it).

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
     OR m.name = '0114_f6d_explicit_place_ref_backfill'
     OR m.name > '0114_f6d_explicit_place_ref_backfill'
     OR (substring(m.name from '^[0-9]{4}'))::int > 114
     OR ((substring(m.name from '^[0-9]{4}'))::int = 114
         AND m.name <> '0114_f6d_explicit_place_ref_backfill')
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
        WHEN (substring(m.name from '^[0-9]{4}'))::int > 114
            THEN 'NUMBER_ABOVE_EXPECTED_LEAF'
        WHEN (substring(m.name from '^[0-9]{4}'))::int = 114
             AND m.name <> '0114_f6d_explicit_place_ref_backfill'
            THEN 'UNKNOWN_SAME_NUMBER_SIBLING'
        ELSE 'LEXICALLY_ABOVE_EXPECTED_LEAF'
    END AS drift_reason
FROM django_migrations AS m
WHERE m.app = 'temples'
  AND (
        substring(m.name from '^[0-9]{4}') IS NULL
     OR (substring(m.name from '^[0-9]{4}'))::int > 114
     OR ((substring(m.name from '^[0-9]{4}'))::int = 114
         AND m.name <> '0114_f6d_explicit_place_ref_backfill')
     OR m.name > '0114_f6d_explicit_place_ref_backfill'
  )
ORDER BY m.name;

SELECT
    '0.2 migration_ledger_tail' AS section,
    m.name,
    m.applied
FROM django_migrations AS m
WHERE m.app = 'temples'
ORDER BY (substring(m.name from '^[0-9]{4}'))::int DESC NULLS LAST, m.name DESC
LIMIT 10;

SELECT
    '0.3 migration_ledger_counts' AS section,
    count(*) FILTER (
        WHERE m.name = '0100_p8a_duplicate_shrine_shadow_cleanup'
    ) AS migration_0100_applied,
    count(*) FILTER (
        WHERE m.name = '0113_adopt_usa_jingu_position'
    ) AS migration_0113_applied,
    count(*) FILTER (
        WHERE m.name = '0114_f6d_explicit_place_ref_backfill'
    ) AS migration_0114_applied_rows,
    count(*) FILTER (
        WHERE m.name > '0114_f6d_explicit_place_ref_backfill'
    ) AS lexically_above_leaf_count,
    count(*) FILTER (
        WHERE (substring(m.name from '^[0-9]{4}'))::int > 114
    ) AS migration_number_above_leaf_count,
    count(*) FILTER (
        WHERE (substring(m.name from '^[0-9]{4}'))::int = 114
          AND m.name <> '0114_f6d_explicit_place_ref_backfill'
    ) AS unknown_same_number_sibling_count,
    count(*) FILTER (
        WHERE substring(m.name from '^[0-9]{4}') IS NULL
    ) AS migration_name_unparseable_count,
    max((substring(m.name from '^[0-9]{4}'))::int) AS max_migration_number,
    count(*) AS temples_migration_rows
FROM django_migrations AS m
WHERE m.app = 'temples';

-- 0.4 The single latest temples migration, resolved by numeric prefix first
-- (lexical order alone is not authoritative — see the SECTION 0 note).
SELECT
    '0.4 temples_latest_migration' AS section,
    m.name AS temples_latest_name,
    (substring(m.name from '^[0-9]{4}'))::int AS temples_latest_number,
    m.applied,
    (m.name = '0114_f6d_explicit_place_ref_backfill') AS latest_is_expected_leaf
FROM django_migrations AS m
WHERE m.app = 'temples'
ORDER BY (substring(m.name from '^[0-9]{4}'))::int DESC NULLS LAST, m.name DESC
LIMIT 1;


-- =====================================================================
-- SECTION 1 — PRIMARY SHRINES (21 / 22 / 49) AND THEIR MAPPING
-- =====================================================================
-- Expected: exactly 3 rows, audited identity unchanged, and each row now
-- carrying EXACTLY its audited place_ref_id.
--
--   21 長太稲荷神社  -> ChIJX19mq8nxGGARsA2kP4gX90M
--   22 給田六所神社  -> ChIJl-MEepfxGGAR1Eo44p__GaE
--   49 富岡八幡宮    -> ChIJK11I4BGJGGAR5mZswigcu58
--
-- Shrine 49's coordinate is the P8-C (temples.0099) corrected value and is
-- verified here as an immutability check — 0114 must not have touched it.
-- `location` is NOT selected (legacy text column guard).

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
    '1.2 primary_identity_and_mapping' AS section,
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
    (
        (s.id = 21 AND s.place_ref_id = 'ChIJX19mq8nxGGARsA2kP4gX90M')
     OR (s.id = 22 AND s.place_ref_id = 'ChIJl-MEepfxGGAR1Eo44p__GaE')
     OR (s.id = 49 AND s.place_ref_id = 'ChIJK11I4BGJGGAR5mZswigcu58')
    ) AS mapping_matches_audited_pair,
    s.place_ref_id
FROM temples_shrine AS s
WHERE s.id IN (21, 22, 49)
ORDER BY s.id;


-- =====================================================================
-- SECTION 2 — TARGET PLACEREFS
-- =====================================================================
-- Expected: exactly 3 rows — 0114 binds them, it must never delete them
-- (C3_ROLLBACK = ... + KEEP_PLACE_REF_ROWS).
--
-- OBSERVATION ONLY — these values are NOT Shrine identity authority and no
-- gate metric is derived from name / address / coordinates.
--
-- snapshot_json is reported as (presence, text length, md5 of its text form)
-- rather than dumped raw: the raw Google Places payload is several KB per row
-- and would make the aligned psql output unreadable. The md5 makes the value
-- reproducible and comparable against the PRE run without printing it.

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
-- Every Shrine pointing at one of the three targets, whoever it is.
-- Expected: exactly the 3 audited pairs and nothing else.
--
--   TARGET_PLACE_REF_CLAIM_COUNT = 3
--   EXPECTED_MAPPING_MATCH_COUNT = 3
--   UNEXPECTED_CLAIM_COUNT       = 0
--
-- An UNEXPECTED claim is a claim on a target place_id by any (shrine, place)
-- combination that is not one of the three audited pairs — a wrong owner, a
-- swapped pair, or a second Shrine claiming an already-bound target.

SELECT
    '3.1 target_place_ref_claims' AS section,
    s.id AS shrine_id,
    s.name_jp,
    s.place_ref_id,
    (
        (s.id = 21 AND s.place_ref_id = 'ChIJX19mq8nxGGARsA2kP4gX90M')
     OR (s.id = 22 AND s.place_ref_id = 'ChIJl-MEepfxGGAR1Eo44p__GaE')
     OR (s.id = 49 AND s.place_ref_id = 'ChIJK11I4BGJGGAR5mZswigcu58')
    ) AS is_audited_pair
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
-- 0100 deleted shrine 101 / 103 / 104 and F-6B closed the runtime path that
-- could recreate them. Expected: 0 rows.
-- Any row => SHADOW_RECURRENCE and F6D_POST_VERIFIED = false.

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
-- 0114 must not have moved a single interaction log. Searched GLOBALLY by
-- the canonical predicate (user_id + action_type + metadata.ctx + exact
-- created_at) first, NOT scoped to a shrine — exactly as migration 0100's
-- reverse and the F-6C PRE do. Then the owner is compared.
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
-- SECTION 6 — MACHINE-READABLE POST SUMMARY
-- =====================================================================
-- Every individual metric is reported alongside the boolean, so a failure is
-- never hidden behind F6D_POST_VERIFIED alone.
--
-- F6D_POST_VERIFIED = true ONLY when every condition below holds. Fail closed.

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
        count(*) FILTER (
            WHERE (p.id = 21 AND p.place_ref_id = 'ChIJX19mq8nxGGARsA2kP4gX90M')
               OR (p.id = 22 AND p.place_ref_id = 'ChIJl-MEepfxGGAR1Eo44p__GaE')
               OR (p.id = 49 AND p.place_ref_id = 'ChIJK11I4BGJGGAR5mZswigcu58')
        ) AS expected_mapping_match_count,
        count(*) FILTER (WHERE p.place_ref_id IS NULL) AS primary_place_ref_null_count
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
    SELECT
        count(*) AS target_place_ref_claim_count,
        count(*) FILTER (
            WHERE NOT (
                (s.id = 21 AND s.place_ref_id = 'ChIJX19mq8nxGGARsA2kP4gX90M')
             OR (s.id = 22 AND s.place_ref_id = 'ChIJl-MEepfxGGAR1Eo44p__GaE')
             OR (s.id = 49 AND s.place_ref_id = 'ChIJK11I4BGJGGAR5mZswigcu58')
            )
        ) AS unexpected_claim_count
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
        ) AS migration_0113_applied,
        count(*) FILTER (
            WHERE m.name = '0114_f6d_explicit_place_ref_backfill'
        ) AS migration_0114_applied_rows,
        count(*) FILTER (
            WHERE m.name > '0114_f6d_explicit_place_ref_backfill'
        ) AS lexically_above_leaf_count,
        count(*) FILTER (
            WHERE (substring(m.name from '^[0-9]{4}'))::int > 114
        ) AS migration_number_above_leaf_count,
        count(*) FILTER (
            WHERE (substring(m.name from '^[0-9]{4}'))::int = 114
              AND m.name <> '0114_f6d_explicit_place_ref_backfill'
        ) AS unknown_same_number_sibling_count,
        count(*) FILTER (
            WHERE substring(m.name from '^[0-9]{4}') IS NULL
        ) AS migration_name_unparseable_count
    FROM django_migrations AS m
    WHERE m.app = 'temples'
),
latest_stats AS (
    SELECT
        (
            SELECT m.name
            FROM django_migrations AS m
            WHERE m.app = 'temples'
            ORDER BY (substring(m.name from '^[0-9]{4}'))::int DESC NULLS LAST,
                     m.name DESC
            LIMIT 1
        ) AS temples_latest_name
)
SELECT
    '6.1 F6D_POST_GATE_SUMMARY' AS section,
    114                                             AS expected_leaf_number,
    '0114_f6d_explicit_place_ref_backfill'          AS expected_leaf_name,
    ls.temples_latest_name                          AS temples_latest_name,
    (ls2.migration_0114_applied_rows = 1)           AS migration_0114_applied,
    (
        ls.temples_latest_name = '0114_f6d_explicit_place_ref_backfill'
    )                                               AS production_temples_latest_is_0114,
    (ls2.migration_0100_applied = 1)                AS migration_0100_applied,
    (ls2.migration_0113_applied = 1)                AS migration_0113_applied,
    ls2.lexically_above_leaf_count                  AS lexically_above_leaf_count,
    ls2.migration_number_above_leaf_count           AS migration_number_above_leaf_count,
    ls2.unknown_same_number_sibling_count           AS unknown_same_number_sibling_count,
    ls2.migration_name_unparseable_count            AS migration_name_unparseable_count,
    (
        ls2.lexically_above_leaf_count > 0
        OR ls2.migration_number_above_leaf_count > 0
        OR ls2.unknown_same_number_sibling_count > 0
        OR ls2.migration_name_unparseable_count > 0
    )                                               AS unknown_migration_branch_detected,
    ps.primary_count                                AS primary_count,
    ps.primary_identity_match_count                 AS primary_identity_match_count,
    ps.expected_mapping_match_count                 AS expected_mapping_match_count,
    ps.primary_place_ref_null_count                 AS primary_place_ref_null_count,
    ts.target_place_ref_count                       AS target_place_ref_count,
    cs.target_place_ref_claim_count                 AS target_place_ref_claim_count,
    cs.unexpected_claim_count                       AS unexpected_claim_count,
    sh.shadow_count                                 AS shadow_count,
    (es.event_a_count + es.event_b_count)           AS audited_event_exact_count,
    (es.event_a_wrong_owner + es.event_b_wrong_owner) AS audited_event_wrong_owner_count,
    (
        ls2.migration_0114_applied_rows = 1
        AND ls.temples_latest_name = '0114_f6d_explicit_place_ref_backfill'
        AND ls2.migration_0100_applied = 1
        AND ls2.migration_0113_applied = 1
        AND ls2.lexically_above_leaf_count = 0
        AND ls2.migration_number_above_leaf_count = 0
        AND ls2.unknown_same_number_sibling_count = 0
        AND ls2.migration_name_unparseable_count = 0
        AND ps.primary_count = 3
        AND ps.primary_identity_match_count = 3
        AND ps.expected_mapping_match_count = 3
        AND ps.primary_place_ref_null_count = 0
        AND ts.target_place_ref_count = 3
        AND cs.target_place_ref_claim_count = 3
        AND cs.unexpected_claim_count = 0
        AND sh.shadow_count = 0
        AND es.event_a_count = 1
        AND es.event_b_count = 1
        AND es.event_a_wrong_owner = 0
        AND es.event_b_wrong_owner = 0
    )                                               AS f6d_post_verified
FROM primary_stats AS ps
CROSS JOIN target_stats AS ts
CROSS JOIN claim_stats AS cs
CROSS JOIN shadow_stats AS sh
CROSS JOIN event_stats AS es
CROSS JOIN ledger_stats AS ls2
CROSS JOIN latest_stats AS ls;
