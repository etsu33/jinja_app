> **Status: `STOP_GATE_A_TRIGGERED_SOURCE_CONTENT_ACCESS_BLOCKED`。**
>
> 本監査はread-only auditである。Production DBへの書き込み、既存Shrine Seed /
> Knowledge Batch Seed / Model / Migration / Serializer / Evidence Gate /
> Recommendation / Ranking / Concierge / Knowledge Contractの変更は一切
> 行っていない。新しいKnowledge Pipeline・新しいFact Schema・新しいImporterも
> 作っていない。
>
> **要旨**: Pilot対象5社すべてについてSource discovery（WebSearchによる候補
> 特定）までは完了したが、**Source本文の取得（Content Acquisition）が本監査
> セッションで技術的に不可能**であることが判明した（`WebFetch`は全ドメインで
> `EGRESS_BLOCKED`、素の`curl`もproxy層で`CONNECT tunnel failed, response
> 403`）。これは5/5社・計5 URLで再現した。最重要原則「Source本文で確認できない
> Factを生成してはならない」に従い、**STOP GATE A（Source Access）を全Pilot
> shrineに対して発動し、Phase 6（Fact Extraction）以降には一切進んでいない。**
> Fact Candidateは1件も生成していない。これは失敗ではなく、Knowledge
> Contractが安全に機能した結果として記録する。

# Shrine Knowledge Source Acquisition & Fact Generation Pilot

## 1. Objective

`docs/audit/shrine-discovery-automation-readiness.md`（PR #2530）で選定・
duplicate check済みの3県9 Candidateから対象を絞り、信頼できるSource本文を
取得した上で既存Shrine Knowledge Contractに従いShrineKnowledgeSource /
ShrineDeity / ShrineHistoryのFact Candidateを生成し、既存Knowledge Seed
Schemaへ変換して`--validate-only`・`--dry-run`まで実行できるかを検証する。
新しいKnowledge Pipelineの構築、Production DBへの書き込みは行わない。

## Branch / Start

| 項目 | 結果 |
|---|---|
| PR #2530のdevelopへのmerge | 確認済み（`origin/develop` HEAD直下に`8a680f1 docs: Shrine Discovery自動化Readiness監査とConditional Pilotを実施 (#2530)`） |
| 作業開始時のbranch | `audit/shrine-discovery-automation-readiness`（前タスクの残branch） |
| working tree | clean |
| origin/developとの差分 | branch作成前は差分なし（前PRがmerge済みのため） |
| 作成したbranch | `audit/shrine-knowledge-source-automation-readiness`（`origin/develop`から新規作成） |

## 2. Preconditions（確認結果）

| 項目 | 結果 |
|---|---|
| `docs/audit/shrine-data-pipeline-phase0-audit.md` | 存在確認済み |
| `docs/audit/shrine-geographic-knowledge-coverage.md` | 存在確認済み |
| `docs/audit/shrine-discovery-automation-readiness.md` | 存在確認済み |
| PR #2530の内容がdevelopへ存在 | 確認済み |
| Pilotで使用したShrine Candidatesの特定 | 可能（前Pilotの3県9 Candidate、§5参照） |
| 既存Knowledge Batch 1〜16のSeed確認 | 確認済み（`backend/temples/data/knowledge_seeds/batch_1_7_seed.json`〜`batch_16_seed.json`、Phase 0監査で参照済み） |
| `import_shrine_knowledge`の現行CLI contract確認 | 確認済み（`--validate-only`/`--dry-run`/実行の3段構成、Phase 0監査で全文確認済み） |
| existing Knowledge Coverage tooling確認 | 確認済み（`knowledge_coverage_report`、Geographic Coverage監査で実測済み） |

前提はすべて満たされたため、Phase 1へ進んだ。

## 3. Existing Source Research Flow（Phase 1）

