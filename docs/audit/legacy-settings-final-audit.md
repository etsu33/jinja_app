> **Status: Reference**
>
> 本ドキュメントは、KAMI MUSUBIリポジトリ全体を横断した古い設定・廃止済み設定・互換目的の設定・未使用設定の監査結果である。
>
> 本監査は分類のみを目的とし、削除・リファクタ・設定変更は行っていない。実装コードは一切変更していない。

# Legacy Settings Final Audit

## 目的

KAMI MUSUBIの現行リポジトリ（Backend / `apps/web` / `apps/mobile` / `.github/workflows`）を横断し、環境変数・Feature Flag・Enum・fallback・旧キー・互換レイヤー・未使用コードを安全に分類する。

本監査の目的は削除ではなく、現状を根拠付きで分類することである。

---

## 監査方法

- Web / Mobile / Backendそれぞれで、各設定の定義箇所と参照箇所をgrepで確認した
- 参照が0件であることを確認できた場合のみDeadと判定した（推測のみでのDead判定は行っていない）
- 実装コードは一切変更していない
- Render無料枠の制約（インタラクティブShellが無い）を前提とした運用提案はしていない
- 既存の関連監査文書（後述）を確認し、重複調査を避けつつ本監査の結論と突き合わせた

---

## 既存の関連監査文書との関係

本監査に着手する前に、以下の既存文書がリポジトリ内に存在することを確認した。本監査はこれらの結論と矛盾しないことを確認し、必要な箇所で参照している。

| 文書 | 関係 |
|---|---|
| `docs/infra/env_policy.md` | env運用方針の正本。「`backend/.env.example`を正本とする」という方針を本監査でも踏襲した |
| `docs/audit/release-config-and-billing-audit.md` | Billing判定窓口・env読み込み順序をすでに整理済み。`backend/.env` / `backend/.env.dev` / `backend/.env.bak`を「廃止・非推奨」と既に明記している。本監査ではBackend層の対象を広げ、Web/Mobile/CI/Recommendation等を追加で監査した |
| `docs/audit/deprecated-files-cleanup.md` | `backend/temples/_deprecated/`と`apps/web/src/features/concierge/components/legacy/`を「別PRで判断する」保留事項として記録済み。本監査ではこの2つを実際に参照解析し、判断材料を提供した（判断そのものは本監査でも確定させず、後続PR候補として整理する） |
| `docs/audit/score-v3-shadow-audit.md` | `SCORE_V3_MODE`がshadow固定で動作することを確認済み。本監査では同じ変数について「未デプロイだが本番反映可能な実装が既に存在する」という追加事実を記録した |
| `docs/audit/score-v3-consultation-axis-history-theme-mapping.md` | Score v3のaxis×history_theme対応表の設計メモ。本監査で発見した「到達不能な4 axisキー」の背景情報として関連する |
| `docs/audit/cross-platform-event-contract.md` | Analytics送信処理（Web/Mobile）の既存監査。本監査ではAnalytics固有の深掘りはこの文書へ委譲し、設定・Flag観点のみを扱った |
| `docs/audit/product-document-responsibility-audit.md` | `history_theme`関連の定義・実装整合監査（本セッションの別PRで実施済み）。Recommendation/Meaning Translation節の一部はこの監査と重複するため、詳細はそちらへ委譲する |

---

## 分類サマリー

| 分類 | 件数（概算） | 意味 |
|---|---:|---|
| Active | 15 | 現行機能で必要 |
| Compatibility | 16 | 旧データ・旧クライアント互換のため必要 |
| Deprecated | 7 | 移行後に削除予定、または既に移行完了し置き換え済み |
| Dead | 30 | 参照がなく削除可能性が高い |
| Uncertain | 14 | 根拠不足で判断保留 |

件数は本監査で個別に確認した項目数の概算であり、リポジトリ全体の環境変数・Flagを網羅した総数ではない。

---

## 1. Backend: 環境変数・設定ファイル

### 1.1 env ファイルの構成

| 設定名 | 定義場所 | 参照場所 | 対象レイヤ | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|---|
| `backend/.env.local` | リポジトリ直下（Git管理外） | `backend/shrine_project/settings.py:47-49`が起動時に読み込む | Backend | 通常起動時の環境変数読み込み元 | Active | なし | なし | なし |
| `backend/.env.test` | リポジトリ直下（Git管理外） | `settings.py:59-63`がpytest判定時に`.env.local`の後に上書き読み込み | Backend | pytest専用の環境変数上書き | Active | なし | なし | なし |
| `backend/.env.example` | `backend/.env.example`（Git管理下） | `backend/README.md:82,85`、`docs/infra/env_policy.md:9,31`で「正本」と明記 | Backend | 開発者が`.env.local`を作る際のテンプレート | Active | なし | なし | なし |
| `backend/.env.dev`, `backend/.env.bak` | `docs/audit/release-config-and-billing-audit.md:123-125`が既に「廃止・非推奨」「運用対象外」と明記 | 参照なし（既存監査で確認済み、本監査でも再確認しrepo内grep結果は0件） | Backend | なし | Deprecated（既存監査で確定済み） | 低（既に非運用と明記済み） | 実ファイルが現存するか（Git管理外のため本監査では確認不可） | ファイル削除は開発者各自のローカル作業のため、リポジトリ側の後続PRは不要 |
| `backend/.env.dev.old`（Git管理外、`.old`拡張子で発見） | ローカルファイル | 参照なし | Backend | なし。ファイル名からも既に個人環境で退避済みと判断できる | Deprecated | 低（Git非管理のため repo への影響なし） | なし | なし（Git管理外のためリポジトリ側の対応不要） |
| `.env.example`（リポジトリルート） | `.env.example`（Git管理下） | `docs/infra/env_policy.md`は`backend/.env.example`のみを正本として明記。ルート`.env.example`を指す記述は`README.md`/`backend/README.md`のいずれにも無し | Backend（想定） | 不明瞭。`backend/.env.example`のサブセット（LLM_*/Stripe/Throttle関連の変数を含まない）であり、内容が古い可能性がある | Uncertain | 中（誤って開発者がこちらをコピーすると環境変数が不足する） | ルート`.env.example`を今も案内している手順書・READMEが他に無いか全文検索する。無ければ`backend/.env.example`への一本化を検討する | `.env.example`（ルート）を`backend/.env.example`へ統合、またはルート側に「`backend/.env.example`を参照」の誘導コメントを追加するPR |
| `.env.render.example`（Git管理外） | リポジトリルート | 参照なし（README等からの案内なし） | Backend（Render用） | Render本番環境の変数サンプルと推測されるが、`backend/.env.example`との使い分けがドキュメント化されていない | Uncertain | 中 | Render運用手順書（`docs/infra/render-startup.md`等）にこのファイルへの案内があるか確認する | なし（現時点では追加調査が先） |
| `NOMINATIM_BASE` / `NOMINATIM_EMAIL`（ルート`.env`に定義あり） | Git管理外のルート`.env`。`backend/shrine_project/settings.py`には該当する`env.str(...)`代入が存在しない | Backend: `temples/services/geocode.py:36,48,85`が`getattr(settings, "NOMINATIM_EMAIL"/"NOMINATIM_BASE", default)`で参照するが、settings.py側に代入が無いため常にデフォルト値（`unknown@example.com` / `https://nominatim.openstreetmap.org`）にフォールバックする | Backend | 環境変数としては定義されているが、Djangoの`settings`オブジェクトには反映されないため実質的に無効 | Uncertain | 低〜中（意図しない挙動があれば要修正だが、現状デフォルト値で動作しており実害は確認できていない） | `settings.py`に`NOMINATIM_BASE`/`NOMINATIM_EMAIL`を正式に取り込む意図があったか、設計上デフォルト値のみで運用する想定だったかを実装担当者に確認する | `settings.py`へ`NOMINATIM_BASE = env.str("NOMINATIM_BASE", default="...")`を追加するか、`.env`側の記述を削除するかのいずれかを行うPR（本監査では判断しない） |
| `USE_GOOGLE` / `PLACES_RADIUS_M` / `PLACES_LIMIT` / `THROTTLE_ANON` / `THROTTLE_USER` / `THROTTLE_PLACES` / `THROTTLE_SHRINES` / `CACHE_BACKEND`（ルート`.env`に定義あり） | Git管理外のルート`.env` | Backend全体（`.py`ファイル）でのgrep結果0件。シェルスクリプト・Makefile・YAML設定でも参照0件 | 不明 | 定義されているが、いずれの層からも読み取られていない | Dead（ただしGit管理外ファイルのため repo としてのDead判定は参考情報扱い） | 低（Git非管理のためリポジトリへの影響なし） | なし | なし（Git管理外のためリポジトリ側の対応不要。開発者への周知のみ） |

