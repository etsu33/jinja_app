-- nsrc-000006 赤井神社 G7 Production Import Gate — read-only preflight
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.
--
-- Canonical target = exact (name_jp, address): 赤井神社 / 新潟県佐渡市加茂歌代2662番地.
-- Same-name rows at other addresses (including the noncanonical 新潟県佐渡市加茂歌代2622番地 /
-- 新潟県佐渡市加茂歌代1164-7 forms) are diagnostics only and never identify the target.
--
-- Source identity is the importer's semantic identity only
-- (knowledge_seed.resolve_source_identity(): source_type + normalize_source_url()):
--   S2 = tourism_official + https://sado-geinou.com/geinou/kamoutashiro
--   S3 = local_history + https://dl.ndl.go.jp/pid/971197
-- Per Source, three separate concepts:
--   source_identity_count            exact importer identity (the only reusable rows)
--   source_metadata_compatible_count identity rows whose _SOURCE_REUSE_FIELDS match the seed
--   source_url_lookalike_count       broad diagnostic match; never reusable by itself

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
  to_regclass('public.temples_shrinedeitycollective') IS NOT NULL AS collective_table_exists,
  to_regclass('public.temples_shrine_goriyaku_tags') IS NOT NULL AS goriyaku_tags_table_exists,
  to_regclass('public.temples_shrinegoriyakuassignment') IS NOT NULL AS goriyaku_assignment_table_exists;

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total,
  (SELECT COUNT(*) FROM temples_shrinedeitycollective) AS collective_total;

SELECT
  COUNT(*) FILTER (
    WHERE name_jp = '赤井神社'
      AND address = '新潟県佐渡市加茂歌代2662番地'
  ) AS target_exact_count,
  COUNT(*) FILTER (WHERE name_jp = '赤井神社') AS same_name_akai_count,
  COUNT(*) FILTER (WHERE name_jp = '赤井神社' AND address <> '新潟県佐渡市加茂歌代2662番地') AS same_name_other_address_count,
  COUNT(*) FILTER (WHERE address = '新潟県佐渡市加茂歌代2662番地') AS same_address_count
FROM temples_shrine;

-- Diagnostics only: same-name rows at other addresses do not identify the canonical target.
SELECT
  id,
  name_jp,
  address,
  latitude,
  longitude,
  place_ref_id,
  COALESCE(goriyaku, '') AS goriyaku,
  (name_jp = '赤井神社' AND address = '新潟県佐渡市加茂歌代2662番地') AS is_canonical_target
FROM temples_shrine
WHERE name_jp = '赤井神社'
   OR address = '新潟県佐渡市加茂歌代2662番地'
ORDER BY id;

WITH
-- BEGIN nsrc_000006_source_identity
-- Byte-identical in every nsrc_000006_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000006_g7_source_identity_sql.py).
-- S2 and S3 are independent importer identities; neither is ever matched approximately.
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
-- S2 importer semantic identity: same source_type, non-empty url, same normalized URL
s2_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'tourism_official'
    AND url <> ''
    AND normalized_url = 'https://sado-geinou.com/geinou/kamoutashiro'
),
-- S2 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s2_metadata_compatible AS (
  SELECT *
  FROM s2_identity
  WHERE btrim(COALESCE(publisher, '')) = '佐渡芸能アーカイブ'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S2 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s2_identity)
s2_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%sado-geinou.com%' AND lower(url) LIKE '%geinou%kamoutashiro%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%sado-geinou.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%geinou%kamoutashiro%')
),
-- S3 importer semantic identity: same source_type, non-empty url, same normalized URL
s3_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'local_history'
    AND url <> ''
    AND normalized_url = 'https://dl.ndl.go.jp/pid/971197'
),
-- S3 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s3_metadata_compatible AS (
  SELECT *
  FROM s3_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟県神職会佐渡支部'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S3 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s3_identity)
s3_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%dl.ndl.go.jp%' AND lower(url) LIKE '%pid%971197%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%dl.ndl.go.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%pid%971197%')
)
-- END nsrc_000006_source_identity
SELECT
  'S2' AS source_label,
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
  EXISTS (SELECT 1 FROM s2_identity i WHERE i.id = l.id) AS is_source_identity,
  EXISTS (SELECT 1 FROM s2_metadata_compatible m WHERE m.id = l.id) AS is_metadata_compatible
