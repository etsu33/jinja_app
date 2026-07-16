# Supabase Security Advisor 総合監査（Error / Warning）

## 目的

Supabase Security Advisor に表示されている Error / Warning を精査し、本当に修正すべき項目を分類する。今回は監査のみ。SQL実行・migration作成・backendコード変更・Supabase設定変更は行わない。

## この監査のスコープと前提（重要）

このセッションでは Supabase ダッシュボードへの直接アクセス手段（MCP接続等）がなく、Advisor画面の Error/Warning 全件を当初は取得できていなかった。その後、ユーザーから Advisor Center 画面（Security / Severity: Critical フィルタ）のスクリーンショットが共有され、`RLS Disabled in Public` の対象テーブルの一部を実データで確認できた（2026-07-08）。

- 確認済み: `RLS Disabled in Public` の対象テーブル（画面の可視範囲分。スクロール未実施のため全件ではない可能性がある）
- 未確認: `Function Search Path Mutable` / `Security Definer View` / Auth設定 / API公開設定 は、対象オブジェクトの実名が未取得のため、**引き続き「未確認」として枠のみ整備**している。

## Error / Warning 一覧（現時点で分かっている範囲）

| # | 項目 | 種別 | ステータス |
|---|------|------|-----------|
| 1 | RLS Disabled in Public | Error（Supabase上はCRITICAL表示） | スクリーンショットで15件確認済み。画面はスクロール可能で、さらに続きがある可能性が高い（全件ではない） |
| 2 | Function Search Path Mutable | Warning | 未確認（対象関数名なし） |
| 3 | Security Definer View | Warning/Error | 未確認（対象view名なし） |
| 4 | Auth設定関連（OTP有効期限 / Leaked Password Protection 等） | Warning | 未確認 |
| 5 | API公開設定（exposed schema / anon key 権限） | 設定監査 | 未確認 |

## 重点確認項目ごとの整理

### 1. RLS Disabled in Public

- **内容**: public schema のテーブルで Row Level Security が無効になっている。
- **原因**: Django が直接DB接続（psycopg経由、テーブル所有者相当のロール）で利用しているテーブル群に対し、Supabase側で個別にRLSを設定していないため。Django自体はPostgresの通常権限モデルで動作しており、RLSの有無を前提にしていない。
- **危険度**: Supabase自身が全件 **CRITICAL** として表示している（スクリーンショットで確認済み）。対象テーブルがPostgREST/Supabase API経由で公開されている場合、認可なしでデータ露出・改ざんのリスク。ただしDjangoの直接DB接続経路には影響しない。
- **Djangoへの影響**: RLSを安易に有効化すると、Django接続ロールの種類（テーブル所有者 or 汎用ロール）次第では既存クエリ・migrationが影響を受ける可能性がある。特にmigration実行ロールとRLS対象ロールが同一だと予期せぬブロックは起きにくいが、未検証。
- **Supabase APIへの影響**: PostgRESTでexposeされているschemaに対象テーブルが含まれる場合、RLSが無いと anon/authenticated ロールからテーブル全件が読み書き可能になり得る（API公開設定の確認が前提）。
- **修正優先度**: テーブル種別により異なる（下記「Django内部テーブル vs 業務テーブル」参照）。

#### 確認済みテーブル（2026-07-08 Advisor Center スクリーンショットより、severity: CRITICAL）

Advisor画面（Security / Severity: Critical フィルタ）で実際に `RLS Disabled in Public` として表示されていたテーブル。画面はスクロール可能で、可視範囲は先頭15件のみ。全件かどうかは未確定。

1. `public.django_migrations`
2. `public.django_content_type`
3. `public.auth_permission`
4. `public.auth_group`
5. `public.auth_group_permissions`
6. `public.auth_user_groups`
7. `public.auth_user_user_permissions`
8. `public.django_admin_log`
9. `public.auth_user`
10. `public.favorites_favorite`
11. `public.django_session`
12. `public.place_ref`
13. `public.temples_shrine_deities`（※要注記、下記参照）
14. `public.temples_deity`
15. `public.temples_visit`

