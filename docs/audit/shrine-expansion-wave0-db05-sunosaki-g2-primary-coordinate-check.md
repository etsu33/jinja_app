# W0-DB05 洲崎神社 G2 入口座標一次Source探索（2026-10-08）

## Result

- Candidate: `wave0-029`（千葉県館山市洲崎神社）
- Requested evidence: 県道257号側の参道入口に紐付く一次Source座標、または現地測位
- Result: **NOT_OBTAINED**（参道入口を示す一次測位座標は未取得）
- G1: `PASS`（変更なし）
- G2: `HOLD_POSITION_REVIEW`（変更なし）
- Production / Candidate Master / Seed write: なし

## Checked sources

| Source | URL | Verified | Limitation |
|---|---|---|---|
| 館山市 文化財「洲崎神社本殿」 | https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html | 本殿の所在地は館山市洲崎1344 | 参道入口の座標ではない |
| 千葉県公式観光「洲崎神社」 | https://maruchiba.jp/spot/detail_12056.html | 随身門裏手の150段の階段、無料駐車場 | 入口ピンの独立測位なし |
| 館山市観光協会 | https://tateyamacity.com/archives/2746 | 住所洲崎1344 | 入口座標なし |
| オープンデータ ジャパン（避難場所） | https://opd.opendata-japan.com/facility_and_place_v5s?facility_id=GV-VZ1G-AXQQ-LBYL | 「洲崎神社」避難場所の座標 `34.96796939, 139.75821923`、精度表示 `ORIGINAL`、元データ更新「平成24年」 | 二次集約サイトであり、参道入口の一次測位と確認できない。ORIGINALを入口精度の保証と解釈しない |
| Yahoo!マップ 洲﨑神社社務所 | https://map.yahoo.co.jp/v3/place/M1EHvZ2zaGI | 洲崎1344の社務所POI | POI位置を参道入口座標と同一視しない |
| Yahoo!マップ 浜鳥居 | https://map.yahoo.co.jp/v3/place/tCzIcffL5gU | 浜鳥居が独立POIとして登録 | 海側鳥居を県道側参道入口と混同しない |

## Coordinate candidates and identity

- Prior entrance candidate: `34.968075, 139.756508` (`MAP_INTERPRETED`、accuracy `UNKNOWN`)
- Newly located open-data coordinate: `34.96796939, 139.75821923`（避難場所POI、**入口座標として不採用**）
- Different feature / provenance: no evidence that these represent the same entrance
- Independently surveyed entrance coordinate: **NO**
- Primary-source georeferenced entrance map: **NOT_FOUND**
- Field GPS survey: **NOT_PERFORMED**（遠隔調査のため）
- G2 decision: **HOLD_POSITION_REVIEW** 継続

## Next evidence needed

- [ ] 神社管理者・自治体による参道入口の位置を示す一次資料、または現地での入口GPS測位を取得
- [ ] 一次資料の対象地点が県道257号側の参道入口であることを写真・動線で確認
- [ ] 独立Sourceと座標を照合し、不確実性・測位日・座標系を記録
- [ ] 母艦がG2を再判定

住所・本殿・社務所・避難場所・浜鳥居のPOI座標は、参道入口の測位値に転用しない。
