-- SELECT-only. Safe to run against Production. Never write, never DDL.
--
-- Preflight for applying `temples` migrations 0095 -> 0096 -> 0097 -> 0098
-- IN SEQUENCE. This file is scoped to exactly those four migrations and is
-- SEPARATE from `pre_migration_snapshot.sql` / `post_migration_verification.sql`,
-- which are the historical runbook for `users 0006` / `temples 0090-0093` and
-- are NOT reused here (they check a different, earlier migration boundary and
-- must not be edited or repurposed for this one).
--
-- Each section below derives its precondition directly from that migration's
-- own `forward` implementation and its own test suite -- nothing here is
-- guessed. Where a section reports "expected", that is the exact condition
-- `forward` itself checks before mutating anything; a mismatch does not mean
-- the SQL is wrong, it means the migration will either no-op (0095 / 0096,
-- which are best-effort) or raise and change nothing (0097 / 0098, which are
-- fail-closed) -- a human decides whether that outcome is acceptable before
-- running `migrate`.
--
-- How to run (never paste a credential into chat; see README.md "Credential
-- Bridge"):
--   scripts/migration_safety/readonly_query.sh \
--     ~/.config/kami-musubi/production-db.env DATABASE_URL \
--     scripts/migration_safety/sql/temples_0095_0098_preflight.sql
--
-- Run this once immediately before applying 0095-0098, and re-run it again
-- immediately before the actual `migrate` command if any time has passed --
-- treat any change since the last run as a reason to stop and re-derive.


-- ============================================================================
-- SECTION 0 -- Migration ledger state
-- ============================================================================

-- 0-a. Confirm temples 0094 is applied and 0095/0096/0097/0098 are NOT.
SELECT
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples' AND name = '0094_fix_shrine_70_coordinates'
  ) AS temples_0094_applied_expected_true,
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples' AND name = '0095_batch17_recommendation_evidence_activation'
  ) AS temples_0095_applied_expected_false,
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples' AND name = '0096_source_backfill_id10_id22'
  ) AS temples_0096_applied_expected_false,
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples' AND name = '0097_p5_id21_id22_tag_reconciliation'
  ) AS temples_0097_applied_expected_false,
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples' AND name = '0098_remove_stray_test_source_id1'
  ) AS temples_0098_applied_expected_false;
-- Expected: temples_0094_applied_expected_true = true; the other four = false.
-- If ANY of 0095-0098 is already true, STOP -- do not run the rest of this
-- file's assumptions forward; the chain has moved since this preflight was
-- written and preconditions must be re-derived against the real state.

