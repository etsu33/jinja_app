-- nsrc-000004 G7 post-Knowledge Production verification
-- SELECT-only. No credential / connection-target output.

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total;

WITH target AS (
  SELECT id
  FROM temples_shrine
  WHERE name_jp = '青海神社'
    AND address = '新潟県加茂市大字加茂字宮山229番地'
)
SELECT
  (SELECT COUNT(*) FROM target) AS target_shrine,
  (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) AS target_deity,
  (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) AS target_history,
  (SELECT COUNT(*) FROM temples_shrinesourcefact f JOIN target t ON t.id = f.shrine_id) AS target_source_fact,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS target_goriyaku_tag_links;

SELECT COUNT(*) AS target_sources
FROM temples_shrineknowledgesource
WHERE source_type = 'shrine_official'
  AND (
    lower(url) LIKE '%aomi-jinjya.or.jp/history/gosaisin.html%'
    OR lower(url) LIKE '%aomi-jinjya.or.jp/history/yuisyo.html%'
    OR lower(url) LIKE '%aomi-jinjya.or.jp/gokitou/syurui.html%'
  );

WITH target AS (
  SELECT id
  FROM temples_shrine
  WHERE name_jp = '青海神社'
    AND address = '新潟県加茂市大字加茂字宮山229番地'
)
SELECT
  (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id WHERE NOT EXISTS (SELECT 1 FROM temples_shrinedeity_sources ds WHERE ds.shrinedeity_id = d.id)) AS sourceless_deity,
  (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) AS sourceless_history,
  (SELECT COUNT(*) FROM temples_shrinesourcefact f JOIN target t ON t.id = f.shrine_id WHERE NOT EXISTS (SELECT 1 FROM temples_shrinesourcefact_sources fs WHERE fs.shrinesourcefact_id = f.id)) AS sourceless_source_fact;

WITH target AS (
  SELECT id
  FROM temples_shrine
  WHERE name_jp = '青海神社'
    AND address = '新潟県加茂市大字加茂字宮山229番地'
)
SELECT
  (SELECT COUNT(*) FROM temples_shrinedeity_sources ds JOIN temples_shrinedeity d ON d.id = ds.shrinedeity_id JOIN target t ON t.id = d.shrine_id) AS deity_source_relations,
  (SELECT COUNT(*) FROM temples_shrinehistory_sources hs JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id JOIN target t ON t.id = h.shrine_id) AS history_source_relations,
  (SELECT COUNT(*) FROM temples_shrinesourcefact_sources fs JOIN temples_shrinesourcefact f ON f.id = fs.shrinesourcefact_id JOIN target t ON t.id = f.shrine_id) AS source_fact_source_relations;

SELECT
  COUNT(*) AS stable_key_count,
  COUNT(DISTINCT stable_key) AS stable_key_unique_count
FROM temples_shrinesourcefact
WHERE stable_key IN (
  'aomi_jinja_kamo__prayer__kanai_anzen',
  'aomi_jinja_kamo__prayer__kosazuke_kigan',
  'aomi_jinja_kamo__prayer__anzan_kigan',
  'aomi_jinja_kamo__prayer__kotsu_anzen',
  'aomi_jinja_kamo__prayer__yakubarai',
  'aomi_jinja_kamo__prayer__hoi_barai',
  'aomi_jinja_kamo__prayer__byoki_heiyu_kigan',
  'aomi_jinja_kamo__prayer__mi_no_anzen_kigan',
  'aomi_jinja_kamo__prayer__gokaku_kigan',
  'aomi_jinja_kamo__prayer__shobai_hanjo',
  'aomi_jinja_kamo__prayer__hissho_kigan'
);
