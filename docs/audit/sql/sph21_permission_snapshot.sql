-- KAMI MUSUBI / SPH-21 permission snapshot query set v1.1
-- DESIGN ONLY. DO NOT EXECUTE against production without Mother Ship approval.
-- Run S0-S9 in ONE operator-approved REPEATABLE READ READ ONLY transaction
-- (use docs/audit/sql/sph21_permission_snapshot_run.psql; S0 stops the run otherwise).
-- All queries are PostgreSQL catalog-only SELECT statements; no application rows.
-- Store raw results privately; do not commit raw ACLs or role inventories to GitHub.
--
-- v1.1 changes (review: docs/audit/sph21-permission-snapshot-sql-review-2026-11-23.md)
--   * Role names come from JOIN pg_roles (snapshot-consistent), not pg_get_userbyid() / ::regrole.
--   * NULL ACLs carry default_acl = acldefault(...) so the implied privileges are visible.
--   * Deterministic ORDER BY ... COLLATE "C" with full keys (membership grantor included).
--   * Added S0 (snapshot metadata + guard), S7 (column ACLs), S8 (database ACL),
--     S9 (normalized one-row-per-privilege ACL items for diffing).
--   * Every result row starts with snapshot_query = 'S0'..'S9' so one output file can be split.
--   * Scope (schemas listed) is unchanged from v1.0; widening it is a Mother Ship decision.

-- S0. Snapshot metadata and guard. Fails unless the transaction is REPEATABLE READ READ ONLY.
SELECT 'S0' AS snapshot_query, current_setting('server_version_num')::int AS server_version_num,
       current_setting('transaction_isolation') AS transaction_isolation,
       current_setting('transaction_read_only') AS transaction_read_only,
       pg_current_snapshot()::text AS snapshot,
       transaction_timestamp() AS snapshot_started_at,
       CASE WHEN current_setting('transaction_isolation') = 'repeatable read'
             AND current_setting('transaction_read_only') = 'on'
            THEN 'ok'
            ELSE ('STOP:' || current_setting('transaction_isolation'))::int::text
       END AS guard;

-- S1. Role attributes and ALL direct membership edges (retain for transitive graph reconstruction).
SELECT * FROM (
SELECT 'S1' AS snapshot_query, 'role' AS record_kind, r.rolname::text AS object_name, ''::text AS grantor_key,
       jsonb_build_object('role_oid',r.oid,'can_login',r.rolcanlogin,'superuser',r.rolsuper,
          'create_db',r.rolcreatedb,'create_role',r.rolcreaterole,
          'bypass_rls',r.rolbypassrls,'inherit',r.rolinherit,
          'replication',r.rolreplication,'connection_limit',r.rolconnlimit) AS detail
FROM pg_roles AS r
UNION ALL
SELECT 'S1', 'membership', member.rolname || ' -> ' || parent.rolname, COALESCE(grantor.rolname::text, ''),
       jsonb_build_object('member_role',member.rolname,'granted_role',parent.rolname,
          'grantor_role',grantor.rolname,'admin_option',m.admin_option,
          'inherit_option',m.inherit_option,'set_option',m.set_option)
FROM pg_auth_members AS m
JOIN pg_roles AS member ON member.oid=m.member
JOIN pg_roles AS parent ON parent.oid=m.roleid
LEFT JOIN pg_roles AS grantor ON grantor.oid=m.grantor
) AS u
ORDER BY record_kind COLLATE "C", object_name COLLATE "C", grantor_key COLLATE "C";

-- S2. Existing relation ACLs and ownership; relacl NULL means default implied ACL (see default_acl).
SELECT 'S2' AS snapshot_query, n.nspname AS schema_name, c.relname AS object_name, c.relkind AS object_kind,
       o.rolname AS owner_role,
       c.relacl::text AS raw_acl, c.relacl IS NULL AS acl_is_null,
       acldefault('r', c.relowner)::text AS default_acl,
       c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS force_rls
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid=c.relnamespace
JOIN pg_roles AS o ON o.oid=c.relowner
WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
ORDER BY n.nspname COLLATE "C", c.relname COLLATE "C";