-- 0-b. STOP check: any `temples` migration numbered higher than 0094 applied
-- that this preflight does not already name above? (Defensive -- should
-- return 0 rows given 0-a; if it returns rows, a human must look at exactly
-- which migration(s) and re-derive this file's assumptions before proceeding.)
SELECT name, applied
FROM django_migrations
WHERE app = 'temples'
  AND SUBSTRING(name FROM '^[0-9]{4}')::int > 94
ORDER BY name;
-- Expected: 0 rows.

-- 0-c. Full recent `temples` ledger tail, for human eyeballing / audit trail.
SELECT name, applied
FROM django_migrations
WHERE app = 'temples'
ORDER BY applied DESC
LIMIT 10;


-- ============================================================================
-- SECTION 1 -- 0095_batch17_recommendation_evidence_activation
--
-- Forward activates a shrine ONLY when ALL of: (a) identity matches exactly
-- (pk + name_jp + address); (b) `goriyaku` is empty; (c) it has zero
-- `goriyaku_tags` relations; (d) every canonical PASS label for that shrine
-- already exists in the GoriyakuTag master by exact name. Any deviation
-- makes that shrine a SILENT NO-OP -- 0095 is best-effort, not fail-closed.
-- This section exists so a human can see in advance which of shrine 107 /
-- 108 will actually activate versus silently no-op.
-- ============================================================================

-- 1-a. Shrine identity + goriyaku emptiness (107 建部大社).
SELECT
  id, name_jp, address, place_ref_id, goriyaku,
  (name_jp = '建部大社' AND address = '滋賀県大津市神領1-16-1') AS identity_matches_expected_true,
  (COALESCE(goriyaku, '') = '') AS goriyaku_is_empty_expected_true
FROM temples_shrine
WHERE id = 107;
-- Expected: 1 row, both boolean columns true.

-- 1-b. Shrine identity + goriyaku emptiness (108 波上宮).
SELECT
  id, name_jp, address, place_ref_id, goriyaku,
  (name_jp = '波上宮' AND address = '沖縄県那覇市若狭1-25-11') AS identity_matches_expected_true,
  (COALESCE(goriyaku, '') = '') AS goriyaku_is_empty_expected_true
FROM temples_shrine
WHERE id = 108;
-- Expected: 1 row, both boolean columns true.

-- 1-c. Existing goriyaku_tags relation count per shrine (forward requires 0
-- for a shrine to be eligible for activation).
SELECT
  s.id AS shrine_id,
  COUNT(g.goriyakutag_id) AS existing_goriyaku_tag_count,
  (COUNT(g.goriyakutag_id) = 0) AS zero_relations_expected_true
FROM temples_shrine s
LEFT JOIN temples_shrine_goriyaku_tags g ON g.shrine_id = s.id
WHERE s.id IN (107, 108)
GROUP BY s.id
ORDER BY s.id;
-- Expected: existing_goriyaku_tag_count = 0 for both rows.

-- 1-d. Canonical PASS labels for shrine 107 already exist in the GoriyakuTag
-- master (forward NEVER creates a tag; a missing label makes this shrine a
-- no-op).
SELECT
  107 AS shrine_id, x.label, (t.id IS NOT NULL) AS label_exists_expected_true
FROM (VALUES
  ('開運'), ('厄除け'), ('出世運'), ('勝運'), ('縁結び'), ('商売繁盛'), ('家内安全'), ('病気平癒')
) AS x(label)
LEFT JOIN temples_goriyakutag t ON t.name = x.label
ORDER BY x.label;
-- Expected: 8 rows, label_exists_expected_true = true for all.

-- 1-e. Canonical PASS labels for shrine 108 already exist in the GoriyakuTag
-- master.
SELECT
  108 AS shrine_id, x.label, (t.id IS NOT NULL) AS label_exists_expected_true
FROM (VALUES
  ('海上安全'), ('家内安全'), ('商売繁盛'), ('厄除け'), ('安産'), ('交通安全'), ('合格祈願'), ('心願成就')
) AS x(label)
LEFT JOIN temples_goriyakutag t ON t.name = x.label
ORDER BY x.label;
-- Expected: 8 rows, label_exists_expected_true = true for all.


-- ============================================================================
-- SECTION 2 -- 0096_source_backfill_id10_id22
--
-- Forward, per shrine independently: if identity matches AND at least one of
-- that shrine's target ShrineHistory rows is present (matched by shrine_id +
-- history_type + title -- never by pk, which drifts between Local and
-- Production), it get-or-creates a specific Source (matched by url +
-- source_type; reused as-is if already present, created fresh otherwise) and
-- adds only the history<->Source relations that do not already exist. No
-- identity/history match for a shrine makes that shrine a silent no-op.
-- ============================================================================

-- 2-a. Shrine identity (10 鶴岡八幡宮).
SELECT id, name_jp, place_ref_id,
       (name_jp = '鶴岡八幡宮' AND place_ref_id IS NULL) AS identity_matches_expected_true
FROM temples_shrine WHERE id = 10;

-- 2-b. Shrine identity (22 給田六所神社).
SELECT id, name_jp, place_ref_id,
       (name_jp = '給田六所神社' AND place_ref_id IS NULL) AS identity_matches_expected_true
FROM temples_shrine WHERE id = 22;

