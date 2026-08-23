> **Status: `FACT_GENERATION_PILOT_VALIDATE_ONLY_PASS_DRY_RUN_PASS_EVIDENCE_GATE_ALL_USABLE`。**
>
> 本監査はread-only + scratch DB限定のPilotである。Production DBへの書き込み、
> 既存Shrine Seed / Knowledge Batch Seed / Model / Migration / Serializer /
> Evidence Gate / Recommendation / Ranking / Concierge / Knowledge Contractの
> 変更は一切行っていない。新しいKnowledge Pipeline・新しいFact Schema・
> 新しいImporterも作っていない。
>
> **要旨**: 北海道神宮・建部大社・波上宮の3社について、事前にSource本文確認・
> Calibration済みとして与えられたFact Candidate（Deity 12件、History 11件、
> Source 4件）を、既存Knowledge Seed Schemaへ機械的に変換した。role・
> history_type・verification_status・confidence・Source relationの意味は
> 一切再解釈していない。`import_shrine_knowledge --validate-only`・
> `--dry-run`はいずれもPASSし、既存Evidence Gate（`decide_fact_usability`、
> 未変更）を通した結果**23/23 Factすべてがusable=True**だった。既存Pipelineを
> 変更せずに3社分のKnowledge投入が構造的に成立することを確認した。

# Shrine Knowledge Fact Generation Pilot

## Objective

北海道神宮・建部大社・波上宮の3社について、ChatGPT側でSource本文確認・
Calibration済みとして提供されたFact Candidateを、既存Knowledge Pipeline
（Seed Schema → validate-only → dry-run → Evidence Gate整合確認）へ接続し、
既存Pipelineの変更なしで安全に扱えるかを検証する。Production importは
行わない。

## 作業ブランチ / 前提確認

| 項目 | 結果 |
|---|---|
| 作業branch | `audit/shrine-knowledge-fact-generation-pilot`（`origin/develop`から新規作成、専用branch） |
| `audit/shrine-dataset-integrity`への変更 | なし（このbranchはローカルに存在しないため、そもそも触れる対象がない） |
| origin/develop最新化 | 確認済み（`git fetch origin develop`後にbranch作成。HEAD=`e9d4aa1 docs: Shrine Knowledge Source取得・Fact生成PilotでSTOP GATE Aを記録 (#2531)`） |
| working tree clean | 確認済み |
| Phase 0 Shrine Data Pipeline Audit | `docs/audit/shrine-data-pipeline-phase0-audit.md`、develop存在確認済み |
| Geographic / Knowledge Coverage Audit | `docs/audit/shrine-geographic-knowledge-coverage.md`、develop存在確認済み |
| Discovery Automation Readiness Audit | `docs/audit/shrine-discovery-automation-readiness.md`、develop存在確認済み |
| Source Acquisition Readiness Audit | `docs/audit/shrine-knowledge-source-automation-readiness.md`、develop存在確認済み |
| existing Knowledge importer | `backend/temples/management/commands/import_shrine_knowledge.py`存在確認済み |
| existing Knowledge Seed Schema | `backend/temples/services/knowledge_seed.py`存在確認済み |
| Evidence Gate | `backend/temples/services/evidence_gate.py`存在確認済み |
| Batch 16 Seed | `backend/temples/data/knowledge_seeds/batch_16_seed.json`存在確認済み |

前提はすべて満たされたため、Phase 1へ進んだ。

## Calibration

### Existing Schema（Phase 1、`batch_16_seed.json`実物 + `knowledge_seed.py`のparser実装から確認）

- top-level: `schema_version`（文字列、`parse_seed`は`"1.0"`と厳密一致でのみ受理）、
  `sources`（**list**、各要素に`key`フィールドを持つ。dictではない）、`shrines`（list）
- `sources[i]`: `key`（必須・一意）, `source_type`（`SOURCE_TYPE_CHOICES`のいずれか）,
  `title`（必須）, `publisher`, `url`, `bibliography`, `accessed_at`（Date）,
  `verified_at`（DateTime、`verification_status`が`source_confirmed`/`reviewed`の
  場合は必須）, `verification_status`, `confidence`, `language`, `note`
- `shrines[i]`: `shrine_ref`（`name_jp`必須, `address`）, `deities`（list）,
  `histories`（list）
