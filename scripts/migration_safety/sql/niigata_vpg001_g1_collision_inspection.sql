-- NIIGATA-001-VPG001 G1 Identity / Duplicate — Production collision inspection (read-only)
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.
--
-- Targets (canonical identity candidates, docs/audit/niigata-vpg001-g1-identity-duplicate.md):
--   nsrc-000021 荒川神社   / 新潟県胎内市桃崎浜187番地
--   nsrc-000022 五十嵐神社 / 新潟県三条市大字飯田2283番地
--   nsrc-000023 熱串彦神社 / 新潟県佐渡市長江854番地
--   nsrc-000024 秋葉神社   / 新潟県新潟市秋葉区秋葉3丁目8番19号
--   nsrc-000025 天津神社   / 新潟県糸魚川市一の宮1丁目3番34号
--
-- Tables: temples_shrine and temples_shrinecandidate.
-- name_key    = NFKC, all whitespace removed.
-- address_key = NFKC, all whitespace removed, leading 新潟県 removed.
-- Same-name rows are listed even when the address differs. A listed row is evidence to explain,
-- not a duplicate decision. This file does not authorize any write.

-- 1. session / totals
SELECT
  current_setting('transaction_read_only') AS transaction_read_only,
  current_setting('server_encoding') AS server_encoding,
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrinecandidate) AS shrinecandidate_total;

-- 2. per target, per table: exact identity / same name other address / same address other name
WITH
targets (candidate_id, name_jp, frozen_address) AS (
  VALUES
    ('nsrc-000021', '荒川神社', '胎内市桃崎浜187番地'),
    ('nsrc-000022', '五十嵐神社', '三条市大字飯田2283番地'),
    ('nsrc-000023', '熱串彦神社', '佐渡市長江854番地'),
    ('nsrc-000024', '秋葉神社', '新潟市秋葉区秋葉3丁目8番19号'),
    ('nsrc-000025', '天津神社', '糸魚川市一の宮1丁目3番34号')
),
target_keys AS (
  SELECT
    candidate_id,
    regexp_replace(normalize(name_jp, NFKC), '[[:space:]]', '', 'g') AS name_key,
    regexp_replace(
      regexp_replace(normalize(frozen_address, NFKC), '[[:space:]]', '', 'g'), '^新潟県', ''
    ) AS address_key
  FROM targets
),
rows_all (source_table, id, name_jp, address) AS (
  SELECT 'temples_shrine', id, name_jp, COALESCE(address, '') FROM temples_shrine
  UNION ALL
  SELECT 'temples_shrinecandidate', id, name_jp, COALESCE(address, '') FROM temples_shrinecandidate
),
row_keys AS (
  SELECT
    source_table,
    id,
    regexp_replace(normalize(name_jp, NFKC), '[[:space:]]', '', 'g') AS name_key,
    regexp_replace(
      regexp_replace(normalize(address, NFKC), '[[:space:]]', '', 'g'), '^新潟県', ''
    ) AS address_key
  FROM rows_all
)
SELECT
  t.candidate_id,
  tbl.source_table,
  (SELECT COUNT(*) FROM row_keys r WHERE r.source_table = tbl.source_table
     AND r.name_key = t.name_key AND r.address_key = t.address_key) AS exact_identity_count,
  (SELECT COUNT(*) FROM row_keys r WHERE r.source_table = tbl.source_table
     AND r.name_key = t.name_key AND r.address_key <> t.address_key) AS same_name_other_address_count,
  (SELECT COUNT(*) FROM row_keys r WHERE r.source_table = tbl.source_table
     AND r.address_key = t.address_key AND r.name_key <> t.name_key) AS same_address_other_name_count
FROM target_keys t
CROSS JOIN (VALUES ('temples_shrine'), ('temples_shrinecandidate')) AS tbl (source_table)
ORDER BY t.candidate_id, tbl.source_table;

