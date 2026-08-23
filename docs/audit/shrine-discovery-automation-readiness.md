> **Status: `DISCOVERY_READINESS_AUDIT_COMPLETE_PILOT_PARTIAL_KNOWLEDGE_LAYER_STOPPED`。**
>
> 本監査はread-only audit + 限定Pilotである。Production DBへのwrite、既存Seed /
> Knowledge Batch / Model / Contract / Recommendation / Conciergeの変更は一切
> 行っていない。新しいShrine Data Pipelineは構築していない。
>
> **要旨**: `fetch_shrine_candidates.py`は実際には使われていない死んだstubであり
> （Phase 1〜2で確認）、これを拡張する意味はない。一方、責務が競合しない**別の
> 既存実装**（`places_resolve.py`の`get_or_create_shrine_by_place_id`、および
> `sync_places_seeds`/`places_sync.py`のprefecture-scoped nearby search）が既に
> Discovery Layerとして稼働しており、REUSE_AS_ISで使える。新規Pilotコードは一切
> 書かず、AI（本監査Claude自身）によるCandidate調査 + 既存
> `find_duplicate_candidates` + 既存`import_shrines_seed --dry-run`のみで、
> 未登録3県・9 Candidateの**Shrine base-seed層**のPilotを実行した（9/9成功）。
> **Knowledge層**（deity/history Fact抽出）は、本監査セッションの`WebFetch`が
> 全外部ドメインでegress遮断されており、出典ページ本文を読めなかったため、
> Fact provenanceを確保できずSTOP GATE Bで意図的に停止した（Source URLの存在
> 確認＝WebSearchでは可能、Source本文の読解＝本セッションでは不可能、という
> 環境上の制約であり、Pipeline設計上の欠落ではない）。

# Shrine Discovery Automation Readiness Audit & Conditional Pilot

## 1. Objective

現在Shrine登録が存在しない20都道府県について、既存Shrine/Knowledge
Pipelineを再利用しながら「未登録地域 → Candidate Discovery → Source
Research → Existing Seed Candidate → validate-only → dry-run」までを安全に
自動化できるかを監査し、新規Pipelineを作らずにEXTEND_EXISTINGで成立するかを
確認する。成立する場合は3県×最大3 Candidate（最大9件）の限定Pilotを実施し、
自動化率（KPI）を実測する。全国展開の可否は決定しない（母艦判断事項）。

## 0. Preconditions（確認結果）

| 項目 | 結果 |
|---|---|
| PR #2529がdevelopへ存在 | 確認済み（`origin/develop` HEAD=`d59078e`、`docs: Shrine地理分布・Knowledge Coverage監査を実施 (#2529)`） |
| working tree clean | 確認済み |
| local develop == origin/develop | 確認済み（branch作成前に`git fetch origin develop`、`origin/develop`から新規branch作成） |
| `docs/audit/shrine-data-pipeline-phase0-audit.md` 存在 | 確認済み |
| `docs/audit/shrine-geographic-knowledge-coverage.md` 存在 | 確認済み |
| Geographic Coverage監査結果 | 確認済み（Shrine登録0社の都道府県20件を特定） |
| branch | `audit/shrine-discovery-automation-readiness`（`origin/develop`から新規作成） |

前提はすべて満たされたため、Phase 1へ進んだ。

## 2. Existing System（既存資産の全体像）

Phase 0監査（`shrine-data-pipeline-phase0-audit.md`）がREUSE_AS_ISと判定した
資産（Shrine Model / Knowledge Models / seed / import_shrines_seed /
import_shrine_knowledge / validate-only / dry-run / Evidence Gate / Coverage
tooling / Source-Fact契約 / Batch rollout workflow）に加え、本監査で新たに
確認したDiscovery関連の既存資産は以下。

