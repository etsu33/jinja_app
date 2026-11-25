# W0-DB05 洲崎神社 G2 Position Evidence Collection

- Recorded: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社（館山市）
- Base decision: G1 `PASS` / G2 `HOLD_POSITION_REVIEW`
- Scope: read-only public-source collection; no Production / Candidate Master / Seed change

## Evidence register

| ID | Authority / source | Evidence | Supports | Limitation |
|---|---|---|---|---|
| P01 | 館山市（文化財・本殿） https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html | 本殿所在地は館山市洲崎1344 | 神社Identity・所在地 | 道路からの参道入口座標ではない |
| P02 | 千葉県公式観光 https://maruchiba.jp/spot/detail_12056.html | 洲崎1344、無料駐車場、随身門裏手から150段の階段 | 参拝者動線と施設の存在 | 駐車場・入口のピン座標なし |
| P03 | 館山市観光案内所 https://tateyamacity.com/en/shrines-temples/sunosaki-shrine/ | 1344、社殿へ150段の石段 | P02の参拝動線補強 | 入口測位なし |
| P04 | 一の宮案内 https://ichinomiya.gr.jp/026.html | 神社前の道路を隔て海側に鳥居、社殿は御手洗山中腹 | 浜鳥居と社殿参道の区別 | 鳥居と参道入口の精密位置なし |
| P05 | 現地訪問記録（第三者） https://chiba.jinja.love/?p=32877 | 県道257号（房総フラワーライン）に面した入口を写真付きで紹介 | 参道入口の地物識別 | 非一次資料、GPS・座標メタデータの独立検証なし |
| P06 | 千葉県文化財 https://www.pref.chiba.lg.jp/kyouiku/bunkazai/bunkazai/p431-051.html | 自然林所在地は洲崎1697他、所有者は洲崎神社 | 1344/1697の用途差の説明 | 参道入口座標ではない |

## Navigation Anchor selection

- Candidate coordinate (unchanged): `34.968075, 139.756508`
- Acquisition: `MAP_INTERPRETED`（既存Street View位置の解釈）
- Intended feature: 県道257号側の参道入口付近
- Competing feature to exclude: 道路を挟んだ浜鳥居（海側）
- Entrance coordinate independently surveyed / primary-source georeferenced: **NO**
- Accuracy in metres: **UNKNOWN**
- Coordinate-to-entrance discrepancy: **NOT_VERIFIED**
- G2 decision: **HOLD_POSITION_REVIEW**（維持）
- Coordinate promoted to Production `Shrine.latitude/longitude`: **NO**

## Missing evidence / release checklist

- [ ] 神社管理者または公的管理主体による参拝者向け入口・駐車場案内の地図上の位置特定
- [ ] 現地入口のGPS測位、または一次Sourceに結び付く座標付き地図情報の取得
- [ ] 独立した地図・現地資料による同一入口の照合（浜鳥居・社殿中心点との混同排除）
- [ ] 座標と根拠URL・取得日・座標系・精度または不確実性を監査記録に固定
- [ ] 母艦によるG2再判定（自動PASS禁止）

## Source discipline

住所や観光案内の地図中心座標はNavigation Anchorの一次測位に置き換えない。第三者訪問写真は入口地物の同定補助としてのみ使用し、GPS根拠へ格上げしない。G1判定は変更しない。
