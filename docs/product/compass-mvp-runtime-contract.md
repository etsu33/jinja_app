> **Status: Active**
>
> 本ドキュメントは、Visit Compass MVPを実行するために必要な最小Runtime入出力契約を管理する正本文書である。
>
> 本書は`docs/product/compass-product-contract.md`（PR #2475、Section 2.2はPR #2508時点）を上位の正本とし、その定めるMaster Principle・Product Promise・Authority境界・Signal-to-Explanation Ruleに従属する。前回監査群（`docs/audit/premium-visit-compass-recommendation-feasibility.md`・`docs/audit/premium-visit-compass-time-model-contract.md`）はここでは補助的な証拠として引用するのみとし、内容が`compass-product-contract.md`と矛盾する場合は`compass-product-contract.md`を優先する。Section 5・Section 8のMonthly Fallback関連改訂は`docs/product/compass-product-direction-decision.md`（PR #2508、Mother Ship Product Decision Record）のFinal Direction Logic（Option C）をCONTRACT TARGETとして整合させたものであり、実装は含まない。
>
> 本書はDocsのみのPRとして作成された。コード・Model・Migration・Serializer・API Endpoint・候補フィルタ・Recommendation統合・UI・Premium Gate・Analyticsの実装は一切含まない。記載内容はRuntime契約の設計であり、実装済みであることを意味しない。

# Visit Compass — MVP Runtime Contract

## 目的

本ドキュメントは、Compass MVPを実行するために必要な最小限のRuntime入出力を、候補フィルタ・Recommendation統合・UIを実装せずに定義する。

1. `target_date`の責務と、月次Product Modelとの整合を定義する
2. Profile Runtime（生年月日）の要否と、既存kyusei Runtime入力を定義する
3. Origin Runtimeの正本表現と、既存`UserOrigin`構造の再利用を定義する
4. Purpose Runtimeの最小表現と、既存taxonomyの再利用を定義する
5. Direction Runtime出力（Compass Runtime Authorityが返す最小情報）を定義する
6. Recommendation Handoffのために将来必要となる最小Runtimeコンテキストを分離定義する（統合自体は実装しない）
7. 永続化要否を判定する
8. Fail-safe契約を定義する

## 対象範囲

### 対象

- Compass Runtime Authorityの入出力Schema設計
- `target_date`・origin・birthdate・purposeの責務分離
- Direction Runtime出力の最小形
- 永続化要否
- Fail-safe挙動

### 対象外

- 候補フィルタの実装（Phase 3）
- Recommendation統合の実装（Phase 4）
- UI実装（Phase 5）
- Premium Gate（Phase 7）
- Analytics（Phase 8）
- Concierge既存リクエストSchemaの変更（変更しない）
- DB Migration（本書は不要と判定する。根拠はSection 7）

---

## 0. 前提確認

- **MONTH is confirmed as the Product time model**（`docs/product/compass-product-contract.md` Section 4）。
- **日盤（day-plate）はMVP対象外**であることを継承する（同Section 4、`docs/ops/direction-fail-safe.md`の禁止事項）。

本書のすべての設計は、この2点を不変条件として扱う。

---

## 1. Time Runtime

### `target_date`の責務

`target_date`は、Compass Runtime Authorityへの唯一の時間入力とする。ISO 8601形式の日付文字列（`YYYY-MM-DD`）を受け取る。

### なぜ`target_date`のままでよいか（Product ModelがMONTHであるにもかかわらず）

`docs/product/compass-product-contract.md` Section 4が既に確定している通り、Product Modelが月次粒度であることと、Runtime契約が日付型フィールドを受け取ることは矛盾しない。責務は次のように分離する。

```text
Runtime Contract（本書）: target_date（日付を受け取る）
    ↓
Backend内部処理: 節気月バケットへ丸める（Section 1-2参照）
    ↓
Product表示: 「今月」という月次粒度の言葉で見せる
```

既存`visit_date`（`backend/temples/api_views_concierge.py`の`data.get("visit_date") or data.get("planned_visit_date")`）が同型のパターンを本番採用済みであり、Compassはこの前例をそのまま踏襲する。将来day-plateを実装する場合も、`target_date`という契約名を変更せずに精度のみを引き上げられる。

### `target_date`が既存の節気月バケットへ解決される方法

