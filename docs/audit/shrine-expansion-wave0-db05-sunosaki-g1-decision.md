# W0-DB05 洲崎神社 G1 Identity / Duplicate Gate 判定記録

## Status

- Recorded at: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社 / 千葉県館山市
- Batch: `W0-DB05`
- G1 Identity / Duplicate: **PASS**（母艦が本会話で確定）
- G2 Position / Navigation Anchor: **HOLD_POSITION_REVIEW**（2026-10-08、母艦正式判定。PASSではない）
- Candidate Master: `BUILD_READY` / `duplicate_status: NEW`（変更なし）
- Production write: なし
- Candidate Master write: なし
- Schema / Migration / Seed / Recommendation change: なし

## Governing contracts

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-position-contract.md`
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`
- `docs/audit/shrine-expansion-wave0-data-build-plan.md`

## G1 母艦判定

**G1 = PASS**（2026-10-08、本会話における母艦判断）。

### Identity / address evidence

- 名称: 洲崎神社
- 代表住所候補: 千葉県館山市洲崎1344
- 関連番地: 洲崎1697（自然林等の文化財所在地として公的資料に記載）
- 館山市の文化財公式情報: https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html
- 1344と1697は同一神社に関係する番地として説明可能。土地境界・括弧書きの法的意味までは確定しない。

### Production Identity evidence

- Render service: `jinja-backend` (`srv-d4sk1uscjiac739ko5r0`)、branch `develop`
- Render `DATABASE_URL` の設定上のSupabase Project IDと、照合したSupabase project `uigvlbwnsthqqklzpfml` が一致（母艦提供の2026-10-08画面による確認）。**認証情報・接続文字列は記録しない。**
- Supabase project: `kami-musubi-db` / `uigvlbwnsthqqklzpfml`
- Read-only SQL（2026-10-08）: `public.temples_shrine` に対して名称「洲崎」「洲﨑」、住所「館山市洲崎」「洲崎1344」「洲崎1697」を照合し、該当 **0件**。
- Read-only SQL（2026-10-08）: `public.temples_shrinecandidate` に対して名称「洲崎」「洲﨑」、住所「洲崎」を照合し、該当 **0件**。
- Candidate Master上の `duplicate_status: NEW` と矛盾する検出はなかった。

### 判定の射程・留保

このPASSは、館山市公式Identity Source、住所の関連性、上記名称・住所条件でのProduction重複不検出に基づく母艦判定である。異なる別名・住所で登録された同一神社や、座標のみから検出できる衝突の不存在を保証しない。Render実行プロセスの実接続セッションそのものは確認していない。

## G2 Position / Navigation Anchor Gate（母艦正式判定：2026-10-08）

**G2 = HOLD_POSITION_REVIEW**。G1 PASSの前提条件は満たすが、候補点の位置Sourceと採用座標の一致、入口地点の独立検証が未充足のため、正式なNavigation Anchorとして採用しない。

- Official / visitor-facing identity: G1 PASSの洲崎神社を対象とする。
- Primary position provenance: Street View表示座標付近の地図解釈であり、入口そのものを測位したSourceではない。
- Corroboration: GSIの道路接続トポロジーのみ。GSI URLの中心座標を独立測位として扱わない。
- Coordinate conflict / distance delta (m): NOT_VERIFIED。数値を推定・創作しない。
- Position status: `HOLD_POSITION_REVIEW`（監査上の状態）。Candidate Masterの`candidate_status`とは別。
- Release condition: 同一神社のvisitor-facing入口またはNavigation Anchorの位置を、追跡可能な一次Sourceと独立した裏付けで確認し、Sourceとの座標整合を監査記録に残したうえで母艦再判定する。

## G2 evidence boundary

- Navigation Anchor候補: `34.968075, 139.756508`
- Coordinate method: `MAP_INTERPRETED`（Street View付近の表示座標からの解釈）
- Accuracy (m): UNKNOWN
- GSI照合: 道路接続の地形・道路構造を補助的に確認。GSI地図中心座標を入口座標の独立検証として扱わない。
- Entrance point independently verified: NO
- G2: **HOLD_POSITION_REVIEW**。G1 PASSを理由にG2を自動PASSにしない。

## Next steps

- [x] G1母艦判定を監査文書に記録
- [x] G2 Position / Navigation Anchorを正式判定（HOLD_POSITION_REVIEW）
- [ ] 本監査文書のPRを作成

## Change boundary

本記録は監査ドキュメントのみ。Production DB、Candidate Master、既存Seed、推薦ロジック、環境変数は変更しない。