FROM s2_url_lookalike l
ORDER BY l.id;

WITH
-- BEGIN nsrc_000006_source_identity
-- Byte-identical in every nsrc_000006_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000006_g7_source_identity_sql.py).
-- S2 and S3 are independent importer identities; neither is ever matched approximately.
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
-- S2 importer semantic identity: same source_type, non-empty url, same normalized URL
s2_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'tourism_official'
    AND url <> ''
    AND normalized_url = 'https://sado-geinou.com/geinou/kamoutashiro'
),
-- S2 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s2_metadata_compatible AS (
  SELECT *
  FROM s2_identity
  WHERE btrim(COALESCE(publisher, '')) = '佐渡芸能アーカイブ'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S2 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s2_identity)
s2_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%sado-geinou.com%' AND lower(url) LIKE '%geinou%kamoutashiro%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%sado-geinou.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%geinou%kamoutashiro%')
),
-- S3 importer semantic identity: same source_type, non-empty url, same normalized URL
s3_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'local_history'
    AND url <> ''
    AND normalized_url = 'https://dl.ndl.go.jp/pid/971197'
),
-- S3 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s3_metadata_compatible AS (
  SELECT *
  FROM s3_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟県神職会佐渡支部'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S3 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s3_identity)
s3_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%dl.ndl.go.jp%' AND lower(url) LIKE '%pid%971197%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%dl.ndl.go.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%pid%971197%')
)
-- END nsrc_000006_source_identity
SELECT
  'S3' AS source_label,
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
  EXISTS (SELECT 1 FROM s3_identity i WHERE i.id = l.id) AS is_source_identity,
  EXISTS (SELECT 1 FROM s3_metadata_compatible m WHERE m.id = l.id) AS is_metadata_compatible
FROM s3_url_lookalike l
ORDER BY l.id;

WITH
-- BEGIN nsrc_000006_source_identity
-- Byte-identical in every nsrc_000006_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000006_g7_source_identity_sql.py).
-- S2 and S3 are independent importer identities; neither is ever matched approximately.
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
-- S2 importer semantic identity: same source_type, non-empty url, same normalized URL
s2_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'tourism_official'
    AND url <> ''
    AND normalized_url = 'https://sado-geinou.com/geinou/kamoutashiro'
),
-- S2 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s2_metadata_compatible AS (
  SELECT *
  FROM s2_identity
  WHERE btrim(COALESCE(publisher, '')) = '佐渡芸能アーカイブ'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S2 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s2_identity)
s2_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%sado-geinou.com%' AND lower(url) LIKE '%geinou%kamoutashiro%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%sado-geinou.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%geinou%kamoutashiro%')
),
-- S3 importer semantic identity: same source_type, non-empty url, same normalized URL
s3_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'local_history'
    AND url <> ''
    AND normalized_url = 'https://dl.ndl.go.jp/pid/971197'
),
-- S3 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s3_metadata_compatible AS (
  SELECT *
  FROM s3_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟県神職会佐渡支部'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S3 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s3_identity)
s3_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%dl.ndl.go.jp%' AND lower(url) LIKE '%pid%971197%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%dl.ndl.go.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%pid%971197%')
)
-- END nsrc_000006_source_identity
SELECT
  'S2' AS source_label,
  'tourism_official' AS source_type,
  'https://sado-geinou.com/geinou/kamoutashiro' AS normalized_url,
  (SELECT COUNT(*) FROM s2_identity) AS source_identity_count,
  (SELECT COUNT(*) FROM s2_metadata_compatible) AS source_metadata_compatible_count,
  (SELECT COUNT(*) FROM s2_url_lookalike) AS source_url_lookalike_count,
  (SELECT COUNT(*) FROM s2_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM s2_identity i WHERE i.id = l.id)) AS source_url_lookalike_non_identity_count,
  (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'tourism_official' AND url <> '' AND normalized_url IS NULL) AS source_type_url_unparseable_count,
  CASE
    WHEN (SELECT COUNT(*) FROM s2_identity) > 1 THEN 'CONFLICT_IDENTITY_AMBIGUOUS'
    WHEN (SELECT COUNT(*) FROM s2_identity) = 1
     AND (SELECT COUNT(*) FROM s2_metadata_compatible) = 0 THEN 'CONFLICT_METADATA_DRIFT'
    WHEN (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'tourism_official' AND url <> '' AND normalized_url IS NULL) > 0
      THEN 'CONFLICT_IMPORTER_UNPARSEABLE_URL'
    WHEN (SELECT COUNT(*) FROM s2_url_lookalike l
           WHERE NOT EXISTS (SELECT 1 FROM s2_identity i WHERE i.id = l.id)) > 0
      THEN 'CONFLICT_NON_IDENTITY_LOOKALIKE'
    WHEN (SELECT COUNT(*) FROM s2_identity) = 1 THEN 'REUSABLE'
    ELSE 'ABSENT'
  END AS source_identity_state;

