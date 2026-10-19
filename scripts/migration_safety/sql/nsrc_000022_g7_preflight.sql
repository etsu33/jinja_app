-- nsrc-000022 五十嵐神社 G7 Production Import Gate — read-only preflight
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.
--
-- Canonical target = exact (name_jp, address): 五十嵐神社 / 新潟県三条市大字飯田2283番地.
-- Frozen G1 same-name identities at other addresses: none recorded in G1 (G1 = NEW).
-- Same-name rows are diagnostics only and never identify the target.
--
-- Source identity is the importer's semantic identity only
-- (knowledge_seed.resolve_source_identity(): source_type + normalize_source_url()):
--   SANJO_CITY_IGARASHI_JINJA = government + https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html
-- Three separate concepts:
--   source_identity_count            exact importer identity (the only reusable rows)
--   source_metadata_compatible_count identity rows whose _SOURCE_REUSE_FIELDS match the seed
--   source_url_lookalike_count       broad diagnostic match; never reusable by itself
--
-- Repository payload maximum (not a Production delta): Shrine +1 / Source +1 max / Deity +1 /
-- History +0 / Citation +0 / SourceFact +0 / Collective +0 / goriyaku +0.
-- The citation table is counted for aggregate invariance; the seed (schema 1.0) has no citation.

SELECT
  current_database() IS NOT NULL AS database_identity_available,
  current_user IS NOT NULL AS database_user_available,
  current_setting('server_version') IS NOT NULL AS server_version_available;

SELECT
  current_setting('server_version') AS server_version,
  current_setting('server_version_num') AS server_version_num;

SELECT
  COALESCE(MAX(name), '') AS latest_temples_migration,
  COUNT(*) FILTER (WHERE name = '0121_shrine_fact_source_citation') = 1
    AS fact_source_citation_migration_applied
FROM django_migrations
WHERE app = 'temples';

SELECT
  to_regclass('public.temples_shrine') IS NOT NULL AS shrine_table_exists,
  to_regclass('public.temples_shrineknowledgesource') IS NOT NULL AS source_table_exists,
  to_regclass('public.temples_shrinedeity') IS NOT NULL AS deity_table_exists,
  to_regclass('public.temples_shrinedeity_sources') IS NOT NULL AS deity_sources_table_exists,
  to_regclass('public.temples_shrinehistory') IS NOT NULL AS history_table_exists,
  to_regclass('public.temples_shrinehistory_sources') IS NOT NULL AS history_sources_table_exists,
  to_regclass('public.temples_shrinefactsourcecitation') IS NOT NULL AS fact_source_citation_table_exists,
  to_regclass('public.temples_shrinesourcefact') IS NOT NULL AS source_fact_table_exists,
  to_regclass('public.temples_shrinedeitycollective') IS NOT NULL AS collective_table_exists,
  to_regclass('public.temples_shrine_goriyaku_tags') IS NOT NULL AS goriyaku_tags_table_exists,
  to_regclass('public.temples_shrinegoriyakuassignment') IS NOT NULL AS goriyaku_assignment_table_exists;

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) AS citation_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total,
  (SELECT COUNT(*) FROM temples_shrinedeitycollective) AS collective_total;

SELECT
  COUNT(*) FILTER (
    WHERE name_jp = '五十嵐神社'
      AND address = '新潟県三条市大字飯田2283番地'
  ) AS target_exact_count,
  COUNT(*) FILTER (WHERE name_jp = '五十嵐神社') AS same_name_count,
  COUNT(*) FILTER (WHERE name_jp = '五十嵐神社' AND address <> '新潟県三条市大字飯田2283番地') AS same_name_other_address_count,
  COUNT(*) FILTER (WHERE address = '新潟県三条市大字飯田2283番地') AS same_address_count,
  COUNT(*) FILTER (WHERE address = '新潟県三条市大字飯田2283番地' AND name_jp <> '五十嵐神社') AS same_address_other_name_count
FROM temples_shrine;

-- Diagnostics only: same-name rows at other addresses are other shrines, not the target.
SELECT
  id,
  name_jp,
  address,
  latitude,
  longitude,
  place_ref_id,
  COALESCE(goriyaku, '') AS goriyaku,
  (name_jp = '五十嵐神社' AND address = '新潟県三条市大字飯田2283番地') AS is_canonical_target
FROM temples_shrine
WHERE name_jp = '五十嵐神社'
   OR address = '新潟県三条市大字飯田2283番地'
ORDER BY id;