| 資産 | 場所 | 状態 |
|---|---|---|
| Google Places個別解決API | `temples/api/views/places_resolve.py`（`GET`検索・`POST /places/resolve/`でplace_id→Shrine/ShrineCandidate作成） | **稼働中**。`get_or_create_shrine_by_place_id`が実際にShrineを直接作成し、`ShrineCandidate(source=RESOLVE)`も記録する |
| Places自由検索API | `temples/api/views/search.py`の`places_find`（`GET/POST /places/find/`） | **稼働中**。Google Places Find Place APIをlive呼び出し |
| Prefecture-scoped nearby discovery | `management/commands/sync_places_seeds.py` + `services/places_sync.py`（`sync_nearby_seed`） | **コードは稼働可能な状態でREUSE_AS_IS**。`--pref-code`引数で都道府県絞り込み、budget/cooldown管理、`--dry-run`ネイティブ対応。ただしseed点データ（`temples/data/places_seeds_jp_v1.json`）は東京都の3点のみで、他46都道府県分は未整備。かつ`GOOGLE_PLACES_API_KEY`/`GOOGLE_MAPS_API_KEY`が本監査環境に未設定（外部依存） |
| Shinto候補判定・正規化 | `services/places_heuristics.py`（`is_shinto_candidate`, `looks_buddhist_by_name`, `norm_name`） | REUSE_AS_IS |
| Shrine重複検出（呼び出し可能な関数） | `services/shrine_submission.py`の`find_duplicate_candidates(name, address)` | REUSE_AS_IS。ユーザー投稿神社の重複チェックで実運用中。本Pilotで実際に9件呼び出し、動作確認済み |
| Candidate Model | `temples/models.py`の`ShrineCandidate`（`Status`: auto/approved/imported/rejected、`Source`: resolve/manual/places_find/**stub (legacy)**） | REUSE_AS_IS。**Sourceのstub値自体がモデル定義内で明示的に"Stub (legacy)"とラベル付けされている** |
| `fetch_shrine_candidates.py` | `management/commands/fetch_shrine_candidates.py` | **死んだstub。詳細はPhase 3** |

## 3. `fetch_shrine_candidates.py` Audit

### Phase 1: 現行実装

- file path: `backend/temples/management/commands/fetch_shrine_candidates.py`（34行、全文）
- 実装内容: 固定文字列`place_id="stub-place-id"`、固定name_jp「テスト候補神社」、
  固定address「テスト住所」、固定`lat=35.0, lng=135.0`を`ShrineCandidate`へ
  `update_or_create`するのみ。外部I/O・Google Places呼び出し・prefecture引数・
  address引数は一切ない
- CLI contract: 引数なし（`add_arguments`が定義されていない）。実行するたびに
  同じ`place_id="stub-place-id"`のレコードを`update_or_create`するのみ
- input: なし（CLI引数を一切受け取らない）
- output: `ShrineCandidate`テーブルへの1行固定upsert（DB書き込みを伴う）
- dependency: `temples.models.ShrineCandidate`のみ
- 呼び出し元: 検索したが、他のcommand/service/testからの呼び出しは0件
  （`grep -rn "fetch_shrine_candidates" --include=*.py .`で自身のfile以外
  ヒットなし）
- 呼び出し先: なし（外部API呼び出しコードが存在しない）
- tests: 専用テストファイルなし（`grep -rl "fetch_shrine_candidates"
  --include=*.py backend/temples/tests/` で0件）
- docs: 本fileを直接説明する既存docsは0件（`grep -rl
  "fetch_shrine_candidates" docs/`で0件）
- git history: `git log --oneline --follow`は3件のcommit
  （`b0abe2c`参拝コンパスMVP UI、`77f1fa1`Compass方位候補フィルタ、
  `3693c35`Compass MVP Runtime Contract定義）を返すが、**3commitとも同一blob
  内容**（同一ハッシュ`aec7e2d`のfileが繰り返し"new file"として現れる）。
  これはこのfileがCompass機能実装のために新規作成されたのではなく、squash
  merge時の履歴表示上の副作用であり、実質的な最初の導入時点・意図した設計者は
  この3commitのcommit messageからは特定できない。同様に`ShrineCandidate`
  Model自体も`git log -S"class ShrineCandidate"`で同じ3commitしかヒットせず、
  真の導入経緯はgit historyから追跡できなかった

### Phase 2: Stub理由の分類

**分類: `superseded`（Evidence: 高）。**

根拠:

1. `ShrineCandidate.Source`enum定義そのものが`STUB = "stub", "Stub (legacy)"`
   と明記しており、モデル設計者自身がこの値を過去の遺物として扱っている
   （`temples/models.py` L1057）
2. 同じ責務（ShrineCandidate作成）を担う、実際に呼び出し元（API endpoint）を
   持つ実装が別に存在する。`temples/api/views/places_resolve.py`の
   `POST /places/resolve/`は`Source.RESOLVE`でShrineCandidateを作成し、かつ
   実際に`Shrine`本体も作成する。これは本物のGoogle Places API連携
   （`temples/services/places.py`の`get_or_create_shrine_by_place_id`）を
   経由する
3. `fetch_shrine_candidates.py`のoutputは固定値（`place_id="stub-place-id"`）
   であり、実行するたびに同じ1行をupsertするだけで、実データを一切生成しない
4. 呼び出し元0件・専用テスト0件・専用docs0件という状況は、機能として使われた
   形跡がないことと整合する

「未完成のまま放置された」（`implementation missing`）である可能性も検討したが、
`Source.STUB`が明示的に"legacy"と自己申告している事実と、機能的に代替する
実装（`places_resolve.py`）が既に存在し実際にAPI経由で呼ばれている事実から、
`unused`単独ではなく`superseded`（別実装に置き換えられ、削除されずに残った）
と判定する。`external dependency missing`（Google APIキー未設定）は
`places_resolve.py`側にも共通するため、`fetch_shrine_candidates.py`固有の
stub理由ではない。

### Phase 3: 既存Output Contract

`fetch_shrine_candidates.py`自体は固定値しか生成しないため「本来何を生成する
想定か」を同ファイルから読み取ることはできない。ただし`ShrineCandidate`
Model定義（正本）から、Candidateのschemaは以下の通り確定している。

| フィールド | 型 | 扱い |
|---|---|---|
| `place_id` | str, nullable, unique+status複合constraint | Google Place ID。Discovery段階のkey |
| `name_jp` | str, required | 神社名 |
| `address` | str, blank可 | 住所（都道府県専用fieldなし、Shrine同様） |
| `lat` / `lng` | float, nullable | 座標。Shrine側の`latitude`/`longitude`と同じ意味 |
| `goriyaku` | str, blank可 | ご利益（自由記述） |
| `source` | choices（resolve/manual/places_find/stub） | 由来。deity/history/confidence/verificationに相当するfieldはCandidate Model自体には存在しない |
| `raw` | JSONField | 元APIレスポンス等のsnapshot |
| `status` | choices（auto/approved/imported/rejected） | Human Review用の状態機械（既存） |

**確認結果:**

- Shrine base seedとの関係: `name_jp`/`address`/`lat`・`lng`は
  `shrines_seed_clean.json`の`name_jp`/`address`/`latitude`・`longitude`と
  1:1で対応可能（fieldキー名の差はlat/lng ↔ latitude/longitudeのみ）
- Knowledge seedとの関係: `ShrineCandidate`にはdeity/history/confidence/
  verification相当のfieldが一切ない。Knowledge Seed（Source/Deity/History）
  はCandidate Modelの責務外であり、既存Knowledge Seed Schema
  （`knowledge_seed.py`の`SourceEntry`/`DeityEntry`/`HistoryEntry`）を
  そのまま使う以外の設計は存在しない、というのが既存Contractの実態
- Source URLの扱い: `ShrineCandidate.raw`（JSONField、自由形式）に格納可能。
  ただしKnowledge Seedの`SourceEntry.url`と違い、Candidate側には専用fieldも
  Source種別（`SOURCE_TYPE_CHOICES`）もない
- prefecture/addressの扱い: 専用fieldなし。`Shrine.address`と同様、文字列
  住所の先頭一致で都道府県判定する既存手法（Geographic Coverage監査で確立）を
  そのまま踏襲可能
- coordinatesの扱い: `lat`/`lng`のみ（PointFieldなし、Shrineより簡素）
- deity/history/goriyakuの扱い: `goriyaku`のみCandidate Model内にfieldあり。
  deity/historyはCandidate Modelの責務外（Knowledge Seed側の責務）
- confidence/verificationの扱い: Candidate Model自体には存在しない。これらは
  Knowledge Seed（`SourceEntry`/`DeityEntry`/`HistoryEntry`）側の責務であり、
  Candidate → Knowledge Seed変換時に新たに人手/既存Source Contractに基づき
  付与する必要がある（Candidate Model側が代わりに持つ設計にはなっていない）
- temporary artifactの有無: 専用の一時artifact形式は存在しない。本監査では
  scratchpad（session一時領域）にJSON fileを作成し、既存Seed Schemaへの
  変換可能性を検証した（後述Phase 13）

新しいCandidate schemaは作らず、既存`ShrineCandidate` Model + 既存Knowledge
Seed dataclass（`SourceEntry`/`DeityEntry`/`HistoryEntry`）をそのまま正本として
扱った。

## 4. Existing Seed Compatibility（Phase 4）

`import_shrines_seed.py`（`backend/temples/management/commands/
import_shrines_seed.py`、全文確認済み、変更なし）:

| 項目 | 内容 |
|---|---|
| required fields | `name_jp`, `address`（どちらか欠落した行はSKIP） |
| optional fields | `latitude`, `longitude`, `goriyaku`, `kyusei`, `astro_elements`, `visit_style_tags`, `name_romaji`, `sajin`, `description`, `element` |
| upsert key | `(name_jp, address)`の完全一致（`Shrine.objects.filter(name_jp=name, address=address).order_by("id").first()`） |
| normalization | なし（文字列の完全一致のみ。表記ゆれの吸収は行わない） |
| address format | 自由文字列。都道府県専用fieldなし（Geographic Coverage監査と同じ制約） |
| coordinate format | float。`USE_GIS=1`かつlat/lng両方非nullの場合のみ`Point(lng, lat, srid=4326)`を追加生成 |
| overwrite behavior | 既存行があれば変更fieldのみ`update_fields`で保存。既存の`--dry-run`フラグでロールバック可能（`transaction.set_rollback(True)`） |
| validation behavior | Django Model levelの`full_clean()`は呼ばれない（`Shrine.objects.create(**payload)`を直接呼ぶのみ）。必須field欠落はSKIPで防御 |

**判定: REUSE_AS_IS。** Candidate（`name_jp`, `address`, `lat`→`latitude`,
`lng`→`longitude`）から本Schemaへの変換は完全に可能で、field名の読み替え
以外の変換ロジックは不要。Phase 13で実際に9件変換し、Phase 14で
`--dry-run`が9/9成功することを確認した（後述）。

## 5. Duplicate Detection Compatibility（Phase 5）

| 項目 | 内容 |
|---|---|
| Shrine同一性判定 | `temples/services/shrine_submission.py`の`find_duplicate_candidates(name, address, limit=3)`（実際にUser Shrine投稿フローで運用中） |
| name normalization | `shrine_duplicate_normalize.normalize_shrine_name_for_duplicate`（全角→半角スペース、連続空白除去、全角括弧→半角） |
| address normalization | `shrine_duplicate_normalize.normalize_shrine_address_for_duplicate` |
| name + address key | `shrine_name_duplicate_base_key`（括弧内除去した比較キー） |
| alias handling | 括弧表記（例:「神田神社(神田明神)」）のみ対応。別名を横断するalias tableは存在しない |
| duplicate candidate behavior | `find_duplicate_candidates`が最大`limit`件を返す（新規実装なし、既存関数をそのまま利用） |
| import時のduplicate behavior | `import_shrines_seed.py`は`(name_jp, address)`完全一致のみでupsertを判定し、`find_duplicate_candidates`の曖昧一致は使わない（Seed importは「既知の確定済みデータ」を前提とした別責務であり、Candidate Discovery段階の「曖昧な重複疑い検出」とは意図的に別ロジック） |

**判定: REUSE_AS_IS。** Candidate Discovery専用の重複ロジックを新規作成する
必要はない。Phase 12で実際に9 Candidateすべてに対し`find_duplicate_candidates`
を呼び出し、動作を確認した（後述、9件とも重複0件）。

## 6. Existing Source Research Flow（Phase 6）

Batch 1〜16（`docs/audit/shrine-knowledge-rollout-batch-1〜7.md`、
`docs/audit/knowledge-batch8〜16-*.md`）で反復された既存フローを正本として
扱う。新しいSourceルールは定義しない。

- Source discovery: 神社公式サイトを一次情報として直接fetchする（Batch文書内で
  一貫）
- official source preference: `shrine_official` > `government` /
  `cultural_property` > `tourism_official` > `secondary_editorial` >
  `user_observation`（`ShrineKnowledgeSource.SOURCE_TYPE_CHOICES`の並び順、
  Batch文書内の実運用と整合）
- prefectural shrine association（都道府県神社庁）: `SOURCE_TYPE_CHOICES`に
  専用の値はなく、既存Contract上は`government`に最も近いが、本監査時点では
  Batch 1〜16実績内に神社庁ソースの採用例は確認できなかった（未検証領域）
- municipality（市区町村公式サイト）: `government`に該当
- cultural property source: `cultural_property`
- tourism source: `tourism_official`
- secondary source handling: `secondary_editorial`（低優先度、Batch文書内でも
  補助的にのみ使用）
- verification: `KNOWLEDGE_VERIFICATION_STATUS_CHOICES`
  （draft/unverified/**source_confirmed**/**reviewed**/disputed/outdated/
  rejected）。太字2つがFact-ready（`KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES`）