Batch 1〜16（`docs/audit/shrine-knowledge-rollout-batch-1〜7.md`、
`docs/audit/knowledge-batch8〜16-*.md`）を確認した結果、Source本文の取得は
一貫して「担当者（人手／AI補助）が対象神社の公式サイト等を直接fetchする」
という運用であり、**repository内にSource本文取得を自動化する専用の
management command・helper scriptは存在しない**（`requests.get`/
`urllib.request`/`httpx.get`をKnowledge Source研究目的で使うコードを検索したが
該当なし。`geocode.py`のみ該当したが座標変換用でSource Researchとは無関係）。
batch-7監査文書には「複数回の直接fetchでも公式ページで確認できず」という
記述があり、Source本文取得はBatchごとの担当セッションが持つ外部アクセス能力
（Webブラウジング）に依存していたことが確認できる。

各Source typeの既存Contract上の扱い（新しいルールは作らず、以下のまま採用）:

| Source type | 既存Contract上の扱い |
|---|---|
| Shrine official website | `shrine_official`。最優先 |
| prefectural shrine association（都道府県神社庁） | `SOURCE_TYPE_CHOICES`に専用値なし。最も近いのは`government`だが、Batch 1〜16実績内に採用例は確認できず（Discovery監査でも同じ結論） |
| municipality | `government` |
| government / cultural property | `government` / `cultural_property` |
| tourism official | `tourism_official` |
| local history | `local_history` |
| secondary editorial | `secondary_editorial`（低優先度） |
| Wikipedia | **`SOURCE_TYPE_CHOICES`に専用値が存在しない**。強いて分類するなら`secondary_editorial`が最も近いが、既存Contractの禁止事項（本書§最重要原則/前task指示）は「Wikipedia単独でStored Factを確定しない」と明記しており、単独Sourceとしては採用しない |

## 4. Source Contract（Phase 2）

`ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory`（`backend/temples/
models.py`、現行developより全文確認、変更なし）。

**ShrineKnowledgeSource**: `source_type`（10種、上表）、`title`（必須）、
`publisher`、`url`（URLField）、`bibliography`、`accessed_at`（Date）、
`verified_at`（DateTime）、`verification_status`（
draft/unverified/**source_confirmed**/**reviewed**/disputed/outdated/
rejected）、`confidence`（low/medium/high/未設定）、`language`、`note`。
`clean()`が`verification_status`がFact-ready
（`source_confirmed`/`reviewed`）の場合に`verified_at`必須をvalidateする。

**ShrineDeity**: `display_name`（必須）、`canonical_name`、`role`（
primary/enshrined/secondary/unknown）、`sort_order`、`sources`
（M2M→ShrineKnowledgeSource）、`verification_status`、`confidence`、
`verified_at`、`note`。

**ShrineHistory**: `history_type`（
official_origin/founding/historical_event/tradition/regional_context/
editorial_summary）、`title`、`content`（必須）、`period_text`、
`event_date`、`sort_order`、`sources`（M2M）、`verification_status`、
`confidence`、`verified_at`、`note`。

**判定: 既存enumで完全に表現可能。** 必要なtypeが存在しないケースは、
Pilot対象5社のいずれについても確認されなかった（Wikipedia除外は既存
禁止事項の範囲内であり、type不足の問題ではない）。

## 5. Pilot Shrines（Phase 3）

`docs/audit/shrine-discovery-automation-readiness.md`の3県9 Candidate
（すべてduplicate check済み、重複0件）から、以下5社を選定した。

| # | 都道府県 | 神社 | 選定理由 |
|---|---|---|---|
| 1 | 北海道 | 北海道神宮 | 公式サイトのURLが既に判明しており（`http://www.hokkaidojingu.or.jp/`）、Source取得難易度が低いと想定されるケース |
| 2 | 北海道 | 函館八幡宮 | 前Pilotで神社公式サイトを特定できなかった（神社庁ページのみ確認）候補。「公式Sourceが弱い可能性のあるCandidate」を意図的に1件含める |
| 3 | 滋賀県 | 建部大社 | 北海道と異なる地方（近畿）、公式サイト確認済み（`https://takebetaisha.jp/`） |
| 4 | 沖縄県 | 波上宮 | 北海道・滋賀と異なる地方（九州・沖縄）かつ琉球王国由来の独自宗教文化圏。本土の神社と異なる史料体系での再現性チェック |
| 5 | 沖縄県 | 沖縄県護国神社 | 同じ沖縄県内でも性質が異なる神社（護国神社＝戦没者慰霊）を含め、history_type分類（`historical_event`寄りになりやすい）のvarianceを見る |