`backend/temples/domain/kyusei.py:229-236` `_solar_month_index()`が既に実装済みの節気月境界（固定近似日: 2/4, 3/6, 4/5, 5/6, 6/6, 7/7, 8/8, 9/8, 10/8, 11/7, 12/7）を、Compassはそのまま再利用する。新しい月バケットロジックを実装しない。

`target_date`は`backend/temples/domain/kyusei.py:239` `planned_visit_lucky_directions(birthdate, visit_date)`へそのまま渡す（引数名は既存関数のシグネチャに従い`visit_date`のままでよい。Compass Runtime Contractの外部フィールド名`target_date`と、既存関数の内部引数名`visit_date`は別レイヤーの命名であり、統一する必要はない）。

### `target_month`は必要か

**不要と判定する**。`compass-product-contract.md`が既にKEEP `target_date`を確定しており（Section 4）、`target_month`という別名のフィールドを新設する製品的・技術的必然性は、前回Feasibility監査・Time Model監査のいずれにおいても確認されなかった。API/Schemaの不要な改名を避ける。

### Month-boundary挙動

`_solar_month_index()`の境界は固定近似日であり、暦月の1日とは一致しない。例えば2月3日と2月4日では異なる節気月バケットに属する場合がある。これは既存の`planned_visit_lucky_directions()`の挙動そのものであり、Compassのために新しい特別処理を追加しない。境界を跨いだ結果の違いは「実装の仕様」として扱い、平滑化・補間しない。

### 不正/未対応な日付の挙動

2つのケースを明確に区別する。

| ケース | 挙動 |
|---|---|
| `target_date`が未指定 | MVPスコープ（today）のデフォルトとして、システムの現在日付（`timezone.localdate()`相当、既存`kyusei.py:151`の`year_star()`のデフォルト挙動と同型）を用いる |
| `target_date`が指定されているが不正/パース不能 | 「未指定」として扱わず、方向コンテキストを省略する（Section 8のFail-safe Contract参照）。クライアントの不正値を黙って「today」へ差し替えない |

いずれの場合も、日次精度を新たに導入しない（`target_date`の「日」の値は、既存`_solar_month_index()`の境界判定にのみ使われ、それ以外の計算には影響しない）。

---

## 2. Profile Runtime

### 生年月日はCompass MVPに必須か

**Birthdate Requirement: REQUIRED**（Compassの主要出力である「方向コンテキスト」を生成するために）。

根拠: `backend/temples/domain/kyusei.py:130` `honmei_star(birthdate)`がNoneを返す場合、`annual_lucky_directions()`・`planned_visit_lucky_directions()`の両方が即座にNoneを返す（`:194,243`）。方位を持たない一般的（非個人化）な代替方位計算は本コードベースに存在しない。したがって生年月日なしにCompassのDirection Runtime出力（Section 5）を生成することはできない。

### 使用されるProfile-derived値

- `honmei.num`（本命星番号、1-9）— **内部のみ**、Presentation Authorityへは公開しない（`compass-product-contract.md` Section 6のMust not explain境界に該当）
- `honmei.name`（例:「七赤金星」）— Secondary（Signal-to-Explanation Ruleの分類、`compass-product-contract.md` Section 8）
- `luckyDirection`/`luckyDirections`（吉方位ラベルの配列）— Compass Runtime Authorityの主要出力（Section 5）

### 既存kyusei Runtime入力

`birthdate`（`backend/users/models.py:15` `UserProfile.birthday`から取得可能、または匿名ユーザーの場合はRuntimeリクエストで直接指定）+ `target_date`（Section 1）。この2値のみがCompass Runtime Authorityの入力である。

### 生年月日欠落時のFail-safe挙動

Section 8で定義する。

### Shrine dataへの永続化禁止

Compass由来の個人化された派生値（本命星、吉方位等）を`Shrine`モデルまたはその関連テーブルへ書き込んではならない。これは`compass-product-contract.md` Section 9の「Runtime signalがShrine Knowledgeを新設・上書きしてはならない」という絶対的制約の直接の帰結である。

---

## 3. Origin Runtime

### 正本の出発地点表現

`packages/shared/userOrigin.ts`が既に定義する`UserOrigin`型をCompassの正本表現として再利用する。新しい型を定義しない。

```typescript
type UserOriginSource = "device" | "station" | "address" | "prefecture";
type UserOrigin = {
  latitude: number;
  longitude: number;
  source: UserOriginSource;
  displayName?: string;
  accuracy: "precise" | "approximate";
};
type OriginMode = "none" | "device" | "manual" | "prefecture" | "disabled";
```

