-- NIIGATA-001-VPG001 G8 condition #8: canonical GoriyakuTag master current-state.
-- Cohort: nsrc-000021 / nsrc-000022 / nsrc-000024 / nsrc-000025 (nsrc-000023 excluded).
-- SELECT-only. Execute through scripts/migration_safety/readonly_query.sh.
-- Expected canonical state: 39 / 1 / 39 / 39.

SELECT
  COUNT(*) AS goriyaku_tag_total,
  MIN(id) AS goriyaku_tag_min_id,
  MAX(id) AS goriyaku_tag_max_id,
  COUNT(DISTINCT id) AS goriyaku_tag_distinct_ids
FROM temples_goriyakutag;
