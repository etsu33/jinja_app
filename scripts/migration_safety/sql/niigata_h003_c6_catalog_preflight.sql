-- NIIGATA-001-H003 C6 Catalog Production Import — read-only preflight
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- This file intentionally contains no credential, production hostname, or database identifier.
--
-- Write cohort (C4 / C5 PASS, Catalog-only):
--   nsrc-000011 赤城神社 / 新潟県新潟市江南区二本木1丁目7番16号 / 37.841794, 139.118507
--   nsrc-000012 赤城神社 / 新潟県長岡市四郎丸2丁目5番33号     / 37.440743, 138.855238
--   nsrc-000013 赤城神社 / 新潟県長岡市山屋314番地           / 37.496407, 139.008620
--   nsrc-000015 赤城神社 / 新潟県魚沼市湯之谷芋川311番地     / 37.214543, 139.036468
-- Diagnostics only, never in the write cohort:
--   nsrc-000014 赤城神社 / 新潟県五泉市上杉川1310番地2 (G2 HOLD_POSITION_REVIEW)
--
-- Per-target state:  ABSENT / EXACT_EXISTING / CONFLICT
-- Cohort state:      CLEAN_CREATE / ALREADY_MATERIALIZED / PARTIAL_EXISTING / CONFLICT
-- The cohort state is a candidate only. Mother Ship confirms it from the real Production output.
-- This file does not authorize any write.

SELECT
  current_database() IS NOT NULL AS database_identity_available,
  current_user IS NOT NULL AS database_user_available,
  current_setting('server_version') IS NOT NULL AS server_version_available;

SELECT
  current_setting('server_version') AS server_version,
  current_setting('server_version_num') AS server_version_num,
  current_setting('transaction_read_only') AS transaction_read_only;

SELECT
  COALESCE(MAX(name), '') AS latest_temples_migration,
  COUNT(*) FILTER (WHERE name LIKE '%\_shrine\_fact\_source\_citation') AS fact_source_citation_migration_applied
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
  to_regclass('public.temples_evidencelink') IS NOT NULL AS evidence_link_table_exists,
  to_regclass('public.temples_shrinesourcefact') IS NOT NULL AS source_fact_table_exists,
  to_regclass('public.temples_shrinesourcefact_sources') IS NOT NULL AS source_fact_sources_table_exists,
  to_regclass('public.temples_shrinedeitycollective') IS NOT NULL AS collective_table_exists,
  to_regclass('public.temples_shrinedeitycollective_sources') IS NOT NULL AS collective_sources_table_exists,
  to_regclass('public.temples_goriyakutag') IS NOT NULL AS goriyaku_tag_master_table_exists,
  to_regclass('public.temples_shrine_goriyaku_tags') IS NOT NULL AS goriyaku_tags_table_exists,
  to_regclass('public.temples_shrinegoriyakuassignment') IS NOT NULL AS goriyaku_assignment_table_exists,
  to_regclass('public.temples_historythemeassignment') IS NOT NULL AS history_theme_assignment_table_exists,
  to_regclass('public.temples_shrine_canonical_anchor') IS NOT NULL AS canonical_anchor_table_exists;

-- Production aggregates (pre-state). The C6 frozen delta is derived from these, not from the
-- repository Base Seed.
SELECT
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_total,
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_total,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_total,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_total,
  (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) AS citation_total,
  (SELECT COUNT(*) FROM temples_shrinesourcefact) AS source_fact_total,
  (SELECT COUNT(*) FROM temples_shrinedeitycollective) AS collective_total,
  (SELECT COUNT(*) FROM temples_shrine WHERE COALESCE(goriyaku, '') <> '') AS shrine_nonempty_goriyaku_total,
  (SELECT COUNT(*) FROM temples_goriyakutag) AS goriyaku_tag_master_total,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags) AS goriyaku_tag_link_total,
  (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment) AS goriyaku_assignment_total,
  (SELECT COUNT(*) FROM temples_historythemeassignment) AS history_theme_assignment_total,
  (SELECT COUNT(*) FROM temples_shrine_canonical_anchor) AS canonical_anchor_total,
  (SELECT COUNT(*) FROM temples_shrine WHERE name_jp = '赤城神社') AS akagi_jinja_total;

