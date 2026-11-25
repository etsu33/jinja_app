-- NIIGATA-001-VPG001 G7 cohort guard, Stage P4: after nsrc-000024 Knowledge
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh
-- (psql ON_ERROR_STOP=1). Five statements; each raises division-by-zero unless its
-- assertion holds, so the first drift stops the run. FAIL = STOP. Never import on FAIL.
-- PRODUCTION_EXECUTION_MODE = VPG001_4_CANDIDATE_BATCH
-- GUARD_BASELINE_MODE = SINGLE_FROZEN_PRESTATE + CUMULATIVE_STAGE_CHECKPOINTS
-- Candidate order: nsrc-000021 -> nsrc-000022 -> nsrc-000024 -> nsrc-000025.
-- Stage P4 = DERIVED / EXPECTED cumulative checkpoint (not a Production measurement):
--   Shrine / Source / Deity / History / Citation / SourceFact / Collective
--   = 133 / 148 / 300 / 239 / 2 / 34 / 6
-- Candidate states at this stage:
--   nsrc-000021: KNOWLEDGE
--   nsrc-000022: KNOWLEDGE
--   nsrc-000024: KNOWLEDGE
--   nsrc-000025: BASE_ONLY
-- No Production numeric PK is referenced. No credential or connection target is output.
-- Statement 1 / 5: cohort aggregate checkpoint + G7 schema contract
WITH
-- BEGIN niigata_vpg001_g7_frozen_pre_state
-- Byte-identical in every statement of every niigata_vpg001_g7_*_guard.sql file (checked by
-- backend/temples/tests/test_niigata_vpg001_g7_cohort_guard.py).
-- FROZEN_PRE_STATE: SET. MEASURED = Stage P0 only: the single read-only Production measurement
-- taken by Mother Ship after PR #3279 merged (PostgreSQL 17.6 / server_version_num 170006,
-- latest temples migration 0121_shrine_fact_source_citation), before any of the four candidates
-- exists. Mother Ship accepted PRODUCTION_STATE_CLASS = CLEAN_CREATE x4. Every later stage value
-- is a DERIVED / EXPECTED cumulative checkpoint, never a Production measurement.
frozen AS (
  SELECT
    true AS frozen_values_set,
    129::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    2::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- nsrc-000021: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000021_same_name_other_address_total,
    0::bigint AS nsrc_000021_accepted_source_count,
    0::bigint AS nsrc_000021_foreign_fact_source_relation_total,
    -- nsrc-000022: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000022_same_name_other_address_total,
    0::bigint AS nsrc_000022_accepted_source_count,
    0::bigint AS nsrc_000022_foreign_fact_source_relation_total,
    -- nsrc-000024: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000024_same_name_other_address_total,
    0::bigint AS nsrc_000024_accepted_source_count,
    0::bigint AS nsrc_000024_foreign_fact_source_relation_total,
    -- nsrc-000025: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000025_same_name_other_address_total,
    0::bigint AS nsrc_000025_accepted_source_count,
    0::bigint AS nsrc_000025_foreign_fact_source_relation_total
)
-- END niigata_vpg001_g7_frozen_pre_state
,
-- BEGIN niigata_vpg001_g7_stage_checkpoint
-- Stage P4: DERIVED / EXPECTED cumulative checkpoint, NOT a Production measurement.
-- expected total = frozen P0 + cumulative repository payload delta (accepted_source_count = 0
-- for every target, so every completed candidate adds exactly one Source).
checkpoint AS (
  SELECT
    'P4'::text AS stage,
    4::bigint AS shrine_delta,
    3::bigint AS source_delta,
    5::bigint AS deity_delta,
    3::bigint AS history_delta,
    0::bigint AS citation_delta,
    0::bigint AS source_fact_delta,
    0::bigint AS collective_delta,
    133::bigint AS shrine_total,
    148::bigint AS source_total,
    300::bigint AS deity_total,
    239::bigint AS history_total,
    2::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total
)
-- END niigata_vpg001_g7_stage_checkpoint
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND c.stage = 'P4'
  AND c.shrine_total = f.shrine_total + c.shrine_delta
  AND c.source_total = f.source_total + c.source_delta
  AND c.deity_total = f.deity_total + c.deity_delta
  AND c.history_total = f.history_total + c.history_delta
  AND c.citation_total = f.citation_total + c.citation_delta
  AND c.source_fact_total = f.source_fact_total + c.source_fact_delta
  AND c.collective_total = f.collective_total + c.collective_delta
  AND to_regclass('public.temples_shrine') IS NOT NULL
  AND to_regclass('public.temples_shrineknowledgesource') IS NOT NULL
  AND to_regclass('public.temples_shrinedeity') IS NOT NULL
  AND to_regclass('public.temples_shrinedeity_sources') IS NOT NULL
  AND to_regclass('public.temples_shrinehistory') IS NOT NULL
  AND to_regclass('public.temples_shrinehistory_sources') IS NOT NULL
  AND to_regclass('public.temples_shrinefactsourcecitation') IS NOT NULL
  AND to_regclass('public.temples_shrinesourcefact') IS NOT NULL
  AND to_regclass('public.temples_shrinedeitycollective') IS NOT NULL
  AND to_regclass('public.temples_shrine_goriyaku_tags') IS NOT NULL
  AND to_regclass('public.temples_shrinegoriyakuassignment') IS NOT NULL
  AND (SELECT COUNT(*) FROM temples_shrine) = c.shrine_total
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = c.source_total
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = c.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = c.history_total
  AND (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) = c.citation_total
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = c.source_fact_total
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective) = c.collective_total
) THEN 1 ELSE 0 END AS niigata_vpg001_g7_p4_cohort_checkpoint_pass
FROM frozen f
CROSS JOIN checkpoint c;

