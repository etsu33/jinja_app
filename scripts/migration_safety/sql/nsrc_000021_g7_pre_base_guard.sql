-- nsrc-000021 G7 pre-Base Production write guard
-- SELECT-only; raises division-by-zero unless the frozen CLEAN_CREATE pre-state still holds.
-- While the frozen block is UNSET (frozen_values_set = false, values NULL) it always fails.
-- Expected pre-state (CLEAN_CREATE only; other states never reach this guard):
--   aggregates (Shrine / Source / Deity / History / Citation / SourceFact / Collective) = frozen
--   target exact = 0; same-address = 0; 荒川神社 at other addresses = frozen (diagnostic, no drift)
--   Source: identity = compatible = lookalike = frozen accepted count (0 or 1);
--   no importer-unparseable URL of the same source_type; foreign Fact relations = frozen
-- No Production numeric PK is referenced.
WITH
-- BEGIN nsrc_000021_frozen_pre_state
frozen AS (
  -- FROZEN_PRE_STATE: UNSET.
  -- nsrc_000021_g7_preflight.sql has NOT been executed on Production and Mother Ship has
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
    -- 荒川神社 rows at other addresses (distinct shrines; frozen only to detect drift)
    NULL::bigint AS same_name_other_address_total,
    -- other shrines' Deity / History relations to the Source identity (frozen to detect drift)
    NULL::bigint AS foreign_fact_source_relation_total,
    -- = measured source_identity_count; only 0 (ABSENT) or 1 (REUSABLE)
    NULL::bigint AS accepted_source_count
),
-- END nsrc_000021_frozen_pre_state
-- BEGIN nsrc_000021_source_identity
-- Byte-identical in every nsrc_000021_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000021_g7_source_identity_sql.py).
-- One Source (NIIGATA_PREF_KITAMAEBUNE02). Whether it already exists in Production is measured,
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
    AND normalized_url = 'https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟県'
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
  WHERE (lower(url) LIKE '%pref.niigata.lg.jp%' AND lower(url) LIKE '%kitamaebune02%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%pref.niigata.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%kitamaebune02%')
)
-- END nsrc_000021_source_identity
,
-- BEGIN nsrc_000021_target_facts
-- Byte-identical in every nsrc_000021_g7_*.sql file that contains it. Requires the
-- nsrc_000021_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '荒川神社'
    AND address = '新潟県胎内市桃崎浜187番地'
),
-- expected_key = the frozen Deity the row equals in every field (NULL = unexpected row)
target_deity AS (
  SELECT
    d.id,
    d.display_name,
    CASE
      WHEN d.display_name = '天鈿女命' AND d.role = 'unknown'
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
    CASE
      WHEN h.history_type = 'regional_context' AND h.title = '船主による船絵馬の奉納'
       AND h.content = '荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。'
       AND h.period_text = '' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h1'
      ELSE NULL
    END AS expected_key
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
-- END nsrc_000021_target_facts
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND (SELECT COUNT(*) FROM temples_shrine) = f.shrine_total
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total
  AND (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) = f.citation_total
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective) = f.collective_total
  AND (SELECT COUNT(*) FROM target) = 0
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県胎内市桃崎浜187番地') = 0
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '荒川神社' AND address <> '新潟県胎内市桃崎浜187番地') = f.same_name_other_address_total
  AND f.accepted_source_count IN (0, 1)
  AND (SELECT COUNT(*) FROM source_identity) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM source_metadata_compatible) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_lookalike) = f.accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM foreign_relation) = f.foreign_fact_source_relation_total
  AND (SELECT COUNT(*) FROM target_deity) = 0
  AND (SELECT COUNT(*) FROM target_history) = 0
  AND (SELECT COUNT(*) FROM target_relation) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS g7_pre_base_guard_pass
FROM frozen f;
