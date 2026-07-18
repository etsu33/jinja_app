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
| 1 | ~~`backend/temples/_deprecated/`（4ファイル、1313行）の削除~~ **対応済み** | 削除 | P1 | 不要 |
| 2 | ~~`apps/web/src/features/concierge/components/legacy/`＋`ConciergeSections.tsx`（311行）の削除~~ **対応済み**（PR #2077） | 削除 | P1 | 不要 |
| 3 | ~~`recommend_shrines()`と関連LUCK_BONUS系設定の削除~~ **対応済み**（PR #2075） | 削除 | P1 | 不要 |
| 4 | `ConciergeRecommendationClickLog`モデルの削除 | 削除 | P2 | 必要（本番DBのデータ有無） |
| 5 | ~~`PlacesSearchResponse.items`フィールドの削除~~ **対応済み**（PR #2076） | 削除 | P1 | 不要 |
| 6 | ~~`apps/mobile/components/home/`配下未使用コンポーネント群の削除~~ **対応済み**（PR #2081） | 削除 | P1 | 不要 |
| 7 | ~~`apps/mobile`の`nativewind`/`tailwindcss`関連一式の削除~~ **対応済み**（PR #2078） | 削除 | P1 | 不要 |
| 8 | Score v3の到達不能axisキー4件（28エントリ）の削除、またはエイリアス追加による復活 | 保留 | P2 | 必要（Product判断：4 axis正式導入の計画有無） |
| 9 | ~~`BillingState`/`plan_from_profile()`の削除~~ **対応済み** | 削除 | P1 | 不要 |
| 10 | ~~`apps/web/src/lib/auth/token.ts`の削除~~ **対応済み**（PR #2080） | 削除 | P1 | 不要 |
| 11 | ~~Web Analytics dead event（`premium_preview_view`/`next_session`/`next_thread`）の型定義削除~~ **対応済み**（PR #2077） | 削除 | P1 | 不要 |
| 12 | ~~`RecommendationReasonViewModel.why`/`.interpretation`の削除~~ **対応済み**（PR #2077） | 削除 | P1 | 不要 |
| 13 | ~~`useMyGoshuin.ts`・`MapCardListClient.tsx`の削除~~ **対応済み**（PR #2077） | 削除 | P1 | 不要 |
| 14 | ~~`apps/web`の`@heroicons/react`の削除~~ **対応済み**（PR #2077） | 削除 | P1 | 不要 |
| 15 | ~~`SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`のリネーム~~ **対応済み** | 命名修正 | **P0** | 不要（ただし実装担当者への意図確認は推奨） |
| 16 | `.github/workflows/backend-tests.yml`のコメントアウト済み残骸の削除 | 削除 | P3 | 不要 |
| 17 | `.github/workflows/web-tests.yml`の条件式とコメントの乖離解消 | 命名修正 | P3 | 不要 |
| 18 | `ShrineSerializer`互換名の解消 | 互換移行 | P2 | 不要（社内コード変更のみ） |
| 19 | `USE_LLM_CONCIERGE`/`CONCIERGE_THROTTLE`旧env名fallbackの削除 | 互換移行 | P3 | 必要（デプロイ先の実env値） |
| 20 | `BillingStatusLegacyView`（単数形`billing/status/`）の削除 | 削除 | P2 | 必要（本番アクセスログ） |
| 21 | `temples/api/serializers/concierge.py`のCOMPAT LAYER解消 | 互換移行 | P3 | 不要（ロードマップ確認のみ） |
| 22 | `ConciergeThread.recommendations`（v1）読み取りfallbackの削除 | 互換移行 | P2 | 必要（本番DBの旧スレッド残存数） |
| 23 | `apps/web`のBackendオリジンURL環境変数命名の1本化（**監査・移行設計は完了**。`docs/audit/backend-origin-env-migration-design.md`参照。実際の移行実施はVercel確認後の別PR） | 設定統一 | P1 | 不要（ただし設計レビューは必須） |
| 24 | `apps/web`の期限超過互換ルート（`/api/shrines/[id]`）の削除 | 削除 | **P0** | 必要（本番アクセスログ、削除実行の判断材料として） |
| 25 | ~~`apps/web`の`SHOW_NEW_RENDERER`ハードコード解消~~ **対応済み** | 命名修正 | **P0** | 不要 |
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