WITH
-- BEGIN nsrc_000022_source_identity
-- Byte-identical in every nsrc_000022_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000022_g7_source_identity_sql.py).
-- One Source (SANJO_CITY_IGARASHI_JINJA). Whether it already exists in Production is measured,
-- never assumed, and never matched approximately.
-- normalized_url reproduces knowledge_seed.normalize_source_url() exactly:
-- strip whitespace, drop TAB/CR/LF, lowercase scheme and hostname, drop userinfo,
-- drop default port (http 80 / https 443), drop fragment, ignore non-root trailing
-- '/', keep path case, keep query byte-for-byte, keep http and https distinct.
-- A URL the importer cannot parse (invalid port, bracketed host) yields NULL, so it
-- never counts as identity. Bracketed hosts are IP literals and cannot equal the target.
source_url_norm AS (
  SELECT
    s.id,
    s.source_type,
    s.title,
    s.publisher,
    s.url,
    s.verification_status,
    s.confidence,
    s.language,
    s.bibliography,
    CASE
      WHEN e.port_invalid_or_bracket THEN NULL
      WHEN e.stripped = '' THEN ''
      ELSE
        CASE WHEN b.scheme <> '' THEN b.scheme || ':' ELSE '' END
        || CASE
             WHEN e.netloc_norm <> ''
               OR (b.scheme <> '' AND b.scheme IN (
                     'ftp', 'http', 'gopher', 'nntp', 'telnet', 'imap', 'wais', 'file',
                     'mms', 'https', 'shttp', 'snews', 'prospero', 'rtsp', 'rtsps',
                     'rtspu', 'rsync', 'svn', 'svn+ssh', 'sftp', 'nfs', 'git',
                     'git+ssh', 'ws', 'wss', 'itms-services')
                   AND left(e.path_norm, 2) <> '//')
             THEN '//' || e.netloc_norm
                  || CASE WHEN e.path_norm <> '' AND left(e.path_norm, 1) <> '/'
                          THEN '/' || e.path_norm ELSE e.path_norm END
             ELSE e.path_norm
           END
        || CASE WHEN d.query <> '' THEN '?' || d.query ELSE '' END
    END AS normalized_url
  FROM temples_shrineknowledgesource s
  CROSS JOIN LATERAL (
    -- str.strip() (Python isspace set), then urlsplit(): lstrip C0 controls/space,
    -- then remove TAB / CR / LF anywhere.
    SELECT
      regexp_replace(COALESCE(s.url, ''),
        '^[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$',
        '', 'g') AS stripped
  ) a0
  CROSS JOIN LATERAL (
    SELECT
      a0.stripped,
      regexp_replace(regexp_replace(a0.stripped, '^[\u0001-\u0020]+', ''), '[\t\r\n]', '', 'g') AS trimmed
  ) a
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN lower(substring(a.trimmed FROM '^([A-Za-z][A-Za-z0-9+.-]*):'))
           ELSE '' END AS scheme,
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN substring(a.trimmed FROM '^[A-Za-z][A-Za-z0-9+.-]*:(.*)$')
           ELSE a.trimmed END AS rest
  ) b
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//([^/?#]*)') ELSE '' END AS netloc,
      split_part(CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//[^/?#]*(.*)$')
                      ELSE b.rest END, '#', 1) AS before_fragment
  ) c
  CROSS JOIN LATERAL (
    SELECT
      split_part(c.before_fragment, '?', 1) AS path,
      CASE WHEN position('?' IN c.before_fragment) > 0
           THEN substring(c.before_fragment FROM position('?' IN c.before_fragment) + 1)
           ELSE '' END AS query,
      regexp_replace(c.netloc, '^.*@', '') AS hostinfo
  ) d
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN position(':' IN d.hostinfo) > 0
           THEN substring(d.hostinfo FROM position(':' IN d.hostinfo) + 1)
           ELSE '' END AS port_raw,
      lower(split_part(d.hostinfo, ':', 1)) AS hostname
  ) p
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN p.port_raw = '' THEN NULL
           WHEN p.port_raw ~ '^[0-9]+$' AND length(ltrim(p.port_raw, '0')) <= 5
                AND COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint <= 65535
             THEN COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint
           ELSE NULL END AS port
  ) q
  CROSS JOIN LATERAL (
    SELECT
      a.stripped,
      (p.port_raw <> '' AND q.port IS NULL) OR c.netloc ~ '[][]' AS port_invalid_or_bracket,
      p.hostname
        || CASE WHEN q.port IS NOT NULL
                 AND NOT ((b.scheme = 'http' AND q.port = 80) OR (b.scheme = 'https' AND q.port = 443))
                THEN ':' || q.port::text ELSE '' END AS netloc_norm,
      CASE WHEN d.path IN ('', '/') THEN '/' ELSE rtrim(d.path, '/') END AS path_norm
  ) e
),
-- Source importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '三条市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.sanjo.niigata.jp%' AND lower(url) LIKE '%jinja_jisha_joshi/2289%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.sanjo.niigata.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%jinja_jisha_joshi/2289%')
)
-- END nsrc_000022_source_identity
SELECT
  'SANJO_CITY_IGARASHI_JINJA' AS source_key,
  l.id,
  l.source_type,
  l.title,
  l.publisher,
  l.url,
  l.verification_status,
  l.confidence,
  l.language,
  l.bibliography,
  l.normalized_url,
  EXISTS (SELECT 1 FROM source_identity i WHERE i.id = l.id) AS is_source_identity,
  EXISTS (SELECT 1 FROM source_metadata_compatible m WHERE m.id = l.id) AS is_metadata_compatible
FROM source_url_lookalike l
ORDER BY l.id;

WITH
-- BEGIN nsrc_000022_source_identity
-- Byte-identical in every nsrc_000022_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000022_g7_source_identity_sql.py).
-- One Source (SANJO_CITY_IGARASHI_JINJA). Whether it already exists in Production is measured,
-- never assumed, and never matched approximately.
-- normalized_url reproduces knowledge_seed.normalize_source_url() exactly:
-- strip whitespace, drop TAB/CR/LF, lowercase scheme and hostname, drop userinfo,
-- drop default port (http 80 / https 443), drop fragment, ignore non-root trailing
-- '/', keep path case, keep query byte-for-byte, keep http and https distinct.
-- A URL the importer cannot parse (invalid port, bracketed host) yields NULL, so it
-- never counts as identity. Bracketed hosts are IP literals and cannot equal the target.
source_url_norm AS (
  SELECT
    s.id,
    s.source_type,
    s.title,
    s.publisher,
    s.url,
    s.verification_status,
    s.confidence,
    s.language,
    s.bibliography,
    CASE
      WHEN e.port_invalid_or_bracket THEN NULL
      WHEN e.stripped = '' THEN ''
      ELSE
        CASE WHEN b.scheme <> '' THEN b.scheme || ':' ELSE '' END
        || CASE
             WHEN e.netloc_norm <> ''
               OR (b.scheme <> '' AND b.scheme IN (
                     'ftp', 'http', 'gopher', 'nntp', 'telnet', 'imap', 'wais', 'file',
                     'mms', 'https', 'shttp', 'snews', 'prospero', 'rtsp', 'rtsps',
                     'rtspu', 'rsync', 'svn', 'svn+ssh', 'sftp', 'nfs', 'git',
                     'git+ssh', 'ws', 'wss', 'itms-services')
                   AND left(e.path_norm, 2) <> '//')
             THEN '//' || e.netloc_norm
                  || CASE WHEN e.path_norm <> '' AND left(e.path_norm, 1) <> '/'
                          THEN '/' || e.path_norm ELSE e.path_norm END
             ELSE e.path_norm
           END
        || CASE WHEN d.query <> '' THEN '?' || d.query ELSE '' END
    END AS normalized_url
  FROM temples_shrineknowledgesource s
  CROSS JOIN LATERAL (
    -- str.strip() (Python isspace set), then urlsplit(): lstrip C0 controls/space,
    -- then remove TAB / CR / LF anywhere.
    SELECT
      regexp_replace(COALESCE(s.url, ''),
        '^[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$',
        '', 'g') AS stripped
  ) a0
  CROSS JOIN LATERAL (
    SELECT
      a0.stripped,
      regexp_replace(regexp_replace(a0.stripped, '^[\u0001-\u0020]+', ''), '[\t\r\n]', '', 'g') AS trimmed
  ) a
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN lower(substring(a.trimmed FROM '^([A-Za-z][A-Za-z0-9+.-]*):'))
           ELSE '' END AS scheme,
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN substring(a.trimmed FROM '^[A-Za-z][A-Za-z0-9+.-]*:(.*)$')
           ELSE a.trimmed END AS rest
  ) b
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//([^/?#]*)') ELSE '' END AS netloc,
      split_part(CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//[^/?#]*(.*)$')
                      ELSE b.rest END, '#', 1) AS before_fragment
  ) c
  CROSS JOIN LATERAL (
    SELECT
      split_part(c.before_fragment, '?', 1) AS path,
      CASE WHEN position('?' IN c.before_fragment) > 0
           THEN substring(c.before_fragment FROM position('?' IN c.before_fragment) + 1)
           ELSE '' END AS query,
      regexp_replace(c.netloc, '^.*@', '') AS hostinfo
  ) d
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN position(':' IN d.hostinfo) > 0
           THEN substring(d.hostinfo FROM position(':' IN d.hostinfo) + 1)
           ELSE '' END AS port_raw,
      lower(split_part(d.hostinfo, ':', 1)) AS hostname
  ) p
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN p.port_raw = '' THEN NULL
           WHEN p.port_raw ~ '^[0-9]+$' AND length(ltrim(p.port_raw, '0')) <= 5
                AND COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint <= 65535
             THEN COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint
           ELSE NULL END AS port
  ) q
  CROSS JOIN LATERAL (
    SELECT
      a.stripped,
      (p.port_raw <> '' AND q.port IS NULL) OR c.netloc ~ '[][]' AS port_invalid_or_bracket,
      p.hostname
        || CASE WHEN q.port IS NOT NULL
                 AND NOT ((b.scheme = 'http' AND q.port = 80) OR (b.scheme = 'https' AND q.port = 443))
                THEN ':' || q.port::text ELSE '' END AS netloc_norm,
      CASE WHEN d.path IN ('', '/') THEN '/' ELSE rtrim(d.path, '/') END AS path_norm
  ) e
),
-- Source importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '三条市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.sanjo.niigata.jp%' AND lower(url) LIKE '%jinja_jisha_joshi/2289%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.sanjo.niigata.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%jinja_jisha_joshi/2289%')
)
-- END nsrc_000022_source_identity
SELECT
  'SANJO_CITY_IGARASHI_JINJA' AS source_key,
  'government' AS source_type,
  'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html' AS normalized_url,
  (SELECT COUNT(*) FROM source_identity) AS source_identity_count,
  (SELECT COUNT(*) FROM source_metadata_compatible) AS source_metadata_compatible_count,
  (SELECT COUNT(*) FROM source_url_lookalike) AS source_url_lookalike_count,
  (SELECT COUNT(*) FROM source_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM source_identity i WHERE i.id = l.id)) AS source_url_lookalike_non_identity_count,
  (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) AS source_type_url_unparseable_count,
  CASE
    WHEN (SELECT COUNT(*) FROM source_identity) > 1 THEN 'CONFLICT_IDENTITY_AMBIGUOUS'
    WHEN (SELECT COUNT(*) FROM source_identity) = 1
     AND (SELECT COUNT(*) FROM source_metadata_compatible) = 0 THEN 'CONFLICT_METADATA_DRIFT'
    WHEN (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) > 0
      THEN 'CONFLICT_IMPORTER_UNPARSEABLE_URL'
    WHEN (SELECT COUNT(*) FROM source_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM source_identity i WHERE i.id = l.id)) > 0
      THEN 'CONFLICT_NON_IDENTITY_LOOKALIKE'
    WHEN (SELECT COUNT(*) FROM source_identity) = 1 THEN 'REUSABLE'
    ELSE 'ABSENT'
  END AS source_identity_state;

