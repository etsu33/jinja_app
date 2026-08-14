# Recommendation Result IA v2 Observation Policy

## 1. Purpose

Recommendation Result IA v2は、PR #2438〜#2445で主要実装が完了し、
[recommendation-result-ia-v2-final.md](../audit/recommendation-result-ia-v2-final.md)（PR #2443）でGO・Must/Should残件0と
判定された。続く[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md)（PR #2446）
では、現行Analytics ContractによるMeasurement Readinessを
CONDITIONAL GOと判定し、Primary KPI（Hero Detail CTR）・Secondary KPI
（Rendered Recommendation CTR）を確定した。

本書は、Result IA v2を**「Implementation」から「Observation /
Measurement」フェーズへ正式に移行する**ための単一の正本を定める。
何を凍結し、何を計測し、どの状態になったら次のProduct判断（新しい
Result UI改善PR着手）を再開してよいかを、ここに一本化する。

**本書は文書化のみである。production codeの変更は一切含まない**
（`git diff` 0件）。

## 2. Current Status

```text
Result IA v2:
  Implementation Complete（PR #2438〜#2445、GO判定、PR #2443）
    ↓
  Observation（本書、PR #2447相当、で正式移行）
```

- Implementation Complete: 2026-08-14（PR #2445 merge、
  `b2c043963d6b928a9ee2ca85e1de6d0d23f12a2a`）。
- Measurement Readiness: CONDITIONAL GO（PR #2446、根拠は§6/§7）。
- 本書merge時点をもって、Result IA v2は正式にObservationフェーズへ
  移行する。

## 3. Freeze Scope

観測期間中（後述§10の`PRODUCT CHANGE READY`に到達するまで）、
以下は**原則として変更しない**。

- Hero IA（`ConciergeTopRecommendationHero.tsx`の情報構造:
  name → Conclusion → Explanation-only reference → Next Action →
  Primary CTA、PR #2439/#2442確立）
- Compact IA（`ShrineCardCompact.tsx`のreason block構造、PR #2444確立）
- fallback CTA hierarchy（escape-hatchの視覚的弱体化、PR #2445確立）
- Explanation-only distinction（`reasonV4FactPriority.ts`/
  `buildHeroReasonV4Sections.ts`のdeity/shrine_history分類、PR #2442確立）
- Recommendation Authority（Signal Authority正本
  [recommendation-signal-authority.md](recommendation-signal-authority.md)、変更なし継続）
- Reason generation（`recommendation_reason_v4`/`reason_facts`生成ロジック、
  Backend、変更なし継続）
