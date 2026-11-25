-- SELECT-only. Safe to run against Production.
-- Run this immediately before taking a manual backup / applying migrations.
-- Record every result (and the time you ran this) in the execution gate doc.

-- 1. Confirm the target migrations are not already applied.
SELECT
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'users' AND name = '0006_userprofile_birth_profile_fields'
  ) AS users_0006_applied,
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples' AND name = '0093_shrine_knowledge_model_foundation'
  ) AS temples_0093_applied;
-- Expected: both false. If either is true, STOP — the known state has
-- changed since the last audit; do not proceed on stale assumptions.

-- 2. Aggregate row counts (no personal data, counts only).
SELECT
  (SELECT COUNT(*) FROM auth_user) AS auth_user_count,
  (SELECT COUNT(*) FROM users_userprofile) AS userprofile_count,
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_count,
  (SELECT COUNT(*) FROM favorites_favorite) AS favorite_count,
  (SELECT COUNT(*) FROM temples_visit) AS visit_count,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags) AS shrine_goriyaku_relation_count;

-- 3. Knowledge tables must not exist yet (temples 0093 not applied).
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'temples_shrineknowledgesource',
  'temples_shrinedeity',
  'temples_shrinehistory',
  'temples_shrinedeity_sources',
  'temples_shrinehistory_sources'
);
-- Expected: 0 rows.

-- 4. UserProfile's 4 new columns must not exist yet (users 0006 not applied).
SELECT column_name FROM information_schema.columns
WHERE table_name = 'users_userprofile'
AND column_name IN ('birthday', 'birth_time', 'birth_place', 'worship_style');
-- Expected: 0 rows. If any exist, this is a migration-history/schema
-- mismatch — classify separately, do not treat as a normal pending state.

-- 5. Record wall-clock time of this snapshot.
SELECT now() AS snapshot_taken_at;