3県4地方（北海道地方・近畿地方・九州沖縄地方のうち3つ、沖縄県は同一県内で
2社）にまたがり、Source取得難易度に意図的なvariance（強4件・弱1件）を持たせた。
全国展開の優先順位決定ではなく、Source/Fact Pipeline検証用の選定に留める。

## 6. Source Acquisition Results（Phase 4〜5）

WebSearchで各Shrineの候補Sourceを探索した（Phase 4、Discovery監査と同一の
Claude自身によるAI補助Discoveryを流用）。続けて、候補となったURL全件に対し
実際に`WebFetch`で本文取得を試み、Phase 5「URLが存在する ≠ Source本文を
確認できた」の区分に従って状態を記録した。

| Shrine | Source | Type候補 | Fetch試行 | 状態 |
|---|---|---|---|---|
| 北海道神宮 | http://www.hokkaidojingu.or.jp/ | shrine_official | `WebFetch`実行 | `EGRESS_BLOCKED`（domain: www.hokkaidojingu.or.jp） → **SOURCE_EXISTS_BUT_UNREACHABLE** |
| 函館八幡宮 | https://hokkaidojinjacho.jp/函館八幡宮/（北海道神社庁） | government相当（神社庁専用typeなし） | `WebFetch`実行 | `EGRESS_BLOCKED` → **SOURCE_EXISTS_BUT_UNREACHABLE** |
| 建部大社 | https://takebetaisha.jp/ | shrine_official | `WebFetch`実行（2回、前Pilot含む） | `EGRESS_BLOCKED` → **SOURCE_EXISTS_BUT_UNREACHABLE** |
| 波上宮 | https://naminouegu.jp/ | shrine_official | `WebFetch`実行（2回、前Pilot含む） | `EGRESS_BLOCKED` → **SOURCE_EXISTS_BUT_UNREACHABLE** |
| 沖縄県護国神社 | https://okinawa-gokoku.jp/ | shrine_official | `WebFetch`実行 | `EGRESS_BLOCKED` → **SOURCE_EXISTS_BUT_UNREACHABLE** |

**追加の技術的検証**: `WebFetch`ツール固有の制限である可能性を排除するため、
本セッションのBashから素の`curl`で`https://takebetaisha.jp/`へ直接接続を
試みた。

```
$ curl -sS -o /dev/null -w "HTTP_STATUS:%{http_code}\n" --max-time 15 https://takebetaisha.jp/
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000
```

環境のegress proxy status（`$HTTPS_PROXY/__agentproxy/status`）を確認したところ、
`noProxy`許可リストはAPI/パッケージレジストリ用途のインフラ
（`api.anthropic.com`, `registry.npmjs.org`, `pypi.org`等）に限定されており、
一般Webドメインへの直接egressは許可リスト外だった。これは`WebFetch`
ツール固有の制限ではなく、**本監査セッションのネットワーク層で一般外部
ドメインへのHTTPS接続そのものが許可されていない**ことを意味する
（`WebSearch`のみが機能した理由は、検索が別経路＝Anthropic自身の検索基盤を
経由するためと推測される。ただし推測である旨を明記する）。

**結果: 5/5 Shrine・5/5 Source URLで`CONTENT_VERIFIED`は0件。** すべて
`SOURCE_EXISTS_BUT_UNREACHABLE`に分類される（URLの存在自体はWebSearchの
snippet情報で間接的に確認できているが、本文は一切読めていない）。

## STOP GATE A 判定（Source Access）

> Source本文を取得できない → **該当（5/5 Shrine全件）**

他のSTOP GATE A条件（Source identity曖昧、同名神社との区別不能、Source URLが
別神社を指す、Source間の重大な矛盾、Source Contract上の分類不能）は、
そもそもSource本文へ到達できなかったため判定不能（N/A）である。