-- 2-c. Target ShrineHistory rows (matched by shrine_id + history_type + title
-- only; pk is never used by 0096).
SELECT id, shrine_id, history_type, title
FROM temples_shrinehistory
WHERE (shrine_id, history_type, title) IN (
  (10, 'founding', '由比若宮の勧請'),
  (10, 'historical_event', '現在地への遷座'),
  (22, 'founding', '武蔵総社六所宮よりの分霊勧請')
)
ORDER BY shrine_id, history_type;
-- Expected: 3 rows (one per tuple). 0 matching rows for shrine 10 makes
-- shrine 10 a no-op (`if not histories: continue`); independently for
-- shrine 22's single expected row.

-- 2-d. Target Source existing state for shrine 10 (matched by url +
-- source_type -- never by title/pk). Presence means forward REUSES this row
-- (no new row created); absence means forward CREATEs it.
SELECT
  id, source_type, title, url, note,
  (note LIKE '[temples.0096:auto-created]%'
   OR note LIKE '%' || E'\n\n' || '[temples.0096:auto-created]%') AS already_carries_0096_marker
FROM temples_shrineknowledgesource
WHERE url = 'https://online.bunka.go.jp/heritages/detail/160978'
  AND source_type = 'cultural_property';
-- Expected: 0 or 1 row. If 1 row already carries the 0096 marker in `note`
-- while Section 0-a shows temples_0096_applied_expected_false = true (i.e.
-- 0096 is NOT recorded as applied), that is a drift signal -- STOP and
-- investigate before applying (an unrecorded prior run would make forward
-- reuse and re-tag a row it does not know it already touched).

-- 2-e. Target Source existing state for shrine 22 (same interpretation as
-- 2-d).
SELECT
  id, source_type, title, url, note,
  (note LIKE '[temples.0096:auto-created]%'
   OR note LIKE '%' || E'\n\n' || '[temples.0096:auto-created]%') AS already_carries_0096_marker
FROM temples_shrineknowledgesource
WHERE url = 'https://www.dentou-hasshin.bunka.go.jp/search/158.html'
  AND source_type = 'government';
-- Expected: 0 or 1 row, same interpretation as 2-d.

-- 2-f. Existing history<->Source relation state for the target histories
-- found in 2-c, against either target Source url from 2-d/2-e. Informational
-- only: this tells you whether forward would add 0, some, or all of the
-- links -- 0096 is idempotent per-link, so any of these outcomes is a normal,
-- safe result, not a precondition failure.
SELECT
  h.id AS history_id, h.shrine_id, h.history_type, h.title,
  EXISTS (
    SELECT 1 FROM temples_shrinehistory_sources hs
    JOIN temples_shrineknowledgesource s ON s.id = hs.shrineknowledgesource_id
    WHERE hs.shrinehistory_id = h.id
      AND s.url IN (
        'https://online.bunka.go.jp/heritages/detail/160978',
        'https://www.dentou-hasshin.bunka.go.jp/search/158.html'
      )
  ) AS already_cites_target_source
FROM temples_shrinehistory h
WHERE (h.shrine_id, h.history_type, h.title) IN (
  (10, 'founding', '由比若宮の勧請'),
  (10, 'historical_event', '現在地への遷座'),
  (22, 'founding', '武蔵総社六所宮よりの分霊勧請')
)
ORDER BY h.shrine_id, h.history_type;


-- ============================================================================
-- SECTION 3 -- 0097_p5_id21_id22_tag_reconciliation (STRICT_EXACT / fail-closed)
--
-- Forward validates ALL of the below for BOTH shrine 21 and shrine 22 BEFORE
-- mutating ANYTHING (validate-all-then-mutate-all across the whole target
-- list, not per-shrine). If any REQUIRED GoriyakuTag row or REQUIRED
-- relation is missing for either shrine, OR the OPTIONAL 地域安泰 tag row
-- exists without its relation to an identity-matched shrine, forward raises
-- PreconditionViolation and changes ZERO rows for either shrine. An identity
-- mismatch (3-a below) makes only that one shrine a no-op -- it is not a
-- fail-closed violation by itself.
-- ============================================================================

