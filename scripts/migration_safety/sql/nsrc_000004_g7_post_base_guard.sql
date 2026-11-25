-- nsrc-000004 G7 post-Base / pre-Knowledge Production guard
-- SELECT-only; raises division-by-zero on any unexpected Base delta.
SELECT 1 / CASE WHEN (
  (SELECT COUNT(*) FROM temples_shrine) = 121
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource) = 137
  AND (SELECT COUNT(*) FROM temples_shrinedeity) = 293
  AND (SELECT COUNT(*) FROM temples_shrinehistory) = 226
  AND (SELECT COUNT(*) FROM temples_shrinesourcefact) = 23
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp='青海神社' AND address='新潟県加茂市大字加茂字宮山229番地') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp='青海神社') = 1
  AND (SELECT COUNT(*) FROM temples_shrine WHERE name_jp='青海神社' AND address='新潟県加茂市大字加茂字宮山229番地' AND abs(latitude - 37.65657387) < 0.00000001 AND abs(longitude - 139.0536436) < 0.00000001 AND COALESCE(goriyaku,'')='') = 1
  AND (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags gt JOIN temples_shrine s ON s.id=gt.shrine_id WHERE s.name_jp='青海神社' AND s.address='新潟県加茂市大字加茂字宮山229番地') = 0
  AND (SELECT COUNT(*) FROM temples_shrineknowledgesource WHERE source_type='shrine_official' AND (
    lower(url) LIKE '%aomi-jinjya.or.jp/history/gosaisin.html%'
    OR lower(url) LIKE '%aomi-jinjya.or.jp/history/yuisyo.html%'
    OR lower(url) LIKE '%aomi-jinjya.or.jp/gokitou/syurui.html%'
  )) = 0
) THEN 1 ELSE 0 END AS g7_post_base_guard_pass;
