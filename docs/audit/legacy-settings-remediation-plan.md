> **Status: Reference**
>
> 本ドキュメントは、`docs/audit/legacy-settings-final-audit.md`が整理した29件の後続PR候補に、優先度・分類・実行条件を付与した実施計画である。
>
> 本文書は計画のみを目的とし、実装・削除・設定変更は行っていない。優先順位の最終判断・実施承認は母艦へ差し戻す。

# Legacy Settings Remediation Plan

## 目的

`docs/audit/legacy-settings-final-audit.md`「9. 推奨する後続PR一覧」に整理した29件の候補について、以下を確定する。

- 優先度（P0〜P3）
- 分類（削除 / 命名修正 / 設定統一 / 互換移行 / 保留）
- 外部環境確認が必要な項目の分離
- 実行可能な単位へのPRグルーピングと、各PRの変更範囲・テスト・Rollback条件

本文書では実装・削除・設定変更のいずれも行っていない。

---

## 1. 29件の一覧と優先度・分類

元の29件は、監査文書「9. 推奨する後続PR一覧」の4区分（低リスク14件・命名整合3件・移行完了後8件・追加調査4件）に対応する。以下では通し番号を付け直し、優先度と分類を付与する。

### 優先度の定義

| 優先度 | 意味 |
|---|---|
| P0 | 現状のまま放置すると誤解・誤操作につながるリスクがある。命名が実態と矛盾している、または削除期限を既に超過している項目 |
| P1 | 参照0件を確認済みの安全な削除候補。外部確認を要さず、単独PRとして着手できる |
| P2 | 削除・変更自体は妥当だが、実行前に本番DB・アクセスログ等の外部環境確認、または移行の完了確認が必要 |
| P3 | 影響が軽微、または方針判断待ちのため急ぎでない。調査・判断が先 |

### 一覧

| # | 項目 | 分類 | 優先度 | 外部環境確認 |
|---:|---|---|---|---|
| 1 | `backend/temples/_deprecated/`（4ファイル、1313行）の削除 | 削除 | P1 | 不要 |
| 2 | `apps/web/src/features/concierge/components/legacy/`＋`ConciergeSections.tsx`（311行）の削除 | 削除 | P1 | 不要 |
| 3 | `recommend_shrines()`と関連LUCK_BONUS系設定の削除 | 削除 | P1 | 不要 |
| 4 | `ConciergeRecommendationClickLog`モデルの削除 | 削除 | P2 | 必要（本番DBのデータ有無） |
| 5 | `PlacesSearchResponse.items`フィールドの削除 | 削除 | P1 | 不要 |
| 6 | `apps/mobile/components/home/`配下未使用コンポーネント群の削除 | 削除 | P1 | 不要 |
| 7 | `apps/mobile`の`nativewind`/`tailwindcss`関連一式の削除 | 削除 | P1 | 不要 |
| 8 | Score v3の到達不能axisキー4件（28エントリ）の削除、またはエイリアス追加による復活 | 保留 | P2 | 必要（Product判断：4 axis正式導入の計画有無） |
| 9 | `BillingState`/`plan_from_profile()`の削除 | 削除 | P1 | 不要 |
| 10 | `apps/web/src/lib/auth/token.ts`の削除 | 削除 | P1 | 不要 |
| 11 | Web Analytics dead event（`premium_preview_view`/`next_session`/`next_thread`）の型定義削除 | 削除 | P1 | 不要 |
| 12 | `RecommendationReasonViewModel.why`/`.interpretation`の削除 | 削除 | P1 | 不要 |
| 13 | `useMyGoshuin.ts`・`MapCardListClient.tsx`の削除 | 削除 | P1 | 不要 |
| 14 | `apps/web`の`@heroicons/react`の削除 | 削除 | P1 | 不要 |
| 15 | ~~`SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`のリネーム~~ **対応済み** | 命名修正 | **P0** | 不要（ただし実装担当者への意図確認は推奨） |
| 16 | `.github/workflows/backend-tests.yml`のコメントアウト済み残骸の削除 | 削除 | P3 | 不要 |
| 17 | `.github/workflows/web-tests.yml`の条件式とコメントの乖離解消 | 命名修正 | P3 | 不要 |
| 18 | `ShrineSerializer`互換名の解消 | 互換移行 | P2 | 不要（社内コード変更のみ） |
| 19 | `USE_LLM_CONCIERGE`/`CONCIERGE_THROTTLE`旧env名fallbackの削除 | 互換移行 | P3 | 必要（デプロイ先の実env値） |
| 20 | `BillingStatusLegacyView`（単数形`billing/status/`）の削除 | 削除 | P2 | 必要（本番アクセスログ） |
| 21 | `temples/api/serializers/concierge.py`のCOMPAT LAYER解消 | 互換移行 | P3 | 不要（ロードマップ確認のみ） |
| 22 | `ConciergeThread.recommendations`（v1）読み取りfallbackの削除 | 互換移行 | P2 | 必要（本番DBの旧スレッド残存数） |
| 23 | `apps/web`のBackendオリジンURL環境変数命名の1本化 | 設定統一 | P1 | 不要（ただし設計レビューは必須） |
| 24 | `apps/web`の期限超過互換ルート（`/api/shrines/[id]`）の削除 | 削除 | **P0** | 必要（本番アクセスログ、削除実行の判断材料として） |
| 25 | `apps/web`の`SHOW_NEW_RENDERER`ハードコード解消 | 命名修正 | **P0** | 不要 |
| 26 | ルート`.env.example`と`backend/.env.example`の統合要否判断 | 保留 | P3 | 不要（文書検索のみ） |
| 27 | `apps/mobile`の未到達ルート6画面の実機導線確認 | 保留 | P2 | 必要（実機/シミュレータ操作） |
| 28 | `NOMINATIM_BASE`/`NOMINATIM_EMAIL`未接続の設計意図確認 | 保留 | P3 | 必要（実装担当者への確認） |
| 29 | `apps/web`の`checkout_session_id`互換分岐の要否確認 | 保留 | P3 | 必要（Stripe Checkout設定の確認） |

