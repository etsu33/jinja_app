> **Status: Preparation Only — 母艦Gate承認待ち**
>
> 本ドキュメントはBatch 5のPreparation記録である。**DB書き込みは一切行っていない。**
> 実際のデータ投入は、母艦がPhase 12「Mother Ship Gate」を確認・確定した後に、
> 別セッション（別PR）として実施する。

# Shrine Knowledge Batch 5 Source Availability

## Phase 0 — PR #2303 Closure

| 項目 | 値 |
|---|---|
| PR #2303 | MERGED（2026-08-08T04:44:42Z、merge commit `34f45a8c`） |
| develop HEAD | `34f45a8c9a69d64e7b80daa0b567b3ca3c3d1233` |
| working tree | clean |
| `docs/audit/batch4-closure-trust-ux-audit-batch5-gate.md` | develop反映済み |

## Phase 1 — Coverage Baseline（実測のみ採用）

| 指標 | 値 |
|---|---|
| Audit Target Shrines | 100 |
| Knowledge Coverage | 26/100 |
| Zero-Knowledge | 74/100 |
| Deity Coverage | 26/100 |
| History Coverage | 24/100 |
| Verified Source Count | 42 |
| candidate pool（`build_chat_candidates(limit=20)`） | 100 |
| query count | 6 |

## Phase 2 — Batch 5 Candidate Identity（投入前確認、不一致ゼロ）

| Shrine | id | name_jp | address | fixture | duplicate | 既存Knowledge | 同名取り違え |
|---|---|---|---|---|---|---|---|
| 賀茂別雷神社（上賀茂神社） | 35 | 賀茂別雷神社（上賀茂神社） | 京都府京都市北区上賀茂本山339 | No | No | なし | 賀茂御祖神社(34)とは別Shrine |
| 賀茂御祖神社（下鴨神社） | 34 | 賀茂御祖神社（下鴨神社） | 京都府京都市左京区下鴨泉川町59 | No | No | なし | 賀茂別雷神社(35)とは別Shrine |
| 日枝神社 | 43 | 日枝神社 | 東京都千代田区永田町2-10-5 | No | No | なし | なし |
| 東京大神宮 | 44 | 東京大神宮 | 東京都千代田区富士見2-4-1 | No | No | なし | なし |
| 白山比咩神社 | 41 | 白山比咩神社 | 石川県白山市三宮町ニ105-1 | No | No | なし | 白山神社(65)とは別Shrine |

STOPは発生していない。

## Phase 3 — Fresh Source Availability Audit（direct fetch優先）

検索結果summaryだけでは確定せず、投入予定内容は全て公式ページを直接fetchして確認した。

| Shrine | Source | source_type | reachability |
|---|---|---|---|
| 上賀茂神社 | 御由緒と御神紋｜賀茂別雷神社（`kamigamojinja.jp/about/yuisho/`） | shrine_official | 到達可能・直接fetch確認済み |
| 上賀茂神社 | 御神話｜賀茂別雷神社（`kamigamojinja.jp/about/shinwa/`） | shrine_official | 同上 |
| 下鴨神社 | 御祭神・歴史・神話｜下鴨神社（`shimogamo-jinja.or.jp/about`） | shrine_official | 到達可能・直接fetch確認済み |
| 日枝神社 | 日枝神社について（`hiejinja.net/about/`） | shrine_official | 到達可能・直接fetch確認済み |
| 東京大神宮 | 東京大神宮の紹介（`tokyodaijingu.or.jp/syoukai/`） | shrine_official | 到達可能・直接fetch確認済み |
| 白山比咩神社 | 白山比咩神社について（`shirayama.or.jp/about/`） | shrine_official | 到達可能・直接fetch確認済み |

government/cultural_property/shrine association/local historyの独立Sourceは、5社とも今回は
個別に追加確認していない（下鴨神社の文化財情報は公式ページ本文中の記載に留まり、文化庁等
独立Sourceでの裏付けは今回未実施）。secondary editorialも今回は使用していない（全社
shrine_officialのみで十分な内容が得られたため）。

### 重要な発見: 史実/伝承の書き分けをSource原文レベルで検証した

検索結果要約の段階では「史実」と分類されていた記述の一部が、公式ページ原文を直接確認した
結果、**Source自身が明示的に伝承として書いていた**ことが判明した。

- **下鴨神社「崇神天皇の7年（BC90）」**: 原文は「当神社の**正確な創祀は不明ですが**、
  崇神天皇の7年（BC90）に神社の瑞垣の修造がおこなわれた**という記録があるため**、それ以前の
  古い時代からお祀りされていたと**考えられます**」。断定ではなく推定として書かれている。
