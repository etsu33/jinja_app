-- nsrc-000002 青澤神社 G7 Production Import Gate — read-only preflight
-- SELECT-only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.
--
-- Accepted Source identity (importer: source_type + normalize_source_url()):
--   source_type = government
--   normalized  = https://matsuri.geo-itoigawa.com/calendar/m04
-- The SQL match below lower-cases the whole URL, drops a fragment and trailing '/',
-- and accepts the explicit default port. It is a superset of the importer's
-- normalization (the importer keeps path case), so it cannot miss a reusable row.

SELECT
  current_database() IS NOT NULL AS database_identity_available,
  current_user IS NOT NULL AS database_user_available,
  current_setting('server_version') IS NOT NULL AS server_version_available;

SELECT
  current_setting('server_version') AS server_version,
  current_setting('server_version_num') AS server_version_num;

SELECT
  COALESCE(MAX(name), '') AS latest_temples_migration
FROM django_migrations
WHERE app = 'temples';

SELECT
  to_regclass('public.temples_shrine') IS NOT NULL AS shrine_table_exists,
  to_regclass('public.temples_shrineknowledgesource') IS NOT NULL AS source_table_exists,
  to_regclass('public.temples_shrinedeity') IS NOT NULL AS deity_table_exists,
  to_regclass('public.temples_shrinehistory') IS NOT NULL AS history_table_exists,
  to_regclass('public.temples_shrinehistory_sources') IS NOT NULL AS history_sources_table_exists,
  to_regclass('public.temples_shrinesourcefact') IS NOT NULL AS source_fact_table_exists,
  to_regclass('public.temples_shrine_goriyaku_tags') IS NOT NULL AS goriyaku_tags_table_exists,
  to_regclass('public.temples_shrinegoriyakuassignment') IS NOT NULL AS goriyaku_assignment_table_exists;

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total;

SELECT
  COUNT(*) FILTER (
    WHERE name_jp = '青澤神社'
      AND address = '新潟県糸魚川市大字青海2696番地'
  ) AS target_exact_count,
  COUNT(*) FILTER (WHERE name_jp = '青澤神社') AS same_name_aosawa_kyuji_count,
  COUNT(*) FILTER (WHERE name_jp = '青沢神社') AS same_name_aosawa_shinji_count,
  COUNT(*) FILTER (WHERE address = '新潟県糸魚川市大字青海2696番地') AS same_address_count
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
WHERE name_jp IN ('青澤神社', '青沢神社')
   OR address = '新潟県糸魚川市大字青海2696番地'
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
WHERE lower(s.url) LIKE '%matsuri.geo-itoigawa.com/calendar/m04%'
ORDER BY s.id;

SELECT
  COUNT(*) AS accepted_source_identity_count
FROM temples_shrineknowledgesource s
WHERE s.source_type = 'government'
  AND lower(rtrim(split_part(btrim(s.url), '#', 1), '/')) IN (
    'https://matsuri.geo-itoigawa.com/calendar/m04',
    'https://matsuri.geo-itoigawa.com:443/calendar/m04'
  );

SELECT
  COUNT(*) AS accepted_source_metadata_compatible_count
FROM temples_shrineknowledgesource s
WHERE s.source_type = 'government'
  AND lower(rtrim(split_part(btrim(s.url), '#', 1), '/')) IN (
    'https://matsuri.geo-itoigawa.com/calendar/m04',
    'https://matsuri.geo-itoigawa.com:443/calendar/m04'
  )
  AND btrim(COALESCE(s.publisher, '')) = '糸魚川市 / 糸魚川ジオパーク協議会'
  AND btrim(COALESCE(s.verification_status, '')) = 'source_confirmed'
  AND btrim(COALESCE(s.confidence, '')) = 'high'
  AND btrim(COALESCE(s.bibliography, '')) = ''
  AND btrim(COALESCE(s.language, '')) = 'ja';

SELECT
  d.id,
  d.shrine_id,
  d.display_name,
  d.role,
  d.verification_status,
  d.confidence
FROM temples_shrinedeity d
JOIN temples_shrine s ON s.id = d.shrine_id
WHERE s.name_jp = '青澤神社'
  AND s.address = '新潟県糸魚川市大字青海2696番地'
ORDER BY d.id;

SELECT
  h.id,
  h.shrine_id,
  h.history_type,
  h.title,
  h.period_text,
  h.event_date,
  h.verification_status,
  h.confidence
FROM temples_shrinehistory h
JOIN temples_shrine s ON s.id = h.shrine_id
WHERE s.name_jp = '青澤神社'
  AND s.address = '新潟県糸魚川市大字青海2696番地'
ORDER BY h.id;

SELECT
  hs.shrinehistory_id,
  hs.shrineknowledgesource_id,
  src.source_type,
  src.url,
  src.verification_status
FROM temples_shrinehistory_sources hs
JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
JOIN temples_shrine s ON s.id = h.shrine_id
JOIN temples_shrineknowledgesource src ON src.id = hs.shrineknowledgesource_id
WHERE s.name_jp = '青澤神社'
  AND s.address = '新潟県糸魚川市大字青海2696番地'
ORDER BY hs.shrinehistory_id, hs.shrineknowledgesource_id;

SELECT
  sf.id,
  sf.shrine_id,
  sf.stable_key,
  sf.verification_status,
  sf.confidence
FROM temples_shrinesourcefact sf
JOIN temples_shrine s ON s.id = sf.shrine_id
WHERE s.name_jp = '青澤神社'
  AND s.address = '新潟県糸魚川市大字青海2696番地'
ORDER BY sf.id;

SELECT
  (SELECT COUNT(*)
     FROM temples_shrine_goriyaku_tags gt
     JOIN temples_shrine s ON s.id = gt.shrine_id
    WHERE s.name_jp = '青澤神社'
      AND s.address = '新潟県糸魚川市大字青海2696番地') AS target_goriyaku_tag_links,
  (SELECT COUNT(*)
     FROM temples_shrinegoriyakuassignment ga
     JOIN temples_shrine s ON s.id = ga.shrine_id
    WHERE s.name_jp = '青澤神社'
      AND s.address = '新潟県糸魚川市大字青海2696番地') AS target_goriyaku_assignments;