-- 3-a. Shrine identity (21 長太稲荷神社 / 22 給田六所神社).
SELECT id, name_jp, place_ref_id,
       (name_jp = '長太稲荷神社' AND place_ref_id IS NULL) AS identity_matches_expected_true
FROM temples_shrine WHERE id = 21;

SELECT id, name_jp, place_ref_id,
       (name_jp = '給田六所神社' AND place_ref_id IS NULL) AS identity_matches_expected_true
FROM temples_shrine WHERE id = 22;

-- 3-b. Required GoriyakuTag rows + required relation to their shrine. Every
-- row here must have BOTH boolean columns true, or forward raises
-- PreconditionViolation for the WHOLE migration (both shrines).
SELECT
  21 AS shrine_id, x.label,
  (t.id IS NOT NULL) AS tag_row_exists_expected_true,
  EXISTS (
    SELECT 1 FROM temples_shrine_goriyaku_tags g
    WHERE g.shrine_id = 21 AND g.goriyakutag_id = t.id
  ) AS relation_exists_expected_true
FROM (VALUES ('商売繁盛'), ('五穀豊穣')) AS x(label)
LEFT JOIN temples_goriyakutag t ON t.name = x.label
UNION ALL
SELECT
  22, x.label,
  (t.id IS NOT NULL),
  EXISTS (
    SELECT 1 FROM temples_shrine_goriyaku_tags g
    WHERE g.shrine_id = 22 AND g.goriyakutag_id = t.id
  )
FROM (VALUES ('家内安全')) AS x(label)
LEFT JOIN temples_goriyakutag t ON t.name = x.label
ORDER BY shrine_id, label;
-- Expected: 3 rows (21/商売繁盛, 21/五穀豊穣, 22/家内安全), both boolean
-- columns true on every row.

-- 3-c. Optional 地域安泰 tag row -- STRICT_EXACT 3-state contract:
--   (i)   row absent (chiiki_antai_tag_id IS NULL)               -> safe;
--         forward skips it for both shrines, never creates it.
--   (ii)  row present AND relation_exists_if_row_present = true
--         for a shrine                                           -> safe;
--         forward will remove that shrine's relation and reverse will
--         restore it exactly.
--   (iii) row present AND relation_exists_if_row_present = false
--         for EITHER shrine                                      -> forward
--         WILL raise PreconditionViolation for the WHOLE migration (this is
--         exactly the STRICT_EXACT gap closed by this session's fix to
--         0097 -- an existing tag row with no relation would otherwise let
--         reverse fabricate a relation that never existed pre-forward).
SELECT
  t.id AS chiiki_antai_tag_id,
  s.id AS shrine_id,
  s.name_jp,
  CASE WHEN t.id IS NULL THEN NULL ELSE EXISTS (
    SELECT 1 FROM temples_shrine_goriyaku_tags g
    WHERE g.shrine_id = s.id AND g.goriyakutag_id = t.id
  ) END AS relation_exists_if_row_present
FROM (SELECT id, name_jp FROM temples_shrine WHERE id IN (21, 22)) s
LEFT JOIN temples_goriyakutag t ON t.name = '地域安泰'
ORDER BY s.id;
-- Expected: EITHER chiiki_antai_tag_id IS NULL on both rows (case i), OR --
-- if chiiki_antai_tag_id IS NOT NULL -- relation_exists_if_row_present = true
-- on BOTH rows (case ii). If chiiki_antai_tag_id IS NOT NULL and
-- relation_exists_if_row_present = false for either shrine (case iii), STOP:
-- forward will raise PreconditionViolation and change nothing. Resolve the
-- drift (attach the missing relation, or remove the stray tag row) before
-- applying 0097.


-- ============================================================================
-- SECTION 4 -- 0098_remove_stray_test_source_id1 (P6_0098_PRESTATE_POLICY =
-- FAIL_CLOSED)
--
-- Forward's ONE clean no-op is total absence of a Shrine pk 1 row. Once
-- Shrine pk 1 exists, ALL of the following must hold or forward raises
-- RuntimeError('PRESTATE_MISMATCH') before any mutation -- there is no
-- partial-repair or "guess" path.
-- ============================================================================

