> **Status: `GEO_KNOWLEDGE_COVERAGE_AUDIT_COMPLETE_NO_STOP`。**
>
> 本監査はread-only auditであり、Shrine/Knowledge/Seed/Importer/Recommendationの
> いずれも変更しない。新しいShrineの追加・収集、Coverage改善施策の実装は行わない。
>
> **本監査値はrepository内のSeedおよびKnowledge Batchから再構築したlocal DBを
> 対象とする。Production DBの直接計測値ではない。**

# Shrine Geographic / Knowledge Coverage Aggregation Audit

## Method

### 使用DB・再構築方法

Production DBへは接続していない。本監査専用に、このセッション内でlocal
PostgreSQL 16（非GIS構成）を新規構築し、repository内の既存Seed / Knowledge
Batchのみを使って以下の手順で再構築した。コード・Seed・Importer自体への変更は
一切行っていない。

1. `python manage.py migrate`（`USE_GIS=0` → `temples.migrations_nogis`使用。
   PostGIS未導入環境向けの既存fallback経路であり、本Repoの通常テスト実行
   （`docs/audit/shrine-knowledge-rollout-batch-7.md`§J「9 skipはPostGIS/GDAL
   未導入起因のみ」）と同じ経路）
2. `python manage.py import_shrines_seed`（既定source
   `temples/data/shrines_seed_clean.json`、100件、`created=100, updated=0,
   skipped=0`）
3. `python manage.py import_shrine_knowledge` を Batch 1〜16 の seed file
   （`temples/data/knowledge_seeds/batch_1_7_seed.json`
   〜`batch_16_seed.json`、計10ファイル）に対し順番に実行。**全10ファイルで
   エラー0件。**
4. `python manage.py knowledge_coverage_report --format json`
   （既存read-only集計command、変更なし）を実行し、以下の実測値を得た。
   これは`docs/audit/post-batch16-knowledge-next-track-comparison.md`が記録する
   Batch 16時点の値（Source 109 / Deity 233 / History 182）と**完全一致**した。

| 指標 | 実測値 |
|---|---:|
| total_db_shrines | 100 |
| audit_target_shrines | 100 |
| excluded_test_shrines | 0（注記参照） |
| knowledge_coverage | 86（86.0%） |
| zero_knowledge | 14（14.0%） |
| deity_coverage | 86 |
| history_coverage | 84 |
| verified_source_count / total_source_count | 109 / 109 |

> **注記（excluded_test_shrinesについて）**: 実際の開発/検証DBには
> `docs/audit/`が言及するPR2271（`audit/knowledge-coverage-shadow-105`、id
> 101-105の「承認テスト神社」「重複検証神社」等）由来のQA fixture Shrineが
> 追加で存在しうるが、これらはSeed fileから再現可能な資産ではなく（ad-hoc
> 投入）、本監査の再構築DBには含まれていない。ただし既存Coverage tooling
> （`temples.services.shrine_qa_fixture_exclusion.exclude_qa_fixture_shrines`、
> name_jpの命名規約でfilter）はこれらを**いずれにせよCoverage計算から除外する**
> ため、この不在は本監査のCoverage関連数値には一切影響しない
> （`excluded_test_shrines`の値のみ、フルレプリカでは0より大きくなりうる）。

### Seed source

- Base Shrine: `backend/temples/data/shrines_seed_clean.json`（100件）
- Knowledge: `backend/temples/data/knowledge_seeds/batch_1_7_seed.json`,
  `batch_8_seed.json`〜`batch_16_seed.json`（Batch 1〜16、既存repository資産）

### Knowledge Batch範囲

Batch 1〜16（`docs/audit/shrine-knowledge-rollout-batch-1〜7.md`、
`docs/audit/knowledge-batch8〜16-production-import-execution.md`等が記録する
既存投入実績の全範囲）。Batch 16が本Repo上で確認できる最新の投入済みBatchである
（`git log`確認済み、2026-08-12以降にKnowledge関連のcommitなし）。

### 都道府県判定方法

`Shrine.address`（自由入力CharField、都道府県専用fieldは存在しない）の文字列
先頭が都道府県名で始まる形式を前提に、47都道府県名との前方一致で判定した。
100件中98件はこの前方一致で直接解決した。残り2件（id=21 長太稲荷神社、id=22
給田六所神社）は`"日本、〒157-0064 東京都..."`というGoogle Maps形式
（国名＋郵便番号prefixが付与された別formatのaddress）だったため、既知の
`日本、〒NNN-NNNN `prefixのみを除去した上で同じ前方一致判定を適用し、両方とも
東京都と一意に判定できた（47都道府県名同士に部分文字列衝突がないことは事前に
全組み合わせを機械的に確認済み）。この2形式以外の非対応formatを持つShrineは
0件だった。判定不能（真にどの都道府県か決定できない）Shrineは0件であり、STOP
条件「addressから都道府県を一意に判定できないShrineが存在」には該当しない。

