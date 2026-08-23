> **Status: Complete. Audit only — `NEED_TEXT_WEIGHTS`を含むProduction Codeは変更していない。**

# Compass Protection Text Evidence Overlap Audit

## 1. Scope

`protection`へText Coverage（SET-A）を実装する価値を、既存goriyaku_tag Evidenceとの重複構造の実測に基づいて判定する。AUDIT ONLY、read-onlyのみ、実装は一切行っていない。

## 2. Baseline

- 作業開始時点のlocal `develop` HEAD = `origin/develop` HEAD = `f50e968694235826721f79c9fce54501bd1f3a91`
- 専用worktree（`../jinja_app-compass-protection-text-overlap`、branch `audit/compass-protection-text-evidence-overlap`）をこのSHAから作成。main working treeは変更していない
- PR #2551相当（`docs/audit/compass-protection-text-coverage-boundary.md`）・PR #2549相当（Reason/Lead）・PR #2545相当（Mapping `{11,32,2}`）をfresh readで確認、drift無し

## 3. SET-A

```
厄除: 2, 厄払い: 3, 浄化: 2, 守護: 1, 守ってほしい: 1
```

`NEED_TEXT_WEIGHTS["mental"]`から現行値をそのまま抽出（fresh read）。前Audit記載値と完全一致、drift無し。

## 4. Fixture Population

既存Purpose Sensitivity/Protection Audit群と同一fixture: origin=(35.662443, 139.5920237)、direction_context={referenceDirections:["東"], calculationMethod:"annual_monthly_kyusei_v1"}。

```
direction_candidate_count = 23
distance_stage_km = 15
distance_candidate_count = 12
distance_candidate_ids = [21, 103, 1, 61, 59, 60, 43, 58, 46, 50, 45, 44]
```

既存監査（`compass-purpose-goriyaku-mapping.md`等）と完全一致、再現性確認済み。

## 5. GID/Text Evidence Groups（Fixture-level）

| Shrine | goriyaku IDs | goriyaku text | gid match | SET-A hits | text match |
|---|---|---|---|---|---|
| 長太稲荷神社(21) | [] | "" | NO | [] | NO |
| 長太稲荷神社(103) | [] | "" | NO | [] | NO |
| 明治神宮(1) | [1,2,3] | 縁結び・厄除け・交通安全 | **YES** | 厄除 | **YES** |
| 花園神社(61) | [4,6,29] | 商売繁盛・芸能運・開運 | NO | [] | NO |
| 乃木神社(59) | [7,11,12] | 仕事運・勝運・家内安全 | **YES** | [] | NO |
| 赤坂氷川神社(60) | [1,2,12] | 縁結び・厄除け・仕事運 | **YES** | 厄除 | **YES** |
| 日枝神社(43) | [4,12,27] | 仕事運・出世運・商売繁盛 | NO | [] | NO |
| 靖國神社(58) | [2,7,11] | 厄除け・家内安全・勝運 | **YES** | 厄除 | **YES** |
| 愛宕神社(46) | [12,27] | 出世運・仕事運 | NO | [] | NO |
| 品川神社(50) | [6,28] | 開運・金運 | NO | [] | NO |
| 芝大神宮(45) | [1,4] | 縁結び・商売繁盛 | NO | [] | NO |
| 東京大神宮(44) | [1,20] | 縁結び・恋愛成就 | NO | [] | NO |

分類（4 Group、排他的）:

| Group | Shrine count | Shrine IDs |
|---|---:|---|
| GID_ONLY | 1 | [59] |
| **TEXT_ONLY** | **0** | [] |
| BOTH | 3 | [1, 60, 58] |
| NONE | 8 | [21, 103, 61, 43, 46, 50, 45, 44] |

## 6. Coverage KPIs（Fixture-level）

- **KPI-1 TEXT_ONLY_COUNT = 0**
- KPI-2 BOTH_COUNT = 3
- KPI-3 GID_ONLY_COUNT = 1
- KPI-4 TEXT_ONLY_RATE = 0/12 = 0.000
- KPI-5 OVERLAP_RATE = 3/3 = 1.000（text matchした候補は100%が既にgid matchも成立していた）

**このfixtureに限れば、SET-Aは新規coverageを一切生まず、既存gid matchへ100%重複する。**

## 7. Score Accumulation Trace

`_prefilter_candidates_for_need()`（`concierge_chat_ranking.py` L1592-1610）が加算する`score`と、`_attach_breakdown()`側の`score_need_rank_weighted`（同 L1149、`sum(text_score_by_tag.values()) * 1.2`）が、gid由来のscoreとtext由来のscoreを**tagごとに独立して単純加算**することをコード上確認済み（`compass-protection-text-coverage-boundary.md` §7で確認済み、今回実測で再確認）。

