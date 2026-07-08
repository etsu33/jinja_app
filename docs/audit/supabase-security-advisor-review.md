# Supabase Security Advisor 総合監査（Error / Warning）

## 目的

Supabase Security Advisor に表示されている Error / Warning を精査し、本当に修正すべき項目を分類する。今回は監査のみ。SQL実行・migration作成・backendコード変更・Supabase設定変更は行わない。

## この監査のスコープと前提（重要）

このセッションでは Supabase ダッシュボードへの直接アクセス手段（MCP接続等）がなく、Advisor画面の Error/Warning 全件を今回新たに取得することはできなかった。ユーザーとの合意により、今回は以下の情報のみで整理する。

- 既存doc [`supabase-security-advisor-rls.md`](./supabase-security-advisor-rls.md) に記録済みの `RLS Disabled in Public` の一部情報
- 本リポジトリのDjangoモデル定義から機械的に洗い出せるテーブル一覧（`backend/temples/models.py` ・ `backend/favorites/models.py` ・ `backend/users/models.py` ・ `INSTALLED_APPS`）

`Function Search Path Mutable` / `Security Definer View` / Auth設定 / API公開設定 は、対象オブジェクトの実名がAdvisor画面から未取得のため、**すべて「未確認」として枠のみ整備**した。次アクションで実データを埋める前提の骨子ドキュメントである。

## Error / Warning 一覧（現時点で分かっている範囲）

| # | 項目 | 種別 | ステータス |
|---|------|------|-----------|
| 1 | RLS Disabled in Public | Error | 一部テーブル名を確認済み（全件ではない） |
| 2 | Function Search Path Mutable | Warning | 未確認（対象関数名なし） |
| 3 | Security Definer View | Warning/Error | 未確認（対象view名なし） |
| 4 | Auth設定関連（OTP有効期限 / Leaked Password Protection 等） | Warning | 未確認 |
| 5 | API公開設定（exposed schema / anon key 権限） | 設定監査 | 未確認 |

## 重点確認項目ごとの整理

### 1. RLS Disabled in Public

- **内容**: public schema のテーブルで Row Level Security が無効になっている。
- **原因**: Django が直接DB接続（psycopg経由、テーブル所有者相当のロール）で利用しているテーブル群に対し、Supabase側で個別にRLSを設定していないため。Django自体はPostgresの通常権限モデルで動作しており、RLSの有無を前提にしていない。
- **危険度**: 高（対象テーブルがPostgREST/Supabase API経由で公開されている場合、認可なしでデータ露出・改ざんのリスク）。ただしDjangoの直接DB接続経路には影響しない。
- **Djangoへの影響**: RLSを安易に有効化すると、Django接続ロールの種類（テーブル所有者 or 汎用ロール）次第では既存クエリ・migrationが影響を受ける可能性がある。特にmigration実行ロールとRLS対象ロールが同一だと予期せぬブロックは起きにくいが、未検証。
- **Supabase APIへの影響**: PostgRESTでexposeされているschemaに対象テーブルが含まれる場合、RLSが無いと anon/authenticated ロールからテーブル全件が読み書き可能になり得る（API公開設定の確認が前提）。
- **修正優先度**: テーブル種別により異なる（下記「Django内部テーブル vs 業務テーブル」参照）。

#### 既存docで確認済みのテーブル

- ユーザーデータ系（優先度A想定）: `auth_user`, `favorites_favorite`, `django_session`
- Django内部系（優先度D想定）: `django_migrations`, `django_content_type`, `auth_permission`, `auth_group`

#### 今回モデル定義から新たに洗い出した業務テーブル（Advisor上での確認は未実施）

`backend/temples/models.py` ・ `backend/favorites/models.py` ・ `backend/users/models.py` に定義された全モデルのDBテーブル名（Django既定命名規則。Metaで`db_table`指定があるものは注記）。