-- S3. Existing sequence ACLs and ownership.
SELECT 'S3' AS snapshot_query, n.nspname AS schema_name, c.relname AS sequence_name,
       o.rolname AS owner_role,
       c.relacl::text AS raw_acl, c.relacl IS NULL AS acl_is_null,
       acldefault('s', c.relowner)::text AS default_acl
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid=c.relnamespace
JOIN pg_roles AS o ON o.oid=c.relowner
WHERE n.nspname='public' AND c.relkind='S'
ORDER BY n.nspname COLLATE "C", c.relname COLLATE "C";

-- S4. Default privileges for each grantor role and applicable schema/global scope.
-- pg_default_acl.defaclacl is NOT NULL; acl_is_null is kept only for v1.0 output compatibility.
-- Schema-scoped rows ADD to the built-in defaults; global rows REPLACE them (absence = revoked).
SELECT 'S4' AS snapshot_query, cr.rolname AS creator_role,
       COALESCE(n.nspname::text,'(global)') AS target_schema,
       d.defaclobjtype AS object_type,
       d.defaclacl::text AS raw_acl, d.defaclacl IS NULL AS acl_is_null
FROM pg_default_acl AS d
JOIN pg_roles AS cr ON cr.oid=d.defaclrole
LEFT JOIN pg_namespace AS n ON n.oid=d.defaclnamespace
ORDER BY cr.rolname COLLATE "C", COALESCE(n.nspname::text,'(global)') COLLATE "C", d.defaclobjtype::text COLLATE "C";

-- S5. Schema ACLs and function ACLs (including SECURITY DEFINER and search-path config).
-- A NULL function ACL means EXECUTE for PUBLIC (see default_acl).
SELECT * FROM (
SELECT 'S5' AS snapshot_query, 'schema' AS record_kind, n.nspname::text AS schema_name, n.nspname::text AS object_name,
       o.rolname AS owner_role, n.nspacl::text AS raw_acl,
       acldefault('n', n.nspowner)::text AS default_acl,
       jsonb_build_object('acl_is_null',n.nspacl IS NULL) AS detail
FROM pg_namespace AS n
JOIN pg_roles AS o ON o.oid=n.nspowner
WHERE n.nspname IN ('public','extensions','auth','graphql')
UNION ALL
SELECT 'S5', 'function', n.nspname::text,
       p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
       o.rolname, p.proacl::text,
       acldefault('f', p.proowner)::text,
       jsonb_build_object('acl_is_null',p.proacl IS NULL,
         'security_definer',p.prosecdef,'function_kind',p.prokind,
         'configuration',to_jsonb(p.proconfig))
FROM pg_proc AS p
JOIN pg_namespace AS n ON n.oid=p.pronamespace
JOIN pg_roles AS o ON o.oid=p.proowner
WHERE n.nspname='public'
) AS u
ORDER BY record_kind COLLATE "C", schema_name COLLATE "C", object_name COLLATE "C";

-- S6. RLS state and complete policy metadata for every in-scope table.
SELECT 'S6' AS snapshot_query, n.nspname AS schema_name, c.relname AS table_name,
       o.rolname AS owner_role,
       c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS force_rls,
       p.polname AS policy_name, p.polcmd AS command, p.polpermissive AS permissive,
       CASE WHEN p.oid IS NULL THEN NULL ELSE
         ARRAY(SELECT CASE WHEN x.role_oid=0 THEN 'PUBLIC' ELSE COALESCE(pr.rolname::text, x.role_oid::text) END
               FROM unnest(p.polroles) AS x(role_oid)
               LEFT JOIN pg_roles AS pr ON pr.oid=x.role_oid
               ORDER BY (CASE WHEN x.role_oid=0 THEN 'PUBLIC'
                              ELSE COALESCE(pr.rolname::text, x.role_oid::text) END) COLLATE "C")
       END AS policy_roles,
       pg_get_expr(p.polqual,p.polrelid) AS using_expression,
       pg_get_expr(p.polwithcheck,p.polrelid) AS with_check_expression
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid=c.relnamespace
JOIN pg_roles AS o ON o.oid=c.relowner
LEFT JOIN pg_policy AS p ON p.polrelid=c.oid
WHERE n.nspname='public' AND c.relkind IN ('r','p')
ORDER BY n.nspname COLLATE "C", c.relname COLLATE "C", p.polname COLLATE "C" NULLS FIRST;

