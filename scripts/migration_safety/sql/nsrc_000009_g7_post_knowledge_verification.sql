-- nsrc-000009 G7 post-Knowledge Production verification
-- SELECT-only. No credential / connection-target output. No Production numeric PK is referenced.
-- While the frozen block is UNSET (frozen_values_set = false, values NULL) it always fails.
-- Expected final delta from the frozen pre-state:
--   Shrine +1 / Source +(1 - accepted_shared_source_count) / Deity +0 / History +2
--   Citation +2 / SourceFact +0 / Collective +0
-- H1 and H2: exactly one Source relation each, to the same shared compatible Source; exactly one
-- ShrineFactSourceCitation each, citing that same Source with locator_text '中魚沼郡誌上 p.445'.
-- Shared Source: exactly one importer identity row, metadata compatible (bibliography stays the
-- legacy '中魚沼郡誌上 p.398'; it is never rewritten to p.445), no lookalike beyond it.
-- source-less History 0, no current Deity, goriyaku '' / tag links 0 / assignments 0.

SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) AS citation_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total,
  (SELECT COUNT(*) FROM temples_shrinedeitycollective) AS collective_total;

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
  (SELECT COUNT(*) FROM target) AS target_shrine,
  (SELECT COUNT(*) FROM target_deity) AS target_deity,
  (SELECT COUNT(*) FROM target_history) AS target_history,
  (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) AS target_source_fact,
  (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) AS target_collective,
  (SELECT COUNT(*) FROM target_relation) AS history_source_relations,
  (SELECT COUNT(*) FROM target_history h
     WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) AS sourceless_history,
  (SELECT COUNT(*) FROM target_citation) AS target_citations,
  (SELECT COUNT(*) FROM target_citation WHERE is_expected) AS target_citations_expected,
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
  src.bibliography AS source_bibliography,
  src.verification_status AS source_verification_status,
  src.confidence AS source_confidence,
  src.language AS source_language,
  c.locator_text AS citation_locator_text,
  (c.source_id = src.id) AS citation_source_matches_relation
FROM temples_shrinehistory h
JOIN temples_shrine s ON s.id = h.shrine_id
JOIN temples_shrinehistory_sources hs ON hs.shrinehistory_id = h.id
JOIN temples_shrineknowledgesource src ON src.id = hs.shrineknowledgesource_id
LEFT JOIN temples_shrinefactsourcecitation c ON c.shrine_history_id = h.id
WHERE s.name_jp = '赤城社'
  AND s.address = '新潟県十日町市伊達乙48番地'
ORDER BY h.title, src.url, c.locator_text;

WITH
-- BEGIN nsrc_000009_frozen_pre_state
frozen AS (
  -- FROZEN_PRE_STATE: UNSET.
  -- nsrc_000009_g7_preflight.sql has NOT been executed on Production and Mother Ship has
  -- not accepted a production_state_class. Every value is NULL and frozen_values_set is
  -- false, so this guard always fails closed (division by zero) until a separate,
  -- Mother-Ship-authorized change replaces this block with measured Production values.
  -- Repository or local counts must never be substituted for Production values.
  -- The block must be identical in the pre-Base / post-Base / post-Knowledge files.
  SELECT
    false AS frozen_values_set,
    NULL::bigint AS shrine_total,
    NULL::bigint AS source_total,
    NULL::bigint AS deity_total,
    NULL::bigint AS history_total,
    NULL::bigint AS citation_total,
    NULL::bigint AS source_fact_total,
    NULL::bigint AS collective_total,
    -- 赤城社 rows at other addresses (distinct shrines, e.g. nsrc-000007; frozen only to detect drift)
    NULL::bigint AS same_name_other_address_total,
    -- = measured shared Source source_identity_count; only 0 (ABSENT) or 1 (REUSABLE)
    NULL::bigint AS accepted_shared_source_count
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
  AND f.accepted_shared_source_count IN (0, 1)
  AND (SELECT COUNT(*) FROM temples_shrine) = f.shrine_total + 1
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total + (1 - f.accepted_shared_source_count)
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total + 2
  AND (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) = f.citation_total + 2
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective) = f.collective_total
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県十日町市伊達乙48番地') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '赤城社' AND address <> '新潟県十日町市伊達乙48番地') = f.same_name_other_address_total
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.089683) < 0.00000001
          AND abs(longitude - 138.748108) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND (SELECT COUNT(*) FROM target_deity) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM target_history) = 2
  AND (SELECT COUNT(*) FROM target_history WHERE is_h1) = 1
  AND (SELECT COUNT(*) FROM target_history WHERE is_h2) = 1
  AND (SELECT COUNT(*) FROM target_relation) = 2
  AND (SELECT COUNT(*) FROM target_relation WHERE NOT to_shared) = 0
  AND (SELECT COUNT(*) FROM target_relation r JOIN target_history th ON th.id = r.shrinehistory_id
        WHERE th.is_h1) = 1
  AND (SELECT COUNT(*) FROM target_relation r JOIN target_history th ON th.id = r.shrinehistory_id
        WHERE th.is_h1 AND r.to_shared) = 1
  AND (SELECT COUNT(*) FROM target_citation c JOIN target_history th ON th.id = c.shrine_history_id
        WHERE th.is_h1) = 1
  AND (SELECT COUNT(*) FROM target_citation c JOIN target_history th ON th.id = c.shrine_history_id
        WHERE th.is_h1 AND c.is_expected) = 1
  AND (SELECT COUNT(*) FROM target_relation r JOIN target_history th ON th.id = r.shrinehistory_id
        WHERE th.is_h2) = 1
  AND (SELECT COUNT(*) FROM target_relation r JOIN target_history th ON th.id = r.shrinehistory_id
        WHERE th.is_h2 AND r.to_shared) = 1
  AND (SELECT COUNT(*) FROM target_citation c JOIN target_history th ON th.id = c.shrine_history_id
        WHERE th.is_h2) = 1
  AND (SELECT COUNT(*) FROM target_citation c JOIN target_history th ON th.id = c.shrine_history_id
        WHERE th.is_h2 AND c.is_expected) = 1
  AND (SELECT COUNT(*) FROM target_history h
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 2
  AND (SELECT COUNT(*) FROM target_citation WHERE NOT is_expected) = 0
  AND (SELECT COUNT(*) FROM shared_identity) = 1
  AND (SELECT COUNT(*) FROM shared_metadata_compatible) = 1
  AND (SELECT COUNT(*) FROM shared_url_lookalike) = 1
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS g7_post_knowledge_verification_pass
FROM frozen f;