- `users_userprofile`
- `favorites_favorite`（favoritesアプリ）
- `temples_favorite`（temples内の別Favoriteモデル。favoritesアプリの`favorites_favorite`とは別実体）
- `place_ref`（`Meta.db_table`指定）
- `place_cache`（`Meta.db_table`指定）
- `temples_goriyakutag`
- `temples_shrine`
- `temples_conciergethread`
- `temples_conciergemessage`
- `temples_visit`
- `temples_shrinereflection`
- `temples_shrineinteractionlog`
- `temples_actionevent`
- `temples_goshuin`
- `temples_goshuinimage`
- `temples_like`
- `temples_rankinglog`
- `temples_conciergehistory`
- `temples_deity`
- `temples_conciergeusage`
- `temples_shrinesubmission`
- `temples_shrinecandidate`
- `temples_crawltile`（運用ジョブ用の内部データ寄り）
- `temples_productiondatabootstraprun`（運用ジョブ用の内部データ寄り）

これらが Advisor 上で実際に `RLS Disabled in Public` として検出されているかは未確認。次アクションでAdvisor実データと突合する。

### 2. Function Search Path Mutable

- **内容**: Postgres関数の `search_path` が固定されておらず、呼び出し時の `search_path` に依存する状態。
- **原因（一般論）**: `CREATE FUNCTION` 時に `SET search_path = ...` を明示していない場合に発生する。本プロジェクトのどの関数が該当するかはAdvisor実データ未取得のため特定できていない。
- **危険度**: 中〜高（`SECURITY DEFINER` 関数と組み合わさると、`search_path` 汚染による権限昇格・意図しないオブジェクト参照のリスクがある）。
- **Djangoへの影響**: Django ORMは通常カスタムPostgres関数を直接呼ばないため、影響は限定的と推測される。ただしトリガー関数（例: `temples/signals.py` の `auto_geocode_on_save` 等はPython側のシグナルでありPostgres関数ではない）を別途DB側に持っている場合は要確認。
- **Supabase APIへの影響**: RPC経由で外部公開されている関数が対象の場合、外部呼び出し時に `search_path` 汚染のリスクがある。
- **修正優先度**: 対象関数の実体確認後に判断（現時点は **C**、確認後に格上げ検討）。

### 3. Security Definer View

- **内容**: `SECURITY DEFINER` 属性を持つview（view所有者の権限でクエリが実行される）。
- **原因**: view作成時に明示、またはSupabase側の自動生成viewでデフォルト付与されている可能性。
- **危険度**: 高（呼び出し元の権限に関わらずview所有者権限で実行されるため、RLSをすり抜けてデータが見える可能性がある）。
- **Djangoへの影響**: Djangoが当該viewを直接参照していなければ影響は小さい（本リポジトリのDjangoモデルでviewを参照している定義は確認できていない＝未確認）。
- **Supabase APIへの影響**: PostgREST経由で当該viewが公開されている場合、RLS設定と無関係にデータが露出する可能性がある。
- **修正優先度**: 対象view確認後に判断（現時点は **B** 想定、本番前に確認推奨）。

### 4. Auth設定

- **内容**: Supabase Auth関連の設定項目（例: Leaked Password Protection無効、OTP有効期限が長い、MFA未設定など）。
- **原因**: プロジェクト作成時のデフォルト設定が変更されていない可能性。
- **危険度**: 中（Supabase Authを実際に利用している場合はアカウント乗っ取りリスクに直結するため高くなる）。
- **Djangoへの影響**: 本プロジェクトの認証は `rest_framework_simplejwt` を用いたDjango側JWT認証が主体とみられる。Supabase Authを別途利用しているかは未確認。
- **Supabase APIへの影響**: Supabase Authを利用している場合、設定次第でセッション乗っ取り・パスワード漏洩耐性に直結する。
- **修正優先度**: Supabase Authの利用有無を確認後に判断（現時点は **C**）。

### 5. API公開設定

- **内容**: PostgREST経由でexposeされるschema/テーブルの設定、anon keyの権限範囲。
- **原因**: デフォルトで `public` schema がexposeされている可能性がある。
- **危険度**: 高（この設定次第で、他の全項目＝RLS Disabled等の実害度合いが決まる）。
- **Djangoへの影響**: Djangoは直接DB接続のため無関係。Supabase API側の設定はDjangoの動作と独立して有効なままになりうる。
- **Supabase APIへの影響**: 最重要項目。exposeされているschema/テーブル範囲が広いほど、他のWarning/Errorの実害が大きくなる。
- **修正優先度**: **A**（最優先で確認すべき設定。RLSより先に「そもそも何が外部から見えるか」を把握する必要がある）。