- Action Grounding（Action Suggestion生成・grounding判定、変更なし継続）
- Analytics contract（event名・property名・払い出しロジック、
  [recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §2で確認した
  現行契約を凍結）

**重大bugを除き、追加のUI polishを行わない。** 「重大bug」とは、
クラッシュ・データ破損・既存contractの意図しない後退など、Freeze
Scope自体を守るために必要な修正を指す。見た目の微調整・新機能の
追加はこれに含まれない。

## 4. Primary KPI

**Hero Detail CTR** = `shrine_detail_transition`(position=hero_primary)
÷ `concierge_result_impression`(position=hero_primary)

[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §5で確定。
PR #2438（Hero raise）・#2439（Conclusion統合）・#2440（CTA階層）・
#2442（Explanation-only区別）・#2445（fallback escape-hatch弱体化）が
直接対象とした「Heroの情報構造とPrimary CTAの見え方」に対する、
最も近い直接指標である。

## 5. Secondary KPI

**Rendered Recommendation CTR** = `shrine_detail_transition`(全position)
÷ `concierge_result_impression`(全position)

Hero Detail CTRの変化が純増か、Compactからの単純な付け替え
（cannibalization）かを切り分けるための対照指標。PR #2444がCompact
自体の理由表現も変更しているため、合算値の動きも無視できない
（[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §5）。

**Primary/Secondary以外はPrimary KPIにしない。** Save rate / Route
rate / Visit conversion / Reflection conversionは、現時点の母数
（全期間で1桁〜2桁、[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §4/§9）
ではPrimary KPIとして統計的に機能しない。traffic量が十分に蓄積された
場合にのみ、補助指標として再評価する（§11 Future Freezeとは別軸、
KPIの追加自体は本書のFreeze Scope対象外だが、現時点でPrimaryへ
昇格させる決定は行わない）。

## 6. Data Quality Gate

CTRを見る**前に**、必ず以下を確認する
（[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §7の方法論を継続適用）。

| 確認項目 | 合格基準 | 不合格時の扱い |
|---|---|---|
| `recommendationInstanceId` | 対象期間のimpression/click双方で有意な比率で存在すること | 欠損が支配的な場合、Measurement Gap（§10） |
| `primaryReasonSource` | 同上 | 同上 |
| `resultSetId` | 全件で存在すること（既存契約、通常は100%） | 欠損があれば計測基盤そのものの異常、Measurement Gap |
| `shrineId` | 全件で存在すること | 同上 |
| `rank` | 1/2/3等の値が分布していること | 極端な偏り・欠損はMeasurement Gap |
| duplicate impression | `(resultSetId, shrineId, position)`の重複を認識し、CTR分母は**生event count**で計算していること（`resultSetId`ユニーク化ではない、[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §7.3） | 生event count以外の分母を使った比較結果は採用しない |
| orphan click | `shrine_detail_transition`の`resultSetId`欠損が無視できる比率であること | 有意な比率で欠損があればMeasurement Gap |

**identity/provenance（`recommendationInstanceId`/`primaryReasonSource`）
に欠損がある場合、Product比較（CTR改善/悪化の判定）ではなく
Measurement Gapとして扱う。** 判断を先送りすることが正しい対応であり、
欠損を無視して見かけ上のCTRだけで判断してはならない。

## 7. Traffic Quality Gate

Mother Ship自身によるQA/開発操作由来のtrafficを、organic usageとして
扱わない（[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §7.6で確立した方法論を
継続適用）。最低限、以下を確認する。

- **distinct user**（`distinct_id`のユニーク数）
- **distinct threadId**（相談スレッドの多様性）
- **Hero impression**（`concierge_result_impression`, position=hero_primary件数）
- **Hero detail transition**（`shrine_detail_transition`, position=hero_primary件数）

判定基準（[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §7.6の観測結果を
基準線とする）:

- `accessLevel`分布が`premium`に極端に偏っている（観測されたQA基準線:
  95.3%）、かつ/または`distinct_id`が一桁台に留まっている場合、
  そのtrafficは引き続きQA的であるとみなす。
- 上記が解消され、`accessLevel`分布がanonymous/free中心へ移行し、
  `distinct_id`・`distinct threadId`が明確に増加した時点を、organic
  trafficへの切り替わりの兆候として扱う。

**session diversity不足時は、CTR改善・悪化のいずれも結論にしない。**

## 8. Segmentation

[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §6の技術的可否判定を、
Observation期間中の運用基準として固定する。

| Segment | 状態 |
|---|---|
| Hero / Compact（`position`） | Ready Now |
| rank（`recommendationRank`） | Ready Now |
| `primaryReasonSource` / fallback（`isFallbackRecommendation`） | PR #2429以降のtrafficに限り有効。それ以前のデータとは混在させない |
| Web / Mobile | 実データなし（Measurement Gap、§10・§12） |
| anonymous / authenticated | `card_view`の`accessLevel`との`resultSetId` JOINが必要（`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`、未検証のまま） |

## 9. Observation Rules

Hero Detail CTRを含むいかなる比較・判断も、以下の順序を必ず踏む。
順序を飛ばしてCTRの数値だけを見て判断しない。

1. post-IA v2 traffic（PR #2445 merge以降のevent）が存在することを
   確認する。
2. §6 Data Quality Gateを通過することを確認する。
3. §7 Traffic Quality Gateに基づき、QA trafficとorganic trafficを
   分離する。
4. session diversity（distinct user / distinct threadId）を確認する。
5. Hero Detail CTRを算出する（§4）。
6. Rendered Recommendation CTRを併記する（§5、cannibalization確認）。
7. Authority（`primaryReasonSource`）・fallback・rank別に確認する
   （§8のsegmentation可否に従う）。
8. 次の改善仮説を**1つだけ**選ぶ（複数の仮説を同時に走らせない）。

## 10. Decision States

Observation期間中の状態は、常に以下3つのいずれかに分類する。

### WAIT FOR DATA

traffic不足、またはsession diversity不足（§7・§9-1/4）。現時点の
既定状態（[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §8: PR #2445
merge以降のtrafficは0件）。

### MEASUREMENT GAP

identity/provenance欠損（`recommendationInstanceId`/
`primaryReasonSource`）、duplicate impression未処理、orphan clickなど、
計測Contract自体に問題がある状態（§6）。CTRの数値が出ていても、この
状態ではProduct判断の根拠として採用しない。

### PRODUCT CHANGE READY

trafficとmeasurement qualityが十分で（§6・§7・§9のすべてを通過）、
明確な行動差（Hero Detail CTRの有意な変化、Rendered Recommendation
CTRとの整合、Authority/fallback/rank別の一貫した傾向）が確認できた
状態。

**`PRODUCT CHANGE READY`に到達するまで、新しいResult UI改善PRを
開始しない。** これはFreeze Scope（§3）を実効あるものにするための
Gateであり、Observation Ruleの最終ステップ（§9-8「次の改善仮説を1つ
だけ選ぶ」）は、この状態に到達して初めて実行してよい。

## 11. Future Freeze

以下は、[recommendation-result-ia-v2-final.md](../audit/recommendation-result-ia-v2-final.md) §15で再評価済みのFuture候補
であり、本書でも引き続き凍結する。

- Visual confidence indicator
- trustMetadata gating
- Personalization surfacing
- Compact trustMetadata
- grounded / generic_safe Action visual distinction

**データがこれらの必要性を示した場合のみ再検討する。** 「データが
示す」とは、§10 `PRODUCT CHANGE READY`到達後のObservationにおいて、
これらのFuture候補が対応しうる具体的なギャップ（例: fallback候補の
体感信頼度が低いことがsegment別CTRで示される等）が実測で確認された
場合を指す。着想や一般論だけでの再検討は行わない。

## 12. Next Product Decision Gate

1. 本書merge後、最初にすべきことは**待つこと**である。新しいコードの
   着手ではない。
2. `PRODUCT CHANGE READY`（§10）に到達するまで、Result UI改善の新規
   PRを開始しない。これは[recommendation-result-v2-measurement-baseline.md](../audit/recommendation-result-v2-measurement-baseline.md) §14
   「Next Product Decision Gate」で示された推奨と同じ結論であり、
   本書によって正式なPolicyとして固定する。
3. 次にProduct判断が必要になるタイミングは、以下のいずれかが発生した
   時点である。
   - §9 Observation Rulesの8ステップを一巡し、`PRODUCT CHANGE READY`
     と判定できるだけのtraffic・data qualityが揃った場合。
   - Freeze Scope（§3）の対象範囲で重大bugが発見された場合
     （この場合も、Freeze Scopeの原状回復を目的とした最小修正に限る）。
4. `PRODUCT CHANGE READY`到達時、次のPRは「Observation結果に基づく
   改善仮説1つ」に限定してスコープする（§9-8）。複数の改善を同時に
   積み込まない。
5. Mobile segmentation（§8）・`accessLevel` JOIN契約
   （`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`、§8）は、それぞれ独立した
   小さな監査タスクとして、Observation期間中いつでも並行して検証して
   よい（Result UI自体を変更しないため、Freeze Scopeとは独立）。

---

Production code changes = 0
UI changes = 0
Ranking changes = 0
Recommendation Authority changes = 0
Reason generation changes = 0
Action Grounding changes = 0
Analytics schema changes = 0
Migrations = 0