**判定: STOP GATE Aが5/5 Pilot Shrineすべてに対して発動した。** 弱いSource
（神社庁ページ等のsnippetのみ）から無理にFactを補完することはせず、
Phase 6（Fact Extraction Contract）以降には一切進んでいない。

## 7. Fact Extraction Results（Phase 6〜9）

**実施していない。** STOP GATE Aが全Pilot Shrineに対して発動したため、
`ShrineDeity`/`ShrineHistory`のFact Candidateは1件も生成していない。
deity boundary確認・tradition/historical fact境界確認・Fact provenance記録・
confidence/verification分類・Conflicting Evidence確認のいずれも、対象となる
Fact Candidateが存在しないため実施していない。

**AI推測による代替生成は一切行っていない。** 「北海道神宮の祭神は一般的に
天照大神・明治天皇等」といった一般知識・training data由来の情報を
Fact Candidateとして提示することは、最重要原則（Source本文で確認できない
Factを生成してはならない）および禁止事項（一般的な神話・神道知識から
補完しない、他の同名神社の情報を流用しない）に明確に違反するため、
意図的に行っていない。

## 8. Deferred / Rejected Facts

該当なし（Fact Candidateが1件も生成されていないため、Deferred/Rejectedの
対象自体が存在しない）。

## 9. Seed / Validation Results（Phase 10〜12）

**実施していない。** Fact Candidateが存在しないため、既存Knowledge Batch
Seed Schemaへの変換対象がなく、`import_shrine_knowledge --validate-only`/
`--dry-run`の実行対象も存在しない。Evidence Gate（`evidence_gate.py`）との
整合確認も、判定対象のFactが存在しないため実施していない（Evidence Gateの
判定ロジックには一切到達していない）。

前Pilot（`shrine-discovery-automation-readiness.md`）で実施したShrine
base-seed層（`name_jp`/`address`/座標のみ）の`import_shrines_seed --dry-run`
は既に9/9成功済みであり、本監査はその結果を変更しない。

## 10. KPI（Phase 14）

推測値は含まない。計測不能な項目はすべてN/Aとした。

| KPI | 値 | 算出根拠 |
|---|---|---|
| Source Discovery Rate | 5/5 = 100.0% | WebSearchで5社すべてについて候補Source URLを1件以上特定できた |
| Source Content Verification Rate | 0/5 = 0.0% | `CONTENT_VERIFIED`は0件。5件とも`SOURCE_EXISTS_BUT_UNREACHABLE` |
| Fact Generation Rate | 0/5 = 0.0% | STOP GATE Aにより1件も生成せず |
| Knowledge Seed Conversion Rate | N/A（分母0） | Fact Candidate生成shrine数が0のため算出不能 |
| Validation Pass Rate | N/A（分母0） | Seed変換対象が0のため算出不能 |
| Dry-run Pass Rate | N/A（分母0） | 同上 |
| Human Correction Rate | N/A | 本監査に人間レビュアーは参加していない。かつレビュー対象のFact Candidateが0件 |
| Human Review Time | N/A | 同上、架空の時間は作らない |

## 11. Findings

観測事実のみを記載する。

- Source discovery（URLの存在確認）と Source content acquisition（本文取得）
  は明確に別の能力であり、本監査セッションでは前者のみが機能し後者は
  機能しなかった
- `WebFetch`の`EGRESS_BLOCKED`エラーは、5/5社・計5ドメイン
  （`hokkaidojingu.or.jp`, `hokkaidojinjacho.jp`, `takebetaisha.jp`,
  `naminouegu.jp`, `okinawa-gokoku.jp`）すべてで再現し、神社公式サイト・
  都道府県神社庁ページ・市公式ページの区別なく一律に発生した
- 素の`curl`による直接接続も同じ`https://takebetaisha.jp/`に対し
  `CONNECT tunnel failed, response 403`で失敗しており、`WebFetch`ツール
  固有の制限ではなく、本監査セッションのネットワークegress設定そのものが
  一般外部ドメインへのHTTPS接続を許可していないことを示す