-- Per-target identity counts. same_name_other_address_count includes the other H003 targets
-- and any other 赤城神社. Those rows are diagnostics and never identify the target.
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  candidate_id,
  name_jp,
  address,
  adopted_latitude,
  adopted_longitude,
  exact_count,
  same_name_other_address_count,
  same_address_other_name_count
FROM target_state
ORDER BY candidate_id;

-- Stored values of exact target rows (empty when every target is ABSENT).
-- location is reported as presence only. Its column type differs between PostGIS and nogis.
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  e.candidate_id,
  s.id AS shrine_id,
  s.kind,
  s.latitude,
  s.longitude,
  s.location IS NOT NULL AS location_present,
  s.goriyaku,
  s.kyusei,
  s.astro_elements,
  s.name_romaji,
  s.sajin,
  s.description,
  s.element,
  s.visit_style_tags,
  s.history_theme,
  s.place_ref_id,
  e.coordinate_match,
  e.payload_neutral,
  e.catalog_neutral
FROM exact_rows e
JOIN temples_shrine s ON s.id = e.shrine_id
ORDER BY e.candidate_id, s.id;

-- Knowledge / goriyaku / Source-Fact relations attached to exact target rows (all 0 when ABSENT).
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  candidate_id,
  exact_count,
  deity_count,
  history_count,
  source_fact_count,
  collective_count,
  goriyaku_tag_link_count,
  goriyaku_assignment_count,
  history_theme_assignment_count,
  canonical_anchor_count,
  source_fact_relation_count
FROM target_state
ORDER BY candidate_id;

-- Per-target classification.
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  candidate_id,
  target_state,
  target_state_reason,
  exact_count,
  same_address_other_name_count,
  coordinate_match_count,
  payload_neutral_count,
  catalog_neutral_count
FROM target_state
ORDER BY candidate_id;

-- Diagnostics only: every 赤城神社 row and every row at a target address.
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  s.id,
  s.name_jp,
  s.address,
  s.latitude,
  s.longitude,
  s.place_ref_id,
  COALESCE(s.goriyaku, '') AS goriyaku,
  (SELECT t.candidate_id FROM targets t
     WHERE t.name_jp = s.name_jp AND t.address = s.address) AS exact_target_candidate_id,
  EXISTS (SELECT 1 FROM targets t
     WHERE t.address = s.address AND t.name_jp <> s.name_jp) AS same_address_other_name
FROM temples_shrine s
WHERE s.name_jp = '赤城神社'
   OR s.address IN (SELECT address FROM targets)
ORDER BY s.id;

-- Diagnostics only (not part of the classification): rows within about 220 m of an adopted
-- coordinate that are not an exact target identity. Each listed row must be reviewed as a
-- possible same real-world shrine under another name / address before C6 authorization.
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  t.candidate_id,
  s.id,
  s.name_jp,
  s.address,
  s.latitude,
  s.longitude,
  round((111320 * sqrt(
    power(s.latitude - t.adopted_latitude, 2)
    + power((s.longitude - t.adopted_longitude) * cos(radians(t.adopted_latitude)), 2)
  ))::numeric, 1) AS approx_distance_m
FROM targets t
JOIN temples_shrine s
  ON abs(s.latitude - t.adopted_latitude) <= 0.002
 AND abs(s.longitude - t.adopted_longitude) <= 0.0025
WHERE NOT EXISTS (
  SELECT 1 FROM targets x WHERE x.name_jp = s.name_jp AND x.address = s.address
)
ORDER BY t.candidate_id, approx_distance_m, s.id;

