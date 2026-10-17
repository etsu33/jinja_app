-- nsrc-000009 G7 post-Base / pre-Knowledge Production guard
-- SELECT-only; raises division-by-zero unless exactly the single target Base row was added.
-- Frozen values = Mother Ship Production read-only measurement (see the frozen block).
-- Expected: Shrine = frozen + 1, every other aggregate (Knowledge and Citation) unchanged,
-- target exact = 1, same-address = 1, 赤城社 at other addresses unchanged, canonical coordinate
-- 37.089683 / 138.748108 within 1e-8, goriyaku '' with 0 goriyaku tag links / assignments,
-- target Knowledge / relations / citations still absent, shared Source state unchanged.
WITH
-- BEGIN nsrc_000009_frozen_pre_state
frozen AS (
  -- FROZEN_PRE_STATE: measured by nsrc_000009_g7_preflight.sql on Production (read-only),
  -- executed by Mother Ship through readonly_query.sh after PR #3237 and the temples 0121 gate,
  -- temples 0121_shrine_fact_source_citation (temples_shrinefactsourcecitation exists, 0 rows).
  -- Mother Ship decision: PRODUCTION_STATE_CLASS = CLEAN_CREATE
  -- (shared Source source_identity_state = REUSABLE, accepted_shared_source_count = 1).
  -- Any drift from these values fails closed.
  -- The block must be identical in the pre-Base / post-Base / post-Knowledge files.
  SELECT
    true AS frozen_values_set,
    124::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    234::bigint AS history_total,
    0::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- 赤城社 rows at other addresses (distinct shrines, e.g. nsrc-000007; frozen only to detect drift)
    1::bigint AS same_name_other_address_total,
    -- = measured shared Source source_identity_count; only 0 (ABSENT) or 1 (REUSABLE)
    1::bigint AS accepted_shared_source_count
),
-- END nsrc_000009_frozen_pre_state
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
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND (SELECT COUNT(*) FROM temples_shrine) = f.shrine_total + 1
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total
  AND (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) = f.citation_total
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective) = f.collective_total
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県十日町市伊達乙48番地') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '赤城社' AND address <> '新潟県十日町市伊達乙48番地') = f.same_name_other_address_total
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.089683) < 0.00000001
          AND abs(longitude - 138.748108) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND f.accepted_shared_source_count IN (0, 1)
  AND (SELECT COUNT(*) FROM shared_identity) = f.accepted_shared_source_count
  AND (SELECT COUNT(*) FROM shared_metadata_compatible) = f.accepted_shared_source_count
  AND (SELECT COUNT(*) FROM shared_url_lookalike) = f.accepted_shared_source_count
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM target_deity) = 0
  AND (SELECT COUNT(*) FROM target_history) = 0
  AND (SELECT COUNT(*) FROM target_relation) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS g7_post_base_guard_pass
FROM frozen f;
