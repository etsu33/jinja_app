-- SELECT-only. Safe to run against Production.
--
-- Position Audit v2（docs/audit/shrine-position-ground-truth-v2.md）の
-- Production 側入力。Shrine の Visitor / Navigation Anchor 監査に必要な
-- 位置関連 field を、1行1列の JSON として read-only で出力する。
--
-- 既存の sql/shrine_identity_reconciliation.sql とは別ファイルである。
-- あちらは W0-B02 Reconciliation Gate の契約であり、本ファイルの都合で
-- 列を足すと Gate 側の契約が壊れるため、**変更せずに分離する**。
--
-- 出力は scripts/audit_shrine_positions_v2.py が
-- --production-snapshot として読む。
--
-- 契約:
--   * SELECT 1文のみ。DB へ一切書き込まない（INSERT/UPDATE/DELETE/DDL なし）。
--   * identity normalization を行わない。name_jp / address は格納値を
--     そのまま出力する。正規化は監査側の比較時のみ行う。
--   * kind による絞り込みを行わない。Shrine table 全体が母集団である。
--     temple kind の行も隠さず出力し、監査側で表面化させる。
--   * latitude / longitude は float8 をそのまま出力する。丸めない。
--     PostgreSQL の extra_float_digits 設定によりテキスト表現は変わりうるが、
--     監査側の Seed ↔ Production 比較は Float Comparison Contract v1
--     （rel_tol=0 / abs_tol=1e-12）で行うため round-trip 差分を吸収する。
--
-- 使い方:
--   scripts/migration_safety/readonly_query.sh \
--     ~/.config/kami-musubi/production-db.env DATABASE_URL \
--     scripts/migration_safety/sql/shrine_position_audit_snapshot.sql \
--     > /path/outside/repo/production-position-snapshot.txt
SELECT COALESCE(
         json_agg(
           json_build_object(
             'id', s.id,
             'name_jp', s.name_jp,
             'address', s.address,
             'latitude', s.latitude,
             'longitude', s.longitude,
             'kind', s.kind,
             'place_ref_id', s.place_ref_id
           )
           ORDER BY s.id
         )::text,
         '[]'
       ) AS production_position_snapshot_json
FROM temples_shrine AS s;
