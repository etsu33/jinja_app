> **Status: Active**
>
> 本ドキュメントは、神社Knowledge（`deity` / `shrine_history`等）の値の意味、出典（Source）、確認状態、信頼度（confidence）、Fact利用条件、表示条件、AI生成値の制約および情報矛盾時の扱いを管理する正本である。
>
> 神社プロフィールの項目一覧・必須任意・Coverage・品質条件は`docs/knowledge/shrine-profile-spec.md`を正本とする。Recommendationパイプライン全体の段階構成は`docs/core/recommendation-architecture.md`を正本とする。本書はこれらと重複する内容を再定義しない。
>
> 本書はDocsのみのPRとして作成された。コード・Model・Migration・Serializer・Admin・DBデータの変更は一切含まない。記載内容のうちTo-Beと明記した項目は設計方針であり、実装済みであることを意味しない。Model選択・Pilot対象神社・enum最終確定は母艦判断へ差し戻す（本書作成時点＝As-Is）。
>
> **現在（2026-08-01時点）の状況**: 本書「Model選択肢比較」の案4（別Model）が母艦判断で採用され、`ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource`として`feature/shrine-knowledge-model-foundation`（PR #2221）で実装され、`develop`へマージ済みである。また明治神宮1社を対象にReal Data Pilot #1をAdmin経由で実施済み（詳細は`docs/audit/shrine-knowledge-real-data-pilot-1.md`）。ただしEvidence Gate・Recommendation・Score・Web/Mobileへの接続は本書作成時点から変わらず未実装であり、3〜5社規模のPilot本体（PR3相当）・105件Rollout（PR4相当）・Foundationの100%完了判定も未確定のまま母艦判断待ちである。以下の本文はPR2219系列作成時点のAs-Isを保持し、書き換えていない。
>
> **追記（2026-08-02時点）**: 上記注記の後、Evidence Gate（PR2相当）はPR-A（`verification_status`によるFact利用可否判定の一本化、PR #2227）とPR-B（Fact confidenceによるRecommendation Reason表現強度制御、PR #2228・follow-up #2229）として`develop`へ実装・マージ済みである。ShrineDeity/ShrineHistoryの`confidence`（high/medium/low/未設定）はRecommendation Reasonの表現強度（assertive/weakened/suppressed/legacy-compatible）へ接続済み。一方、`ShrineKnowledgeSource.confidence`（Source自体の信頼度）・複数Source間のconfidence集約・Conflicting Evidence（Source間の明示的な矛盾表現）は本追記時点でも未接続のままであり、PR-C1（Source Confidence Contract、本書「Source Confidence Contract」節を参照）で契約のみ整理し、実装はさらに後続PRへ委ねている。Shrine Detail APIへの表示・Score/Rankingへの接続は引き続き未実装。

# Shrine Knowledge Contract

## 目的

本ドキュメントは、以下を単一の情報源として固定する。

1. `deity`（祭神）・`shrine_history`（由緒・歴史）を、根拠のあるFactとして安全にRecommendationへ利用するための契約を定義する
2. Knowledgeの値がどのSourceに基づき、どの確認状態・信頼度を持つかを扱うSource契約を定義する
3. Official / Historical / Editorial Summary / Experience / User Reflection / AI Generated Draftの6分類ごとに、保存可否・表示可否・Recommendation利用可否を定義する
4. 根拠不足の状態でFactが断定的に生成されることを防ぐEvidence Gate要件を、将来実装レベルまで具体化する
5. `Shrine.sajin` / `Shrine.description`を含む5つのModel実装選択肢を比較し、最終選択を母艦判断へ委ねる
6. Pilot対象3〜5社の選定条件・完了条件を定義する（実データ投入は今回行わない）
7. 後続PR4本（Model Foundation / Evidence Gate / Pilot Data / 105件Rollout）の目的・範囲・完了条件を設計する

本書は`docs/audit/concierge-end-to-end-consistency-audit.md`で確認されたBlocker #1（`deity`/`shrine_history`が105件中105件で空。欠損時に`goriyaku_tags`/`history_theme`へfallbackし、根拠のあるFactのように見える可能性がある）を主対象とする。本書はコード・Model・Migration・Serializer・Admin・DBデータの変更を一切伴わない。

## 対象範囲

### 対象

- `deity` / `shrine_history`の値の意味・分類・不明値の扱い
- Source（出典）の項目・確認状態・信頼度・優先順位
- Knowledge分類ごとの保存・表示・Recommendation利用条件
- Evidence Gate要件（将来実装、今回は未実装）
- Fact / Interpretation / Actionとの整合（`docs/core/recommendation-architecture.md`との矛盾がないことの確認）
- Model実装選択肢の比較
- Pilot対象選定条件・完了条件
- 後続PRの設計

### 対象外

- 神社Profile項目の必須・任意・Coverage・品質条件の定義（`docs/knowledge/shrine-profile-spec.md`が正本）
- Recommendationパイプライン全体の段階構成（`docs/core/recommendation-architecture.md`が正本）
- Recommendation ScoreのWeight・計算式（`docs/analytics/recommendation-score-v3-design.md`が正本）
- Recommendation Reasonの出力Schema（`docs/core/recommendation-reason-contract.md`が正本）
- Model・Migration・Serializer・Admin・APIの実装そのもの（後続PRで扱う。2026-08-01時点でPR1相当は`feature/shrine-knowledge-model-foundation`（PR #2221）として実装・マージ済み）
- 105件の実データ投入・Pilotデータ投入（後続PRで扱う。2026-08-01時点で明治神宮1社によるReal Data Pilot #1を実施済み。詳細は`docs/audit/shrine-knowledge-real-data-pilot-1.md`。3〜5社規模のPilot本体・105件Rolloutは未実施）

## 文書構成の判断

### 比較した2案

**案A：`shrine-profile-spec.md`へKnowledge Contract章を追加する**

評価:

| 評価項目 | 評価 |
|---|---|
| 既存のProfile項目定義と自然につながるか | つながるが、「項目が何であるか」と「値をどう信頼するか」が同一章内に混在する |
| 文書が肥大化しすぎないか | 肥大化する。`shrine-profile-spec.md`は現状約710行あり、本書が要求する内容（deity契約・shrine_history契約・Source契約・6分類・Evidence Gate・5案Model比較・Pilot・PR設計）を追加すると2倍近くになる |
| 項目仕様と利用契約が混在しないか | 混在する。`shrine-profile-spec.md`は既に「⑥ Trust Layer」で出典要否の基準までは定義しているが、Source構造・verification_status・confidence算出・AI生成値制約は「未確定事項」として意図的に本文から切り出されている |
| Recommendation Architectureから参照しやすいか | しやすいが、Profile項目定義と混在した状態では引用範囲の特定が難しい |
| 将来のSource ModelやExperience Knowledgeまで扱えるか | 扱えるが、既存の7層モデル（Fact/Meaning/Consultation/Action/Reflection/Trust/Recommendation Readiness）という別の軸との整合を都度取る必要がある |

**案B：`docs/knowledge/shrine-knowledge-contract.md`を新設する**

評価:

| 評価項目 | 評価 |
|---|---|
| shrine-profile-spec.mdとの責務境界が明確になるか | 明確になる。「何の項目が存在するか」（shrine-profile-spec.md）と「その値をどう信頼し、どう利用するか」（本書）を分離できる |
| Knowledgeの出典・確認・利用条件を独立して管理できるか | できる。Source契約・verification_status・confidenceは項目定義よりも変更頻度・実装検討の粒度が異なるため、独立した文書のほうがPR分割・レビュー粒度に合う |
| 重複する正本を生まないか | 生まない。`shrine-profile-spec.md`側の「⑥ Trust Layer」「未確定事項5. Trust Layerの実装場所」は本書へ委譲するポインタへ縮小し、内容を重複させない |
| 将来のModel実装、Evidence Gate、Rollout Planへ接続しやすいか | 接続しやすい。後続PR（Model Foundation/Evidence Gate/Pilot Data/Rollout Plan）は全て本書のSection構成と1対1に対応する |

### 採用した構成と理由

**案Bを採用する。** `docs/knowledge/shrine-knowledge-contract.md`を新設し、`shrine-profile-spec.md`から参照する。

理由:

1. `shrine-profile-spec.md`は既に「本書はTrust Layerの物理実装方法を決定しない」と明記しており、Source構造・確認状態・信頼度・AI生成値制約は既存正本の対象外として意図的に切り出されている。新設はこの既存の境界と一致する
2. 要求される内容量（deity契約・shrine_history契約・Source契約・6分類・Evidence Gate・5案Model比較・Pilot・4本のPR設計）は独立した正本として扱うべき規模である
3. 判断基準として与えられた責務分担（`shrine-profile-spec.md`＝項目・必須任意・Coverage・品質条件、Knowledge Contract＝値の意味・出典・確認状態・信頼度・Fact利用条件・表示条件・AI生成値の制約）にそのまま合致する