-- Statement 2 / 5: nsrc-000021 = KNOWLEDGE_COMPLETE (every frozen Fact exactly once, one relation each to the compatible Source)
-- The source_identity / target_facts blocks below are byte-identical to the #3279 authority
-- files scripts/migration_safety/sql/nsrc_000021_g7_*.sql.
WITH
-- BEGIN niigata_vpg001_g7_frozen_pre_state
-- Byte-identical in every statement of every niigata_vpg001_g7_*_guard.sql file (checked by
-- backend/temples/tests/test_niigata_vpg001_g7_cohort_guard.py).
-- FROZEN_PRE_STATE: SET. MEASURED = Stage P0 only: the single read-only Production measurement
-- taken by Mother Ship after PR #3279 merged (PostgreSQL 17.6 / server_version_num 170006,
-- latest temples migration 0121_shrine_fact_source_citation), before any of the four candidates
-- exists. Mother Ship accepted PRODUCTION_STATE_CLASS = CLEAN_CREATE x4. Every later stage value
-- is a DERIVED / EXPECTED cumulative checkpoint, never a Production measurement.
frozen AS (
  SELECT
    true AS frozen_values_set,
    129::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    2::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- nsrc-000021: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000021_same_name_other_address_total,
    0::bigint AS nsrc_000021_accepted_source_count,
    0::bigint AS nsrc_000021_foreign_fact_source_relation_total,
    -- nsrc-000022: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000022_same_name_other_address_total,
    0::bigint AS nsrc_000022_accepted_source_count,
    0::bigint AS nsrc_000022_foreign_fact_source_relation_total,
    -- nsrc-000024: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000024_same_name_other_address_total,
    0::bigint AS nsrc_000024_accepted_source_count,
    0::bigint AS nsrc_000024_foreign_fact_source_relation_total,
    -- nsrc-000025: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000025_same_name_other_address_total,
    0::bigint AS nsrc_000025_accepted_source_count,
    0::bigint AS nsrc_000025_foreign_fact_source_relation_total
)
-- END niigata_vpg001_g7_frozen_pre_state
,
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
  AND f.nsrc_000021_accepted_source_count = 0
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県胎内市桃崎浜187番地') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '荒川神社' AND address <> '新潟県胎内市桃崎浜187番地') = f.nsrc_000021_same_name_other_address_total
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 38.1409456) < 0.00000001
          AND abs(longitude - 139.4073314) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND (SELECT COUNT(*) FROM target_deity) = 1
  AND (SELECT COUNT(*) FROM target_deity WHERE expected_key IS NOT NULL) = 1
  AND (SELECT COUNT(DISTINCT expected_key) FROM target_deity) = 1
  AND (SELECT COUNT(*) FROM target_history) = 1
  AND (SELECT COUNT(*) FROM target_history WHERE expected_key IS NOT NULL) = 1
  AND (SELECT COUNT(DISTINCT expected_key) FROM target_history) = 1
  AND (SELECT COUNT(*) FROM target_relation WHERE fact_kind = 'deity') = 1
  AND (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'deity' AND to_source) = 1
  AND (SELECT COUNT(*) FROM target_relation WHERE fact_kind = 'history') = 1
  AND (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'history' AND to_source) = 1
  AND (SELECT COUNT(*) FROM target_relation WHERE NOT to_source) = 0
  AND (SELECT COUNT(*) FROM target_deity d
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinedeity_sources ds WHERE ds.shrinedeity_id = d.id)) = 0
  AND (SELECT COUNT(*) FROM target_history h
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM source_identity) = 1
  AND (SELECT COUNT(*) FROM source_metadata_compatible) = 1
  AND (SELECT COUNT(*) FROM source_url_lookalike) = 1
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM foreign_relation) = f.nsrc_000021_foreign_fact_source_relation_total
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS niigata_vpg001_g7_p4_nsrc_000021_pass
FROM frozen f;

