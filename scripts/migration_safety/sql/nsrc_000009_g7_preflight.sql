-- nsrc-000009 赤城社 G7 Production Import Gate — read-only preflight
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.
--
-- Canonical target = exact (name_jp, address): 赤城社 / 新潟県十日町市伊達乙48番地.
-- H002 has other distinct shrines named 赤城社 (e.g. nsrc-000007 at 新潟県十日町市四日町2534番地);
-- same-name rows are diagnostics only and never identify the target.
--
-- Shared Source identity is the importer's semantic identity only
-- (knowledge_seed.resolve_source_identity(): source_type + normalize_source_url()):
--   TOKAMACHI_REKIBUN_SHIRYOU = government + https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf
-- Three separate concepts:
--   source_identity_count            exact importer identity (the only reusable rows)
--   source_metadata_compatible_count identity rows whose _SOURCE_REUSE_FIELDS match the seed
--   source_url_lookalike_count       broad diagnostic match; never reusable by itself
--
-- Fact locator: ShrineFactSourceCitation (table temples_shrinefactsourcecitation, migration
-- temples 0121_shrine_fact_source_citation). If that migration is not applied, the citation
-- table does not exist and every statement after the table-existence check fails (fail closed).

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
    WHERE name_jp = '赤城社'
      AND address = '新潟県十日町市伊達乙48番地'
  ) AS target_exact_count,
  COUNT(*) FILTER (WHERE name_jp = '赤城社') AS same_name_akagi_count,
  COUNT(*) FILTER (WHERE name_jp = '赤城社' AND address <> '新潟県十日町市伊達乙48番地') AS same_name_other_address_count,
  COUNT(*) FILTER (WHERE address = '新潟県十日町市伊達乙48番地') AS same_address_count
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
  (name_jp = '赤城社' AND address = '新潟県十日町市伊達乙48番地') AS is_canonical_target
FROM temples_shrine
WHERE name_jp = '赤城社'
   OR address = '新潟県十日町市伊達乙48番地'
ORDER BY id;

WITH
-- BEGIN nsrc_000009_source_identity
-- Byte-identical in every nsrc_000009_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py).
-- One shared municipal Source (TOKAMACHI_REKIBUN_SHIRYOU). It may already exist through
-- nsrc-000007; that is measured, never assumed, and never matched approximately.
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
-- Shared Source importer semantic identity: same source_type, non-empty url, same normalized URL
shared_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf'
),
-- Shared Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). bibliography stays the legacy nsrc-000007
-- value p.398; the nsrc-000009 Fact locator p.445 lives only in ShrineFactSourceCitation.
shared_metadata_compatible AS (
  SELECT *
  FROM shared_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Shared Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of shared_identity)
shared_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.tokamachi.lg.jp%' AND lower(url) LIKE '%rekibun_shiryou%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.tokamachi.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%rekibun_shiryou%')
)
-- END nsrc_000009_source_identity
SELECT
  'TOKAMACHI_REKIBUN_SHIRYOU' AS source_key,
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
  EXISTS (SELECT 1 FROM shared_identity i WHERE i.id = l.id) AS is_source_identity,
  EXISTS (SELECT 1 FROM shared_metadata_compatible m WHERE m.id = l.id) AS is_metadata_compatible
FROM shared_url_lookalike l
ORDER BY l.id;

WITH
-- BEGIN nsrc_000009_source_identity
-- Byte-identical in every nsrc_000009_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py).
-- One shared municipal Source (TOKAMACHI_REKIBUN_SHIRYOU). It may already exist through
-- nsrc-000007; that is measured, never assumed, and never matched approximately.
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
-- Shared Source importer semantic identity: same source_type, non-empty url, same normalized URL
shared_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf'
),
-- Shared Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). bibliography stays the legacy nsrc-000007
-- value p.398; the nsrc-000009 Fact locator p.445 lives only in ShrineFactSourceCitation.
shared_metadata_compatible AS (
  SELECT *
  FROM shared_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Shared Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of shared_identity)