BOTH代表: 明治神宮(id=1)

| Metric | Before | After（SET-A patch） | Delta |
|---|---:|---:|---:|
| score_need | 1 | 1 | 0 |
| matched_need_tags | ["protection"] | ["protection"] | 変化なし |
| text_score_by_tag | {} | {"protection": 2} | +2 |
| `_score_total` | 0.6069056032997854 | **1.3269056032997855** | **+0.72（約2.19倍）** |

TEXT_ONLY代表: **N/A**（Group該当なし、§5参照）

## 8. New Discovery vs Existing Boost

未trim（12件全件）のBefore/After比較（read-only、patch.dict使用、tracked code変更なし）:

| Shrine | Classification | Before score_need | After score_need | Before score | After score |
|---|---|---:|---:|---:|---:|
| 明治神宮(1) | **EXISTING_BOOST** | 1 | 1 | 0.6069 | 1.3269 |
| 赤坂氷川神社(60) | **EXISTING_BOOST** | 1 | 1 | 0.6019 | 1.3219 |
| 靖國神社(58) | **EXISTING_BOOST** | 1 | 1 | 0.6012 | 1.3212 |
| 乃木神社(59) | NO_EFFECT | 1 | 1 | 0.6027 | 0.6027（不変） |
| 他8件 | NO_EFFECT | 0 | 0 | 不変 | 不変 |

集計:
- **NEW_DISCOVERY_COUNT = 0**
- **EXISTING_BOOST_COUNT = 3**
- NO_EFFECT_COUNT = 9

**このfixtureで観測された効果は100%がEXISTING_BOOST、0%がNEW_DISCOVERYである。**

## 9. Ranking / Top3 Churn

| Rank | Before | After | Cause |
|---:|---|---|---|
| 1 | 明治神宮(1) | 明治神宮(1) | 変化なし（ただしscoreは倍増） |
| 2 | 乃木神社(59) | 赤坂氷川神社(60) | **EXISTING_BOOST**（赤坂氷川神社のscoreが0.60→1.32へ上昇し乃木神社を追い抜いた） |
| 3 | 赤坂氷川神社(60) | 靖國神社(58) | **EXISTING_BOOST**（靖國神社のscoreが0.60→1.32へ上昇） |
| （脱落） | — | 乃木神社(59)はrank4へ降格 | 乃木神社自身のscoreは不変（0.6026568285963632で完全一致）——他候補がboostされた結果の相対的降格 |

前Audit（`compass-protection-text-coverage-boundary.md`）で観測された「乃木神社 → 靖國神社」の入替が**再現した**（`BASELINE_DRIFT`なし）。

## 10. Churn Cause Decomposition

Top3変化3件全て（明治神宮のscore上昇、赤坂氷川神社のrank上昇、靖國神社の新規Top3入り）は、§8の分類上**すべてEXISTING_BOOSTに起因**——NEW_DISCOVERYに起因する変化は0件。**乃木神社の降格は「新しい正しい候補が上がった」結果ではなく、「既存match候補が二重boostされた」ことの直接的な帰結である。**

## 11. DB-wide Coverage

隔離local DB全101 Shrine行を対象に、既存ORM（`manage.py shell`での一回限りread-onlyクエリ、tracked scriptは作成せず）で同じ4 Groupへ分類した。

| Group | DB-wide Shrine Count |
|---|---:|
| GID_ONLY | 4 |
| **TEXT_ONLY** | **2** |
| BOTH | **51** |
| NONE | 44 |

**DB-wide TEXT_ONLY_COUNT = 2（全101件中）。DB-wide BOTH_COUNT = 51（全101件中、過半数）。BOTH:TEXT_ONLY 比は約25:1。**

## 12. TEXT_ONLY Quality Review

DB-wide TEXT_ONLY 2件、全件確認した。

| Shrine | Hit | goriyaku_tags実態 | Classification | Reason |
|---|---|---|---|---|
| 阿蘇神社(100) | "守護"（"農業守護"の部分文字列） | [(7,家内安全),(39,農業守護),(6,開運)] | **QUESTIONABLE** | 「農業守護」は農業に特化した守護概念であり、protectionの想定する「厄除け・守り」より意味範囲が狭く異なる。文字列一致は技術的に正しいが概念としては別物 |
| 小網神社(62) | "厄除"（"強運厄除け"の部分文字列） | [(4,商売繁盛),(30,強運厄除け),(28,金運)] | **TRUE_POSITIVE** | 実際に厄除け関連のgoriyaku_tagを持つが、それが独立した「厄除け」(id=2)ではなく複合タグ「強運厄除け」(id=30、`NEED_TO_GORIYAKU_IDS["career"]`のQUESTIONABLE語彙としても登場する別タグ)としてbackfillされているため、現行protectionのgid mapping`{11,32,2}`では拾えない。Text Coverageが正しくこのgid mappingの穴を補完する実例 |