### Knowledgeあり/なしの定義

独自定義を新設していない。既存`temples.services.knowledge_coverage_report`の
`knowledge_coverage`指標と同一の定義（`ShrineDeity`が1件以上存在、または
`ShrineHistory`が1件以上存在＝`deity_shrine_ids | history_shrine_ids`）を、
同モジュールの内部関数（`_audit_target_shrine_ids`, `_per_shrine_fact_counts`）
をそのまま呼び出して算出した。QA fixture除外条件も同モジュールが委譲する
`exclude_qa_fixture_shrines`をそのまま使用しており、独自の除外ロジックは
追加していない。

### 集計日

2026-08-23（本監査実施日、local DB再構築後の実測）

## Summary

| 項目 | 値 |
|---|---:|
| Shrine総数（audit target） | 100 |
| 登録済み都道府県数 | 27 / 47 |
| 登録0社の都道府県数 | 20 / 47 |
| Knowledgeあり総数 | 86 |
| Knowledgeなし総数 | 14 |
| Knowledge Coverage率 | 86.0% |

## Tables

### 1. 47都道府県別Coverage

| 都道府県 | Shrine | 構成比 | Knowledgeあり | Knowledgeなし | Knowledge Coverage |
|---|---:|---:|---:|---:|---:|
| 北海道 | 0 | 0.0% | 0 | 0 | - |
| 青森県 | 0 | 0.0% | 0 | 0 | - |
| 岩手県 | 0 | 0.0% | 0 | 0 | - |
| 宮城県 | 0 | 0.0% | 0 | 0 | - |
| 秋田県 | 0 | 0.0% | 0 | 0 | - |
| 山形県 | 0 | 0.0% | 0 | 0 | - |
| 福島県 | 0 | 0.0% | 0 | 0 | - |
| 茨城県 | 6 | 6.0% | 6 | 0 | 100.0% |
| 栃木県 | 5 | 5.0% | 4 | 1 | 80.0% |
| 群馬県 | 4 | 4.0% | 1 | 3 | 25.0% |
| 埼玉県 | 9 | 9.0% | 7 | 2 | 77.8% |
| 千葉県 | 5 | 5.0% | 4 | 1 | 80.0% |
| 東京都 | 30 | 30.0% | 24 | 6 | 80.0% |
| 神奈川県 | 9 | 9.0% | 9 | 0 | 100.0% |
| 新潟県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 富山県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 石川県 | 2 | 2.0% | 2 | 0 | 100.0% |
| 福井県 | 0 | 0.0% | 0 | 0 | - |
| 山梨県 | 0 | 0.0% | 0 | 0 | - |
| 長野県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 岐阜県 | 0 | 0.0% | 0 | 0 | - |
| 静岡県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 愛知県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 三重県 | 2 | 2.0% | 2 | 0 | 100.0% |
| 滋賀県 | 0 | 0.0% | 0 | 0 | - |
| 京都府 | 7 | 7.0% | 7 | 0 | 100.0% |
| 大阪府 | 2 | 2.0% | 2 | 0 | 100.0% |
| 兵庫県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 奈良県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 和歌山県 | 0 | 0.0% | 0 | 0 | - |
| 鳥取県 | 0 | 0.0% | 0 | 0 | - |
| 島根県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 岡山県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 広島県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 山口県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 徳島県 | 0 | 0.0% | 0 | 0 | - |
| 香川県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 愛媛県 | 0 | 0.0% | 0 | 0 | - |
| 高知県 | 0 | 0.0% | 0 | 0 | - |
| 福岡県 | 4 | 4.0% | 4 | 0 | 100.0% |
| 佐賀県 | 0 | 0.0% | 0 | 0 | - |
| 長崎県 | 0 | 0.0% | 0 | 0 | - |
| 熊本県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 大分県 | 1 | 1.0% | 1 | 0 | 100.0% |
| 宮崎県 | 1 | 1.0% | 0 | 1 | 0.0% |
| 鹿児島県 | 0 | 0.0% | 0 | 0 | - |
| 沖縄県 | 0 | 0.0% | 0 | 0 | - |
| **合計** | **100** | **100.0%** | **86** | **14** | **86.0%** |