-- Diagnostics only: every Deity / History of any shrine related to a lookalike Source row.
-- Never authorizes anything.
WITH
-- BEGIN nsrc_000022_source_identity
-- Byte-identical in every nsrc_000022_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000022_g7_source_identity_sql.py).
-- One Source (SANJO_CITY_IGARASHI_JINJA). Whether it already exists in Production is measured,
-- never assumed, and never matched approximately.
-- normalized_url reproduces knowledge_seed.normalize_source_url() exactly:
-- strip whitespace, drop TAB/CR/LF, lowercase scheme and hostname, drop userinfo,
-- drop default port (http 80 / https 443), drop fragment, ignore non-root trailing
-- '/', keep path case, keep query byte-for-byte, keep http and https distinct.
-- A URL the importer cannot parse (invalid port, bracketed host) yields NULL, so it
-- never counts as identity. Bracketed hosts are IP literals and cannot equal the target.
source_url_norm AS (
  SELECT
    s.id,
    s.source_type,
    s.title,
    s.publisher,
    s.url,
    s.verification_status,
    s.confidence,
    s.language,
    s.bibliography,
    CASE
      WHEN e.port_invalid_or_bracket THEN NULL
      WHEN e.stripped = '' THEN ''
      ELSE
        CASE WHEN b.scheme <> '' THEN b.scheme || ':' ELSE '' END
        || CASE
             WHEN e.netloc_norm <> ''
               OR (b.scheme <> '' AND b.scheme IN (
                     'ftp', 'http', 'gopher', 'nntp', 'telnet', 'imap', 'wais', 'file',
                     'mms', 'https', 'shttp', 'snews', 'prospero', 'rtsp', 'rtsps',
                     'rtspu', 'rsync', 'svn', 'svn+ssh', 'sftp', 'nfs', 'git',
                     'git+ssh', 'ws', 'wss', 'itms-services')
                   AND left(e.path_norm, 2) <> '//')
             THEN '//' || e.netloc_norm
                  || CASE WHEN e.path_norm <> '' AND left(e.path_norm, 1) <> '/'
                          THEN '/' || e.path_norm ELSE e.path_norm END
             ELSE e.path_norm
           END
        || CASE WHEN d.query <> '' THEN '?' || d.query ELSE '' END
    END AS normalized_url
  FROM temples_shrineknowledgesource s
  CROSS JOIN LATERAL (
    -- str.strip() (Python isspace set), then urlsplit(): lstrip C0 controls/space,
    -- then remove TAB / CR / LF anywhere.
    SELECT
      regexp_replace(COALESCE(s.url, ''),
        '^[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$',
        '', 'g') AS stripped
  ) a0
  CROSS JOIN LATERAL (
    SELECT
      a0.stripped,
      regexp_replace(regexp_replace(a0.stripped, '^[\u0001-\u0020]+', ''), '[\t\r\n]', '', 'g') AS trimmed
  ) a
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN lower(substring(a.trimmed FROM '^([A-Za-z][A-Za-z0-9+.-]*):'))
           ELSE '' END AS scheme,
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN substring(a.trimmed FROM '^[A-Za-z][A-Za-z0-9+.-]*:(.*)$')
           ELSE a.trimmed END AS rest
  ) b
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//([^/?#]*)') ELSE '' END AS netloc,
      split_part(CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//[^/?#]*(.*)$')
                      ELSE b.rest END, '#', 1) AS before_fragment
  ) c
  CROSS JOIN LATERAL (
    SELECT
      split_part(c.before_fragment, '?', 1) AS path,
      CASE WHEN position('?' IN c.before_fragment) > 0
           THEN substring(c.before_fragment FROM position('?' IN c.before_fragment) + 1)
           ELSE '' END AS query,
      regexp_replace(c.netloc, '^.*@', '') AS hostinfo
  ) d
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN position(':' IN d.hostinfo) > 0
           THEN substring(d.hostinfo FROM position(':' IN d.hostinfo) + 1)
           ELSE '' END AS port_raw,
      lower(split_part(d.hostinfo, ':', 1)) AS hostname
  ) p
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN p.port_raw = '' THEN NULL
           WHEN p.port_raw ~ '^[0-9]+$' AND length(ltrim(p.port_raw, '0')) <= 5
                AND COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint <= 65535
             THEN COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint
           ELSE NULL END AS port
  ) q
  CROSS JOIN LATERAL (
    SELECT
      a.stripped,
      (p.port_raw <> '' AND q.port IS NULL) OR c.netloc ~ '[][]' AS port_invalid_or_bracket,
      p.hostname
        || CASE WHEN q.port IS NOT NULL
                 AND NOT ((b.scheme = 'http' AND q.port = 80) OR (b.scheme = 'https' AND q.port = 443))
                THEN ':' || q.port::text ELSE '' END AS netloc_norm,
      CASE WHEN d.path IN ('', '/') THEN '/' ELSE rtrim(d.path, '/') END AS path_norm
  ) e
),
-- Source importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '三条市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.sanjo.niigata.jp%' AND lower(url) LIKE '%jinja_jisha_joshi/2289%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.sanjo.niigata.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%jinja_jisha_joshi/2289%')
)
-- END nsrc_000022_source_identity
SELECT
  'deity' AS fact_kind,
  ds.shrineknowledgesource_id AS source_id,
  d.display_name AS fact_label,
  s.name_jp AS shrine_name_jp,
  s.address AS shrine_address