**TRUE_POSITIVE 1件、QUESTIONABLE 1件、FALSE_POSITIVE 0件。** Text-onlyの母数自体が2件と非常に少ないため、量的な価値判断としては限定的だが、質的には少なくとも1件（小網神社）は正当なgid mapping gapの補完例である。

## 13. mental SET-A Contribution

DB-wide（101 Shrine全件）、mentalの文脈でSET-A 5語の寄与を確認した。

| Metric | Count |
|---|---:|
| SET-A語hit Shrine数（mental文脈） | 53 |
| SET-Aのみでmental matchしている（他のmental語彙も同時hitしていない）Shrine数 | **53（全件）** |
| 他mental語彙（心を整える/不安/落ち着く/静か）も同時hitしているShrine数 | **0** |

**mentalの現行`NEED_TEXT_WEIGHTS`のうち、goriyaku自由記述に対して実際にhitしているのは101件中53件だが、その53件全てがSET-A（厄除/厄払い/浄化/守護/守ってほしい）由来であり、mental固有の語彙（心を整える・不安・落ち着く・静か）は1件もhitしていない。** これは構造的に説明できる——goriyaku自由記述は「神社が提供する利益」を記述するものであり、「不安」「落ち込み」等のユーザー側の感情状態を表す語がそこに出現することは通常ない。

## 14. Mental Removal Regression（Phase 15）

`NEED_TEXT_WEIGHTS["mental"]`からSET-A 5語のみを一時除去（`patch.dict`、tracked code変更なし）し、同一fixtureでmental purposeを実行した。

| Metric | Before（SET-A含む） | After（SET-A除去） | Delta |
|---|---|---|---|
| candidate count（score_need>0） | 5（靖國神社/明治神宮/赤坂氷川神社/乃木神社/品川神社） | **3**（乃木神社/靖國神社/品川神社） | **-2** |
| 明治神宮のmatch | score_need=1（`mental:text`のみ、gidなし） | score_need=0（マッチ消滅） | **完全に消滅** |
| 赤坂氷川神社のmatch | score_need=1（`mental:text`のみ、gidなし） | score_need=0（マッチ消滅） | **完全に消滅** |

Top3:

| Rank | Before | After |
|---:|---|---|
| 1 | 靖國神社(58) | 乃木神社(59) |
| 2 | 明治神宮(1) | 靖國神社(58) |
| 3 | 赤坂氷川神社(60) | 品川神社(50) |

**Top3の2/3枠が入れ替わり、5件あった候補matchが3件へ減少した。明治神宮・赤坂氷川神社はSET-Aのみでmentalへ一致していた（gidでの独立したmental一致経路を持たない）ため、SET-A除去で完全にmental purposeの候補から脱落する。**

**mental Removal影響: 大。**

## 15. Cross-Purpose Boundary Assessment

- protection TEXT_ONLY: fixture-level = 0、DB-wide = 2（ほぼ無し）
- mental Removal影響: 大（実測確認済み、§14）

**該当Case: CASE 3**——「protection TEXT_ONLYほぼ無し、mental Removal影響大 → protection Text追加の価値が弱い」

補足: CASE 3はSET-Aをmentalから除去することを推奨するものではない（本監査はmental語彙の実削除を禁止されている、制約#2）。この判定は「SET-Aをprotectionへ**追加**することの限界的価値」についてのものであり、「mentalに置かれたままのSET-Aを今後どうするか」は別の判断（`compass-protection-text-coverage-boundary.md` §16のMother Ship Decision Inputsに既述）。

## 16. Scoring Options（設計候補、実装せず）

| Option | Coverage | Double-count Risk | Ranking Churn | Implementation Complexity |
|---|---|---|---|---|
| **A — Current Additive**（既存仕様） | フル（gid+text両方カウント） | **高**（§7-10で実測、BOTH群でscoreが約2.2倍） | 高（実測: Top3 2/3枠変化） | 最小（新規辞書追加のみ） |
| B — Text as Fallback（gid未matchの場合のみtext使用） | KPI-1相当のみ（TEXT_ONLY群のみが恩恵を受ける） | なし（gid match時はtext加算されない） | 低（BOTH群は現状維持、TEXT_ONLY群のみ新規match） | 中（既存`_prefilter_candidates_for_need`のtag loop内へ条件分岐が必要） |
| C — Deduplicated Evidence（同一意味なら高い方のみ採用） | フル | 低（意味的に単一Evidenceとして扱う） | 中（BOTHのscoreはgid/textのうち高い方のみ、現行の加算よりは小さいが0ではない） | 中〜高（「同一意味」の判定基準を新設する必要） |
| D — Candidate Discovery Only（textはprefilter専用、ranking scoreへ非加点） | KPI-1相当のみ | なし | 最小（scoreへの影響ゼロ、candidate選定順のみ変化） | 中（scoreパスとprefilterパスの分離が必要） |

