# Collective Deity Contract Stress Audit（靖國神社を主対象とした`ShrineDeity`Contract境界監査）

## Status

Archive（時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`および`docs/core/recommendation-readiness.md`を正本とする）

## 目的

「多数・集合的な祭神をcurrent `ShrineDeity` Modelでどう扱うか」というContract境界のみを対象とする、read-only監査である。本監査ではFact登録・Model変更・Migrationのいずれも行っていない。

主対象: 靖國神社。比較材料として、既存実データ（春日大社・熱田神宮・伏見稲荷大社・阿蘇神社・三峯神社・武蔵御嶽神社）を用いる。

## 責務境界（Political / Religious Neutrality Guard）

本監査が扱うのはSource表現・Data Model・Recommendation requirement・Scale・Contract compatibilityのみである。靖國神社に対する政治的評価、歴史認識の正誤、宗教的妥当性の評価、祭神の価値判断のいずれも本監査の対象外であり、以下のいずれのセクションにも含まない。

---

## A. Current ShrineDeity Contract（再確認）

`backend/temples/models.py`の`ShrineDeity`は以下のfieldのみを持つ。

`shrine`(FK) / `display_name` / `canonical_name` / `role`(primary/enshrined/secondary/unknown) / `sort_order` / `sources`(M2M) / `verification_status` / `confidence` / `verified_at` / `note` / `created_at` / `updated_at`

collective/group表現用field、count表現用field、sub-group/category表現用fieldは**存在しない**。

`docs/knowledge/shrine-knowledge-contract.md`「deity契約」は以下を明記する。

- 「`deity`を、神社に祀られている神格・祭神に関するKnowledgeとして定義する」
- 「1社に複数の`deity`エントリを保持できる（1対多）」
- 序列不明時は全エントリを`role: unknown`として対等に列挙する

すなわち現行Contractは「1エントリ = 1つの名指しされた神格」という設計思想で一貫しており、「多数・匿名・集合的な被祀者群」を表現する概念は明文化されていない。これは補完すべき見落としではなく、現行Contract文書自体に不在の概念である。

---

## B. 靖國神社 Exact Source Audit（fresh確認）

| 項目 | 内容 |
|---|---|
| Source | 靖國神社の由緒 (`https://www.yasukuni.or.jp/history/detail.html`) |
| organization | 靖國神社 |
| direct fetch | 可能（直接確認済み） |

**祭神表現**: ページ内で「祭神」という語は使われず、「御祭神」が用いられる。「靖國神社には、戊辰戦争やその後に起こった佐賀の乱、西南戦争といった国内の戦いで...尊い生命を捧げられた方々の神霊（みたま）が祀られており、その数は**246万6千余柱**に及びます」と記載。

**246万柱の文脈**: 身分・勲功・男女の区別なく、「祖国に殉じられた尊い神霊」として一律平等に祀られている総数として説明されている。

**個別列挙の有無**: 由緒ページ上には、霊璽簿・祭神名票等、個々の氏名を列挙する仕組みについての言及は確認できなかった。

**重要**: これは「本監査が直接fetchした由緒ページに記載が無かった」という事実であり、「個別氏名の記録が公式に存在しない」という断定ではない。本監査はこの2つを区別し、後者を主張しない。個別氏名記録の存否そのものは、本監査の責務（Data Contract）の範囲外であり評価しない。

---

## C. Representation Options比較

### Option A — Individual Rows（246万件個別ShrineDeity化）

| 観点 | 評価 |
|---|---|
| 技術的現実性 | DB自体は大量行を扱えるが、1 shrineに246万件の子行を持たせる設計は本アプリのデータ運用（Fact Sheet単位でexact Sourceを個別確認して登録する方式）と根本的に相容れない |
| Source追跡可能性 | 不成立。公式サイトは個々の氏名を列挙しておらず（§B）、246万件それぞれに`exact URL/title/verification`を用意する手段が存在しない |
| DB規模 | 現在の全deity総数49件（Batch3時点）の**5万倍**の規模となる |
| API/prefetch負荷 | `shrine_knowledge_selector.fetch_fact_ready_knowledge_deities()`は対象shrineの全deity行を`prefetch_related`込みで一括Python化する実装であり、1 shrineの巨大な行数に対する上限は設けられていない。246万件の場合、1リクエストで246万オブジェクト＋そのsources M2Mをメモリ上に展開することになる |
| Recommendation利用価値 | `_join_knowledge_deity_names()`は全Fact-ready deityの`display_name`を「、」で無制限に連結し、Reason文用の一文にする設計（読点区切りの自然文を想定）。246万件を連結した文字列は実用上意味をなさない |

→ Source Availability・データ運用・Recommendation実利用のいずれの観点からも非現実的。