- **白山比咩神社「崇神天皇7年（紀元前91年）」**: 原文は「創建された**と伝わり**」「創建された
  **と伝えられる**」。明確に伝承として書かれている。
- 対照的に、白山比咩神社の**霊亀2年（716年）・文明12年（1480年）**の遷座記述には伝承を示す
  言葉が付いておらず、断定的な史実表現だった。

この検証がなければ、AI要約段階の「史実」という粗い分類をそのまま`history_type=official_origin`
や`founding`へ採用してしまうリスクがあった。`docs/audit/tradition-output-contract-fix.md`の
Tradition Confidence Gap知見（confidenceとhistory_typeは別軸）を踏まえ、古代の天皇紀年
（崇神天皇・応神天皇等、史実性が学術的に確立していない時代区分）に基づく創建伝承は、
Source自身の書き方に関わらず慎重に扱う方針を本Batchでも維持した。

## Phase 4 — 上賀茂神社（id=35）Fact Sheet

| 項目 | 内容 |
|---|---|
| 主祭神 | 賀茂別雷大神（role=primary, confidence=high） |
| 創建由緒 | 天武天皇6年（677年）、山背国により賀茂神宮が造営された（**断定的記述、伝承語なし**）→ `history_type=official_origin` |
| 神話/伝承 | 「神代の昔」に神山へ御降臨、賀茂玉依比売命が丹塗矢を拾い懐妊し賀茂別雷大神を生んだとする伝承（`釋日本紀所引山城國風土記逸文`・`賀茂舊記`を出典と明記）→ `history_type=tradition` |
| period_text | 677年の史料は「天武天皇6年（677年）」、神話は年代不明のため無し |
| event_date | 未使用（月日不明のため） |
| Source relation | 2件（御由緒ページ・御神話ページ、いずれもshrine_official） |
| confidence | 全件high（Source自体は公式で信頼できるため。tradition側もconfidence=highのままhistory_typeで区別する） |

古代創建説（神代の降臨）を史実年として断定していない。677年の造営記録のみを`official_origin`として扱う。

## Phase 5 — 下鴨神社（id=34）Fact Sheet

| 項目 | 内容 |
|---|---|
| 祭神構造 | 西殿=賀茂建角身命、東殿=玉依媛命（本殿2棟、いずれもrole=enshrined、序列を示す記述がSourceにないためprimary単独指定なし） |
| 創祀伝承 | 崇神天皇7年（BC90）瑞垣修造の記録を根拠とする推定（Source自身「正確な創祀は不明」と明記）→ `tradition` |
| historical_event（3件） | 文武天皇2年（698年）葵祭警備命令の記録／長元9年（1036年）式年遷宮制度の確立／平成6年（1994年）UNESCO世界文化遺産登録 |
| 祭神自身の神話 | 玉依媛命の丹塗矢懐妊伝説、賀茂建角身命の八咫烏化身神話（いずれも下鴨神社祭神自身に関する記述、上賀茂神社の神話とは別視点で下鴨神社側にも登録可能）→ `tradition`、1つのcontentへ合成せず別Factとする |
| cultural_property系Source有無 | 本文中に「国宝2棟」「重要文化財53棟」の記載はあるが、文化庁等の独立Sourceでの確認は今回未実施のため、Fact登録対象外（由緒本文の一部としてのみ触れる） |

複数祭神のroleを公式記述以上に解釈していない（西殿/東殿の構造をそのままrole=enshrinedで表現し、
どちらかを主祭神と推測していない）。

## Phase 6 — 日枝神社（id=43）Fact Sheet

| 項目 | 内容 |
|---|---|
| exact shrine identity | id=43、東京都千代田区永田町2-10-5、公式サイト`hiejinja.net`と一致確認済み |
| 祭神 | 大山咋神（主祭神, primary, high）、相殿: 国常立神・伊弉冉神・足仲彦尊（enshrined, high、note="相殿"） |
| 江戸/徳川関連由緒 | 文明10年（1478年）太田道灌による川越山王社勧請、天正18年（1590年）徳川家康の江戸入府を経て江戸城内鎮護の神として位置づけられた経緯 → `official_origin` |
| 遷座・再建 | 明暦3年（1657年）の大火による社殿炎上、赤坂への遷祀 → `historical_event` |
| tradition/historical_eventの分離 | 大山咋神の『古事記』由来神話（山の神としての性質）は登録対象外。1478年以降の日枝神社固有の経緯のみ`official_origin`/`historical_event`として登録する |

「山王信仰一般」（大山咋神の記紀由来・全国の山王信仰との関係）と「日枝神社固有Fact」
（1478年以降の当社自身の沿革）を明確に分離し、前者はFactとして登録しない方針とした。

## Phase 7 — 東京大神宮（id=44）Fact Sheet