### 2. 8地方別Coverage

地方区分の定義（一般的な8地方区分。都道府県の重複・欠落なし、47都道府県を
すべて1地方にのみ割り当て）:

- 北海道: 北海道（1）
- 東北: 青森県, 岩手県, 宮城県, 秋田県, 山形県, 福島県（6）
- 関東: 茨城県, 栃木県, 群馬県, 埼玉県, 千葉県, 東京都, 神奈川県（7）
- 中部: 新潟県, 富山県, 石川県, 福井県, 山梨県, 長野県, 岐阜県, 静岡県, 愛知県（9）
- 近畿: 三重県, 滋賀県, 京都府, 大阪府, 兵庫県, 奈良県, 和歌山県（7）
- 中国: 鳥取県, 島根県, 岡山県, 広島県, 山口県（5）
- 四国: 徳島県, 香川県, 愛媛県, 高知県（4）
- 九州・沖縄: 福岡県, 佐賀県, 長崎県, 熊本県, 大分県, 宮崎県, 鹿児島県, 沖縄県（8）

| 地方 | Shrine | 構成比 | Knowledgeあり | Knowledgeなし | Knowledge Coverage |
|---|---:|---:|---:|---:|---:|
| 北海道 | 0 | 0.0% | 0 | 0 | - |
| 東北 | 0 | 0.0% | 0 | 0 | - |
| 関東 | 68 | 68.0% | 55 | 13 | 80.9% |
| 中部 | 7 | 7.0% | 7 | 0 | 100.0% |
| 近畿 | 13 | 13.0% | 13 | 0 | 100.0% |
| 中国 | 4 | 4.0% | 4 | 0 | 100.0% |
| 四国 | 1 | 1.0% | 1 | 0 | 100.0% |
| 九州・沖縄 | 7 | 7.0% | 6 | 1 | 85.7% |
| **合計** | **100** | **100.0%** | **86** | **14** | **86.0%** |

### 3. Knowledge Coverage（全体）

| 指標 | 値 |
|---|---:|
| Knowledgeあり | 86 |
| Knowledgeなし | 14 |
| Knowledge Coverage率 | 86.0% |
| （参考）既存`knowledge_coverage_report`実測値との一致 | 一致（86/100, 86.0%） |

### 4. Coverage区分（都道府県のShrine登録数による分類）

| 区分 | 該当都道府県数 | 都道府県 |
|---|---:|---|
| 0社 | 20 | 北海道, 青森県, 岩手県, 宮城県, 秋田県, 山形県, 福島県, 福井県, 山梨県, 岐阜県, 滋賀県, 和歌山県, 鳥取県, 徳島県, 愛媛県, 高知県, 佐賀県, 長崎県, 鹿児島県, 沖縄県 |
| 1〜2社 | 18 | 新潟県, 富山県, 石川県, 長野県, 静岡県, 愛知県, 三重県, 大阪府, 兵庫県, 奈良県, 島根県, 岡山県, 広島県, 山口県, 香川県, 熊本県, 大分県, 宮崎県 |
| 3〜5社 | 4 | 栃木県, 群馬県, 千葉県, 福岡県 |
| 6社以上 | 5 | 茨城県, 埼玉県, 東京都, 神奈川県, 京都府 |
| **合計** | **47** | |

### 5. Shrine登録数Top 10

| 順位 | 都道府県 | Shrine数 |
|---:|---|---:|
| 1 | 東京都 | 30 |
| 2 | 埼玉県 | 9 |
| 2 | 神奈川県 | 9 |
| 4 | 京都府 | 7 |
| 5 | 茨城県 | 6 |
| 6 | 栃木県 | 5 |
| 6 | 千葉県 | 5 |
| 8 | 群馬県 | 4 |
| 8 | 福岡県 | 4 |
| 10 | 石川県 | 2 |
| 10 | 三重県 | 2 |
| 10 | 大阪府 | 2 |

（Top 10だが同数タイのため12都道府県を掲載。11位以下は1〜2社区分に含まれる）

### 6. Knowledge未投入Shrine地域分布（14件）

| 都道府県 | 件数 | Shrine名 |
|---|---:|---|
| 東京都 | 6 | 千住神社, 鳥越神社, 花園神社, 靖國神社, 愛宕神社, 長太稲荷神社 |
| 群馬県 | 3 | 赤城神社, 冠稲荷神社, 榛名神社 |
| 埼玉県 | 2 | 調神社, 武蔵一宮 氷川女體神社 |
| 栃木県 | 1 | 古峯神社 |
| 千葉県 | 1 | 千葉神社 |
| 宮崎県 | 1 | 高千穂神社 |
| **合計** | **14** | |