-- Statement 3 / 5: nsrc-000022 = KNOWLEDGE_COMPLETE (every frozen Fact exactly once, one relation each to the compatible Source)
-- The source_identity / target_facts blocks below are byte-identical to the #3279 authority
-- files scripts/migration_safety/sql/nsrc_000022_g7_*.sql.
WITH
-- BEGIN niigata_vpg001_g7_frozen_pre_state
-- Byte-identical in every statement of every niigata_vpg001_g7_*_guard.sql file (checked by
-- backend/temples/tests/test_niigata_vpg001_g7_cohort_guard.py).
-- FROZEN_PRE_STATE: SET. MEASURED = Stage P0 only: the single read-only Production measurement
-- taken by Mother Ship after PR #3279 merged (PostgreSQL 17.6 / server_version_num 170006,
-- latest temples migration 0121_shrine_fact_source_citation), before any of the four candidates
-- exists. Mother Ship accepted PRODUCTION_STATE_CLASS = CLEAN_CREATE x4. Every later stage value
-- is a DERIVED / EXPECTED cumulative checkpoint, never a Production measurement.
frozen AS (
  SELECT
    true AS frozen_values_set,
    129::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    2::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- nsrc-000021: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000021_same_name_other_address_total,
    0::bigint AS nsrc_000021_accepted_source_count,
    0::bigint AS nsrc_000021_foreign_fact_source_relation_total,
    -- nsrc-000022: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000022_same_name_other_address_total,
    0::bigint AS nsrc_000022_accepted_source_count,
    0::bigint AS nsrc_000022_foreign_fact_source_relation_total,
    -- nsrc-000024: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000024_same_name_other_address_total,
    0::bigint AS nsrc_000024_accepted_source_count,
    0::bigint AS nsrc_000024_foreign_fact_source_relation_total,
    -- nsrc-000025: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000025_same_name_other_address_total,
    0::bigint AS nsrc_000025_accepted_source_count,
    0::bigint AS nsrc_000025_foreign_fact_source_relation_total
)
-- END niigata_vpg001_g7_frozen_pre_state
,
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
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND f.nsrc_000022_accepted_source_count = 0
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県三条市大字飯田2283番地') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '五十嵐神社' AND address <> '新潟県三条市大字飯田2283番地') = f.nsrc_000022_same_name_other_address_total
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.573979) < 0.00000001
          AND abs(longitude - 139.048758) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND (SELECT COUNT(*) FROM target_deity) = 1
  AND (SELECT COUNT(*) FROM target_deity WHERE expected_key IS NOT NULL) = 1
  AND (SELECT COUNT(DISTINCT expected_key) FROM target_deity) = 1
  AND (SELECT COUNT(*) FROM target_history) = 0
  AND (SELECT COUNT(*) FROM target_history WHERE expected_key IS NOT NULL) = 0
  AND (SELECT COUNT(DISTINCT expected_key) FROM target_history) = 0
  AND (SELECT COUNT(*) FROM target_relation WHERE fact_kind = 'deity') = 1
  AND (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'deity' AND to_source) = 1
  AND (SELECT COUNT(*) FROM target_relation WHERE fact_kind = 'history') = 0
  AND (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'history' AND to_source) = 0
  AND (SELECT COUNT(*) FROM target_relation WHERE NOT to_source) = 0
  AND (SELECT COUNT(*) FROM target_deity d
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinedeity_sources ds WHERE ds.shrinedeity_id = d.id)) = 0
  AND (SELECT COUNT(*) FROM target_history h
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) = 0
  AND (SELECT COUNT(*) FROM target_deity WHERE display_name IN ('五十日帯彦命')) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM source_identity) = 1
  AND (SELECT COUNT(*) FROM source_metadata_compatible) = 1
  AND (SELECT COUNT(*) FROM source_url_lookalike) = 1
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM foreign_relation) = f.nsrc_000022_foreign_fact_source_relation_total
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS niigata_vpg001_g7_p4_nsrc_000022_pass
FROM frozen f;