### shrine-profile-spec.mdとの責務境界

| 責務 | 正本 |
|---|---|
| 神社Profile項目の一覧（どの項目が存在するか） | `shrine-profile-spec.md` |
| 項目の必須・任意・Coverage | `shrine-profile-spec.md` |
| 項目のRecommendation利用に必要な充足条件 | `shrine-profile-spec.md`（Readiness判定材料の提供）、`docs/core/recommendation-readiness.md`（Readiness Level本体） |
| `deity` / `shrine_history`の値の意味・分類・不明値の扱い | 本書 |
| Source（出典）の項目・確認状態・信頼度 | 本書 |
| Fact利用条件・表示条件・AI生成値の制約 | 本書 |
| 情報矛盾時の扱い | 本書 |
| Recommendationパイプライン全体の段階構成 | `docs/core/recommendation-architecture.md` |

本書は`shrine-profile-spec.md`を統合・吸収しない。`shrine-profile-spec.md`の「⑥ Trust Layer」「未確定事項 5. Trust Layerの実装場所」は、本書公開後は本書への参照ポインタとして扱う（本書がその内容を正本化したことの明示のみを`shrine-profile-spec.md`側へ最小限追記する。項目定義の書き換えは行わない）。

## As-Is（現行コード確認結果）

以下は本書作成にあたり、現行コード（読み取りのみ、変更なし）を確認した結果である。推測は含まない。

> **注記（2026-08-01時点）**: 以下は`Shrine.sajin` / `Shrine.description`という既存のLegacy Fieldに関するAs-Isであり、本書作成後にPR #2221で実装された`ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource`（新Model）とは別物である。`sajin` / `description`はPR #2221でも変更・削除されておらず、以下の記述は現在も有効である。新Modelの実装・Admin・Serializer・APIの状況は本書「Model選択肢比較」「後続PR設計」の追記、および`docs/audit/shrine-knowledge-real-data-pilot-1.md`を参照。

### Model定義

`backend/temples/models.py`の`Shrine`Model:

```python
sajin = models.TextField(help_text="祭神", blank=True, null=True, default="")
description = models.TextField(blank=True, null=True)
```

- `sajin`・`description`はいずれも単一のTextField。複数祭神を構造的に保持する仕組み、出典・確認状態・信頼度・AI生成フラグを保持するFieldは存在しない
- `description`には`help_text`が設定されておらず、「神社紹介文」「由緒」「ご利益説明」「Recommendation用説明」のいずれを意図したFieldかがModel定義からは判別できない。実装上の利用箇所を確認した限り、`description`を単一責務として扱っている箇所は無く、責務が混在している状態と確認できる

### Serializerでの返却範囲

- `ShrineWriteSerializer`（`backend/temples/api/serializers/shrine.py`）: `sajin` / `description`を書き込み可能Fieldとして含む
- `ShrineListSerializer` / `ShrineDetailSerializer`（`ShrineSerializer`としてエイリアス、同ファイル）: `sajin`を含まない。`description`も含まない
- `ShrinePublicSerializer`（`backend/temples/api/serializers/shrine_public.py`）: `description`は含むが`sajin`は含まない

**確認された事実**: Web/Mobileの神社詳細表示（Detail画面）が実際に使用するSerializerには`sajin`が一切含まれていない。`description`も`ShrineDetailSerializer`には含まれず、`ShrinePublicSerializer`経由の一部エンドポイントでのみ返却される。つまり現状、`sajin`はSerializer経由でWeb/Mobileの表示APIへ到達する経路がない。

### Recommendation Reason生成での利用経路

`sajin`/`description`は上記の表示用Serializerとは別の、Recommendation内部専用の経路でのみFact生成に利用されている。

`backend/temples/services/concierge_chat.py`の`_build_score_v3_candidate_profile()`:

```python
"deity": rec.get("sajin") or source.get("sajin"),
"shrine_history": rec.get("description") or source.get("description"),
```

この`rec`/`source`はRecommendation内部のRuntime dict（表示用Serializerとは別経路）であり、ここで初めて`sajin`→`deity`、`description`→`shrine_history`という概念名への変換が行われる。

`backend/temples/services/recommendation_reason_v4.py`の`_build_fact()`は、この`candidate_profile`（上記dictの後継）から`deity`/`shrine_history`を取り出しFactへ格納する。`deity`/`shrine_history`自体には`goriyaku_tags`や`history_theme`へのフォールバックは実装されていない（空なら空のまま）。

一方、同関数が生成する`label`（Fact全体の代表ラベル）は次の優先順位でフォールバックする。

```python
label = _first_string(deity, shrine_history, place_context, history_theme, goriyaku, name, "候補神社") or "候補神社"
```

さらに`QUALITY_FACT_KEYS = ("deity", "shrine_history", "goriyaku", "history_theme")`（同ファイル）が示すとおり、Recommendation Reasonの品質判定（`reason_facts`が空か否か）は`deity`/`shrine_history`と`goriyaku`/`history_theme`を同列に扱っている。`docs/audit/reason-facts-coverage.md`が既に記録しているとおり、`deity`/`shrine_history`が105件中105件で空である現状では、`reason_facts`の非空判定は実質的に`goriyaku`/`history_theme`（Meaning Layerの解釈情報）にのみ依存している。これがBlocker #1の「欠損時にfallbackし、根拠のあるFactのように見える可能性がある」の具体的な発生箇所である。

> **注記（2026-08-01時点）**: ここで言う`deity`/`shrine_history`は、上記コード引用のとおり`Shrine.sajin`/`Shrine.description`（Legacy Field）に由来するRecommendation内部Fact keyであり、PR #2221で実装された`ShrineDeity`/`ShrineHistory`Modelとは接続されていない（本PR・Pilot #1のいずれも「Recommendation・Score・Evidence Gate・Frontendには接続しない」を明示的な対象外としている）。したがって明治神宮1社に対する新Modelへのデータ登録（Pilot #1）後も、この「105件中105件で空」という状態および数値は変化していない。

### Admin編集経路

`ShrineAdmin`（`backend/temples/admin.py`）は`fields`/`fieldsets`/`exclude`を明示的に指定していないため、Django標準の挙動により`sajin`/`description`を含む全Modelフィールドが編集フォームへ表示される。ただし`list_display`には含まれず、専用の入力補助・出典入力欄・確認状態入力欄は存在しない。`seed_history_theme`のような専用Admin Actionも`sajin`/`description`には存在しない。

### ShrineReflectionの現行責務

`ShrineReflection`（`backend/temples/models.py`）:

```python
history_theme = models.CharField(...)  # 保存時点のスナップショット
prompt = models.TextField(...)
answer = models.TextField()
mood_before = models.CharField(...)
mood_after = models.CharField(...)
```

出典・確認状態・信頼度・匿名化・集約に関するFieldは存在しない。同一ユーザー・同一神社に対する個人記録として保存されるのみで、他ユーザーの推薦へ還元される経路、または神社Knowledgeへ反映される経路は存在しない（`docs/core/recommendation-architecture.md` Section 13「Reflection and Learning」のAs-Isと一致）。

### 実データ確認

`backend/`の実データ確認により、`Shrine.sajin`・`Shrine.description`は105件中105件で空（`sajin=''`、`description=None`）であることを確認済み（前回監査時点の確認を維持）。また、DBには`id=101〜105`として明らかなテストフィクスチャ（「承認テスト神社」「admin承認テスト神社」「重複検証神社」等）が含まれており、これらは`history_theme`未設定のまま残置されている。これはBlocker #1の対象データそのものではないが、後続のPilot選定・Rollout範囲確認時にテストデータを実神社と混同しないための注意事項として記録する。

---

## deity契約

`deity`を、神社に祀られている神格・祭神に関するKnowledgeとして定義する。

### 項目

| 項目 | 定義 |
|---|---|
| `display_name` | UI表示に用いる祭神名（正規化前、神社の掲載表記を優先） |
| `canonical_name` | 検索・照合用に正規化した祭神名 |
| `role` | この神社における当該祭神の位置付け（下記参照） |
| `aliases` | 別名・異表記のリスト |
| `source_reference` | この祭神情報の根拠となるSource（Source契約を参照） |
| `verification_status` | 確認状態（Source契約を参照） |
| `confidence` | 信頼度（Source契約を参照） |
| `verified_at` | 確認日時 |
| `note` | 補足（複数説がある場合の注記等） |

### role候補

- `primary`: 主祭神
- `enshrined`: 祀られている神（主祭神とは限らない一般的な位置付け）
- `secondary`: 配祀神・相殿神
- `unknown`: 神社側の記載から序列・位置付けが判別できない