WITH
-- BEGIN nsrc_000006_source_identity
-- Byte-identical in every nsrc_000006_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000006_g7_source_identity_sql.py).
-- S2 and S3 are independent importer identities; neither is ever matched approximately.
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
-- S2 importer semantic identity: same source_type, non-empty url, same normalized URL
s2_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'tourism_official'
    AND url <> ''
    AND normalized_url = 'https://sado-geinou.com/geinou/kamoutashiro'
),
-- S2 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s2_metadata_compatible AS (
  SELECT *
  FROM s2_identity
  WHERE btrim(COALESCE(publisher, '')) = '佐渡芸能アーカイブ'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S2 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s2_identity)
s2_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%sado-geinou.com%' AND lower(url) LIKE '%geinou%kamoutashiro%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%sado-geinou.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%geinou%kamoutashiro%')
),
-- S3 importer semantic identity: same source_type, non-empty url, same normalized URL
s3_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'local_history'
    AND url <> ''
    AND normalized_url = 'https://dl.ndl.go.jp/pid/971197'
),
-- S3 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s3_metadata_compatible AS (
  SELECT *
  FROM s3_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟県神職会佐渡支部'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S3 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s3_identity)
s3_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%dl.ndl.go.jp%' AND lower(url) LIKE '%pid%971197%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%dl.ndl.go.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%pid%971197%')
)
-- END nsrc_000006_source_identity
SELECT
  'S3' AS source_label,
  'local_history' AS source_type,
  'https://dl.ndl.go.jp/pid/971197' AS normalized_url,
  (SELECT COUNT(*) FROM s3_identity) AS source_identity_count,
  (SELECT COUNT(*) FROM s3_metadata_compatible) AS source_metadata_compatible_count,
  (SELECT COUNT(*) FROM s3_url_lookalike) AS source_url_lookalike_count,
  (SELECT COUNT(*) FROM s3_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM s3_identity i WHERE i.id = l.id)) AS source_url_lookalike_non_identity_count,
  (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'local_history' AND url <> '' AND normalized_url IS NULL) AS source_type_url_unparseable_count,
  CASE
    WHEN (SELECT COUNT(*) FROM s3_identity) > 1 THEN 'CONFLICT_IDENTITY_AMBIGUOUS'
    WHEN (SELECT COUNT(*) FROM s3_identity) = 1
     AND (SELECT COUNT(*) FROM s3_metadata_compatible) = 0 THEN 'CONFLICT_METADATA_DRIFT'
    WHEN (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'local_history' AND url <> '' AND normalized_url IS NULL) > 0
      THEN 'CONFLICT_IMPORTER_UNPARSEABLE_URL'
    WHEN (SELECT COUNT(*) FROM s3_url_lookalike l
           WHERE NOT EXISTS (SELECT 1 FROM s3_identity i WHERE i.id = l.id)) > 0
      THEN 'CONFLICT_NON_IDENTITY_LOOKALIKE'
    WHEN (SELECT COUNT(*) FROM s3_identity) = 1 THEN 'REUSABLE'
    ELSE 'ABSENT'
  END AS source_identity_state;