**P0（3件）の選定理由**: いずれも「現状のまま放置すると誤解・誤操作につながる」項目である。#15は命名が「shadow専用」を示唆するが実際には本番ランキングへ直接影響しており、この命名を信じた開発者が誤って無効化・変更するリスクがある。#24は文書化された削除期限（2026-04-01）を本監査時点で3.5ヶ月超過しており、削除保留の判断が更新されないまま放置されている。#25は「デモ用の一時対応」が本番コードに固定化されたままであり、コード上のコメントが示す意図（デモ後に環境変数制御へ戻す）と実態が乖離している。

---

## 2. 分類ごとの集計

| 分類 | 件数 | 該当 # |
|---|---:|---|
| 削除 | 16 | 1,2,3,4,5,6,7,9,10,11,12,13,14,16,20,24 |
| 命名修正 | 3 | 15,17,25 |
| 設定統一 | 1 | 23 |
| 互換移行 | 4 | 18,19,21,22 |
| 保留 | 5 | 8,26,27,28,29 |

合計29件（16+3+1+4+5）。

---

## 3. 外部環境確認が必要な項目

以下は、リポジトリ内の調査だけでは実行可否を判断できず、外部環境（本番DB・アクセスログ・実機・EAS/Stripe管理画面等）の確認、または実装担当者・母艦への判断照会を要する。