**原則**: 日本語の「主祭神」「配祀神」「相殿神」という表現の粒度は神社ごとに異なり、序列の有無自体が神社の由緒・宗派の事情に依存する。全ての神社を一律に「主祭神・配祀神」の二分類へ強制的に押し込まない。序列が公式情報に存在しない場合は`role: unknown`とし、複数祭神を対等に列挙する。

### 複数祭神

- 1社に複数の`deity`エントリを保持できる（1対多）
- 表示順序は、公式情報に序列がある場合はその順序を尊重し、ない場合は登録順または五十音順など機械的な順序を用いる（最終方式は実装PRで決定）
- 主祭神が不明なケースでは、全エントリを`role: unknown`として列挙し、Fact生成時に「主祭神」という断定表現を使わない
- 公式情報に序列がないケース（例: 複数の神を対等に祀る神社）では、序列の不在自体を`note`へ記録し、順序を推測で作らない
- 同一神格の別名（例: 大国主神/大己貴命）は`aliases`へ保持し、`canonical_name`で名寄せする
- 神社ごとの表記（旧字体・独自の当て字等）は`display_name`として個別に保持し、`canonical_name`へ強制的に一本化しない

### 表記揺れ

以下を区別して保持する。

| 区分 | 内容 |
|---|---|
| 公式掲載名 | 神社公式サイト・由緒書に掲載されている表記そのもの |
| 一般的な表記 | 百科事典・観光情報等で一般に使われる表記 |
| 別名 | 神話上の別名・異称 |
| 旧字体・新字体 | 同一神格の字体差 |
| 読み仮名 | 読みの情報（存在する場合） |
| 正規化キー | 検索・照合用に一意化したキー（`canonical_name`） |

### 不明値

不明・未登録・未確認を空文字で曖昧に混在させない。最低限、以下を区別する。

| 値 | 意味 |
|---|---|
| `unknown` | 公式情報を確認したが祭神が特定できない、または非公開 |
| `not_collected` | まだ情報収集を行っていない（未着手） |
| `unverified` | 情報は存在するが確認作業が完了していない |
| `not_applicable` | 祭神という概念が該当しない対象（該当ケースがあれば個別記録） |

`not_collected`と`unknown`を同一視しない。前者は運用上の未着手、後者は確認済みの情報不足である。

### 出典必須条件

- `deity`をFactとして表示・利用するには`source_reference`が必要
- AI生成のみの祭神情報を`verification_status: source_confirmed`以上として保存しない
- 二次情報しかない場合は、`verification_status`と`confidence`でその弱さを区別する（断定Factとしては扱わない）
- 情報源が矛盾する場合、黙って一方を採用しない（Source契約の「情報矛盾時」を参照）
- 複数説がある場合は、その状態自体を保持する（1つに絞り込んで確定情報のように見せない）

### Fact利用条件

`deity`をRecommendation ReasonのFactとして利用してよいのは、以下をすべて満たす場合とする。

- `verification_status`がFact利用可能な状態にある（Source契約の「verification_statusとFact利用可否」を参照）
- 利用可能な`source_reference`が存在する
- 対象神社との紐付けが確認できる（他の神社の祭神情報を誤って参照していない）
- AI生成値のみではない（`AI Generated Draft`分類のみでは利用不可）
- 情報が`disputed`（矛盾未解決）の場合は断定利用しない
- `confidence`が不足する場合は表現を弱めるか非表示にする（Evidence Gate要件を参照）

### AI生成値の制約

以下を禁止する。

- AIが推測した祭神情報を確認済みFactとして保存する
- Sourceなしで`canonical_name`を確定する
- 不明値をAIで埋めて`verification_status: source_confirmed`扱いにする

AIの利用は以下に限定する。

- 表記揺れ候補の抽出
- 要約案の作成
- 調査候補（次に確認すべきSource候補）の提示
- 正規化候補（`canonical_name`候補）の提示
- レビュー前のDraft作成（`AI Generated Draft`分類として保存し、人手確認前は`verified`扱いにしない）

---

## shrine_history契約

`shrine_history`を、由緒・創建・歴史的出来事・伝承に関するKnowledgeとして定義する。

### 現行`Shrine.description`の責務混在（As-Is確認結果）

As-Is確認の結果、`description`は以下の複数責務を分離せずに1つのTextFieldへ格納する設計になっている可能性が高いことを確認した（`help_text`未設定、単一責務を示す利用制約がコード上に存在しない）。

- 神社紹介文
- 由緒
- 歴史
- ご利益説明
- Recommendation用説明
- 編集要約
- AI生成文

### 分類案（To-Be）

| 分類 | 内容 |
|---|---|
| `official_origin` | 神社公式が掲載する由緒そのもの（原文または原文に基づく保存） |
| `founding` | 創建・鎮座に関する情報（確定年・推定年代・不詳を区別） |
| `historical_event` | 創建後の歴史的出来事（再建・遷座・合祀・被災等） |
| `tradition` | 伝承・社伝（確定史実と区別する） |
| `regional_context` | 地域史・周辺文化との関係 |
| `editorial_summary` | Sourceに基づくアプリ向け要約（公式原文ではない） |
| `ai_generated_draft` | AIが生成した要約・説明文の下書き（未確認） |

分離は今回のPRでは実装しない。分類案として提示し、実装方式（単一Field内の構造化か、複数Fieldか、別Modelか）はSection「Model選択肢比較」で扱う。

### 公式由緒

- 神社公式が掲載する由緒は`official_origin`として扱う
- 原文引用ではなく、「保存方式」（Sourceへのリンク・書誌情報の保持）と「要約方式」（アプリ向け短文）を分離する。長文の原文をそのままDBへ複製する方式は本書では前提としない
- `source_reference`を必須とする
- 公式情報であっても、由緒に含まれる伝承的記述を歴史的確定事実として扱わない（公式由緒の中にも`tradition`要素が混在し得ることを前提とする）

### 創建情報

- 創建年: 確定年が判明している場合はその年を保持する
- 推定年代: 「〜世紀頃」等、幅を持つ年代情報を保持する。確定年と同一Fieldへ混在させない
- 不詳: 創建年が不明であることを明示する値を持つ（空文字と区別する）
- 再建・遷座・合祀・現在地への移転: いずれも`historical_event`として個別に記録できる構造にする

確定年と伝承上の年代（社伝による創建年等、史料的裏付けが弱いもの）を同一の年数値へ押し込まない。伝承上の年代は`tradition`分類側で扱う。

### 歴史的出来事

各出来事について以下を保持する。

- 出来事の内容
- 時期（確定日/推定時期/不詳）
- Source
- 確認状態
- 神社との関連（直接の出来事か、周辺地域の出来事か）
- 現在の神社体験との関係有無（Recommendationで言及してよい関連性があるか）

### 伝承

- 伝承は`Historical Knowledge`の一部として扱うが、確定史実とは明確に区別する
- 表現ルール: 「伝えられている」「社伝では〜とされる」等、伝承であることが読み手に伝わる文体を用いる。確定した歴史的事実であるかのような断定表現（「〜した」で言い切る等）を用いない
- Recommendation Reasonでは、伝承を事実として断定しない

### 編集要約

- `editorial_summary`はSourceに基づくアプリ向け要約であり、公式原文そのものではない
- 元のSourceへ追跡可能な状態を維持する（どのSourceのどの記述を要約したかを`source_reference`で保持する）
- AI生成Draftと人手確認済み要約を`verification_status`で区別する
- 編集要約を神社の公式見解であるかのように表示しない

### 不明値・未確認値

| 値 | 意味 |
|---|---|
| 情報なし | 調査済みだが該当する記述が存在しないと確認できた状態 |
| 未調査 | まだ調査に着手していない状態 |
| 公式情報なし | 公式Sourceに由緒記述が存在しない状態（二次資料のみ存在する可能性がある） |
| 複数説あり | 由緒・創建年等について複数の異なる説が存在する状態 |
| 出典確認中 | Sourceの妥当性を確認する作業が進行中の状態 |
| AI Draftのみ | AIが生成した内容のみで、人手確認が行われていない状態 |

### Fact利用条件

`shrine_history`をFactとして利用してよいのは、以下をすべて満たす場合とする。

- `source_reference`が存在する
- `verification_status`がFact利用可能な状態にある
- 確定史実（`founding`/`historical_event`）と伝承（`tradition`）が分類されている
- `AI Generated Draft`のみではない
- Sourceの内容を越えた因果関係（例:「この歴史があるから運気が上がる」）を付け加えていない

### 断定可能範囲