1〜11は既存doc（[`supabase-security-advisor-rls.md`](./supabase-security-advisor-rls.md)）に一部記載済みだった内容と一致し、今回のスクリーンショットで裏付けが取れた。12〜15は本ドキュメントでモデル定義から予測していた業務テーブル一覧と一致する（後述の予測一覧のうち `place_ref` / `temples_deity` / `temples_visit` を実データで確認できた）。

> **注記: `public.temples_shrine_deities` について**
> `backend/temples/migrations/0040_shrine_deities.py` で `Shrine.deities`（M2Mフィールド）が追加されたが、`backend/temples/migrations/0072_remove_shrine_deities_alter_shrine_address.py` で当該フィールドは削除済みで、現在の `temples/models.py` にも `deities` フィールドは存在しない。にもかかわらず Advisor 上に `temples_shrine_deities` テーブルが表示されているのは、**本番DBでmigration 0072が未適用、もしくはテーブルが物理的に残存している**可能性を示唆する。これはRLS云々以前に、モデル定義とDBスキーマの乖離（migration drift）の疑いがあるため、RLS対応より先に `python manage.py showmigrations temples` 相当の確認を本番環境に対して行うことを推奨する（今回はSQL実行禁止のため未実施）。

#### モデル定義から洗い出した業務テーブル一覧（Advisor実データとの突合は一部のみ）

`backend/temples/models.py` ・ `backend/favorites/models.py` ・ `backend/users/models.py` に定義された全モデルのDBテーブル名（Django既定命名規則。Metaで`db_table`指定があるものは注記）。上記「確認済み」に含まれるものは注記した。

- `users_userprofile`
- `favorites_favorite`（favoritesアプリ／**確認済み**）
- `temples_favorite`（temples内の別Favoriteモデル。favoritesアプリの`favorites_favorite`とは別実体）
- `place_ref`（`Meta.db_table`指定／**確認済み**）
- `place_cache`（`Meta.db_table`指定）
- `temples_goriyakutag`
- `temples_shrine`
- `temples_conciergethread`
- `temples_conciergemessage`
- `temples_visit`（**確認済み**）
- `temples_shrinereflection`
- `temples_shrineinteractionlog`
- `temples_actionevent`
- `temples_goshuin`
- `temples_goshuinimage`
- `temples_like`
- `temples_rankinglog`
- `temples_conciergehistory`
- `temples_deity`（**確認済み**）
- `temples_conciergeusage`
- `temples_shrinesubmission`
- `temples_shrinecandidate`
- `temples_crawltile`（運用ジョブ用の内部データ寄り）
- `temples_productiondatabootstraprun`（運用ジョブ用の内部データ寄り）

上記のうち「確認済み」以外が Advisor 上で実際に `RLS Disabled in Public` として検出されているかは未確認（スクリーンショットの可視範囲外の可能性が高い）。次アクションで画面をスクロールした続きのデータと突合する。

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

- `auth_user`（Django標準テーブルだが実体はユーザーデータそのもの、**確認済み**）
- `users_userprofile`
- `favorites_favorite`（**確認済み**） / `temples_favorite`
- `place_ref`（**確認済み**） / `place_cache`
- `temples_shrine` / `temples_goriyakutag` / `temples_deity`（**確認済み**）
- `temples_conciergethread` / `temples_conciergemessage` / `temples_conciergehistory` / `temples_conciergeusage`
- `temples_visit`（**確認済み**） / `temples_shrinereflection` / `temples_shrineinteractionlog` / `temples_actionevent`
- `temples_goshuin` / `temples_goshuinimage` / `temples_like` / `temples_rankinglog`
- `temples_shrinesubmission` / `temples_shrinecandidate`

### 運用・バッチ系（業務データではあるがユーザー個人情報を含まない、優先度は他より低め）

- `temples_crawltile`
- `temples_productiondatabootstraprun`

### 要調査（分類保留）

- `temples_shrine_deities`（**確認済み／Advisor上に実在**）: 現行モデル定義には対応するフィールドが存在しない（migration 0072で削除済み）。Django内部/業務テーブルのどちらにも機械的に分類できないため、まず「なぜ本番DBに存在するか」の確認が先決。RLS対応の優先度を議論する前段階として扱う。