| 項目 | 内容 |
|---|---|
| 祭神構造 | 天照皇大神（primary, high）、豊受大神（enshrined, high）、造化の三神＝天之御中主神・高御産巣日神・神産巣日神（enshrined, high、collective note="公式サイトが一括して呼称する集合的名称"）、倭比賣命（enshrined, high） |
| 明治期創建 | 明治13年（1880年）、明治天皇の御裁断により伊勢神宮の遥拝殿として創建 → `official_origin` |
| 伊勢神宮との関係 | 内宮（天照皇大神）・外宮（豊受大神）の御祭神を奉斎する遥拝殿として創設された旨、公式ページに明記 |
| 神前結婚式等の歴史的事実 | **Fact登録対象外**とする。公式ページは「現在広く行われている神前結婚式は、当社の創始によるもの」と記載するが、「具体的な証拠資料は示されていない」社伝的性格の記述であり、一般的な縁結びイメージをFactとして混入しない方針に従い見送る |
| event_date利用可否 | 明治13年は年のみで月日の記載がなく、`event_date`（確定日）は使用せず`period_text`（幅を持つ期間表現）として扱う |

Batch 1-4はいずれも中世以前の創建だったのに対し、東京大神宮は初めての近代（明治期）創建例。

## Phase 8 — 白山比咩神社（id=41）Fact Sheet

| 項目 | 内容 |
|---|---|
| 祭神 | 白山比咩大神＝菊理媛尊（primary, high）、伊弉諾尊（enshrined, high）、伊弉冉尊（enshrined, high） |
| 白山信仰との関係 | 全国約三千社の白山神社の総本宮である旨、公式ページに明記（白山信仰一般の教義そのものはFact化せず、当社自身の由緒のみ登録） |
| 創祀伝承 | 崇神天皇7年（紀元前91年）、舟岡山への創建「**と伝わり**」（Source自身が明示的に伝承として記述）→ `tradition` |
| historical_event（2件） | 霊亀2年（716年）「安久濤の森」への遷座（断定的記述）／文明12年（1480年）の大火を経た現在地への遷座（断定的記述） |
| 神仏習合の扱い | 本文中に明示的な神仏習合関連の記述は今回の直接fetch範囲では確認できず、Fact登録対象外 |
| 保留事項 | 応神天皇28年（297年）の遷座について、崇神天皇7年と同様の古代天皇紀年であるため慎重を期すべきだが、伝承語の有無を今回個別に確認できていない。他の遷座記述（716年・1480年）と同列に断定記述として扱うことはせず、**追加確認が必要な項目として保留**する |

白山信仰一般（全国的な信仰の広がり）と白山比咩神社固有Fact（当社自身の創祀・遷座の経緯）を分離した。

## Phase 9 — Contract Compatibility Matrix

| Shrine | 判定 |
|---|---|
| 上賀茂神社 | `PASS_WITH_NOTE`（神代神話とofficial_originを分離） |
| 下鴨神社 | `PASS_WITH_NOTE`（創祀年代をtradition化、複数historical_eventを分離登録） |
| 日枝神社 | `PASS_WITH_NOTE`（山王信仰一般を除外、shrine固有historyのみ） |
| 東京大神宮 | `PASS_WITH_NOTE`（神前結婚式起源説を除外） |
| 白山比咩神社 | `PASS_WITH_NOTE`（創祀伝承をtradition化、応神天皇28年は保留） |

5社ともBLOCKINGなし、DEFER_DISPUTEDなし、DO_NOT_ENTER_INSUFFICIENT_EVIDENCEなし。

確認事項:

- collective deity問題なし: 東京大神宮の「造化の三神」は3柱の総称として公式サイト自身が一括呼称するため、八坂神社の八柱御子神（Batch 4）と同型で吸収できる
- sacred objectをdeity化していない: 該当なし（今回投入予定は全て神格）
- religion-wide doctrineをShrine Factにしない: 日枝神社の大山咋神記紀由来神話（山王信仰一般）、白山信仰一般の教義は、いずれも意図的にFact登録から除外した
- traditionをhistorical factへ昇格していない: 下鴨神社・白山比咩神社の崇神天皇7年創祀伝承は、Source自身の伝承語（「という記録がある」「考えられます」「伝わり」「伝えられる」）を根拠に`tradition`分類とし、`official_origin`/`founding`へは昇格させていない
- Source不足を推測補完していない: 該当なし（全5社、公式サイトが十分な由緒情報を提供）
- multiple accountsを1 Factへ混ぜていない: 上賀茂神社（神代神話 / 677年造営）、下鴨神社（複数の歴史的事実・祭神別の神話）を、それぞれ別Factとして分離する方針とした