- `deities[i]`: `display_name`（必須）, `canonical_name`, `role`
  （`ROLE_CHOICES`: primary/enshrined/secondary/unknown）, `sort_order`,
  `verification_status`, `confidence`, `verified_at`, `note`, `source_keys`
  （list、`sources`の`key`を参照。未知keyはエラー）
- `histories[i]`: `history_type`（`HISTORY_TYPE_CHOICES`:
  official_origin/founding/historical_event/tradition/regional_context/
  editorial_summary）, `title`（必須）, `content`（必須）, `period_text`,
  `event_date`（Date）, `sort_order`, `verification_status`, `confidence`,
  `verified_at`, `note`, `source_keys`

新しいSchemaは作らず、上記を完全に踏襲した。

### Model / Batch 16実例からの確認事項

- `_validate_verified_at_consistency`（`models.py`）により、
  `verification_status`が`source_confirmed`の場合、Source・Deity・History
  いずれも`verified_at`が必須。`batch_16_seed.json`ではSourceの`verified_at`と
  同一timestampを、そのSourceを参照する全FactのFactレベル`verified_at`
  にもコピーする運用が確認できた（例: `2026-08-12T07:00:00+00:00`が
  Source・Deity・History全件に共通）。本Pilotでも同じ運用を踏襲し、
  4 Source全件・23 Fact全件に`2026-08-23T07:00:00+00:00`（本監査実施日の
  固定UTC時刻、Pilot内で一貫）を設定した
- `enshrined`実例: 波上宮の6 deityのうち3件（火神・産土神・少彦名神）に
  `role: "enshrined"`を使用した。これは提供されたFact Candidateの指定通りで
  あり、既存Contract（`ROLE_CHOICES`）にそのまま含まれる値である。Codex側で
  roleを再判定・変更していない
- `event_date`/`period_text`実例: 全11 Historyとも`event_date: null`のまま
  （提供されたFact Candidateが`event_date: null`と明記していたものをそのまま
  使用）。年代情報はすべて`period_text`（自由記述、伝承由来の粒度を保持）へ
  収めており、Codex側で`event_date`を独自に埋めていない

## Candidate Summary

| Shrine | Source | Deity | History |
|---|---:|---:|---:|
| 北海道神宮 | 1（`hokkaido-jingu-official-history`） | 4 | 3 |
| 建部大社 | 2（`takebe-taisha-official-about`, `takebe-taisha-japan-heritage`） | 2 | 3 |
| 波上宮 | 1（`naminoue-gu-official-history`） | 6 | 5 |
| **合計** | **4（一意key）** | **12** | **11** |

## Phase 2: Shrine Base Existence

3社ともscratch DB（本監査専用のlocal PostgreSQL、Production DBとは別。
`docs/audit/shrine-geographic-knowledge-coverage.md`/
`shrine-discovery-automation-readiness.md`で構築したものと同一の環境を継続
使用）に存在しないことを確認した（`Shrine.objects.filter(name_jp=...)`が
3社とも0件）。既存`import_shrines_seed`（変更なし）を使い、前回Discovery
Pilotで確認済みのCandidate情報（`name_jp`/`address`/近似座標）から
scratch DBにのみ3社を作成した（`created=3, updated=0, skipped=0`）。
**Production Seed（`shrines_seed_clean.json`）・Production DBへは一切
追加していない。**

## Sources（Phase 3、既存Seed Schemaへの変換のみ、内容は与えられたまま）

| key | source_type | publisher | verification_status | confidence |
|---|---|---|---|---|
| `hokkaido-jingu-official-history` | shrine_official | 北海道神宮 | source_confirmed | high |
| `takebe-taisha-official-about` | shrine_official | 建部大社 | source_confirmed | high |
| `takebe-taisha-japan-heritage` | government | 日本遺産ポータルサイト | source_confirmed | high |
| `naminoue-gu-official-history` | shrine_official | 波上宮 | source_confirmed | high |

## Fact Candidate（Phase 4〜6、既存Schemaへの機械変換のみ）

提供されたFact Candidate（北海道神宮4 deity/3 history、建部大社2 deity/
3 history、波上宮6 deity/5 history）を、既存`SourceEntry`/`DeityEntry`/
`HistoryEntry`のfield名・型にそのまま対応させた。deity role・history_type・
verification_status・confidence・Source relation・title・content・
period_textはいずれも提供された値をそのまま使用し、Codex側で意味の
再解釈・変更を一切行っていない（`verified_at`の付与のみ機械的に追加、
上記Calibration節参照）。