shared_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.tokamachi.lg.jp%' AND lower(url) LIKE '%rekibun_shiryou%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.tokamachi.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%rekibun_shiryou%')
)
-- END nsrc_000009_source_identity
SELECT
  'TOKAMACHI_REKIBUN_SHIRYOU' AS source_key,
  'government' AS source_type,
  'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf' AS normalized_url,
  (SELECT COUNT(*) FROM shared_identity) AS source_identity_count,
  (SELECT COUNT(*) FROM shared_metadata_compatible) AS source_metadata_compatible_count,
  (SELECT COUNT(*) FROM shared_url_lookalike) AS source_url_lookalike_count,
  (SELECT COUNT(*) FROM shared_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM shared_identity i WHERE i.id = l.id)) AS source_url_lookalike_non_identity_count,
  (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) AS source_type_url_unparseable_count,
  CASE
    WHEN (SELECT COUNT(*) FROM shared_identity) > 1 THEN 'CONFLICT_IDENTITY_AMBIGUOUS'
    WHEN (SELECT COUNT(*) FROM shared_identity) = 1
     AND (SELECT COUNT(*) FROM shared_metadata_compatible) = 0 THEN 'CONFLICT_METADATA_DRIFT'
    WHEN (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) > 0
      THEN 'CONFLICT_IMPORTER_UNPARSEABLE_URL'
    WHEN (SELECT COUNT(*) FROM shared_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM shared_identity i WHERE i.id = l.id)) > 0
      THEN 'CONFLICT_NON_IDENTITY_LOOKALIKE'
    WHEN (SELECT COUNT(*) FROM shared_identity) = 1 THEN 'REUSABLE'
    ELSE 'ABSENT'
  END AS source_identity_state;

-- Diagnostics only: every Fact citation that points at a shared-Source lookalike row
-- (e.g. other shrines' citations of the same municipal PDF). Never authorizes anything.
WITH
-- BEGIN nsrc_000009_source_identity
-- Byte-identical in every nsrc_000009_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py).
-- One shared municipal Source (TOKAMACHI_REKIBUN_SHIRYOU). It may already exist through
-- nsrc-000007; that is measured, never assumed, and never matched approximately.
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
-- Shared Source importer semantic identity: same source_type, non-empty url, same normalized URL
shared_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf'
),
-- Shared Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). bibliography stays the legacy nsrc-000007
-- value p.398; the nsrc-000009 Fact locator p.445 lives only in ShrineFactSourceCitation.
shared_metadata_compatible AS (
  SELECT *
  FROM shared_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Shared Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of shared_identity)
shared_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.tokamachi.lg.jp%' AND lower(url) LIKE '%rekibun_shiryou%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.tokamachi.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%rekibun_shiryou%')
)
-- END nsrc_000009_source_identity
SELECT
  c.id,
  c.source_id,
  c.shrine_history_id,
  c.shrine_deity_id,
  c.locator_text,
  COALESCE(sh.name_jp, sd.name_jp) AS shrine_name_jp,
  COALESCE(sh.address, sd.address) AS shrine_address,
  EXISTS (SELECT 1 FROM shared_metadata_compatible m WHERE m.id = c.source_id) AS cites_shared_compatible_source
FROM temples_shrinefactsourcecitation c
LEFT JOIN temples_shrinehistory h ON h.id = c.shrine_history_id
LEFT JOIN temples_shrine sh ON sh.id = h.shrine_id
LEFT JOIN temples_shrinedeity d ON d.id = c.shrine_deity_id
LEFT JOIN temples_shrine sd ON sd.id = d.shrine_id
WHERE c.source_id IN (SELECT id FROM shared_url_lookalike)
ORDER BY c.id;

SELECT
  d.id,
  d.shrine_id,
  d.display_name,
  d.role,
  d.verification_status,
  d.confidence
FROM temples_shrinedeity d
JOIN temples_shrine s ON s.id = d.shrine_id
WHERE s.name_jp = '赤城社'
  AND s.address = '新潟県十日町市伊達乙48番地'
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
WHERE s.name_jp = '赤城社'
  AND s.address = '新潟県十日町市伊達乙48番地'
ORDER BY h.id;

SELECT
  hs.shrinehistory_id,
  hs.shrineknowledgesource_id,
  src.source_type,
  src.url,
  src.bibliography,
  src.verification_status