**対象**: #1（`_deprecated/`4ファイル1313行、**対応済み**）、#3（`recommend_shrines()`+LUCK_BONUS系、**対応済み**）、#9（`BillingState`/`plan_from_profile()`、**対応済み**）

**変更範囲**:

- `backend/temples/_deprecated/`ディレクトリ全体の削除（別PRで対応済み）
- `backend/temples/services/recommendation.py`から`recommend_shrines()`と`ENABLE_LUCK_BONUS`/`LUCK_BASE_FIELD`/`LUCK_BONUS_ELEMENT`/`LUCK_BONUS_POINT`の削除、および専用テスト（`test_recommendation_adapter.py`）の削除
- `backend/users/services/billing.py`から`BillingState`（dataclass）と`plan_from_profile()`の削除（別PRで対応済み）

**#1の実施状況**: `backend/temples/_deprecated/`配下の4ファイルを、参照0件の再確認後に削除した。削除前後でPackage Import Sweepを実行し、API URL、REST Framework設定およびSerializerのImportテストを含む関連テストが通過することを確認した。
**#3の実施状況**: PR #2075で対応済み。`backend/temples/services/recommendation.py`（`recommend_shrines()`と`ENABLE_LUCK_BONUS`/`LUCK_BASE_FIELD`/`LUCK_BONUS_ELEMENT`/`LUCK_BONUS_POINT`）をファイル全体として削除し、専用テスト`test_recommendation_adapter.py`も削除した。Recommendation関連テスト64件・Concierge Rankingテスト86件・Backend Import Sweep・API thin module importテストが通過することを確認済み。
**#9の実施状況**: `backend/users/services/billing.py`の`BillingState`と`plan_from_profile()`は、Backend・Web・Mobile・テストからの参照0件を再確認した上で削除した。現行処理が利用する`is_subscription_active()`は維持した。Billing Checkout、StatusおよびWebhookの契約テスト12件と、Backend Import関連テスト6件が通過することを確認した。

**テスト**:

- `pytest`全体（既存の698件超のテストスイート）が削除後も全て通過することを確認する
- 削除対象を直接importしているファイルが無いことを、削除前に改めて`grep -rn`で全域確認する
- `pytest temples/` `pytest users/`を個別に実行し、import errorが出ないことを確認する

**Rollback条件**:

- CI（`backend-tests.yml`）が失敗した場合は即座にrevert
- 本番デプロイ後、`ImportError`または`AttributeError`がログに出た場合はrevert

### PR-B: Web Dead Code削除

**対象**: #2（`legacy/`+`ConciergeSections.tsx`、**対応済み**）、#10（`src/lib/auth/token.ts`、**対応済み**。ただしPR-Bグルーピング内ではなく単独PR #2080で実施）、#11（Analytics dead event型定義、**対応済み**）、#12（`RecommendationReasonViewModel.why`/`.interpretation`、**対応済み**）、#13（`useMyGoshuin.ts`・`MapCardListClient.tsx`、**対応済み**）、#14（`@heroicons/react`、**対応済み**）

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

**実施状況（PR #2077）**: 上記対象のうち#2・#11・#12・#13・#14の5件を実施した。`concierge/components/legacy/`＋`ConciergeSections.tsx`を削除、`cardEvents.ts`の`premium_preview_view`と`retentionEvents.ts`の`next_session`/`next_thread`を型定義から削除、`buildRecommendationReasonViewModel.ts`から`.why`/`.interpretation`を削除（テストの`.why.*`アサーションは値が同一の`.list.*`/`.debug.reasonKeys.*`へ整合、snapshotも再生成）、`useMyGoshuin.ts`と専用テストを削除、`MapCardListClient.tsx`を削除、`package.json`から`@heroicons/react`を`pnpm remove`で削除した。Web Typecheck・Lintともにエラーなし、Web契約テスト446件pass、関連Unit Test 88件pass、`next build`成功を確認済み。

