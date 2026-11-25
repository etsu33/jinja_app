> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBI全体へ横断的に適用するFixed Rule（通常タスクから暗黙変更してはならない原則）のindex / contractである。
>
> 本書はRuleの**所在と境界**を管理する。個別Field、Payload、Weight、API path、helper名、Event property等のversioned detailは持ち込まず、各owning canonical文書、実装コードおよびテストへ委譲する。
>
> 本書は新しいProduct仕様を作らない。`docs/audit/rule-canonicalization-audit.md`（Phase 1）・`docs/audit/rule-authority-resolution.md`（Phase 2A）・`docs/audit/rule-conflict-resolution.md`（Phase 2B）・`docs/audit/rule-status-classification.md`（Phase 3）で`CURRENT_FIXED`と確定した124件のRule Candidateを、意味を失わない範囲で統合した結果である。traceabilityは`docs/audit/fixed-rules-finalization.md`を参照する。

# KAMI MUSUBI Fixed Rules

## 目的

KAMI MUSUBIには、機能横断で維持しなければならない原則がある。これらは特定Featureの都合で暗黙に上書きされてはならない。

本書は次の2点を固定する。

1. どの原則がFixed Ruleであるか
2. Fixed Ruleを変更する場合に何をしなければならないか

## 本書が扱わないもの

以下は本書の責務外であり、各owning canonicalが管理する。

- 個別Field、Schema、Enum、Payload構造
- Score計算式、Weight、Ranking順序
- API Endpoint、Route、helper名、関数名
- Event名、Property名、KPI定義
- 画面レイアウト、コピー文言
- 実装状況、進捗、TODO、PR履歴

## Fixed / Versioned / Unresolved / Superseded

| 分類 | 意味 | 変更方法 |
| --- | --- | --- |
| **Fixed**（本書） | KAMI MUSUBI全体へ適用する横断原則 | 通常Feature PRから暗黙変更禁止。§Fixed Rule Change Procedureに従う |
| **Versioned** | 各owning canonical contractがCurrent authority | 専用Feature / Contract PRで、canonical + implementation + testsを同期して変更する |
| **Unresolved** | Authority未確定 | Current Ruleとして利用しない。推測でFixed / Versionedへ昇格させない |
| **Superseded** | Current authorityを持たない | 履歴として必要な場所のみ保持する。Fixed Rulesへ復活させない |

VersionedなRuleを本書へ複製しない。Fixed Ruleは「その原則を破ってはならない」ことを固定し、「現在どの値・どのFieldか」は固定しない。

## Rule IDの扱い

- Rule IDはstable IDとして扱い、将来の参照に用いる
- Ruleを削除した場合もIDを再利用しない
- IDの意味を変える改訂は、新IDの発行と旧IDのSuperseded化として扱う

---

## 1. Authority / Source of Truth

### `FR-AUTH-01` 文書と実装の役割分担

canonical文書は、目的、責務、境界、入出力の意味、禁止事項、委譲関係、互換方針および更新条件を管理する。

実装コードとテストは、Endpoint、Route、Field、Payload、保存処理、判定処理、Fallbackおよび実際のResponseを管理する。

一方が他方を代替しない。文書に書かれていないことを理由に実装が自由であるとは扱わず、実装が存在することを理由に仕様が正しいとも扱わない。

### `FR-AUTH-02` business decisionのruntime authorityはBackendに置く

ユーザーへ提示する判断の最終決定権はBackendに置く。Frontend / Mobileは、Backendが決定した結果を表示する側として扱う。

Backend生成値が利用可能な場合、Frontendは自前の代替生成値でそれを置き換えない。

対象となる判断の範囲、および各Engineの正確な入出力は各owning canonicalと実装を参照する。

### `FR-AUTH-03` Domain canonicalの責務境界

Core / Product / Knowledge / Analytics / Auditは、それぞれ異なる責務を持つ。他Domainの契約を自Domain文書で重複定義しない。

- Core: システム全体構造、横断技術責務、品質基準、接続契約、生成原則
- Product: 画面、体験、機能単位の契約
- Knowledge: 神社データ品質、意味定義、コピー生成原則
- Analytics: Event、Payload、KPI、Funnel、集計責務
- Audit: 監査結果、過去判断、時点記録

正本文書とReference文書の責務を同一文書内で混在させない。

### `FR-AUTH-04` canonical sourceを環境状態と同一視しない

開発環境の現在状態をcanonical source of truthとして扱わない。

- ローカルDBの現在状態そのものをcanonicalとしない
- 作業単位の一時branchをmerge後の長期source of truthとしない
- 作業対象として固定したRepository以外をactive development sourceとして使用しない

---

## 2. Conflict / Documentation Governance

### `FR-GOV-01` Conflictを推測で解決しない

