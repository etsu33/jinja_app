-- nsrc-000002 G7 post-Base / pre-Knowledge Production guard
-- SELECT-only; raises division-by-zero unless exactly the single target Base row was added.
-- Expected: Shrine = frozen + 1, every Knowledge aggregate unchanged, target Knowledge 0,
-- canonical coordinate within 1e-8, goriyaku '' and 0 goriyaku tag links / assignments,
-- Source state unchanged from the frozen pre-state.
WITH
frozen AS (
  -- FROZEN_PRE_STATE: measured by nsrc_000002_g7_preflight.sql on Production (read-only),
  -- PostgreSQL 17.6, temples 0120_shrine_source_fact_foundation.
  -- Mother Ship decision: G7_READ_ONLY_PREFLIGHT = PASS / PRODUCTION_STATE_CLASS = CLEAN_CREATE
  -- (source_identity_state = ABSENT). Any drift from these values fails closed.
  -- The block must be identical in the pre-Base / post-Base / post-Knowledge files.
  SELECT
    121::bigint AS shrine_total,
    140::bigint AS source_total,
    295::bigint AS deity_total,
    228::bigint AS history_total,
    34::bigint AS source_fact_total,
    -- = measured source_identity_count; only 0 (absent) or 1 (metadata compatible) may proceed
    0::bigint AS accepted_source_count
),
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '青澤神社'
    AND address = '新潟県糸魚川市大字青海2696番地'
),
-- BEGIN nsrc_000002_source_identity
-- Byte-identical in every nsrc_000002_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000002_g7_source_identity_sql.py).
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
-- importer semantic identity: same source_type, non-empty url, same normalized URL
source_identity AS (
  SELECT *
  FROM source_url_norm
  WHERE source_type = 'government'
    AND url <> ''
    AND normalized_url = 'https://matsuri.geo-itoigawa.com/calendar/m04'
),
-- importer reuse rule: every _SOURCE_REUSE_FIELDS value equal after strip()
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '糸魚川市 / 糸魚川ジオパーク協議会'
    AND btrim(COALESCE(verification_status, '')) = 'source_confirmed'
    AND btrim(COALESCE(confidence, '')) = 'high'
    AND btrim(COALESCE(bibliography, '')) = ''
    AND btrim(COALESCE(language, '')) = 'ja'
),
-- diagnostic only (never reusable): any source_type, case-insensitive host + path substring
-- on the raw or normalized URL (always a superset of source_identity)
source_url_lookalike AS (
  SELECT *
  FROM source_url_norm
  WHERE (lower(url) LIKE '%matsuri.geo-itoigawa.com%' AND lower(url) LIKE '%calendar%m04%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%matsuri.geo-itoigawa.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%calendar%m04%')
)
-- END nsrc_000002_source_identity
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
  AND f.accepted_source_count IN (0, 1)
  AND (SELECT COUNT(*) FROM source_identity) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM source_metadata_compatible) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_lookalike) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeity d JOIN target t ON t.id = d.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinehistory h JOIN target t ON t.id = h.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS g7_post_base_guard_pass
FROM frozen f;