## Django内部テーブル vs 業務テーブル 分類

### Django内部テーブル（Supabase API露出回避を優先し、RLS即時適用は保留＝D想定）

- `django_migrations`
- `django_content_type`
- `django_admin_log`
- `django_session`（※ユーザーのセッションデータを含むため実害の観点ではA寄り。テーブル種別としては内部テーブルだが優先度は業務データ側に寄せて評価する）
- `auth_permission`
- `auth_group`
- `auth_group_permissions`
- `auth_user_groups`
- `auth_user_user_permissions`
- `token_blacklist_outstandingtoken`（`rest_framework_simplejwt.token_blacklist`）
- `token_blacklist_blacklistedtoken`（同上）

### 業務テーブル（ユーザー影響あり、優先度A/B想定）

- `auth_user`（Django標準テーブルだが実体はユーザーデータそのもの）
- `users_userprofile`
- `favorites_favorite` / `temples_favorite`
- `place_ref` / `place_cache`
- `temples_shrine` / `temples_goriyakutag` / `temples_deity`
- `temples_conciergethread` / `temples_conciergemessage` / `temples_conciergehistory` / `temples_conciergeusage`
- `temples_visit` / `temples_shrinereflection` / `temples_shrineinteractionlog` / `temples_actionevent`
- `temples_goshuin` / `temples_goshuinimage` / `temples_like` / `temples_rankinglog`
- `temples_shrinesubmission` / `temples_shrinecandidate`

### 運用・バッチ系（業務データではあるがユーザー個人情報を含まない、優先度は他より低め）

- `temples_crawltile`
- `temples_productiondatabootstraprun`

## 対応レベル分類（A/B/C/D）

**A：今すぐ確認**
- API公開設定（exposed schema / anon key 権限）— 他項目の実害を左右するため最優先
- RLS Disabled: `auth_user`, `users_userprofile`, `favorites_favorite`, `temples_favorite`, `django_session`

**B：本番前に修正**
- RLS Disabled: 上記A以外の業務テーブル全般（`temples_shrine`, `concierge_*`, `visit`, `shrine_reflection`, `shrine_interaction_log`, `action_event`, `goshuin*`, `like`, `ranking_log`, `shrine_submission`, `shrine_candidate` 等）
- Security Definer View（対象view確認後に本判定を維持するか見直す）

**C：保留（追加確認待ち）**
- Function Search Path Mutable（対象関数の実名確認後に格上げ判断）
- Auth設定（Supabase Authの利用有無の確認待ち）

**D：Supabase特有の警告で対応不要（または影響小と推測）**
- RLS Disabled: `django_migrations`, `django_content_type`, `django_admin_log`, `auth_permission`, `auth_group`, `auth_group_permissions`, `auth_user_groups`, `auth_user_user_permissions`, `token_blacklist_*`
  - 理由: Django内部テーブルで業務ロジック上の個人情報を直接保持しない。Supabase API側でexposeさえ止めれば実害は小さいと推測されるため、RLS即時適用よりAPI露出回避を優先する。
- `temples_crawltile` / `temples_productiondatabootstraprun`（運用バッチ内部データ、個人情報を含まない）

## 未確認事項（次アクション）

1. Security Advisor画面の Error/Warning 全件をエクスポート（スクリーンショット or テキスト）し、本ドキュメントの「一覧」を実データで置き換える。
2. `Function Search Path Mutable` / `Security Definer View` の対象オブジェクト実名を確認する（本タスクではSQL実行禁止のため、次PRでダッシュボードの詳細画面またはCLIで確認）。
3. Supabase Authを実際に利用しているか（DjangoのJWT認証と併用しているか、していないか）を確認する。
4. Database Settings > API の exposed schemas 設定、および anon/authenticated ロールの権限範囲を確認する。
5. 上記1〜4の結果を踏まえ、C評価の項目をA/B/Dへ再分類する。

## Decision

今回はdocsの更新のみ。SQL実行・migration作成・backendコード変更・Supabase設定変更は行わない。

次のアクションとして、Advisor全件データの取得と、Function/View実名の特定を優先する。それまでは本ドキュメントの分類は「既知の一部情報からの推測を含む暫定分類」として扱うこと。