文書・実装・テスト・情報源のいずれかが食い違う場合、どれか一つを自動的に正しいものとして扱わない。意図した仕様をAuthorityへ確認する。

矛盾するSourceを削除して整合しているように見せることを禁止する。説明不能な競合を推測で統合しない。

### `FR-GOV-02` Current Source of Truthを優先して読む

現在仕様を判断する際は、Current Source of Truth → 最新のAudit → 中間Audit → 時点Snapshot の順で参照する。

下流文書だけを更新して、上流仕様または共通用語と矛盾する変更を行わない。

時点記録と現在の実装が食い違う場合は、より新しい実装・テストの確認結果を優先する。

### `FR-GOV-03` 分類を暗黙に昇格・降格させない

- Reference文書の未実装案を、実装済み仕様として扱わない
- Archive文書を現行の仕様判断・計測契約判断に使用しない
- Status未記載を「古い」「Superseded」「Archive」と断定しない。未分類は未分類として扱う

### `FR-GOV-04` canonical indexを同一PRで同期する

正本文書を追加・削除・分類変更した場合、対応するDomain READMEおよび分類管理文書を同じPRで更新する。

契約文書と実装を変更する場合は、同じPRで両方を更新する。

READMEへ詳細仕様、TODO、実装履歴、監査結果およびPR情報を記載しない。

---

## 3. Backend / Frontend Responsibility

### `FR-RESP-01` 認証・権限・課金の責務分離

Frontendは認証状態と認証要求時のUIを担当する。Token保持・更新・Backendへの付与はBFFの責務とする。認証、権限、所有者および課金状態の最終判定はBackendが担当する。

WebとMobileのToken保存方式を同一視しない。

### `FR-RESP-02` Frontend / MobileはBackend-owned decisionを再計算しない

Backendが決定・生成した結果を、Frontend / Mobileが独自ロジックで再計算、再解釈または上書きしない。

同一の業務判定をclient側へ重複実装しない。判定が複数画面で必要な場合は、client側でも共通実装へ集約し、画面ごとに判定結果が食い違う状態を作らない。

### `FR-RESP-03` 横断契約は共通層を経由する

複数画面・複数Platformで共有する契約は、画面コードへ分散させず共通層へ集約する。

- Analytics Eventは専用helperを経由して送信する
- UI ComponentはSemantic Token層を参照する。下位層を直接参照する場合は例外として理由を残す

### `FR-RESP-04` 画面責務を混同しない

検索、コンシェルジュ、地図、人気ランキング等、目的の異なる画面責務を混同しない。ある画面の都合で他画面の責務を吸収しない。

---

## 4. Safety / Non-assertion / User Autonomy

### `FR-SAFE-01` 断定しない

KAMI MUSUBIは、ユーザーの心理状態、性格、運命、未来、および宗教的効果を断定しない。

- 診断、宗教的保証、結果保証、決定論的な未来予測を行わない
- 神社の由緒やご利益を、未来の結果やユーザー状態を保証する根拠として利用しない
- 単一の分類値だけでユーザーの状態を判定しない
- 過去の記録だけを根拠にユーザーの状態、性格または将来を断定しない

Fact層に心理診断を書かない。Interpretation層に神社の未確認事実を書かない。Action層に宗教的効果保証を書かない。

### `FR-SAFE-02` 確度を超える表現をしない

情報の確度を超える表現強度で出力しない。

- 伝承として記録された情報を、確度の高さに関わらず断定表現で出さない
- 実装が持たない精度を含意する表現を使わない

### `FR-SAFE-03` ユーザーの自律を尊重する

- 参拝作法や宗教的実践を唯一の正解として強制しない
- 行動しない選択を異常として扱わない
- 感情を評価せず、回答を誘導せず、望ましい感情を設定しない
- 危険または禁止されている行動を提案しない

### `FR-SAFE-04` 内部表現・Governance指標をユーザーへ露出しない

内部タグ、内部変数名およびfallback文言をそのままユーザーへ表示しない。

Governance観測指標（Coverage、整備状態等）を、神社の信頼度や格としてユーザーへ提示しない。断定的な優劣表現を避ける。

---

## 5. Fact / Evidence / Knowledge Integrity

### `FR-KNOW-01` EvidenceなしにShrine Factを主張・確定しない

保存済みの根拠がないものをFactとして主張しない。

- AI生成のみで事実項目を確定しない
- 実在が確認できない施設、文化財、由緒、境内設備を根拠として使用しない
- 神社固有の根拠が存在しない提案を行わない
- 根拠のない解釈を一次情報として保存しない
- 単一の二次sourceのみを唯一の根拠としない

### `FR-KNOW-02` 情報の確度と種別を混同しない