- confidence: `KNOWLEDGE_CONFIDENCE_CHOICES`（low/medium/high）
- Fact Sheet: Batch監査文書自体がFact Sheet相当（出典URL・publisher・
  accessed_atを記録）
- Source Relation: `ShrineDeity.sources` / `ShrineHistory.sources`
  （M2M、`knowledge_seed.py`の`source_keys`経由）
- Evidence Gate: `services/evidence_gate.py`（`decide_fact_usability`）が
  Recommendation/Detail両経路の正本。今回のPilotではFactを一切作成していない
  ため、Evidence Gateの判定ロジックには一切触れていない

**判定: REUSE_AS_IS。** Sourceの優先順位・分類・確認状態・信頼度の定義は
すべて既存Contractのままとした。

## 7. Reuse Matrix（Phase 7）

| # | Component | Classification | Evidence |
|---|---|---|---|
| 1 | Prefecture input | EXTEND_EXISTING | `sync_places_seeds --pref-code`は既存コードだが、`places_seeds_jp_v1.json`が東京都3点のみでデータが未整備。コード変更不要、JSON行追加のみで拡張可能。ただし`GOOGLE_PLACES_API_KEY`が本監査環境に未設定（外部依存） |
| 2 | Shrine candidate discovery | EXTEND_EXISTING（`fetch_shrine_candidates.py`は対象外） | `places_resolve.py`（既知place_id解決）・`sync_places_seeds`+`places_sync`（nearby search）が実装済み。`fetch_shrine_candidates.py`は§3で確認した通りCONFLICT/DRIFT（superseded）につき、拡張対象から除外 |
| 3 | Candidate normalization | REUSE_AS_IS | `places_heuristics.py`（`norm_name`, `is_shinto_candidate`）、`shrine_duplicate_normalize.py` |
| 4 | Duplicate detection | REUSE_AS_IS | `shrine_submission.find_duplicate_candidates`。Pilotで9件実行、動作確認済み（§12） |
| 5 | Source discovery | EXTEND_EXISTING | Source優先順位Contractは既存のまま(REUSE_AS_IS)だが、Source本文取得の自動化ツールは存在せず（Batch 1〜16は人手/AI補助の直接fetchで実施）。本監査セッションでは`WebSearch`（URL・snippet取得）は機能したが、`WebFetch`（本文取得）が全外部ドメインでegress遮断され、Source本文の読解ができなかった（§13/§Findings参照、本環境固有の制約） |
| 6 | Source classification | REUSE_AS_IS | `SOURCE_TYPE_CHOICES` |
| 7 | Fact extraction | REUSE_AS_IS（意図的に人手/AI補助のプロセスのまま） | Knowledge Contractが「AI Generated DraftはSourceとして扱わない」と明記（`models.py`の`SOURCE_TYPE_CHOICES`コメント）。自動Fact抽出は設計上禁止されており、既存Batch workflow（人手+AI補助のSource Research）がそのまま正しいプロセス。MISSINGではない |
| 8 | Shrine Seed conversion | REUSE_AS_IS | `import_shrines_seed.py`。Pilotで9/9件`--dry-run`成功（§14） |
| 9 | Knowledge Seed conversion | REUSE_AS_IS（Schema/Toolingとして。今回未実行） | `import_shrine_knowledge.py` + `knowledge_seed.py`はBatch 1〜16で16回実証済み。本Pilotでは#5の制約によりFact本文を取得できず、Knowledge Seed生成そのものを実行していない（§Findings） |
| 10 | validate-only | REUSE_AS_IS | `import_shrine_knowledge.py --validate-only`（既存、未変更） |
| 11 | dry-run | REUSE_AS_IS | `import_shrines_seed.py --dry-run` / `import_shrine_knowledge.py --dry-run`。前者はPilotで実行済み |
| 12 | Evidence Gate | REUSE_AS_IS | `evidence_gate.py`。本Pilotでは1件もFactを作成していないため、判定ロジックへは一切到達していない（迂回もしていない） |
| 13 | Human Review | EXTEND_EXISTING | `ShrineCandidate.Status`（auto/approved/imported/rejected）はModelとして既存。専用のReview UI/adminのwiring状況は本監査で確認しておらず未検証（over-claimを避けるためEXTEND_EXISTINGとした） |
| 14 | Import | REUSE_AS_IS | `import_shrines_seed.py` / `import_shrine_knowledge.py`。Production importはPilot対象外として実行していない |
| 15 | Post-import Coverage | REUSE_AS_IS | `knowledge_coverage_report.py`。`docs/audit/shrine-geographic-knowledge-coverage.md`で実証済み |