| # | 項目 | 必要な確認 | 確認主体 |
|---:|---|---|---|
| 4 | `ConciergeRecommendationClickLog`削除 | 本番DBに実データが入っていないか | Backend運用担当 |
| 8 | Score v3到達不能axis 4件 | 4 axisの正式導入計画の有無 | Product判断 |
| 19 | 旧env名fallback削除 | デプロイ先（Render等）が旧env名を使っていないか | インフラ担当 |
| 20 | `BillingStatusLegacyView`削除 | 単数形エンドポイントへの本番アクセス実績 | Backend運用担当 |
| 22 | `ConciergeThread.recommendations`(v1)fallback削除 | 本番DBに残る旧スレッド（v2フィールドが空）の件数 | Backend運用担当 |
| 27 | Mobile未到達ルート6画面 | 実機/シミュレータでTab経由の到達性 | Mobile開発担当 |
| 28 | `NOMINATIM_BASE`/`NOMINATIM_EMAIL`未接続 | settings.pyへの取り込み意図があったか | 実装担当者への照会 |
| 29 | `checkout_session_id`互換分岐 | 現行Stripe Checkout設定の`success_url`仕様 | Billing担当 |

これら8件は、外部確認が完了するまで実装PRに着手しない。

---

## 4. Deadコード削除PRの対象確定

参照0件を確認済みで、外部環境確認を要さない削除候補（P1）を1つのPR群として確定する。

### PR-A: Backend Dead Code削除

**対象**: #1（`_deprecated/`4ファイル1313行）、#3（`recommend_shrines()`+LUCK_BONUS系）、#9（`BillingState`/`plan_from_profile()`）

**変更範囲**:

- `backend/temples/_deprecated/`ディレクトリ全体の削除
- `backend/temples/services/recommendation.py`から`recommend_shrines()`と`ENABLE_LUCK_BONUS`/`LUCK_BASE_FIELD`/`LUCK_BONUS_ELEMENT`/`LUCK_BONUS_POINT`の削除、および専用テスト（`test_recommendation_adapter.py`）の削除
- `backend/users/services/billing.py`から`BillingState`（dataclass）と`plan_from_profile()`の削除

**テスト**:

- `pytest`全体（既存の698件超のテストスイート）が削除後も全て通過することを確認する
- 削除対象を直接importしているファイルが無いことを、削除前に改めて`grep -rn`で全域確認する
- `pytest temples/` `pytest users/`を個別に実行し、import errorが出ないことを確認する

**Rollback条件**:

- CI（`backend-tests.yml`）が失敗した場合は即座にrevert
- 本番デプロイ後、`ImportError`または`AttributeError`がログに出た場合はrevert

### PR-B: Web Dead Code削除

**対象**: #2（`legacy/`+`ConciergeSections.tsx`）、#10（`src/lib/auth/token.ts`）、#11（Analytics dead event型定義）、#12（`RecommendationReasonViewModel.why`/`.interpretation`）、#13（`useMyGoshuin.ts`・`MapCardListClient.tsx`）、#14（`@heroicons/react`）

**変更範囲**:

- `apps/web/src/features/concierge/components/legacy/`と`ConciergeSections.tsx`の削除
- `apps/web/src/lib/auth/token.ts`の削除
- `cardEvents.ts`の`premium_preview_view`、`retentionEvents.ts`の`next_session`/`next_thread`を型定義から削除
- `buildRecommendationReasonViewModel.ts`から`.why`/`.interpretation`フィールドを削除
- `useMyGoshuin.ts`・`MapCardListClient.tsx`の削除（テストファイルの扱いも合わせて確認）
- `package.json`から`@heroicons/react`を削除

**テスト**:

- `pnpm --filter ./apps/web test:contract`（Web契約テスト全件）
- `pnpm --filter ./apps/web typecheck`（型エラーが出ないことを確認。特に`.why`/`.interpretation`削除後に参照が残っていないか型検査で検出する）
- `pnpm --filter ./apps/web lint`
- `useMyGoshuin.ts`のテストファイルが削除対象を参照している場合は、テストファイルも合わせて削除するか、削除の是非を個別に再検討する

**Rollback条件**:

- CI（`web-tests.yml`）の型検査・contract testが失敗した場合は即座にrevert
- 本番デプロイ後、該当コンポーネント・フィールドの参照エラーがブラウザコンソール/Sentry等で検出された場合はrevert

### PR-C: Backend API Serializer軽微削除

**対象**: #5（`PlacesSearchResponse.items`フィールド）

**変更範囲**:

- `backend/temples/api/serializers/places.py`から`items`フィールドを削除

**テスト**:

- `pytest temples/tests/api/`配下のPlaces関連テストを実行
- OpenAPI schema（`schema.yml`）の差分を確認し、`items`フィールドが除外されたことを確認する

**Rollback条件**:

- OpenAPI契約テスト（`dependency-review.yml`ではなくAPI契約系テスト）が失敗した場合はrevert

---

## 5. Mobile未使用依存削除PRの対象確定

### PR-D: Mobile未使用コンポーネント・依存削除

**対象**: #6（`components/home/`配下未使用コンポーネント群）、#7（`nativewind`/`tailwindcss`関連一式）

**変更範囲**:

- `apps/mobile/components/home/PopularSection.tsx`、`PopularShrineCard.tsx`、`Skeletons.tsx`、`hooks/usePopularShrines.ts`の削除
- `apps/mobile/components/home/NearbyShrines.tsx`、`RankingCarousel.tsx`、`SearchChips.tsx`、`MyPageCard.tsx`（コンポーネント版）、`RecentViewed.tsx`の削除
- `apps/mobile/components/ui/Layout.tsx`（`Spacer`/`Section`）の削除
- `package.json`から`nativewind`、`tailwindcss`、`@tailwindcss/postcss`、`autoprefixer`を削除
- `tailwind.config.js`、`postcss.config.js`、`lib/cn.ts`の削除

**テスト**:

- `apps/mobile`のExpo起動確認（`npx expo start`相当。Render無料枠の制約とは無関係のローカル/CI検証のため、Shell前提の運用提案には該当しない）
- 既存のMobileテストスイート（存在する場合）を実行
- 削除対象コンポーネントを他のどのファイルもimportしていないことを、削除前に改めてgrepで確認する

**Rollback条件**:

- Expo起動時にモジュール解決エラーが出た場合はrevert
- EASビルドが失敗した場合はrevert

**優先度に関する注記**: #6・#7は参照0件を確認済みのP1だが、#8（未到達ルート6画面、P2）とは独立した別問題である。#6・#7はどの画面からも到達しない「孤立コンポーネント」、#27（旧番号）は「Tab登録されているが導線がないルート」であり、混同しないよう本PRの対象からは除外している。

---

## 6. Feature Flag整理PRの対象確定

### PR-E: 命名修正・Flag実態の是正

**対象**: #15（`SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`リネーム、**対応済み**）、#25（`SHOW_NEW_RENDERER`ハードコード解消、未着手）

**#15の実施状況**: `backend/temples/services/concierge_chat_ranking.py`の`SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`を`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`へリネームする別PRで対応済み。計算式・加算先は無変更。関連テスト（`test_score_v3_history_signal.py`）およびBackend全体テスト（745件）が通過することを確認済み。互換エイリアスは追加していない（非公開のPython定数で、参照元は定義ファイルとテストファイルの2箇所のみ、環境変数としての読み込みも無いため、旧名を残す実益がないと判断）。

**変更範囲（#25、未実施）**:

- `apps/web/src/features/concierge/rendererMode.ts`の`SHOW_NEW_RENDERER`ハードコードを解消し、`NEXT_PUBLIC_CONCIERGE_RENDERER`環境変数による制御へ戻す。ただし、旧レンダラー分岐（環境変数がfalse相当の場合）が現在も正しく動作するか事前に確認する。動作しない場合は、新レンダラーへの完全移行を確定した上でFlag自体を削除する（いずれの方針を採るかは母艦の判断を仰ぐ）

**テスト（#25、未実施分）**:

- `SHOW_NEW_RENDERER`解消PRでは、`NEXT_PUBLIC_CONCIERGE_RENDERER`を明示的に`true`/`false`双方に設定した状態で`ConciergeClientFull.tsx`のレンダリング結果を目視確認する（Web契約テストに両パターンのケースが無ければ追加する）

**Rollback条件**:

- リネームPR（#15、対応済み）: マージ後にScore v3関連テストが失敗した場合はrevert（実施時点で745件全てパスを確認済み）
- `SHOW_NEW_RENDERER`解消PRで、環境変数未設定時のデフォルト挙動が本番想定と異なる場合は即座にrevert（Concierge結果画面はコア体験のため、表示崩れは早急な巻き戻しが必要）

**優先度に関する注記**: 両者ともP0だが、内容としては別領域（Backend計算ロジックの命名 / Web UIレンダリング制御）であり、依存関係が無いため同一PRにまとめる必要はない。実施順序は任意（レビューの都合で分割してもよい）。

---

## 7. 環境変数統一PRの事前確認項目確定

### PR-F: `apps/web` Backendオリジン環境変数の統一（設計フェーズ先行）

**対象**: #23（`DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`の5系統併存）

このPRは影響範囲が広いため、実装PRの前に以下の**事前確認**を完了する。

**事前確認項目**:

1. 5つの環境変数名それぞれについて、`apps/web/.env`・`apps/web/.env.local`・Vercelの環境変数設定（本番/Preview）に実際にどの名前が設定されているかを確認する（Vercel側の確認はダッシュボードで行い、本監査の範囲外）
2. `src/lib/server/backend.ts`、`src/app/api/auth/login/route.ts`、`src/app/api/auth/register/route.ts`、`src/lib/api/shrines.server.ts`、`src/lib/api/shrineMeaning.server.ts`の5ファイルそれぞれで、現在どの優先順位でフォールバックしているかを一覧化する（本監査で確認済みの情報を土台に、さらに他の参照箇所が無いか`grep -rn "DJANGO_ORIGIN\|BACKEND_ORIGIN\|DJANGO_API_BASE_URL\|BACKEND_URL\|BACKEND_BASE_URL"`で再確認する）
3. 統一後の単一名称candidate（例: `BACKEND_ORIGIN`への一本化）を決め、共通ヘルパー関数（例: `src/lib/server/resolveBackendOrigin.ts`）への集約設計を先にレビューする
4. Vercel環境変数の切り替えタイミングとコードデプロイのタイミングをどう同期するか（新旧両対応の移行期間を設けるか）を決める

**変更範囲（事前確認完了後）**:

- 上記5ファイルのフォールバックロジックを共通ヘルパーへ置き換える
- 旧環境変数名を移行期間中は互換フォールバックとして残すか、Vercel側の設定切り替えと同時に完全撤廃するかは、事前確認4の結果に従う

**テスト**:

- Backend疎通を伴う統合テスト（`route.test.ts`系）が全て通過することを確認する
- ローカル環境・Preview環境・本番環境それぞれでBackendへの疎通が失敗しないことを確認する（Preview環境での確認はVercel Previewデプロイで実施）

**Rollback条件**:

- Preview環境でBackend疎通が失敗した場合はマージしない
- 本番デプロイ後、Backend API呼び出しが失敗するログが検出された場合は即座にrevertし、旧フォールバックロジックへ戻す

---

## 8. Compatibility項目ごとの削除条件と期限

Compatibility（互換目的で現役）に分類された項目について、削除条件と目安の確認期限を設定する。期限は「この日までに削除する」ではなく「この日までに削除条件を再確認する」ためのチェックポイントである。

| # | 項目 | 削除条件 | 確認期限（目安） |
|---:|---|---|---|
| 18 | `ShrineSerializer`互換名 | `backend/temples/views.py`側の呼び出し元が新名`ShrineDetailSerializer`へ更新されること | 2026-09-30 |
| 19 | `USE_LLM_CONCIERGE`/`CONCIERGE_THROTTLE`旧env名fallback | Render本番環境変数に旧名が設定されていないことを確認できること | 2026-08-31 |
| 20 | `BillingStatusLegacyView`（単数形） | 本番アクセスログで直近30日間のアクセス数が0件であること | 2026-08-31 |
| 21 | `temples/api/serializers/concierge.py`のCOMPAT LAYER | 新モジュール`temples/serializers/concierge.py`へ残りのシンボル（`ConciergeHistorySerializer`等）が移行完了すること | 期限設定なし（新モジュール移行のロードマップ次第。ロードマップの有無自体を2026-09-30までに確認） |
| 22 | `ConciergeThread.recommendations`（v1）読み取りfallback | 本番DBで`recommendations_v2`が空かつ`recommendations`（v1）のみ存在するスレッド件数が0件であること | 2026-09-30 |
| 23（環境変数、参考） | Backendオリジン環境変数5系統 | 統一後の単一名称へVercel本番/Preview環境変数が切り替わり、旧名参照コードが無くなること | 2026-08-31（事前確認完了目標） |

