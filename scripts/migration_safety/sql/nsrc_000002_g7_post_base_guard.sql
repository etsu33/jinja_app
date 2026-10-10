-- nsrc-000002 G7 post-Base / pre-Knowledge Production guard
-- SELECT-only; raises division-by-zero unless exactly the single target Base row was added.
-- Expected: Shrine = frozen + 1, every Knowledge aggregate unchanged, target Knowledge 0,
-- canonical coordinate within 1e-8, goriyaku '' and 0 goriyaku tag links / assignments.
-- The FROZEN_PRE_STATE block must hold the same values as nsrc_000002_g7_pre_base_guard.sql.
WITH frozen AS (
  -- FROZEN_PRE_STATE: every NULL below must be replaced with the value measured by
  -- nsrc_000002_g7_preflight.sql on Production (read-only) before this file is used.
  -- While any value is NULL the guard cannot return 1 and fails closed.
  SELECT
    NULL::bigint AS shrine_total,
    NULL::bigint AS source_total,
    NULL::bigint AS deity_total,
    NULL::bigint AS history_total,
    NULL::bigint AS source_fact_total,
    -- 0 = accepted Source absent (CLEAN_CREATE), 1 = exactly one metadata-compatible row present
    NULL::bigint AS accepted_source_count
),
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '青澤神社'
    AND address = '新潟県糸魚川市大字青海2696番地'
),
accepted_source AS (
  SELECT id, publisher, verification_status, confidence, bibliography, language
  FROM temples_shrineknowledgesource
  WHERE source_type = 'government'
    AND lower(rtrim(split_part(btrim(url), '#', 1), '/')) IN (
      'https://matsuri.geo-itoigawa.com/calendar/m04',
      'https://matsuri.geo-itoigawa.com:443/calendar/m04'
    )
),
compatible_source AS (
  SELECT id
  FROM accepted_source
  WHERE btrim(COALESCE(publisher, '')) = '糸魚川市 / 糸魚川ジオパーク協議会'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
)
SELECT 1 / CASE WHEN (
  (SELECT COUNT(*) FROM temples_shrine) = f.shrine_total + 1
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '青澤神社') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '青沢神社') = 0
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県糸魚川市大字青海2696番地') = 1
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.00763484) < 0.00000001
          AND abs(longitude - 137.79024297) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM accepted_source) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM compatible_source) = f.accepted_source_count
) THEN 1 ELSE 0 END AS g7_post_base_guard_pass
FROM frozen f;