SELECT
  d.id,
  d.shrine_id,
  d.display_name,
  d.role,
  d.verification_status,
  d.confidence
FROM temples_shrinedeity d
JOIN temples_shrine s ON s.id = d.shrine_id
WHERE s.name_jp = '赤井神社'
  AND s.address = '新潟県佐渡市加茂歌代2662番地'
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
WHERE s.name_jp = '赤井神社'
  AND s.address = '新潟県佐渡市加茂歌代2662番地'
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
WHERE s.name_jp = '赤井神社'
  AND s.address = '新潟県佐渡市加茂歌代2662番地'
ORDER BY hs.shrinehistory_id, hs.shrineknowledgesource_id;

SELECT
  sf.id,
  sf.shrine_id,
  sf.stable_key,
  sf.verification_status,
  sf.confidence
FROM temples_shrinesourcefact sf
JOIN temples_shrine s ON s.id = sf.shrine_id
WHERE s.name_jp = '赤井神社'
  AND s.address = '新潟県佐渡市加茂歌代2662番地'
ORDER BY sf.id;

WITH
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '赤井神社'
    AND address = '新潟県佐渡市加茂歌代2662番地'
)
SELECT
  (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS target_collectives,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS target_goriyaku_tag_links,
  (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS target_goriyaku_assignments;

-- State class candidate (CLEAN_CREATE / ALREADY_MATERIALIZED / PARTIAL_EXISTING / CONFLICT).
-- Any CONFLICT_* Source state, target identity ambiguity, same-address collision, or
-- unexpected target Knowledge is CONFLICT. Mother Ship confirms the class; this query
-- does not authorize any write.
WITH
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '赤井神社'
    AND address = '新潟県佐渡市加茂歌代2662番地'
),
-- BEGIN nsrc_000006_source_identity
-- Byte-identical in every nsrc_000006_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000006_g7_source_identity_sql.py).
-- S2 and S3 are independent importer identities; neither is ever matched approximately.
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
-- S2 importer semantic identity: same source_type, non-empty url, same normalized URL
s2_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'tourism_official'
    AND url <> ''
    AND normalized_url = 'https://sado-geinou.com/geinou/kamoutashiro'
),
-- S2 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s2_metadata_compatible AS (
  SELECT *
  FROM s2_identity
  WHERE btrim(COALESCE(publisher, '')) = '佐渡芸能アーカイブ'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S2 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s2_identity)