FROM temples_shrinehistory_sources hs
JOIN temples_shrinehistory h ON h.id = hs.shrinehistory_id
JOIN temples_shrine s ON s.id = h.shrine_id
JOIN temples_shrineknowledgesource src ON src.id = hs.shrineknowledgesource_id
WHERE s.name_jp = '赤城社'
  AND s.address = '新潟県十日町市伊達乙48番地'
ORDER BY hs.shrinehistory_id, hs.shrineknowledgesource_id;

WITH
-- BEGIN nsrc_000009_source_identity
-- Byte-identical in every nsrc_000009_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py).
-- One shared municipal Source (TOKAMACHI_REKIBUN_SHIRYOU). It may already exist through
-- nsrc-000007; that is measured, never assumed, and never matched approximately.
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
-- Shared Source importer semantic identity: same source_type, non-empty url, same normalized URL
shared_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf'
),
-- Shared Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). bibliography stays the legacy nsrc-000007
-- value p.398; the nsrc-000009 Fact locator p.445 lives only in ShrineFactSourceCitation.
shared_metadata_compatible AS (
  SELECT *
  FROM shared_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Shared Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of shared_identity)
shared_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.tokamachi.lg.jp%' AND lower(url) LIKE '%rekibun_shiryou%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.tokamachi.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%rekibun_shiryou%')
)
-- END nsrc_000009_source_identity
,
-- BEGIN nsrc_000009_target_facts
-- Byte-identical in every nsrc_000009_g7_*.sql file that contains it. Requires the
-- nsrc_000009_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '赤城社'
    AND address = '新潟県十日町市伊達乙48番地'
),
target_deity AS (
  SELECT d.id
  FROM temples_shrinedeity d
  JOIN target t ON t.id = d.shrine_id
),
-- is_h1 / is_h2 = every frozen H1 / H2 field equal (no approximate match)
target_history AS (
  SELECT
    h.id,
    (h.history_type = 'historical_event' AND h.title = '天明3年8月の創立記録'
       AND h.content = '赤城社は天明3年8月に創立されたと記録されている。'
       AND h.period_text = '天明3年8月' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS is_h1,
    (h.history_type = 'historical_event' AND h.title = '大正2年の改築記録'
       AND h.content = '赤城社は大正2年に改築されたと記録されている。'
       AND h.period_text = '大正2年' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS is_h2
  FROM temples_shrinehistory h
  JOIN target t ON t.id = h.shrine_id
),
-- every History-Source relation of a target History
target_relation AS (
  SELECT
    hs.shrinehistory_id,
    hs.shrineknowledgesource_id,
    EXISTS (SELECT 1 FROM shared_metadata_compatible cs
             WHERE cs.id = hs.shrineknowledgesource_id) AS to_shared
  FROM temples_shrinehistory_sources hs
  JOIN target_history th ON th.id = hs.shrinehistory_id
),
-- every ShrineFactSourceCitation of a target History or target Deity
-- expected = shared compatible Source, exact locator, and that Source is already one of the
-- History's own M2M sources (citation Source matches the related Source)
target_citation AS (
  SELECT
    c.id,
    c.shrine_history_id,
    c.shrine_deity_id,
    c.source_id,
    c.locator_text,
    (c.shrine_history_id IS NOT NULL
     AND c.locator_text = '中魚沼郡誌上 p.445'
     AND EXISTS (SELECT 1 FROM shared_metadata_compatible cs WHERE cs.id = c.source_id)
     AND EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs
                  WHERE hs.shrinehistory_id = c.shrine_history_id
                    AND hs.shrineknowledgesource_id = c.source_id)) AS is_expected
  FROM temples_shrinefactsourcecitation c
  WHERE c.shrine_history_id IN (SELECT id FROM target_history)
     OR c.shrine_deity_id IN (SELECT id FROM target_deity)
)
-- END nsrc_000009_target_facts
SELECT
  tc.id,
  tc.shrine_history_id,
  tc.shrine_deity_id,
  h.title AS history_title,
  tc.source_id,
  src.source_type,
  src.url,
  src.bibliography AS source_bibliography,
  tc.locator_text,
  tc.is_expected
FROM target_citation tc
LEFT JOIN temples_shrinehistory h ON h.id = tc.shrine_history_id
JOIN temples_shrineknowledgesource src ON src.id = tc.source_id
ORDER BY tc.id;

SELECT
  sf.id,
  sf.shrine_id,
  sf.stable_key,
  sf.verification_status,
  sf.confidence
FROM temples_shrinesourcefact sf
JOIN temples_shrine s ON s.id = sf.shrine_id
WHERE s.name_jp = '赤城社'
  AND s.address = '新潟県十日町市伊達乙48番地'
ORDER BY sf.id;

WITH
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '赤城社'
    AND address = '新潟県十日町市伊達乙48番地'
)
SELECT
  (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS target_collectives,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS target_goriyaku_tag_links,
  (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS target_goriyaku_assignments;

-- State class candidate (CLEAN_CREATE / ALREADY_MATERIALIZED / PARTIAL_EXISTING / CONFLICT).
-- Any CONFLICT_* Source state, target identity ambiguity, same-address collision, or
-- unexpected target Knowledge / relation / citation is CONFLICT. Mother Ship confirms the
-- class; this query does not authorize any write.
WITH
-- BEGIN nsrc_000009_source_identity
-- Byte-identical in every nsrc_000009_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py).
-- One shared municipal Source (TOKAMACHI_REKIBUN_SHIRYOU). It may already exist through
-- nsrc-000007; that is measured, never assumed, and never matched approximately.
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
-- Shared Source importer semantic identity: same source_type, non-empty url, same normalized URL
shared_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf'
),
-- Shared Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). bibliography stays the legacy nsrc-000007
-- value p.398; the nsrc-000009 Fact locator p.445 lives only in ShrineFactSourceCitation.
shared_metadata_compatible AS (
  SELECT *
  FROM shared_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- Shared Source diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of shared_identity)
