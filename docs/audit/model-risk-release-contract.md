# Model Risk Release Contract Audit

> Status: `MODEL_RISK_RELEASE_CONTRACT_READY`
>
> 本書は、これまで MODEL / PRODUCT HOLD とされていた9社について、
> HOLD解除条件を固定するためのGovernance / Audit Contractである。
>
> Production write: **NO**  
> Seed change: **NO**  
> Recommendation change: **NO**  
> Model / Migration change: **NO**

---

## 0. Audit Base

| 項目 | 値 |
|---|---|
| Repository | `etsu33/jinja_app` |
| Base branch | `develop` |
| Audit branch | `audit/model-risk-release-contract` |
| BASE_SHA | `963bd7f318b0b6963b1f5dc9cf420ca74c676bf8` |
| 監査開始時のBASE_SHAとdevelop | identical |
| 参照する現行Production denominator | Shrine 113 rows |
| 対象となるMODEL / PRODUCT HOLD | 9社 |

対象9社:

- 靖國神社
- 千葉神社
- 愛宕神社
- 赤城神社
- 千住神社
- 冠稲荷神社
- 古峯神社
- 高千穂神社
- 榛名神社

本監査では、実装順・Production write順・事業優先順位は決定しない。

---

## 1. Purpose

本監査が答える問いは1つである。

> 現在MODEL / PRODUCT HOLDとなっている9社について、どの明示条件を満たせばHOLDを解除し、通常のKnowledge作成フローへ戻せるか。

本監査では次を明確に分離する。

```text
HOLD解除
!= Seed承認
!= Production write承認
```

HOLD解除とは、その神社を通常のKnowledge作成工程へ戻してよい状態になったことだけを意味する。

解除後も通常フローは維持する。

```text
HOLD解除
-> Fact research / Fact Sheet
-> Seed Preflight
-> Human Approval
-> Production write
```

本書だけでは、いずれの神社についてもProduction writeを承認しない。

---

## 2. Non-goals

本監査では以下を行わない。

- Production dataの書き換え
- Knowledge Seedの作成・変更
- Recommendation eligibility / rankingの変更
- `ShrineDeity` / `ShrineHistory` schema変更
- Migration作成
- 祭神identityの創作
- 不明な祭神名の推測補完
- 未解決な宗教的relationを断定的Deity Factへ平坦化
- Mother Shipに代わるProduct Scope判断

---

## 3. 現行Knowledge Modelの表現境界

### 3.1 ShrineDeity

現行`ShrineDeity`が安全に表現できる単位は次である。

```text
1つの個別帰属可能な名指し祭神
+
role
+
Source relation
+
verification_status
+
confidence
```

複数祭神は1対多の複数rowで保持できる。

Sourceに序列がない場合は`role: unknown`を用い、主祭神を推測しない。

現行`ShrineDeity`は、次の構造を直接表現しない。

- 匿名・未確定の集合祭神
- 「ほか8柱」「ほか15柱以上」のようなopen-ended group
- 祭神一覧のcomplete / partial
- 集合祭神の人数
- 集合名と個別構成員の親子関係
- 神格と仏教尊格のidentity relation
- 神格と権現・本地仏のsemantic relation
- 本社 / 摂社 / 末社のhierarchy
- Associated Worship Targetの分類

### 3.2 ShrineHistory

現行`ShrineHistory`は次を保持できる。

- `official_origin`
- `founding`
- `historical_event`
- `tradition`
- `regional_context`
- `editorial_summary`
- `period_text`
- `event_date`
- Source relation
- verification status
- confidence

Sourceが裏付ける限り、歴史的神仏習合、旧称、仏教組織との関係、神仏分離、遷座、合祀、伝承などを保持できる。

ただし`ShrineHistory`は、未解決の現在祭神identityを逃がすための代替領域ではない。

### 3.3 Runtime EligibilityとModel Risk解除を分離する

現行Runtime Eligibilityは次である。

```text
usable Deity >= 1
OR
usable History >= 1
```

このOR条件をModel Risk回避に使用してはならない。

例:

```text
現在祭神構造 = 未解決
+
usable History = 1件
=
Runtime Eligibilityは成立し得る
しかし
MODEL RISKは未解決
```

したがって以下を固定する。

