> **Status: `BATCH15_TARGET_SELECTION_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch14-closure-batch15-reentry.md`
> （`BATCH14_CLOSED_BATCH15_REENTRY_READY_WITH_LIMITATIONS`）を受け、
> Batch 15のTarget Selection（候補選定）のみを実施した記録である。
> **Production writeは一切行っていない。** Batch 15 seed作成・Source
> 登録・Production importはこのドキュメントのスコープ外であり、実施
> していない。

develop SHA（作業開始時点）: `0ecf611ee02ae06d1b0131c128b56fa3d3467bdf`
（PR #2373反映済み、`origin/develop`と同期済み、working tree clean）。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（既に最新）
- [x] HEAD SHA記録: `0ecf611ee02ae06d1b0131c128b56fa3d3467bdf`
- [x] working tree clean確認
- [x] PR #2373（`BATCH14_CLOSED_BATCH15_REENTRY_READY_WITH_LIMITATIONS`）
      のmerge確認（`git log`でmerge commit確認済み）
- [x] `knowledge-batch14-closure-batch15-reentry.md`・
      `knowledge-batch14-target-selection.md`・
      `knowledge-batch14-seed-preflight.md`・
      `docs/knowledge/shrine-knowledge-contract.md`・importer実装を
      freshに再読

過去チャットの記憶ではなく、merge済みrepo実体を正本として扱った。

---

## Phase 1 — Production Current State Recheck（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | Closure Audit記載 | 判定 |
|---|---:|---:|---|
| Knowledge Shrine | 76 | 76 | 一致 |
| Source | 97 | 97 | 一致 |
| Deity | 210 | 210 | 一致 |
| History | 149 | 149 | 一致 |
| Deity–Source relation | 223 | 223 | 一致 |
| History–Source relation | 154 | 154 | 一致 |
| complete | 74 | 74 | 一致 |
| partial | 2 | 2 | 一致 |
| none | 29 | 29 | 一致 |

drift 0件。

---

## Phase 2 — Candidate Universe Fresh Rebuild

raw `none`集合（29件）をfreshに抽出し、除外条件を一から適用した
（参考値24を盲信せず独立導出）。

| 除外区分 | 件数 | 内訳 |
|---|---:|---|
| QA fixture | 1 | id=102「テスト確認神社 20260611」 |
| unresolved identity | 1 | id=105「広島市」（神社名ではなく地名） |
| duplicate（非canonical重複行） | 3 | id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複 |
| **canonical candidate（fresh導出）** | **24** | — |

独立に導出した結果が参考値24と一致した。除外5件は
`knowledge-batch14-closure-batch15-reentry.md`記載の5件と完全に同一
（drift 0）。

24件の内訳（id/name_jp/address）:

冠稲荷神社(87)・千住神社(67)・千葉神社(78)・古峯神社(86)・
報徳二宮神社(92)・多摩川浅間神社(70)・宇都宮二荒山神社(84)・
平塚八幡宮(94)・愛宕神社(46)・榛名神社(27)・櫻木神社(80)・
武蔵一宮氷川女體神社(72)・水戸東照宮(53)・湯島天満宮(64)・
白山神社(65)・箭弓稲荷神社(76)・花園神社(61)・葛西神社(68)・
調神社(73)・赤城神社(89)・長太稲荷神社(21)・靖國神社(58)・
高千穂神社(42)・鳥越神社(63)

---

## Phase 3 — Partial Track Separation（fresh再確認）

| shrine | id | Deity | History | missing layer |
|---|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | History |
| 香取神宮 | 15 | 1 | 0 | History |

両社とも変化なし。分類: `PARTIAL_REPAIR_CANDIDATE`。Batch 15通常候補
から除外する。**repairは本ドキュメントでは実施しない。**

---

## Phase 4 — Historical Model-risk Candidates（fresh再確認、過去判断を上書きしない）

