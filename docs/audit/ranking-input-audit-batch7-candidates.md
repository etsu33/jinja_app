> **Status: Active**
>
> 本ドキュメントは2つのトピックをまとめて記録する。**Score算出ロジックは一切変更していない。
> Batch 7のデータ投入も本ドキュメントでは行っていない（候補選定とSource availability確認のみ）。**

# Recommendation Ranking Input Audit / Batch 7 Candidate Proposal

## PR #2308 Closure

| 項目 | 値 |
|---|---|
| PR #2308 | MERGED（2026-08-08T08:56:58Z、merge commit `849de825`） |
| develop HEAD | `849de825b2086d7d99edb0b1c5bdc8dc8448f85e` |
| working tree | clean |
| Knowledge Coverage | 36/100（再確認済み） |

---

## Part 1 — Recommendation Ranking Input Audit

### 目的

`docs/audit/shrine-knowledge-rollout-batch-6.md`で「top3出現率の高さは著名度ではなく
goriyaku/needテーマ一致による」と結論したが、この結論の根拠となった具体的メカニズムを
コードレベルで追跡し、定量的に検証する。

### consultation → need/theme変換

`temples/services/concierge_chat_need.py`の`NEED_SYNONYMS`（study/career/mental/love/
money/restの6カテゴリ、キーワード辞書）で自由文クエリからneed_tagsへ変換する。1クエリで
複数のneed_tagsが同時に検出されることがある（例:「厄除けして心を整えたい」→
`['protection', 'mental', 'rest']`の3つ同時検出）。

### goriyaku_tagsがScoreへ入る経路

`temples/services/concierge_chat_ranking.py`の`_prefilter_candidates_for_need()`が、
候補ごとに以下を加算する。

- `astro_tags`一致: +2
- `goriyaku_tag_ids`と`need_tags_to_goriyaku_ids(need_tag)`の積集合が非空: +2（`gid`一致）
- `goriyaku`/`description`テキスト中のneed別キーワードヒット: +1（重み付き`text_score_by_tag`も別途加算）
- `history_theme`とconsultation_axisの一致ボーナス

このスコアで候補を`(-score, -popular_score, name)`によりソートする。`popular_score`は
DB全体で`0.0`のまま未設定であるため（`docs/audit/recommendation-quality-at-31pct-coverage.md`
で既に確認済み）、実質的な同点タイブレークは神社名の文字列順になる。

### 決定的な発見: need_tagカテゴリ間のgoriyaku_tag_id重複

`temples/domain/need_to_goriyaku_tag_ids.py`の`NEED_TO_GORIYAKU_IDS`を確認したところ、
`mental`（`{11,16,26,28,38,43}`）と`protection`（`{11,16,26,28,32,38}`）が**6件中5件を
共有**していることが判明した。

```
mental & protection overlap: {11, 16, 26, 28, 38}
```

このため、`goriyaku_tag_id=16`（"厄除け"）を持つ神社は、1クエリで`mental`と`protection`が
同時検出された場合、**同一のgoriyaku_tag一致で2回（+2×2=+4）score加算**される。実際に
「厄除けして心を整えたい」を`_prefilter_candidates_for_need()`へ直接投入したところ、
`goriyaku_tag_ids`に16を含む神社（武蔵御嶽神社・護王神社・酒列磯前神社・高良大社）が
軒並みscore 7で並び、`matched`ログに`['protection:gid', 'mental:gid', 'mental:text',
'rest:gid']`が記録されることを確認した。

### 19-query fixtureでのtag別出現率測定

| need_tag | 19クエリ中の出現回数 |
|---|---:|
| rest | 7 |
| mental | 5 |
| love | 4 |
| money | 3 |
| career | 2 |
| protection | 2 |
| courage | 1 |
| study | 1 |

`rest`・`mental`（`protection`と重複しやすい2カテゴリ）が19クエリ中12回（63%）を占める。

| goriyaku_tag（top3内、57スロット中） | 出現回数 |
|---|---:|
| 開運 | 33 |
| 厄除け | 28 |
| 勝運 | 18 |
| 縁結び | 16 |
| 心願成就 | 15 |
| 商売繁盛 | 11 |

"開運"・"厄除け"という汎用的なgoriyakuタグが突出して多い。DB全体（100shrine）でも
"厄除け"（id=16）は51件が保有する非常に一般的なタグである。

### famous shrine / Knowledge有無との交絡分離

| 観点 | 結果 |
|---|---|
| tag16(厄除け)保有shrineのうちKnowledge-backed比率 | 23/51（45.1%）。全体のKnowledge-backed比率36.0%よりやや高いが、突出した交絡ではない |
| top3で最も頻出したshrine | 武蔵御嶽神社（19クエリ中7回、Batch4でKnowledge投入済み）。goriyaku_tag_ids=[20,16,43,18]で"厄除け"を保有 |
| 2位・3位 | 護王神社・酒列磯前神社（各5回、いずれもBatch6でKnowledge投入済み、いずれも"厄除け"を保有） |

いずれも"厄除け"タグを保有することが直接の原因であり、著名度・Knowledge有無との相関は
副次的（tag16保有率がKnowledge-backedでやや高い程度）であることを確認した。

### Counterfactual: goriyaku_tagsを除去して順位比較

`goriyaku_tag_ids`・`goriyaku`（テキスト）を候補から意図的に除去し、19クエリで再実行した。

| 結果 | 件数 |
|---|---:|
| ranking完全一致 | 1/19 |
| ranking変化 | 18/19 |