**#10の実施状況（PR #2080）**: `src/lib/auth/token.ts`はPR #2077の変更ファイル一覧に含まれておらず、`develop`上に現存することを2026-07-18時点で確認していた（計画時点では#2/#11/#12/#13/#14と同一PR対象として整理していたが、実際の実装PRのスコープには含まれなかった）。この漏れに対応するため、`token.ts`単独の削除PR（PR #2080）を起票した。import元・`ACCESS_KEY`/`REFRESH_KEY`/`tokens`各exportの参照元をリポジトリ全域で再検索し0件であることを確認、現行の認証はhttpOnly Cookie（`access_token`/`refresh_token`、`middleware.ts`と`login/route.ts`が使用）に一本化されていることを確認した上で`token.ts`を削除した。Web Typecheck・Lint・契約テスト446件が通過することを確認済み。

### PR-C: Backend API Serializer軽微削除

**対象**: #5（`PlacesSearchResponse.items`フィールド、**対応済み**）

**変更範囲**:

- `backend/temples/api/serializers/places.py`から`items`フィールドを削除

**テスト**:

- `pytest temples/tests/api/`配下のPlaces関連テストを実行
- OpenAPI schema（`schema.yml`）の差分を確認し、`items`フィールドが除外されたことを確認する

**Rollback条件**:

- OpenAPI契約テスト（`dependency-review.yml`ではなくAPI契約系テスト）が失敗した場合はrevert

**実施状況（PR #2076）**: `backend/temples/api/serializers/places.py`から`items`フィールドを削除した。Places関連テスト28件・OpenAPI Schema契約テスト（`test_api_style.py::test_openapi_conventions`、ライブスキーマに対する検証）・API URL smoke test・Backend Importテストが通過することを確認済み。自動生成スキーマファイル（`openapi.json`・`docs/openapi_generated.yaml`）は本PR以前から数千行規模の既存ドリフトがあり、CIでも検証対象外のため意図的に対象外とした。

---

## 5. Mobile未使用依存削除PRの対象確定

### PR-D: Mobile未使用コンポーネント・依存削除

**対象**: #6（`components/home/`配下未使用コンポーネント群、**対応済み**。ただしPR-Dグルーピング内ではなく単独PR #2081で実施）、#7（`nativewind`/`tailwindcss`関連一式、**対応済み**）

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

**実施状況（PR #2078）**: #7（`nativewind`/`tailwindcss`/`@tailwindcss/postcss`/`autoprefixer`と`tailwind.config.js`・`postcss.config.js`・`lib/cn.ts`）のみを実施した。`className`利用0件、Babel/Metro/Expo設定への接続0件を確認した上で削除し、Mobile Typecheck（削除対象由来の新規エラー0件）・Unit Test 57件pass（`npx vitest`による一時実行）・`expo-doctor`19/20 pass・Expo起動確認（Metro Bundler起動・config解決成功）を確認済み。#6（`components/home/`配下未使用コンポーネント群）はPR #2078の実施範囲に含まれておらず、当時「未対応のまま」だった。PR #2078自体の指示が「スタイル依存の削除だけを扱い、未使用Home Component群の削除は行わない」と明記してPR-Dの対象を意図的に縮小したものであり、実装漏れではない。

**#6の実施状況（PR #2081）**: `apps/mobile/components/PopularSection.tsx`・`PopularShrineCard.tsx`・`Skeletons.tsx`・`hooks/usePopularShrines.ts`・`components/home/NearbyShrines.tsx`・`RankingCarousel.tsx`・`SearchChips.tsx`・`MyPageCard.tsx`・`RecentViewed.tsx`・`components/ui/Layout.tsx`（計10ファイル）を対象に、import・JSX・router参照をリポジトリ全域で再検索し、いずれも参照0件であることを確認した上で削除した。Git履歴で旧Home画面（初期MVP実装、2025年9〜10月）由来であることを確認し、現行のHome画面（`app/index.tsx`、2026-06-18の全面刷新以降）は`ConditionFieldsCard`のみに依存する別実装であることを確認した。Mobile Typecheck（削除対象由来の新規エラー0件）・Unit Test 57件pass・Expo起動確認（Metro Bundler起動・config解決成功）を確認済み。`package.json`・lockfile・設定ファイルは変更していない。

---

## 6. Feature Flag整理PRの対象確定

### PR-E: 命名修正・Flag実態の是正

