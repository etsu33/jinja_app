> **Status: Decided（KPI定義を正本化、コード実装は伴わない）**
>
> 本ドキュメントは、Batch 7 Closure確認時に発覚した「Internal Traceability」指標の
> 誤判定を訂正し、`docs/knowledge/shrine-knowledge-contract.md`へTraceability Contractを
> 追記した記録である。**コード変更は一切行っていない。**

# Traceability Metric Correction

## 発端: Batch 7 Closure時の誤判定

Batch 7 Closure確認の中で、DB全体のFact traceabilityを再測定したところ、2件の
"trace-unable Fact"（明治天皇・昭憲皇太后、`ShrineDeity` id=1,2、明治神宮）を検出した。
これはBatch 7の新規投入分（17 Fact）には含まれない、Batch 1以前（最初のKnowledge Pilot）
由来のFactだった。

### 誤判定の原因

当時使用した測定ロジックは、「Factに紐づく**全て**のSourceが`url`を持つこと」を
traceabilityの条件としていた。しかし該当2 Factを直接確認したところ、実際には
以下のように**2件のSourceが紐づいており、そのうち1件はURLを持つ**ことが判明した。

```
明治天皇 -> sources:
  (999005, shrine_official, 'https://www.meijijingu.or.jp/about/')  # URLあり
  (999004, user_observation, '')                                     # URLなし（現地観察の補強Source）
```

「全てのSourceがURLを持つこと」という条件は誤りであり、正しくは「**少なくとも1件の
Sourceが到達可能であること**」または「Fact自体がSource relationを持つこと」を基準に
すべきだった。`user_observation`（現地観察）は、Web出典と並行して補強的に付与される
ケースがあり、これ自体はFact Integrity上まったく問題のない構成である。

## Traceability Contractの追記

`docs/knowledge/shrine-knowledge-contract.md`のSource契約へ、以下を追記した。

- **Fact → Source relation到達を必須条件とする**（URLの有無を問わない）。これは
  Evidence Gateが既に強制している要件と一致する。
- **Source typeごとのtraceability要件**を定義した。`shrine_official`等はURL必須を
  基本とし、`user_observation`・書籍等の`local_history`はURLなしを許容する代わりに
  `title`/`source_type`/`verification_status`（`user_observation`の場合）または
  `bibliography`/`publisher`（書籍等の場合）を必須とする。
- **3つのKPIを再定義し、混同しないことを明記した**:
  - **Internal Source Traceability Rate** = Source relationへ逆引き可能なFact数 ÷ 対象Fact数
  - **URL-backed Source Rate** = URLを持つSourceに紐づくFact数 ÷ 対象Fact数
  - **Offline Source-backed Fact Rate** = `user_observation`・書籍等のoffline Sourceに紐づくFact数 ÷ 対象Fact数

## 再測定結果（develop HEAD `694f422d`時点、DB全体188 Fact）

新しい定義でDB全体を再測定した。

| KPI | 値 |
|---|---|
| Internal Source Traceability Rate | 188/188（100.0%） |
| URL-backed Source Rate | 188/188（**100.0%**、訂正前の186/188という誤った値を修正） |
| Offline Source-backed Fact Rate | 2/188（1.1%、明治天皇・昭憲皇太后が`shrine_official`のURL付きSourceに加え`user_observation`の補強Sourceも持つことを示す） |

`user_observation` Source（id=999004）自体が新しい per-source-type要件を満たすことも
確認した（`title`/`source_type`/`verification_status`いずれも設定済み、Fact relationも存在）。

**訂正: 前回のBatch 7 Closure確認で報告した「DB-wide traceability 186/188（98.9%）」は
誤りであり、正しくは新しいURL-backed Source Rate定義で100%である。** Internal Source
Traceability Rate（Source relation存在の有無のみを問う、最も基本的な指標）は、訂正前も
訂正後も一貫して100%であり、この点に誤りはなかった。

## Repository Changes

- `docs/knowledge/shrine-knowledge-contract.md`: Source契約へ「Traceability Contract」節を追記
- `docs/audit/traceability-metric-correction.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/Score/Ranking/DB書き込み: すべて変更なし）

## Stop

- Batch 8はまだ開始していない
- Score/Ranking codeは変更していない
- PER_FACT_RENDERINGは変更していない
- Source UIは変更していない