**B/C/Dはいずれも既存仕様ではなく、今回のAuditで新設提案するのみ**（制約通り採用・実装しない）。

## 17. Text Coverage Recommendation

判断材料:

1. DB-wide TEXT_ONLY_COUNT = 2/101（約2%）——極めて小さい
2. TRUE_POSITIVE率 = 1/2（50%、ただし母数が2件のみで統計的信頼度は低い）
3. BOTH_COUNT = 51/101（約50%）——Option A（既存仕様）採用時、この過半数が二重加点の対象になる
4. Top3 churn原因 = 実測で100%がEXISTING_BOOST（§10）、意図された"coverage expansion"としての効果は本fixtureでは0%
5. mental Removal影響 = 大（§14で実測確認、SET-Aがmentalの主要なtext match経路になっている）
6. double-count risk = 高（§7実測、scoreが約2.2倍）

**総合判定: `IMPLEMENT_WITH_SCORING_CHANGE_REQUIRED`寄り、または`DO_NOT_IMPLEMENT_YET`。**

現行のOption A（既存Additive方式）でSET-Aをそのまま追加した場合、新規coverageの実質的な価値（KPI-1が示す通り非常に小さい）に対して、既存match候補への意図しないscore増幅・Top3 churn（§7-10で実測確認済み）という副作用が明確に上回る。§16のOption B/Dのような、既存gid Evidenceとの二重加点を避ける設計変更を検討した上での実装が望ましいと考えられるが、**これはscoring logic自体の変更を要するため、本監査の制約（scoring logic変更禁止）の範囲外であり、最終Product判断は母艦へ返す。**

## 18. Implementation Scope Proposal

実測結果を踏まえ、当初想定していた3 PR構成（PR-A: Text Coverage単体、PR-B: Evidence Dedup、PR-C: Mental Vocabulary Cleanup）のうち：

- **PR-A（現行Additive方式でのSET-A単純追加）は、本監査のEvidenceにより推奨しない**（§17）
- PR-B相当（Scoring Option B/C/D等のEvidence Dedup設計）が、SET-A導入の前提として先に必要になる可能性が高い——ただしこれはscoring logic変更であり、本監査のスコープ外。設計自体を今回のAuditでは行っていない（§16は選択肢の提示のみ）
- PR-C（mental語彙のcleanup/移動）は制約により評価対象外のまま。§14の実測は「除去した場合の影響が大きい」ことを示すのみで、除去すべきという結論ではない

具体的なPR設計は、Scoring Option（§16）についての母艦判断が確定してから行うべきと考える。

## 19. Mother Ship Decision Inputs

- 現行Additive方式（Option A）のままSET-Aを追加することを許容するか（§7-10のscore増幅・churnを許容範囲と判断するか）
- Option B/C/D（Evidence Dedup系）の設計・実装を先行させるか
- SET-A（DB-wide TEXT_ONLY=2件、うちTRUE_POSITIVE 1件）という小さいが非ゼロの新規coverage価値を、現状のリスクと比較してどう評価するか
- mentalに残るSET-Aの扱い（維持・整理）は別タスクとするか

## 20. Out of Scope

`NEED_TEXT_WEIGHTS`（実装0件、simulationのみ）・mental語彙（削除0件、simulationのみ）・`NEED_TO_GORIYAKU_IDS`・Reason/Lead・Ranking weight・scoring logic・Purpose taxonomy・consultation_axis・DB/GoriyakuTag master・migration・frontendはいずれも変更していない（`git diff --stat`で確認）。

## 21. Limitations

- Fixture-levelの分析は1つの固定origin/directionのみに基づく。他のorigin/directionでのTEXT_ONLY出現率は未検証（DB-wide分析はこの限界を補うが、Direction/Distance Filterを通していない全件ベースの数値である点に注意）
- TEXT_ONLY Quality Reviewの母数が2件と少なく、TRUE_POSITIVE率（50%）の統計的信頼性は低い
- Scoring Option B/C/Dは設計候補の提示のみであり、実装可能性・既存contractとの整合性の詳細検証は行っていない
- mental Removal Simulationは1 fixtureのみで実施。DB-wide/他fixtureでの影響度は未測定
