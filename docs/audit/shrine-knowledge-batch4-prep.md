> **Status: Preparation Only — 母艦Gate承認待ち**
>
> 本ドキュメントはBatch 4のPreparation記録である。**DB書き込みは一切行っていない。**
> 実際のデータ投入は、母艦がPhase C「Mother Ship Gate Proposal」を確認・確定した後に、
> 別セッション（別PR）として実施する。

# Shrine Knowledge Batch 4 Preparation

## 前提

`docs/audit/shrine-knowledge-rollout-batch-1.md`〜`batch-3.md`（19社・49 deity・実データ）に続く、
Batch 4の候補選定・Source Availability Audit・Fact Sheet起案の記録。
本Batchの投入順（技術推奨）・最終Gate確定は母艦が行う。

## Phase A — Candidate Population（母集団再取得）

`knowledge_coverage_report`と同じ判定ロジック（`shrine_qa_fixture_exclusion` + Evidence Gate
Fact-ready判定）で、zero-Knowledge shrineを再取得した。

```
QA fixture除外後の監査対象: 100件
Knowledge Coverage: 21件（21.0%）
Zero-Knowledge: 79件（79.0%）
```

## Phase A' — Exclusion（既知の除外理由）

| 除外対象 | 理由 | 出典 |
|---|---|---|
| 靖國神社(id=58) | Collective deity構造（246万柱、公式が個別列挙という発想自体を採らない）。Model/Contract判断が確定するまでBatch対象候補から除外 | `docs/audit/collective-deity-contract-stress.md`（Mother Ship Decision: 靖國神社=`DEFER`、Batch 4=`CONTINUE`（collective case除外）） |
| 長太稲荷神社(id=21) | 信頼できるSource（shrine_official/government/cultural_property）が一切確認できず`DO_NOT_ENTER_INSUFFICIENT_EVIDENCE`確定済み | `docs/audit/shrine-knowledge-rollout-batch-2.md`、`docs/audit/recommendation-fact-integrity-negative-pilot.md`（両方で同一結論を再確認済み） |

除外後の候補母集団: **77件**。

護国神社系列（靖國神社と同型の集合的祭神構造を持つ可能性がある神社）に該当する
shrineは、現在の79件母集団の中には存在しないことを名称確認した（該当0件）。

## Phase B — 候補選定（Batch 4案、5社）

Batch 1-3の技術推奨（「Source構造が単純なケースから開始」）に従い、単一または少数の
明確な祭神を持つ、公式サイトが安定して存在する著名な神社を優先して5社を選んだ。
これは提案であり、最終選定は母艦Gateで確定する。

| Shrine | id | 選定理由 |
|---|---|---|
| 太宰府天満宮 | 6 | 単一祭神（菅原道真公）、天満宮総本宮、公式サイト安定 |
| 石清水八幡宮 | 12 | 八幡大神3柱、日本三大八幡宮の一つ、公式サイト安定 |
| 香取神宮 | 15 | 単一祭神（経津主大神）、既存の鹿島神宮Fact（Negative Pilot投入済み）と対になる関係性、公式サイト安定 |
| 住吉大社 | 11 | 住吉三神+神功皇后、住吉信仰総本社、公式サイト安定 |
| 八坂神社 | 56 | 素戔嗚尊中心、祇園信仰総本社、公式サイト安定 |

### 候補差し替えの記録: 宇佐神宮 → 八坂神社

当初、日本三大八幡宮つながりで宇佐神宮(id=8)を候補に含めたが、公式ドメイン
`usajinguu.com`がTLS証明書不一致（証明書のSAN一覧に自ドメインが含まれない、
さくらインターネット共用SSLの設定不備と見られる）により直接fetchできなかった。
Source自体が存在しないケース（長太稲荷神社）とは性質が異なる
（**`SOURCE_EXISTS_BUT_UNREACHABLE`**として区別する）ため、`INSUFFICIENT_EVIDENCE`
とは判定せず、単に本Batch候補からは見送り、八坂神社へ差し替えた。
宇佐神宮は将来のBatchで、公式サイトの復旧確認後に再候補化できる。