Backendへの送信時は、既存`toOriginPayload()`が行う変換（`{lat, lng}`への正規化、有限値・範囲チェック）をそのまま再利用し、Compass専用の座標フォーマットを新設しない。

### originはCompassに必須か

**Origin Requirement: REQUIRED**（Compassの中核出力である「参拝候補」を生成するために）。

根拠: `backend/temples/services/direction_reference.py:35` `_bearing()`は出発地点座標と神社座標の両方を必須とする純粋関数であり、いずれかが欠ける場合`build_direction_reference()`は`None`を返す（`:75-76`）。kyusei計算（Section 2）自体はoriginを必要としないが、Compassの目的（Section 3のPrimary Experience: 「geographic candidate set」「shrine」の生成）はorigin座標なしには達成できない。したがって、Compass全体のRuntime Contractとしてはoriginを必須とする。

### 既存UserOrigin/location構造の再利用

- Device位置情報: `OriginMode = "device"`
- 駅名・住所検索: `OriginMode = "manual"`（既存`/api/geocodes/search/`を再利用、検索語・未選択候補は送信しない、`docs/core/direction-response-contract.md`の既存原則を継承）
- 都道府県代表地点: `OriginMode = "prefecture"`、`packages/shared/userOrigin.ts`の`PREFECTURE_ORIGINS`/`prefectureOrigin()`をそのまま再利用
- 方位情報を使用しない: `OriginMode = "disabled"`

いずれも既存Concierge/direction機能が既に持つ表現であり、Compass専用の新しいOrigin取得UIパターンを設計する必要はない（ただしUI実装自体はPhase 5の対象外）。

### Device位置情報拒否時の挙動

`OriginMode`が`"device"`から取得失敗した場合、既存パターン（`direction_analytics`の`result: "denied"|"failed"`分類、前回Time Model監査で参照した`docs/analytics/direction-events.md`）に倣い、`"manual"`または`"prefecture"`への切り替えを促す。Compassはこの切り替えのUIを本書では設計しない（Phase 5）。

### 手動選択originの挙動

既存の駅名・住所検索フローをそのまま再利用する。確定済み座標のみを`UserOrigin`へ変換し、検索途中の入力・未選択候補は送信しない。

### origin欠落時のFail-safe挙動

Section 8で定義する。

### 本フェーズでのUI非実装の確認

本書はOrigin Runtimeのデータ契約のみを定義し、UIコンポーネント・画面遷移は実装しない（Phase 5の対象）。

---

## 4. Purpose Runtime

### 最小表現

`purpose`は単一の`need_tag`スラッグ値とする（MVPは複数選択に対応しない。前回Time Model監査のMVP仮説「one purpose」と整合）。

```typescript
type CompassPurpose = NeedTagSlug; // 既存 need_tags.py の15固定タグのいずれか
```

### 既存taxonomyの再利用可否

**既存`need_tag`/`goriyaku`taxonomyをそのまま再利用可能と判定する**（`docs/audit/premium-visit-compass-recommendation-feasibility.md` Section 9で確認済み、15固定タグ: `love, relationship, marriage, communication, career, money, study, health, mental, protection, courage, focus, rest, family, travel_safe`、`backend/temples/domain/need_tags.py:11-27`）。

### purpose → 既存taxonomyのマッピング責務

**新しいマッピング層を追加しない**。`purpose`フィールドの値そのものが既存`need_tag`スラッグの1つである、という直接一致方式を採用する。Compass専用の語彙（例:「work」「money」等の別名）を新設し、それを`need_tag`へ変換する翻訳テーブルを設けることは、それ自体が小さな新規taxonomyの導入に相当するため避ける。

### 新規taxonomy不要の確認

現行リポジトリの証拠（既存15固定`need_tags`、既存`NEED_TO_GORIYAKU_IDS`マッピング、`backend/temples/domain/need_to_goriyaku_tag_ids.py:8-24`）は、新規taxonomyが必要であることを示していない。既存タグのみでCompassのpurpose選択肢を構成できる。

### purposeはkyusei/方位計算を変えないというルールの維持

`compass-product-contract.md` Section 10が既に確定している通り、`purpose`はCompass Runtime Authority（`kyusei.py`・`direction_reference.py`）の計算に一切入力してはならない。Compass Runtime Contractは、`purpose`をDirection Runtime出力（Section 5）とは完全に独立したフィールドとして扱う。