> Runtime Recommendation Eligibilityの成立と、Model Risk HOLDの解除は別Gateである。

---

## 4. Risk Taxonomy

### 4.1 Collective Deity

`COLLECTIVE_DEITY_MODEL_GAP`は、現在の本社祭神情報に匿名・未確定の集合が含まれ、有限個の名指し`ShrineDeity` rowだけでは意味を保ったまま再現できない状態を指す。

例:

```text
A神
B神
ほか8柱
```

または:

```text
ほか15柱以上
```

単に祭神数が多いことは問題ではない。

20柱すべてが個別名・Source付きで確認できるなら、20 rowで表現できる。

禁止するfallback:

- `UNKNOWN_MEMBER_1`等の架空祭神
- 「ほか8柱」を祭神名として保存
- 未確認祭神名の創作
- Sourceが部分一覧しか示していないのに、登録済み祭神を完全一覧として扱うこと

### 4.2 Shinbutsu-shugo

歴史上の神仏習合が存在すること自体はModel Change条件ではない。

Source上で次を分離できる場合、

```text
現在の本社祭神
と
歴史的な仏教尊格 / 権現 / 修験道文脈
```

以下の分担で表現できる。

```text
現在祭神 -> ShrineDeity
歴史的文脈 -> ShrineHistory
```

`SHINBUTSU_SHUGO_MODEL_GAP`は、現在の主祭神identity自体が、重要な神仏習合relationを潰さずには表現できない場合に限る。

### 4.3 Associated Worship Target

Associated Worship Targetとは、神社の境内・信仰実践・公式案内上で祀られている／信仰対象となっていても、現在の本社祭神とは自動的に同一視しない対象を指す。

例:

- 七福神
- 富士塚
- 付随する仏教系信仰対象
- 本社とは別の儀礼文脈に属する特別な信仰対象

「同じ公式ページに掲載されている」ことは、「親Shrineの`ShrineDeity`に入る」根拠にならない。

本社祭神集合が独立して確認できる場合、この問題は原則curationで処理できる。

### 4.4 Main Shrine / Sub-shrine

`Shrine` rowへ保持するKnowledgeは、そのrowが表す神社entityへ直接帰属するFactに限定する。

次は、同じ境内・同じ公式サイトに存在するという理由だけでは親神社へ昇格させない。

- 摂社
- 末社
- 境内社
- 別宮
- 奥宮
- 旧社・合祀吸収元

```text
Source page owner
!=
Fact owner
```

合祀された歴史は`ShrineHistory`へ保持できるが、旧社の祭神を現在の親神社`ShrineDeity`へ入れるのは、accepted Sourceが現在の本社祭神として明示する場合に限る。

---

## 5. Release Classification Rules

### 5.1 CURATION_RELEASE_CANDIDATE

既存Schemaのまま、子社・付随対象などを明示的に分離することで、登録予定の現在本社Knowledgeを意味損失なく表現できる場合に使用する。

必要条件:

1. accepted Sourceで現在の本社祭神集合を確認できる
2. Sub-shrine / Associated Targetを分離できる
3. 分離によりSourceの意味を歪めない
4. anonymous collectiveが残らない
5. 現在祭神identityの未解決relationが残らない
6. 除外境界をFact Sheet / Seed Preflightへ記録する

### 5.2 RESEARCH_REQUIRED_BEFORE_RELEASE

現行Modelで表現可能な可能性は高いが、accepted Sourceだけでは現在本社の帰属境界をまだ確定できない場合に使用する。

これは`MODEL_CHANGE_REQUIRED`とは異なる。

### 5.3 MODEL_REVIEW_REMAINS

Repository上はModel Riskが確認されているが、curationで解消可能なのか、Schema / Contract拡張が必要なのかをまだ判定できない場合に使用する。

次工程は即Model変更ではなく、Source / identity境界のfocused reviewである。

### 5.4 MODEL_CHANGE_REQUIRED

Source-backedな現在Knowledgeを、現行`ShrineDeity / ShrineHistory` Contractでは意味損失なしに表現できない場合だけ使用する。

対象例:

- 匿名・未確定の集合祭神
- 現在主祭神identityが重要な神仏習合relationから分離不能
- 一部祭神だけ登録すると現在祭神構造を重大に誤認させるケース

