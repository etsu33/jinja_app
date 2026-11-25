-- SELECT-only. Production Schema Remediation Gate postcheck for temples 0107/0108.

-- 1. 0107 / 0108 must both be recorded.
SELECT app, name, applied FROM django_migrations WHERE app = 'temples' AND name IN ('0107_restore_places_seed_schema','0108_remove_legacy_temples_models') ORDER BY name;

-- 2. Expected physical table state: 2 restored tables PRESENT, 4 retired legacy tables ABSENT.
WITH expected(table_name, expected_state) AS (VALUES ('places_seed','PRESENT'),('places_seed_state','PRESENT'),('temples_like','ABSENT'),('temples_concierge_recommendation_click_log','ABSENT'),('temples_conciergehistory','ABSENT'),('temples_rankinglog','ABSENT')) SELECT e.table_name, e.expected_state, CASE WHEN t.table_name IS NULL THEN 'ABSENT' ELSE 'PRESENT' END AS actual_state FROM expected e LEFT JOIN information_schema.tables t ON t.table_schema = 'public' AND t.table_name = e.table_name ORDER BY e.table_name;

-- 3. Restored table columns.
SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name IN ('places_seed','places_seed_state') ORDER BY table_name, ordinal_position;

-- 4. Primary keys and foreign keys on restored tables.
SELECT tc.table_name, tc.constraint_type, tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name FROM information_schema.table_constraints tc LEFT JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.constraint_schema = kcu.constraint_schema LEFT JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.constraint_schema = ccu.constraint_schema WHERE tc.table_schema = 'public' AND tc.table_name IN ('places_seed','places_seed_state') AND tc.constraint_type IN ('PRIMARY KEY','FOREIGN KEY') ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

-- 5. Explicit indexes defined by migration 0075.
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname IN ('places_seed_pref_co_27f61e_idx','places_seed_is_acti_04817c_idx','places_seed_last_st_b771ca_idx','places_seed_cooldow_b4ea36_idx') ORDER BY tablename, indexname;