- 伝承的記述を歴史的確定事実として扱わない。公式情報であっても同様とする
- 種別の異なる情報を相互の代替として扱わない
- 「未着手」と「確認済みの情報不足」を同一視しない
- 概念項目と物理フィールドを同一視しない

### `FR-KNOW-03` 未解決の矛盾を断定利用しない

複数Sourceが矛盾し未解決である情報を、断定的なFactとして利用しない。

### `FR-KNOW-04` 位置・identityを推測で確定しない

判断保留の状態で座標や所在地を推測してSeedまたはProductionへ投入しない。

既存値を惰性で維持せず、距離等の単一指標だけで候補を自動採用せず、用途の異なる情報を単独の採用根拠としない。

---

## 6. Recommendation / Meaning / Reason Boundary

### `FR-REC-01` Recommendation関連レイヤーの責務を混同しない

各レイヤーは自身の責務を超えない。

- 意味づけを担う補助レイヤーは、推薦順位、Scoreまたは推薦理由そのものを単独で決定しない
- 解釈レイヤーは表示コピーを生成しない
- 行動提案レイヤーは神社の選定や推薦理由を決定しない
- Governance観測の責務とRuntime判定の責務を混同しない。一方が他方の判定ルールを再実装しない

### `FR-REC-02` Fact / Interpretation / Actionの依存順序と非代替性

Fact（事実）とInterpretation（意味文脈）は責務が別であり、どちらか一方だけでは他方を代替しない。

RecommendationはMeaningを前提とし、ActionはRecommendationを前提とし、ReflectionはActionを前提とする。同じ用語を複数の意味で利用しない。

### `FR-REC-03` Runtime Snapshotを暗黙に再計算しない

保存済みの推薦結果は、神社情報、評価ロジックまたはユーザー行動状態が後から変化しても、暗黙に再計算または再ランキングしない。

現在状態として管理する情報と、過去のSnapshotを同一視しない。監査・品質計測用のpayloadと、ユーザーへ提示した推薦理由を同一視しない。

### `FR-REC-04` 製品間Authorityを混在させない

共有基盤を持つことは、共有製品責務を意味しない。ある製品体験の価値を作るために、別の製品体験の挙動、Ranking、API契約またはUX責務を暗黙に再設計または弱めない。

ある製品で解除した表示制約が、別の製品の制約を自動的に解除するものとして扱わない。

### `FR-REC-05` Runtime signalをShrine Knowledgeへ越境させない

Runtime signal（方位・占術等）は、神社そのものの性質を新設または上書きしない。

- 神社の根拠をRuntime signalから捏造しない
- 実際に使用していないsignalをrecommendation evidenceとして提示しない
- Runtime signal単独で最終的な神社を決定しない
- Runtime signalを推薦理由の主理由として提示せず、主理由の順位を上書きしない

### `FR-REC-06` 単一signal・未検証入力で推薦決定を完結させない

単一の分類値やprofile値だけで推薦結果を決定しない。ユーザーの生入力を直接スコアへ加点しない。

投稿者入力を確認工程を経ずにRecommendation Authorityへ接続しない。

Runtime情報を神社の固定情報として保存しない。

### `FR-REC-07` 候補生成と最終順位付けを分離する

広めの候補取得と最終順位付けを分離し、候補生成段階で最終順位を確定しない。

新しいScoreは既存順位へ直ちに反映せず、差分、各signalの寄与および行動データとの関係を観測した上で適用可否を判断する。

---

## 7. Security / Production Safety

### `FR-SEC-01` 認証情報とBackend到達経路をclientへ露出しない

認証Tokenは、client側のJavaScriptから到達できる領域へ保存しない。

FrontendからBackendへ認証付き通信を直接行わず、専用の中間層を経由する。Backend Originや接続先設定をFrontend Component / Routeから直接参照しない。認証付与処理をRouteごとに重複実装しない。

### `FR-SEC-02` 権限境界を越える操作を無防備に公開しない

- 権限昇格を伴う操作を、認証・権限チェックなしにHTTP経由で公開しない
- 内部stateを返すdebug用の経路を、認証・権限チェックなしに公開しない
- 課金状態や権限をFrontendだけで確定しない。client側の未確定状態を理由にBackendの利用制限を回避できる設計にしない

### `FR-SEC-03` secret / 認証state / Production資産の取り扱い境界

- 機微情報をproduction runtimeのログへ出力しない。level（Debug / Info / Error / Warning）を問わない
- secret値をRepositoryへcommitせず、ソースコードへ直接記述しない
- 認証stateを含むbackupをRepositoryへcommitしない
- Production databaseおよびProduction接続情報をlocal development操作へ流用しない

### `FR-SEC-04` テストから外部API・本番データへ接続しない