- Sourceが示す範囲だけをFactとして扱う
- 歴史的事実から心理的効能を直接導かない
- 由緒から現在の雰囲気（静けさ・混雑等）を断定しない（雰囲気は`Experience Knowledge`の責務であり、`Historical Knowledge`と混同しない）
- ご利益タグ（`goriyaku_tags`）を歴史的事実の代替として扱わない
- `history_theme`（Meaning Layerの解釈情報）を由緒そのものとして扱わない。`docs/product/meaning-translation-mapping.md`が定義するとおり、`history_theme`は`shrine_history`からの解釈生成物であり、一次事実ではない

---

## Source契約

Knowledgeの根拠を保持するSource契約を以下に定義する。

### 項目

| 項目 | 内容 |
|---|---|
| `source_type` | 出典種別（下記参照） |
| `title` | 出典のタイトル（書籍名・掲載記事名・案内板名称等） |
| `publisher` | 発行主体（神社、自治体、出版社等） |
| `url` | Web出典のURL（存在する場合） |
| `bibliography` | 書誌情報（書籍・論文等、URLを持たない出典向け） |
| `accessed_at` | 情報源へアクセスした日 |
| `verified_at` | 内容を人または承認済み工程で確認した日 |
| `verification_status` | 確認状態（下記参照） |
| `confidence` | 信頼度（下記参照） |
| `note` | 補足 |
| `archived_reference` | Web出典が消失した場合等に備えたアーカイブ参照 |
| `language` | 出典の言語 |

### source_type候補

- `shrine_official`: 神社公式サイト・公式刊行物
- `government`: 国・自治体の公開資料
- `cultural_property`: 文化財指定関連資料
- `academic`: 学術論文・研究書
- `museum_or_archive`: 博物館・公的アーカイブ
- `local_history`: 地域史・郷土資料
- `tourism_official`: 公式観光情報（自治体観光協会等）
- `secondary_editorial`: 信頼できる二次資料（百科事典・出版物等）
- `user_observation`: 現地観察（運用担当者・信頼できる参拝記録）
- `internal_research`: 社内調査記録
- `ai_generated_draft`: AI生成Draft（Sourceとしての独立した信頼性は持たない）

既存の命名規約が別途存在する場合はそれに合わせる。今回のPRでは既存のsource_type命名規約を確認したが、専用の既存正本は確認できなかったため、上記を新規の初期候補として提示する。

### URLまたは書誌情報

Web出典のみを前提にしない。以下を扱えるようにする。

- URL
- 書籍
- 論文
- 自治体資料
- 現地案内板
- パンフレット
- 文化財データ
- 現地観察記録

### accessed_atとverified_at

- `accessed_at`: 情報源（URL・資料）へアクセスした日
- `verified_at`: 内容を人または承認済み工程で確認した日

両者は独立して記録する。アクセスしただけで内容確認が完了していない状態（`accessed_at`はあるが`verified_at`がない）を区別できるようにする。

### verification_status候補

| 状態 | 意味 | Fact利用可否 |
|---|---|---|
| `draft` | 未確認の下書き段階 | 不可 |
| `unverified` | Sourceは存在するが内容未確認 | 不可（Interpretation限定での言及は状況による） |
| `source_confirmed` | Sourceの内容と一致することを確認済み | 可（`confidence`次第で表現強度を調整） |
| `reviewed` | 複数人または承認工程でレビュー済み | 可 |
| `disputed` | 複数Sourceが矛盾し未解決 | 不可（断定禁止。多説併記または非表示） |
| `outdated` | 過去に確認済みだが情報が古くなった可能性がある | 再確認まで限定的表現に留める |
| `rejected` | 確認の結果、誤りと判断され採用しない | 不可 |

最終enumの確定は今回行わず、Model実装前の母艦判断としてもよい。ただし各状態の意味とFact利用可否は上表のとおり定義する。

### confidence

`confidence`を単なる飾りの数値にしない。最低限、以下の利用先を定義する。

- Fact表示可否（`docs/core/recommendation-architecture.md` Section 12「Evidence Gate要件」の閾値判定に接続）
- Recommendation Reasonの表現強度（断定/弱い表現/非表示の切り替え）
- Evidence Gate（本書のEvidence Gate要件を参照）
- `data_confidence_score`（`docs/core/recommendation-architecture.md` Section 7のScore軸）
- Review対象抽出（confidence不足のエントリを優先的にレビューキューへ）
- Rollout QA（Section「後続PR設計」PR4のQA指標）

算出方式は今回確定しない。候補を比較する。

| 候補 | 内容 |
|---|---|
| 人手入力 | レビュー担当が主観的に評価し入力する |
| Source typeによる基準値 | `source_type`ごとに基準confidenceを設定する（例: `shrine_official`は高め、`ai_generated_draft`は低め） |
| verification_statusから算出 | `verification_status`の値に応じて機械的に決定する |
| 複数Source一致度から算出 | 同一項目に複数Sourceが存在する場合、内容の一致度から算出する |
| 複合方式 | 上記を組み合わせる（例: Source typeを基準値とし、verification_statusで補正する） |

> **追記（PR-C1、2026-08-02時点）**: 上記`confidence`は`ShrineDeity`/`ShrineHistory`（Fact自身）と`ShrineKnowledgeSource`（Source自身）の双方が個別に持つ同名フィールドであり、意味が異なる。
>
> - **Fact confidence**（`ShrineDeity.confidence`/`ShrineHistory.confidence`）: Evidence Gate PR-Bで実装済み。Recommendation Reasonの表現強度（high→assertive/現行文言、medium→weakened/限定表現、low→suppressed/Knowledge Factとして使用しない、未設定→legacy-compatible/現行互換の通常表現）へ接続されている。Fact利用可否（usable判定）そのものには使わない。
> - **Source confidence**（`ShrineKnowledgeSource.confidence`）: PR-C1時点で以下のいずれにも使わないと確定する。Evidence usable判定、Recommendation Reason表現強度、Score/Ranking。Source confidenceからFact confidenceへの自動変換も行わない（上表の「Source typeによる基準値」「複数Source一致度から算出」「複合方式」はいずれも未採用のままの候補であり、Source confidence自体をどう算出・利用するかは引き続き未確定）。
> - 上表の「利用先」のうち、`data_confidence_score`（Score軸）は今回も対象外のまま。数値閾値も導入していない（PR-Bはcategorical値(high/medium/low)をそのままReason表現強度へ対応させており、数値閾値を持たない）。

### 情報矛盾時

- 矛盾するSourceを削除せず保持する（片方を消して整合性があるように見せない）
- 優先Sourceを記録する（どちらを主として扱っているかを`note`等で明示する）
- 未解決状態（`disputed`）を保持する
- Recommendationでは断定を避ける（Evidence Gate要件を参照）
- Admin（または将来のReview Queue）で確認対象として抽出できるようにする
- 多説併記が必要な場合、`deity`の複数祭神と同様に、両論を対等に保持する構造を許容する

### 出典優先順位

固定的な絶対順位ではなく、情報種別に応じた優先原則として以下を定義する。

1. 神社公式（`shrine_official`）
2. 国・自治体・文化財機関（`government` / `cultural_property`）
3. 学術・博物館・公的アーカイブ（`academic` / `museum_or_archive`）
4. 地域史・郷土資料（`local_history`）
5. 公式観光情報（`tourism_official`）
6. 信頼できる二次資料（`secondary_editorial`）
7. 現地観察（`user_observation`）
8. ユーザーReflection（`User Reflection`分類。Knowledge分類を参照）
9. AI Generated Draft（`ai_generated_draft`。Sourceとしての独立した信頼性は最も低い）

**重要な例外**: 神社公式の記述であっても、その中に伝承（`tradition`）が含まれる場合は、公式Sourceであることが伝承を史実へ格上げする根拠にはならない。史実と伝承の分類は、Source種別の優先順位とは独立して行う。

> **追記（PR-C1、2026-08-02時点）**: 上記の優先順位は「情報確認時にどのSourceを先に当たるか・優先して参照するか」という運用上の原則であり、`confidence`の自動算出式ではない。したがって以下を明確にする。
>
> - `source_type: shrine_official`だからといって、そのSourceの`confidence`が自動的に`high`になるわけではない
> - `source_type: government`だからといって、そのSourceの`confidence`が自動的に`high`になるわけではない
> - `source_type`の値だけから`confidence`を自動設定する処理は行わない（Evidence Gate・Recommendation双方に、`source_type`から`confidence`を導出するロジックは実装されていない。`source_type`単体で`confidence`を推測することを禁止する）
> - 上記「重要な例外」（公式Source内の伝承は公式であることだけで史実にならない）は、confidenceについても同様に適用される。公式Sourceであることは高confidenceの根拠にならない

## Source Confidence Contract（PR-C1、2026-08-02追加）