- repository内には、Batch 1〜16のSource Research作業を代替できる自動fetch
  toolingは元々存在しない。Source本文取得は常に担当セッションの外部
  アクセス能力に依存する設計だった（新規に発見された欠落ではなく、既存の
  運用前提そのもの）
- STOP GATE Aが機能し、Fact捏造（training data由来の一般知識での補完）を
  防いだ。これは意図した通りの安全側動作である

## 12. Environment Constraints

**Pipeline GapとEnvironment Constraintの分離:**

- **Pipeline Gap（コード/設計上の欠落）: 0件。** Source Contract・Fact
  Schema・Seed Schema・Evidence Gate・Import/Validation toolingは全て
  既存のまま機能可能であることを確認した（Phase 2、Phase 9参照）。
  Knowledge Pipeline自体に欠落は見つからなかった
- **Environment Constraint（本監査セッション固有の制約）: 1件。** 本監査
  セッションのネットワークegress設定が、API/パッケージレジストリ用途以外の
  一般外部ドメインへのHTTPS接続を許可していない。これにより`WebFetch`・
  素の`curl`のいずれでもSource本文を取得できなかった。この制約は
  `docs/audit/shrine-discovery-automation-readiness.md`でも同一の現象
  （`WebFetch`の`EGRESS_BLOCKED`）として報告済みであり、本監査で
  再現・別角度（`curl`によるネットワーク層検証）から確認を強化した

この制約は、Batch 1〜16の実運用（人間またはブラウジング可能なAIセッションが
Source本文を直接確認していた）とは異なる、本監査を実行しているセッション
固有の環境設定によるものであり、Knowledge Pipeline自体の設計・実装の欠陥では
ない。

## 13. Mother Ship Decision

以下を母艦へ返す。本監査内では結論を出さない。

- 本監査で確認されたネットワークegress制約を解除した、ブラウジング可能な
  環境（またはSource本文取得が可能な別セッション）でSource Acquisition &
  Fact Generation Pilotを再実施するか
- 再実施する場合、本監査で選定した5社（北海道神宮・函館八幡宮・建部大社・
  波上宮・沖縄県護国神社）をそのままPilot対象として採用するか
- Source本文取得を将来的に自動化するツールをrepositoryへ追加するか
  （現時点でPipeline Gapとしては未確認だが、Environment Constraintを
  恒久的に回避する手段として検討の余地はある。ただし本監査はこの実装を
  提案するのみで、着手しない）
- 20県への拡張、Batchサイズ、Human Reviewの配置は、Fact Generationが
  少なくとも1回成功するまでは判断材料が存在しないため、次のPilot
  再実施の結果を待つべきという事実のみを記録する

## Repository Change Policy（実施結果）

`docs/audit/shrine-knowledge-source-automation-readiness.md`のみを
commitする。Pilot用scratch artifact（Fact Candidate、Knowledge Seed
candidate JSON）は生成していない（Fact Candidateが1件も存在しないため、
そもそも生成物がない）。

## Validation（最終確認）

```
$ git status --short
```

の結果、本ドキュメント1件のみが新規追加であることを確認する（下記
「完了条件」実行時に併記）。

- Production write = 0（本監査はいかなるDBにも接続していない。WebFetch/curl
  試行はすべて外部ネットワークへのHTTPS接続試行であり、DB操作は一切なし）
- Existing Shrine Seed change = 0
- Existing Knowledge Seed change = 0
- Model change = 0
- Migration change = 0
- Evidence Gate change = 0
- Recommendation change = 0
- Ranking change = 0
- Concierge change = 0

## 完了条件チェック

STOP GATE Aが5/5 Pilot Shrineに対して発動したため、Phase 6以降
（Fact Extraction〜Human Review〜KPI算出の一部）は「実施しない」という
形で完了条件を満たす。「STOPは失敗ではない」という本タスクの明示的な
方針に従い、この結果をそのまま母艦へ返す。
