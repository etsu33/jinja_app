-- SELECT-only. Safe to run against Production.
-- Run after applying migrations. Compare every result against the values
-- recorded by pre_migration_snapshot.sql.

-- 1. Confirm the target migrations are now applied.
SELECT app, name, applied FROM django_migrations
WHERE (app = 'users' AND name = '0006_userprofile_birth_profile_fields')
   OR (app = 'temples' AND name = '0093_shrine_knowledge_model_foundation');
-- Expected: 2 rows.

-- 2. UserProfile's 4 new columns must now exist.
SELECT column_name FROM information_schema.columns
WHERE table_name = 'users_userprofile'
AND column_name IN ('birthday', 'birth_time', 'birth_place', 'worship_style');
-- Expected: 4 rows.

-- 3. Knowledge tables + M2M relation tables must now exist.
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'temples_shrineknowledgesource', 'temples_shrinedeity', 'temples_shrinehistory',
  'temples_shrinedeity_sources', 'temples_shrinehistory_sources'
);
-- Expected: 5 rows.

-- 4. Aggregate row counts must be unchanged from the pre-migration snapshot.
SELECT
  (SELECT COUNT(*) FROM auth_user) AS auth_user_count,
  (SELECT COUNT(*) FROM users_userprofile) AS userprofile_count,
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_count,
  (SELECT COUNT(*) FROM favorites_favorite) AS favorite_count,
  (SELECT COUNT(*) FROM temples_visit) AS visit_count,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags) AS shrine_goriyaku_relation_count;

-- 5. New Knowledge tables should be empty (no import has happened yet).
SELECT
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_count,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_count,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_count;
-- Expected: all 0 (Knowledge import is a separate, later gate).