shared_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.tokamachi.lg.jp%' AND lower(url) LIKE '%rekibun_shiryou%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.tokamachi.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%rekibun_shiryou%')
)
-- END nsrc_000009_source_identity
,
-- BEGIN nsrc_000009_target_facts
-- Byte-identical in every nsrc_000009_g7_*.sql file that contains it. Requires the
-- nsrc_000009_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '赤城社'
    AND address = '新潟県十日町市伊達乙48番地'
),
target_deity AS (
  SELECT d.id
  FROM temples_shrinedeity d
  JOIN target t ON t.id = d.shrine_id
),
-- is_h1 / is_h2 = every frozen H1 / H2 field equal (no approximate match)
target_history AS (
  SELECT
    h.id,
    (h.history_type = 'historical_event' AND h.title = '天明3年8月の創立記録'
       AND h.content = '赤城社は天明3年8月に創立されたと記録されている。'
       AND h.period_text = '天明3年8月' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS is_h1,
    (h.history_type = 'historical_event' AND h.title = '大正2年の改築記録'
       AND h.content = '赤城社は大正2年に改築されたと記録されている。'
       AND h.period_text = '大正2年' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high') AS is_h2
  FROM temples_shrinehistory h
  JOIN target t ON t.id = h.shrine_id
),
-- every History-Source relation of a target History
target_relation AS (
  SELECT
    hs.shrinehistory_id,
    hs.shrineknowledgesource_id,
    EXISTS (SELECT 1 FROM shared_metadata_compatible cs
             WHERE cs.id = hs.shrineknowledgesource_id) AS to_shared
  FROM temples_shrinehistory_sources hs
  JOIN target_history th ON th.id = hs.shrinehistory_id
),
-- every ShrineFactSourceCitation of a target History or target Deity
-- expected = shared compatible Source, exact locator, and that Source is already one of the
-- History's own M2M sources (citation Source matches the related Source)
target_citation AS (
  SELECT
    c.id,
    c.shrine_history_id,
    c.shrine_deity_id,
    c.source_id,
    c.locator_text,
    (c.shrine_history_id IS NOT NULL
     AND c.locator_text = '中魚沼郡誌上 p.445'
     AND EXISTS (SELECT 1 FROM shared_metadata_compatible cs WHERE cs.id = c.source_id)
     AND EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs
                  WHERE hs.shrinehistory_id = c.shrine_history_id
                    AND hs.shrineknowledgesource_id = c.source_id)) AS is_expected
  FROM temples_shrinefactsourcecitation c
  WHERE c.shrine_history_id IN (SELECT id FROM target_history)
     OR c.shrine_deity_id IN (SELECT id FROM target_deity)
)
-- END nsrc_000009_target_facts
,
counts AS (
  SELECT
    (SELECT COUNT(*) FROM target) AS target_exact,
    (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県十日町市伊達乙48番地') AS same_address,
    (SELECT COUNT(*) FROM shared_identity) AS shared_identity,
    (SELECT COUNT(*) FROM shared_metadata_compatible) AS shared_compatible,
    (SELECT COUNT(*) FROM shared_url_lookalike l
     WHERE NOT EXISTS (SELECT 1 FROM shared_identity i WHERE i.id = l.id)) AS shared_lookalike_non_identity,
    (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) AS shared_unparseable,
    (SELECT COUNT(*) FROM target_deity) AS deity,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) AS source_fact,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS collective,
    (SELECT COUNT(*) FROM target_history) AS history,
    (SELECT COUNT(*) FROM target_history WHERE is_h1) AS h1_expected,
    (SELECT COUNT(*) FROM target_history WHERE is_h2) AS h2_expected,
    (SELECT COUNT(*) FROM target_relation) AS relations,
    (SELECT COUNT(*) FROM target_relation WHERE NOT to_shared) AS relations_not_shared,
    (SELECT COUNT(*) FROM target_relation r JOIN target_history th ON th.id = r.shrinehistory_id
       WHERE th.is_h1 AND r.to_shared) AS h1_relations_shared,
    (SELECT COUNT(*) FROM target_relation r JOIN target_history th ON th.id = r.shrinehistory_id
       WHERE th.is_h2 AND r.to_shared) AS h2_relations_shared,
    (SELECT COUNT(*) FROM target_citation) AS citations,
    (SELECT COUNT(*) FROM target_citation WHERE NOT is_expected) AS citations_unexpected,
    (SELECT COUNT(*) FROM target_citation c JOIN target_history th ON th.id = c.shrine_history_id
       WHERE th.is_h1 AND c.is_expected) AS h1_citations_expected,
    (SELECT COUNT(*) FROM target_citation c JOIN target_history th ON th.id = c.shrine_history_id
       WHERE th.is_h2 AND c.is_expected) AS h2_citations_expected,
    (SELECT COUNT(*) FROM target
       WHERE abs(latitude - 37.089683) < 0.00000001
         AND abs(longitude - 138.748108) < 0.00000001) AS coordinate_ok,
    (SELECT COUNT(*) FROM target WHERE COALESCE(goriyaku, '') = '') AS goriyaku_empty,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) AS goriyaku_tags,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) AS goriyaku_assignments
)
SELECT
  CASE
    WHEN shared_identity > 1 OR (shared_identity = 1 AND shared_compatible = 0)
      OR shared_unparseable > 0 OR shared_lookalike_non_identity > 0
      OR target_exact > 1
      OR same_address <> target_exact
      THEN 'CONFLICT'
    WHEN target_exact = 0 THEN 'CLEAN_CREATE'
    WHEN deity > 0 OR source_fact > 0 OR collective > 0 OR history > 2
      OR h1_expected > 1 OR h2_expected > 1
      OR (history >= 1 AND h1_expected + h2_expected <> history)
      OR relations_not_shared > 0
      OR citations_unexpected > 0
      OR coordinate_ok = 0 OR goriyaku_empty = 0 OR goriyaku_tags > 0 OR goriyaku_assignments > 0
      THEN 'CONFLICT'
    WHEN history = 2 AND h1_expected = 1 AND h2_expected = 1
      AND relations = 2 AND h1_relations_shared = 1 AND h2_relations_shared = 1
      AND citations = 2 AND h1_citations_expected = 1 AND h2_citations_expected = 1
      AND shared_identity = 1 AND shared_compatible = 1
      THEN 'ALREADY_MATERIALIZED'
    ELSE 'PARTIAL_EXISTING'
  END AS production_state_class_candidate,
  shared_identity AS shared_source_identity_count,
  shared_compatible AS shared_source_metadata_compatible_count,
  target_exact AS target_exact_count,
  history AS target_history_count,
  relations AS target_history_source_relation_count,
  citations AS target_citation_count
FROM counts;