## Phase 7: Scratch Seed生成

`schema_version: "1.0"`、上記4 Source + 3 Shrine blockのみを含む
scratch Knowledge Seed JSONを、このセッションのscratchpad
（`/tmp/.../scratchpad/fact_pilot_knowledge_seed.json`）にのみ生成した。
**commit対象外**であり、本PRには含まれていない。Production Seed
（`backend/temples/data/knowledge_seeds/batch_*.json`）への追記・変更は
一切行っていない。

## Validation（Phase 9: validate-only）

```
$ python manage.py import_shrine_knowledge <scratch_seed.json> --validate-only
validate-only: OK, no errors
```

**結果: PASS。** 構造検証（schema_version一致、必須field充足、
source_keys解決、role/history_type/verification_status/confidence値検証、
`verified_at`整合性）・shrine identity解決（3社とも一意に解決）のいずれも
エラー0件だった。

## Dry-run（Phase 10）

```
$ python manage.py import_shrine_knowledge <scratch_seed.json> --dry-run
[source] CREATE ×4
[deity] CREATE ×12（北海道神宮4・建部大社2・波上宮6）
[history] CREATE ×11（北海道神宮3・建部大社3・波上宮5）
plan summary: {'source_CREATE': 4, 'deity_CREATE': 12, 'history_CREATE': 11}
dry-run: OK, no DB writes performed
```

**結果: PASS。** 全23 Fact + 4 SourceがすべてCREATE判定（新規、
SKIP_EXISTS/CONFLICT/AMBIGUOUSは0件）で、エラー0件・DB書き込み0件。
scratch DB以外（Production DB含む）への接続・書き込みは行っていない。

## Evidence Gate（Phase 11）

既存`evidence_gate.decide_fact_usability`（コード変更なし）を、
パース済みのscratch Seedの全23 Fact（各Factのverification_status・
confidence・関連source_keysのSource verification_status）に対して実際に
呼び出した。

```
total facts: 23, usable: 23, suppressed: 0
```

**結果: 23/23 Factが`usable=True`, `display_mode="full"`,
`reason_strength="assertive"`。** 全FactのSourceが`source_confirmed`で
あり、Fact自身も`source_confirmed`であるため、既存Evidence Gate契約
（`docs/knowledge/shrine-knowledge-contract.md`の「Evidence Gate要件」）
上、Recommendation/Shrine Detail両経路でそのまま利用可能と判定された。
disputed・suppressed・想定外のhiddenは0件だった。Evidence Gateのコードは
一切変更していない。

## Phase 12: Validation Result

| Shrine | Source | Deity | History | validate-only | dry-run | Evidence Gate |
|---|---:|---:|---:|---|---|---|
| 北海道神宮 | 1 | 4 | 3 | PASS | PASS（CREATE ×4 deity, ×3 history） | 7/7 usable |
| 建部大社 | 2 | 2 | 3 | PASS | PASS（CREATE ×2 deity, ×3 history） | 5/5 usable |
| 波上宮 | 1 | 6 | 5 | PASS | PASS（CREATE ×6 deity, ×5 history） | 11/11 usable |
| **合計** | **4** | **12** | **11** | **3/3 PASS** | **3/3 PASS** | **23/23 usable** |

## Deviations（既存Contractとの差異）

**差異なし。** 提供されたFact CandidateのSchema・値はすべて既存Contract
（`ROLE_CHOICES`, `HISTORY_TYPE_CHOICES`, `KNOWLEDGE_VERIFICATION_STATUS_CHOICES`,
`KNOWLEDGE_CONFIDENCE_CHOICES`, `SOURCE_TYPE_CHOICES`）の範囲内に収まって
おり、Codex側で追加した唯一の要素は`verified_at`（Batch 16実例と同じ運用
パターンでの機械的付与）のみである。deity role・history_type・
Source classification・verification_status・confidence・Source relation・
title・content・period_textは一切変更していない。

## Production Safety

`git status --short` / `git diff --stat`で確認した。