## Phase 10 — Variance Audit（人工的にvarianceを作らない）

| Variance | 本Batchでの状況 |
|---|---|
| low confidence | なし（実データ実例は依然ゼロ） |
| medium confidence | なし（今回投入予定は全てhigh） |
| disputed | なし（実データ実例は依然ゼロ） |
| tradition | **あり**（上賀茂神社1件・下鴨神社1件・白山比咩神社1件、計3件新規） |
| deity only | なし（5社ともHistoryも投入予定） |
| history only | なし |
| cultural_property | なし（下鴨神社の文化財情報は本文言及のみに留め、独立Source化は見送った） |
| relatively modern founding | **あり**（東京大神宮、明治13年=1880年。Batch1-4は全て中世以前の創建だったため初の近代創建例） |
| multi-deity structure | **あり**（下鴨神社2柱・日枝神社4柱・東京大神宮4柱） |
| shrine-specific vs religion-wide distinction | **あり**（日枝神社・白山比咩神社で、religion-wide教義を明示的にFactから除外する実例が初めて生じた） |

low/medium/disputedは依然として実データ実例ゼロのまま（既知のギャップ`INSUFFICIENT_NEGATIVE_CASES`は
本Batchでも埋まらない）。これらのvarianceは5社の公式Source内容を素直に読んだ結果として自然に
生じたものであり、variance確保を目的に内容を作為的に選んでいない。

## Phase 11 — Batch 5 Final Entry Recommendation（提示のみ、DB投入なし）

| Shrine | 提案 |
|---|---|
| 上賀茂神社 | `ENTER`（deity）+ `ENTER`（history: 677年、official_origin）+ `ENTER_AS_TRADITION`（神代神話） |
| 下鴨神社 | `ENTER`（deity×2）+ `ENTER_AS_TRADITION`（創祀年代）+ `ENTER`（historical_event×3）+ `ENTER_AS_TRADITION`（祭神別神話×2） |
| 日枝神社 | `ENTER`（deity×4）+ `ENTER`（history×2、official_origin+historical_event）+ 記紀由来神話は`DO_NOT_ENTER`（religion-wide） |
| 東京大神宮 | `ENTER`（deity×4）+ `ENTER`（history×1、official_origin）+ 神前結婚式起源説は`DO_NOT_ENTER` |
| 白山比咩神社 | `ENTER`（deity×3）+ `ENTER_AS_TRADITION`（創祀伝承）+ `ENTER`（historical_event×2）+ 応神天皇28年は`DEFER_PENDING_VERIFICATION` |

## Phase 12 — Mother Ship Gate（母艦へ返す、本ドキュメントでは決定しない）

- [ ] Batch 5を開始するか
- [ ] 5社維持か（技術的には全5社`PASS_WITH_NOTE`）
- [ ] 5社すべて投入可能か（技術的には可能と判断。最終可否は母艦判断）
- [ ] `PASS_WITH_NOTE`を許可するか（Batch 1-4で前例あり）
- [ ] traditionの扱い（新規3件、`TRADITION_ALWAYS_HEDGED`契約は稼働中のため追加対応は不要と見ているが確認を要する）
- [ ] disputedが出た場合の扱い（今回は実例なし、想定不要）
- [ ] 代替候補が必要か（白山比咩神社の応神天皇28年をどう扱うか＝保留のまま投入する／代替Sourceを探す／このFact自体を見送るか、方針が必要）

## Phase 13 — Recommendation Safety Pre-check（投入前の既存機構再確認）

DB投入は行っていないため、Batch 4投入後の状態から変化はない。Phase 1で再測した結果と合わせ、
以下を確認した。

| 項目 | 結果 |
|---|---|
| Mixed Confidence FULL_SUPPRESSION維持 | ○（`docs/audit/mixed-confidence-policy-decision.md`確定通り、Policy変更なし） |
| TRADITION_ALWAYS_HEDGED維持 | ○（`_apply_tradition_hedge_floor()`、コード変更なし） |
| Source-less Fact suppression維持 | ○（Evidence Gate、コード変更なし） |
| disputed suppression維持 | ○（同上） |
| candidate query count 6維持 | ○（Phase 1で再実測） |

## Phase 14 — Documentation

本ドキュメント（`docs/audit/shrine-knowledge-batch-5-source-availability.md`）が記録。

## Phase 15 — Stop

本ドキュメントでは以下を一切行っていない。

- DB投入
- Batch 6
- user-facing Source UI
- Recommendation API contract変更
- confidence UI
- Score/Ranking変更
- PER_FACT_RENDERING

## Repository Changes

- `docs/audit/shrine-knowledge-batch-5-source-availability.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/DB書き込み: すべて変更なし）
