-- NIIGATA-001-H003 C6 post-Base Production verification
-- SELECT / WITH only. Execute only through scripts/migration_safety/readonly_query.sh.
-- Statement 1 lists the four target states (diagnostics). The last statement raises
-- division-by-zero unless exactly the four target Catalog rows were added:
--   Shrine = frozen + 4 (= 129). Every other frozen aggregate (Source / Deity / History /
--   SourceFact / Collective / Citation / non-empty goriyaku / GoriyakuTag master / tag links /
--   goriyaku assignments / history-theme assignments / canonical anchors) unchanged
--   every target = EXACT_EXISTING: exists exactly once, adopted coordinate within the importer
--   tolerance 1e-12, neutral Base payload, Catalog defaults (kind / visit_style_tags /
--   history_theme / place_ref), no Deity / History / SourceFact / Collective, no goriyaku tag
--   link / assignment / history-theme assignment / canonical anchor / Source-Fact relation
--   no same-address different-name row. nsrc-000014 still absent.
-- FAIL = STOP. Do not repair with ad-hoc writes (gate contract C6).
-- No Production numeric PK is referenced.
WITH
-- BEGIN niigata_h003_c6_frozen_pre_state
-- Identical in niigata_h003_c6_pre_base_guard.sql and niigata_h003_c6_post_base_verification.sql
-- (checked by backend/temples/tests/test_niigata_h003_c6_target_only_import.py).
-- FROZEN_PRE_STATE: measured by niigata_h003_c6_catalog_preflight.sql on Production (read-only),
-- executed by Mother Ship through readonly_query.sh after PR #3254.
-- Mother Ship decision: PRODUCTION_STATE_CLASS = CLEAN_CREATE
-- (nsrc-000011 / 000012 / 000013 / 000015 = ABSENT, conflict_count = 0,
-- nsrc-000014 = ABSENT / NOT_IN_WRITE_COHORT).
-- Every aggregate the preflight measured is frozen. Any drift fails closed.
frozen AS (
  SELECT
    true AS frozen_values_set,
    125::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    2::bigint AS citation_total,
    116::bigint AS shrine_nonempty_goriyaku_total,
    39::bigint AS goriyaku_tag_master_total,
    366::bigint AS goriyaku_tag_link_total,
    0::bigint AS goriyaku_assignment_total,
    0::bigint AS history_theme_assignment_total,
    0::bigint AS canonical_anchor_total,
    4::bigint AS expected_shrine_delta
),
-- END niigata_h003_c6_frozen_pre_state
hold AS (
  -- nsrc-000014 (G2 HOLD_POSITION_REVIEW): never in the write cohort. Measured ABSENT.
  SELECT
    (SELECT COUNT(*) FROM temples_shrine
       WHERE name_jp = '赤城神社' AND address = '新潟県五泉市上杉川1310番地2') AS hold_exact_count,
    (SELECT COUNT(*) FROM temples_shrine
       WHERE address = '新潟県五泉市上杉川1310番地2') AS hold_address_count
),
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
  coordinate_match_count,
  payload_neutral_count,
  catalog_neutral_count,
  (SELECT bool_and(s.location IS NOT NULL) FROM temples_shrine s
     WHERE s.name_jp = target_state.name_jp AND s.address = target_state.address) AS location_present
FROM target_state
ORDER BY candidate_id;

WITH
-- BEGIN niigata_h003_c6_frozen_pre_state
-- Identical in niigata_h003_c6_pre_base_guard.sql and niigata_h003_c6_post_base_verification.sql
-- (checked by backend/temples/tests/test_niigata_h003_c6_target_only_import.py).
-- FROZEN_PRE_STATE: measured by niigata_h003_c6_catalog_preflight.sql on Production (read-only),
-- executed by Mother Ship through readonly_query.sh after PR #3254.
-- Mother Ship decision: PRODUCTION_STATE_CLASS = CLEAN_CREATE
-- (nsrc-000011 / 000012 / 000013 / 000015 = ABSENT, conflict_count = 0,
-- nsrc-000014 = ABSENT / NOT_IN_WRITE_COHORT).
-- Every aggregate the preflight measured is frozen. Any drift fails closed.
frozen AS (
  SELECT
    true AS frozen_values_set,
    125::bigint AS shrine_total,
    145::bigint AS source_total,
    295::bigint AS deity_total,
    236::bigint AS history_total,
    34::bigint AS source_fact_total,
    6::bigint AS collective_total,
    2::bigint AS citation_total,
    116::bigint AS shrine_nonempty_goriyaku_total,
    39::bigint AS goriyaku_tag_master_total,
    366::bigint AS goriyaku_tag_link_total,
    0::bigint AS goriyaku_assignment_total,
    0::bigint AS history_theme_assignment_total,
    0::bigint AS canonical_anchor_total,
    4::bigint AS expected_shrine_delta
),
-- END niigata_h003_c6_frozen_pre_state
hold AS (
  -- nsrc-000014 (G2 HOLD_POSITION_REVIEW): never in the write cohort. Measured ABSENT.
  SELECT
    (SELECT COUNT(*) FROM temples_shrine
       WHERE name_jp = '赤城神社' AND address = '新潟県五泉市上杉川1310番地2') AS hold_exact_count,
    (SELECT COUNT(*) FROM temples_shrine
       WHERE address = '新潟県五泉市上杉川1310番地2') AS hold_address_count
),
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
SELECT 1 / CASE WHEN (
  f.frozen_values_set
  AND (SELECT COUNT(*) FROM temples_shrine) = f.shrine_total + f.expected_shrine_delta
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = f.source_total
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = f.deity_total
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = f.history_total
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = f.source_fact_total
  AND (SELECT COUNT(*) FROM temples_shrinedeitycollective) = f.collective_total
  AND (SELECT COUNT(*) FROM temples_shrinefactsourcecitation) = f.citation_total
  AND (SELECT COUNT(*) FROM temples_shrine WHERE COALESCE(goriyaku, '') <> '') = f.shrine_nonempty_goriyaku_total
  AND (SELECT COUNT(*) FROM temples_goriyakutag) = f.goriyaku_tag_master_total
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags) = f.goriyaku_tag_link_total
  AND (SELECT COUNT(*) FROM temples_shrinegoriyakuassignment) = f.goriyaku_assignment_total
  AND (SELECT COUNT(*) FROM temples_historythemeassignment) = f.history_theme_assignment_total
  AND (SELECT COUNT(*) FROM temples_shrine_canonical_anchor) = f.canonical_anchor_total
  AND (SELECT COUNT(*) FROM target_state) = 4
  AND (SELECT COUNT(*) FROM target_state WHERE target_state = 'EXACT_EXISTING') = 4
  AND (SELECT COUNT(*) FROM target_state WHERE same_address_other_name_count > 0) = 0
  AND (SELECT hold_exact_count FROM hold) = 0
  AND (SELECT hold_address_count FROM hold) = 0
  AND (SELECT COUNT(*) FROM target_state WHERE exact_count = 1) = 4
) THEN 1 ELSE 0 END AS h003_c6_post_base_verification_pass
FROM frozen f;