> **Status**: 契約確定のみ。コード実装は伴わない（PR-C1はDocsのみのPR）。

PR-A（`verification_status`によるFact利用可否の一本化）・PR-B（Fact confidenceによるRecommendation Reason表現強度制御）により、Knowledge Factの利用可否・表現強度は確定した。本節は、まだ未接続の`ShrineKnowledgeSource.confidence`（Source自身のconfidence）・複数Source間の集約・Conflicting Evidenceについて、実装せずに契約のみを整理する。

### Source confidenceの現在の扱い

`ShrineKnowledgeSource.confidence`は、個々の出典（Source）自体への信頼度metadataである。PR-C1時点で、以下のいずれにも使わないと確定する。

- Evidence usable判定（`temples.services.evidence_gate.decide_fact_usability()`は`Source.verification_status`のみを参照し、`Source.confidence`は参照しない）
- Recommendation Reason表現強度（表現強度はFact confidenceのみから決定する）
- Score / Ranking
- Fact confidenceへの自動変換（Source confidenceが高いからFact confidenceを引き上げる、といった自動反映は行わない）

Source confidenceは、上記いずれとも独立したmetadataとして保存され続ける。将来これを利用する場合は、別途PR（後述PR-C5候補）で契約を確定してから実装する。

### 複数Source confidenceの集約（未確定）

1つのFactに複数Sourceが紐づき、それぞれのconfidenceが異なる場合（例: Source A=high, Source B=medium）の集約方式は、本書・実装のいずれにも存在しない。以下はいずれも**採用していない**候補である。

- min（最も低い値を採用）
- max（最も高い値を採用）
- average（平均）
- majority（多数決）
- highest priority source（出典優先順位が最も高いSourceのconfidenceを採用）
- official source override（`shrine_official`のconfidenceを優先）

PR-C1では、これらのうちいずれか一つを新たに確定・実装することはしない。集約方式そのものが**未確定**であることを契約として明記するに留める。

### Conflicting Evidenceの表現限界（現行Model）

`ShrineDeity.sources` / `ShrineHistory.sources`は`ShrineKnowledgeSource`への`ManyToManyField`（`through`未指定の暗黙中間テーブル）であり、Relationの「意味」を保持するfieldを持たない。したがって現行Modelでは、以下の2つを区別できない。

- 「SourceがそのFactへRelationされていない」（＝単に言及・確認していない）
- 「SourceがそのFactを明示的に否定している」（＝内容を読んで矛盾すると判断した結果としての否定）

`docs/audit/knowledge-model-pilot-2-shinagawa.md`（Pilot #2、品川神社）でも同様の指摘が既に記録されている（「『Source Bに書かれていない』ことと『Source BがSource Aを否定している』ことは分離する必要がある」）。この区別が必要なケースは、PR-C1時点では**未対応**として扱う。Evidence Gateへ「Relationが無い＝暗黙的に否定している」等の推測ロジックを追加しない。

### Future Model候補（確定しない）

将来、Source間の明示的な支持・否定・言及を区別する必要が生じた場合の候補として、`FactSourceEvidence`（仮称）のような明示的中間Modelを提示する。ただし今回はModel設計を確定せず、Migrationも作らない。

候補field（あくまで案）:

- `source`（FK: `ShrineKnowledgeSource`）
- `deity` / `history`（FK: `ShrineDeity` / `ShrineHistory`、いずれか一方）
- `relation_type`（choices候補: `supports`（支持） / `contradicts`（明示的否定） / `mentions`（言及のみ、支持とも否定とも言えない中立情報））
- `note`
- 確認metadata（`verified_at`等、既存Source契約に準ずる）

採否・詳細設計は将来のPR（後述PR-C3候補）で改めて検討する。

### disputedの表示方針との分離

`verification_status: disputed`のFactを非表示にするか多説併記にするかという表示方針は、本節（Source Confidence Contract）の対象外とする。これは「Source Confidence」ではなく「単一Fact内でverification_statusがdisputedになった場合の表示制御」であり、別PR（後述PR-C4候補）で設計する。PR-C1はこの方針を確定しない。

### `data_confidence_score`との関係

`data_confidence_score`（`docs/core/recommendation-architecture.md` Section 7のScore軸候補）は、PR-C1でも引き続き対象外とする。算出式を作らない。Score/Rankingへの接続も行わない。

---

## Knowledge分類

### Official Knowledge

| 項目 | 内容 |
|---|---|
| 定義 | 神社が公式に提供する事実情報 |
| 例 | 祭神、所在地、公式由緒、参拝時間、公式設備情報 |
| 保存可否 | 可 |
| 表示可否 | 可（`verification_status`がFact利用可能な状態の場合） |
| Recommendation利用可否 | 可（Evidence Gate要件を満たす場合） |
| 必要なSource | 必須 |
| 必要なverification | 必須（`source_confirmed`以上） |
| confidenceの扱い | Fact表示強度の調整に使用 |
| 禁止事項 | 古くなった情報を鮮度確認なく永続的にFactとして扱うこと |

### Historical Knowledge

| 項目 | 内容 |
|---|---|
| 定義 | 創建・歴史的出来事・伝承・地域史・文化財背景に関する情報 |
| 例 | 創建年、再建・遷座の記録、伝承、地域史との関係 |
| 保存可否 | 可 |
| 表示可否 | 可（史実/伝承が分類されている場合） |
| Recommendation利用可否 | 可（Sourceを越えた因果関係を付け加えない範囲で） |
| 必要なSource | 必須 |
| 必要なverification | 必須（史実は`source_confirmed`以上、伝承は`tradition`分類であることの明示で足りる） |
| confidenceの扱い | 伝承か史実かの区別と合わせて表現強度を調整 |
| 禁止事項 | 伝承を確定史実として断定表示すること |

### Editorial Summary

| 項目 | 内容 |
|---|---|
| 定義 | Sourceに基づくアプリ向け要約。公式原文そのものではない |
| 例 | アプリ向け由緒要約、神社紹介文、読みやすく整えた説明 |
| 保存可否 | 可 |
| 表示可否 | 可（元Sourceへの追跡可能性がある場合） |
| Recommendation利用可否 | 可（新たなFactの追加をしない範囲で） |
| 必要なSource | 必須（要約元） |
| 必要なverification | AI Draftと人手確認済みを区別して管理 |
| confidenceの扱い | 人手確認済みかAI Draftかで区別 |
| 禁止事項 | 編集要約を神社の公式見解として表示すること、要約時にFactを新規追加すること |

### Experience Knowledge

| 項目 | 内容 |
|---|---|
| 定義 | 参拝時の観察に基づく雰囲気・環境情報 |
| 例 | 静けさ、混雑、坂、階段、滞在しやすさ、季節感、朝夕の雰囲気 |
| 保存可否 | 可（観察日を伴う場合） |
| 表示可否 | 可（観察件数・鮮度を考慮した限定表現で） |
| Recommendation利用可否 | 可（表現を限定した範囲で。Official/Historical Knowledgeとの混同禁止） |
| 必要なSource | `user_observation`（現地観察） |
| 必要なverification | 観察日の記録が必須 |
| confidenceの扱い | 観察件数・時間帯・季節の偏りを考慮して低めに設定 |
| 禁止事項 | Official Knowledgeと混同すること、少数観察（例: 1件）から一般化すること、個人差・時間帯差・季節差を無視すること |

### User Reflection

| 項目 | 内容 |
|---|---|
| 定義 | 個人の参拝記録（`ShrineReflection`） |
| 例 | 感情、実感、推薦との一致・不一致、再訪意向 |
| 保存可否 | 可（本人記録として） |
| 表示可否 | 原則として本人向けのみ |
| Recommendation利用可否 | 不可（単独では）。匿名集約後のExperience Knowledge化は将来設計（`docs/core/recommendation-architecture.md` Section 13 To-Be候補を参照） |
| 必要なSource | `user_observation`相当（本人の体験そのもの） |
| 必要なverification | 本人記録である旨の記録のみ。第三者検証は行わない |
| confidenceの扱い | 個人記録として扱い、他ユーザー向けFactの信頼度計算には算入しない |
| 禁止事項 | 無断で他ユーザー向けFactにすること、単独ReflectionをExperience Knowledgeへ直接昇格すること |

### AI Generated Draft

| 項目 | 内容 |
|---|---|
| 定義 | AIが生成した要約案・正規化候補・調査候補等の下書き |
| 例 | 要約案、正規化候補、表記揺れ候補、調査候補、説明文Draft |
| 保存可否 | 可（Draftとして。verified Factとしては不可） |
| 表示可否 | 不可（確認前は非公開。レビュー後に他分類へ昇格して初めて表示対象） |
| Recommendation利用可否 | 不可 |
| 必要なSource | 不要（Draft自体はSourceの代替ではない） |
| 必要なverification | 昇格には人手レビューが必須 |
| confidenceの扱い | 常に最低水準として扱う |
| 禁止事項 | Sourceの代替として使うこと、公開前に確認工程を経ずに表示すること、不明値を埋める目的で利用すること |