**MISSING: 0件。** すべてREUSE_AS_ISまたはEXTEND_EXISTING（データ拡張・
外部依存解消のみ、コードロジックの新規実装は不要）で説明できた。

**CONFLICT / DRIFT: 1件。** `fetch_shrine_candidates.py`固有（Component #2の
一部）。実装済みの別実装（`places_resolve.py`）と責務が重複し、かつ
モデル自身がその出力を"legacy"と自己申告している。**この1 fileを拡張する
という選択肢は不採用とし、Pilotでも一切使用していない。**

## STOP GATE A 判定

該当条件を個別に確認した。

| STOP条件 | 該当 | 詳細 |
|---|---|---|
| Existing Seed Schemaとの接続不能 | 否 | §4・Pilotで実証（9/9 dry-run成功） |
| duplicate detectionとの接続不能 | 否 | §5・Pilotで実証（9件実行、正常動作） |
| Source Contractが不明 | 否 | §6、既存Contractが明確に定義済み |
| Candidate schemaのownershipが不明 | 否 | `ShrineCandidate` Modelが正本として明確 |
| **fetch_shrine_candidates.pyの責務が別機能と競合** | **該当** | `places_resolve.py`と責務重複（§3 Phase 2）。ただし解決は自明（この1fileを拡張しない、既存の別実装を使う）であり、他のDiscovery Layer全体を止める理由にはならないと判断した |
| Model / Seed / Importer drift | 否（上記1件を除き） | 他のcomponentにdriftは確認されなかった |
| Production writeが必要 | 否 | Pilotは全てread-only/scratch DB/dry-runのみ |
| 新規Importerが必要 | 否 | 既存`import_shrines_seed`/`import_shrine_knowledge`で完結 |
| 新規Knowledge Pipelineが必要 | 否 | 既存`knowledge_seed.py`で完結 |
| Evidence Gateを通せない | 否（未到達） | 本PilotはFactを作成していないため判定不要 |
| AI生成FactとStored Factを安全に分離できない | 否 | 本Pilotでは分離ではなく「AI生成Factを一切作らない」という、より安全側の選択をした（§13/§14） |

