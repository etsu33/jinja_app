-- PR-2 read-only inspection. No production execution is authorized by this file.
SELECT version();
SELECT app, name, applied FROM django_migrations
WHERE app = 'temples' ORDER BY applied DESC, name DESC LIMIT 5;

SELECT 'Shrine' AS model, COUNT(*) AS rows FROM temples_shrine
UNION ALL SELECT 'History', COUNT(*) FROM temples_shrinehistory
UNION ALL SELECT 'Source', COUNT(*) FROM temples_shrineknowledgesource
UNION ALL SELECT 'Highlight', COUNT(*) FROM temples_shrinehighlight
UNION ALL SELECT 'HighlightHistory', COUNT(*) FROM temples_shrinehighlighthistory;

SELECT c.relname AS table_name, i.relname AS index_name,
       x.indisunique, x.indisvalid, pg_get_indexdef(i.oid) AS definition
FROM pg_index x
JOIN pg_class c ON c.oid = x.indrelid
JOIN pg_class i ON i.oid = x.indexrelid
WHERE c.oid IN ('temples_shrinehistory'::regclass,
                'temples_shrinehighlight'::regclass,
                'temples_shrinehighlighthistory'::regclass)
ORDER BY c.relname, i.relname;

SELECT r.relname AS table_name, c.conname, c.contype,
       c.convalidated, c.condeferrable, pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c JOIN pg_class r ON r.oid = c.conrelid
WHERE c.conrelid IN ('temples_shrinehistory'::regclass,
                     'temples_shrinehighlight'::regclass,
                     'temples_shrinehighlighthistory'::regclass)
ORDER BY r.relname, c.conname;

SELECT attname, attnotnull
FROM pg_attribute
WHERE attrelid = 'temples_shrinehighlighthistory'::regclass
AND attname IN ('highlight_id', 'history_id', 'shrine_id');

-- Must be zero before and after the migration. Do not auto-repair mismatches.
SELECT COUNT(*) AS inconsistent_links
FROM temples_shrinehighlighthistory l
LEFT JOIN temples_shrinehighlight h ON h.id = l.highlight_id
LEFT JOIN temples_shrinehistory t ON t.id = l.history_id
WHERE h.id IS NULL OR t.id IS NULL
   OR l.shrine_id IS DISTINCT FROM h.shrine_id
   OR l.shrine_id IS DISTINCT FROM t.shrine_id;