地方別では、関東13件（東京都6・群馬県3・埼玉県2・栃木県1・千葉県1）、
九州・沖縄1件（宮崎県1）。中部・近畿・中国・四国のKnowledge未投入Shrineは0件。

## Findings

数値から直接確認できる事実のみを記載する。推測・改善案・優先順位付けは含まない。

- Shrine登録は47都道府県中27都道府県に存在し、20都道府県は登録0社である。
- 登録済み27都道府県のうち、関東7都道府県すべてに登録があり、関東だけで
  全Shrine100件中68件（68.0%）を占める。
- 東京都単独で30件（全体の30.0%）であり、Shrine登録数Top 10（12都道府県、
  タイ含む）のうち上位6都道府県（東京都・埼玉県・神奈川県・京都府・茨城県・
  栃木県/千葉県）で合計64件（64.0%）を占める。
- 東北6県・北海道の登録は0社である（東北地方全体・北海道地方の登録Shrine数は
  いずれも0）。
- 四国4県中、登録があるのは香川県のみ（1社）。九州・沖縄8県中、登録があるのは
  福岡県（4）・熊本県（1）・大分県（1）・宮崎県（1）の4県のみで、佐賀県・
  長崎県・鹿児島県・沖縄県は0社である。
- Knowledge Coverage率は全体で86.0%（86/100）であり、既存
  `knowledge_coverage_report` commandの実測値（86/100, 86.0%）と完全一致する。
- Knowledge未投入14件のうち13件（92.9%）が関東地方に集中しており、その内訳は
  東京都6件・群馬県3件・埼玉県2件・栃木県1件・千葉県1件である。残り1件は
  宮崎県（高千穂神社）で、これは宮崎県の登録1社そのものがKnowledge未投入
  （Coverage率0.0%）であることを意味する。
- Shrine数が多い都道府県ほどKnowledge Coverageが低いとは限らない。京都府
  （7社、Coverage 100.0%）・神奈川県（9社、Coverage 100.0%）・茨城県（6社、
  Coverage 100.0%）はShrine数が多い側だがCoverage 100.0%である一方、東京都
  （30社、Coverage 80.0%）・群馬県（4社、Coverage 25.0%）はShrine数に対して
  未投入件数が残っている。
- Shrine数・Knowledge Coverageともに100.0%達成の都道府県が27都道府県中20
  都道府県ある（1〜2社区分18都道府県中17都道府県＋6社以上区分5都道府県中3
  都道府県）。Coverage率が100.0%未満の登録済み都道府県は7件（栃木県80.0%・
  群馬県25.0%・埼玉県77.8%・東京都80.0%・千葉県80.0%・宮崎県0.0%、および
  地方合計としての関東80.9%・九州沖縄85.7%）である。
- Shrine 0社の都道府県（20件）は、そのままKnowledge Coverage算出の対象外
  （分母0）である。これらの都道府県について「Knowledge未投入」を論じることは
  できない（Shrine自体が存在しないため）。

## Validation

| 検証項目 | 結果 |
|---|---|
| 都道府県別Shrine合計 = Shrine総数 | 100 = 100（一致） |
| 地方別Shrine合計 = Shrine総数 | 100 = 100（一致） |
| Knowledgeあり + Knowledgeなし = Shrine総数 | 86 + 14 = 100（一致） |
| 47都道府県がすべて表に存在 | 一致（Table 1に47行） |
| Knowledge判定が既存Contract/Coverage toolingと一致 | 一致（`knowledge_coverage_report`の内部関数をそのまま再利用） |
| 既存Coverage reportとの主要数値一致 | 一致（total_db_shrines=100, audit_target_shrines=100, knowledge_coverage=86/86.0%, deity_coverage=86, history_coverage=84, source count=109/109、いずれもBatch 16後の既存監査文書の値と一致） |
| address→都道府県 一意判定不能なShrineの有無 | 0件（100件全件を一意に判定。詳細はMethod「都道府県判定方法」節） |

**STOP条件はいずれも該当しなかった。**

## Repository Changes

- `docs/audit/shrine-geographic-knowledge-coverage.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Admin/command/Seed/Knowledge/Recommendation: 変更なし
- 本監査用に一時的に構築したlocal PostgreSQL DBはこのセッション内のみに存在し、
  repositoryにもProduction環境にも一切影響しない