### 5.5 PRODUCT_DECISION_REQUIRED

技術的なModel表現可否とは独立して、Repository Governance上、製品scope / 編集方針判断が必要とされている場合に使用する。

Modelが表現可能になっただけではProduct HOLDを自動解除しない。

---

## 6. 9社の現在分類

| 神社 | 現在分類 | 意味 |
|---|---|---|
| 千住神社 | `CURATION_RELEASE_CANDIDATE` | Associated Targetを正しく除外できれば現行Modelで処理可能 |
| 榛名神社 | `RESEARCH_REQUIRED_BEFORE_RELEASE` | 現在祭神集合と歴史・境内社境界のSource再確認が必要 |
| 古峯神社 | `RESEARCH_REQUIRED_BEFORE_RELEASE` | 現在本社祭神と修験道・神仏習合史の分離確認が必要 |
| 愛宕神社 | `MODEL_REVIEW_REMAINS` | 仏教称号と現在祭神構造のidentity境界確認が必要 |
| 赤城神社 | `MODEL_REVIEW_REMAINS` | 神仏習合要素と現在主祭神identityの境界確認が必要 |
| 高千穂神社 | `MODEL_CHANGE_REQUIRED` | 「ほか8柱」を現行1 row = 1 named deityで表現不可 |
| 冠稲荷神社 | `MODEL_CHANGE_REQUIRED` | 「ほか15柱以上」がCollective Deity gapとして残る |
| 千葉神社 | `MODEL_CHANGE_REQUIRED` | Repository上、主祭神identity自体が未解決な神仏習合ケース |
| 靖國神社 | `PRODUCT_DECISION_REQUIRED` | Repository Governance上、通常のschema-only問題とは別のProduct Policy Gate |

---

## 7. 神社別HOLD解除条件

### 7.1 千住神社

現在分類:

```text
CURATION_RELEASE_CANDIDATE
```

解除条件:

1. accepted Sourceで現在の本社祭神集合をfresh再確認する
2. 須佐之男命・宇迦之御魂命が本社へ帰属することを維持確認する
3. 七福神 / 恵比寿関連・富士塚関連を親`ShrineDeity`から明示的に除外する
4. 除外境界をFact Sheet / Seed Preflightへ記録する
5. fresh reviewで新しいcollective / subordinate-shrine問題が発生しない

全条件PASS:

```text
MODEL HOLD RELEASE
-> 通常Fact / Seed workflow
```

未達:

```text
CURATION_HOLD
```

を維持する。

### 7.2 榛名神社

現在分類:

```text
RESEARCH_REQUIRED_BEFORE_RELEASE
```

解除条件:

1. accepted Sourceで現在の本社祭神集合を確定する
2. Repository上の「主要6柱」「満行権現から現行二神への改称」等の記録を、推測せず整合させる
3. 境内社・関連祭神を本社祭神から分離する
4. 満行権現、歴史的仏教組織、神仏分離への移行を`ShrineHistory`で表現できる
5. 現在祭神identityを通常の名指し`ShrineDeity` rowで意味損失なく表現できる

全条件PASS:

```text
CURATION_RELEASE
```

現在祭神identityが現行Modelで表現不能:

```text
MODEL_CHANGE_REQUIRED
```

それ以外:

```text
RESEARCH_REQUIRED_BEFORE_RELEASE
```

を維持する。

### 7.3 古峯神社

現在分類:

```text
RESEARCH_REQUIRED_BEFORE_RELEASE
```

解除条件:

1. accepted Sourceで現在の本社祭神集合を直接確認する
2. 現在祭神identityと歴史的な修験道・神仏習合文脈を分離できる
3. 歴史的文脈を`ShrineHistory`で保持できる
4. Associated Target / Sub-shrineを本社祭神へ混入させない
5. unresolved collective / identity relationが残らない

全条件PASS:

```text
CURATION_RELEASE
```

現在主祭神identity自体が現行Contractで表現不能:

```text
MODEL_CHANGE_REQUIRED
```

### 7.4 愛宕神社

現在分類:

```text
MODEL_REVIEW_REMAINS
```

解除条件:

1. accepted Sourceで現在の本社祭神集合を確定する
2. 将軍地蔵尊・普賢大菩薩等の仏教称号と現在本社祭神集合とのrelationをSourceから確定する
3. 現行Schemaへ合わせるためだけに仏教称号を黙って捨てない
4. 歴史・付随対象として分離可能ならcurationで処理する
5. 現在祭神構造自体が現行Modelで表現できない場合は`MODEL_CHANGE_REQUIRED`へ移す

判定:

```text
Source上で分離可能
-> CURATION_RELEASE

Source上でも現在祭神identityが分離不能
-> MODEL_CHANGE_REQUIRED

未解決
-> MODEL_REVIEW_REMAINS
```

### 7.5 赤城神社

現在分類:

```text
MODEL_REVIEW_REMAINS
```

解除条件:

1. accepted Sourceで現在の本社祭神集合を確定する
2. 本地仏・千手観音等の要素を、現在祭神identityか歴史的神仏習合文脈かで判定する
3. Sourceが裏付ける場合に限り、歴史的要素を`ShrineHistory`へ分離する
4. 未確認のdeity relationを推論しない

判定:

```text
Source上で分離可能
-> CURATION_RELEASE

現在主祭神identityが分離不能
-> MODEL_CHANGE_REQUIRED

未解決
-> MODEL_REVIEW_REMAINS
```

### 7.6 高千穂神社

現在分類:

```text
MODEL_CHANGE_REQUIRED
```

Blocking structure:

```text
三毛入野命
鵜目姫命
ほか8柱
```

解除条件:

1. unnamed / incomplete collectiveを祭神identity創作なしで表現できるKnowledge Contractがある
2. 集合であること・Source帰属をModelで保持できる
3. 名指し済み祭神だけを完全一覧として表示しない
4. 通常の1 row = 1 named deityという既存`ShrineDeity`意味を壊さない
5. 必要なMigration / Serializer / Evidence Gate変更を専用Model-risk PRで実装する
6. 既存通常Deity dataの意味が変わらないことを回帰テストする

全条件完了まで:

```text
MODEL HOLD
```

を維持する。

### 7.7 冠稲荷神社

現在分類:

```text
MODEL_CHANGE_REQUIRED
```

独立した2問題を持つ。

```text
A. Main-shrine Collective Deity
   -> ほか15柱以上

B. Associated / Subordinate Worship Target
   -> 聖天宮等
```

解除条件:

1. 高千穂神社と同等のCollective Deity表現能力を成立させる
2. 「ほか15柱以上」を架空の個別祭神rowへ変換しない
3. 聖天宮等を、accepted Sourceが本社祭神として明示しない限り親`ShrineDeity`へ混入させない
4. A/B双方を独立にPASSする

Associated Target問題だけ解決してもHOLDは解除しない。

### 7.8 千葉神社

現在分類:

```text
MODEL_CHANGE_REQUIRED
```

Blocking issue:

```text
現在主祭神identity
+
神仏習合 / 妙見信仰relation
```

解除条件:

1. accepted Sourceで現在・歴史上のidentityを確認する
2. 複数の宗教的identityを独立した複数祭神rowへ平坦化せずrelationを保持できるKnowledge Contractを成立させる
3. Sourceにない同一視を推論しない
4. Detail / Recommendation transportで意味が変質しない
5. Evidence Gate挙動を明示テストする
6. Model / Contract変更を専用Model-risk PRに隔離する

意味損失なくrelationを表現できるまで:

```text
MODEL HOLD
```

を維持する。

### 7.9 靖國神社

現在分類:

```text
PRODUCT_DECISION_REQUIRED
```

この分類はRepository Governance記録に基づく。本監査は対象神社への政治的・宗教的評価を独自に行わない。

Product HOLD解除にはMother Shipによる明示scope判断が必要である。

少なくとも次のsurfaceについて扱いを明示する。

```text
Knowledge登録
Detail表示
Search / Map表示
Recommendation参加
```

これらは別々に判断可能である。

将来Modelが技術的に表現可能になったとしても、Product HOLDを自動解除しない。

Mother Shipによる明示scope判断がない場合:

```text
PRODUCT_HOLD
```

を維持する。

---

## 8. 9社共通Release Rules

### Rule 1: 構造Gapを推測で埋めない

以下を創作しない。