**対象**: #15（`SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`リネーム、**対応済み**）、#25（`SHOW_NEW_RENDERER`ハードコード解消、**対応済み**）

**#15の実施状況**: `backend/temples/services/concierge_chat_ranking.py`の`SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`を`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`へリネームする別PRで対応済み。計算式・加算先は無変更。関連テスト（`test_score_v3_history_signal.py`）およびBackend全体テスト（745件）が通過することを確認済み。互換エイリアスは追加していない（非公開のPython定数で、参照元は定義ファイルとテストファイルの2箇所のみ、環境変数としての読み込みも無いため、旧名を残す実益がないと判断）。

**#25の実施状況**: 事前確認の結果、旧レンダラー分岐（環境変数がfalse相当の場合）は本ハードコード導入（`960dcb31`）より前のコミット`7b185e9e`（PR #847）で実体`ConciergeSections`が既に削除されており、false分岐は「新レンダラー前提」というstubメッセージ、または（`isFilterOpen`側の分岐では）何も表示しない空白になっていた。つまり環境変数制御へ単純に戻しても、ユーザーには壊れた表示しか出せない状態だった。この事実を踏まえ、別PRで新レンダラーへの完全移行を確定した上でFlag自体（`rendererMode.ts`・`SHOW_NEW_RENDERER`・`CONCIERGE_RENDERER`、および`ConciergeClientFull.tsx`側の3箇所の分岐）を削除して対応済み。Score/Recommendation/Analyticsのロジックには一切触れていない。`apps/web/.env.local`の`NEXT_PUBLIC_CONCIERGE_RENDERER`はgitignore対象のローカルファイルのため対象外。

**Rollback条件**:

- リネームPR（#15、対応済み）: マージ後にScore v3関連テストが失敗した場合はrevert（実施時点で745件全てパスを確認済み）
- Flag削除PR（#25、対応済み）: マージ後にConcierge結果画面の表示崩れが確認された場合は`git revert`で即座に巻き戻す（Concierge結果画面はコア体験のため早急な対応が必要）

**優先度に関する注記**: 両者ともP0だが、内容としては別領域（Backend計算ロジックの命名 / Web UIレンダリング制御）であり、依存関係が無いため同一PRにまとめる必要はない。実施順序は任意（レビューの都合で分割してもよい）。

---

## 7. 環境変数統一PRの事前確認項目確定

### PR-F: `apps/web` Backendオリジン環境変数の統一（設計フェーズ先行）

**対象**: #23（`DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`の5系統併存。**監査の結果、`NEXT_PUBLIC_API_BASE_URL`を加えた7系統であることが判明**）

このPRは影響範囲が広いため、実装PRの前に以下の**事前確認**を完了する。

**事前確認項目の実施状況**: 4項目中2・3を完了し、詳細な監査・移行設計を`docs/audit/backend-origin-env-migration-design.md`へ記録した（削除フェーズではなく、監査・設計のみを行うPRとして実施。実装コード・環境変数は変更していない）。1・4は引き続きVercelダッシュボードへのアクセスが必要なため未着手。

1. ~~5つの環境変数名それぞれについて...~~ **未着手（Vercel確認が必要）**。同文書「4. Vercel確認が必要な項目」に4項目の確認リストを整理済み
2. ~~5ファイルそれぞれで、現在どの優先順位でフォールバックしているかを一覧化する~~ **完了**。同文書「2. 各参照ファイルのフォールバック優先順位一覧」で5ファイル（うち1ファイルはログ出力専用の重複コードと判明）を一覧化し、加えて`resolveServerBaseUrl()`への隠れたフォールバック依存という新たなリスクを発見した
3. ~~統一後の単一名称candidateを決め、共通ヘルパー関数への集約設計をレビューする~~ **完了**。同文書「5. 統一後の正式な環境変数名候補」で`BACKEND_ORIGIN`を採用候補として整理し、「6. 共通Backendオリジン解決ヘルパーの責務設計」で既存`backend.ts`の`getDjangoOrigin()`を拡張する設計を整理した（新規ファイル`resolveBackendOrigin.ts`は既存実装との責務重複のため採用しない方針とした）
4. Vercel環境変数の切り替えタイミングとコードデプロイのタイミングをどう同期するか **設計は完了**（同文書「7. 新旧環境変数の移行順序」Phase 1〜4）が、実際の切り替え実施はVercel確認（項目1）の完了後

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