FROM temples_shrinedeity_sources ds
JOIN temples_shrinedeity d ON d.id = ds.shrinedeity_id
JOIN temples_shrine s ON s.id = d.shrine_id
WHERE ds.shrineknowledgesource_id IN (SELECT id FROM source_url_lookalike)
UNION ALL
SELECT
  'history' AS fact_kind,
  hs.shrineknowledgesource_id AS source_id,
  h.title AS fact_label,
  s.name_jp AS shrine_name_jp,
  s.address AS shrine_address
FROM temples_shrinehistory_sources hs
JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
JOIN temples_shrine s ON s.id = h.shrine_id
WHERE hs.shrineknowledgesource_id IN (SELECT id FROM source_url_lookalike)
ORDER BY 1, 2, 3;

SELECT
  d.id,
  d.shrine_id,
  d.display_name,
  d.role,
  d.verification_status,
  d.confidence
FROM temples_shrinedeity d
JOIN temples_shrine s ON s.id = d.shrine_id
WHERE s.name_jp = '五十嵐神社'
  AND s.address = '新潟県三条市大字飯田2283番地'
ORDER BY d.id;

SELECT
  h.id,
  h.shrine_id,
  h.history_type,
  h.title,
  h.content,
  h.period_text,
  h.event_date,
  h.verification_status,
  h.confidence
FROM temples_shrinehistory h
JOIN temples_shrine s ON s.id = h.shrine_id
WHERE s.name_jp = '五十嵐神社'
  AND s.address = '新潟県三条市大字飯田2283番地'
ORDER BY h.id;