---

## 5. Direction Runtime

### 最小Runtime出力

Compass Runtime Authorityは、以下の最小Schemaを返す。

```typescript
type CompassDirectionRuntime = {
  targetDate: string;           // 解決に使用した target_date（ISO 8601）
  targetYear: number;           // 節気年（kyusei.pyのki_year）
  solarMonthIndex: number;      // 節気月インデックス（1-12、_solar_month_index()由来）
  referenceDirections: string[]; // 8方位ラベルの配列（例: ["北西", "西"]）
  calculationMethod: "annual_monthly_kyusei_v1" | "monthly_kyusei_v1"; // CONTRACT TARGET: 第二値はSection 5-1参照、未実装
  note: string;                 // 既存 DIRECTION_REFERENCE_NOTE と同型の安全な注記文言
};
```

**`calculationMethod`の型改訂（CONTRACT TARGET、未実装）**: `"monthly_kyusei_v1"`は
`monthly_lucky_directions()`（#2506でkyusei.pyへ追加済み、Section 5-1参照）が
既に返す固定値である。本書はこれを`CompassDirectionRuntime.calculationMethod`の
正当な値として受理する契約に改訂する。Schemaのフィールド自体（型・個数）は
変更しない——`calculationMethod`という既存フィールドが取りうる値の集合を
拡張するのみである。

### 年盤情報

`backend/temples/domain/kyusei.py:191` `annual_lucky_directions()`が返す`luckyDirections`/`targetYear`/`calculationMethod`。Compassは`target_date`が有効な限り、これを単独では使わない（下記「月盤情報」を参照）。

### 月盤情報

Compassの主要経路は、`backend/temples/domain/kyusei.py:239` `planned_visit_lucky_directions(birthdate, target_date)`（年盤×月盤の交差済み結果）とする。既存`direction_reference.py:59` `build_direction_reference()`が`calculationMethod == "annual_monthly_kyusei_v1"`のみを受理する（年盤単独の`"annual_kyusei_v1"`を拒否する）という既存の「grounded inputsのみ」契約と整合させるため、**Compassも年盤単独結果を出力として採用しない**。`target_date`が無効な場合はSection 8のFail-safe Contractに従い、方向コンテキスト自体を省略する（年盤のみへ縮退させない）。

### 方位セクター表現

既存8方位ラベル（`direction_reference.py:10` `_DIRECTION_LABELS = ("北", "北東", "東", "南東", "南", "南西", "西", "北西")`）をそのまま採用する。新しい方位分割方式（例: 16方位、角度レンジ）は導入しない。`referenceDirections`はこの8ラベルの部分集合として表現する。

### Compass Runtime AuthorityがPresentation Authorityへ公開してよいもの

`CompassDirectionRuntime`型のフィールドすべて（`targetDate`/`targetYear`/`solarMonthIndex`/`referenceDirections`/`calculationMethod`/`note`）。

### 内部に留めるべきもの

- `honmei.num`（本命星番号）
- `STAR_ELEMENTS`/`GENERATES`（五行相生ロジックの内部変数）
- `excludedDirections`（凶方位の除外理由、内部計算過程であり、ユーザー向け説明として使う信号ではない——`compass-product-contract.md` Section 8「内部スコアの仕組みをそのまま露出する必要はない」に該当）
- `_ki_year`の節分境界計算過程

### 候補フィルタは実装しない

`CompassDirectionRuntime`は、まだどの神社にも紐づかない「方向そのもの」の情報である。「この方向に実際にどの神社があるか」という候補フィルタ（bearing計算を個々の候補神社へ適用する処理）はPhase 3の範囲であり、本書では実装しない。

### Rankingは変更しない

本フェーズはRuntime契約の設計のみであり、`concierge_chat_ranking.py`のいかなる関数・Weightにも変更を加えない。

### 年盤∩月盤の交差が空集合になる場合（Section 8-1・8-2参照）