| shrine | id | 過去の判断 | 本セッションでの扱い |
|---|---:|---|---|
| 靖國神社 | 58 | 近代・政治的機微を理由にBatch12〜14で継続除外 | 新しい根拠は生じていないため、過去判断を維持（`MODEL_UNSUITABLE_FOR_NORMAL_BATCH`） |
| 千葉神社 | 78 | shinbutsu-shugo疑い（妙見菩薩由来）を理由にBatch12〜14で継続除外 | 同上 |
| 愛宕神社 | 46 | 明示的な仏教称号を理由にBatch11〜14で継続除外 | 同上 |
| 赤城神社 | 89 | 神仏習合の明示的記述（本地仏千手観音等）によりBatch14で`MODEL_REVIEW_REQUIRED` | 同上 |
| 千住神社 | 67 | `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（境内の七福神・富士塚）によりBatch14でAlternative止まり | 同上、`MODEL_REVIEW_REQUIRED`のまま |

いずれも24候補には構造的に残存するが、Recommended 5・Top 10双方に
含めていない（Top 10は候補として一覧に含める場合も選定理由に注記する）。

---

## Phase 5-10 — Lightweight Screening → Deep-dive（有力候補、公式本文を直接WebFetch/Browser paneで確認済み）

**方針**: 24候補全件を同じ深さで詳細調査することはしない。Batch 14
Target Selection時点で既に`A = OFFICIAL_SOURCE_READY`と分類されていた
候補群を中心に、fresh再確認（前回の分類を鵜呑みにせず、公式サイトを
直接再取得）を行った。

### 深掘りした候補と結果

| shrine | 公式Source URL | 御祭神（fresh確認） | 由緒概要 | content-model所見 |
|---|---|---|---|---|
| 湯島天満宮 | https://www.yushimatenjin.or.jp/pc/engi/engi.htm | 天之手力雄命・菅原道真公の二柱 | 雄略天皇2年(458)創建伝承（天之手力雄命奉斎）、正平10年(1355)菅原道真勧請合祀、文明10年(1478)太田道灌再建、天正18-19年(1590-91)徳川家康崇敬・朱印地寄進、元禄16年(1703)火災全焼、明治5-18年(1872-85)郷社→府社昇格、平成7年(1995)現社殿造営 | 摂社・仏教尊格の記載なし。`MODEL_FIT_SAFE` |
| 報徳二宮神社 | https://www.ninomiya.or.jp/sontoku/（祭神）、https://www.ninomiya.or.jp/info/（由緒） | 二宮尊徳翁の一柱 | 明治27年(1894)創建、6カ国報徳社の総意により尊徳翁を御祭神として祀る、明治42年本殿新築、平成6年(1994)創建百年記念 | 単一祭神、人物神格化（乃木神社に前例あり、Batch13で既に確認済みの型）。`MODEL_FIT_SAFE` |
| 箭弓稲荷神社 | https://www.yakyu-inari.jp/yuisho/ | 保食神の一柱（本社） | 和銅5年(712)創建伝承、源頼信の戦勝祈願と社名改称の言い伝え、江戸期の隆盛 | 末社「團十郎稲荷」（宇迦之御魂神）は別途祀られる社でありFact化対象外。本社は`MODEL_FIT_SAFE` |
| 水戸東照宮 | https://gongensan-mito-toshogu.jp/gosaisin.html | 徳川家康公（東照公）・徳川頼房公（威公、昭和11年配祀）の二柱 | 元和7年(1621)創建、天保14年(1843)神道による祭祀へ改革（公式サイト自身が「初期は神仏習合で仏祭を行っていた」と明記した上でこの改革を記載）、昭和20年(1945)空襲焼失、昭和37年(1962)再建 | 人物神格化（東照宮型、全国に多数の前例がある確立した神道慣習）。神仏習合は歴史的事実として記載されているが、現在は神道による祭祀に改められたと公式サイト自身が明記。`MODEL_FIT_SAFE`（注記付き） |
| 葛西神社 | https://www.kasaijinja.jp/about/saijin.html（祭神）、https://www.kasaijinja.jp/about/（由緒） | 経津主神・日本武尊・徳川家康命（東照権現さま）の三柱 | 元暦2年(1185)創建、下総国香取神宮より分霊、領主葛西三郎清重、天正18-19年(1590-91)豊臣秀吉・徳川家康より御朱印、明治14年(1881)「葛西神社」に改称 | 境内社（招魂社・弁天・富士）は年中行事名としてのみ言及され、御祭神ページには含まれない。Fact化対象外として明確に区別可能。`MODEL_FIT_SAFE` |

### 軽量スクリーニングのみ実施した候補（Alternatives・未深堀り）

| shrine | Batch14時点分類 | 本セッションでの扱い |
|---|---|---|
| 冠稲荷神社 | A（Batch14時点） | **fresh再確認の結果、リスクを再評価。** 本殿祭神が「宇迦御魂神、大穴牟遅神、太田神、天照大御神ほか15柱以上」、別途「聖天宮」（聖天=歓喜天、仏教尊格）を含む多数の境内社を持つことが判明。単純なA分類には収まらず、`MODEL_REVIEW_REQUIRED`寄りへ格下げし、Recommended 5から除外した |
| 高千穂神社 | B（公式サイト独立ドメイン未確認） | 未深堀り、Alternative候補のまま |
| 武蔵一宮氷川女體神社 | B | 未深堀り、Alternative候補のまま |
| 白山神社（文京区） | B | 未深堀り、Alternative候補のまま |
| 調神社 | B | 未深堀り、Alternative候補のまま |
| 鳥越神社 | B | 未深堀り、Alternative候補のまま |
| 榛名神社 | 未分類 | 主要6柱は確認できたが、由緒詳細ページに到達できず（サイト構造上、通知ページが前面に出る）。国祖社等の境内社の扱いも要精査。`C = ADDITIONAL_RESEARCH_REQUIRED` |
| 多摩川浅間神社 | 未分類 | 主祭神（木花咲耶姫命）は明確だが、熊野神社・赤城神社の合祀があり除外範囲の精査が必要。`C = ADDITIONAL_RESEARCH_REQUIRED` |
| 宇都宮二荒山神社 | C寄り | 未深堀り、`C = ADDITIONAL_RESEARCH_REQUIRED`のまま |
| 平塚八幡宮・櫻木神社・古峯神社・花園神社 | 未分類/A(等) | 未深堀り |
| 長太稲荷神社 | D（Batch14時点） | 変化なし、`D = SOURCE_INSUFFICIENT` |

---

## Phase 6 — Identity Safety（Recommended 5候補、fresh実測）

| shrine | id | address | `place_ref_id IS NULL` | 同名重複 | Deity | History |
|---|---:|---|---|---:|---:|---:|
| 湯島天満宮 | 64 | 東京都文京区湯島3-30-1 | true | 1 | 0 | 0 |
| 報徳二宮神社 | 92 | 神奈川県小田原市城内8-10 | true | 1 | 0 | 0 |
| 箭弓稲荷神社 | 76 | 埼玉県東松山市箭弓町2-5-14 | true | 1 | 0 | 0 |
| 水戸東照宮 | 53 | 茨城県水戸市宮町2-5-13 | true | 1 | 0 | 0 |
| 葛西神社 | 68 | 東京都葛飾区東金町6-10-5 | true | 1 | 0 | 0 |

**全5社が`IDENTITY_SAFE`。**

---

## Phase 7 — Source Semantic Conflict Precheck（fresh実施）

Production既存97件のSourceと`normalize_source_url()`実装をそのまま
使用して照合した。

```sql
SELECT id, source_type, title, publisher, url FROM temples_shrineknowledgesource
WHERE url ILIKE '%yushimatenjin%' OR url ILIKE '%ninomiya.or.jp%'
   OR url ILIKE '%yakyu-inari%' OR url ILIKE '%mito-toshogu%'
   OR url ILIKE '%kasaijinja%';
