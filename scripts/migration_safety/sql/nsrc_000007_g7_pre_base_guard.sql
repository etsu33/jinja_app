-- nsrc-000007 G7 pre-Base Production write guard
-- SELECT-only; raises division-by-zero unless the frozen CLEAN_CREATE pre-state still holds.
-- Frozen values = Mother Ship Production read-only measurement (see the frozen block).
-- Expected pre-state (CLEAN_CREATE only; other states never reach this guard):
--   aggregates (Shrine / Source / Deity / History / SourceFact / Collective) = frozen
--   target exact = 0; same-address = 0; 赤城社 at other addresses = frozen (diagnostic, no drift)
--   per S2 / S3: identity = compatible = lookalike = frozen accepted count (0 or 1);
--   no importer-unparseable URL of that source_type
-- No Production numeric PK is referenced.
WITH
-- BEGIN nsrc_000007_frozen_pre_state
frozen AS (
  -- FROZEN_PRE_STATE: measured by nsrc_000007_g7_preflight.sql on Production (read-only),
  -- executed by Mother Ship through readonly_query.sh after PR #3193,
  -- PostgreSQL 17.6, temples 0120_shrine_source_fact_foundation.
  -- Mother Ship decision: G7_READ_ONLY_PREFLIGHT = PASS / PRODUCTION_STATE_CLASS = CLEAN_CREATE
  -- (S2 source_identity_state = ABSENT, S3 source_identity_state = ABSENT).
  -- Any drift from these values fails closed.
  -- The block must be identical in the pre-Base / post-Base / post-Knowledge files.
  SELECT
    true AS frozen_values_set,
    122::bigint AS shrine_total,
    141::bigint AS source_total,
    295::bigint AS deity_total,
    229::bigint AS history_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- 赤城社 rows at other addresses (distinct shrines; frozen only to detect drift)
    0::bigint AS same_name_other_address_total,
    -- = measured S2 / S3 source_identity_count; only 0 (absent) or 1 (metadata compatible)
    0::bigint AS s2_accepted_source_count,
    0::bigint AS s3_accepted_source_count
),
-- END nsrc_000007_frozen_pre_state
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '赤城社'
    AND address = '新潟県十日町市四日町2534番地'
),
-- BEGIN nsrc_000007_source_identity
-- Byte-identical in every nsrc_000007_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000007_g7_source_identity_sql.py).
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
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf'
),
-- S2 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s2_metadata_compatible AS (
  SELECT *
  FROM s2_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S2 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s2_identity)
s2_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%city.tokamachi.lg.jp%' AND lower(url) LIKE '%rekibun_shiryou%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.tokamachi.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%rekibun_shiryou%')
),
-- S3 importer semantic identity: same source_type, non-empty url, same normalized URL
s3_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'museum_or_archive'
    AND url <> ''
    AND normalized_url = 'https://www.tokamachi-museum.jp/archives/bunka023'
),
-- S3 importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
s3_metadata_compatible AS (
  SELECT *
  FROM s3_identity
  WHERE btrim(COALESCE(publisher, '')) = '十日町市博物館'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- S3 diagnostic only (never reusable): any source_type, case-insensitive host + path
-- substring on the raw or normalized URL (always a superset of s3_identity)
s3_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%tokamachi-museum.jp%' AND lower(url) LIKE '%archives%bunka023%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%tokamachi-museum.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%archives%bunka023%')
)
-- END nsrc_000007_source_identity
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND (SELECT COUNT(*) FROM temples_shrine) = f.shrine_total
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective) = f.collective_total
  AND (SELECT COUNT(*) FROM target) = 0
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県十日町市四日町2534番地') = 0
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '赤城社' AND address <> '新潟県十日町市四日町2534番地') = f.same_name_other_address_total
  AND f.s2_accepted_source_count IN (0, 1)
  AND f.s3_accepted_source_count IN (0, 1)
  AND (SELECT COUNT(*) FROM s2_identity) = f.s2_accepted_source_count
  AND (SELECT COUNT(*) FROM s2_metadata_compatible) = f.s2_accepted_source_count
  AND (SELECT COUNT(*) FROM s2_url_lookalike) = f.s2_accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM s3_identity) = f.s3_accepted_source_count
  AND (SELECT COUNT(*) FROM s3_metadata_compatible) = f.s3_accepted_source_count
  AND (SELECT COUNT(*) FROM s3_url_lookalike) = f.s3_accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'museum_or_archive' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS g7_pre_base_guard_pass
FROM frozen f;