---

## Evidence Gate要件（将来実装。今回は未実装）

Evidence Gateは、根拠不足の状態でFactが断定的に生成されることを防ぐための実行時チェックである。`docs/core/recommendation-architecture.md` Section 12の要件を、`deity`/`shrine_history`/Experience単位まで具体化する。

### deity

- `deity`が未登録（`not_collected`）なら祭神由来Factを生成しない
- `deity`が`unverified`なら断定表示しない
- `source_reference`がないなら`deity`をFactとして利用しない
- `AI Generated Draft`のみなら`deity`をFact利用しない
- `verification_status: disputed`の場合、複数説を併記するか非表示にする（単一の説を勝手に選ばない）

### shrine_history

- `shrine_history`が未登録なら歴史由来Factを生成しない
- 伝承（`tradition`）を確定史実として扱わない
- `source_reference`がないなら断定しない
- `Editorial Summary`のみの場合、要約元Sourceの確認状態を参照する（要約自体の存在をもってFact利用可能とはしない）
- `AI Generated Draft`のみなら`shrine_history`をFact利用しない

### Experience

- `Experience Knowledge`が存在しなければ雰囲気を断定しない
- 1件の観察から「いつも静か」等の一般化を行わない（最低観察件数は今回確定せず、後続PRで定める）
- 観察日が古い場合は鮮度低下を考慮する
- 混雑・アクセス状況等の変動情報は、恒常的な特徴として扱わない

### fallback

`goriyaku_tags`と`history_theme`へのfallbackを、全面的にFactの代替として使わない。以下を区別する。

| 区分 | 扱い |
|---|---|
| Fact fallback | 原則禁止。`deity`/`shrine_history`が空の場合、それらをFactとして生成しない |
| Interpretation fallback | 条件付きで可能。「登録されているテーマ上、今回の相談と接点がある候補として選ばれています」のように、Interpretationであることが読み手に伝わる表現に限る |
| Action fallback | 神社固有のEvidenceがない場合、弱い一般提案（時間帯・混雑回避等の一般的な参拝マナー水準）に限定する |

禁止例: 「この神社は決断を後押しする歴史を持っています」（`shrine_history`が存在しないにもかかわらず史実であるかのように断定している）

許容候補の例: 「登録されているテーマ上、今回の相談と接点がある候補として選ばれています」（Interpretationであることが明確）

fallbackを利用した場合、それがFactではなくInterpretationであることを内部的に識別できる設計要件（例: `source: "fallback_interpretation"`のようなAudit用フィールドの保持）を将来のEvidence Gate実装で満たす。今回はこの要件を記載するのみで実装しない。

### confidence不足

| confidence水準 | 扱い |
|---|---|
| 高 | Fact表示可能 |
| 中 | 限定表現（断定を避けた表現）に限る |
| 低 | 非表示、またはInterpretation限定 |
| `disputed` | 断定禁止（多説併記または非表示） |
| `unknown` | 利用禁止 |

数値閾値は今回確定しない。後続PR（Evidence Gate実装PR）で定める。

> **追記（PR-C1、2026-08-02時点）**: 上表は`confidence`（高/中/低）と`verification_status`の値（`disputed`）・Modelに存在しない値（`unknown`）を同一の「confidence水準」列に混在させており、2軸を分離できていなかった。実装済みのEvidence Gate PR-A/PR-Bを踏まえ、以下のとおり明確に分離する。
>
> **verification_status軸**（Fact利用可否の土台。`draft`/`unverified`/`source_confirmed`/`reviewed`/`disputed`/`outdated`/`rejected`）: `disputed`はここに属する値であり、confidenceの値ではない。`disputed`の場合の非表示/多説併記の方針はPR-A実装後も未確定のまま（「disputedの表示方針との分離」節、母艦判断項目を参照）。
>
> **confidence軸**（表現強度。PR-Bで実装済み）: `high`/`medium`/`low`/未設定（空文字）の4状態のみ。`unknown`という値はModel（`KNOWLEDGE_CONFIDENCE_CHOICES`）に存在しない。実装済みの対応関係は以下のとおり。
>
> | confidence（Fact自身） | Recommendation Reason表現強度 |
> |---|---|
> | high | assertive（現行文言のまま） |
> | medium | weakened（限定表現） |
> | low | suppressed（Knowledge FactをReasonへ使用しない。Fact自体はDB・Detail API・Knowledge selectorからは消えない） |
> | 未設定（空文字） | legacy-compatible（現行互換の通常表現。highへの読み替えではない） |
>
> 複数DeityのconfidenceがReason文へ連結される際に一致しない場合は、上記いずれの値も安全に採用できないため、内部専用sentinelとして`suppressed`相当に倒す（コード実装の詳細はPR-B follow-up、PR #2229を参照）。

### Fact・Interpretation・Actionとの整合

`docs/core/recommendation-architecture.md` Section 10の定義と矛盾しないよう、以下を確認・踏襲する。

- Fact: Sourceで確認可能な情報のみ
- Interpretation: Factと相談内容の接点（Factそのものの断定ではない）
- Action: 参拝時の任意提案（神社固有の御利益保証ではない）

以下を禁止する。

- InterpretationをFactの文体（断定調）で表示すること
- Actionを神社固有の御利益として保証すること
- `history_theme`（Meaning Layerの解釈情報）だけで神社固有のActionを生成すること
- Evidenceが欠けている部分をLLMの生成で穴埋めすること
- 根拠不足の状態でも文量を維持する目的でfallbackを多用すること

---

## Model選択肢比較

最終Modelは今回決定しない。以下5案を比較する（本書作成時点＝As-Is。**2026-08-01時点の解決状況は本節末尾の注記を参照**）。

### 案1：現行Field継続（`Shrine.sajin` / `Shrine.description`）

| 評価項目 | 評価 |
|---|---|
| 実装速度 | 最速。Migration不要 |
| 既存互換性 | 最も高い |
| 複数祭神対応 | 不可（単一TextField） |
| Source保持 | 不可 |
| verification保持 | 不可 |
| confidence保持 | 不可 |
| 由緒と紹介文の責務分離 | 不可（現状混在。As-Isで確認済み） |
| Recommendation利用時の安全性 | 低い（出典なしFactを断定表示するリスクが構造的に残る） |
| 105件展開時の保守性 | 低い（複数祭神・伝承と史実の区別ができないため、入力担当が非構造化テキストへ全てを詰め込むことになりやすい） |

### 案2：新Field追加

例（構造案。Field名は確定しない）: `deity_text`, `shrine_history_text`, `deity_source`, `history_source`, `verification_status`等。

| 評価項目 | 評価 |
|---|---|
| 実装速度 | 速い（既存Model拡張のみ） |
| 既存互換性 | 高い |
| 複数祭神対応 | 弱い（単一Fieldへカンマ区切り等で押し込むと構造化されない。真に複数保持するには別途配列/JSON的な工夫が必要） |
| Source保持 | 可能（新Field追加で） |
| verification保持 | 可能 |
| confidence保持 | 可能 |
| 由緒と紹介文の責務分離 | 部分的に可能（Field名を分ければ責務は分離できるが、案1同様の構造的柔軟性の欠如は残る） |
| Recommendation利用時の安全性 | 中（出典の有無で表示制御可能になる） |
| 105件展開時の保守性 | 中（Field数が増えるたびにMigrationが必要） |

### 案3：JSONField

| 評価項目 | 評価 |
|---|---|
| 柔軟性 | 高い（複数祭神・Source構造を1Fieldで柔軟に表現可能） |
| Validation | 弱い（型安全性がなく、アプリ側での厳密なValidationが必要） |
| Query性能 | 弱い（JSON内部の条件検索はRDBMSのINDEX最適化が効きにくい） |
| Admin編集 | 弱い（標準Adminでは生JSON編集になりやすく誤入力リスクが高い） |
| Serializer | 中（構造のバリデーションをSerializer側で担う必要がある） |
| Migration | 少ない（Field追加は1回で済むが、内部構造変更はコード側の対応が必要） |
| 型安全性 | 弱い |
| 将来変更 | 柔軟（構造変更にMigration不要） |
| Sourceとの関係 | 1Field内にSourceを埋め込む形になり、Source単体の再利用・複数Fact間の共有がしづらい |

### 案4：別Model（例: `ShrineKnowledge`、名称は確定しない）

`deity`・`shrine_history`をそれぞれ独立したレコードとして持つModel。