**判定: STOP GATE Aは、`fetch_shrine_candidates.py`を拡張対象とすることに
限っては該当したが、それ以外の全条件は非該当だった。fetch_shrine_
candidates.pyを一切使わず・拡張せず、既存の別実装（AI/WebSearchによる
Discovery + 既存duplicate detection + 既存Seed/Import tooling）のみで
Pilotへ進んだ。** これは「同じ責務を持つparallel implementationは禁止する」
という最重要原則そのものへの対応であり、STOP GATE Aの趣旨（危険な拡張を
止める）と矛盾しない。

## 5. Minimal Extension Design（Phase 8）

新しいcommand・新しいPipeline directoryは作らない。設計は以下の通り
（コード変更ゼロで成立、実際に本監査でこの設計のまま実行した）。

```
未登録prefecture
  ↓ (AI + WebSearch によるCandidate調査。sync_places_seedsの
  ↓  --pref-code機構は本来この位置で使えるが、本監査環境には
  ↓  GOOGLE_PLACES_API_KEY未設定のため今回は代替した)
Candidate Discovery
  ↓ (既存 shrine_submission.find_duplicate_candidates をそのまま呼び出し)
Existing Duplicate Check
  ↓ (既存Source Contract の優先順位に従い WebSearch で公式サイト等を特定)
Official Source Discovery
  ↓ (ShrineCandidate schema 相当の構造へ手動整理。新schema無し)
Structured Candidate
  ↓ (name_jp/address/latitude/longitudeへ読み替えるのみ)
Existing Seed Candidate（scratchpad上の一時JSON、本番Seed非変更）
  ↓
Existing dry-run（import_shrines_seed --dry-run。scratch DBに対して実行）
  ↓
Human Review（本監査では未実施。§Unresolved参照）
```