-- S7. Column-level ACLs (GRANT ... (column) ON ...). Not visible in relacl.
SELECT 'S7' AS snapshot_query, n.nspname AS schema_name, c.relname AS object_name, a.attname AS column_name,
       a.attacl::text AS raw_acl
FROM pg_attribute AS a
JOIN pg_class AS c ON c.oid=a.attrelid
JOIN pg_namespace AS n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
  AND a.attnum > 0 AND NOT a.attisdropped AND a.attacl IS NOT NULL
ORDER BY n.nspname COLLATE "C", c.relname COLLATE "C", a.attname COLLATE "C";

-- S8. Current database ACL (CONNECT / TEMPORARY / CREATE). The database name is not output.
SELECT 'S8' AS snapshot_query, o.rolname AS owner_role,
       d.datacl::text AS raw_acl, d.datacl IS NULL AS acl_is_null,
       acldefault('d', d.datdba)::text AS default_acl
FROM pg_database AS d
JOIN pg_roles AS o ON o.oid=d.datdba
WHERE d.datname = current_database();

-- S9. Normalized ACL items: one row per (object, grantee, privilege). Primary input for diffs.
-- acl_source = 'explicit' (stored ACL) | 'implied_default' (NULL ACL, expanded with acldefault).
WITH acl_objects AS (
    SELECT 'relation'::text AS object_type, n.nspname::text AS schema_name, c.relname::text AS object_name,
           c.relowner AS owner_oid, c.relacl AS acl, acldefault('r', c.relowner) AS default_acl
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
    UNION ALL
    SELECT 'sequence', n.nspname, c.relname, c.relowner, c.relacl, acldefault('s', c.relowner)
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind='S'
    UNION ALL
    SELECT 'column', n.nspname, c.relname || '.' || a.attname, c.relowner, a.attacl, NULL::aclitem[]
    FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
      AND a.attnum > 0 AND NOT a.attisdropped AND a.attacl IS NOT NULL
    UNION ALL
    SELECT 'schema', n.nspname, n.nspname, n.nspowner, n.nspacl, acldefault('n', n.nspowner)
    FROM pg_namespace n WHERE n.nspname IN ('public','extensions','auth','graphql')
    UNION ALL
    SELECT 'function', n.nspname, p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
           p.proowner, p.proacl, acldefault('f', p.proowner)
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public'
    UNION ALL
    SELECT 'database', '', '(current)', d.datdba, d.datacl, acldefault('d', d.datdba)
    FROM pg_database d WHERE d.datname = current_database()
    UNION ALL
    SELECT 'default_acl:' || d.defaclobjtype::text, COALESCE(n.nspname::text,'(global)'),
           cr.rolname::text, d.defaclrole, d.defaclacl, NULL::aclitem[]
    FROM pg_default_acl d JOIN pg_roles cr ON cr.oid=d.defaclrole
    LEFT JOIN pg_namespace n ON n.oid=d.defaclnamespace
)
SELECT * FROM (
SELECT 'S9' AS snapshot_query, o.object_type, o.schema_name, o.object_name,
       CASE WHEN o.acl IS NULL THEN 'implied_default'
            WHEN cardinality(o.acl) = 0 THEN 'explicit_empty'
            ELSE 'explicit' END AS acl_source,
       CASE WHEN x.grantee IS NULL THEN NULL WHEN x.grantee=0 THEN 'PUBLIC'
            ELSE COALESCE(ge.rolname::text, x.grantee::text) END AS grantee,
       x.privilege_type,
       x.is_grantable,
       COALESCE(gr.rolname::text, x.grantor::text) AS grantor,
       (x.grantee = o.owner_oid) AS grantee_is_owner
FROM acl_objects o
LEFT JOIN LATERAL aclexplode(COALESCE(o.acl, o.default_acl)) AS x ON true
LEFT JOIN pg_roles ge ON ge.oid=x.grantee
LEFT JOIN pg_roles gr ON gr.oid=x.grantor
) AS u
ORDER BY object_type COLLATE "C", schema_name COLLATE "C", object_name COLLATE "C",
         grantee COLLATE "C" NULLS FIRST, privilege_type COLLATE "C" NULLS FIRST, grantor COLLATE "C" NULLS FIRST;
