# Weekly Compass — Presentation Product Contract

> **Status: Active — Direction-only target / v1 implementation gap recorded**
>
> 本ドキュメントはWeekly CompassのPresentation責務を管理するProduct正本文書である。現行Runtimeにはpurpose-based v1実装が残るが、2026-09-27 Mother Ship DecisionによりDirection-only targetではpurposeをProduct inputとして使用しない。
>
> 本書は新しいWeekly挙動を発明するための設計書ではない。PR #2800（Weekly Presentation Foundation）、PR #2801（Weekly Compass API）、PR #2807（Web接続）で実装済みの責務境界を、Product Contractとして集約する。
>
> Compass全体のMaster Principle・Authority境界・Signal-to-Explanation Ruleは`docs/product/compass-product-contract.md`を上位正本とする。Direction-only Ranking / Weekly Themeの決定は`docs/product/compass-direction-only-ranking-weekly-theme-decision.md`を参照する。Direction Runtimeの永続化境界は`docs/product/compass-mvp-runtime-contract.md`、Analytics attributionのPersistence境界は`docs/analytics/compass-analytics-contract.md`を参照する。
>
> **Direction-only override:** 本書中の`purpose`を含むv1 Snapshot / API / seedの記述は、現行実装の事実としてのみ有効であり、Direction-only Product Targetを定義しない。Runtime整合後はpurpose依存を解消し、旧v1 Snapshotはhistorical dataとして扱う。

# 目的

Weekly Compassは、既存Monthly Compass / Recommendationの意味・順位・方位計算を変更せず、同一Ownerの同一週におけるPresentation結果を安定して再提示するための表示レイヤである。

本書では以下を定義する。

1. Weekly PresentationのProduct責務
2. Weeklyの時間境界
3. Owner境界
4. Weekly Themeの意味上の責務
5. Featured Shrineの候補・選択・表示契約
6. Snapshotによる再現性契約
7. Monthly Compassとの依存関係
8. Fail-safe / degradation境界
9. Privacy / Persistence境界
10. 現行契約で未決定の事項

---

## 1. Product Promise

Weekly Compassが提供する価値は、**Monthly Direction-only結果を週単位で安定して再提示し、参拝検討へつなぐPresentation continuity**である。

Direction-only targetのPresentationは次の2要素で構成する。

```text
Weekly Presentation
├─ neutral action prompt
└─ 今週の神社
```

neutral action promptは相談・願い・ご利益・心理状態を解釈する「今週の意味テーマ」ではない。

Weekly Compassは、新しい占術計算、Recommendation score、Shrine Knowledge、Reason Authorityを所有しない。

---

## 2. Monthly Compassとの関係

Weekly CompassはMonthly Compassを置き換えない。

Web上の現行責務は次の順序である。

```text
Monthly Compass request
    ↓
Monthly recommendation_success
    ↓
Monthly結果を表示
    ↓
Weekly request
    ↓
weekly_success の場合のみWeekly Presentationを追加表示
```

Weekly requestはMonthly結果の描画を待たせない。

Weekly requestの通信失敗、HTTP 5xx、またはWeekly non-success stateは、Monthly Compassを`backend_error`へ変更しない。

Monthly Compassの以下のfail-safe stateではWeekly requestを実行しない。

- `invalid_purpose`
- `direction_filter_unavailable`
- `no_common_direction`
- `recommendation_eligibility_zero_candidates`
- `direction_zero_candidates`
- `evidence_zero_candidates`
- `backend_error`

したがってWeekly Compassは、**Monthly Compass成功後に追加される補助Presentation**であり、Monthly Compassの成功条件を拡張・上書きしない。

---

## 3. Time Contract

Weekly Compassの時間AuthorityはBackendに置く。

```text
timezone   = Asia/Tokyo
week start = Monday
week range = [ Monday 00:00 JST, next Monday 00:00 JST )
```

DBへ保存する時間境界は`week_start`である。

`week_end`は`week_start + 6 days`として導出する値であり、Snapshotの正本fieldとして保存しない。

Weekly public requestは`target_date`または`timezone`を受け取らない。

Weeklyの基準日はBackendの現在日付から決定する。test用の`reference_date`注入はinternal serviceの責務であり、Product入力ではない。

### Weeklyは独自の方位計算を持たない

Weekly専用の`weekly_lucky_directions`、週番号による方位ローテーション等は存在しない。