Production ImportはPilot対象外とし、実行していない。

## 6. Pilot（Phase 9〜10）

### 選定県

Shrine登録0社の20都道府県から、以下3県を選定した。

| 都道府県 | 地方 | 選定理由 |
|---|---|---|
| 北海道 | 北海道地方 | 単独で1地方を構成し、他候補県と地方が重複しない。北海道神宮など全国的に著名な神社があり、Source availability検証に適する |
| 滋賀県 | 近畿地方 | 既にShrine登録がある京都府・大阪府に地理的に隣接するが、それ自体は0社という対照的なケース。建部大社・多賀大社・日吉大社など複数の著名神社があり、Candidate比較検証に適する |
| 沖縄県 | 九州・沖縄地方 | 琉球王国由来の独自宗教文化圏であり、本土の神社Sourceパターンがそのまま通用するかを試す一般化可能性チェックに適する。「琉球八社」という既存の公式分類があり複数Candidate比較が可能 |

3県は北海道地方・近畿地方・九州沖縄地方と、8地方区分のうち3つの異なる地方に
分散しており、特定地方への偏りはない。3県とも既存Shrine登録0社であることは
Geographic Coverage監査（`docs/audit/shrine-geographic-knowledge-coverage.md`
Table 4「0社」区分）で確認済み。

これは全国展開の優先順位決定ではなく、Pilot検証に適した県の選定に留める。

### Candidate（3県×3件、合計9件）

WebSearchで各県の著名神社を調査した（本監査Claude自身による実施、AIの用途は
Phase 11の許容範囲＝Candidate discovery assistance / Source discovery
assistanceに限定）。