-- Diagnostics only (not part of the classification): 赤城-named rows in 新潟県 that are not an
-- exact target identity (known H002 赤城社 rows, the nsrc-000014 HOLD identity if present,
-- or an unexplained variant that must be reviewed before C6 authorization).
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  s.id,
  s.name_jp,
  s.address,
  s.latitude,
  s.longitude,
  s.place_ref_id
FROM temples_shrine s
WHERE s.name_jp LIKE '%赤城%'
  AND s.address LIKE '新潟県%'
  AND NOT EXISTS (
    SELECT 1 FROM targets x WHERE x.name_jp = s.name_jp AND x.address = s.address
  )
ORDER BY s.id;

-- nsrc-000014 HOLD identity: diagnostics only. Never part of the write cohort, never authorized here.
SELECT
  'nsrc-000014' AS candidate_id,
  'G2_HOLD_POSITION_REVIEW' AS candidate_hold,
  false AS in_write_cohort,
  COUNT(*) FILTER (
    WHERE name_jp = '赤城神社' AND address = '新潟県五泉市上杉川1310番地2'
  ) AS hold_exact_count,
  COUNT(*) FILTER (
    WHERE address = '新潟県五泉市上杉川1310番地2' AND name_jp <> '赤城神社'
  ) AS hold_same_address_other_name_count,
  CASE
    WHEN COUNT(*) FILTER (
      WHERE name_jp = '赤城神社' AND address = '新潟県五泉市上杉川1310番地2'
    ) = 0 THEN 'ABSENT'
    ELSE 'PRESENT'
  END AS hold_identity_state
FROM temples_shrine;

SELECT
  id,
  name_jp,
  address,
  latitude,
  longitude,
  place_ref_id
FROM temples_shrine
WHERE address = '新潟県五泉市上杉川1310番地2'
ORDER BY id;