WeeklyはMonthly Compassと同じ`build_compass_direction_runtime()`を利用する。

したがってWeeklyという時間単位は、**新しい方位計算精度を意味しない**。

---

## 4. Input Responsibility

Direction-only targetでWeekly Presentationが利用するProduct入力は以下である。

| 入力 | 責務 |
|---|---|
| `birthdate` | 既存Direction Runtimeへの入力 |
| `origin` | Direction-only候補生成の起点 |
| Owner | SnapshotのPresentation continuityを分離するIdentity |
| Backend week boundary | neutral action promptのcadenceとSnapshot週境界 |

Weeklyはpublic inputとして`target_date`・`timezone`を追加しない。

`purpose` / `need_tag` / `goriyaku` はWeekly Direction-only Product inputではない。現行API / Modelに残るpurposeはImplementation Gapであり、固定値や別名へ置換して残してはならない。

---

## 5. Owner Contract

Weekly Presentation SnapshotはOwner単位で分離する。

Ownerは次のXORである。

```text
Authenticated:
  request.user

Anonymous:
  existing concierge_anon_id
```

両方を同時にOwnerとして使用しない。

Weekly専用のanonymous identityまたはcookieを新設しない。

匿名Ownerは既存Identity Authorityを再利用し、同じbrowserからの再アクセスでは同一OwnerとしてSnapshotを参照する。

Ownerの違いはPresentation continuityの分離に使うものであり、Recommendation rankingを変更するためのsignalではない。

---

## 6. Weekly Theme Contract

```text
WEEKLY_THEME_DIRECTION_ONLY_POLICY = NEUTRAL_ACTION_PROMPT
WEEKLY_THEME_PURPOSE_DEPENDENCY    = PROHIBITED
WEEKLY_THEME_DIRECTION_SYMBOLISM   = PROHIBITED
WEEKLY_THEME_SHRINE_SEMANTICS      = PROHIBITED
WEEKLY_THEME_SELECTION_SEED        = WEEK_START_PLUS_PRESENTATION_VERSION
```

Direction-only Weeklyでは、旧purpose-based「今週のテーマ」をsemantic Themeとして維持しない。

代わりに、Weekly Presentation Copyは**neutral action prompt**として扱う。役割は、Monthly Compassで得た候補を参拝検討へつなぐ軽い操作上のきっかけだけである。

### 許可される意味範囲

neutral action promptは、たとえば次のような行動レベルまでを扱える。

```text
- 今月の参考方位にある候補を一つ確認する
- 気になる候補の経路を確認する
- 行けそうな距離の候補を見ておく
```

上記はsemantic contractの例であり、最終UI copyを固定するものではない。

### 禁止事項

neutral action promptは以下を主張してはならない。

```text
- 恋愛 / 仕事 / 金運等のpurpose
- need / goriyaku
- ユーザーの心理状態
- 「今週必要な行動」という断定
- 方位の象徴意味
- 「縁がある」「呼ばれている」等の宗教的因果
- Shrine Knowledgeから導いた個人向け意味
```

### Deterministic selection

neutral action promptの選択に使えるのは次だけ。

```text
week_start
+ presentation_version
```

同じ週・同じPresentation versionなら同じpromptを返す。Owner、birthdate、purpose、direction_fingerprint、Shrine Knowledge、Recommendation scoreはprompt selectionに使用しない。

`direction_fingerprint` をseedに使わないのは、意味関係がないcopyに対して「この方位だからこのテーマが選ばれた」という誤った因果を作らないためである。

LLMとruntime randomは使用しない。

### v1 implementation gap

現行 `weekly_theme_catalog_v1.py` は15 purpose別catalogであり、`purpose + direction_fingerprint + week_start + presentation_version`をseedへ使用する。これはDirection-only targetと不整合であり、Runtime整合PRで置き換える。

既存Snapshotに保存済みのpurpose-based v1 `weekly_theme` は後から書き換えない。Direction-only cutoverでは新しい`presentation_version`を使用し、旧v1 Snapshotと意味を混在させない。

### User-facing表示

FrontendはBackendが返したneutral action promptを意味変更せず表示する。

UI上の見出しを「今週のテーマ」のまま残すことは避け、semantic占い・意味解釈に見えない名称へ変更する。最終copyはFrontend実装PRで確定する。


---

## 7. Featured Shrine Contract