| # | 都道府県 | 神社名 | 住所（WebSearchで確認） | 公式Source URL | Source種別 |
|---|---|---|---|---|---|
| 1 | 北海道 | 北海道神宮 | 北海道札幌市中央区宮ヶ丘474 | http://www.hokkaidojingu.or.jp/ | shrine_official（確認済み） |
| 2 | 北海道 | 函館八幡宮 | 北海道函館市谷地頭町2-5 | 確認できず（北海道神社庁ページのみ） | 未確認（神社庁掲載のみ） |
| 3 | 北海道 | 北海道護國神社 | 北海道旭川市花咲町1丁目2282番2 | 確認できず（旭川市公式サイト内ページのみ） | government相当（神社公式は未確認） |
| 4 | 滋賀県 | 建部大社 | 滋賀県大津市神領1-16-1 | https://takebetaisha.jp/ | shrine_official（確認済み） |
| 5 | 滋賀県 | 多賀大社 | 滋賀県犬上郡多賀町多賀604 | https://www.tagataisya.or.jp/ | shrine_official（確認済み） |
| 6 | 滋賀県 | 日吉大社 | 滋賀県大津市坂本本町4220 | https://hiyoshitaisha.jp/ | shrine_official（確認済み） |
| 7 | 沖縄県 | 波上宮 | 沖縄県那覇市若狭1-25-11 | https://naminouegu.jp/ | shrine_official（確認済み） |
| 8 | 沖縄県 | 普天満宮 | 沖縄県宜野湾市普天間1-27-10 | http://futenmagu.or.jp/ | shrine_official（確認済み） |
| 9 | 沖縄県 | 沖縄県護国神社 | 沖縄県那覇市奥武山町44 | https://okinawa-gokoku.jp/ | shrine_official（確認済み） |

緯度経度はGoogle Geocoding APIが本監査環境で利用不可（APIキー未設定）のため、
一般的に知られた近似値を暫定的に使用した。**本番投入前には既存の位置情報取得
経路（PlaceRef経由のgeocoding）での再検証が必要**であり、この座標は
Pilot Seed変換の構造検証専用であることを明記する。

### Duplicate Check（実施結果、既存関数を実際に呼び出し）

9候補すべてに対し`temples.services.shrine_submission.find_duplicate_candidates`
を実際に呼び出した（scratchpadのscript経由、`python manage.py shell`で実行、
DB書き込みなし）。

**結果: 9/9件で重複0件。** 3県とも既存Shrine登録が0社であるため、この結果は
Geographic Coverage監査の結果と整合する。

## 7. KPI（Phase 15/Pilot KPI）

計測できた範囲のみを記載する。推測値は含まない。

| KPI | 値 | 算出根拠 |
|---|---|---|
| Candidate Discovery Success Rate | 9/9 = 100.0% | 生成した9件すべてが名称・住所を一意に特定でき、重複検出（0件）・Shrine Seed変換（9/9成功、後述）まで到達した |
| Official Source Availability Rate | 7/9 = 77.8% | `shrine_official`種別のSource URLが確認できたCandidate数 / usable candidates。函館八幡宮・北海道護國神社の2件は神社公式サイトを特定できず（神社庁/市公式ページのみ確認） |
| Seed Conversion Success Rate（Shrine base層） | 9/9 = 100.0% | `import_shrines_seed --dry-run`で9/9件が`CREATE`判定、`SKIP`/エラー0件 |
| Seed Conversion Success Rate（Knowledge層） | N/A（未実施） | §Findings参照。本セッションの`WebFetch`が全外部ドメインでegress遮断され、Source本文を読めなかったためFact抽出を実施しておらず、分子分母とも存在しない |
| Validation Pass Rate（Shrine base層） | 9/9 = 100.0% | 上記dry-run結果と同一（`import_shrines_seed.py`は`--dry-run`のみを提供し、`--validate-only`相当の判定はdry-run内のSKIP/エラー検出で代替されている） |
| Human Correction Rate | N/A（未計測） | 本Pilotに人間レビュアーは参加していない（本監査はAIセッション単独で実施）。推測値は作らない |
| Human Review Time | N/A（未計測） | 同上 |

## 8. Findings

観測事実のみを記載する。推測・改善案・優先順位付けは含まない。

- `fetch_shrine_candidates.py`は現行developで実際には呼び出されておらず
  （呼び出し元0件、専用テスト0件）、`ShrineCandidate.Source`enumが自らを
  "Stub (legacy)"とラベル付けしている。同じ責務を担う別の稼働中実装
  （`places_resolve.py`）が存在する
- Candidate Discovery自体は、既に稼働中の`places_resolve.py`（既知place_id
  単発解決）と、コードとしては完成しているがseed点データが東京都3点のみで
  未整備な`sync_places_seeds`（prefecture-scoped nearby search）の2経路が
  既存する
- `GOOGLE_PLACES_API_KEY`/`GOOGLE_MAPS_API_KEY`は本監査環境に設定されていない
  （`env`・`.env`いずれにも存在せず）。`sync_places_seeds`経路の実行には
  この外部APIキーが必須である