### 1.2 互換目的の環境変数（Backend設定コード内で明示的に互換と記載）

| 設定名 | 定義場所 | 参照場所 | 対象レイヤ | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|---|
| `USE_LLM_CONCIERGE`（env） | `backend/shrine_project/settings.py:95-100`。コード中コメント「互換: USE_LLM_CONCIERGE（過去の env 名を吸収）」 | `CONCIERGE_USE_LLM = env.bool("CONCIERGE_USE_LLM", ...) or env.bool("USE_LLM_CONCIERGE", ...)`として合成。`USE_LLM_CONCIERGE`単体を直接読む箇所は他に無し | Backend | 旧env名からの移行期間中の後方互換 | Compatibility | 低 | 現行の`.env.example`系ファイルは新名`CONCIERGE_USE_LLM`のみを案内しているか確認する（`backend/.env.example:14`は`CONCIERGE_USE_LLM`のみ記載済みを確認） | 旧名を使うデプロイ先が無いことを確認できた段階で、settings.py側のfallback読み込みを削除するPR |
| `CONCIERGE_THROTTLE`（env） | `backend/shrine_project/settings.py:329-331`。コード中コメント「旧 env 名互換（これも "あれば上書き" だけ）」 | `_rates["concierge"]`を上書きする箇所でのみ参照。新名`THROTTLE_CONCIERGE`と併存 | Backend | 旧env名からの移行期間中の後方互換 | Compatibility | 低 | 同上 | 同上（`THROTTLE_CONCIERGE`への一本化が完了した後に削除） |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD`（env） | `backend/shrine_project/settings.py:126-131` | `build_database_config()`で`DATABASE_URL`が未設定の場合のみ使用される最終fallback。`DB_NAME`/`DB_USER`/`DB_PASSWORD`はさらに`POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD`（Docker Compose標準命名）へのfallbackも持つ | Backend | `DATABASE_URL`方式への移行前の個別変数指定方式。Render本番は`DATABASE_URL`を使用するため、通常運用では到達しない分岐 | Compatibility | 中（`DATABASE_URL`が未設定の環境で暗黙的に使われるため、削除するとローカル個別変数運用が壊れる） | ローカル開発で個別DB変数運用を使っている開発者が現存するか確認する | 現時点では削除不要。将来`DATABASE_URL`方式へ完全統一する場合のみ検討 |
| `concierge_chat_compat` / URL `concierge/chat/` | `backend/temples/api/views/compat.py`、`backend/temples/api/urls.py:133-134` | Web: `apps/web/src/lib/conciergeChat.ts:45`が`message`キーで送信。Mobile: `apps/mobile/app/concierge/index.tsx:415`が`query`キーで送信。両者を吸収する実装であることをコードで確認済み。Webは`hooks.ts:363`で応答の`echo:`プレフィックスを除去する処理も持つ（`compat.py`側が付与する`reply`フィールドに依存） | Backend / Web / Mobile | Web/Mobileでリクエストのキー名（`message` vs `query`）が異なるため、両対応の互換ラッパとして現役稼働している | Compatibility（現役） | 高（WebとMobileの両方が依存しているため、削除するとどちらかが壊れる） | Web側を`query`キーへ統一できればラッパを簡略化できる可能性がある | Web側リクエストのキー名を`message`から`query`へ統一した上で、`compat.py`のmessage処理分岐を削除するPR（実施は本監査の範囲外） |

---

## 2. Backend: Billing / Premium判定

サブエージェントによる調査結果を集約した。詳細な参照箇所はサブエージェントの報告に基づく。

| 設定名 | 定義場所 | 参照場所 | 対象レイヤ | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|---|
| `BillingState`（dataclass） | `backend/users/services/billing.py:13-20` | Backend/Web/Mobile/テストいずれも参照0件 | Backend | 不明。同ファイル内の`is_subscription_active`/`ACTIVE_STATUSES`のみが実際に使われている | Dead | 低 | Git履歴でいつ最後に使われていたか確認する | 削除PR（`billing.py`から`BillingState`と`plan_from_profile()`を削除） |
| `plan_from_profile()` | `backend/users/services/billing.py:42-48` | 参照0件 | Backend | 実際のplan判定は`temples/services/billing_state.py:get_billing_status()`が別ロジックで行っている | Dead | 低 | 同上 | 同上 |
| `apply_stripe_subscription_event()` | `backend/users/services/stripe_webhook.py:418-421`。コード中コメントで「互換エイリアス（過去コード向け）」と明記 | 参照0件 | Backend | `apply_stripe_event()`への単純委譲。呼び出し元が存在しない | Compatibility（実利用0件） | 低 | 過去にこの関数名を直接呼んでいたコード・外部連携が本当に無いか、Git履歴で確認する | 参照0件が確定した後続PRで削除を検討 |
| `BillingStatusLegacyView` / URL `billing/status/`（name=`billing-status-legacy`） | `backend/temples/api/views/billing.py:69-70`、`backend/temples/api/urls.py:139` | Backend: ルーティング上は有効。Web: `apps/web/src/lib/api/billing.ts:18`, `billing.server.ts:25`は複数形`billings/status/`のみ使用。Mobile: `apps/mobile/lib/billing.ts:113,127`も同様。テスト参照0件 | Backend | 現行の正本エンドポイントは複数形`billings/status/`。単数形は`@extend_schema(exclude=True)`でOpenAPIスキーマからも除外済み | Deprecated | 低〜中（外部クライアントが直接叩いている可能性はゼロではない） | 単数形エンドポイントへのアクセスログが実際に存在するか、本番アクセスログで確認する | アクセス実績が0であることを確認できたら、エンドポイント削除PR |
| `STRIPE_PREMIUM_PRICE_ID` | `backend/shrine_project/settings.py:363`（`STRIPE_PRICE_ID`へのfallback定義）、`backend/temples/services/billing_checkout.py:26-31` | 全`.env`系ファイル（Git管理下・管理外問わず）に実値の設定なし | Backend | `STRIPE_PRICE_ID`の代替名として二重定義されているが、実運用は常に`STRIPE_PRICE_ID`経由 | Compatibility | 低 | 将来複数プラン（例: 年額/月額）を扱う際にこの変数名を再利用する計画があるか確認する | 計画が無ければ`STRIPE_PRICE_ID`への一本化PR |
| `provider="revenuecat"`（PROVIDER_CHOICES enum値） | `backend/temples/api/views/billing.py:24`、`backend/temples/services/billing_state.py:13`、Web/Mobileの型定義にも存在 | 分岐ロジック・SDK依存なし。`docs/audit/release-config-and-billing-audit.md:38`が「将来のモバイル課金連携候補」と明記 | Backend / Web / Mobile | 将来のRevenueCat対応を見越した先行enum拡張。既存監査文書で意図が明記されている | Compatibility（将来拡張の意図的プレースホルダ） | 低 | なし（既存文書で意図確認済み） | なし（実装が必要になった時点で着手） |
| `trial_ends_at`（BillingStatusフィールド） | `backend/temples/services/billing_state.py:22`、`backend/temples/api/views/billing.py:39` | 常に`None`を返す実装。Web/Mobileは型としては保持するが値は常にnull | Backend / Web / Mobile | APIコントラクトとして予約されているが、Stripeのtrial期間を反映するロジックは未実装 | Uncertain | 低（フィールド自体はActive、ロジックのみ未実装） | Trial機能を提供する計画があるか確認する | 計画が無ければ、フィールド自体をAPIコントラクトから削除するか判断するPR |

---

## 3. Backend: Recommendation / Meaning Translation / Score v2・v3

サブエージェントによる調査結果を集約した。`history_theme`固有の定義整合性については本セッションの別PR（`docs/audit/product-document-responsibility-audit.md`15〜16節）で既に監査済みのため、本節では設定・Flag観点のみを扱う。

| 設定名 | 定義場所 | 参照場所 | 対象レイヤ | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|---|
| `SCORE_V3_MODE`（env） | `backend/temples/services/concierge_chat_ranking.py:61-88`（`resolve_score_v3_mode`/`resolve_score_v3_mode_detail`） | Backend: `concierge_chat.py:51-52,647-654`で実際にソートキー切替に使用。テスト複数（`test_score_v3_feature_flag.py`等）で`active`/`shadow`両方を検証済み。Web/Mobile: 参照なし。全`.env`系ファイルに設定なし | Backend | `active`にするとScore v3が本番ランキングのソートキーになる。実装は完了しているが、どの環境変数ファイルにも設定されておらず、現状は常に`shadow`（デフォルト）で動作 | Active（未デプロイ・dormant） | 中（Flagを立てるだけでランキングアルゴリズムが切り替わるため、有効化には別途検証が必要） | `docs/audit/score-v3-shadow-audit.md`の「shadow observation only」という説明が、"切替不能"という意味なのか"デフォルトがshadow"という意味なのかを明確化する | Score v3を本番反映する計画がある場合、有効化の判断基準（品質評価）を先に整備するPR |
| `SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` | `backend/temples/services/concierge_chat_ranking.py:247-250` | Backend: `resolve_history_theme_candidate_boost()`経由で`score_need_rank_weighted`（1117-1121行）と候補prefilterスコア（1576-1582行）に直接加算。**Shadowではなく現行の実ランキングに影響している** | Backend | `SCORE_V3_HISTORY_THEME_BY_AXIS`の単純コピーだが、命名に反して常時有効な本番ロジックとして機能している | Uncertain（命名がミスリーディング） | 中（既に本番影響がある機能のため、リネームや無効化はランキング結果に直接影響する） | 「SCORE_V3」という命名が意図的か、単なる命名ミスかを実装担当者に確認する | 命名を`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`（SCORE_V3を含まない名前）へリネームするPR。動作は変えず名前のみ変更 |
| `relationship_repair` / `health` / `protection` / `travel_safe`（axisキー、上記2テーブル内、計28エントリ） | `concierge_chat_ranking.py:164-172,209-217,227-235,236-244` | `consultation_axis`の唯一の生成元`domain/consultation_axis.py`の`normalize_consultation_axis()`が許可する値（`money_growth,career_change,independence,rest_healing,restart_mindset,nature_reset,study_success,other`）にこれら4値が含まれておらず、到達不能。ユニットテストが関数を直接呼ぶケース以外に参照なし | Backend / テスト | 到達不能なテーブルエントリ | Dead | 低（到達経路が無いため削除しても挙動に影響しない） | これら4 axisを将来正式導入する計画があるか確認する | 計画が無ければ、4キー28エントリを削除するPR。計画があれば`CONSULTATION_AXIS_ALIASES`側にエイリアスを追加して到達可能にするPR |
| `recommend_shrines()`および`ENABLE_LUCK_BONUS`/`LUCK_BASE_FIELD`/`LUCK_BONUS_ELEMENT`/`LUCK_BONUS_POINT` | `backend/temples/services/recommendation.py:9-80` | 自身のテスト（`test_recommendation_adapter.py`）以外の呼び出し元0件。`settings.py`にも該当設定値の定義なし | Backend / テスト | なし | Dead | 低 | なし | 関数・設定・専用テストを削除するPR |
| `ConciergeRecommendationClickLog` | `backend/temples/models_concierge_analytics.py:42-71`、migration `0076` | モデル定義とmigrationのみ。`.objects.create(`呼び出し0件、admin登録なし、シリアライザ/APIエンドポイント参照なし、テスト参照なし | Backend | なし（テーブルは存在するがwrite/read経路が皆無） | Dead | 低〜中（DBテーブルを伴うため、削除にはmigrationが必要） | 本番DBに実データが入っていないか確認してから削除する | モデル削除＋DROP TABLE migrationのPR（本番データ有無の確認後） |
| `ConciergeThread.recommendations`（v1フィールド） | `backend/temples/models.py:449` | `api_views_concierge.py:889-910,926-927`で`recommendations_v2`と併せて書き込み継続。`journey_timeline.py:103`で`thread.recommendations_v2 or thread.recommendations or []`という読み取りfallbackに使用 | Backend | v2導入前の旧スレッドデータを読むためのfallback | Compatibility | 中（削除すると古いスレッドのJourney Timeline表示が欠落する可能性） | 旧スレッド（v2フィールドが空のもの）が本番DBにどれだけ残っているか確認する | 旧データの移行（v1→v2へのバックフィル）が完了した後に、v1フィールドの読み取りfallbackを削除するPR |
| `PublicMode = Literal["need","compat"]` | `concierge_chat_ranking.py:23,725-752,1681-1723` | Backend: `concierge_chat.py:554`ほか多数。Web: `ConciergeClientFull.tsx`等で「相性ベース」モードとして能動的に使用 | Backend / Web | 生年月日ベースの「相性」推薦モード（query未入力時の代替フロー）。名前に"compat"を含むが、レガシー互換シムではなく現役のプロダクト機能 | Active | なし | なし（誤解を避けるため名称の由来をコード内コメントで明記すると良い） | なし（機能名の紛らわしさに関する軽微なドキュメント改善のみ、任意） |
| `rec["score_v2"]`（APIレスポンス項目） | `concierge_chat_ranking.py:1450`、算出元`recommendation_score_v2.py` | Backend: `concierge_chat.py`、`concierge_explanation_payload.py`等で`_explanation_payload.score_v2`として送出。Web: `_explanation_payload`自体は消費されるが、`score_v2`/`scoreV2`キー単体の参照は確認できず。Mobile: 参照なし | Backend / Web（未消費） | Backendの構造化出力としては現行スコアリングと一致する値を持つが、Webが個別キーとして消費していない | Uncertain | 低〜中（APIレスポンスからの削除はAPI契約変更に相当する） | Web側でこのフィールドを将来使う計画（デバッグ表示等）があるか確認する | 計画が無ければAPIレスポンスから除外するか判断するPR（API契約テストの更新が必要） |

---

## 4. Backend: API / Serializer / 互換レイヤー

| 設定名 | 定義場所 | 参照場所 | 対象レイヤ | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|---|
| `backend/temples/_deprecated/`（4ファイル、計1313行） | `backend/temples/_deprecated/api_views_legacy.py`（956行）、`api_views_places_legacy.py`（282行）、`concierge_django_views.py`（71行）、`concierge_api_views.py`（4行、`raise RuntimeError`でimport自体を禁止する明示的tripwireのみ） | `backend/temples/api/`・`shrine_project/urls.py`・テスト・Web/Mobileいずれからも参照0件（grep確認済み） | Backend | なし。`concierge_api_views.py`は「DEPRECATED: do not import」というdocstringと共に、import時に例外を発生させる安全装置のみを持つ | Dead | 低（参照が一切ないため削除しても現行動作に影響しない） | `docs/audit/deprecated-files-cleanup.md`が既に「別PRで判断する」と保留していた対象。本監査で参照0件を再確認できたため、判断材料は揃っている | ディレクトリ全体（4ファイル）を削除するPR |
| `apps/web/src/features/concierge/components/legacy/`（`RecommendationUnit.tsx`, `RecommendationSwitchList.tsx`、計197行） | 同ディレクトリ | 参照元`ConciergeSections.tsx`（114行）自体が、JSXとしても`import`としても他のどこからも参照されていない（`<ConciergeSections`/`from ".../ConciergeSections"`のgrep結果0件） | Web | なし。`ConciergeSections.tsx`ごと参照が途切れているDeadクラスタ | Dead | 低 | 同上（`deprecated-files-cleanup.md`の保留対象） | `ConciergeSections.tsx`と`legacy/`ディレクトリ（計311行）をまとめて削除するPR |
| `ShrineSerializer = ShrineDetailSerializer`（互換名） | `backend/temples/api/serializers/shrine.py:110`。コメント「互換名」 | `backend/temples/views.py:30,60,191`、`backend/temples/tests/test_favorite.py:7,21`、`backend/temples/serializers/__init__.py:15,18,36`で`ShrineSerializer`（旧名）として能動的に使用。`_deprecated/api_views_legacy.py`も同名を参照（Dead側からの参照のため考慮不要） | Backend | 新名`ShrineDetailSerializer`へのリネームが行われたが、`views.py`等の既存呼び出し元は旧名のまま残っている | Compatibility（現役） | 中（`views.py`側の呼び出し元コードを変更しないと解消できない） | `views.py`側を新名`ShrineDetailSerializer`へ更新できるか確認する | `views.py`の`ShrineSerializer`参照を`ShrineDetailSerializer`へ置き換え、互換エイリアスを削除するPR |
| `PlacesSearchResponse.items`フィールド | `backend/temples/api/serializers/places.py:18-19`。コメント「互換が必要なら残す（不要なら消す）」 | 実装側（`backend/temples/api/views/search.py`）は`results`キーのみを組み立てており、`items`キーを設定する箇所は0件。Web側（`apps/web/src/lib/api/places.ts`）でも`.items`/`.results`いずれの直接参照も確認できず | Backend | なし。コメントの時点で開発者自身が削除候補として認識していた | Dead | 低 | Web/Mobileの型定義・過去バージョンで`items`キーを消費するコードが本当に無いか、念のため型定義ファイルも確認する | `PlacesSearchResponse`から`items`フィールドを削除するPR |
| `temples/api/serializers/concierge.py`（COMPAT LAYER） | ファイル冒頭のコメントで「COMPAT LAYER」と明記。`temples/serializers/concierge.py`（新モジュール）から可能な限り再エクスポートし、無ければフォールバック実装を使う構造 | 新モジュール`temples/serializers/concierge.py`は`ShrineRecommendationSerializer`/`LocationSerializer`/`PlaceLiteSerializer`/`ConciergePlanRequestSerializer`/`ConciergePlanResponseSerializer`の5つのみを定義しており、`ConciergeHistorySerializer`等の残りのシンボルは新モジュールに存在しないためフォールバック実装が実際に使われている | Backend | 新旧モジュール移行の途中段階。一部シンボルは移行済み、残りは移行未着手 | Compatibility（現役） | 中（新モジュールへの統合が未完了のため、フォールバック実装を削除すると壊れる） | 新モジュールへの統合作業がロードマップ上どこまで進んでいるか確認する | 残りのシンボル（`ConciergeHistorySerializer`等）を新モジュールへ移行し、`try/except`フォールバック構造を解消するPR |

---

## 5. Backend: Render起動時Flag

| 設定名 | 定義場所 | 参照場所 | 対象レイヤ | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|---|
| `RUN_MIGRATIONS_ON_START` / `RUN_STARTUP_CHECK` | `backend/start.sh:17-25` | `docs/infra/render-startup.md`が現行の運用手順として明記 | Backend（Render） | 通常デプロイではmigrationをスキップし、Render無料枠でのポートバインドタイムアウトを回避する。migrationが必要な時のみ手動でFlagを立てる | Active | なし | なし | なし |
| `RUN_SHRINE_REFLECTION_REPAIR` / `RUN_FAVORITE_REPAIR_ON_START` / `RUN_FEATUREUSAGE_REPAIR_ON_START` | `backend/start.sh:29-63` | `docs/infra/render-startup.md:29-38`が「必要な時のみ有効化する」現行運用として明記 | Backend（Render） | 特定テーブルのスキーマ不整合を復旧するための再利用可能な安全弁 | Active（低頻度使用が前提の設計） | なし | なし | なし |
| `RUN_BOOTSTRAP_ON_START`（migration `0083`分岐を含む） | `backend/start.sh:65-73` | 同上 | Backend（Render） | 本番データのbootstrap。migration `0083`が適用済みかどうかで分岐するが、現在の最新migrationは`0092`であり、`0083`は通常のデプロイ環境で既に適用済みのはず | Active（ただし内部分岐の一部が事実上到達しない） | 低 | `showmigrations temples` の出力を`grep "0083"`で確認した分岐が偽になるケースが実運用であるか確認する | 分岐ロジックの簡略化（`0083`判定を削除し、常に`bootstrap_production_data`を呼ぶ）を検討するPR。優先度は低い |

---

## 6. Web (`apps/web`)

サブエージェントによる調査結果を集約した。`apps/web/.env` / `apps/web/.env.local`はGit管理外（`.gitignore`対象）のため、以下の「参照なし」判定はコード側のgrep結果に基づく。値そのものは開発者ごとに異なる可能性がある。

### 6.1 BackendオリジンURLの環境変数命名分裂

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `DJANGO_ORIGIN` / `BACKEND_ORIGIN` | `apps/web/.env:21-22` | `src/lib/server/backend.ts:6`、`src/app/api/auth/login/route.ts:66`が論理OR演算子によるフォールバックで解決 | Backendオリジンの解決 | Compatibility（新旧2キー併存） | 中 | どちらが正式名か、コミット履歴で経緯を確認する | 1つの名前へ統一するPR |
| `DJANGO_API_BASE_URL` / `BACKEND_URL` / `BACKEND_BASE_URL` | 定義箇所なし（`.env`/`.env.local`/`.env.example`いずれにも無し） | `src/lib/api/shrines.server.ts:13-15`、`shrineMeaning.server.ts:13-15`、`api/auth/register/route.ts:5-7`が独自の論理OR演算子によるフォールバック連鎖を持つ | 上記と別系統の、ファイルごとに異なるBackendオリジン解決ロジック | Uncertain（命名がさらに分岐しており実態把握が必要） | 中〜高（5系統の命名が並立しており、どれか1つを削除すると他のフォールバックに依存しているファイルが影響を受ける可能性） | `DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`/`NEXT_PUBLIC_API_BASE`の6命名を1箇所（例: `src/lib/server/backend.ts`）に集約できるか設計を検討する | Backendオリジン解決ロジックを共通ヘルパーへ集約し、環境変数名を1つに統一するPR（影響範囲が広いため慎重な設計が必要） |
| `NEXT_PUBLIC_API_BASE` | `apps/web/.env:2` | `src/lib/api.ts:2`、`src/lib/api/http.ts:60` | クライアント側APIベースURL | Active | なし | なし | なし |

### 6.2 `apps/web/.env`内のDjangoバックエンド設定の混入

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `DJANGO_SECRET_KEY` / `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` / `GOOGLE_MAPS_API_KEY` / `GOOGLE_PLACES_API_KEY`（`apps/web/.env`内、`GOOGLE_MAPS_API_KEY`/`GOOGLE_PLACES_API_KEY`はそれぞれ2回重複定義） | `apps/web/.env` | Next.js側コード（`apps/web/src/`）からの参照0件。いずれもDjango（Backend）側の`.env.example`に本来存在すべき項目 | なし（apps/webの実行には無関係） | Dead（`apps/web`視点。Backend側では同名の変数が別途Active） | 低（Git管理外のファイルの記載を削るだけで、コードには影響しない） | このファイルがBackend用`.env`のコピーから誤って作成された経緯がないか確認する | `apps/web/.env`から該当行を削除する（開発者各自のローカル作業） |
| `APP_ORIGIN` / `API_BASE_SERVER` | `apps/web/.env:1,4` | 参照なし | 不明 | Dead | 低 | なし | 同上 |
| `OSRM_BASE_URL`（`apps/web/.env.local`） | `apps/web/.env.local:4` | 参照なし（Backend側の`ROUTE_PROVIDER=osrm`関連の可能性が高いが、apps/web側では未使用） | なし | Dead（`apps/web`視点） | 低 | なし | 同上 |
| `NEXT_PUBLIC_MAP_PROVIDER` / `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS` | `apps/web/.env.local:5`他 | 参照なし | 不明 | Dead | 低 | なし | 同上 |

### 6.3 デモ用ハック・期限切れTODO

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `NEXT_PUBLIC_CONCIERGE_RENDERER` / `SHOW_NEW_RENDERER` | `apps/web/src/features/concierge/rendererMode.ts` | `ConciergeClientFull.tsx`3箇所が`SHOW_NEW_RENDERER`（ハードコードされた`true`）を参照。環境変数`NEXT_PUBLIC_CONCIERGE_RENDERER`自体はコード内コメントに残るのみで、実際の分岐には使われていない | コメントに「プレゼン用の一時対応」「デモ完了後、環境変数制御へ戻す」と明記されているが、戻されていない | Deprecated | 中（環境変数制御に戻す場合、両方のレンダラーが現在も動作することを確認する必要がある） | デモが完了しているか、旧レンダラー（環境変数がfalse相当の場合の分岐）が今も必要か確認する | 環境変数制御へ戻すか、新レンダラーへの完全移行を確定して旧分岐を削除するか、いずれかを判断するPR |
| ~~互換ルート`src/app/api/shrines/[id]/route.ts`（単体GET）~~（**対応済み・削除**） | `src/app/api/shrines/[id]/route.ts:1`。コメント「TODO: 互換ルート。2026-04-01 までにアクセス0なら削除」 | `apps/web`内のクライアントコードからの参照0件。期限（2026-04-01）を本監査時点（2026-07-18）で3.5ヶ月超過 | 期限切れの削除保留TODO | ~~Deprecated~~ 削除済み | 低〜中（本番アクセスログでの実測は本監査の範囲外） | 本番アクセスログで実際のアクセス数を確認する | 削除済み。Vercel Runtime Logsで実測を試みたがHobbyプランのため保持期間が1時間しかなく、長期的な実測は不可能と判明した。代わりに、同一データを返す正本ルート`apps/web/src/app/api/public/shrines/[id]/route.ts`（`lat`/`lng`正規化・非JSON応答の安全処理を追加で持つ、より新しい実装）へ完全に代替されていること、Web/Mobile双方から本ルートへの参照が0件であることをコードレベルで確認した上で削除した。詳細はリネーム/削除PRの説明を参照 |

### 6.4 未使用コード（Dead）

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `src/lib/auth/token.ts`（localStorageベースのトークン管理一式、`ACCESS_KEY`/`REFRESH_KEY`） | `src/lib/auth/token.ts` | importer 0件。実際の認証はhttpOnly Cookie（`access_token`/`refresh_token`、`middleware.ts`と`login/route.ts`が使用）＋`AuthProvider.tsx`の`auth:logged_in`フラグで完結している | なし | Dead | 低 | なし | ファイル削除PR |
| `IS_DEMO`（`src/lib/config.ts:2`、`NEXT_PUBLIC_DEMO_MODE`由来） | `src/lib/config.ts:2` | 参照0件 | なし | Dead | 低 | なし | 削除PR |
| `cardEvents.ts`の`premium_preview_view` | `apps/web/src/lib/analytics/cardEvents.ts:25` | 参照0件（テスト含む） | なし | Dead | 低 | なし | 型定義から削除するPR（他のAnalytics dead eventと合わせて） |
| `retentionEvents.ts`の`next_session` / `next_thread` | `apps/web/src/lib/analytics/retentionEvents.ts:4-5` | 参照0件 | なし | Dead | 低 | なし | 同上 |
| `RecommendationReasonViewModel.why` / `.interpretation` | `apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts:83-107`。コード中コメントで「legacy compatibility field」「依存箇所がなくなったら削除可」と明記 | 本番コンシューマー（`viewmodels/conciergeToShrineList.ts`、`shrines/[id]/page.tsx`、`ConciergeSectionsRenderer.tsx`）は全て`.detail.*`のみを参照。`.why`/`.interpretation`はテストファイル内でのみ読まれている | なし（自己文書化された削除可能フィールド） | Dead | 低 | なし | コメントの指示通り削除するPR |
| `useMyGoshuin.ts`（コメント「旧importの互換用」） | `apps/web/src/hooks/`配下 | 本番コード参照0件。テストファイルのみ参照 | なし | Dead | 低 | なし | 削除PR（テストの扱いも合わせて確認） |
| `MapCardListClient.tsx`（コメント「互換のために残す：旧 import を壊さない」） | 該当ファイル | 自ファイル以外からのimport0件 | なし | Dead | 低 | なし | 削除PR |
| `@heroicons/react`（package.json dependencies） | `apps/web/package.json` | `grep -rn "heroicons" src`が0件（`lucide-react`へ統一済みと推測） | なし | Dead | 低 | なし | package.jsonから削除するPR |

### 6.5 互換目的で現役のもの

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `placeCaches.ts`のコメント「互換: 旧名を残す」 | 該当ファイル | `src/components/PlaceSuggestBox.tsx`が`fetchPlaceCacheSuggest`を現在も使用中 | 旧関数名を現役で使用 | Compatibility（現役） | 低 | なし | なし |
| `checkout_session_id` ?? `session_id`（URLクエリ互換） | `src/app/billing/success/page.tsx:64` | Stripe標準の`success_url`パラメータは`session_id`のみを返す想定。`checkout_session_id`は旧パラメータ名の名残と推測される | 決済成功ページでのセッションID取得の後方互換 | Compatibility | 低〜中（現行Stripe設定で`checkout_session_id`が実際にどこかから渡ることがあるか未確認） | 現行のStripe Checkout設定（`success_url`のテンプレート）が`session_id`のみを使っているか確認する | 確認後、不要であれば`checkout_session_id`分岐を削除するPR |

### 6.6 未文書化だが機能しているFlag（Uncertain）

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `DEBUG_LOG`（server側、`NEXT_PUBLIC_`prefixなし） | 定義箇所なし（`.env`/`.env.local`/`.env.example`いずれにも無し） | `src/app/api/places/*/route.ts`、`favorites/route.ts`、`users/me/icon/route.ts`、`src/lib/server/logging.ts:7` | サーバー側デバッグログの出し分け。クライアント側の`NEXT_PUBLIC_DEBUG_LOG`と命名が非対称 | Uncertain | 低 | `.env.example`への追記漏れかどうか確認する | `.env.example`（Web用があれば）への追記、または命名を`NEXT_PUBLIC_DEBUG_LOG`と揃えるPR |
| `NEXT_PUBLIC_ENABLE_CONCIERGE_DEBUG_PANEL` | 定義箇所なし | `ConciergeClientFull.tsx:272` | デバッグパネル表示ゲート | Uncertain | 低 | 同上 | 同上 |
| `NEXT_PUBLIC_APP_VERSION` → `APP_VERSION`（`src/lib/version.ts:2`） | 定義箇所なし | `APP_VERSION`自体の参照が`src`全体で0件 | なし | Dead | 低 | なし | `version.ts`のexport自体を削除するPR |

---

## 7. Mobile (`apps/mobile`)

サブエージェントによる調査結果を集約した。

### 7.1 環境変数

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | `apps/mobile/.env:1` | `apps/mobile/lib/http.ts:3`、`apps/mobile/app/premium/index.tsx:44` | APIベースURLの切替。未設定時は`http://localhost:8000/api`にfallback | Active | なし | なし | なし |
| `EXPO_PUBLIC_POSTHOG_KEY` | `.env`に定義なし（EAS Dashboard側で管理、`docs/audit/cross-platform-event-contract.md:30,126`に記載あり） | `apps/mobile/lib/posthogAnalyticsProvider.ts:40` | 本番判定時のみPostHog初期化のゲートに使用 | Active（ローカルでは値未検証） | なし | なし | なし |
| `EXPO_PUBLIC_POSTHOG_HOST` | 定義箇所なし（コード外部管理） | `apps/mobile/lib/posthogAnalyticsProvider.ts:44` | 未設定時は`DEFAULT_POSTHOG_HOST`にfallback | Active/Uncertain | 低 | EAS Dashboard側の実設定値を確認する | なし |
| `babel.config.js`の「旧reanimated/plugin無効化」設定 | `apps/mobile/babel.config.js:6` | 同ファイル内`presets`として適用中 | Expo自動設定によるreanimated pluginの二重注入を防ぐ明示的ワークアラウンド | Compatibility | なし | なし | なし |
| `recommendationReasonV4 → reasonFacts → legacyReason`のフォールバック連鎖 | `apps/mobile/app/concierge/index.tsx:302-326`、`apps/mobile/app/shrines/[id].tsx:166-182` | 両ファイル内の`resolveRecommendationReason`から使用 | 推薦理由表示の新旧フォーマット吸収 | Compatibility（現役） | 中（削除すると旧フォーマットのみ持つデータの表示が壊れる） | 旧フォーマット（v4未満）のデータが実際に残っているか確認する | 旧データの移行完了後にfallback連鎖を簡略化するPR |
| `BillingProvider = "revenuecat"`（型） | `apps/mobile/lib/billing.ts:4,33` | バリデーションのみ、RevenueCat SDKは`package.json`に無し | 型としては許容するが実挙動なし | Uncertain（Backend側の同名enumと同じ「将来拡張の意図的プレースホルダ」の可能性が高い） | 低 | Backend側`docs/audit/release-config-and-billing-audit.md`の記載と合わせて意図を確認済み扱いとする | なし |

### 7.2 未使用コンポーネント・ルート

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| AsyncStorageキー`"recent_shrines"` | `apps/mobile/components/home/RecentViewed.tsx:11` | 同ファイル内のみ（コンポーネント自体が0参照） | 「最近見た神社」の旧実装。現行実装は`lib/storage.ts`の`sanpai:recents`キー | Dead | 低 | なし | `RecentViewed.tsx`ごと削除するPR（下記コンポーネント群と合わせて） |
| `components/PopularSection.tsx`（および依存する`PopularShrineCard.tsx`/`Skeletons.tsx`/`hooks/usePopularShrines.ts`） | 各ファイル冒頭 | 参照元0件。コード内コメントで「map 画面がある前提のまま残しています。未実装ならここは後続PRで対応。」と自己申告し、存在しない`/map`ルートへ`router.push`する実装 | 「地図で見る」導線として構想されたが未接続 | Dead | 低 | なし | 削除PR、または`/map`ルート実装を伴う復活PR（いずれか判断） |
| `components/home/NearbyShrines.tsx` / `RankingCarousel.tsx` / `SearchChips.tsx` / `MyPageCard.tsx`（コンポーネント版） | 各ファイル冒頭 | 参照元0件（`MyPageCard`は`app/mypage/index.tsx`のローカル関数と命名衝突があるが別実体） | Home画面刷新前の旧コンポーネント群と推測される | Dead | 低 | なし | Home画面の`components/home/`配下未使用ファイルを一括削除するPR |
| `components/ui/Layout.tsx`（`Spacer`/`Section`） | `apps/mobile/components/ui/Layout.tsx:5,7` | 参照元0件 | 未使用のレイアウトヘルパー | Dead | 低 | なし | 同上と合わせて削除 |
| `app/birthday` / `app/search` / `app/visit-history` / `app/reflection-history` / `app/consultation-history` / `app/recently-viewed` | `apps/mobile/app/`配下、`app/_layout.tsx`にTab登録済み | 他画面からの`router.push`/`Link`が0件。特に`app/mypage/index.tsx`の「誕生日」カードは`onPress`自体が未設定 | ルートとしては実装済みだが、アプリ内導線が存在せずユーザーが到達できない | Uncertain（Dead候補。Tab登録経由でのみ到達可能かは未検証） | 中（Tab登録経由の到達性は本監査のgrep手法では確認しきれない） | 実機/シミュレータでTab経由の到達性を確認する。到達できないなら導線追加かルート削除のいずれかを判断する | 到達性確認後、導線追加または未使用ルート削除のPR |
| `nativewind` / `tailwindcss` / `@tailwindcss/postcss` / `autoprefixer` / `lib/cn.ts` | `apps/mobile/package.json`、`tailwind.config.js`、`postcss.config.js`、`lib/cn.ts:2` | `className=`使用0件、`babel.config.js`にnativewindプリセット記載なし、metro.config.jsも存在せずビルドパイプラインに未接続 | 設定一式が存在するが実質未接続 | Dead | 低（ビルドに影響しないパッケージのため） | なし | package.json・設定ファイル一式を削除するPR |
| `expo-constants` / `expo-font` / `expo-splash-screen` / `expo-status-bar` | `apps/mobile/package.json` | コード内import 0件 | Expo SDK標準構成の一部として残存している可能性 | Uncertain | 低〜中（Expoの内部依存として間接的に必要な可能性があるため、単純な未import判定だけでは断定できない） | `expo install`が自動追加する標準パッケージかどうかExpo SDKのドキュメントで確認する | 確認後、真に不要なもののみ削除するPR |

---

## 8. CI/CD (`.github/workflows/`)

サブエージェントによる調査結果を集約した。

| 設定名 | 定義場所 | 参照場所 | 現行用途 | 分類 | 削除リスク | 必要な後続確認 | 推奨する後続PR |
|---|---|---|---|---|---|---|---|
| `backend-integration.yml` / `backend-tests.yml` / `codeql.yml` / `dependency-review.yml` / `readme-guard.yml` / `runner-smoke.yml` / `web-tests.yml`（全7ワークフロー） | `.github/workflows/`配下 | いずれも実行トリガー（push/pull_request/cron/workflow_dispatch）が確認でき、ワークフロー名・ジョブ名に old/legacy/deprecated/temp は無し | それぞれ独立した目的（Backend単体・統合テスト、CodeQL、依存関係レビュー、README fence guard、ランナー疎通確認、Web CI）を持つ | Active（全て） | なし | なし | なし |
| `secrets.GOOGLE_MAPS_API_KEY` / `secrets.GOOGLE_PLACES_API_KEY` | `backend-integration.yml`、`backend-tests.yml`（workflow_call経由） | `.env.example`/`backend/.env.example`、`backend/temples/services/google_places.py`等の実装コードで使用 | integrationテストへのAPIキー注入 | Active | なし | なし | なし |
| コメントアウトされたトップレベル`env: CONCIERGE_THROTTLE`ブロック | `.github/workflows/backend-tests.yml:31-32` | 参照なし（コメントのため実行されない）。Git履歴から、ジョブレベルenv（149行目・287行目）へ置き換えられた際の残骸と確認 | 置換済みの残骸 | Deprecated | 低（コメントのため実害なし） | なし | コメント自体を削除するPR（クリーンアップのみ、任意） |
| `if:` 条件式（末尾に論理OR trueが付与されている） | `.github/workflows/web-tests.yml:58`（jobs.full） | 末尾の論理OR trueにより常にtrue評価となり、直上のコメント「重いジョブは絞る（必要なら条件変更）」が意図する条件分岐が実質機能していない | 条件式とコメントが乖離している | Uncertain | 低（実行を妨げていないため実害はない） | 意図した条件分岐（`workflow_dispatch`以外の時だけ実行する等）が本来何だったか、Git履歴で確認する | 条件式をコメントの意図に合わせて修正するか、現在の常時true動作を意図として明記するPR |

---

## 9. 推奨する後続PR一覧（優先度順の目安）

本監査は分類のみを目的としており、以下はあくまで「次に着手できる候補」の整理である。優先順位の最終判断・実施は母艦へ差し戻す。

### 低リスク・削除可能性が高いもの（Dead判定・参照0件を確認済み）

1. `backend/temples/_deprecated/`（4ファイル、1313行）の削除
2. `apps/web/src/features/concierge/components/legacy/`と参照元`ConciergeSections.tsx`（計311行）の削除
3. `backend/temples/services/recommendation.py`の`recommend_shrines()`と関連LUCK_BONUS系設定の削除
4. `ConciergeRecommendationClickLog`モデルの削除（本番DBのデータ有無確認後）
5. `PlacesSearchResponse.items`フィールドの削除
6. `apps/mobile/components/home/`配下未使用コンポーネント群（`PopularSection.tsx`とその依存、`NearbyShrines.tsx`、`RankingCarousel.tsx`、`SearchChips.tsx`、`MyPageCard.tsx`、`RecentViewed.tsx`）と`components/ui/Layout.tsx`の削除
7. `apps/mobile`の`nativewind`/`tailwindcss`関連パッケージ・設定ファイルの削除
8. Score v3の到達不能axisキー4件（28エントリ）の削除、または`CONSULTATION_AXIS_ALIASES`へのエイリアス追加による復活
9. `backend/users/services/billing.py`の`BillingState`/`plan_from_profile()`の削除
10. `apps/web/src/lib/auth/token.ts`（localStorageベースのトークン管理、参照0件）の削除
11. `apps/web`のAnalytics dead event（`premium_preview_view`/`next_session`/`next_thread`）の型定義削除
12. `RecommendationReasonViewModel.why`/`.interpretation`の削除（コード内コメントで削除可能と自己文書化済み）
13. `apps/web`の`useMyGoshuin.ts`（旧import互換用）・`MapCardListClient.tsx`（互換維持コメント付き未参照ファイル）の削除
14. `apps/web/package.json`の`@heroicons/react`（未import）の削除

### 命名・ドキュメント整合（動作は変えない）

1. `SCORE_V3_HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`のリネーム（実際にはshadowではなく本番ランキングへ影響するため）
2. `.github/workflows/backend-tests.yml`のコメントアウト済み残骸の削除
3. `.github/workflows/web-tests.yml`の条件式とコメントの乖離解消

### 移行完了後に着手すべきもの（現時点では削除しない）

1. `ShrineSerializer`互換名の解消（`views.py`側の呼び出し元更新が前提）
2. `USE_LLM_CONCIERGE` / `CONCIERGE_THROTTLE`旧env名fallbackの削除（旧名使用環境が無いことの確認が前提）
3. `BillingStatusLegacyView`（単数形`billing/status/`）の削除（本番アクセスログ確認が前提）
4. `temples/api/serializers/concierge.py`のCOMPAT LAYER解消（新モジュールへの統合完了が前提）
5. `ConciergeThread.recommendations`（v1）読み取りfallbackの削除（旧データ移行完了が前提）
6. `apps/web`のBackendオリジンURL環境変数命名（`DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`の5系統併存）の1本化。影響範囲が広いため設計を先に固める
7. ~~`apps/web`の`src/app/api/shrines/[id]/route.ts`互換ルート削除（削除期限2026-04-01を既に超過。本番アクセスログでアクセス0を確認後）~~ **対応済み**（別PRで削除。詳細は本項目のセルを参照）
8. `apps/web`の`SHOW_NEW_RENDERER`ハードコード解消（デモ用の一時対応が環境変数制御へ戻されていない。`rendererMode.ts`）

### 追加調査が必要なもの

1. ルート`.env.example`と`backend/.env.example`の統合要否の判断
2. `apps/mobile`の未到達ルート6画面（`birthday`/`search`/`visit-history`/`reflection-history`/`consultation-history`/`recently-viewed`）の実機導線確認
3. `NOMINATIM_BASE`/`NOMINATIM_EMAIL`がsettings.pyに未接続である点の設計意図確認
4. `apps/web`の`checkout_session_id`と`session_id`の互換分岐が現行Stripe設定で本当に必要か確認

---

## 10. 品質確認

- [x] Markdownコードブロックの閉じ確認（コードフェンス数は偶数、テーブル内の未エスケープ`|`を修正済み）
- [x] Markdown参照切れ確認（本文中で言及した既存文書・ファイルパスの実在を確認済み）
- [x] `git diff --check`
- [x] `git status --short`（本監査で新規追加したのは本ファイルのみ）