```

結果: 0件（既存Sourceに一致なし）。**5候補Sourceすべてが`NO_CONFLICT`。**

---

## Phase 8 — Deity Evidence Feasibility

| shrine | 判定 | 根拠 |
|---|---|---|
| 湯島天満宮 | HIGH | 2柱とも公式由緒ページで個別名・由来が明記 |
| 報徳二宮神社 | HIGH | 単一祭神が公式ページで明記、人物神格化として明確 |
| 箭弓稲荷神社 | HIGH | 本社祭神1柱が公式サイトで明記。末社は別ページ・別祭神として区別可能 |
| 水戸東照宮 | HIGH | 2柱とも公式祭神ページで明記、配祀の経緯（昭和11年）も明記 |
| 葛西神社 | HIGH | 3柱とも公式祭神ページで個別に説明文付きで明記 |

**Recommended 5全件がHIGH。**

---

## Phase 9 — History Evidence Feasibility

| shrine | 判定 | founding/tradition/historical_event候補 |
|---|---|---|
| 湯島天満宮 | HIGH | founding(458年創建伝承)、historical_event(1355年道真勧請、1478年太田道灌再建、1590-91年家康崇敬、1703年火災、1872-85年社格昇格) |
| 報徳二宮神社 | HIGH | founding(1894年創建)、historical_event(1909年本殿新築、1994年百年記念) |
| 箭弓稲荷神社 | HIGH | founding/tradition(712年創建伝承)、tradition(源頼信の戦勝祈願伝説) |
| 水戸東照宮 | HIGH | founding(1621年創建)、historical_event(1843年神道祭祀改革、1936年配祀、1945年焼失、1962年再建) |
| 葛西神社 | HIGH | founding(1185年創建、香取神宮分霊)、historical_event(1590-91年御朱印、1881年改称) |

**Recommended 5全件がHIGH。** 伝承（箭弓稲荷神社の創建年、湯島天満宮の
458年創建）と確定できる歴史的出来事は分離してFact化可能であることを
確認した。

---

## Phase 10 — Content-model Risk

| shrine | 確認した懸念 | 判定 |
|---|---|---|
| 湯島天満宮 | 「天神信仰」の解説文は神道の信仰概念説明であり仏教尊格ではない。摂社記載なし | `MODEL_FIT_SAFE` |
| 報徳二宮神社 | 人物神格化（乃木神社前例あり） | `MODEL_FIT_SAFE` |
| 箭弓稲荷神社 | 末社「團十郎稲荷」を除外すれば本社のみで安全 | `MODEL_FIT_SAFE`（末社除外を明記） |
| 水戸東照宮 | 人物神格化（東照宮型、確立した前例）。歴史的な神仏習合期への言及があるが、現在は神道祭祀へ改革済みと公式サイト自身が明記 | `MODEL_FIT_SAFE`（注記付き） |
| 葛西神社 | 人物神格化（東照権現、東照宮型）。境内社（招魂社・弁天・富士）は祭神ページに含まれず区別可能 | `MODEL_FIT_SAFE`（境内社除外を明記） |

**Recommended 5全件が`MODEL_FIT_SAFE`。**

---

## Phase 11 — Runtime User Value Confirmation（fresh再確認、コード変更なし）

Batch 14 Closure（`KNOWLEDGE_RUNTIME_EXPOSED`）をfresh再確認した。

```
GET https://jinja-backend.onrender.com/api/shrines/66/data/
→ HTTP 200, name_jp=王子神社, deities=5, histories=3
```

Batch 14で投入したFactが本セッション時点でも変わらず`ShrineDetailSerializer`
経由でRuntime公開されていることを確認した。コード変更は行っていない。
Batch 15で追加するKnowledgeも同一経路（`GET /api/shrines/<id>/data/`
→ Web `ShrineFactSection`／`concierge_chat_candidates.py`経由の
Recommendation）でuser-visible・recommendation-visibleになることが
見込まれる。

---

## Phase 12 — Regional Distribution（fresh集計、tie-breakerとしてのみ使用）

| 現在のKnowledge Shrine 76社 | 上位地域 |
|---|---|
| 東京都 | 19 |
| 京都府 | 7 |
| 神奈川県 | 7 |
| 埼玉県 | 6 |
| 茨城県 | 5 |
| 福岡県 | 4 |

候補プール（24件）も東京都・関東に構造的に偏っている
（Batch14時点から変化なし）。**Recommended 5の地域分布**: 東京
（湯島天満宮・葛西神社）・神奈川（報徳二宮神社）・埼玉（箭弓稲荷神社）・
茨城（水戸東照宮）の4都県。Source品質・Evidence feasibility・
Model Fitを地域分散より優先した選定の結果である。

---

## Phase 13 — Product Value

| 指標 | 結果 |
|---|---|
| favorite件数 | 0 |
| visit件数 | 2 |

**分類: `PRODUCT_VALUE_NOT_AVAILABLE`。** 欠損値を推測で補完していない。

---

## Phase 14 — Selection Rule

優先順位を以下のとおり固定する。

1. **Identity Safety** — `IDENTITY_SAFE`以外は選定不可
2. **Official Source Availability** — Source分類A（`OFFICIAL_SOURCE_READY`）
   を優先
3. **Source Semantic Conflict Safety** — `NO_CONFLICT`以外は除外
4. **Deity Evidence Feasibility** — 原則`HIGH`のみ
5. **History Evidence Feasibility** — 原則`HIGH`のみ
6. **Content-model Fit** — `MODEL_FIT_SAFE`以外
   （`MODEL_REVIEW_REQUIRED`・`MODEL_UNSUITABLE_FOR_NORMAL_BATCH`）は
   通常Batchでは選定しない
7. **Runtime User Value** — 既存経路でuser-visible・recommendation-visible
   になることを確認済み（Batch 14以降は全候補で共通して成立するため
   実質的にtie-breakerとしては機能しない）
8. **Product Value** — `PRODUCT_VALUE_NOT_AVAILABLE`のためtie-breaker
   としても機能しない
9. **Regional Diversity** — 最終的なtie-breakerとしてのみ使用。品質を
   落として人数合わせをしない

---

## Phase 15 — Top 10

| # | shrine | address | prefecture | identity | Source分類 | 公式Source URL | conflict | Deity feasibility | History feasibility | content-model | uncertainty | selection reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 湯島天満宮 | 東京都文京区湯島3-30-1 | 東京 | SAFE | A | https://www.yushimatenjin.or.jp/pc/engi/engi.htm | NO_CONFLICT | HIGH | HIGH | MODEL_FIT_SAFE | 低 | 2柱・458年からの由緒が明確、公式本文直接確認済み |
| 2 | 報徳二宮神社 | 神奈川県小田原市城内8-10 | 神奈川 | SAFE | A | https://www.ninomiya.or.jp/sontoku/ | NO_CONFLICT | HIGH | HIGH | MODEL_FIT_SAFE | 低 | 単一祭神で明確、人物神格化の前例あり |
| 3 | 箭弓稲荷神社 | 埼玉県東松山市箭弓町2-5-14 | 埼玉 | SAFE | A | https://www.yakyu-inari.jp/yuisho/ | NO_CONFLICT | HIGH | HIGH | MODEL_FIT_SAFE | 低 | 単一祭神、末社と本社の区別が明確 |
| 4 | 水戸東照宮 | 茨城県水戸市宮町2-5-13 | 茨城 | SAFE | A | https://gongensan-mito-toshogu.jp/gosaisin.html | NO_CONFLICT | HIGH | HIGH | MODEL_FIT_SAFE | 低 | 2柱、神仏習合から神道祭祀への改革が公式に明記、東照宮型の前例あり |
| 5 | 葛西神社 | 東京都葛飾区東金町6-10-5 | 東京 | SAFE | A | https://www.kasaijinja.jp/about/saijin.html | NO_CONFLICT | HIGH | HIGH | MODEL_FIT_SAFE | 低 | 3柱、境内社との区別が明確、公式本文直接確認済み |
| 6 | 高千穂神社 | 宮崎県西臼杵郡高千穂町三田井1037 | 宮崎 | SAFE | B | 未確認（独立公式ドメイン未確認） | 未実施 | 未確認 | 未確認 | 未確認 | 高 | Alternative候補、公式サイト再調査が必要 |
| 7 | 武蔵一宮 氷川女體神社 | 埼玉県さいたま市緑区宮本2-17-1 | 埼玉 | SAFE | B | 未深堀り | 未実施 | 未確認 | 未確認 | 未確認 | 中 | Alternative候補 |
| 8 | 白山神社（文京区） | 東京都文京区白山5-31-26 | 東京 | SAFE | B | 未深堀り | 未実施 | 未確認 | 未確認 | 未確認 | 中 | Alternative候補 |
| 9 | 調神社 | 埼玉県さいたま市浦和区岸町3-17-25 | 埼玉 | SAFE | B | 未深堀り | 未実施 | 未確認 | 未確認 | 未確認 | 中 | Alternative候補 |
| 10 | 鳥越神社 | 東京都台東区鳥越2-4-1 | 東京 | SAFE | B | 未深堀り | 未実施 | 未確認 | 未確認 | 未確認 | 中 | Alternative候補 |

---

## Phase 16 — Recommended 5

| shrine | id | address |
|---|---:|---|
| 湯島天満宮 | 64 | 東京都文京区湯島3-30-1 |
| 報徳二宮神社 | 92 | 神奈川県小田原市城内8-10 |
| 箭弓稲荷神社 | 76 | 埼玉県東松山市箭弓町2-5-14 |
| 水戸東照宮 | 53 | 茨城県水戸市宮町2-5-13 |
| 葛西神社 | 68 | 東京都葛飾区東金町6-10-5 |

全5社が以下を満たす:

- [x] 全件`IDENTITY_SAFE`
- [x] Source分類A（公式本文を直接WebFetch/Browser paneで確認済み）
- [x] semantic conflict `NO_CONFLICT`
- [x] Deity Evidence HIGH 5/5
- [x] History Evidence HIGH 5/5
- [x] `MODEL_FIT_SAFE` 5/5
- [x] Runtime経路でuser-visible・recommendation-visibleになることを確認済み

**品質を落として人数合わせをしていない。** 冠稲荷神社は当初Source A
分類だったが、fresh再確認の結果「ほか15柱以上」の未確定祭神と
仏教尊格「聖天宮」を含むことが判明したため、Recommended 5から除外した
（人数合わせのために採用しなかった）。千住神社（`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`）・
赤城神社等の過去のmodel-risk除外は本ドキュメントでも維持している。

---

## Phase 17 — Alternatives

| shrine | id | address | replacement reason | Source status | known limitation | model risk |
|---|---:|---|---|---|---|---|
| 高千穂神社 | 42 | 宮崎県西臼杵郡高千穂町三田井1037 | 地域分散のための参考候補（九州枠） | B（独立公式ドメイン未確認） | 独立公式サイトの存在確認が必要 | 未確認 |
| 武蔵一宮 氷川女體神社 | 72 | 埼玉県さいたま市緑区宮本2-17-1 | 汎用の代替候補 | B（未深堀り） | 深堀り未実施 | 未確認 |
| 白山神社（文京区） | 65 | 東京都文京区白山5-31-26 | 汎用の代替候補 | B（未深堀り） | 深堀り未実施 | 未確認 |
| 調神社 | 73 | 埼玉県さいたま市浦和区岸町3-17-25 | 汎用の代替候補 | B（未深堀り） | 深堀り未実施 | 未確認 |
| 冠稲荷神社 | 87 | 群馬県太田市細谷町1 | 群馬枠代替。ただし本殿「ほか15柱以上」・境内「聖天宮」（仏教尊格）を含むため通常のRecommended水準には届かない | A→再評価要 | 未確定祭神多数・仏教尊格の境内社あり | `MODEL_REVIEW_REQUIRED`寄り。採用する場合は本殿の確認できる数柱のみに限定するなど追加設計が必要 |

いずれもSeed Preparation段階で改めて公式本文の直接確認・除外範囲の
精査が必要。

---

## Phase 18 — Contract Reuse

develop HEAD（`0ecf611ee02ae06d1b0131c128b56fa3d3467bdf`）はBatch 14
Closure Audit時点からdocs追加のみで、コード変更は0件。

| contract | 状態 |
|---|---|
| seed schema・identity resolver・Source natural key・Source reuse・
  Evidence Gate・`--validate-only`・`--dry-run`・atomic import・
  Production-equivalent・Fresh Backup・idempotency・Human Execution
  Boundary・Runtime QA | いずれも無変更・再利用可能 |

**分類: `BATCH14_CONTRACT_REUSED`。** Batch 15でコード変更不要。

---

## Phase 19 — Local Test Environment Drift

`pytest-dotenv`のlocal-onlyのdriftをfreshに再確認した。

- requirementsに未宣言・CI未install・local-onlyのdrift
- 本ドキュメントではpackage変更を行っていない

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）。**

---

## Phase 20 — Batch Size

Batch 8–14実績（各5社）から:

- **Source research負荷**: 5社で管理可能。10社では確認漏れリスクが
  増す（冠稲荷神社のように、一見Source Aでも深掘りするとcontent-model
  リスクが見つかるケースがある）
- **Evidence review負荷**: 本Batchでも水戸東照宮・葛西神社の人物神格化
  （東照宮型）という個別判断を要した。10社では見落としリスクが増す
- **model review負荷**: 冠稲荷神社を深掘りの結果、当初のA分類から
  `MODEL_REVIEW_REQUIRED`寄りへ格下げする判断が必要になった。10社
  では同様の見落としリスクがさらに増す
- **Runtime QA負荷**: Batch 14 ClosureでKnowledge Runtime Exposureが
  既に稼働していることが確認済みのため、Runtime未露出のリスクは
  実質的に存在しない。この点は5社継続の必要性を弱める材料には
  ならないが、10社拡大の直接的な後押し材料にもならない
  （Runtime側の負荷はSource research・Evidence review・model review
  の負荷とは独立している）
- **Production blast radius / failure isolation**: 5社なら1回のwriteで
  最大数十行程度の影響に留まる。10社では単純に倍

**技術的推奨: Batch 15も5社を維持する。** 10社への拡大はMother Ship
の明示判断が必要であり、本ドキュメントでは決定しない。

---

## Phase 21 — Post-Batch15 Decision Point

Batch 15 Closureで必ず再評価する項目を以下に定義する（本ドキュメント
では判断しない）。

- Knowledge Shrine coverage（Batch15後の実測値）
- complete率（Batch15後の実測値）
- remaining canonical candidates（24→19見込み、model-risk5件を除く）
- partial backlog（阿佐ヶ谷神明宮・香取神宮のHistory repair、未着手）
- Source confidence distribution（`Source Confidence Contract`が
  「未確定」としている集約方式の検討状況）
- Detail UX quality（`ShrineFactSection`の表示品質、disputed表示等）
- Recommendation Knowledge usage（`concierge_chat_candidates.py`経由の
  実利用状況）
- Evidence表示品質（`ShrinePublicSerializer`のKnowledge非接続を
  解消するかどうか）

選択肢（`knowledge-batch14-closure-batch15-reentry.md` Section 15の
Option A/B/Cを踏襲）:

- A. Batch 16へ継続（Data Coverage拡大）
- B. Runtime品質改善（Source confidence集約・`ShrinePublicSerializer`
  接続等）
- C. Partial repair（阿佐ヶ谷神明宮・香取神宮）
- D. Model repair（赤城神社・千住神社等のcontent-model設計確定）
- E. 混合運用

**本ドキュメントでは決定しない。**

---

## Phase 22 — Final Classification

- [x] candidate universe整合（fresh再導出、過去値と一致）
- [x] Recommended 5 `IDENTITY_SAFE`
- [x] Recommended 5 Source分類A
- [x] Recommended 5 semantic conflict `NO_CONFLICT`
- [x] Recommended 5 Deity/History Evidence HIGH（5/5）
- [x] Recommended 5 `MODEL_FIT_SAFE`
- [x] Recommended 5 Runtime user value確認済み
- [x] Alternativesあり（5候補）
- [x] contract reuse可能（`BATCH14_CONTRACT_REUSED`）

**`BATCH15_TARGET_SELECTION_READY`**

---

## Mother Ship Decision欄

以下は本ドキュメントでは判断せず、Mother Shipの明示判断を要する事項:

- Batch 15を5社のまま実施するか、10社へ拡大するか（Phase 20参照）
- Post-Batch15 Decision Point（Phase 21、Option A/B/C/D/E）
- 冠稲荷神社の扱い（`MODEL_REVIEW_REQUIRED`寄りとして通常Batchから
  除外したままにするか、本殿の確認できる数柱のみに限定した特別設計を
  検討するか）
- 水戸東照宮・葛西神社の人物神格化（東照宮型）パターンを今後の
  content-model標準としてどう文書化するか
- 靖國神社・千葉神社・愛宕神社・赤城神社・千住神社の扱いを将来的に
  見直すかどうか

---

## 最終報告サマリ

1. develop SHA: `0ecf611ee02ae06d1b0131c128b56fa3d3467bdf`
2. Production current state: Knowledge Shrine76・Source97・Deity210・
   History149・rel223/154（drift 0）
3. Coverage: complete74・partial2・none29（drift 0）
4. raw none: 29
5. canonical candidates: 24（fresh独立導出）
6. partial status: 2社、`PARTIAL_REPAIR_CANDIDATE`、対象外
7. exclusions: QA fixture1・unresolved identity1・duplicate3（計5件）
8. model-risk candidates: 靖國神社・千葉神社・愛宕神社・赤城神社・
   千住神社（5件、過去除外を維持）
9. Source classification: A5件（Recommended）・B多数（Alternatives）・
   C2件（榛名神社・多摩川浅間神社、追加調査要）・D1件（長太稲荷神社）
10. identity-safe count: Recommended5候補全件
11. semantic conflict: Recommended5候補全件`NO_CONFLICT`
12. Deity Evidence: Recommended5中5件HIGH
13. History Evidence: Recommended5中5件HIGH
14. content-model risk: 冠稲荷神社を深掘りの結果`MODEL_REVIEW_REQUIRED`
    寄りへ再評価しRecommended5から除外。水戸東照宮・葛西神社の人物
    神格化（東照宮型）は前例に基づき`MODEL_FIT_SAFE`と判定
15. Runtime value: `KNOWLEDGE_RUNTIME_EXPOSED`をfresh再確認（王子神社
    でHTTP200・5 deities・3 histories確認、コード変更なし）
16. regional distribution: 候補プールは東京都・関東偏重（構造的、
    Batch14から変化なし）。Recommended5は東京・神奈川・埼玉・茨城の
    4都県に分散
17. product value: `PRODUCT_VALUE_NOT_AVAILABLE`
18. selection rule: Phase 14参照
19. Top 10: 湯島天満宮・報徳二宮神社・箭弓稲荷神社・水戸東照宮・
    葛西神社・高千穂神社・武蔵一宮氷川女體神社・白山神社・調神社・
    鳥越神社
20. Recommended 5: 湯島天満宮・報徳二宮神社・箭弓稲荷神社・水戸東照宮・
    葛西神社（全件公式本文を直接WebFetch/Browser paneで確認済み）
21. Alternatives: 高千穂神社・武蔵一宮氷川女體神社・白山神社・調神社・
    冠稲荷神社（要追加設計）
22. contract reuse: `BATCH14_CONTRACT_REUSED`
23. pytest drift: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）
24. 5 vs 10 recommendation: 5社を維持、10社はMother Ship判断が必要
25. Post-Batch15 decision point: Phase 21参照（Option A/B/C/D/E、
    決定はしない）
26. remaining limitations: partial2社repair未実施・model-risk5件の
    content-model判断保留・冠稲荷神社の特別設計未着手・Alternatives
    深堀り未実施・local pytest environment drift継続
27. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch15-target-selection.md`）
28. PR: 別途作成（本ドキュメントのcommit時に作成）
29. CI: PR作成後に確認
30. final classification: `BATCH15_TARGET_SELECTION_READY`

Production DB writes = 0
Batch 15 Data writes = 0
Batch 16 = NOT_STARTED