Direction-only targetでは、Weekly Featured Shrineは**Monthly Compassで確定したDISTANCE_ASCのranked result**からPresentation用の最大3件を選ぶ。

Weeklyは新しいRecommendation scoreを作らない。purpose / need / goriyaku / Popularity / Knowledge量で再rankingしない。

### Candidate Universe

Direction-only targetでは次の境界を採用する。

```text
Monthly Direction-only ACTIVE_SET
    ↓
DISTANCE_ASC ranking
    ↓
top 6 only
    ↓
ID resolve
    ↓
invalid removal
    ↓
duplicate removal
    ↓
maximum 3 featured shrines
```

7位以降からの補充は行わない。

上位6件内でinvalid / duplicateが発生し、候補が6件未満になってもCandidate Universeを拡張しない。

現行v1はsemantic Recommendation順位を入力にしているためImplementation Gapである。Direction-only Runtime整合後はMonthlyのDISTANCE_ASC順位をそのまま入力とする。

### 件数Fail-safe

```text
6件以上 -> 上位6件のPoolから最大3件
3〜5件  -> そのPoolから最大3件
1〜2件  -> 全件
0件     -> 空
```

### Display Order

選択されたShrineの表示順は、MonthlyのDISTANCE_ASC順位を維持する。

Frontendでslice、再ranking、shuffle、補充を行わない。

Weekly専用Shrine Card systemは作らず、既存Shrine card representationを再利用する。

---

## 8. Snapshot / Reproducibility Contract

Weekly Presentationの永続化目的は、**同一Owner・同一週・同一purpose・同一direction fingerprint・同一presentation versionの範囲におけるPresentation結果の再現性**である。

Direction Runtimeの計算結果をcacheするための永続化ではない。

### Snapshot Identity

Snapshotは概ね次の組み合わせで一意に識別される。

```text
owner
+ week_start
+ purpose
+ direction_fingerprint
+ presentation_version
```

Reproducibility Contract:

```text
same owner
+ same week_start
+ same purpose
+ same direction_fingerprint
+ same presentation_version

→ same weekly_theme
+ same featured_shrine_ids
```

### Snapshot HIT

Snapshotが存在する場合、保存済みの`weekly_theme`と`featured_shrine_ids`をPresentation Authorityとして使用する。

Snapshot HITでは`get_compass_recommendations()`を再実行しない。

### Snapshot MISS

Snapshotが存在しない場合のみ、次の順でPresentationを確定する。

```text
get_compass_recommendations()
    ↓
Weekly Theme selection
    ↓
Featured Shrine selection
    ↓
Snapshot persistence
```

Recommendationがnon-successの場合はSnapshotを作成しない。

Themeだけを単独で保存しない。

---

## 9. Snapshot Persistence Boundary

Snapshotへ保存するPresentation stateは以下である。

```text
user / anonymous_id
week_start
purpose
direction_fingerprint
weekly_theme
featured_shrine_ids
presentation_version
created_at
```

現行v1では以下をSnapshotの正本データとして保存しない。

- `week_end`
- birthdate
- `target_date`
- origin
- latitude / longitude
- raw `direction_context`
- `recommendation_instance_id`
- `distance_stage_km`
- candidate counts
- raw Recommendation response
- Shrine詳細

したがって、

```text
Direction Runtime = ephemeral / recomputable
Weekly Presentation = persistent
```

は両立する。

Weekly SnapshotはCompass HistoryまたはAnalytics Historyではない。

---

## 10. direction_fingerprint Contract

`direction_fingerprint`は、Weekly SnapshotのPresentation identityを安定させるための内部識別値である。

対象fieldは現行v1で以下に限定する。

```text
referenceDirections
calculationMethod
solarMonthIndex
targetYear
```

`targetDate`や`note`等の表示用fieldはfingerprintへ含めない。

`direction_fingerprint`はユーザー向け意味説明ではない。

方位の象徴意味を表現するIDでもない。

Recommendation scoreでもない。

---

## 11. Hydration / Eligibility Contract

SnapshotはShrine IDを保存し、response生成時に既存Shrine公開表現へhydrateする。

Weekly専用serializer、eligibility rule、Shrine Knowledge ruleは作らない。

既存のShared Recommendation Eligibilityを再利用する。

Snapshot作成後にShrineが削除・非表示・eligibility喪失となった場合、そのShrineは表示から除外する。

この場合、