-- 4-a. Shrine identity.
SELECT id, name_jp, place_ref_id,
       (name_jp = '明治神宮' AND place_ref_id IS NULL) AS identity_matches_expected_true
FROM temples_shrine WHERE id = 1;
-- Expected: 0 rows (the one clean no-op) OR exactly 1 row with
-- identity_matches_expected_true = true. A row present but not matching is
-- a guaranteed PRESTATE_MISMATCH.

-- 4-b. Target Source: exactly one row must match this full 5-field semantic
-- identity (never matched by pk -- Production pk 2, local dev pk 999004).
SELECT id, source_type, title, publisher, url, bibliography,
       verification_status, confidence, language
FROM temples_shrineknowledgesource
WHERE source_type = 'user_observation'
  AND title = 'テスト神社 境内案内板'
  AND publisher = 'テスト神社'
  AND url = ''
  AND bibliography = 'テスト神社境内案内板（2026-08-01現地確認）';
-- Expected (only meaningful if 4-a shows Shrine pk 1 present): exactly 1
-- row. 0 rows or more than 1 row -> forward raises PRESTATE_MISMATCH.

-- 4-c. Target ShrineDeity rows: exactly 明治天皇 and 昭憲皇太后 on
-- shrine_id=1, no missing / duplicate / extra.
SELECT id, display_name, shrine_id
FROM temples_shrinedeity
WHERE shrine_id = 1 AND display_name IN ('明治天皇', '昭憲皇太后')
ORDER BY display_name, id;
-- Expected: exactly 2 rows, one 明治天皇 and one 昭憲皇太后 (no duplicates).

-- 4-d. Both target deities must already cite the target Source identified
-- in 4-b (joined by the Source's semantic identity, so this still reports
-- correctly even if 4-b found 0 or >1 rows -- it will just show 0/ambiguous
-- relations).
SELECT
  d.display_name, d.id AS deity_id,
  EXISTS (
    SELECT 1 FROM temples_shrinedeity_sources ds
    JOIN temples_shrineknowledgesource s ON s.id = ds.shrineknowledgesource_id
    WHERE ds.shrinedeity_id = d.id
      AND s.source_type = 'user_observation'
      AND s.title = 'テスト神社 境内案内板'
      AND s.publisher = 'テスト神社'
      AND s.url = ''
      AND s.bibliography = 'テスト神社境内案内板（2026-08-01現地確認）'
  ) AS cites_target_source_expected_true
FROM temples_shrinedeity d
WHERE d.shrine_id = 1 AND d.display_name IN ('明治天皇', '昭憲皇太后')
ORDER BY d.display_name;
-- Expected: 2 rows, cites_target_source_expected_true = true for both.

-- 4-e. The target Source must be cited by EXACTLY those two deity relations
-- and by ZERO ShrineHistory relations -- otherwise it is not safely
-- deletable and forward raises PRESTATE_MISMATCH.
SELECT
  s.id AS source_id,
  (SELECT COUNT(*) FROM temples_shrinedeity_sources ds
   WHERE ds.shrineknowledgesource_id = s.id) AS deity_citer_count_expected_2,
  (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
   WHERE hs.shrineknowledgesource_id = s.id) AS history_citer_count_expected_0
FROM temples_shrineknowledgesource s
WHERE s.source_type = 'user_observation'
  AND s.title = 'テスト神社 境内案内板'
  AND s.publisher = 'テスト神社'
  AND s.url = ''
  AND s.bibliography = 'テスト神社境内案内板（2026-08-01現地確認）';
-- Expected: 0 or 1 row (per 4-b); when 1 row, deity_citer_count_expected_2 =
-- 2 AND history_citer_count_expected_0 = 0.


-- ============================================================================
-- SECTION 5 -- timestamp
-- ============================================================================

-- 5-a. Record wall-clock time of this preflight run.
SELECT now() AS preflight_run_at;