## 対応レベル分類（A/B/C/D）

**A：今すぐ確認**
- API公開設定（exposed schema / anon key 権限）— 他項目の実害を左右するため最優先
- `temples_shrine_deities` が本番DBに存在する理由の確認（migration drift の疑い。RLSより先に確認すべき）
- RLS Disabled（**確認済み**）: `auth_user`, `favorites_favorite`, `django_session`, `place_ref`, `temples_deity`, `temples_visit`
- RLS Disabled（未確認だが同種のためA相当で扱う）: `users_userprofile`, `temples_favorite`

**B：本番前に修正**
- RLS Disabled: 上記A以外の業務テーブル全般（`temples_shrine`, `concierge_*`, `shrine_reflection`, `shrine_interaction_log`, `action_event`, `goshuin*`, `like`, `ranking_log`, `shrine_submission`, `shrine_candidate` 等。いずれも未確認、Advisor続きデータで裏付けが必要）
- Security Definer View（対象view確認後に本判定を維持するか見直す）

**C：保留（追加確認待ち）**
- Function Search Path Mutable（対象関数の実名確認後に格上げ判断）
- Auth設定（Supabase Authの利用有無の確認待ち）

**D：Supabase特有の警告で対応不要（または影響小と推測）**
- RLS Disabled（**確認済み**）: `django_migrations`, `django_content_type`, `auth_permission`, `auth_group`, `auth_group_permissions`, `auth_user_groups`, `auth_user_user_permissions`, `django_admin_log`
  - 理由: Django内部テーブルで業務ロジック上の個人情報を直接保持しない。Supabase API側でexposeさえ止めれば実害は小さいと推測されるため、RLS即時適用よりAPI露出回避を優先する。
- RLS Disabled（未確認だが同種のためD相当で扱う）: `token_blacklist_outstandingtoken`, `token_blacklist_blacklistedtoken`
- `temples_crawltile` / `temples_productiondatabootstraprun`（運用バッチ内部データ、個人情報を含まない）

## 未確認事項（次アクション）

1. ~~Security Advisor画面の Error/Warning 全件を取得する~~ → `RLS Disabled in Public` の先頭15件はスクリーンショットで確認済み（2026-07-08）。**ただし画面はスクロール可能で、続きが未取得**。Security Advisorを `All` タブ・全severityで見た場合に `Function Search Path Mutable` / `Security Definer View` / Auth設定 / API公開設定 に相当する項目が表示されるか、続きのスクリーンショットで確認する。
2. `Function Search Path Mutable` / `Security Definer View` の対象オブジェクト実名を確認する（本タスクではSQL実行禁止のため、次PRでダッシュボードの詳細画面またはCLIで確認）。
3. Supabase Authを実際に利用しているか（DjangoのJWT認証と併用しているか、していないか）を確認する。
4. Database Settings > API の exposed schemas 設定、および anon/authenticated ロールの権限範囲を確認する。
5. **新規**: `temples_shrine_deities` テーブルが本番DBに存在する理由を確認する（`Shrine.deities` フィールドはmigration 0072で削除済みのため、モデル定義とDBスキーマの乖離＝migration drift の疑いがある）。`python manage.py showmigrations temples` を本番環境に対して実行し、0072が適用済みかどうかを確認するのが次アクション。
6. 上記の結果を踏まえ、C評価の項目をA/B/Dへ再分類する。

## Decision

今回はdocsの更新のみ。SQL実行・migration作成・backendコード変更・Supabase設定変更は行わない。

`RLS Disabled in Public` の一部はスクリーンショットで実データとして確認できたが、全件ではなく、他4項目（Function Search Path Mutable / Security Definer View / Auth設定 / API公開設定）も未確認のまま。次のアクションとして、Advisor残りデータの取得と、`temples_shrine_deities` のmigration drift疑いの確認を優先する。それまでは本ドキュメントの分類は「一部確認済み・一部推測を含む暫定分類」として扱うこと。