-- Statement 4 / 5: nsrc-000024 = KNOWLEDGE_COMPLETE (every frozen Fact exactly once, one relation each to the compatible Source)
-- The source_identity / target_facts blocks below are byte-identical to the #3279 authority
-- files scripts/migration_safety/sql/nsrc_000024_g7_*.sql.
WITH
-- BEGIN niigata_vpg001_g7_frozen_pre_state
-- Byte-identical in every statement of every niigata_vpg001_g7_*_guard.sql file (checked by
-- backend/temples/tests/test_niigata_vpg001_g7_cohort_guard.py).
-- FROZEN_PRE_STATE: SET. MEASURED = Stage P0 only: the single read-only Production measurement
-- taken by Mother Ship after PR #3279 merged (PostgreSQL 17.6 / server_version_num 170006,
-- latest temples migration 0121_shrine_fact_source_citation), before any of the four candidates
-- exists. Mother Ship accepted PRODUCTION_STATE_CLASS = CLEAN_CREATE x4. Every later stage value
-- is a DERIVED / EXPECTED cumulative checkpoint, never a Production measurement.
frozen AS (
  SELECT
    true AS frozen_values_set,
    129::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    2::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- nsrc-000021: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000021_same_name_other_address_total,
    0::bigint AS nsrc_000021_accepted_source_count,
    0::bigint AS nsrc_000021_foreign_fact_source_relation_total,
    -- nsrc-000022: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000022_same_name_other_address_total,
    0::bigint AS nsrc_000022_accepted_source_count,
    0::bigint AS nsrc_000022_foreign_fact_source_relation_total,
    -- nsrc-000024: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000024_same_name_other_address_total,
    0::bigint AS nsrc_000024_accepted_source_count,
    0::bigint AS nsrc_000024_foreign_fact_source_relation_total,
    -- nsrc-000025: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000025_same_name_other_address_total,
    0::bigint AS nsrc_000025_accepted_source_count,
    0::bigint AS nsrc_000025_foreign_fact_source_relation_total
)
-- END niigata_vpg001_g7_frozen_pre_state
,
-- BEGIN nsrc_000024_source_identity
-- Byte-identical in every nsrc_000024_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000024_g7_source_identity_sql.py).
-- One Source (NIIGATA_CITY_AKIHA_BUNKASHIGEN). Whether it already exists in Production is measured,
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
    AND normalized_url = 'https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '新潟市'
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
  WHERE (lower(url) LIKE '%city.niigata.lg.jp%' AND lower(url) LIKE '%akihaku.pdf%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%city.niigata.lg.jp%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%akihaku.pdf%')
)
-- END nsrc_000024_source_identity
,
-- BEGIN nsrc_000024_target_facts
-- Byte-identical in every nsrc_000024_g7_*.sql file that contains it. Requires the
-- nsrc_000024_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '秋葉神社'
    AND address = '新潟県新潟市秋葉区秋葉3丁目8番19号'
),
-- expected_key = the frozen Deity the row equals in every field (NULL = unexpected row)
target_deity AS (
  SELECT
    d.id,
    d.display_name,
    CASE
      WHEN d.display_name = '大己貴神' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd1'
      WHEN d.display_name = '大物主命' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd2'
      WHEN d.display_name = '菅原道真公' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd3'
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
      WHEN h.history_type = 'historical_event' AND h.title = '桂家の守り神から秋葉町内への移譲'
       AND h.content = '秋葉神社は桂家の守り神であり、昭和39年（1964）に秋葉町内に移譲された。'
       AND h.period_text = '昭和39年（1964）' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h1'
      WHEN h.history_type = 'historical_event' AND h.title = '創建250年'
       AND h.content = '秋葉神社は平成25年（2013）に創建250年を迎えた。'
       AND h.period_text = '平成25年（2013）' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h2'
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
-- END nsrc_000024_target_facts
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND f.nsrc_000024_accepted_source_count = 0
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県新潟市秋葉区秋葉3丁目8番19号') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '秋葉神社' AND address <> '新潟県新潟市秋葉区秋葉3丁目8番19号') = f.nsrc_000024_same_name_other_address_total
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.7863255) < 0.00000001
          AND abs(longitude - 139.1351949) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND (SELECT COUNT(*) FROM target_deity) = 3
  AND (SELECT COUNT(*) FROM target_deity WHERE expected_key IS NOT NULL) = 3
  AND (SELECT COUNT(DISTINCT expected_key) FROM target_deity) = 3
  AND (SELECT COUNT(*) FROM target_history) = 2
  AND (SELECT COUNT(*) FROM target_history WHERE expected_key IS NOT NULL) = 2
  AND (SELECT COUNT(DISTINCT expected_key) FROM target_history) = 2
  AND (SELECT COUNT(*) FROM target_relation WHERE fact_kind = 'deity') = 3
  AND (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'deity' AND to_source) = 3
  AND (SELECT COUNT(*) FROM target_relation WHERE fact_kind = 'history') = 2
  AND (SELECT COUNT(DISTINCT fact_id) FROM target_relation WHERE fact_kind = 'history' AND to_source) = 2
  AND (SELECT COUNT(*) FROM target_relation WHERE NOT to_source) = 0
  AND (SELECT COUNT(*) FROM target_deity d
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinedeity_sources ds WHERE ds.shrinedeity_id = d.id)) = 0
  AND (SELECT COUNT(*) FROM target_history h
        WHERE NOT EXISTS (SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id)) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM source_identity) = 1
  AND (SELECT COUNT(*) FROM source_metadata_compatible) = 1
  AND (SELECT COUNT(*) FROM source_url_lookalike) = 1
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'government' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM foreign_relation) = f.nsrc_000024_foreign_fact_source_relation_total
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS niigata_vpg001_g7_p4_nsrc_000024_pass
FROM frozen f;

