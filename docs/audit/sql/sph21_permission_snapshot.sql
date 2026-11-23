-- KAMI MUSUBI / SPH-21 permission snapshot query set v1.0
-- DESIGN ONLY. DO NOT EXECUTE against production without Mother Ship approval.
-- Run each query within one operator-approved REPEATABLE READ READ ONLY transaction.
-- All queries are PostgreSQL catalog-only SELECT statements; no application rows.
-- Store raw results privately; do not commit raw ACLs or role inventories to GitHub.

-- S1. Role attributes and ALL direct membership edges (retain for transitive graph reconstruction).
SELECT 'role' AS record_kind, r.rolname AS object_name,
       jsonb_build_object('can_login',r.rolcanlogin,'superuser',r.rolsuper,
          'create_db',r.rolcreatedb,'create_role',r.rolcreaterole,
          'bypass_rls',r.rolbypassrls,'inherit',r.rolinherit,
          'replication',r.rolreplication,'connection_limit',r.rolconnlimit) AS detail
FROM pg_roles AS r
UNION ALL
SELECT 'membership', member.rolname || ' -> ' || parent.rolname,
       jsonb_build_object('member_role',member.rolname,'granted_role',parent.rolname,
          'grantor_role',grantor.rolname,'admin_option',m.admin_option,
          'inherit_option',m.inherit_option,'set_option',m.set_option)
FROM pg_auth_members AS m
JOIN pg_roles AS member ON member.oid=m.member
JOIN pg_roles AS parent ON parent.oid=m.roleid
LEFT JOIN pg_roles AS grantor ON grantor.oid=m.grantor
ORDER BY record_kind, object_name;

-- S2. Existing relation ACLs and ownership; relacl NULL means default implied ACL.
SELECT n.nspname AS schema_name, c.relname AS object_name, c.relkind AS object_kind,
       pg_get_userbyid(c.relowner) AS owner_role,
       c.relacl::text AS raw_acl, c.relacl IS NULL AS acl_is_null,
       c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS force_rls
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
ORDER BY schema_name, object_name;

-- S3. Existing sequence ACLs and ownership.
SELECT n.nspname AS schema_name,c.relname AS sequence_name,
       pg_get_userbyid(c.relowner) AS owner_role,
       c.relacl::text AS raw_acl,c.relacl IS NULL AS acl_is_null
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind='S'
ORDER BY schema_name,sequence_name;

-- S4. Default privileges for each grantor role and applicable schema/global scope.
SELECT pg_get_userbyid(d.defaclrole) AS creator_role,
       COALESCE(n.nspname,'(global)') AS target_schema,
       d.defaclobjtype AS object_type,
       d.defaclacl::text AS raw_acl, d.defaclacl IS NULL AS acl_is_null
FROM pg_default_acl AS d
LEFT JOIN pg_namespace AS n ON n.oid=d.defaclnamespace
ORDER BY creator_role,target_schema,object_type;

-- S5. Schema ACLs and function ACLs (including SECURITY DEFINER and search-path config).
SELECT 'schema' AS record_kind,n.nspname AS schema_name,n.nspname AS object_name,
       pg_get_userbyid(n.nspowner) AS owner_role,n.nspacl::text AS raw_acl,
       jsonb_build_object('acl_is_null',n.nspacl IS NULL) AS detail
FROM pg_namespace AS n
WHERE n.nspname IN ('public','extensions','auth','graphql')
UNION ALL
SELECT 'function',n.nspname,
       p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
       pg_get_userbyid(p.proowner),p.proacl::text,
       jsonb_build_object('acl_is_null',p.proacl IS NULL,
         'security_definer',p.prosecdef,'function_kind',p.prokind,
         'configuration',to_jsonb(p.proconfig))
FROM pg_proc AS p
JOIN pg_namespace AS n ON n.oid=p.pronamespace
WHERE n.nspname='public'
ORDER BY record_kind,schema_name,object_name;

-- S6. RLS state and complete policy metadata for every in-scope table.
SELECT n.nspname AS schema_name,c.relname AS table_name,
       pg_get_userbyid(c.relowner) AS owner_role,
       c.relrowsecurity AS rls_enabled,c.relforcerowsecurity AS force_rls,
       p.polname AS policy_name,p.polcmd AS command,p.polpermissive AS permissive,
       CASE WHEN p.oid IS NULL THEN NULL ELSE
         ARRAY(SELECT CASE WHEN role_oid=0 THEN 'PUBLIC'
                           ELSE role_oid::regrole::text END
               FROM unnest(p.polroles) AS role_oid ORDER BY role_oid)
       END AS policy_roles,
       pg_get_expr(p.polqual,p.polrelid) AS using_expression,
       pg_get_expr(p.polwithcheck,p.polrelid) AS with_check_expression
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid=c.relnamespace
LEFT JOIN pg_policy AS p ON p.polrelid=c.oid
WHERE n.nspname='public' AND c.relkind IN ('r','p')
ORDER BY schema_name,table_name,policy_name NULLS FIRST;