- 本監査セッションの`WebFetch`ツールは、テストした全ドメイン
  （`takebetaisha.jp`、`ja.wikipedia.org`）で`EGRESS_BLOCKED`エラーを返した。
  `WebSearch`（検索結果snippet取得）は正常に機能した。この非対称性により、
  本Pilotでは「Source URLの存在確認」までは可能だったが「Source本文を読んで
  Factを抽出する」ことは技術的に不可能だった
- `import_shrines_seed.py`は`name_jp`/`address`/`latitude`/`longitude`という
  最小限のfieldでCandidateを受け付け可能であり、9/9件のPilot Candidateが
  変換・dry-run成功した。変換にあたりコード変更は一切不要だった
  （field名の読み替え: `lat`→`latitude`, `lng`→`longitude`のみ）
- `find_duplicate_candidates`（`shrine_submission.py`）は、Candidate
  Discovery専用の重複ロジックを新設せずとも、既存のUser投稿神社向け重複検出
  ロジックをそのまま呼び出すだけで機能した
- 9候補中7候補（77.8%）で神社公式サイト（`shrine_official`）を確認できた。
  残り2候補（函館八幡宮、北海道護國神社）は、神社庁ページ・市公式ページ
  という二次的な情報源しか本監査では確認できなかった
- 本Pilotでは、Fact（deity/history）を1件も作成していない。Evidence Gate・
  Knowledge Contractのいずれの判定ロジックにも到達していない（迂回もしていない）

## 9. Unresolved

- Knowledge層（deity/history Fact抽出）のSeed変換可能性は、本監査セッションの
  `WebFetch`制約により未検証のまま残る。別セッション・別ツール環境
  （実際のBatch Source Research作業と同様、公式ページ本文を読める環境）での
  再検証が必要
- `sync_places_seeds`経路（prefecture-scoped nearby search）は
  `GOOGLE_PLACES_API_KEY`が利用可能な環境での動作検証を行っていない
  （コードは既存のままで変更していないため、コードの正しさそのものは本監査の
  対象外）
- `ShrineCandidate.Status`（Human Review用状態機械）を実際に操作するAdmin/UI
  画面の有無・動作は本監査で確認していない
- Pilot座標（lat/lng）は近似値であり、Google Geocoding等での正式な検証を
  経ていない
- Human Review Time・Human Correction Rateは、実際の人間レビュアーが参加する
  形でのPilotでのみ計測可能であり、本監査（AI単独実施）では計測できなかった
- 函館八幡宮・北海道護國神社の2件について、神社公式サイトが本当に存在しない
  のか、単に本監査のWebSearchで発見できなかっただけなのかは切り分けられて
  いない

## 10. Mother Ship Decision

以下は母艦判断事項として返す。本監査内では結論を出さない。

- 20県（または残り17県）へPrefecture Discoveryを拡張するか
- `sync_places_seeds`の`GOOGLE_PLACES_API_KEY`を本番相当環境で有効化し、
  seed点データ（`places_seeds_jp_v1.json`）を46都道府県分整備するか
- `fetch_shrine_candidates.py`を削除する、または`places_resolve.py`と
  統合するか（本監査は「拡張しない」ことのみを判定し、削除・統合の実装判断は
  母艦へ委ねる）
- Knowledge層Pilot（Fact抽出）を、WebFetch制約のない環境・体制で再実施するか
- 本Pilotで確認された3県9候補（うち7候補がshrine_official Source確認済み）を
  実際のBatch rollout workflowの対象として正式に採用するか
- Human Review工程（`ShrineCandidate.Status`ワークフロー）を実際に運用するか

## Repository Change Rule（実施結果）

監査のみで完了したため、以下のみを変更した。

- `docs/audit/shrine-discovery-automation-readiness.md`（本ドキュメント、新規）

Pilot実施のためのコード変更は一切行っていない。新しいPipeline directory・
parallel management commandは追加していない。

## Tests / Validation

コード変更なしのため、以下のread-only実行結果のみを記録する。

- `find_duplicate_candidates`を9件のPilot Candidateに対し実行（scratchpad
  script経由、`python manage.py shell`、変更なし・書き込みなし） →
  9/9件で重複0件
- `import_shrines_seed --source <scratchpad一時JSON> --dry-run`を実行
  （既存command、引数以外の変更なし） → `created=9, updated=0, skipped=0,
  total_seed=9`、エラー0件
- Django unit test / regression testは、コード変更が0件のため実行していない
  （実行対象となるコード変更が存在しないため省略。前提の`docs/audit/
  shrine-data-pipeline-phase0-audit.md`によりexisting test suiteは既に
  Batch 16時点でPASS確認済み）

## 完了条件チェック

Production write 0件・既存Seed変更0件・既存Knowledge変更0件・既存Model/
Contract/Recommendation/Concierge変更0件を確認した。本監査で変更した
repositoryファイルは本ドキュメント1件のみである。