`referenceDirections`が導出元とする年盤∩月盤の交差は、有効な入力からでも
正当に空集合になり得る（`compass-product-contract.md` Section 2.1、
[#2496](../audit/compass-direction-filter-unavailable-root-cause.md)・
[#2497](../audit/compass-direction-availability-product-decision.md)）。
この場合の意味論上の扱い（`NO_COMMON_DIRECTION`、入力無効時のfail-safeとの
区別）はSection 8-1・8-2を正本とする。空集合の場合に月盤単独結果を試みる
Fallback精度についてはSection 5-1（CONTRACT TARGET、未実装）を参照。
本Sectionが定義する`CompassDirectionRuntime`型自体のSchemaは、この区別の
ために変更しない（型を返すか`None`を返すかの二値のままとする——
Fallback導入後も三値目（Fallback結果）は同じ型形状で表現される、
Section 5-1参照）。

---

### 5-1. Fallback Precedence（Monthly Fallback、CONTRACT TARGET、未実装）

> `docs/product/compass-product-contract.md` Section 2.2、
> [#2508](../product/compass-product-direction-decision.md) Final Direction
> Logic（Option C）が確定した契約。**本Sectionは契約のみを定義し、
> 実装は行わない**——現行`compass_runtime.py`の
> `build_compass_direction_runtime()`は、この精度をまだ実装していない
> （Section 8-1参照）。

**判定順序（CONTRACT TARGET）**:

```
STEP 1: annual_lucky_directions() で年盤の吉方位集合を計算する
STEP 2: monthly_lucky_directions() で月盤単独の吉方位集合を計算する
        （既存 planned_visit_lucky_directions() が内部で行っている月盤計算を
        そのまま公開関数として呼び出す、#2506で追加済み）
STEP 3: 年盤集合と月盤集合の交差を計算する
STEP 4: 交差が空でない場合:
          referenceDirections = 交差
          calculationMethod   = "annual_monthly_kyusei_v1"
          （= COMMON DIRECTION、Section 2.2-2、既存Option Bの経路と同一）
STEP 5: 交差が空、かつ月盤単独集合が空でない場合:
          referenceDirections = 月盤単独の吉方位集合
          calculationMethod   = "monthly_kyusei_v1"
          （= MONTHLY FALLBACK DIRECTION、Section 2.2-3、新規）
STEP 6: 交差・月盤単独集合ともに空の場合:
          NoCommonDirectionResult相当を返す
          （= narrowed NO_COMMON_DIRECTION、Section 2.2-4）
```

**`referenceDirections`の意味論（source依存、CONTRACT TARGET）**:

`referenceDirections`は、STEP 4とSTEP 5とで異なる由来のデータを保持する
——フィールド自体は同じ形（8方位ラベルの配列）だが、STEP 4では「年盤・月盤
の両方が支持する方位」、STEP 5では「月盤のみが支持する方位」を意味する。
この由来の違いは`calculationMethod`の値（`"annual_monthly_kyusei_v1"`
vs `"monthly_kyusei_v1"`）によってのみ判別可能であり、`referenceDirections`
自体の形からは判別できない。

**Fallback source/metadata（機構の決定）**:

`calculationMethod`が既に2つの異なる固定値（STEP 4/STEP 5で相異なる）を
とるため、**COMMON DIRECTIONとMONTHLY FALLBACK DIRECTIONを区別するための
新規フィールドは不要と判定する**。`directionSource`や`fallbackUsed`等の
追加フィールドを新設せず、既存の`calculationMethod`をsource判別の唯一の
機構として採用する。これは、1つの文字列へ複数の独立した意味を詰め込む
「overloaded string」とは異なる——`calculationMethod`は元々「どの計算方法
で導出されたか」を表すフィールドであり、Fallback有無もまさに「どの計算
方法か」の一種であるため、意味的に整合する。

**決定論性（Determinism、CONTRACT TARGET）**:

同一の`birthdate`・同一の`target_date`・同一の計算バージョンであれば、
STEP 1-6は常に同一の分類（COMMON / MONTHLY FALLBACK / NO_COMMON_DIRECTION）
と同一の`referenceDirections`を返さなければならない。リクエストごとに
異なる結果を返すランダム性、ユーザー単位の隠れたヒューリスティクスは
導入しない。

**Concierge / Ranking境界（不変）**:

Fallback Precedenceは`compass_runtime.py`（Compass Layer B）にのみ実装
されるべきポリシーであり、`kyusei.py`（`monthly_lucky_directions()`含む）
のシグネチャ・返り値契約を変更しない。Recommendation Rankingのスコアリング
・順位付け・Reason authorityのいずれにも影響しない
（`compass-product-contract.md` Section 2.2-8）。

---

## 6. Recommendation Handoff（将来の統合のための最小コンテキスト定義のみ）

本セクションは、Phase 4（Recommendation Integration）が将来必要とする最小Runtimeコンテキストを**定義するのみ**とし、統合の実装は行わない。

### 将来必要となる最小コンテキスト

```typescript
type CompassRecommendationHandoffContext = {
  directionContext: CompassDirectionRuntime;  // Section 5の出力（方向コンテキスト）
  purposeContext: { needTag: NeedTagSlug };     // Section 4の出力（purpose）
  originContext: { lat: number; lng: number };  // Section 3のUserOriginから変換済み座標
};
```

### direction context と purpose context の分離

両者は別フィールドとして保持し、単一の統合オブジェクトへマージしない。これは`compass-product-contract.md` Section 6の「Compass Runtime Authorityは候補集合の中でどの神社が最も意味的に合うかを決定する権限を持たない」という境界を、データ構造のレベルでも維持するためである。

### origin context と Recommendation evidence の分離

`originContext`はRecommendation計算（bearing・distance）への入力であり、それ自体がユーザーへ提示される「根拠（evidence）」にはならない。Evidenceとして提示されるのは、Recommendation Authority・Shrine Knowledge Authorityが生成する情報のみである。

### Concierge既存リクエストSchemaへの影響

**なし**。`ConciergeChatView`・`normalize_concierge_request()`・`ConciergeCanonicalInput`のいずれにも変更を加えない。`CompassRecommendationHandoffContext`はConcierge既存リクエストとは独立した、将来のCompass専用エンドポイントのための設計である。

### ConciergeChatViewを実装都合で流用しない

`docs/audit/premium-visit-compass-recommendation-feasibility.md` Section 5-3が指摘した`_resolve_public_mode()`のcompatモード誤爆リスク（生年月日あり・本文なしという入力形状が`compat`モードと誤判定される）を踏まえ、CompassはPhase 4において独立した新規オーケストレーション層を持つものとし、既存`ConciergeChatView`を実装の簡便さのために流用しない。この方針を本書でも再確認する。

---

## 7. Persistence（永続化）

### Compass MVPはSession/Runtime-onlyで完結できるか

**YES**。Compass Runtime Authorityを構成する全関数（`kyusei.py`・`direction_reference.py`）は副作用のない純粋関数であり、`docs/audit/premium-visit-compass-time-model-contract.md` Section 6-6で確認済みの通り、生年月日+対象日があればいつでも同一結果を再計算できる。

### 永続化が技術的に必要か

**NO**。計算コストは軽量であり、キャッシュ・永続化を要求する技術的理由は確認できない。

### DB/Model/Migration影響

- DB Change: **NONE**
- Migration: **NONE**

### 優先方針

証拠が必要性を示さない限り、永続化を行わない方針を維持する。

### Visit/Reflectionとの関係

既存`Visit`/`ShrineReflection`モデルは、Compass経由の参拝についても将来的に再利用できる可能性があるが、これは本書のスコープ外（将来のPhase 4以降で検討）とする。本書はCompass Runtime Authority自体の永続化要否のみを判定し、YES/NOともに「不要」と結論する。

---

## 8. Fail-safe Contract

すべてのケースにおいて、不足する情報を推測・捏造せず、該当する出力を省略する（既存`direction_reference.py`の「grounded inputsのみ」原則をCompass全体に拡張する）。

> **Status: Active（Section 8-1・8-2で改訂、[compass-product-contract.md](compass-product-contract.md)
> Section 2.1 Decision Record、[#2496](../audit/compass-direction-filter-unavailable-root-cause.md)・
> [#2497](../audit/compass-direction-availability-product-decision.md)の監査結論を反映。
> Bグループのトリガー条件はSection 2.2・[#2508](../product/compass-product-direction-decision.md)
> によりCONTRACT TARGETとしてnarrowing済み——Section 8-1参照）**

以下の表は、原因を**A. 入力/Runtimeが無効または利用不可**と
**B. 入力・計算は有効だが結果として共通方位が存在しない（正当な結果）**
の2グループに明確に分ける。この2グループは意味論として区別しなければ
ならず、同一の技術的状態へ意味を混在させてはならない（Section 8-1・8-2で
詳述）。

### A. INVALID / UNAVAILABLE RUNTIME（既存、変更なし）

| ケース | 挙動 |
|---|---|
| 生年月日が欠落 | 方向コンテキスト（`CompassDirectionRuntime`）を生成しない。デフォルトの生年月日・本命星を代入しない |
| originが欠落 | 方向コンテキストを生成しない（bearingが計算不能なため）。デフォルト座標（例: 東京駅）を代入しない |
| 方位計算が例外で失敗 | 既存の縮退契約（`docs/ops/direction-fail-safe.md`）と同型のtry/exceptパターンを踏襲する。固定イベントコード（例: `profile_calculation_failed`相当）でログし、生年月日・座標・例外メッセージは記録しない。当該リクエストの方向コンテキストのみを省略し、Compass全体のレスポンスを失敗させない |
| `target_date`が不正 | 未指定として扱わず（Section 1参照）、方向コンテキストを省略する。クライアントの不正値をtodayへ黙って差し替えない |
| 節気月境界付近 | 特別なフォールバックを設けない。境界を跨いだ結果の違いはそのまま返す（Section 1参照） |

### B. VALID NO-COMMON-DIRECTION RESULT（narrowed、Section 8-1で追加・改訂）

| ケース | 挙動 |
|---|---|
| 生年月日・`target_date`とも有効で、方位計算（年盤・月盤）自体も正常に完了したが、年盤の吉方位集合と月盤の吉方位集合の交差が空集合、**かつ月盤単独の吉方位集合（`monthly_lucky_directions()`）も空集合**（CONTRACT TARGET、Section 5-1・Section 8-1） | **エラーではない。正当なCompass結果**（`compass-product-contract.md` Section 2.1・2.2-4が定義するnarrowed `NO_COMMON_DIRECTION`、概念上の識別子）として扱う。デフォルト方位を代入せず、かつ「入力を確認してください」という誘導も行わない（Section 8-2） |

### B'. VALID MONTHLY FALLBACK RESULT（新規、CONTRACT TARGET、未実装、Section 8-1参照）

| ケース | 挙動 |
|---|---|
| 生年月日・`target_date`とも有効で、年盤の吉方位集合と月盤の吉方位集合の交差が空集合だが、月盤単独の吉方位集合は空でない（Section 5-1 STEP 5） | **エラーではない。正当なCompass結果**（`compass-product-contract.md` Section 2.2-3が定義するMONTHLY FALLBACK DIRECTION）として扱う。年盤・月盤の合意として表示してはならない（Section 5-1、Signal-to-Explanation Rule）。デフォルト方位を代入せず、「入力を確認してください」という誘導も行わない（Bグループと同じくSection 8-2の原則を適用する） |

**共通原則**: いかなるフォールバックも、裏付けのない占術/方位の主張を生成してはならない（`compass-product-contract.md` Section 9の絶対的制約を継承）。この原則はA・Bいずれのケースにも等しく適用され、既存のfail-safe保護（Aグループの5行）は本改訂によって一切弱められない。

### 8-1 現行実装とのギャップ（IMPLEMENTATION GAP）

> **Status: A/B区別はCLOSED（#2499）。Fallback（B'）はOPEN（[#2508](../product/compass-product-direction-decision.md)、CONTRACT TARGET）**

**A/Bグループの区別（本Section表）— 実装済み**: 現行実装
（`backend/temples/services/compass_runtime.py`の
`build_compass_direction_runtime()`）は、AグループとBグループを既に区別
している。Aグループでは`None`を、Bグループでは`NoCommonDirectionResult()`
（`None`とは異なる専用マーカー型）を返し、呼び出し元
（`compass_recommendation_orchestrator.py`）はこれをそれぞれ
`STATE_DIRECTION_FILTER_UNAVAILABLE`・`STATE_NO_COMMON_DIRECTION`
（`"no_common_direction"`）という別々のstateへマッピングする。本書が
以前記録していた「両者が同一のNoneを返す」というギャップは、この実装
（PR #2499）により解消済みである。

**B'グループ（Monthly Fallback）— 未実装、CONTRACT TARGET**:
`build_compass_direction_runtime()`は、年盤∩月盤の交差が空集合の場合、
月盤単独の吉方位（`monthly_lucky_directions()`、#2506でkyusei.pyへ追加
済み）を試みることなく、無条件に`NoCommonDirectionResult()`を返す。
すなわち、現行実装のBグループ（`no_common_direction`）は、Section 2.2-4
がnarrowingする前の旧トリガー条件（交差が空集合のみ）のままである。
Section 5-1が定義するFallback Precedence（STEP 1-6）・本Sectionの
Bグループ行の narrowed トリガー条件・B'グループ行は、いずれも**契約上の
意味論の区別であり、現時点の実装がこれを実装しているという意味ではない**。

将来この区別を実装レベルで表現する場合、B'グループに対応する新しい状態名
（概念上の例: `monthly_fallback_direction`、実際のAPI/state値の名称は
未確定の**CONTRACT TARGET**）を導入するかどうかは別途実装PR
（[#2508](../product/compass-product-direction-decision.md)§27 PR-2）で
判断する。本書は現時点でその状態名を確定しない。`CompassDirectionRuntime`
型自体（Section 5のSchema）は、`calculationMethod`の受理値集合の拡張
（Section 5冒頭）を除き、本改訂で変更しない——新しいフィールドは追加しない。

### 8-2 リトライ・入力訂正の示唆に関する原則（B・B'グループ）

Bグループ（narrowed `NO_COMMON_DIRECTION`）・B'グループ（`MONTHLY
FALLBACK DIRECTION`）のいずれに該当する結果についても:

- 再試行を主要な解決策として提示してはならない。同一本命星・同一対象月であれば、再計算しても交差・月盤単独集合は決定的に同一である（Section 5-1 決定論性）。
- 生年月日・originの訂正を促してはならない——これらはB・B'グループの前提条件として既に有効である。
- Aグループ（真に入力が無効）とB・B'グループを、ユーザーへの案内文言レベルでも混同してはならない。
- **B'グループ（Monthly Fallback）はBグループと同じ「エラーではない」トーンを共有しつつも、年盤・月盤の合意（COMMON DIRECTION）であるかのように表示してはならない**（`compass-product-contract.md` Section 2.2-7、Signal-to-Explanation Rule）。

（詳細は`compass-product-contract.md` Section 2.1-2・2.2を正本とする。本書はRuntime Contractとしての整合性確認のみを目的とし、UX文言の重複管理は行わない。）

---

## 責務境界

### Product

- `target_date`/origin/purpose/directionの入出力責務の定義
- Fail-safe挙動の定義
- 永続化要否の判定

### Backend・実装

- `CompassDirectionRuntime`・`CompassRecommendationHandoffContext`の正確なSchema実装（Phase 3・4で実装、本書は設計のみ）
- `target_date`から節気月バケットへの正確な丸め処理（既存`_solar_month_index()`の再利用）

### 上位契約

Master Principle・Product Promise・Authority境界・Signal-to-Explanation Ruleは`docs/product/compass-product-contract.md`を正本とし、本書はそれに従属する。

---

## 責務外

本書では以下を管理しない。

- 候補フィルタの実装（Phase 3）
- Recommendation統合の実装（Phase 4）
- UI実装（Phase 5）
- Free/Premium境界（Phase 7）
- Analytics契約（Phase 8）
- Ranking Weightの変更（変更しない）
- Concierge既存リクエストSchemaの変更（変更しない）

---

## 関連ドキュメント

- `docs/product/compass-product-contract.md`（上位正本）
- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/audit/premium-visit-compass-time-model-contract.md`
- `docs/audit/compass-direction-filter-unavailable-root-cause.md`
- `docs/audit/compass-direction-availability-product-decision.md`
- `docs/product/compass-product-direction-decision.md`
- `docs/audit/compass-monthly-direction-calculation-contract.md`
- `docs/audit/compass-monthly-fallback-availability.md`
- `backend/temples/domain/kyusei.py`
- `backend/temples/services/compass_runtime.py`
- `backend/temples/services/direction_reference.py`
- `packages/shared/userOrigin.ts`
- `docs/core/direction-response-contract.md`
- `docs/ops/direction-fail-safe.md`

---

## 更新ルール

- 本書はCompass MVPのRuntime入出力契約のみを管理する。
- 候補フィルタ・Recommendation統合・UI・Premium・Analyticsの実装詳細は、各Phase実装時に別途正本を作成し、本書へ重複記載しない。
- `docs/product/compass-product-contract.md`のMaster Principle・Authority境界が変更される場合は、本書との整合を確認する。
- `target_date`/origin/purpose/directionの責務分離が変更される場合のみ、本書を更新する。
- TODO、実装進捗、PR計画は本書へ記載しない。