-- Statement 5 / 5: nsrc-000025 = BASE_ONLY (exact Base row at the frozen G2 coordinate, goriyaku neutral, Knowledge 0, Source ABSENT)
-- The source_identity / target_facts blocks below are byte-identical to the #3279 authority
-- files scripts/migration_safety/sql/nsrc_000025_g7_*.sql.
WITH
-- BEGIN niigata_vpg001_g7_frozen_pre_state
-- Byte-identical in every statement of every niigata_vpg001_g7_*_guard.sql file (checked by
-- backend/temples/tests/test_niigata_vpg001_g7_cohort_guard.py).
-- FROZEN_PRE_STATE: SET. MEASURED = Stage P0 only: the single read-only Production measurement
-- taken by Mother Ship after PR #3279 merged (PostgreSQL 17.6 / server_version_num 170006,
-- latest temples migration 0121_shrine_fact_source_citation), before any of the four candidates
-- exists. Mother Ship accepted PRODUCTION_STATE_CLASS = CLEAN_CREATE x4. Every later stage value
-- is a DERIVED / EXPECTED cumulative checkpoint, never a Production measurement.
frozen AS (
  SELECT
    true AS frozen_values_set,
    129::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    2::bigint AS citation_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    -- nsrc-000021: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000021_same_name_other_address_total,
    0::bigint AS nsrc_000021_accepted_source_count,
    0::bigint AS nsrc_000021_foreign_fact_source_relation_total,
    -- nsrc-000022: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000022_same_name_other_address_total,
    0::bigint AS nsrc_000022_accepted_source_count,
    0::bigint AS nsrc_000022_foreign_fact_source_relation_total,
    -- nsrc-000024: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000024_same_name_other_address_total,
    0::bigint AS nsrc_000024_accepted_source_count,
    0::bigint AS nsrc_000024_foreign_fact_source_relation_total,
    -- nsrc-000025: measured target_exact = same_address = 0 (asserted directly);
    -- same_name_other_address_count and source_identity_count measured 0; no Source row exists,
    -- so no other shrine's Fact can relate to it (foreign relation total 0).
    0::bigint AS nsrc_000025_same_name_other_address_total,
    0::bigint AS nsrc_000025_accepted_source_count,
    0::bigint AS nsrc_000025_foreign_fact_source_relation_total
)
-- END niigata_vpg001_g7_frozen_pre_state
,
-- BEGIN nsrc_000025_source_identity
-- Byte-identical in every nsrc_000025_g7_*.sql file (checked by
-- backend/temples/tests/test_nsrc_000025_g7_source_identity_sql.py).
-- One Source (AMATSU_JINJA_OFFICIAL_STORY). Whether it already exists in Production is measured,
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
  WHERE source_type = 'shrine_official'
    AND url <> ''
    AND normalized_url = 'https://amatsujinja.com/story'
),
-- Source importer reuse rule (SOURCE_REUSE_CONFLICT contract, unchanged): every
-- _SOURCE_REUSE_FIELDS value equal after strip(). The seed has no bibliography.
source_metadata_compatible AS (
  SELECT *
  FROM source_identity
  WHERE btrim(COALESCE(publisher, '')) = '天津神社・奴奈川神社'
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
  WHERE (lower(url) LIKE '%amatsujinja.com%' AND lower(url) LIKE '%/story%')
     OR (lower(COALESCE(normalized_url, '')) LIKE '%amatsujinja.com%'
         AND lower(COALESCE(normalized_url, '')) LIKE '%/story%')
)
-- END nsrc_000025_source_identity
,
-- BEGIN nsrc_000025_target_facts
-- Byte-identical in every nsrc_000025_g7_*.sql file that contains it. Requires the
-- nsrc_000025_source_identity block. The target is the exact (name_jp, address) only.
target AS (
  SELECT id, latitude, longitude, goriyaku
  FROM temples_shrine
  WHERE name_jp = '天津神社'
    AND address = '新潟県糸魚川市一の宮1丁目3番34号'
),
-- expected_key = the frozen Deity the row equals in every field (NULL = unexpected row)
target_deity AS (
  SELECT
    d.id,
    d.display_name,
    CASE
      WHEN d.display_name = '天津彦々火瓊々杵尊' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd1'
      WHEN d.display_name = '天児屋根命' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd2'
      WHEN d.display_name = '天太玉命' AND d.role = 'unknown'
       AND d.verification_status = 'source_confirmed' AND d.confidence = 'high'
       AND d.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'd3'
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
      WHEN h.history_type = 'tradition' AND h.title = '景行天皇御代の創設（公式由緒）'
       AND h.content = '天津神社の公式由緒では、第12代景行天皇の御代に創設されたと伝えられている。'
       AND h.period_text = '第12代景行天皇の御代' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h1'
      WHEN h.history_type = 'tradition' AND h.title = '孝徳天皇の勅願所（公式由緒）'
       AND h.content = '天津神社の公式由緒では、第36代孝徳天皇の勅願所であったとされている。'
       AND h.period_text = '第36代孝徳天皇' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h2'
      WHEN h.history_type = 'historical_event' AND h.title = '本殿の建立'
       AND h.content = '天津神社の本殿は寛政9年（1797）に建立された。'
       AND h.period_text = '寛政9年（1797）' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h3'
      WHEN h.history_type = 'historical_event' AND h.title = '拝殿の改築'
       AND h.content = '天津神社の拝殿は寛文2年（1662）に改築された。'
       AND h.period_text = '寛文2年（1662）' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h4'
      WHEN h.history_type = 'historical_event' AND h.title = '幣殿の増築'
       AND h.content = '天津神社の幣殿は天明2年（1782）に増築された。'
       AND h.period_text = '天明2年（1782）' AND h.event_date IS NULL
       AND h.verification_status = 'source_confirmed' AND h.confidence = 'high'
       AND h.verified_at = TIMESTAMPTZ '2026-10-19T14:35:38+09:00' THEN 'h5'
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
-- END nsrc_000025_target_facts
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND (SELECT COUNT(*) FROM target) = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE address = '新潟県糸魚川市一の宮1丁目3番34号') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '天津神社' AND address <> '新潟県糸魚川市一の宮1丁目3番34号') = f.nsrc_000025_same_name_other_address_total
  AND (SELECT COUNT(*) FROM target
        WHERE abs(latitude - 37.0397729) < 0.00000001
          AND abs(longitude - 137.8644153) < 0.00000001
          AND COALESCE(goriyaku, '') = '') = 1
  AND f.nsrc_000025_accepted_source_count = 0
  AND (SELECT COUNT(*) FROM source_identity) = f.nsrc_000025_accepted_source_count
  AND (SELECT COUNT(*) FROM source_metadata_compatible) = f.nsrc_000025_accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_lookalike) = f.nsrc_000025_accepted_source_count
  AND (SELECT COUNT(*) FROM source_url_norm
        WHERE source_type = 'shrine_official' AND url <> '' AND normalized_url IS NULL) = 0
  AND (SELECT COUNT(*) FROM foreign_relation) = f.nsrc_000025_foreign_fact_source_relation_total
  AND (SELECT COUNT(*) FROM target_deity) = 0
  AND (SELECT COUNT(*) FROM target_history) = 0
  AND (SELECT COUNT(*) FROM target_relation) = 0
  AND (SELECT COUNT(*) FROM target_citation) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact sf JOIN target t ON t.id = sf.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective dc JOIN target t ON t.id = dc.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN target t ON t.id = gt.shrine_id) = 0
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga JOIN target t ON t.id = ga.shrine_id) = 0
) THEN 1 ELSE 0 END AS niigata_vpg001_g7_p4_nsrc_000025_pass
FROM frozen f;