以下は「削除しない」既存判断を本監査で確認済みのため、削除条件・期限を設定しない。

| 項目 | 理由 |
|---|---|
| `concierge_chat_compat`（Web/Mobileの`message`/`query`吸収） | WebとMobile双方が現役で依存する設計。Web側を`query`へ統一するという別の対応（本文書の対象外）が前提 |
| `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`のfallback | `DATABASE_URL`未設定環境での個別変数運用を今後も許容する設計判断 |
| `provider="revenuecat"`（Backend/Web/Mobile enum） | 将来のRevenueCat対応を見越した意図的プレースホルダ（既存監査文書で確認済み） |
| `placeCaches.ts`の「互換: 旧名を残す」 | `PlaceSuggestBox.tsx`が現役で使用中の関数名。リネームの優先度は低い |
| `apps/mobile`の`recommendationReasonV4 → reasonFacts → legacyReason`フォールバック | 旧フォーマットデータの残存状況が未確認のため、期限設定は時期尚早（#27の実機導線確認と合わせて、後日Mobileデータ監査で再検討） |

---

## 9. 保留項目（#8, #26, #27, #28, #29）

以下は削除・変更いずれの実装PRも起票せず、判断材料を揃えるための調査タスクとして扱う。

| # | 項目 | 次のアクション | 担当想定 |
|---:|---|---|---|
| 8 | Score v3到達不能axis 4件 | 4 axis（`relationship_repair`/`health`/`protection`/`travel_safe`）の正式導入予定を母艦へ確認する | Product |
| 26 | ルート`.env.example`統合要否 | ルート`.env.example`を案内する手順書が他に無いか全文検索し、無ければ統合PRを起票する | Backend/インフラ |
| 27 | Mobile未到達ルート6画面 | 実機/シミュレータでTab経由の到達性を確認する | Mobile開発担当 |
| 28 | `NOMINATIM_BASE`/`NOMINATIM_EMAIL`未接続 | settings.pyへの正式取り込み意図があったか実装担当者へ確認する | Backend |
| 29 | `checkout_session_id`互換分岐 | Stripe Checkout設定の`success_url`が実際に返すパラメータ名を確認する | Billing担当 |

---

## 10. 実施順序の目安

本監査・本計画では実施そのものを行わないが、着手する場合の目安順序を示す。

1. **P0（#15, #24, #25）**: 誤解・期限超過リスクがあるため最優先。#24は事前にアクセスログ確認が必要。#15は対応済み
2. **P1のうち外部確認不要な削除（PR-A, PR-B, PR-C, PR-D）**: 参照0件を再確認した上で並行して進められる
3. **PR-E（Feature Flag整理）**: P0の#15, #25を含むため、実質的に(1)と同時期
4. **外部環境確認（3節の8件）**: 上記と並行して進められる調査。確認が完了次第、該当するP2項目（#4, #18, #20, #22等）の実装PRへ進む
5. **PR-F（環境変数統一の事前確認）**: 影響範囲が広いため、他の項目が落ち着いてから着手する
6. **保留項目（9節）**: 随時、担当者の確認が取れ次第

---

## 11. 品質確認

- [x] Markdownコードブロックの閉じ確認（コードフェンス数は偶数）
- [x] Markdown参照切れ確認（`docs/audit/legacy-settings-final-audit.md`への参照の実在を確認済み）
- [x] `git diff --check`