1. **P0（#15, #24, #25）**: 誤解・期限超過リスクがあるため最優先。#24は事前にアクセスログ確認が必要。#15・#25は対応済み
2. **P1のうち外部確認不要な削除（PR-A, PR-B, PR-C, PR-D）**: PR-A（#1・#3・#9）・PR-C（#5）は全項目対応済み。PR-B（#2・#10・#11・#12・#13・#14）・PR-D（#6・#7）はグルーピング内で当初のPR実施範囲から漏れた項目（#10, #6）があったが、それぞれ単独PR（#2080, #2081）で追加対応し、いずれも全項目対応済みとなった
3. **PR-E（Feature Flag整理）**: P0の#15, #25を含むため、実質的に(1)と同時期。両項目とも対応済み
4. **外部環境確認（3節の8件）**: 上記と並行して進められる調査。確認が完了次第、該当するP2項目（#4, #18, #20, #22等）の実装PRへ進む
5. **PR-F（環境変数統一の事前確認）**: 影響範囲が広いため、他の項目が落ち着いてから着手する
6. **保留項目（9節）**: 随時、担当者の確認が取れ次第

---

## 11. 品質確認

- [x] Markdownコードブロックの閉じ確認（コードフェンス数は偶数）
- [x] Markdown参照切れ確認（`docs/audit/legacy-settings-final-audit.md`への参照の実在を確認済み）
- [x] `git diff --check`

---

## 12. P1レガシー削除PR（PR #2075〜#2078）の実施結果とP1残存項目の再集計（2026-07-18時点）

「1. 29件の一覧と優先度・分類」のP1（13件: #1, #2, #3, #5, #6, #7, #9, #10, #11, #12, #13, #14, #23）について、PR #2075〜#2078のマージ後に一覧表と照合して再集計した。

### PR #2075〜#2078のマージ確認

4件全てがGitHub上でMERGED状態であり、各merge commitが`develop`のHEADの祖先に含まれていることを`git merge-base --is-ancestor`で確認した。`develop`上で削除対象の関数名・型フィールド名・依存パッケージ名・ファイルパスを全域再検索し、実装コード・テスト・設定ファイルに参照が残っていないこと（監査文書自身の履歴記述を除く）を確認済み。詳細は各PR本文および`docs/audit/legacy-settings-final-audit.md`「11. 後続対応状況」を参照。

### P1一覧との照合

| # | 項目 | 状態 | 根拠 |
|---:|---|---|---|
| 1 | `_deprecated/`4ファイル削除 | 対応済み | 本文書マージ前に別PRで実施済み |
| 2 | `legacy/`+`ConciergeSections.tsx`削除 | 対応済み | PR #2077。`develop`上で参照0件を再確認 |
| 3 | `recommend_shrines()`+LUCK_BONUS系削除 | 対応済み | PR #2075。`develop`上で参照0件を再確認 |
| 5 | `PlacesSearchResponse.items`削除 | 対応済み | PR #2076。`develop`上で参照0件を再確認 |
| 6 | `apps/mobile/components/home/`未使用コンポーネント群削除 | **未対応** | PR #2078のスコープから意図的に除外。改めて起票が必要 |
| 7 | `nativewind`/`tailwindcss`関連一式削除 | 対応済み | PR #2078。`develop`上で参照0件を再確認 |
| 9 | `BillingState`/`plan_from_profile()`削除 | 対応済み | 本文書マージ前に別PRで実施済み |
| 10 | `apps/web/src/lib/auth/token.ts`削除 | **未対応** | PR-Bグルーピングの計画対象だったが、実施されたPR #2077の範囲に含まれず。`develop`上に現存することを確認 |
| 11 | Analytics dead event型定義削除 | 対応済み | PR #2077。`develop`上で参照0件を再確認 |
| 12 | `RecommendationReasonViewModel.why`/`.interpretation`削除 | 対応済み | PR #2077。`develop`上で参照0件を再確認 |
| 13 | `useMyGoshuin.ts`・`MapCardListClient.tsx`削除 | 対応済み | PR #2077。`develop`上で参照0件を再確認 |
| 14 | `@heroicons/react`削除 | 対応済み | PR #2077。`develop`上で参照0件を再確認 |
| 23 | Backendオリジン環境変数命名統一 | **未対応**（設計フェーズ未着手） | PR-F（7節）の事前確認項目が未着手。外部環境確認は「不要（ただし設計レビューは必須）」に分類されており、「外部環境確認が必要」カテゴリには該当しない |