WITH
-- BEGIN nsrc_000022_source_identity
-- Byte-identical in every nsrc_000022_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000022_g7_source_identity_sql.py).
-- One Source (SANJO_CITY_IGARASHI_JINJA). Whether it already exists in Production is measured,
-- never assumed, and never matched approximately.
-- normalized_url reproduces knowledge_seed.normalize_source_url() exactly:
-- strip whitespace, drop TAB/CR/LF, lowercase scheme and hostname, drop userinfo,
-- drop default port (http 80 / https 443), drop fragment, ignore non-root trailing
-- '/', keep path case, keep query byte-for-byte, keep http and https distinct.
-- A URL the importer cannot parse (invalid port, bracketed host) yields NULL, so it
-- never counts as identity. Bracketed hosts are IP literals and cannot equal the target.
source_url_norm AS (
  SELECT
    s.id,
    s.source_type,
    s.title,
    s.publisher,
    s.url,
    s.verification_status,
    s.confidence,
    s.language,
    s.bibliography,
    CASE
      WHEN e.port_invalid_or_bracket THEN NULL
      WHEN e.stripped = '' THEN ''
      ELSE
        CASE WHEN b.scheme <> '' THEN b.scheme || ':' ELSE '' END
        || CASE
             WHEN e.netloc_norm <> ''
               OR (b.scheme <> '' AND b.scheme IN (
                     'ftp', 'http', 'gopher', 'nntp', 'telnet', 'imap', 'wais', 'file',
                     'mms', 'https', 'shttp', 'snews', 'prospero', 'rtsp', 'rtsps',
                     'rtspu', 'rsync', 'svn', 'svn+ssh', 'sftp', 'nfs', 'git',
                     'git+ssh', 'ws', 'wss', 'itms-services')
                   AND left(e.path_norm, 2) <> '//')
             THEN '//' || e.netloc_norm
                  || CASE WHEN e.path_norm <> '' AND left(e.path_norm, 1) <> '/'
                          THEN '/' || e.path_norm ELSE e.path_norm END
             ELSE e.path_norm
           END
        || CASE WHEN d.query <> '' THEN '?' || d.query ELSE '' END
    END AS normalized_url
  FROM temples_shrineknowledgesource s
  CROSS JOIN LATERAL (
    -- str.strip() (Python isspace set), then urlsplit(): lstrip C0 controls/space,
    -- then remove TAB / CR / LF anywhere.
    SELECT
      regexp_replace(COALESCE(s.url, ''),
        '^[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$',
        '', 'g') AS stripped
  ) a0
  CROSS JOIN LATERAL (
    SELECT
      a0.stripped,
      regexp_replace(regexp_replace(a0.stripped, '^[\u0001-\u0020]+', ''), '[\t\r\n]', '', 'g') AS trimmed
  ) a
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN lower(substring(a.trimmed FROM '^([A-Za-z][A-Za-z0-9+.-]*):'))
           ELSE '' END AS scheme,
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN substring(a.trimmed FROM '^[A-Za-z][A-Za-z0-9+.-]*:(.*)$')
           ELSE a.trimmed END AS rest
  ) b
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//([^/?#]*)') ELSE '' END AS netloc,
      split_part(CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//[^/?#]*(.*)$')
                      ELSE b.rest END, '#', 1) AS before_fragment
  ) c
  CROSS JOIN LATERAL (
    SELECT
      split_part(c.before_fragment, '?', 1) AS path,
      CASE WHEN position('?' IN c.before_fragment) > 0
           THEN substring(c.before_fragment FROM position('?' IN c.before_fragment) + 1)
           ELSE '' END AS query,
      regexp_replace(c.netloc, '^.*@', '') AS hostinfo
  ) d
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN position(':' IN d.hostinfo) > 0
           THEN substring(d.hostinfo FROM position(':' IN d.hostinfo) + 1)
           ELSE '' END AS port_raw,
      lower(split_part(d.hostinfo, ':', 1)) AS hostname
  ) p
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN p.port_raw = '' THEN NULL
           WHEN p.port_raw ~ '^[0-9]+$' AND length(ltrim(p.port_raw, '0')) <= 5
                AND COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint <= 65535
             THEN COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint
           ELSE NULL END AS port
  ) q
  CROSS JOIN LATERAL (
    SELECT
      a.stripped,
      (p.port_raw <> '' AND q.port IS NULL) OR c.netloc ~ '[][]' AS port_invalid_or_bracket,
      p.hostname
        || CASE WHEN q.port IS NOT NULL
                 AND NOT ((b.scheme = 'http' AND q.port = 80) OR (b.scheme = 'https' AND q.port = 443))
                THEN ':' || q.port::text ELSE '' END AS netloc_norm,
      CASE WHEN d.path IN ('', '/') THEN '/' ELSE rtrim(d.path, '/') END AS path_norm
  ) e
),
-- Source importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '三条市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.sanjo.niigata.jp%' AND lower(url) LIKE '%jinja_jisha_joshi/2289%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.sanjo.niigata.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%jinja_jisha_joshi/2289%')
)
-- END nsrc_000022_source_identity
,
-- BEGIN nsrc_000022_target_facts
-- Byte-identical in every nsrc_000022_g7_*.sql file that contains it. Requires the
-- nsrc_000022_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '五十嵐神社'
    AND address = '新潟県三条市大字飯田2283番地'
),
-- expected_key = the frozen Deity the row equals in every field (NULL = unexpected row)
target_deity AS (
  SELECT
    d.id,
    d.display_name,
    CASE
      WHEN d.display_name = '五十日帯日子命' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd1'
      ELSE NULL
    END AS expected_key
  FROM temples_shrinedeity d
  JOIN target t ON t.id = d.shrine_id
),
-- expected_key = the frozen History the row equals in every field (NULL = unexpected row)
target_history AS (
  SELECT
    h.id,
    NULL::text AS expected_key
  FROM temples_shrinehistory h
  JOIN target t ON t.id = h.shrine_id
),
-- every Source relation of a target Deity / History; to_source = the compatible Source
target_relation AS (
  SELECT
    'deity' AS fact_kind,
    ds.shrinedeity_id AS fact_id,
    ds.shrineknowledgesource_id AS source_id,
    EXISTS (SELECT 1 FROM source_metadata_compatible cs
             WHERE cs.id = ds.shrineknowledgesource_id) AS to_source
  FROM temples_shrinedeity_sources ds
  JOIN target_deity td ON td.id = ds.shrinedeity_id
  UNION ALL
  SELECT
    'history' AS fact_kind,
    hs.shrinehistory_id AS fact_id,
    hs.shrineknowledgesource_id AS source_id,
    EXISTS (SELECT 1 FROM source_metadata_compatible cs
             WHERE cs.id = hs.shrineknowledgesource_id) AS to_source
  FROM temples_shrinehistory_sources hs
  JOIN target_history th ON th.id = hs.shrinehistory_id
),
-- every ShrineFactSourceCitation of a target Deity / History (the seed has none)
target_citation AS (
  SELECT c.id, c.shrine_history_id, c.shrine_deity_id, c.source_id, c.locator_text
  FROM temples_shrinefactsourcecitation c
  WHERE c.shrine_history_id IN (SELECT id FROM target_history)
     OR c.shrine_deity_id IN (SELECT id FROM target_deity)
),
-- Fact-Source relations from any other shrine's Deity / History to the Source identity
foreign_relation AS (
  SELECT ds.shrinedeity_id AS fact_id, ds.shrineknowledgesource_id AS source_id
  FROM temples_shrinedeity_sources ds
  JOIN temples_shrinedeity d ON d.id = ds.shrinedeity_id
  WHERE ds.shrineknowledgesource_id IN (SELECT id FROM source_identity)
    AND d.shrine_id NOT IN (SELECT id FROM target)
  UNION ALL
  SELECT hs.shrinehistory_id AS fact_id, hs.shrineknowledgesource_id AS source_id
  FROM temples_shrinehistory_sources hs
  JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
  WHERE hs.shrineknowledgesource_id IN (SELECT id FROM source_identity)
    AND h.shrine_id NOT IN (SELECT id FROM target)
)
-- END nsrc_000022_target_facts
SELECT
  r.fact_kind,
  r.fact_id,
  r.source_id,
  src.source_type,
  src.url,
  src.publisher,
  src.verification_status,
  r.to_source
FROM target_relation r
JOIN temples_shrineknowledgesource src ON src.id = r.source_id
ORDER BY r.fact_kind, r.fact_id, r.source_id;