### Option B — Single Collective Row（例:「英霊」等を1行として保持）

- 公式サイトは実際に「246万6千余柱の神霊」という集合的な語りで祭神を説明しており、この点は集合的表現と一定程度整合する
- ただし公式サイトは「御祭神」という語を「祭神という概念そのもの」を指す言葉として使っており、単一の神名として使ってはいない。「英霊」等の言葉へ集約した`display_name`を独自に作ることは、公式表現にない語を创作することになる
- 「身分・勲功・男女の区別なく」という公式の強調点（個々人の尊厳の平等性）を、1行への集約が意味的に損なう可能性がある
- 現行`deity`契約（1エントリ=1つの名指しされた神格）の暗黙の前提とも一致しない

→ 公式Sourceとの部分整合はあるが、Contractの意味を拡張解釈する必要があり、単純にPASSとは言えない。

### Option C — Representative Deity（代表者1名等への縮約）

公式サイトの記述（「身分・勲功・男女の区別なく」）は、代表者を立てるという発想そのものと相容れない。公式根拠が一切確認できないため不採用。

### Option D — Separate Collective Representation（別concept）

`collective_deity`等の別概念を設ける余地はある、とだけ記録する。`FOLLOW_UP_OPTION`として記録するに留め、Model設計案として確定しない。本監査ではModel設計・migrationは行わない。

### 不採用の明確化

本監査は以下を不採用とする。

- 246万件をindividual `ShrineDeity` row化しない（Option A）
- 代表者1名へ縮約しない（Option C）
- 「英霊」等を根拠なく単一Deity化しない（Option B・Cいずれの形でも）
- 阿蘇神社の「確認できた1柱だけ登録」方式を靖國神社へ機械的に適用しない（§D参照、性質が異なるため）

---

## D. 既存ケースとの比較

| Shrine | パターン |
|---|---|
| 春日大社 | 4柱を個別Row化（公式が個別に命名） |
| 熱田神宮 | 主祭神+相殿5柱を個別Row化（公式が個別に命名） |
| 伏見稲荷大社 | 5柱を個別Row化（公式が個別に命名、座位表現は`note`で保持） |
| 阿蘇神社 | 主祭神1柱のみ個別確認・登録、残り11柱の家族神は集合的にしか確認できず見送り |
| 靖國神社 | 個別列挙の前提自体が公式に存在しない |

阿蘇神社は「有限（12柱）で、将来的に個別Sourceが見つかれば追加登録できる部分集合」であるのに対し、靖國神社は「桁違いの規模（246万）であり、かつ公式が個別列挙という発想自体を採らない」という点で性質が異なる。加えて阿蘇神社には明確な主祭神（健磐龍命）が存在するのに対し、靖國神社には「身分・勲功に関わらず平等」という建前上、単一の中心神格に相当する存在が公式に定義されていない。したがって阿蘇神社方式（確認できる1柱のみ登録）をそのまま靖國神社へ適用することも、公式の平等性の強調と緊張関係を生む。

---

## E. Recommendation Requirement確認

`temples/services/concierge_chat.py`の`_join_knowledge_deity_names()`・`_resolve_knowledge_deity_confidence()`はいずれも「少数の名指しされた祭神を人間可読な一文へ結合する」ことを前提に設計されている（結合に上限はないが、想定用途は自然文への読点結合）。Evidence Gate・Knowledge Selector・Detail API・Reason V4のいずれも、個々の被祀者246万人分の個別情報を要求する設計にはなっていない。

**結論**: Recommendationパイプラインが実際に必要とする粒度は「少数の名指しされたdeity」であり、大量個別データはRecommendation価値を生まない。DB正規化それ自体を目的として巨大なデータ構造を作る理由はない。

---

## F. Scale Stress（構造監査のみ、load testは実施していない）

- `fetch_fact_ready_knowledge_deities()`は対象shrine_idsに対して1クエリで全deity行を取得し、Python側で全件イテレートする。1 shrineあたりの行数上限は実装上存在しない
- 1 shrineが極端に大量のdeity行を持つ場合、そのshrineがcandidate poolに含まれるたび（`build_chat_candidates()`実行のたび）に、当該shrineの全deity行＋M2M sourcesがメモリ上に展開される
- Admin一覧・編集画面も、1 shrineに紐づくdeity行数に応じてスクロール・ページング負荷が線形に増加する

構造上、大量個別行は現在の実装のいずれのレイヤー（Selector/Recommendation/Admin）とも相性が悪い。

---

## G. Contract Decision

### Current Contract Decision: `CURRENT_MODEL_SUFFICIENT_WITH_LIMITATION`

意味:

- 通常の名指しされた祭神を持つ神社には現行`ShrineDeity`で十分（Pilot・Batch1-3、19社・49 deityで実証済み）
- 大規模・匿名的・集合的祭神を表現するContractは存在しない
- この限界はcurrent rolloutを止める理由にはならない
- collective caseへ無理にcurrent modelを適用しない（§C「不採用の明確化」参照）

### Rollout Decision: `AVOID_COLLECTIVE_CASES_TEMPORARILY`

意味:

- Batch 4以降の通常神社Rolloutは継続可能
- 靖國神社等のcollective-deity caseは別Contract判断まで保留
- zero-KnowledgeのままRecommendationへ残すことはcurrent fallback上安全（§H参照）

---

## H. Non-Blocking / Blocking Classification

| 分類 | 内容 |
|---|---|
| BLOCKING | なし。現行Rolloutの継続を妨げるものではない |
| NON_BLOCKING（`SUPPORTED_BY_SAFE_FALLBACK`） | 靖國神社をKnowledge未登録（zero-Knowledge）のまま安全にRecommendationで扱える。長太稲荷神社（Batch2、`INSUFFICIENT_EVIDENCE`）と同型のLegacy fallback経路で、candidate pool・Evidence Gate・Reason V4のいずれもクラッシュせず安全に動作することは、これまでのBatchで繰り返し実証済みの一般的な仕組みである。これは「Recommendation failure」ではなく、fallback機構によって正しく支えられている状態である |
| FOLLOW_UP_REQUIRED | 靖國神社と同様の構造（集合的・大規模な祭神表現）を持つ神社（例: 各都道府県の護国神社）を将来のBatchで対象とする場合、本監査と同じ壁に当たる。着手前に専用のModel/Contract設計判断が必要 |

Candidate / Score / Ranking / Evidence Gate / Reason V4のいずれも変更不要であり、zero-Knowledge fallbackは現行のまま維持可能である。

---

## I. Batch 4 Impact

**`AVOID_COLLECTIVE_CASES_TEMPORARILY`**

残り81/100のzero-Knowledge shrineの大半は、これまでのBatch1-3と同様に個別に名指しされた祭神を持つ通常のケースであり、本監査の結論はそれらに影響しない。ただし、靖國神社および護国神社系列等、同型の集合的祭神構造を持つ神社は、Model/Contract設計判断が行われるまでBatch対象候補から除外することが望ましい。Batch 4自体の対象選定は本監査では行わない。

---

## J. Coverage再確認

`knowledge_coverage_report`実測（監査前後で変化なし、Fact投入を行っていないため）。

- audit_target_shrines = 100
- Knowledge = 19/100 (19.0%)
- zero-Knowledge = 81/100 (81.0%)
- verified_source_count = 33

靖國神社へFactを投入していないため、Coverage値は変化していない。

---

## K. Historical Audit Correction（Batch 3文書の算術訂正）

`shrine-knowledge-rollout-batch-3.md`§Oの「history総数 43→50」は算術ミスであり、正しくは**43→49**（Δ+6、春日大社1+熱田神宮1+諏訪大社2+阿蘇神社1+九頭龍神社新宮1）である。`knowledge_coverage_report`実測（history_count_distribution合計=49）で確認した。Archive済み文書のため`shrine-knowledge-rollout-batch-3.md`は遡及修正せず、本記録のみをHistorical Audit Correctionとして残す。current contract（deity契約・history契約等）の一部ではなく、単なる過去文書の数値訂正である。

---

## L. Duplication Guard

本監査は以下を再定義していない。

- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-architecture.md`
- `docs/audit/shrine-knowledge-rollout-batch-3.md`（内容をコピーしていない）

collective conceptのmodel仕様は確定していない（§C Option D参照）。Batch 4の対象は確定していない（§I参照）。

---

## Mother Ship Decisions Required

1. 靖國神社をcurrent ShrineDeityへ投入しない方針でよいか
2. zero-Knowledgeのまま許容してよいか
3. collective-deity conceptは将来検討事項としてBacklog化するか
4. Batch 4はcollective caseを避けて継続してよいか
5. Model Contract Auditをいつ再開するか

### 今回の技術推奨

| 項目 | 推奨 |
|---|---|
| 靖國神社 | `DEFER` |
| current model | `KEEP` |
| Batch 4 | `CONTINUE`（collective case除外） |
| collective concept | `FOLLOW_UP_REQUIRED` |

最終判断は母艦。

---

## 関連ドキュメント

- `../knowledge/shrine-knowledge-contract.md`
- `../core/recommendation-readiness.md`
- `./shrine-knowledge-rollout-batch-1.md`
- `./shrine-knowledge-rollout-batch-2.md`
- `./shrine-knowledge-rollout-batch-3.md`
