-- nsrc-000004 G8 condition #8: canonical GoriyakuTag master remains unchanged.
-- SELECT-only. Execute through scripts/migration_safety/readonly_query.sh.

SELECT
  COUNT(*) AS goriyaku_tag_total,
  MIN(id) AS goriyaku_tag_min_id,
  MAX(id) AS goriyaku_tag_max_id,
  COUNT(DISTINCT id) AS goriyaku_tag_distinct_ids
FROM temples_goriyakutag;
