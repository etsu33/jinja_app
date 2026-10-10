-- nsrc-000002 G7 post-Knowledge Production verification
-- SELECT-only. No credential / connection-target output. No Production numeric PK is referenced.
-- Expected final delta from the frozen pre-state:
--   Shrine +1 / Source +(1 - accepted_source_count) / Deity +0 / History +1 / SourceFact +0
-- The FROZEN_PRE_STATE block must hold the same values as nsrc_000002_g7_pre_base_guard.sql.

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total;

WITH target AS (
  SELECT id FROM temples_shrine
  WHERE name_jp = '青澤神社' AND address = '新潟県糸魚川市大字青海2696番地'
)
SELECT
  (SELECT COUNT(*) FROM target) AS target_shrine,
  (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) AS target_deity,
  (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) AS target_history,
  (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) AS target_source_fact,
  (SELECT COUNT(*) FROM temples_shrinehistory_sources hs JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id JOIN target t ON t.id = h.shrine_id) AS history_source_relations,
  (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id
     WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) AS sourceless_history,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS target_goriyaku_tag_links,
  (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS target_goriyaku_assignments;

SELECT
  h.history_type,
  h.title,
  h.period_text,
  h.event_date,
  h.verification_status,
  h.confidence,
  src.source_type,
  src.url,
  src.publisher,
  src.verification_status AS source_verification_status,
  src.confidence AS source_confidence,
  src.language AS source_language
FROM temples_shrinehistory h
JOIN temples_shrine s ON s.id = h.shrine_id
JOIN temples_shrinehistory_sources hs ON hs.shrinehistory_id = h.id
JOIN temples_shrineknowledgesource src ON src.id = hs.shrineknowledgesource_id
WHERE s.name_jp = '青澤神社'
  AND s.address = '新潟県糸魚川市大字青海2696番地'
ORDER BY h.title, src.url;

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
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total + (1 - f.accepted_source_count)
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total + 1
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.00763484) < 0.00000001
          AND abs(longitude - 137.79024297) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) = 1
  AND (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id
        WHERE h.history_type = 'regional_context'
          AND h.title = '青沢神社の春季祭礼'
          AND h.period_text = '毎年4月第3日曜日'
          AND h.event_date IS NULL
          AND h.verification_status = 'source_confirmed'
          AND h.confidence = 'high') = 1
  AND (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id) = 1
  AND (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        JOIN compatible_source cs ON cs.id = hs.shrineknowledgesource_id) = 1
  AND (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) = 0
  AND (SELECT COUNT(*) FROM accepted_source) = 1
  AND (SELECT COUNT(*) FROM compatible_source) = 1
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS g7_post_knowledge_verification_pass
FROM frozen f;