s2_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%sado-geinou.com%' AND lower(url) LIKE '%geinou%kamoutashiro%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%sado-geinou.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%geinou%kamoutashiro%')
),
-- S3 importer semantic identity: same source_type, non-empty url, same normalized URL
s3_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'local_history'
    AND url <> ''
    AND normalized_url = 'https://dl.ndl.go.jp/pid/971197'
),
-- S3 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s3_metadata_compatible AS (
  SELECT *
  FROM s3_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟県神職会佐渡支部'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S3 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s3_identity)
s3_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%dl.ndl.go.jp%' AND lower(url) LIKE '%pid%971197%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%dl.ndl.go.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%pid%971197%')
)
-- END nsrc_000006_source_identity
,
counts AS (
  SELECT
    (SELECT COUNT(*) FROM target) AS target_exact,
    (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県佐渡市加茂歌代2662番地') AS same_address,
    (SELECT COUNT(*) FROM s2_identity) AS s2_identity,
    (SELECT COUNT(*) FROM s2_metadata_compatible) AS s2_compatible,
    (SELECT COUNT(*) FROM s2_url_lookalike l
       WHERE NOT EXISTS (SELECT 1 FROM s2_identity i WHERE i.id = l.id)) AS s2_lookalike_non_identity,
    (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'tourism_official' AND url <> '' AND normalized_url IS NULL) AS s2_unparseable,
    (SELECT COUNT(*) FROM s3_identity) AS s3_identity,
    (SELECT COUNT(*) FROM s3_metadata_compatible) AS s3_compatible,
    (SELECT COUNT(*) FROM s3_url_lookalike l
       WHERE NOT EXISTS (SELECT 1 FROM s3_identity i WHERE i.id = l.id)) AS s3_lookalike_non_identity,
    (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'local_history' AND url <> '' AND normalized_url IS NULL) AS s3_unparseable,
    (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) AS deity,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) AS source_fact,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS collective,
    (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) AS history,
    (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id
       WHERE h.history_type = 'regional_context' AND h.title = '4月16日の赤井神社例祭と鬼太鼓奉納'
          AND h.period_text = '' AND h.event_date IS NULL
          AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS h1_expected,
    (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id
       WHERE h.history_type = 'tradition' AND h.title = '元日午前0時の鬼太鼓奉納'
          AND h.period_text = '' AND h.event_date IS NULL
          AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS h2_expected,
    (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id
       WHERE h.history_type = 'regional_context' AND h.title = '加茂の五神社としての記録'
          AND h.period_text = '' AND h.event_date IS NULL
          AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS h3_expected,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
       JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
       JOIN target t ON t.id = h.shrine_id) AS history_relations,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        WHERE h.title = '4月16日の赤井神社例祭と鬼太鼓奉納') AS h1_relations,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        JOIN s2_metadata_compatible cs ON cs.id = hs.shrineknowledgesource_id
        WHERE h.title = '4月16日の赤井神社例祭と鬼太鼓奉納') AS h1_relations_s2,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        WHERE h.title = '元日午前0時の鬼太鼓奉納') AS h2_relations,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        JOIN s2_metadata_compatible cs ON cs.id = hs.shrineknowledgesource_id
        WHERE h.title = '元日午前0時の鬼太鼓奉納') AS h2_relations_s2,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        WHERE h.title = '加茂の五神社としての記録') AS h3_relations,
    (SELECT COUNT(*) FROM temples_shrinehistory_sources hs
        JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
        JOIN target t ON t.id = h.shrine_id
        JOIN s3_metadata_compatible cs ON cs.id = hs.shrineknowledgesource_id
        WHERE h.title = '加茂の五神社としての記録') AS h3_relations_s3,
    (SELECT COUNT(*) FROM target
       WHERE abs(latitude - 38.085938) < 0.00000001
         AND abs(longitude - 138.418312) < 0.00000001) AS coordinate_ok,
    (SELECT COUNT(*) FROM target WHERE COALESCE(goriyaku, '') = '') AS goriyaku_empty,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS goriyaku_tags,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS goriyaku_assignments
)
SELECT
  CASE
    WHEN s2_identity > 1 OR (s2_identity = 1 AND s2_compatible = 0)
      OR s2_unparseable > 0 OR s2_lookalike_non_identity > 0
      OR s3_identity > 1 OR (s3_identity = 1 AND s3_compatible = 0)
      OR s3_unparseable > 0 OR s3_lookalike_non_identity > 0
      OR target_exact > 1
      OR same_address <> target_exact
      THEN 'CONFLICT'
    WHEN target_exact = 0 THEN 'CLEAN_CREATE'
    WHEN deity > 0 OR source_fact > 0 OR collective > 0 OR history > 3
      OR (history >= 1 AND h1_expected + h2_expected + h3_expected <> history)
      OR coordinate_ok = 0 OR goriyaku_empty = 0 OR goriyaku_tags > 0 OR goriyaku_assignments > 0
      THEN 'CONFLICT'
    WHEN history = 3 AND h1_expected = 1 AND h2_expected = 1 AND h3_expected = 1
      AND history_relations = 3
      AND h1_relations = 1 AND h1_relations_s2 = 1
      AND h2_relations = 1 AND h2_relations_s2 = 1
      AND h3_relations = 1 AND h3_relations_s3 = 1
      AND s2_identity = 1 AND s2_compatible = 1 AND s3_identity = 1 AND s3_compatible = 1
      THEN 'ALREADY_MATERIALIZED'
    ELSE 'PARTIAL_EXISTING'
  END AS production_state_class_candidate,
  s2_identity AS s2_source_identity_count,
  s2_compatible AS s2_source_metadata_compatible_count,
  s3_identity AS s3_source_identity_count,
  s3_compatible AS s3_source_metadata_compatible_count
FROM counts;
