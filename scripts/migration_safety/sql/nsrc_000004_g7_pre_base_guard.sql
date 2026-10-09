-- nsrc-000004 G7 pre-Base Production write guard
-- SELECT-only; deliberately raises division-by-zero if the frozen pre-state drifted.
SELECT 1 / CASE WHEN (
  (SELECT COUNT(*) FROM temples_shrine) = 120
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = 137
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = 293
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = 226
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = 23
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp='青海神社' AND address='新潟県加茂市大字加茂字宮山229番地') = 0
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp='青海神社') = 0
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource WHERE source_type='shrine_official' AND (
    lower(url) LIKE '%aomi-jinjya.or.jp/history/gosaisin.html%'
    OR lower(url) LIKE '%aomi-jinjya.or.jp/history/yuisyo.html%'
    OR lower(url) LIKE '%aomi-jinjya.or.jp/gokitou/syurui.html%'
  )) = 0
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact WHERE stable_key IN (
    'aomi_jinja_kamo__prayer__kanai_anzen',
    'aomi_jinja_kamo__prayer__kosazuke_kigan',
    'aomi_jinja_kamo__prayer__anzan_kigan',
    'aomi_jinja_kamo__prayer__kotsu_anzen',
    'aomi_jinja_kamo__prayer__yakubarai',
    'aomi_jinja_kamo__prayer__hoi_barai',
    'aomi_jinja_kamo__prayer__byoki_heiyu_kigan',
    'aomi_jinja_kamo__prayer__mi_no_anzen_kigan',
    'aomi_jinja_kamo__prayer__gokaku_kigan',
    'aomi_jinja_kamo__prayer__shobai_hanjo',
    'aomi_jinja_kamo__prayer__hissho_kigan'
  )) = 0
 THEN 1 ELSE 0 END AS g7_pre_base_guard_pass;
