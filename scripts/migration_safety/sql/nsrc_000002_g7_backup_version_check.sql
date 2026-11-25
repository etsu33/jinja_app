-- nsrc-000002 G7 backup client compatibility diagnosis
-- SELECT-only. No credential or connection-target output.
-- pg_dump / pg_dumpall / pg_restore major version must be >= the server major version.
SELECT
  current_setting('server_version') AS server_version,
  current_setting('server_version_num')::int / 10000 AS server_major_version;