WITH
-- BEGIN nsrc_000022_source_identity
-- Byte-identical in every nsrc_000022_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000022_g7_source_identity_sql.py).
-- One Source (SANJO_CITY_IGARASHI_JINJA). Whether it already exists in Production is measured,
-- never assumed, and never matched approximately.
-- normalized_url reproduces knowledge_seed.normalize_source_url() exactly:
-- strip whitespace, drop TAB/CR/LF, lowercase scheme and hostname, drop userinfo,
-- drop default port (http 80 / https 443), drop fragment, ignore non-root trailing
-- '/', keep path case, keep query byte-for-byte, keep http and https distinct.
-- A URL the importer cannot parse (invalid port, bracketed host) yields NULL, so it
-- never counts as identity. Bracketed hosts are IP literals and cannot equal the target.
source_url_norm AS (
  SELECT
    s.id,
    s.source_type,
    s.title,
    s.publisher,
    s.url,
    s.verification_status,
    s.confidence,
    s.language,
    s.bibliography,
    CASE
      WHEN e.port_invalid_or_bracket THEN NULL
      WHEN e.stripped = '' THEN ''
      ELSE
        CASE WHEN b.scheme <> '' THEN b.scheme || ':' ELSE '' END
        || CASE
             WHEN e.netloc_norm <> ''
               OR (b.scheme <> '' AND b.scheme IN (
                     'ftp', 'http', 'gopher', 'nntp', 'telnet', 'imap', 'wais', 'file',
                     'mms', 'https', 'shttp', 'snews', 'prospero', 'rtsp', 'rtsps',
                     'rtspu', 'rsync', 'svn', 'svn+ssh', 'sftp', 'nfs', 'git',
                     'git+ssh', 'ws', 'wss', 'itms-services')
                   AND left(e.path_norm, 2) <> '//')
             THEN '//' || e.netloc_norm
                  || CASE WHEN e.path_norm <> '' AND left(e.path_norm, 1) <> '/'
                          THEN '/' || e.path_norm ELSE e.path_norm END
             ELSE e.path_norm
           END
        || CASE WHEN d.query <> '' THEN '?' || d.query ELSE '' END
    END AS normalized_url
  FROM temples_shrineknowledgesource s
  CROSS JOIN LATERAL (
    -- str.strip() (Python isspace set), then urlsplit(): lstrip C0 controls/space,
    -- then remove TAB / CR / LF anywhere.
    SELECT
      regexp_replace(COALESCE(s.url, ''),
        '^[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$',
        '', 'g') AS stripped
  ) a0
  CROSS JOIN LATERAL (
    SELECT
      a0.stripped,
      regexp_replace(regexp_replace(a0.stripped, '^[\u0001-\u0020]+', ''), '[\t\r\n]', '', 'g') AS trimmed
  ) a
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN lower(substring(a.trimmed FROM '^([A-Za-z][A-Za-z0-9+.-]*):'))
           ELSE '' END AS scheme,
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN substring(a.trimmed FROM '^[A-Za-z][A-Za-z0-9+.-]*:(.*)$')
           ELSE a.trimmed END AS rest
  ) b
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//([^/?#]*)') ELSE '' END AS netloc,
      split_part(CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//[^/?#]*(.*)$')
                      ELSE b.rest END, '#', 1) AS before_fragment
  ) c
  CROSS JOIN LATERAL (
    SELECT
      split_part(c.before_fragment, '?', 1) AS path,
      CASE WHEN position('?' IN c.before_fragment) > 0
           THEN substring(c.before_fragment FROM position('?' IN c.before_fragment) + 1)
           ELSE '' END AS query,
      regexp_replace(c.netloc, '^.*@', '') AS hostinfo
  ) d
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN position(':' IN d.hostinfo) > 0
           THEN substring(d.hostinfo FROM position(':' IN d.hostinfo) + 1)
           ELSE '' END AS port_raw,
      lower(split_part(d.hostinfo, ':', 1)) AS hostname
  ) p
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN p.port_raw = '' THEN NULL
           WHEN p.port_raw ~ '^[0-9]+$' AND length(ltrim(p.port_raw, '0')) <= 5
                AND COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint <= 65535
             THEN COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint
           ELSE NULL END AS port
  ) q
  CROSS JOIN LATERAL (
    SELECT
      a.stripped,
      (p.port_raw <> '' AND q.port IS NULL) OR c.netloc ~ '[][]' AS port_invalid_or_bracket,
      p.hostname
        || CASE WHEN q.port IS NOT NULL
                 AND NOT ((b.scheme = 'http' AND q.port = 80) OR (b.scheme = 'https' AND q.port = 443))
                THEN ':' || q.port::text ELSE '' END AS netloc_norm,
      CASE WHEN d.path IN ('', '/') THEN '/' ELSE rtrim(d.path, '/') END AS path_norm
  ) e
),
-- Source importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '三条市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.sanjo.niigata.jp%' AND lower(url) LIKE '%jinja_jisha_joshi/2289%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.sanjo.niigata.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%jinja_jisha_joshi/2289%')
)
-- END nsrc_000022_source_identity
,
-- BEGIN nsrc_000022_target_facts
-- Byte-identical in every nsrc_000022_g7_*.sql file that contains it. Requires the
-- nsrc_000022_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '五十嵐神社'
    AND address = '新潟県三条市大字飯田2283番地'
),
-- expected_key = the frozen Deity the row equals in every field (NULL = unexpected row)
target_deity AS (
  SELECT
    d.id,
    d.display_name,
    CASE
      WHEN d.display_name = '五十日帯日子命' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd1'
      ELSE NULL
    END AS expected_key
  FROM temples_shrinedeity d
  JOIN target t ON t.id = d.shrine_id
),
-- expected_key = the frozen History the row equals in every field (NULL = unexpected row)
target_history AS (
  SELECT
    h.id,
    NULL::text AS expected_key
  FROM temples_shrinehistory h
  JOIN target t ON t.id = h.shrine_id
),
-- every Source relation of a target Deity / History; to_source = the compatible Source
target_relation AS (
  SELECT
    'deity' AS fact_kind,
    ds.shrinedeity_id AS fact_id,
    ds.shrineknowledgesource_id AS source_id,
    EXISTS (SELECT 1 FROM source_metadata_compatible cs
             WHERE cs.id = ds.shrineknowledgesource_id) AS to_source
  FROM temples_shrinedeity_sources ds
  JOIN target_deity td ON td.id = ds.shrinedeity_id
  UNION ALL
  SELECT
    'history' AS fact_kind,
    hs.shrinehistory_id AS fact_id,
    hs.shrineknowledgesource_id AS source_id,
    EXISTS (SELECT 1 FROM source_metadata_compatible cs
             WHERE cs.id = hs.shrineknowledgesource_id) AS to_source
  FROM temples_shrinehistory_sources hs
  JOIN target_history th ON th.id = hs.shrinehistory_id
),
-- every ShrineFactSourceCitation of a target Deity / History (the seed has none)
target_citation AS (
  SELECT c.id, c.shrine_history_id, c.shrine_deity_id, c.source_id, c.locator_text
  FROM temples_shrinefactsourcecitation c
  WHERE c.shrine_history_id IN (SELECT id FROM target_history)
     OR c.shrine_deity_id IN (SELECT id FROM target_deity)
),
-- Fact-Source relations from any other shrine's Deity / History to the Source identity
foreign_relation AS (
  SELECT ds.shrinedeity_id AS fact_id, ds.shrineknowledgesource_id AS source_id
  FROM temples_shrinedeity_sources ds
  JOIN temples_shrinedeity d ON d.id = ds.shrinedeity_id
  WHERE ds.shrineknowledgesource_id IN (SELECT id FROM source_identity)
    AND d.shrine_id NOT IN (SELECT id FROM target)
  UNION ALL
  SELECT hs.shrinehistory_id AS fact_id, hs.shrineknowledgesource_id AS source_id
  FROM temples_shrinehistory_sources hs
  JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
  WHERE hs.shrineknowledgesource_id IN (SELECT id FROM source_identity)
    AND h.shrine_id NOT IN (SELECT id FROM target)
)
-- END nsrc_000022_target_facts
SELECT
  tc.id,
  tc.shrine_history_id,
  tc.shrine_deity_id,
  tc.source_id,
  tc.locator_text