## Phase C — Source Availability Audit（5社）

すべて公式サイトへ直接fetchし、内容を確認した（二次情報のみでの登録は行わない）。

### 太宰府天満宮（id=6）

- Source: 御由緒｜太宰府天満宮（`https://www.dazaifutenmangu.or.jp/about/goyuisho`）／shrine_official
- 御祭神: 菅原道真公
- 由緒: 昌泰4年（901年）左遷、延喜3年（903年）2月25日逝去（確定的記述）。延喜19年（919年）勅命により社殿造営（確定的記述）。埋葬地選定の経緯として「牛が伏して動かなくなった」逸話が含まれる（**社伝自身が伝承的記述として提示**）。

### 石清水八幡宮（id=12）

- Source: 石清水八幡宮について｜石清水八幡宮（`https://iwashimizu.or.jp/about/`）／shrine_official
- 御祭神: 中御前=応神天皇（誉田別尊）、西御前=比咩大神（多紀理毘賣命・市寸島姫命・多岐津毘賣命）、東御前=神功皇后（息長帯比賣命）
- 由緒: 貞観元年（859年）、南都大安寺の僧・行教和尚が宇佐八幡宮での託宣を受け男山に勧請したとする（**社伝自身が伝承的記述として提示**）。
- **数値差異の記録**: WebSearch要約では「860年（貞観2年）」という表記も見られたが、公式ページを直接fetchした結果は「貞観元年（859年）」であった。公式ページの記述を正としてFact Sheetへ採用する（要約から生じた誤差であり、公式ページ自体に矛盾はない）。

### 香取神宮（id=15）

- Source: 香取神宮について｜御由緒｜香取神宮（`https://katori-jingu.or.jp/about/`、`/about/history/`）／shrine_official
- 御祭神: 経津主大神（伊波比主命）
- 由緒: 公式ページ（`/about/history/`）には具体的な創建年（西暦・和暦）の記載がなかった。複数の二次情報（Wikipedia等）は「社伝によれば神武天皇18年（紀元前643年）」と紹介しているが、**この年代を明記した公式ページ自体は今回確認できなかった**。国家鎮護の神・下総国一宮・明治以前の「神宮」称号等、公式ページで確認できる記述は多いが、創建年についてはPending。

### 住吉大社（id=11）

- Source: 住吉大社の由緒｜住吉大社について｜住吉大社（`https://www.sumiyoshitaisha.net/about/origin.html`）／shrine_official
- 御祭神: 底筒男命・中筒男命・表筒男命（住吉三神）、息長足姫命（神功皇后）
- 由緒: 神功皇后摂政11年（西暦211年）、新羅遠征からの帰途、住吉大神の神託によりこの地に鎮斎されたとする（**社伝自身が『日本書紀』『古事記』に基づく伝承的記述として提示**）。
- 大阪市住吉区・摂津国一之宮であることを確認済み（博多の住吉神社とは別法人・別Shrine行）。

### 八坂神社（id=56）

- Source: 御祭神｜八坂神社の歴史｜八坂神社（`https://www.yasaka-jinja.or.jp/about/saijin.html`、`/about/history/`）／shrine_official
- 御祭神: 素戔嗚尊（主祭神）、櫛稲田姫命（お妃）、八柱御子神（お二人の御子、公式ページが個別列挙せず一括して呼称する集合的名称）
- 由緒: 公式ページ自身が「社伝としては以下の2つの説が伝わります」と明記した上で2説を提示している。
  - 説1: 斉明天皇2年（656年）、高麗より来朝した伊利之が新羅国牛頭山の素戔嗚尊をこの地に祀った
  - 説2: 貞観18年（876年）、南都の僧・円如が堂を建立し、天神が東山麓の祇園林に降り立った
  - 元慶元年（877年）の疫病鎮静が発展の契機、確定的な初見は祇園御霊会（869年）とされる