- 4位以降から補充しない
- Snapshotを書き換えない
- 残存Shrineの順序を変えない

### 0件成功

現行v1では、Snapshotが有効でもhydrate後に`featured_shrines`が0件になる場合がある。

この場合でもBackend stateは`weekly_success`になり得る。

Frontendは現行実装上、「今週の神社」Sectionを表示しない。

この0件状態へ新しい意味・理由・ダミーShrineを付与しない。

---

## 12. Presentation Version

Weekly Presentationは`presentation_version`によってversionを分離する。

現行v1:

```text
weekly_presentation_v1
```

Theme catalog、Selection Contract、Snapshot identity等の互換性を破る変更を行う場合、既存Snapshotと混同しないversioningを維持する。

既存Snapshotの意味を後から書き換える目的でversionを再利用してはならない。

---

## 13. Fail-safe Contract

WeeklyはMonthly Compassより弱い依存として扱う。

Weekly側の失敗によってMonthly Compassの成功結果を失敗へ変更してはならない。

### Non-success

Recommendationがnon-successの場合:

- Weekly Snapshotを作らない
- Weekly Themeを単独保存しない
- Featured Shrineを生成しない
- Monthly結果は維持する

### Action prompt failure

neutral action prompt選択内部で失敗してもMonthly Compass全体を失敗させない。

purpose-based旧Fallback Themeへ戻してはならない。Direction-only用の固定neutral fallback promptへ縮退するか、prompt Section自体を非表示にする。どちらのtransport形を採るかは実装PRで既存API互換性を確認して決める。

### Stale response

Frontendで複数requestが競合した場合、古いWeekly responseを新しいMonthly結果へ表示しない。

---

## 14. Authority Boundary

Weekly Presentationは以下の既存Authorityを再利用する。

Weekly PresentationはCompass全体の第6のtop-level Authorityではない。`docs/product/compass-product-contract.md`が定義する既存Presentation AuthorityのWeekly特化責務として扱う。

| Responsibility source | Weeklyでの責務 |
|---|---|
| Compass Runtime Authority | Direction Runtimeを提供する |
| Compass Runtime / Direction-only Ranking | Direction RuntimeとDISTANCE_ASCの候補順位を提供する |
| Shrine Knowledge Authority | Shrine事実を候補化理由と分離して提供する |
| Existing owner identity resolution | authenticated / anonymous Ownerを解決する |
| Presentation Authority（Weekly specialization） | neutral action promptとFeatured ShrineのPresentationを週単位で固定する |
| Frontend implementation | 保存済みPresentationの意味を変更せず表示する |

Weekly specializationとしてのPresentation Authorityは、Recommendation Authorityを上書きしない。

neutral action promptはShrine Knowledge・purpose・方位象徴意味を新設しない。

SnapshotはDirection Runtime Authorityの正本にならない。

---

## 15. Free / Premium Boundary

現行実装ではWeekly CompassにFree / Premium gateは存在しない。

本書は将来のPaywall、価格、Entitlementを決定しない。

Weekly Presentationの永続化が存在すること自体を、Premium価値またはPremium entitlementの根拠として扱わない。

将来のFree / Premium境界は別のMother Ship Decisionとして扱う。

---

## 16. Analytics Boundary

Weekly PresentationのSnapshot persistenceとAnalytics attributionは別責務である。

`recommendation_instance_id`はWeekly responseへ含めない。

Weekly Featured Shrine表示のために架空の`recommendation_instance_id`または`recommendation_rank`を生成してはならない。

Frontendは既存Analytics source taxonomyの`source="compass"`を再利用する。

Weekly固有Analytics event contractは現行正本では未定義である。

本書では新しいAnalytics eventを発明しない。

---

## 17. Privacy Boundary

Weekly Presentationの永続化に不要なraw personal dataをSnapshotへ複製しない。

少なくとも現行v1では以下をSnapshotへ保存しない。

- birthdate
- raw origin
- latitude / longitude
- raw direction context
- raw Recommendation response

Observability logへもbirthdate、anonymous_id生値、user email、正確な座標等のPIIを出さない。

---

## 18. 現行v1の既知の特性

以下は現行実装上の事実であり、本書で自動的に解消しない。

### 18-1. SnapshotはOwnerの初回成功request時点で確定する

同じ週でも、異なるOwnerが異なる日時に初回アクセスした場合、それぞれ異なるRecommendation断面がSnapshotへ固定される可能性がある。