FROM target_citation tc
ORDER BY tc.id;

SELECT
  sf.id,
  sf.shrine_id,
  sf.stable_key,
  sf.verification_status,
  sf.confidence
FROM temples_shrinesourcefact sf
JOIN temples_shrine s ON s.id = sf.shrine_id
WHERE s.name_jp = '五十嵐神社'
  AND s.address = '新潟県三条市大字飯田2283番地'
ORDER BY sf.id;

WITH
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '五十嵐神社'
    AND address = '新潟県三条市大字飯田2283番地'
)
SELECT
  (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS target_collectives,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS target_goriyaku_tag_links,
  (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS target_goriyaku_assignments,
  (SELECT COUNT(*) FROM target WHERE COALESCE(goriyaku, '') <> '') AS target_goriyaku_text_nonempty;

-- State class candidate (CLEAN_CREATE / ALREADY_MATERIALIZED / PARTIAL_EXISTING / CONFLICT).
-- Any CONFLICT_* Source state, target identity ambiguity, same-address collision, or
-- unexpected target Knowledge / relation / citation is CONFLICT. Mother Ship confirms the
-- class; this query does not authorize any write.
WITH
-- BEGIN nsrc_000022_source_identity
-- Byte-identical in every nsrc_000022_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000022_g7_source_identity_sql.py).
-- One Source (SANJO_CITY_IGARASHI_JINJA). Whether it already exists in Production is measured,
-- never assumed, and never matched approximately.
-- normalized_url reproduces knowledge_seed.normalize_source_url() exactly:
-- strip whitespace, drop TAB/CR/LF, lowercase scheme and hostname, drop userinfo,
-- drop default port (http 80 / https 443), drop fragment, ignore non-root trailing
-- '/', keep path case, keep query byte-for-byte, keep http and https distinct.
-- A URL the importer cannot parse (invalid port, bracketed host) yields NULL, so it
-- never counts as identity. Bracketed hosts are IP literals and cannot equal the target.
source_url_norm AS (
  SELECT
    s.id,
    s.source_type,
    s.title,
    s.publisher,
    s.url,
    s.verification_status,
    s.confidence,
    s.language,
    s.bibliography,
    CASE
      WHEN e.port_invalid_or_bracket THEN NULL
      WHEN e.stripped = '' THEN ''
      ELSE
        CASE WHEN b.scheme <> '' THEN b.scheme || ':' ELSE '' END
        || CASE
             WHEN e.netloc_norm <> ''
               OR (b.scheme <> '' AND b.scheme IN (
                     'ftp', 'http', 'gopher', 'nntp', 'telnet', 'imap', 'wais', 'file',
                     'mms', 'https', 'shttp', 'snews', 'prospero', 'rtsp', 'rtsps',
                     'rtspu', 'rsync', 'svn', 'svn+ssh', 'sftp', 'nfs', 'git',
                     'git+ssh', 'ws', 'wss', 'itms-services')
                   AND left(e.path_norm, 2) <> '//')
             THEN '//' || e.netloc_norm
                  || CASE WHEN e.path_norm <> '' AND left(e.path_norm, 1) <> '/'
                          THEN '/' || e.path_norm ELSE e.path_norm END
             ELSE e.path_norm
           END
        || CASE WHEN d.query <> '' THEN '?' || d.query ELSE '' END
    END AS normalized_url
  FROM temples_shrineknowledgesource s
  CROSS JOIN LATERAL (
    -- str.strip() (Python isspace set), then urlsplit(): lstrip C0 controls/space,
    -- then remove TAB / CR / LF anywhere.
    SELECT
      regexp_replace(COALESCE(s.url, ''),
        '^[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$',
        '', 'g') AS stripped
  ) a0
  CROSS JOIN LATERAL (
    SELECT
      a0.stripped,
      regexp_replace(regexp_replace(a0.stripped, '^[\u0001-\u0020]+', ''), '[\t\r\n]', '', 'g') AS trimmed
  ) a
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN lower(substring(a.trimmed FROM '^([A-Za-z][A-Za-z0-9+.-]*):'))
           ELSE '' END AS scheme,
      CASE WHEN a.trimmed ~ '^[A-Za-z][A-Za-z0-9+.-]*:'
           THEN substring(a.trimmed FROM '^[A-Za-z][A-Za-z0-9+.-]*:(.*)$')
           ELSE a.trimmed END AS rest
  ) b
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//([^/?#]*)') ELSE '' END AS netloc,
      split_part(CASE WHEN left(b.rest, 2) = '//' THEN substring(b.rest FROM '^//[^/?#]*(.*)$')
                      ELSE b.rest END, '#', 1) AS before_fragment
  ) c
  CROSS JOIN LATERAL (
    SELECT
      split_part(c.before_fragment, '?', 1) AS path,
      CASE WHEN position('?' IN c.before_fragment) > 0
           THEN substring(c.before_fragment FROM position('?' IN c.before_fragment) + 1)
           ELSE '' END AS query,
      regexp_replace(c.netloc, '^.*@', '') AS hostinfo
  ) d
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN position(':' IN d.hostinfo) > 0
           THEN substring(d.hostinfo FROM position(':' IN d.hostinfo) + 1)
           ELSE '' END AS port_raw,
      lower(split_part(d.hostinfo, ':', 1)) AS hostname
  ) p
  CROSS JOIN LATERAL (
    SELECT
      CASE WHEN p.port_raw = '' THEN NULL
           WHEN p.port_raw ~ '^[0-9]+$' AND length(ltrim(p.port_raw, '0')) <= 5
                AND COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint <= 65535
             THEN COALESCE(NULLIF(ltrim(p.port_raw, '0'), ''), '0')::bigint
           ELSE NULL END AS port
  ) q
  CROSS JOIN LATERAL (
    SELECT
      a.stripped,
      (p.port_raw <> '' AND q.port IS NULL) OR c.netloc ~ '[][]' AS port_invalid_or_bracket,
      p.hostname
        || CASE WHEN q.port IS NOT NULL
                 AND NOT ((b.scheme = 'http' AND q.port = 80) OR (b.scheme = 'https' AND q.port = 443))
                THEN ':' || q.port::text ELSE '' END AS netloc_norm,
      CASE WHEN d.path IN ('', '/') THEN '/' ELSE rtrim(d.path, '/') END AS path_norm
  ) e
),
-- Source importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '三条市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.sanjo.niigata.jp%' AND lower(url) LIKE '%jinja_jisha_joshi/2289%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.sanjo.niigata.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%jinja_jisha_joshi/2289%')
)
-- END nsrc_000022_source_identity
,
-- BEGIN nsrc_000022_target_facts
-- Byte-identical in every nsrc_000022_g7_*.sql file that contains it. Requires the
-- nsrc_000022_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '五十嵐神社'
    AND address = '新潟県三条市大字飯田2283番地'
),
-- expected_key = the frozen Deity the row equals in every field (NULL = unexpected row)
target_deity AS (
  SELECT
    d.id,
    d.display_name,
    CASE
      WHEN d.display_name = '五十日帯日子命' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd1'
      ELSE NULL
    END AS expected_key
  FROM temples_shrinedeity d
  JOIN target t ON t.id = d.shrine_id
),
-- expected_key = the frozen History the row equals in every field (NULL = unexpected row)
target_history AS (
  SELECT
    h.id,
    NULL::text AS expected_key
  FROM temples_shrinehistory h
  JOIN target t ON t.id = h.shrine_id
),
-- every Source relation of a target Deity / History; to_source = the compatible Source
target_relation AS (
  SELECT
    'deity' AS fact_kind,
    ds.shrinedeity_id AS fact_id,
    ds.shrineknowledgesource_id AS source_id,
    EXISTS (SELECT 1 FROM source_metadata_compatible cs
             WHERE cs.id = ds.shrineknowledgesource_id) AS to_source
  FROM temples_shrinedeity_sources ds
  JOIN target_deity td ON td.id = ds.shrinedeity_id
  UNION ALL
  SELECT
    'history' AS fact_kind,
    hs.shrinehistory_id AS fact_id,
    hs.shrineknowledgesource_id AS source_id,
    EXISTS (SELECT 1 FROM source_metadata_compatible cs
             WHERE cs.id = hs.shrineknowledgesource_id) AS to_source
  FROM temples_shrinehistory_sources hs
  JOIN target_history th ON th.id = hs.shrinehistory_id
),
-- every ShrineFactSourceCitation of a target Deity / History (the seed has none)
target_citation AS (
  SELECT c.id, c.shrine_history_id, c.shrine_deity_id, c.source_id, c.locator_text
  FROM temples_shrinefactsourcecitation c
  WHERE c.shrine_history_id IN (SELECT id FROM target_history)
     OR c.shrine_deity_id IN (SELECT id FROM target_deity)
),
-- Fact-Source relations from any other shrine's Deity / History to the Source identity
foreign_relation AS (
  SELECT ds.shrinedeity_id AS fact_id, ds.shrineknowledgesource_id AS source_id
  FROM temples_shrinedeity_sources ds
  JOIN temples_shrinedeity d ON d.id = ds.shrinedeity_id
  WHERE ds.shrineknowledgesource_id IN (SELECT id FROM source_identity)
    AND d.shrine_id NOT IN (SELECT id FROM target)
  UNION ALL
  SELECT hs.shrinehistory_id AS fact_id, hs.shrineknowledgesource_id AS source_id
  FROM temples_shrinehistory_sources hs
  JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
  WHERE hs.shrineknowledgesource_id IN (SELECT id FROM source_identity)
    AND h.shrine_id NOT IN (SELECT id FROM target)
)
-- END nsrc_000022_target_facts
,
counts AS (
  SELECT
    (SELECT COUNT(*) FROM target) AS target_exact,
    (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県三条市大字飯田2283番地') AS same_address,
    (SELECT COUNT(*) FROM source_identity) AS source_identity,
    (SELECT COUNT(*) FROM source_metadata_compatible) AS source_compatible,
    (SELECT COUNT(*) FROM source_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM source_identity i WHERE i.id = l.id)) AS source_lookalike_non_identity,
    (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) AS source_unparseable,
    (SELECT COUNT(*) FROM target_deity) AS deity,
    (SELECT COUNT(*) FROM target_deity WHERE expected_key IS NULL) AS deity_unexpected,
    (SELECT COUNT(DISTINCT expected_key) FROM target_deity) AS deity_expected_distinct,
    (SELECT COUNT(*) FROM target_history) AS history,
    (SELECT COUNT(*) FROM target_history WHERE expected_key IS NULL) AS history_unexpected,
    (SELECT COUNT(DISTINCT expected_key) FROM target_history) AS history_expected_distinct,
    (SELECT COUNT(*) FROM target_deity WHERE display_name IN ('五十日帯彦命')) AS excluded_deity,
    (SELECT COUNT(*) FROM target_relation) AS relations,
    (SELECT COUNT(*) FROM target_relation WHERE NOT to_source) AS relations_not_to_source,
    (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'deity' AND to_source) AS deity_related,
    (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'history' AND to_source) AS history_related,
    (SELECT COUNT(*) FROM target_citation) AS citations,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) AS source_fact,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS collective,
    (SELECT COUNT(*) FROM target
       WHERE abs(latitude - 37.573979) < 0.00000001
         AND abs(longitude - 139.048758) < 0.00000001) AS coordinate_ok,
    (SELECT COUNT(*) FROM target WHERE COALESCE(goriyaku, '') = '') AS goriyaku_empty,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS goriyaku_tags,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS goriyaku_assignments
)
SELECT
  CASE
    WHEN source_identity > 1 OR (source_identity = 1 AND source_compatible = 0)
      OR source_unparseable > 0 OR source_lookalike_non_identity > 0
      OR target_exact > 1
      OR same_address <> target_exact
      THEN 'CONFLICT'
    WHEN target_exact = 0 THEN 'CLEAN_CREATE'
    WHEN deity_unexpected > 0 OR history_unexpected > 0
      OR deity - deity_unexpected <> deity_expected_distinct
      OR history - history_unexpected <> history_expected_distinct
      OR excluded_deity > 0
      OR relations_not_to_source > 0
      OR citations > 0 OR source_fact > 0 OR collective > 0
      OR coordinate_ok = 0 OR goriyaku_empty = 0 OR goriyaku_tags > 0 OR goriyaku_assignments > 0
      THEN 'CONFLICT'
    WHEN deity = 1 AND deity_expected_distinct = 1
      AND history = 0 AND history_expected_distinct = 0
      AND relations = 1 AND deity_related = 1 AND history_related = 0
      AND source_identity = 1 AND source_compatible = 1
      THEN 'ALREADY_MATERIALIZED'
    ELSE 'PARTIAL_EXISTING'
  END AS production_state_class_candidate,
  source_identity AS source_identity_count,
  source_compatible AS source_metadata_compatible_count,
  target_exact AS target_exact_count,
  deity AS target_deity_count,
  history AS target_history_count,
  relations AS target_fact_source_relation_count,
  citations AS target_citation_count
FROM counts;