テストおよびE2Eから、課金の発生する外部API、実Backendまたは本番データへ接続しない。

---

## 8. Analytics Privacy / Interpretation

### `FR-ANA-01` private / sensitive contextをAnalyticsへ送信しない

個人または場所を特定しうる情報、ユーザーの自由入力本文、および生成された推薦理由を、Event名を問わずAnalyticsへ送信しない。障害ログについても同じ境界を適用する。

自由入力本文をURL等の観測可能な経路へ含めない。

この境界はPlatform・導線を問わず適用する。禁止対象の具体的なProperty一覧は各Analytics契約で管理する。

### `FR-ANA-02` 観測都合でpayloadを増やさない

品質検証・分析の都合で、本番Event、Payloadまたはユーザー識別子を増やさない。

Event追加より既存属性による集計を優先する。追加が必要な場合は、目的、発火箇所、重複単位、保持期間、禁止属性検査およびPlatform差を先に契約文書へ記載する。

禁止属性が1件でも検出された場合は、送信停止を含めて即時調査する。

### `FR-ANA-03` 識別に関する誤用をしない

少数データから個人を推測しない。少数セルは非表示とするか期間を延長する。個人を特定しうるpropertyやcohortを作成しない。

ある識別子を、意味の異なる別概念の識別子の代用として使用しない。

### `FR-ANA-04` Analyticsの解釈限界を守る

Analyticsは体験改善の観測に利用する。個別ユーザーの心理状態、宗教的効果、信仰の程度または人生上の成果を判定するために利用しない。

- Eventが存在しないことを、その行動が発生しなかった証拠として扱わない
- 相関を因果として扱わない
- 異なる文脈またはセッションから発生した行動を、同一の意思決定として扱わない

---

## 9. Historical Snapshot / Audit Governance

### `FR-HIST-01` 記録された状態を暗黙に別の意味へ変換しない

時点記録として残された数値（Coverage件数、対象件数等）をHistorical Snapshotとして扱い、現在値へ無断で再計算・上書きしない。

延期（Deferred）を削除（Deleted）と同一視しない。

### `FR-HIST-02` Audit文書をCurrent contractとして扱わない

Audit文書に記載された時点判断、TODOおよび設計案を現行契約として扱わない。

Audit index文書は、個別Audit文書の内容、Status、削除および移動を管理しない。新しいAudit chainを索引化する場合は、Current Source of Truthとの対応関係を確認した上で追加する。

---

## 10. Fail-safe / External Dependency Boundary

### `FR-FAIL-01` 副次的な失敗を主要体験の失敗へ昇格させない

補助的な機能・外部依存・未確定状態の失敗を、KAMI MUSUBIの主要フロー全体の失敗へ昇格させない。

- 状態が未取得またはエラーである場合に、正当な利用権を持つユーザーを誤って遮断しない
- 外部依存（地図等）が利用できない状態でも、主要フローを完遂できる構造を維持する

個別機能の縮退手順と表示挙動は、各owning canonicalと実装を参照する。

---

## 11. Fixed Rule Change Procedure

### `FR-CHANGE-01` Fixed Ruleの変更手順

Fixed Ruleは永久不変ではない。ただし通常のFeature / Fix / Audit taskから暗黙に変更してはならない。

変更する場合は、次をすべて満たす専用のRule Change / Architecture Decisionとして実施する。

1. 通常Feature PRへ便乗させない。独立したPRとして実施する
2. 変更理由を記録する
3. 影響Domainを列挙する
4. Mother Ship Decisionが必要な変更は、独断で確定せず明示的に差し戻す
5. 影響するCurrent canonical、実装およびテストを同一方向へ更新する
6. 旧RuleをSupersededとして履歴化する。Rule IDは再利用しない
7. 本書と`docs/audit/fixed-rules-finalization.md`のtraceabilityを同じPRで更新する

### `FR-CHANGE-02` Fixed Ruleと実装が衝突した場合はSTOPする

Fixed RuleとCurrent implementationが衝突した場合、どちらかを推測で正しいものとして扱わない。

作業を停止し、Authorityを確認する。確認が完了するまで、文書側・実装側のいずれも推測で書き換えない。

---

## 関連ドキュメント

- `docs/core/README.md`
- `docs/core/architecture.md`
- `docs/product/README.md`
- `docs/knowledge/README.md`
- `docs/analytics/README.md`
- `docs/audit/fixed-rules-finalization.md`（本書のtraceability。Current Source of Truthではない）

## 更新ルール

- 本書の更新は`FR-CHANGE-01`の手順に従う
- Versioned detail（Field、Payload、Weight、Event property、API path等）を本書へ持ち込まない
- 個別Ruleの実装状況、TODO、PR履歴を本書へ記載しない
- Rule IDを再利用しない
