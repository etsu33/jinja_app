-- nsrc-000004 G7 Production Import Gate — read-only preflight
-- SELECT-only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.

SELECT
  current_database() IS NOT NULL AS database_identity_available,
  current_user IS NOT NULL AS database_user_available,
  current_setting('server_version') IS NOT NULL AS server_version_available;

SELECT
  COALESCE(MAX(name), '') AS latest_temples_migration
FROM django_migrations
WHERE app = 'temples';

SELECT
  EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'temples'
      AND name = '0120_shrine_source_fact_foundation'
  ) AS temples_0120_applied;

SELECT
  to_regclass('public.temples_shrine') IS NOT NULL AS shrine_table_exists,
  to_regclass('public.temples_shrineknowledgesource') IS NOT NULL AS source_table_exists,
  to_regclass('public.temples_shrinedeity') IS NOT NULL AS deity_table_exists,
  to_regclass('public.temples_shrinehistory') IS NOT NULL AS history_table_exists,
  to_regclass('public.temples_shrinesourcefact') IS NOT NULL AS source_fact_table_exists;

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total;

SELECT
  COUNT(*) FILTER (
    WHERE name_jp = '青海神社'
      AND address = '新潟県加茂市大字加茂字宮山229番地'
  ) AS target_exact_count,
  COUNT(*) FILTER (
    WHERE name_jp = '青海神社'
  ) AS same_name_count
FROM temples_shrine;

SELECT
  id,
  name_jp,
  address,
  latitude,
  longitude,
  place_ref_id,
  COALESCE(goriyaku, '') AS goriyaku
FROM temples_shrine
WHERE name_jp = '青海神社'
ORDER BY id;

SELECT
  s.id,
  s.source_type,
  s.title,
  s.publisher,
  s.url,
  s.verification_status,
  s.confidence,
  s.language,
  s.bibliography
FROM temples_shrineknowledgesource s
WHERE s.source_type = 'shrine_official'
  AND (
    lower(s.url) LIKE '%aomi-jinjya.or.jp/history/gosaisin.html%'
    OR lower(s.url) LIKE '%aomi-jinjya.or.jp/history/yuisyo.html%'
    OR lower(s.url) LIKE '%aomi-jinjya.or.jp/gokitou/syurui.html%'
  )
ORDER BY s.id;

SELECT
  d.id,
  d.shrine_id,
  d.display_name,
  d.role,
  d.verification_status,
  d.confidence
FROM temples_shrinedeity d
JOIN temples_shrine s ON s.id = d.shrine_id
WHERE s.name_jp = '青海神社'
  AND s.address = '新潟県加茂市大字加茂字宮山229番地'
ORDER BY d.id;

SELECT
  h.id,
  h.shrine_id,
  h.history_type,
  h.title,
  h.verification_status,
  h.confidence
FROM temples_shrinehistory h
JOIN temples_shrine s ON s.id = h.shrine_id
WHERE s.name_jp = '青海神社'
  AND s.address = '新潟県加茂市大字加茂字宮山229番地'
ORDER BY h.id;

SELECT
  sf.id,
  sf.shrine_id,
  sf.stable_key,
  sf.source_attested_wording,
  sf.evidence_characterization,
  sf.verification_status,
  sf.confidence
FROM temples_shrinesourcefact sf
WHERE sf.stable_key IN (
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
)
ORDER BY sf.stable_key;

SELECT
  COUNT(*) AS target_goriyaku_tag_links
FROM temples_shrine_goriyaku_tags gt
JOIN temples_shrine s ON s.id = gt.shrine_id
WHERE s.name_jp = '青海神社'
  AND s.address = '新潟県加茂市大字加茂字宮山229番地';