## Phase D — Fact Sheet（起案、DB未投入）

Model制約の確認: `role`（primary/enshrined/secondary/unknown）、`history_type`
（official_origin/founding/historical_event/tradition/regional_context/editorial_summary）、
`Multiple Fact保持方針`（1つのcontentへ複数説を合成しない）に従い、以下の構成を提案する。

| Shrine | Deity（役割・confidence案） | History（type・confidence案） |
|---|---|---|
| 太宰府天満宮 | 菅原道真公(primary, high) | 1件, official_origin, high。901-919の確定的経緯を中心に記述し、埋葬地選定の逸話部分のみ「社伝によれば」等のhedge表現を明示的に含める |
| 石清水八幡宮 | 応神天皇=誉田別尊(primary, high)／比咩大神(enshrined, high)／神功皇后=息長帯比賣命(enshrined, high) | 1件, **tradition**, high。TRADITION_ALWAYS_HEDGED契約適用（`docs/core/recommendation-reason-contract.md`） |
| 香取神宮 | 経津主大神(primary, high) | **保留**。公式ページで確認できる範囲（社格・下総国一宮等）に限定するか、創建年について公式ページの別箇所を追加調査するまでHistory登録自体を見送るか、母艦判断が必要 |
| 住吉大社 | 底筒男命/中筒男命/表筒男命(enshrined, high)、息長足姫命(enshrined, high)、主祭神表記なし（4柱を並列表記する公式記述のためrole=primaryの単独指定は行わない案） | 1件, **tradition**, high。TRADITION_ALWAYS_HEDGED契約適用 |
| 八坂神社 | 素戔嗚尊(primary, high)／櫛稲田姫命(enshrined, high)／八柱御子神(enshrined, high、collective note付き) | **2件**, **tradition**×2, high。656年説・876年説をそれぞれ別Factとして登録し、1つのcontentへ合成しない |

石清水八幡宮・住吉大社・八坂神社の3社は、社伝自身が伝承として提示する内容を
`history_type=tradition`で登録することになるため、`docs/audit/tradition-output-contract-fix.md`
のTRADITION_ALWAYS_HEDGED契約が実データで最も多く適用されるBatchになる見込み。

## Phase E — Mother Ship Gate Proposal（未確定、承認待ち）

以下は提案であり、**本ドキュメントでは確定しない**。母艦の確認後、確定した内容を
別途Gate記録として残し、その後のみデータ投入へ進む。

| Shrine | 提案Entry Decision |
|---|---|
| 太宰府天満宮 | `ENTER_WITH_NOTE`（埋葬地逸話のhedge表現を明示） |
| 石清水八幡宮 | `ENTER_WITH_NOTE`（tradition分類、3柱individually） |
| 香取神宮 | `ENTER_WITH_NOTE`（Deityのみ確定投入、Historyは公式ページ追加調査 or 見送り、母艦判断待ち） |
| 住吉大社 | `ENTER_WITH_NOTE`（tradition分類、4柱role=primary単独指定なし） |
| 八坂神社 | `ENTER_WITH_NOTE`（History 2件、tradition×2、八柱御子神collective note付き） |

投入順（技術推奨、Source構造が単純なものから）: 太宰府天満宮 → 香取神宮 → 石清水八幡宮 → 住吉大社 → 八坂神社。

## 禁止事項の遵守

- [x] DB書き込みなし
- [x] confidence値の恣意的な操作なし（すべてSourceに基づく案として提示のみ）
- [x] 二次情報のみでのFact登録提案なし（全社官公式サイトを直接fetch）
- [x] Batch全体を一括投入する提案なし（Phase E以降は母艦Gate確定後、別セッションで順次投入する前提）

## Repository Changes

- `docs/audit/shrine-knowledge-batch4-prep.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/DB書き込み: すべて変更なし）