| 評価項目 | 評価 |
|---|---|
| 長所 | Fact項目ごとに出典・confidence・verified_at・生成元を柔軟に保持できる。複数祭神を複数レコードとして自然に表現できる |
| 短所 | Modelが増え、JOINまたは別クエリが必要。既存Serializerの再設計が必要 |
| Migration影響 | 大（新規Model・Migration） |
| Serializer影響 | 大（新規Serializer、既存Shrine Serializerとの統合設計） |
| Admin影響 | 新規Admin画面が必要（Inline編集等の検討要） |
| API影響 | 中〜大（Shrine詳細APIのレスポンス構造変更を伴う可能性） |
| Recommendation利用時の安全性 | 高い（出典・confidenceを構造的に強制できる） |
| Pilot適合性 | 高い（3〜5社規模の検証に十分な柔軟性を持つ） |
| 105件展開適合性 | 高い（複数祭神・史実伝承分離を含む105件へも自然に拡張できる） |
| 将来拡張性 | 高い |

### 案5：Relation Model（例: `Shrine` / `KnowledgeEntry` / `Source` / `KnowledgeSource`、名称は確定しない）

`KnowledgeEntry`（deity/shrine_history等の値本体）と`Source`（出典）を多対多で関連付け、複数Sourceの共有・再利用を可能にする正規化構成。

| 評価項目 | 評価 |
|---|---|
| 長所 | 出典の再利用・複数Fact項目への紐付けが可能。データ品質管理がしやすい。多説併記・矛盾情報の保持に最も適する |
| 短所 | 設計・実装コストが最大。既存データ移行が最も複雑 |
| Migration影響 | 大（複数新規Model・Migration） |
| Serializer影響 | 大 |
| Admin影響 | 新規Admin画面が必要（Inline・多対多編集UIの検討要） |
| API影響 | 大（正規化構造をAPIとしてどこまで公開するか設計が必要） |
| Recommendation利用時の安全性 | 最高（出典の一意性・再利用性を構造的に保証できる） |
| Pilot適合性 | 中（3〜5社の検証には過剰投資になり得る） |
| 105件展開適合性 | 高い（長期的な品質管理には最も適する） |
| 将来拡張性 | 最高（Experience Knowledgeの多数観察・User Reflectionの集約等、将来の拡張を正規化構造で自然に扱える） |

### 結論

| 区分 | 候補 |
|---|---|
| MVP向け候補 | 案4（別Model）。Pilot 3〜5社の検証規模に対して、出典・confidence・複数祭神を安全に扱うために必要十分な複雑度である |
| 中期向け候補 | 案5（Relation Model）。105件展開時、または将来のExperience Knowledge集約・多説併記の本格運用が必要になった時点で移行を検討する |
| 非推奨候補 | 案1（現行Field継続）。Blocker #1の解消（出典なしFactの断定表示防止）という目的に対して構造的に不十分 |
| 母艦判断事項 | 案2・案3は状況次第で暫定案として採用され得るが、Codex側では最終採用を決定しない |

**設計上の推奨方向性（決定ではない）**: 短期的には案4（別Model）でPilot検証を行い、105件展開時に案5（Relation Model）への移行要否を判断する2段階アプローチが、Migration影響とRecommendation安全性のバランスとして検討に値する。ただし最終選択は母艦判断とする。

> **注記（2026-08-01時点）**: 母艦判断により案4（別Model）が採用され、`ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource`として`feature/shrine-knowledge-model-foundation`（PR #2221）で実装・`develop`へマージ済み。案5（Relation Model）への移行要否は、上記のとおり105件展開時またはExperience Knowledge本格運用時に改めて判断する未確定事項のままである。

---

## Pilot設計

Pilotデータ投入は今回行わない。次のData PR（PR3）で利用する条件を定義する。

> **注記（2026-08-01時点）**: 明治神宮1社を対象に、Django Admin経由でのReal Data Pilot #1を実施済み（詳細・結果は`docs/audit/shrine-knowledge-real-data-pilot-1.md`）。ただしこれは本節が想定する3〜5社規模のPilot本体（PR3）そのものではなく、Model Foundationが実データで成立するかを検証する先行確認と位置づける。件数・選定条件を満たす3〜5社規模のPilot本体、およびEvidence Gate（PR2）との接続検証は未実施のままである。

### 件数

3〜5社

### 選定条件

- 公式サイトまたは信頼できる一次情報がある
- 由緒が確認できる
- 複数祭神のケースを含む
- 公式情報量が多い神社を含む
- 情報量が少ない神社を含む
- 現地参拝済み神社を最低1件含む
- 現行Recommendation候補に登場する神社を含む
- 欠損または曖昧情報のケースを最低1件含む

### 候補（提示のみ。最終選定は母艦判断へ差し戻す）

DB確認（読み取りのみ）の結果、以下を候補として提示する。選定理由は実データ（`goriyaku_tags`件数、`history_theme`設定有無、`ShrineReflection`件数）に基づく。

| 候補神社 | 選定理由 |
|---|---|
| 伊勢神宮（内宮）（id=3） | 単一主祭神（天照大御神）の明確なケース。公式サイト・学術資料・文化財資料が極めて豊富で「情報量が多い神社」の代表例 |
| 出雲大社（id=4） | 単一主祭神（大国主大神）だが縁結びの伝承が豊富。公式サイトが充実し、「情報量が多い神社」の候補として伊勢神宮と異なる由緒パターンを提供 |
| 三峯神社（id=17） | 二柱祭神（伊弉諾尊・伊弉冉尊）を祀り「複数祭神のケース」に該当。`ShrineReflection`が実際に4件存在し、「現地参拝済み神社」の条件を実データで満たす |
| 神田神社（神田明神）（id=23） | 三柱祭神（大己貴命・少彦名命・平将門命）を祀り「複数祭神のケース」の別パターン。平将門に関する伝承は史実と伝承の分離が特に試される好例 |
| 長太稲荷神社（id=21）または給田六所神社（id=22） | 東京都世田谷区の地域神社。全国的な公式情報・学術資料が乏しいと想定され、「情報量が少ない神社」「欠損または曖昧情報のケース」の候補として機能する |

いずれも`history_theme`が設定済み（テストフィクスチャではない）であり、`goriyaku_tags`を保持するため、現行のCandidate Retrieval/Eligibility Filterを通過し「現行Recommendation候補に登場する神社」の条件を満たすと確認できる。

**確認済みの注意事項**: DB上の`id=101〜105`（「承認テスト神社」「重複検証神社」等）は明らかなテストフィクスチャであり、Pilot候補から除外する。

具体的な最終候補（上記5件からの絞り込み、または追加候補の検討）は母艦判断へ差し戻す。

### Pilot完了条件

以下を最低限満たす。

1. `deity`を登録できる
2. 複数祭神を扱える
3. `shrine_history`を登録できる
4. 伝承と史実を区別できる
5. Sourceを保持できる
6. `accessed_at`を保持できる
7. `verified_at`を保持できる
8. `verification_status`を保持できる
9. `confidence`を保持できる
10. AI Draftと確認済み値を区別できる
11. Evidence Gateが利用可否を判定できる
12. Detail表示へ安全に返却できる
13. Recommendation Reasonへ利用できる
14. 欠損時にFactが抑制される
15. fallbackがInterpretationとして扱われる
16. 回帰テストの対象を定義できる

> **注記（2026-08-01時点）**: Real Data Pilot #1（明治神宮）では上記のうち1〜3・5・7・8・9（`deity`登録・複数祭神・`shrine_history`登録・Source保持・`verified_at`保持・`verification_status`保持・`confidence`保持）を確認した。4（伝承と史実の区別）・6（`accessed_at`）・10（AI Draftとの区別）・11〜16（Evidence Gate／Detail表示／Recommendation Reason利用／欠損時抑制／fallback／回帰テスト対象）は本Pilot #1の対象外、または未検証のまま残っている。詳細は`docs/audit/shrine-knowledge-real-data-pilot-1.md`の「未検証事項」を参照。

---

## 後続PR設計

### PR1：Knowledge Model Foundation

- **目的**: 本書の設計（Model選択肢比較の結論を受けた採用案）に基づき、Knowledge保存の実装基盤を構築する
- **ブランチ候補**: `feature/shrine-knowledge-model-foundation`
- **変更範囲**: Model、Migration、Serializer、Admin、Validation、API契約、Tests
- **対象外**: Evidence Gateのロジック実装（PR2）、Pilot実データ投入（PR3）
- **依存PR**: 本書（PR2219系列のフォローアップ、母艦判断でModel選択確定後）
- **テスト**: Model単体テスト、Serializer契約テスト、Admin編集テスト、既存Shrine関連APIの回帰テスト
- **完了条件**: 採用Model構造が実装される。Source・verification・confidenceを保持できる。既存データとの互換方針がある。API contract testsがある。Adminまたは安全な投入経路がある
- **母艦判断項目**: Model選択の最終確定（本書「Model選択肢比較」の結論を受けて）
- **状況（2026-08-01時点）**: 実装済み。`feature/shrine-knowledge-model-foundation`（PR #2221）として`develop`へマージ済み。母艦判断でModel選択は案4（別Model）に確定した