### 集計

- P1合計: 13件
- 対応済み: **10件**（#1, #2, #3, #5, #7, #9, #11, #12, #13, #14）
- 未対応: **3件**（#6, #10, #23）
- 外部環境確認が必要: 0件（P1の定義上、外部確認を要する項目はP2以上に分類されているため）
- 保留: 0件（P1の中に「保留」分類の項目は無い。保留分類の#8, #26, #27, #28, #29はいずれもP2/P3）

集計値は上表（一覧表との照合）を手動で数え上げて算出し、「1. 29件の一覧と優先度・分類」のP1行数（13行）と一致することを確認した。

未対応3件（#6, #10, #23）は、いずれも実装漏れではなく「計画時点でグルーピングされていたが実施PRのスコープが縮小された」（#6, #10）、または「実装PRの前に必要な事前確認・設計フェーズが未着手」（#23）という理由による。改めて個別PRの起票が必要である。

---

## 13. #10の追加対応（PR #2080）

> **注記（2026-07-18・本節の復元について）**: 本節はPR #2080で一度追加されたが、PR #2081が並行して同一ファイルの末尾へ別セクションを追加した際、squash mergeの結果としてPR #2080側の追記（本節と、1節の#10行・4節PR-B「対象」行・「#10の実施状況」段落・10節item 2の該当箇所）が`develop`上で失われていたことを、本PR（#23監査着手時のdevelop最新化確認）で発見した。該当箇所は全て本PRで復元済みである。PR #2080のコード変更自体（`token.ts`削除）はGit履歴・現行`develop`上に正しく反映されており、影響を受けたのはこの監査文書の記述のみである。

上記12節は2026-07-18時点のスナップショットとして保持する。その後、#10（`apps/web/src/lib/auth/token.ts`）を対象とした単独の削除PR（PR #2080）を実施したため、本節で追加対応の内容と更新後の集計を記録する。

**#10の実施内容**: `apps/web/src/lib/auth/token.ts`のimport元・`ACCESS_KEY`/`REFRESH_KEY`/`tokens`各exportの参照元をリポジトリ全域（`.ts`/`.tsx`）で再検索し、定義箇所自身を除き0件であることを確認した。localStorageベースの認証（`tokens.access`/`tokens.refresh`）が現行コードで使われていないこと、現行の認証はhttpOnly Cookie（`access_token`/`refresh_token`、`middleware.ts`と`login/route.ts`が使用）に一本化されていることを確認した上で削除した。Git履歴から、`token.ts`は2025-10-05に`authToken`として導入され、2025-10-30に`tokens`（`access`/`refresh`両対応）へ拡張されたのを最後に一度も参照されないまま放置されていたことを確認した。Web Typecheck・Lintともにエラーなし、Web契約テスト446件が通過することを確認済み。

**更新後のP1集計（PR #2080時点）**:

- P1合計: 13件
- 対応済み: **11件**（#1, #2, #3, #5, #7, #9, #10, #11, #12, #13, #14）
- 未対応: **2件**（#6, #23）
- 外部環境確認が必要: 0件
- 保留: 0件

残る未対応2件（#6: `apps/mobile/components/home/`配下未使用コンポーネント群、#23: Backendオリジン環境変数命名統一）は、引き続き個別PRの起票が必要である。

---

## 14. #6の追加対応（PR #2081）

その後、#6（`apps/mobile/components/home/`配下未使用コンポーネント群と関連ファイル）を対象とした単独の削除PR（PR #2081）を実施したため、本節で追加対応の内容と更新後の集計を記録する。