| 項目 | 結果 |
|---|---|
| Production write | 0（scratch DBのみ操作。Production DB・Production環境への接続は一切なし） |
| Existing Shrine Seed change | 0（`shrines_seed_clean.json`等への変更なし） |
| Existing Knowledge Seed change | 0（`batch_1_7_seed.json`〜`batch_16_seed.json`への変更なし） |
| Model change | 0 |
| Migration change | 0 |
| Serializer change | 0 |
| Evidence Gate change | 0 |
| Recommendation / Ranking change | 0 |
| Concierge change | 0 |
| Knowledge Contract change | 0 |
| 新規Importer / 新規Pipeline / 新規Fact Schema | 0（既存`import_shrine_knowledge`・既存Seed Schemaをそのまま使用） |

本PRのrepository変更は`docs/audit/shrine-knowledge-fact-generation-pilot.md`
（本ドキュメント）1件のみである。scratch Seed JSON・Evidence Gate検証scriptは
いずれもこのセッションのscratchpad（`/tmp/...`）にのみ存在し、commit対象外。

## Tests / Validation

コード変更が0件のため、Django unit test / regression testは実行対象が
存在せず省略した（前提の`docs/audit/shrine-data-pipeline-phase0-audit.md`
によりexisting test suiteはBatch 16時点でPASS確認済み）。本Pilot自体の
検証は上記`--validate-only`・`--dry-run`・Evidence Gate直接呼び出しの
3つの既存read-onlyパスで行った。

## Findings

- 提供された3社23 Factは、既存Knowledge Seed Schema・既存Import
  command・既存Evidence Gateのいずれに対しても変更なしで完全に機能した
- `verified_at`の付与（Batch 16実例と同一パターン）以外、既存Contractへの
  適合のために必要な変換・調整は一切発生しなかった
- 波上宮の`role: "enshrined"`3件（火神・産土神・少彦名神、公式サイトが
  「別鎮斎」として本殿祭神3柱と区分掲載）は、既存Contractの`enshrined`
  区分をそのまま使用でき、新しいrole値・新しい区分ロジックは不要だった
- 建部大社の遷座年（公式=天武天皇期、行政Source=天武天皇4年・676年「伝わる」
  と明記）という2 Source間の粒度差は、`event_date`を確定させず
  `period_text`の自由記述内に両方の情報を保持することで、既存Contract上
  「解決不能な競合」ではなく「粒度の異なる同一tradition」として素直に
  表現できた。新しい競合解決ロジックは不要だった
- Evidence Gateは23/23 Factを`usable=True`と判定した。これは全FactがSource
  ありの`source_confirmed`であるという、Evidence Gate契約が要求する最も
  単純な条件を満たしているためであり、Evidence Gate側の特別な調整は不要
  だった

## Environment Constraints

前Pilot（`docs/audit/shrine-knowledge-source-automation-readiness.md`）で
確認したネットワークegress制約（`WebFetch`/`curl`が外部ドメインへ到達
不能）は、本Pilotには影響しなかった。Source本文確認は本Pilot開始前に
外部（ChatGPT側）で完了済みという前提で作業したためである。本監査は
Source本文の真正性そのものを再検証していない点に留意する（Codexの役割は
既存Schemaへの機械的変換とPipeline適合性検証のみであり、Source本文の
Authority検証は本Pilotのスコープ外）。

## Mother Ship Decision

以下を母艦へ返す。本監査内では結論を出さない。

- このFact生成方法（外部でSource確認済みのFact Candidateを既存Schemaへ
  機械変換 → validate-only → dry-run → Evidence Gate確認）を次Batchへ
  正式に再利用可能か
- 20都道府県（`docs/audit/shrine-geographic-knowledge-coverage.md`で
  確認済みの登録0社県）へのExpansionへ進めるか
- 1 Batchあたり何社を対象にするか（今回は3社、Batch 1〜16の実績は
  1〜7社/Batch）
- Human Review工程をどの地点に置くか（Source本文確認自体は既に外部で
  実施済みという前提のため、本Pilotの範囲では「Codex側の機械変換結果の
  レビュー」が残るHuman Reviewポイントとなる）
- 本Pilotの3社（北海道神宮・建部大社・波上宮）を実際のProduction
  Batch（Batch 17相当）として正式採用し、Production importへ進めるか

全国展開の最終判断は本PRでは行わない。