- 不明祭神名
- 祭神hierarchy
- 神格 / 仏教尊格の同一視
- 部分祭神一覧の完全性
- Sub-shrine Factの本社帰属

### Rule 2: Source-first boundary

Fact ownershipはaccepted Sourceが対象Shrine entityについて何を述べているかで決める。

以下は単独では帰属根拠にならない。

- 同じWebsite
- 同じ境内
- 歴史的関連
- 同じpage section

### Rule 3: 歴史が複雑であること自体はModel failureではない

```text
現在本社祭神
と
歴史的文脈
```

をSourceに基づいて安全に分離できるなら、Schema変更なしで処理できる。

### Rule 4: 複合HOLDは全blocking causeを解消する

1つのriskだけ解決しても、別のblocking causeが残る場合はHOLDを解除しない。

### Rule 5: Model変更とRecommendation変更を分離する

Model-risk実装はRecommendation quality / ranking変更と分離する。

同一Codex指示・同一PRへ束ねない。

### Rule 6: Product PolicyをSchema問題の逃げ道にしない

Model / Source / curationで解決可能性が残るケースを、難しいという理由だけで`PRODUCT_DECISION_REQUIRED`へ送らない。

逆にProduct HOLDは、Schemaが表現可能になっただけでは自動解除しない。

---

## 9. Final State

```text
MODEL / PRODUCT HOLD 9

CURATION_RELEASE_CANDIDATE
└─ 千住神社

RESEARCH_REQUIRED_BEFORE_RELEASE
├─ 榛名神社
└─ 古峯神社

MODEL_REVIEW_REMAINS
├─ 愛宕神社
└─ 赤城神社

MODEL_CHANGE_REQUIRED
├─ 高千穂神社
├─ 冠稲荷神社
└─ 千葉神社

PRODUCT_DECISION_REQUIRED
└─ 靖國神社
```

9社すべてについて、HOLD解除へ進む条件を明示した。

本監査によって自動的にHOLD解除される神社はない。

---

## 10. Implementation Boundary

本監査が承認するのはDocumentationまでである。

後続のModel変更は、別タスクとして以下を明示する。

- purpose
- non-goals
- file / model change scope
- migration plan
- Evidence Gate impact
- Serializer / API impact
- regression tests
- dedicated Human Approval gate

後続Seed / Production作業も、通常Knowledge pipelineとHuman Approval boundaryを維持する。

---

## 11. Completion Checklist

- [x] 監査開始BASE_SHA固定
- [x] 9社の既存HOLD根拠を再確認
- [x] Collective Deity問題を定義
- [x] Shinbutsu-shugo問題を定義
- [x] Associated Worship Target問題を定義
- [x] Main Shrine / Sub-shrine境界を定義
- [x] 現行ShrineDeity / ShrineHistory表現限界を固定
- [x] Runtime EligibilityとModel Risk解除を分離
- [x] CURATION_RELEASE候補を分類
- [x] MODEL_CHANGE_REQUIRED候補を分類
- [x] PRODUCT_DECISION_REQUIRED候補を分類
- [x] Research / Review中間状態を保持
- [x] 各9社のHOLD解除条件を固定
- [x] Production write = 0
- [x] Seed change = 0
- [x] Recommendation change = 0
- [x] Model / Migration change = 0

Final classification:

```text
MODEL_RISK_RELEASE_CONTRACT_READY
```

---

## 12. Related Repository Records

本監査で参照した主要Repository記録:

- `docs/audit/production-knowledge-gap-14-shrines.md`
- `docs/audit/post-batch16-knowledge-next-track-comparison.md`
- `docs/audit/knowledge-batch11-seed-preflight.md`
- `docs/audit/knowledge-batch14-target-selection.md`
- `docs/audit/knowledge-batch15-target-selection.md`
- `docs/audit/knowledge-batch15-seed-preflight.md`
- `docs/audit/knowledge-batch16-target-selection.md`
- `docs/audit/knowledge-batch16-seed-preflight.md`
- `docs/audit/collective-deity-contract-stress.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/models.py`

古い監査記録に現在Runtime Architectureと矛盾する記述がある場合、本書ではBASE_SHA時点の現行Model / Eligibility Contractを優先し、古いRuntime記述はhistorical contextとしてのみ扱う。