### PR2：Recommendation Evidence Gate

- **目的**: 本書のEvidence Gate要件を実装し、根拠不足のFactが生成されないようにする
- **ブランチ候補**: `feature/recommendation-evidence-gate`
- **変更範囲**: Evidence Assembly、Fact利用判定、fallback抑制、confidence対応、Fact・Interpretation・Action分離、Tests
- **対象外**: Knowledge Model自体の変更（PR1に依存）、Score軸（`data_confidence_score`等）本体の実装
- **依存PR**: PR1（Knowledge Modelが実装済みであること）
- **テスト**: `deity`/`shrine_history`欠損時のFact抑制テスト、`disputed`時の非表示/多説併記テスト、confidence閾値ごとの表現切り替えテスト、fallbackのInterpretation識別テスト
- **完了条件**: 根拠なしFactが生成されない。`deity`欠損時に祭神Factが抑制される。`shrine_history`欠損時に歴史Factが抑制される。fallbackがFactとして出力されない。回帰テストがある
- **母艦判断項目**: confidence数値閾値の確定、`disputed`時の表示方針（非表示か多説併記か）
- **状況（2026-08-02時点）**: 本PR2で計画していた範囲のうち、Fact利用可否判定はPR-A（`feature/evidence-gate-pr-a-foundation`、PR #2227）として、Fact confidenceによるRecommendation Reason表現強度制御はPR-B（PR #2228・follow-up #2229）として、それぞれ実装・`develop`へマージ済みである。ただし数値閾値は導入していない（categorical値high/medium/lowをそのまま表現強度へ対応させている）。`disputed`時の表示方針（非表示か多説併記か）は依然未確定のまま、別PR（PR-C4候補、「Source Confidence Contract」節の「disputedの表示方針との分離」を参照）へ切り出されている。Source自身のconfidence（`ShrineKnowledgeSource.confidence`）・複数Source集約・Conflicting Evidenceの契約整理はPR-C1（本節「Source Confidence Contract」）で行い、実装は含まない

### PR3：Pilot Data

- **目的**: 本書のPilot設計に基づき、3〜5社の実データを投入し、Model・Evidence Gateの実運用を検証する
- **ブランチ候補**: `data/shrine-knowledge-pilot`
- **変更範囲**: Pilot対象3〜5社のKnowledgeデータ、Source、verification、confidence、QA記録、Data投入手順
- **対象外**: 105件全体への展開（PR4）
- **依存PR**: PR1（Model）、PR2（Evidence Gate）
- **テスト**: Pilot対象神社ごとのDetail表示確認、Recommendation Reason確認、欠損ケース確認
- **完了条件**: Pilot対象全社が本書の完了条件（16項目）を満たす。Sourceが追跡可能。Detail表示確認済み。Recommendation Reason確認済み。欠損ケース確認済み
- **母艦判断項目**: Pilot対象神社の最終選定（本書「候補」からの絞り込みまたは追加検討）
- **状況（2026-08-01時点）**: 本PR3（3〜5社規模）そのものは未実施。先行検証として明治神宮1社によるReal Data Pilot #1をAdmin経由で実施済み（`docs/audit/shrine-knowledge-real-data-pilot-1.md`）。明治神宮は本書「候補」5件（伊勢神宮・出雲大社・三峯神社・神田神社・長太稲荷神社／給田六所神社）には含まれておらず、母艦判断により候補外から選定された。3〜5社規模の本体実施およびPilot #2条件は同audit文書の「Foundation残り5%完了条件」「Pilot #2条件」を参照

### PR4：105件Rollout Plan

- **目的**: Pilotの結果を踏まえ、105件（テストフィクスチャを除く実神社）へKnowledgeを段階投入する計画を文書化する
- **ブランチ候補**: `docs/shrine-knowledge-rollout-plan`
- **変更範囲**: 出典優先順位の運用細則、収集手順、Review手順、1件ごとの完了条件、品質指標、進捗管理、誤り修正フロー
- **対象外**: 実データそのものの投入（別途データPRで段階的に実施）
- **依存PR**: PR3（Pilotの検証結果）
- **テスト**: 本PRはDocsのみのため、品質指標の追跡可能性（進捗ダッシュボード等）の要否を検討する
- **完了条件**: 105件を段階投入できる計画になっている。一括AI生成を前提にしない。Review担当と手順が明確。CoverageとEvidence品質を追跡できる
- **母艦判断項目**: 105件展開時のReview担当（誰が確認工程を担うか）

---

## 母艦判断項目

以下は本書の設計検討過程で判断が必要と確認されたが、本書では決定しない。

1. Knowledge Contractを新規文書にするか、`shrine-profile-spec.md`へ統合するか（本書は案Bを採用したが、最終的な採否は母艦判断とする）
2. `Shrine.sajin`を継続利用するか（Model選択肢比較の結論を受けて）
3. `Shrine.description`を継続利用するか
4. `deity`を文字列、JSON、別Model、Relationのどれで保持するか
5. `shrine_history`を単一Field、複数Field、別Modelのどれで保持するか
6. Sourceを別Model化するか
7. SourceとKnowledgeを多対多にするか
8. `verification_status`の最終enum候補
9. `confidence`の保存方式
10. `confidence`の算出方式
11. `AI Generated Draft`をDBへ保存可能にするか
12. `disputed`情報の表示方針
13. fallbackをどこまで許可するか（Interpretation限定の範囲の最終確定）
14. 根拠不足候補を除外するか順位を下げるか
15. Pilot対象神社（本書は5候補を提示。最終選定は母艦判断）
16. 105件展開時のReview担当
17. User Reflectionを将来Experience Knowledgeへ還元するか

Codex側では最終決定を行わない。

> **注記（2026-08-01時点）**: 母艦判断により、4〜9はPR #2221（`feature/shrine-knowledge-model-foundation`）で以下のとおり確定・実装済みである。`deity`＝別Model（`ShrineDeity`）、`shrine_history`＝別Model（`ShrineHistory`）、Source＝別Model（`ShrineKnowledgeSource`）として別Model化し、SourceとKnowledge（Deity/History）はManyToManyで関連付けられている。`verification_status`のenum（draft/unverified/source_confirmed/reviewed/disputed/outdated/rejected）、`confidence`の保存方式（low/medium/highのCharField choices）も同PRで確定した（8・9）。一方、2（`Shrine.sajin`継続利用）・3（`Shrine.description`継続利用）はいずれも変更されておらず未確定のまま維持されている。15（Pilot対象神社）は、明治神宮1社に限りReal Data Pilot #1として母艦判断で選定・実施済み（本書「候補」5件には含まれない神社が選ばれた）だが、3〜5社規模のPilot対象確定はなお母艦判断待ちである。1・10〜14・16・17は本書作成時点から変わらず未確定のままである。
>
> **追記（2026-08-02時点、PR-C1）**: 10（`confidence`の算出方式）のうち、**Fact confidence**の算出方式は「人手入力（Admin編集）」で運用されており、Recommendation Reasonへの接続（high/medium/low/未設定→assertive/weakened/suppressed/legacy-compatible）はPR-Bで確定・実装済みである。一方、**Source confidence**の算出方式・複数Source間の集約方式（min/max/average/majority/highest-priority-source/official-source-override等）は今回も未確定のまま据え置く（PR-C1はいずれも新規採用しない）。12（`disputed`情報の表示方針）は本書作成時点から変わらず未確定であり、別PR（PR-C4候補）へ切り出す。加えて、本追記で新たに以下を母艦判断項目へ追加する。
>
> **18.** Source confidenceを将来利用するか、利用する場合はEvidence usable判定・Reason strength・Score/Rankingのいずれへ接続するか
>
> **19.** 複数Source confidenceの集約方式（min/max/average/majority/highest-priority-source/official-source-override等）をどれか一つに確定するか
>
> **20.** Conflicting Evidence（Source間の明示的な否定、Case 9相当）へ対応する必要があるか。対応する場合、`FactSourceEvidence`（仮称）等の中間Model拡張（Migration）を実施するか

---

## 関連ドキュメント

- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/README.md`
- `docs/core/recommendation-architecture.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/recommendation-readiness.md`
- `docs/audit/concierge-end-to-end-consistency-audit.md`
- `docs/audit/reason-facts-coverage.md`