**goriyaku_tagsを除去すると19クエリ中18クエリで上位3件が変わった。** これは
`docs/audit/recommendation-quality-at-31pct-coverage.md`で実施したKnowledge除去の
反実仮想テスト（6/6パターンで完全一致=Knowledgeは無関係）と対照的であり、
goriyaku_tagsが実際にrankingを左右する主要な入力であることを改めて定量的に確認した。

### 結論（Score式は変更していない）

- **特定tagが過剰にScoreを稼いでいる**: `goriyaku_tag_id=16`（厄除け）が、`mental`/
  `protection`という似た2つのneed_tagカテゴリの重複定義により、他のtagより実効的に
  高いscoreを得やすい構造になっている。これは`NEED_TO_GORIYAKU_IDS`のカテゴリ設計上の
  重複であり、Knowledge Rolloutとは無関係の既存Score機構の特性である。
- **famous shrine / Knowledge有無との交絡は限定的**: 交絡はゼロではない（tag16保有率が
  Knowledge-backedでやや高い）が、支配的な要因ではない。ranking上位化の直接要因は
  goriyaku_tag_idの一致であり、これはBatch 6投入前から存在する神社側の既存fieldである。
- **Score式自体は変更していない**（本監査の指示通り）。`NEED_TO_GORIYAKU_IDS`の重複定義を
  修正すべきかどうかはProduct判断が必要な別課題であり、本監査では提起のみに留める。

---

## Part 2 — Batch 7 Candidate Proposal（候補選定のみ、Source Availability軽量確認）

### 候補母集団

Zero-Knowledge 64件から、既知除外（靖國神社・長太稲荷神社・宇佐神宮・日光二荒山神社・
江島神社・富岡八幡宮）を除いた**58件**が母集団。

### 選定方針

Part 1の発見を踏まえ、地理分散に加えて、**goriyaku_tag_id=16（厄除け）を保有しない候補を
中心に選ぶ**ことで、今後のRecommendation QAサンプルにおいて「厄除けタグの効果」以外の
神社固有性検証もできるようにする。

| Shrine | id | 地域 | tag16(厄除け)保有 | 役割 |
|---|---|---|---|---|
| 富士山本宮浅間大社 | 19 | 中部（静岡） | No | 有名・Source strong（UNESCO世界文化遺産、浅間神社総本宮） |
| 宮地嶽神社 | 39 | 九州（福岡） | No | 中規模（神功皇后由来、光の道で知られる） |
| 生田神社 | 36 | 関西（兵庫） | No | 中規模（神戸の地名由来とされる） |
| 秩父神社 | 74 | 関東（埼玉） | No | 中規模（2100年余の歴史を称する古社） |
| 森戸大明神 | 91 | 関東（神奈川） | No | 地域神社（源頼朝ゆかりの葉山郷総鎮守） |

地域分布: 中部1・九州1・関西1・関東2（Batch 6の四国・中国に続き、九州・中部を新たに
カバー）。5社全てtag16非保有のため、Part 1で確認したmental/protection重複による
score増幅の影響を受けない候補群となる。

### Source Availability（軽量確認、direct fetchは未実施）

| Shrine | 想定公式ドメイン |
|---|---|
| 富士山本宮浅間大社 | `fuji-hongu.or.jp`（御由緒ページ確認済み: `/sengen/history/index.html`） |
| 宮地嶽神社 | `miyajidake.or.jp`（御由緒・御祭神ページ確認済み: `/history`, `/history/gosaijin`） |
| 生田神社 | `ikutajinja.or.jp`（紹介ページ確認済み: `/introduction`） |
| 秩父神社 | `chichibu-jinja.or.jp`（ご祭神・由緒ページ確認済み: `/saijin/`） |
| 森戸大明神 | `moritojinja.jp`（由緒・ご祭神ページ確認済み: `/about/gosaishin.html`） |

いずれもWebSearchレベルで明確な公式ドメイン・専用由緒ページの存在を確認した。過去3件
連続でSource到達不能（`sakura.ne.jp`系共用ホスティング等）に遭遇した経緯を踏まえ、
5ドメインとも上記とは異なる独自ドメインであることを確認済みだが、**投入直前の
direct fetchによる再確認は本ドキュメントでは実施していない**（Batch 6と同様、実際の
Fact Sheet起案・Source Availability Auditは別セッションで行う）。

### 特記事項

- 秩父神社は「秩父妙見宮」として中世以降信仰されてきた歴史を持つが、本殿祭神4柱のうち
  「天之御中主神」は鎌倉時代の合祀、「秩父宮雍仁親王」は昭和28年の合祀という異なる時代の
  複数合祀構造を持つ。Fact Sheet起案時には合祀時期をそれぞれ区別して記録する必要がある。
- 森戸大明神は「大山祗命・事代主命」を祀るが、由緒は「源頼朝が三嶋明神の分霊を勧請した」
  という永暦元年（1160年）の伝承が中心であり、`history_type=tradition`候補になる可能性が高い。

---

## Repository Changes

- `docs/audit/ranking-input-audit-batch7-candidates.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Score/Ranking/NEED_TO_GORIYAKU_IDS/Model/DB書き込み: すべて変更なし）

## Stop

本ドキュメントでは以下を行っていない。

- Score式・`NEED_TO_GORIYAKU_IDS`の変更
- Batch 7のFact Sheet起案・Source Availability Audit（direct fetch）
- DB投入