これはOwner単位Snapshotの現行契約と矛盾しない。

「全ユーザーで同じ週の同じPresentationを共有する」という契約ではない。

### 18-2. `direction_context`全体はSnapshotされない

Snapshot HIT時もDirection Runtimeは現在のBackend基準日から再計算される。

`targetDate`はfingerprint対象外であるため、Presentation Snapshotが同じでもresponse上の`direction_context.targetDate`は日ごとに変化し得る。

Weekly Snapshotが固定するのは`weekly_theme`と`featured_shrine_ids`等のPresentation結果であり、raw Direction response全体ではない。

### 18-3. Featured Shrine 0件でもWeekly Successになり得る

Eligibility変化等によりhydrate可能なShrineが0件になっても、Snapshot自体が有効であれば`weekly_success`になり得る。

現行FrontendはShrine Sectionを非表示とする。

---

## 19. 未決定事項 / Mother Ship Decision

以下は現行実装から一意に決定できないため、本書では確定しない。

1. Weekly Presentationを将来Free / Premiumのどちらへ配置するか
2. Weekly SnapshotのRetention / deletion policyをProductとして明文化するか
3. `weekly_success`かつFeatured Shrine 0件時に専用copy/stateを追加するか
4. Ownerの初回アクセス時点でSnapshotを固定する現行モデルを将来も維持するか
5. Weekly固有Analytics event / KPIを定義するか
6. neutral action prompt catalogの候補数・copy運用をどうversioningするか（semantic sourceはDirection-only Decisionで確定済み）

これらを暗黙に決める変更を、本Contract整合作業へ混在させない。

---

## 責務境界

### Product

本書が管理する。

- Weekly Product Promise
- Weekly time / Owner / Presentationの責務境界
- Weekly Themeの意味上の位置づけ
- Featured Shrine Presentation契約
- Snapshot Reproducibility Contract
- Fail-safe / Persistence / Privacy境界

### Backend

実装とテストを正本とする。

- Snapshot Schema
- DB constraints
- fingerprint canonicalization
- race recovery
- API request / responseの正確なSchema
- hydration implementation
- selection implementation

### Frontend

実装とテストを正本とする。

- Weekly Sectionの表示順
- MonthlyとWeeklyの非同期接続
- stale response protection
- Shrine Card表示
- 0件時のSection非表示

### Analytics

`docs/analytics/compass-analytics-contract.md`を参照する。

### Premium

未決定。別途Mother Ship Decisionとする。

---

## 責務外

本書では以下を変更・決定しない。

- kyusei計算
- Monthly Compass fallback precedence
- Recommendation ranking / weights
- Recommendation Reason
- Shrine Knowledge
- Concierge挙動
- Monthly Compass API contract
- Free / Premium entitlement
- 新規Analytics event
- 新規LLM利用
- Compass History
- Personal Continuity全般
- Daily Compass / Daily Word
- Astrology / planetary position logic

---

## 関連ドキュメント

- `docs/product/compass-product-contract.md`
- `docs/product/compass-mvp-runtime-contract.md`
- `docs/analytics/compass-analytics-contract.md`
- `docs/audit/compass-current-state-audit.md`
- `backend/temples/domain/weekly_time_contract.py`
- `backend/temples/domain/weekly_presentation.py`
- `backend/temples/domain/weekly_theme_catalog_v1.py`
- `backend/temples/models_weekly_presentation.py`
- `backend/temples/services/weekly_presentation_snapshot.py`
- `backend/temples/services/weekly_compass_service.py`
- `backend/temples/services/weekly_featured_shrines.py`
- `backend/temples/api_views_compass_weekly.py`

---

## 更新ルール

- 本書はWeekly CompassのProduct / Presentation責務を管理する。
- Weekly APIの正確なfield名・HTTP status・serializer詳細はBackend実装へ重複記載しない。
- Snapshot Schema・fingerprint algorithm等の実装詳細が変わる場合は、本書のProduct責務へ影響するか確認する。
- Weekly Product Promise、Time Contract、Owner Contract、Reproducibility Contract、Authority境界が変更される場合は本書を更新する。
- Free / Premium、Analytics、Retention等の未決定事項を、実装都合のみで本書へ確定事項として追加しない。
- TODO・PR進捗・監査時点メモは本書へ記載しない。