-- 3. diagnostics: every row hit by a name, name-key, name-fragment or address-fragment probe.
--    name          = exact name_jp
--    name_key      = NFKC / whitespace-insensitive name
--    name_fragment = name_jp contains the distinctive part of the name
--    address       = address contains both fragments (fragment_a may be NULL)
--    奴奈川神社 is probed for nsrc-000025 because the precinct also has 奴奈川神社御本殿. A hit is a
--    separate shrine / Fact owner to explain, never a merge target.
WITH
probes (candidate_id, probe_kind, probe_value, fragment_a, fragment_b) AS (
  VALUES
    ('nsrc-000021', 'name', '荒川神社', NULL, NULL),
    ('nsrc-000021', 'name_key', '荒川神社', NULL, NULL),
    ('nsrc-000021', 'name_fragment', '荒川', NULL, NULL),
    ('nsrc-000021', 'address', NULL, NULL, '桃崎浜'),
    ('nsrc-000022', 'name', '五十嵐神社', NULL, NULL),
    ('nsrc-000022', 'name_key', '五十嵐神社', NULL, NULL),
    ('nsrc-000022', 'name_fragment', '五十嵐', NULL, NULL),
    ('nsrc-000022', 'address', NULL, '三条市', '飯田'),
    ('nsrc-000022', 'address', NULL, '下田村', '飯田'),
    ('nsrc-000023', 'name', '熱串彦神社', NULL, NULL),
    ('nsrc-000023', 'name_key', '熱串彦神社', NULL, NULL),
    ('nsrc-000023', 'name_fragment', '熱串', NULL, NULL),
    ('nsrc-000023', 'address', NULL, '佐渡', '長江'),
    ('nsrc-000024', 'name', '秋葉神社', NULL, NULL),
    ('nsrc-000024', 'name_key', '秋葉神社', NULL, NULL),
    ('nsrc-000024', 'name_fragment', '秋葉', NULL, NULL),
    ('nsrc-000024', 'address', NULL, '新潟市', '秋葉区'),
    ('nsrc-000024', 'address', NULL, '新津市', '秋葉'),
    ('nsrc-000025', 'name', '天津神社', NULL, NULL),
    ('nsrc-000025', 'name_key', '天津神社', NULL, NULL),
    ('nsrc-000025', 'name_fragment', '天津', NULL, NULL),
    ('nsrc-000025', 'name', '奴奈川神社', NULL, NULL),
    ('nsrc-000025', 'name_fragment', '奴奈川', NULL, NULL),
    ('nsrc-000025', 'address', NULL, '糸魚川', '一の宮'),
    ('nsrc-000025', 'address', NULL, '糸魚川', '一ノ宮'),
    ('nsrc-000025', 'address', NULL, '糸魚川', '一宮')
),
rows_all (source_table, id, name_jp, address, row_state) AS (
  SELECT 'temples_shrine', id, name_jp, COALESCE(address, ''), kind FROM temples_shrine
  UNION ALL
  SELECT 'temples_shrinecandidate', id, name_jp, COALESCE(address, ''), status
  FROM temples_shrinecandidate
)
SELECT
  p.candidate_id,
  p.probe_kind,
  COALESCE(p.probe_value, COALESCE(p.fragment_a || ' + ', '') || p.fragment_b) AS probe,
  r.source_table,
  r.id,
  r.name_jp,
  r.address,
  r.row_state
FROM probes p
JOIN rows_all r
  ON (p.probe_kind = 'name' AND r.name_jp = p.probe_value)
  OR (p.probe_kind = 'name_key'
      AND regexp_replace(normalize(r.name_jp, NFKC), '[[:space:]]', '', 'g')
        = regexp_replace(normalize(p.probe_value, NFKC), '[[:space:]]', '', 'g')
      AND r.name_jp <> p.probe_value)
  OR (p.probe_kind = 'name_fragment'
      AND position(p.probe_value IN normalize(r.name_jp, NFKC)) > 0)
  OR (p.probe_kind = 'address'
      AND (p.fragment_a IS NULL OR position(p.fragment_a IN normalize(r.address, NFKC)) > 0)
      AND position(p.fragment_b IN normalize(r.address, NFKC)) > 0)
ORDER BY p.candidate_id, p.probe_kind, r.source_table, r.id;