-- H003 write-cohort classification candidate (last statement).
-- expected_shrine_delta_candidate is NULL on CONFLICT. Every other table delta is 0 for a
-- Catalog-only Base import. Mother Ship confirms the class. This query authorizes nothing.
WITH
-- BEGIN niigata_h003_c6_target_state
-- Byte-identical in every statement that uses it (checked by
-- backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py).
-- Frozen authority: C4 canonical name / address, G2 adopted coordinate, Base Seed rows 125-128.
-- nsrc-000014 (G2 HOLD_POSITION_REVIEW) is not a target and never appears in this block.
-- Identity is exact (name_jp, address) only. Same-name rows at other addresses are other shrines.
-- Coordinate equality uses the importer tolerance (import_shrines_seed COORDINATE_ABS_TOLERANCE = 1e-12).
-- payload_neutral mirrors the importer payload for these rows. A mismatch means the importer
-- would UPDATE (overwrite) the existing row.
-- catalog_neutral covers fields the importer does not write but a Catalog-only row must not carry.
targets (candidate_id, name_jp, address, adopted_latitude, adopted_longitude) AS (
  VALUES
    ('nsrc-000011', '赤城神社', '新潟県新潟市江南区二本木1丁目7番16号', 37.841794::double precision, 139.118507::double precision),
    ('nsrc-000012', '赤城神社', '新潟県長岡市四郎丸2丁目5番33号', 37.440743::double precision, 138.855238::double precision),
    ('nsrc-000013', '赤城神社', '新潟県長岡市山屋314番地', 37.496407::double precision, 139.008620::double precision),
    ('nsrc-000015', '赤城神社', '新潟県魚沼市湯之谷芋川311番地', 37.214543::double precision, 139.036468::double precision)
),
exact_rows AS (
  SELECT
    t.candidate_id,
    s.id AS shrine_id,
    COALESCE(
      abs(s.latitude - t.adopted_latitude) <= 1e-12
      AND abs(s.longitude - t.adopted_longitude) <= 1e-12,
      false) AS coordinate_match,
    COALESCE(
      s.goriyaku = ''
      AND s.kyusei IS NULL
      AND s.astro_elements = '[]'::jsonb
      AND s.name_romaji IS NULL
      AND s.sajin = ''
      AND s.description IS NULL
      AND s.element IS NULL,
      false) AS payload_neutral,
    COALESCE(
      s.kind = 'shrine'
      AND s.visit_style_tags = '[]'::jsonb
      AND s.history_theme = ''
      AND s.place_ref_id IS NULL,
      false) AS catalog_neutral
  FROM targets t
  JOIN temples_shrine s
    ON s.name_jp = t.name_jp
   AND s.address = t.address
),
exact_relations AS (
  SELECT
    e.candidate_id,
    e.shrine_id,
    (SELECT COUNT(*) FROM temples_shrinedeity d WHERE d.shrine_id = e.shrine_id) AS deity_count,
    (SELECT COUNT(*) FROM temples_shrinehistory h WHERE h.shrine_id = e.shrine_id) AS history_count,
    (SELECT COUNT(*) FROM temples_shrinesourcefact sf WHERE sf.shrine_id = e.shrine_id) AS source_fact_count,
    (SELECT COUNT(*) FROM temples_shrinedeitycollective dc WHERE dc.shrine_id = e.shrine_id) AS collective_count,
    (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt WHERE gt.shrine_id = e.shrine_id) AS goriyaku_tag_link_count,
    (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment ga WHERE ga.shrine_id = e.shrine_id) AS goriyaku_assignment_count,
    (SELECT COUNT(*) FROM temples_historythemeassignment ha WHERE ha.shrine_id = e.shrine_id) AS history_theme_assignment_count,
    (SELECT COUNT(*) FROM temples_shrine_canonical_anchor ca WHERE ca.shrine_id = e.shrine_id) AS canonical_anchor_count,
    (SELECT COUNT(*) FROM temples_shrinedeity_sources x
       JOIN temples_shrinedeity d ON d.id = x.shrinedeity_id WHERE d.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinehistory_sources x
       JOIN temples_shrinehistory h ON h.id = x.shrinehistory_id WHERE h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinefactsourcecitation x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_evidencelink x
       LEFT JOIN temples_shrinedeity d ON d.id = x.shrine_deity_id
       LEFT JOIN temples_shrinehistory h ON h.id = x.shrine_history_id
       WHERE d.shrine_id = e.shrine_id OR h.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinesourcefact_sources x
       JOIN temples_shrinesourcefact sf ON sf.id = x.shrinesourcefact_id WHERE sf.shrine_id = e.shrine_id)
    + (SELECT COUNT(*) FROM temples_shrinedeitycollective_sources x
       JOIN temples_shrinedeitycollective dc ON dc.id = x.shrinedeitycollective_id WHERE dc.shrine_id = e.shrine_id)
      AS source_fact_relation_count
  FROM exact_rows e
),
per_target AS (
  SELECT
    t.candidate_id,
    t.name_jp,
    t.address,
    t.adopted_latitude,
    t.adopted_longitude,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address = t.address) AS exact_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.name_jp = t.name_jp AND s.address <> t.address) AS same_name_other_address_count,
    (SELECT COUNT(*) FROM temples_shrine s
       WHERE s.address = t.address AND s.name_jp <> t.name_jp) AS same_address_other_name_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.coordinate_match) AS coordinate_match_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.payload_neutral) AS payload_neutral_count,
    (SELECT COUNT(*) FROM exact_rows e
       WHERE e.candidate_id = t.candidate_id AND e.catalog_neutral) AS catalog_neutral_count,
    COALESCE((SELECT SUM(r.deity_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS deity_count,
    COALESCE((SELECT SUM(r.history_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_count,
    COALESCE((SELECT SUM(r.source_fact_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_count,
    COALESCE((SELECT SUM(r.collective_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS collective_count,
    COALESCE((SELECT SUM(r.goriyaku_tag_link_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_tag_link_count,
    COALESCE((SELECT SUM(r.goriyaku_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS goriyaku_assignment_count,
    COALESCE((SELECT SUM(r.history_theme_assignment_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS history_theme_assignment_count,
    COALESCE((SELECT SUM(r.canonical_anchor_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS canonical_anchor_count,
    COALESCE((SELECT SUM(r.source_fact_relation_count) FROM exact_relations r WHERE r.candidate_id = t.candidate_id), 0) AS source_fact_relation_count
  FROM targets t
),
target_state AS (
  SELECT
    p.*,
    CASE
      WHEN p.exact_count > 1 THEN 'CONFLICT'
      WHEN p.same_address_other_name_count > 0 THEN 'CONFLICT'
      WHEN p.exact_count = 0 THEN 'ABSENT'
      WHEN p.coordinate_match_count = 1
        AND p.payload_neutral_count = 1
        AND p.catalog_neutral_count = 1
        AND p.deity_count = 0 AND p.history_count = 0
        AND p.source_fact_count = 0 AND p.collective_count = 0
        AND p.goriyaku_tag_link_count = 0 AND p.goriyaku_assignment_count = 0
        AND p.history_theme_assignment_count = 0 AND p.canonical_anchor_count = 0
        AND p.source_fact_relation_count = 0
        THEN 'EXACT_EXISTING'
      ELSE 'CONFLICT'
    END AS target_state,
    CASE
      WHEN p.exact_count > 1 THEN 'DUPLICATE_EXACT_IDENTITY'
      WHEN p.same_address_other_name_count > 0 THEN 'SAME_ADDRESS_OTHER_NAME'
      WHEN p.exact_count = 0 THEN 'NONE'
      WHEN p.coordinate_match_count = 0 THEN 'COORDINATE_MISMATCH'
      WHEN p.payload_neutral_count = 0 THEN 'IMPORT_WOULD_OVERWRITE_PAYLOAD'
      WHEN p.catalog_neutral_count = 0 THEN 'UNEXPECTED_CATALOG_STATE'
      WHEN p.deity_count + p.history_count + p.source_fact_count + p.collective_count
         + p.goriyaku_tag_link_count + p.goriyaku_assignment_count
         + p.history_theme_assignment_count + p.canonical_anchor_count
         + p.source_fact_relation_count > 0 THEN 'UNEXPECTED_KNOWLEDGE_OR_RELATION'
      ELSE 'NONE'
    END AS target_state_reason
  FROM per_target p
)
-- END niigata_h003_c6_target_state
SELECT
  CASE
    WHEN COUNT(*) FILTER (WHERE target_state = 'CONFLICT') > 0 THEN 'CONFLICT'
    WHEN COUNT(*) FILTER (WHERE target_state = 'ABSENT') = COUNT(*) THEN 'CLEAN_CREATE'
    WHEN COUNT(*) FILTER (WHERE target_state = 'EXACT_EXISTING') = COUNT(*) THEN 'ALREADY_MATERIALIZED'
    ELSE 'PARTIAL_EXISTING'
  END AS h003_cohort_state_class_candidate,
  COUNT(*) AS target_count,
  COUNT(*) FILTER (WHERE target_state = 'ABSENT') AS absent_count,
  COUNT(*) FILTER (WHERE target_state = 'EXACT_EXISTING') AS exact_existing_count,
  COUNT(*) FILTER (WHERE target_state = 'CONFLICT') AS conflict_count,
  COALESCE(string_agg(candidate_id, ',' ORDER BY candidate_id)
    FILTER (WHERE target_state = 'ABSENT'), '') AS create_candidate_ids,
  COALESCE(string_agg(candidate_id, ',' ORDER BY candidate_id)
    FILTER (WHERE target_state = 'CONFLICT'), '') AS conflict_candidate_ids,
  CASE
    WHEN COUNT(*) FILTER (WHERE target_state = 'CONFLICT') > 0 THEN NULL
    ELSE COUNT(*) FILTER (WHERE target_state = 'ABSENT')
  END AS expected_shrine_delta_candidate
FROM target_state;