**#6の実施内容**: 対象10ファイル（`components/PopularSection.tsx`、`components/PopularShrineCard.tsx`、`components/Skeletons.tsx`、`hooks/usePopularShrines.ts`、`components/home/NearbyShrines.tsx`、`components/home/RankingCarousel.tsx`、`components/home/SearchChips.tsx`、`components/home/MyPageCard.tsx`、`components/home/RecentViewed.tsx`、`components/ui/Layout.tsx`）のimport・JSX・router参照をリポジトリ全域で再検索し、定義箇所自身を除き参照0件であることを確認した上で削除した。Git履歴を確認し、対象ファイルはいずれも初期MVP実装（2025年9〜10月）に由来する旧Home画面のコンポーネント群であり、現行のHome画面（`app/index.tsx`、2026-06-18の全面刷新以降）は`ConditionFieldsCard`のみに依存する別実装であることを確認した。Mobile Typecheck（削除対象由来の新規エラー0件）・Unit Test 57件pass・Expo起動確認（Metro Bundler起動・config解決成功）を確認済み。`package.json`・lockfile・設定ファイルは変更していない。

**更新後のP1集計（PR #2081時点）**:

- P1合計: 13件
- 対応済み: **12件**（#1, #2, #3, #5, #6, #7, #9, #10, #11, #12, #13, #14）
- 未対応: **1件**（#23）
- 外部環境確認が必要: 0件
- 保留: 0件

残る未対応1件（#23: Backendオリジン環境変数命名統一）は、「削除フェーズ」ではなく「環境変数移行フェーズ」として、削除系のP1項目とは別枠で扱う。5系統の環境変数名（`DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`）の統一は、単純な未参照コード削除とは異なり、Vercel本番/Preview環境変数の実際の設定値確認、共通ヘルパーへの設計集約、新旧切替タイミングの調整（7節のPR-F事前確認項目）を要するため、削除系のP1消化とは別のトラックとして計画する。

---

## 15. #23: 環境変数移行フェーズの監査・設計完了（現ドキュメント作成PR）

候補#6（PR #2081）までの完了により、削除系のP1未対応項目は0件となった。残る候補#23は「削除フェーズ」の対象ではなく、独立した「環境変数移行フェーズ」として扱う。

**#23の監査・設計内容**: `apps/web`のBackendオリジン関連環境変数を全域検索した結果、監査時点の5系統（`DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`）に加えて、`NEXT_PUBLIC_API_BASE_URL`（`shrines.server.ts`/`shrineMeaning.server.ts`が参照。既知の`NEXT_PUBLIC_API_BASE`とは別名）が新たに見つかり、**合計7系統**であることを確認した。5ファイルのフォールバック優先順位を一覧化し、うち1ファイル（`login/route.ts`）はログ出力専用の重複コードであること、`shrines.server.ts`/`shrineMeaning.server.ts`が最終的にWeb自身のorigin解決関数（`resolveServerBaseUrl()`）へフォールバックする隠れた依存を持つことを新たに発見した。`apps/web/.env.example`が存在せずREADMEにも記載が無いこと、`docs/core/authentication-flow.md`の既存禁止事項と現状の乖離も確認した。

統一後の名称候補として`BACKEND_ORIGIN`を選定し、既存の`backend.ts`の`getDjangoOrigin()`を拡張する形での共通ヘルパー設計、Phase 1〜4の移行順序（Vercel環境変数追加→共通ヘルパーへの集約→非推奨警告によるモニタリング→旧名削除・文書整備）、各Phaseに対応するRollback条件を設計した。

詳細は`docs/audit/backend-origin-env-migration-design.md`を正本とする。

**実施していないこと**: 実装コード（`backend.ts`・`register/route.ts`・`shrines.server.ts`・`shrineMeaning.server.ts`・`resolveServerBaseUrl.ts`・`api.ts`・`http.ts`・`playwright.config.ts`）、Vercel環境変数、`docs/core/authentication-flow.md`等の既存アーキテクチャ文書は一切変更していない。Phase 1〜4は本設計の承認後、別PRで着手する。

**#23の位置づけ**: 「削除フェーズ」のP1項目（#1〜#14のうち削除系11件）とは異なり、#23は「環境変数移行フェーズ」の1件目として扱う。監査・設計は完了したが、Phase 1（Vercel環境変数追加）以降は4節に整理したVercel確認項目の完了を前提とするため、本節時点では「対応済み」ではなく「監査・設計完了、実施は別トラック」として記録する。
