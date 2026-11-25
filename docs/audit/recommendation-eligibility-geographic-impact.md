> **Status: Audit only — read-only simulation.** Recommendation / Ranking / Direction Filter / Distance Boundary / Concierge / Compass のいずれのruntimeも変更していない。DB書き込みなし、DB参照なし、Knowledge / Evidence データ変更なし、migration なし、Knowledge gateのruntime実装なし。89件への制限は本監査のシミュレーション内部にのみ適用した。
>
> 本書は数値の測定と分類のみを行う。Ranking / Direction / Distance / Knowledge gate の変更提案は含まない（タスク制約）。

# Recommendation Eligibility — Geographic Availability Impact Audit

提案中のKnowledge eligibility gate（Knowledgeを持つShrineのみをRecommendation候補とする案）を適用した場合に、Concierge と Compass の地理的availabilityがどう変化するかを、現行runtimeを一切変更せずに測定する。

## 1. Metadata

| Field | Value |
|---|---|
| Task | Re-measure Concierge / Compass availability using the 89 Knowledge-usable shrines as a simulated candidate population |
| Type | **Read-only audit simulation.** No runtime change, no DB access, no data change |
| Branch | `audit/recommendation-eligibility-geographic-impact` |
| Base | `origin/develop` @ `9db3a65cb6e1d154bc2a80c84efaa0642f2d9a74`（`chore: /api/users/me/ の重複routingを整理 (#2703)`） |
| Simulation script | `scripts/audit_recommendation_eligibility_geographic_impact.py`（本PRで追加、read-only、production runtimeから参照されない） |
| Date | 2026-09-05 |

## 2. Method

### 2.1 母集団の定義（invented value なし）

| Population | 定義 | 件数 | 出典 |
|---|---|---:|---|
| **Baseline** | canonical shrine seed 全件 | **103** | `backend/temples/data/shrines_seed_clean.json`（sha256 先頭16桁 `1af2e426e85c17bd`） |
| **Gated（simulated）** | Baseline から「Knowledge未投入14件」を除外 | **89** | 除外リストは `docs/audit/shrine-geographic-knowledge-coverage.md` §6。Batch 17で不変であることは `docs/audit/shrine-geographic-batch18-candidate-selection.md` §2（「Knowledgeなし総数 14（不変）」）で確認 |

103 − 14 = 89。両母集団とも全件が `latitude` / `longitude` を持ち、座標欠損によるcandidate脱落は発生しない（実測: 欠損0件）。

### 2.2 Origin corpus（versioned / reproducible / Tokyo単一ではない）

`packages/shared/userOrigin.ts` の **`PREFECTURE_ORIGINS`（47都道府県、47座標）** をそのまま使用した（sha256 先頭16桁 `70ba9fcd5d91e224`）。これは製品自身がユーザーの「都道府県から地点を選ぶ」origin（`source: "prefecture"`）として使っている座標表であり、本監査で新たに発明したoriginは1件もない。

既存テスト内のorigin（`{lat:35.0,lng:139.0}` / `{lat:35.68,lng:139.76}` / `{lat:35.0,lng:135.0}` 等）はいずれも東京圏または合成値の単一originであり、タスク制約「Do not rely on a single Tokyo-area origin」を満たさないため採用しなかった。

Compassの評価単位は **47 origins × 8 directions = 376 cells**。

### 2.3 再利用した既存ロジック（再実装なし）

シミュレーションは以下をproduction moduleから **import して実行** している。ロジックの写しは作っていない。

| 用途 | import元 |
|---|---|
| 距離計算（haversine） | `temples.services.concierge_chat_candidates._distance_m` |
| Direction Filter | `temples.services.compass_direction_filter.filter_candidates_by_direction` |
| Distance Boundary（15/30/60km stage） | `temples.services.compass_recommendation_orchestrator._apply_compass_distance_stage` |
| 8方位ラベル | `temples.services.direction_reference._DIRECTION_LABELS` |
| goriyaku自由文の分解 | `temples.management.commands.backfill_goriyaku_tags.parse_goriyaku` |
| Need → GoriyakuTag id | `temples.domain.need_to_goriyaku_tag_ids.need_tags_to_goriyaku_ids` |
| Need tag一覧 | `temples.domain.need_tags.NEED_TAGS` |
| Distance stage定数 | `DISTANCE_STAGE_1_KM=15` / `2_KM=30` / `3_KM=60` / `EXPANSION_THRESHOLD=5` / `DEFAULT_CANDIDATE_POOL_LIMIT=60` |

閾値（15 / 30 / 60 km、expansion threshold 5、pool limit）はすべて既存コードの定数をそのまま読み出しており、本監査で新しい閾値を導入していない。

### 2.4 GoriyakuTag id ↔ label の解決

`shrines_seed_clean.json` はgoriyakuを自由文で持ち、`goriyaku_tag_ids` を持たない。そこで既存の `parse_goriyaku()` でラベル分解し、**`docs/audit/goriyaku-mapping-master-integrity.md` §4 の canonical master（39行、id 1–39、連番）** でラベル→idを解決した。この表は `backend/temples/tests/test_need_to_goriyaku_tag_ids.py` が `CANONICAL_MASTER_ID_RANGE = range(1, 40)` として参照している同じ正本である。

`backend/temples/fixtures/goriyaku_tags.json`（15行、`子宝・安産` `厄除け・方除け` 等の複合ラベル）は **この39行masterとは別系統のid空間**であり、`NEED_TO_GORIYAKU_IDS` のidとは互換性がない。したがって当該fixtureは使用していない（使用すると誤ったidで集計される）。

### 2.5 都道府県判定

`docs/audit/shrine-geographic-knowledge-coverage.md` が用いた方式（address前方一致 + Google Maps形式2件の既知例外処理）と同一。実測でも例外は同じ2件（長太稲荷神社・給田六所神社、`日本、〒NNN-NNNN …` 形式）のみで、**103件すべてが都道府県へ解決した（未解決0件）**。地方区分は同監査 §2 の定義をそのまま使用。

## 3. Validation（既存監査との突合）

本監査は独立に集計しているため、既存監査値と一致するかを先に検証した。

| 検証項目 | 本監査の実測 | 既存監査値 | 一致 |
|---|---:|---:|---|
| canonical Shrine総数 | 103 | 103（`shrine-geographic-batch18-candidate-selection.md` §2） | ✅ |
| Knowledgeあり | 89 | 89（同上） | ✅ |
| 関東 Shrine / Knowledgeあり | 68 / 55 | 68 / 55（`shrine-geographic-knowledge-coverage.md` §2） | ✅ |
| 東京都 / 群馬県 / 埼玉県 / 栃木県 / 千葉県 | 30-24 / 4-1 / 9-7 / 5-4 / 5-4 | 同一（同 §1・§6） | ✅ |
| 登録0社の都道府県数 | 17 | 17（`batch18` §2） | ✅ |
| id=1「縁結び」を持つShrine数 | 32 | 32（`goriyaku-mapping-master-integrity.md` §4 shrine_count） | ✅ |
| 39 master外へ落ちたgoriyakuラベル | **0件** | — | ラベル解決の健全性を確認 |

7項目すべて一致。以降の数値はこの基盤の上に立つ。

## 4. Baseline 103 vs Gated 89 — 全体比較

| 指標 | Baseline (103) | Gated (89) | Δ |
|---|---:|---:|---:|
| Shrine総数 | 103 | 89 | **−14（−13.6%）** |
| Shrine登録のある都道府県 | 30 | 29 | −1 |
| Shrine 0件の都道府県 | 17 | **18** | +1（宮崎県） |
| Shrine登録のある地方 | 7 / 8 | 7 / 8 | ±0 |
| Concierge candidate pool（既定パラメータ） | **100** | **89** | −11 |
| Compass 376 cells 合計 direction-filtered candidates | 4,841 | 4,183 | −658（−13.6%） |
| Compass 376 cells 合計 distance-staged candidates | 269 | 233 | −36（−13.4%） |

Compassの候補総量の減少率（−13.4〜13.6%）は母集団の減少率（−13.6%）とほぼ一致する。**全体としてはgateの影響は比例的で、特定地域に不均衡に集中してはいない**（例外は §7・§8 に記載）。

### 4.1 Concierge pool が 103 ではなく 100 である理由（既存挙動、gateとは無関係）

`build_chat_candidates()` は `pool_limit = max(limit * 5, 50)` を使う。Concierge の `DEFAULT_LIMIT = 20` → `pool_limit = 100`。したがって **103件の母集団は距離ソート前に `-popular_score, id` 順で100件へ切り詰められる**（3件が落ちる）。これはKnowledge gateとは無関係の既存挙動である。

どの3件が落ちるかは `popular_score`（runtime集計値）が決めるが、この値は versioned seed に含まれないため **リポジトリデータからは特定できない**。本監査は推測しない（§10 の bounded uncertainty として記録）。

Gated（89件）は `pool_limit=100` を下回るため切り詰めが発生しない。よってConciergeのpool差分は 103→89 の −14 ではなく **100→89 の −11** である。

Compass側は `candidate_pool_limit=60` → `pool_limit = max(300, 50) = 300` であり、103 < 300 のため **Compassでは切り詰めが一切発生しない**（母集団全件がpoolに入る）。

## 5. Concierge — candidate density impact

### 5.1 都道府県別（Shrine登録のある30都道府県のみ抜粋）

| 都道府県 | Baseline | Gated | Δ |
|---|---:|---:|---:|
| 東京都 | 30 | 24 | −6 |
| 群馬県 | 4 | 1 | −3 |
| 埼玉県 | 9 | 7 | −2 |
| 栃木県 | 5 | 4 | −1 |
| 千葉県 | 5 | 4 | −1 |
| 宮崎県 | 1 | **0** | −1 |
| 茨城県 / 神奈川県 / 京都府 / 福岡県 / その他21県 | 変化なし | 変化なし | ±0 |

減少が発生したのは **6都県のみ**。残る24都道府県は影響ゼロ。

### 5.2 地方別

| 地方 | Baseline | Gated | Δ | Coverage |
|---|---:|---:|---:|---:|
| 北海道 | 1 | 1 | ±0 | 100% |
| 東北 | 0 | 0 | ±0 | — |
| 関東 | 68 | 55 | **−13** | 80.9% |
| 中部 | 7 | 7 | ±0 | 100% |
| 近畿 | 14 | 14 | ±0 | 100% |
| 中国 | 4 | 4 | ±0 | 100% |
| 四国 | 1 | 1 | ±0 | 100% |
| 九州・沖縄 | 8 | 7 | −1 | 87.5% |

**14件の減少のうち13件（92.9%）が関東に集中している。** 関東は母集団の66.0%（68/103）を占めるため、絶対数では最大の減少だが、関東の相対coverageは80.9%であり、他地方（100%）より低い。

### 5.3 Need単位のGID evidence availability

Concierge の C1 は need tag ごとに `matched_by_gid`（`NEED_TO_GORIYAKU_IDS[need]` と候補の `goriyaku_tag_ids` の積集合）で need evidence の有無を決める。母集団内で当該needのGIDを1つ以上持つShrine数は以下。

| Need | GIDs | Baseline | Gated | Δ | 新たに0になるか |
|---|---|---:|---:|---:|---|
| love | {1,20} | 32 | 28 | −4 | No |
| relationship | {1} | 32 | 28 | −4 | No |
| marriage | {1,18} | 32 | 28 | −4 | No |
| communication | {} | **0** | **0** | ±0 | **baselineで既に0**（Mother Ship 2026-08-29 `DISABLE_GID_EVIDENCE`。gateとは無関係） |
| career | {6,12,21,27,30} | 67 | 58 | −9 | No |
| money | {4,5,28,36} | 19 | 14 | −5 | No |
| study | {9,10} | 8 | 8 | ±0 | No |
| health | {7,8,24,33,38} | 30 | 27 | −3 | No |
| mental | {11,26,28,38} | 22 | 20 | −2 | No |
| protection | {2,11,32} | 55 | 48 | −7 | No |
| courage | {12,15,18,20,24,30,38} | 19 | 18 | −1 | No |
| focus | {9,10} | 8 | 8 | ±0 | No |
| rest | {7,8} | 27 | 24 | −3 | No |
| family | {16,35} | **5** | **3** | −2 | No（ただし最小） |
| travel_safe | {3,13,14} | 10 | 10 | ±0 | No |

**Knowledge gateによって新たにzero-candidateになるneedは0件。** `communication` は baseline時点で既に0であり、これはGID evidence を意図的に無効化した既存の決定によるものでgateとは無関係。

相対減少が最大なのは **family（5→3、−40.0%）**、次いで **money（19→14、−26.3%）**。family は絶対数が3まで下がるため、地理条件と組み合わさったときに最も脆い。

## 6. Compass — Direction Filter impact

47 origins × 8 directions = **376 cells**。

| 指標 | Baseline | Gated | Δ |
|---|---:|---:|---:|
| direction filter 後に候補0 のcell | 117 (31.1%) | 118 (31.4%) | +1 |
| 方位内に候補はあるが60km圏に0 のcell | 153 (40.7%) | 157 (41.8%) | +4 |
| **最終的に候補0 のcell** | **270 (71.8%)** | **275 (73.1%)** | **+5** |
| 候補ありのcell | 106 (28.2%) | 101 (26.9%) | −5 |

**Knowledge gateによって新たに候補0になったcellは5件**（376中1.3%）。baseline時点で候補があった106 cellに対しては **4.7%** の喪失。

### 6.1 Distance stage の到達段

`_apply_compass_distance_stage()` は 15km→30km→60km の順に試し、候補数が `EXPANSION_THRESHOLD = 5` 以上になった段で止まる。

| 到達stage | Baseline | Gated |
|---|---:|---:|
| 15km で確定 | **1** cell（東京都・東、15件） | 1 cell |
| 30km で確定 | 5 cells | 4 cells |
| 60km まで拡大 | **370** cells (98.4%) | 371 cells (98.7%) |

**376 cell中370（98.4%）が最も広い60kmリングまで拡大している。** 15kmで確定するのは東京都・東の1 cellのみ。これはKnowledge gateの影響ではなく、**現行データセットの地理的密度そのもの**による既存の性質である。

gateによる stage の変化は 東京都・北東 の1件（30km stage で5件 → gated で4件となり60kmへ拡大）。zero にはならないが、ユーザーに提示される距離リングが広がる。

## 7. 15 / 30 / 60 km zero-candidate rates

方位フィルタ通過後の候補が各リング内に1件も無いcellの比率。

| リング | Baseline | Gated | Δ |
|---|---:|---:|---:|
| 15km 圏内 0件 | 342 / 376 = **91.0%** | 345 / 376 = **91.8%** | +0.8pt |
| 30km 圏内 0件 | 314 / 376 = **83.5%** | 319 / 376 = **84.8%** | +1.3pt |
| 60km 圏内 0件 | 270 / 376 = **71.8%** | 275 / 376 = **73.1%** | +1.3pt |

いずれのリングでも、gateによる悪化は **1.3ポイント以内**。既存のzero率（71.8〜91.0%）と比べて、gateの寄与は一桁小さい。

### 7.1 新たに候補0となった5 cellの内訳（全件）

| Origin | Direction | Baseline 60km圏内の候補 | 距離 | 除外理由 |
|---|---|---|---:|---|
| 群馬県 | 北東 | 赤城神社(群馬)、古峯神社(栃木) | 22.2km / 56.7km | 両方ともKnowledge未投入 |
| 群馬県 | 北西 | 榛名神社(群馬) | 19.1km | Knowledge未投入 |
| 埼玉県 | 東 | 武蔵一宮 氷川女體神社(埼玉) | **3.1km** | Knowledge未投入 |
| 千葉県 | 北 | 千葉神社(千葉) | **0.8km** | Knowledge未投入 |
| 熊本県 | 東 | 高千穂神社(宮崎) | 53.6km | Knowledge未投入 |

5 cellすべてが、baseline時点で **候補1〜2件のみで成立していた脆弱なcell** である。特に千葉県・北（0.8km）と埼玉県・東（3.1km）は、originの至近距離にある唯一の候補が落ちることで0になっている。

## 8. Knowledge gateによって新たに利用不可となる地域

| 単位 | 新たに利用不可 | 内容 |
|---|---|---|
| 地方 | **0** | 8地方のいずれもゼロにならない |
| 都道府県（Concierge母集団） | **1** | **宮崎県**（唯一のShrineである高千穂神社がKnowledge未投入 → 登録0社の県が17→18） |
| Compass cell（origin×direction） | **5** | 群馬県北東 / 群馬県北西 / 埼玉県東 / 千葉県北 / 熊本県東 |
| Need（GID evidence） | **0** | いずれのneedも新たにゼロにならない |

Compass availabilityの観点では、**宮崎県originはbaseline時点で既に8方位すべて候補0**である（宮崎市originから高千穂神社まで89.7km、60kmリング外）。したがって宮崎県の「利用不可化」はConcierge母集団の話であり、Compassの可用性は変化しない。

## 9. Availability低下要因の分離

タスク要求 (7) に従い、3つの要因を明確に分離する。

### 9.1 既存の地理的データセットギャップ（gateとは無関係）

| 事実 | 数値 |
|---|---|
| Shrine登録0件の都道府県 | **17 / 47**（青森・岩手・宮城・秋田・山形・福島・山梨・福井・岐阜・和歌山・鳥取・徳島・愛媛・高知・佐賀・長崎・鹿児島） |
| 東北地方のShrine | **0件**（6県すべて） |
| Compass 376 cell中、baselineで既に候補0 | **270 (71.8%)** |
| うち方位内に候補が1件も存在しない | 117 (31.1%) |
| うち方位内に候補はあるが60km圏外 | 153 (40.7%) |
| 60kmリングまで拡大せざるを得ないcell | 370 (98.4%) |
| 母集団の関東集中度 | 68 / 103 = **66.0%** |

Compassのavailability不足の **98.1%（270 / 275）はKnowledge gate以前から存在する**。

### 9.2 Knowledge eligibility ギャップ（gate固有）

| 事実 | 数値 |
|---|---|
| 除外されるShrine | 14 / 103（13.6%） |
| うち関東 | 13 / 14（92.9%） |
| 新たに候補0となるCompass cell | **5 / 376（1.3%）** |
| baselineで候補ありだったcellのうち失われる割合 | 5 / 106（**4.7%**） |
| 新たに0社となる都道府県 | 1（宮崎県） |
| 新たに0となるneed | 0 |
| Compass候補総量の減少 | −13.4%（母集団減少 −13.6% とほぼ比例） |

### 9.3 Direction / Distance フィルタ自体の効果（両母集団に共通）

| 段階 | Baseline | Gated |
|---|---:|---:|
| 母集団（1 originあたり） | 103 | 89 |
| 8方位合計 direction-filtered（376 cell合計） | 4,841 | 4,183 |
| distance stage 通過（376 cell合計） | **269** | **233** |
| Direction+Distanceによる縮小率 | 4,841 → 269 = **−94.4%** | 4,183 → 233 = **−94.4%** |

**Direction Filter と Distance Boundary の縮小効果（−94.4%）は、Knowledge gate の縮小効果（−13.6%）より一桁大きく、かつ両母集団で同一である。** availabilityを支配しているのは gate ではなく、方位×距離条件と Shrine の地理的分布である。

## 10. Limitations / bounded uncertainties（推測で埋めない）

1. **Concierge pool 100件の内訳は特定できない。** `-popular_score, id` 順で103→100に切り詰められる際に落ちる3件は、`popular_score` が versioned seed に無いため決定できない。本監査は該当3件を特定していない（§4.1）。
2. **本監査はProduction DBを参照していない。** 母集団は `shrines_seed_clean.json`（Shrine Seedの正本）であり、Production `Shrine` テーブルの実行時状態（後から追加された行、`popular_score`、`place_ref`、QA行）とは一致しない可能性がある。ただし §3 の7項目がすべて既存Production実測ベースの監査値と一致しているため、地理・Knowledge有無の観点では整合している。
3. **Knowledge有無は名前照合による。** 除外14件は既存監査が記録した**Shrine名**で照合しており、id照合ではない（Production idは環境間で安定しないことが `tomioka-hachimangu-identity-resolution.md` で確認済みのため）。103件は名前が一意（重複0件、実測）。
4. **`build_chat_recommendations` 以降は評価していない。** Compassの `STATE_EVIDENCE_ZERO_CANDIDATES` は本監査の対象外（Recommendation本体の実行を伴うため）。測定したのは Direction Filter と Distance Boundary までである。
5. **originはprefecture代表点（`accuracy: "approximate"`）であり、実ユーザーのdevice originではない。** 都道府県庁所在地相当の1点であるため、県内の実際の位置分布は反映していない。
6. **`goriyaku_tag_ids` は自由文からの再構成である。** Production の `Shrine.goriyaku_tags` M2Mを直接読んでいない。§3の突合（id=1が32件で一致、未解決ラベル0件）で健全性を確認しているが、Production M2Mとの完全一致を保証するものではない。

## 11. Non-Scope 確認

以下はいずれも変更していない。

- Recommendation / Ranking / scoring（`score_need` / `score_need_rank_weighted` / `RECOMMEND_C1_MAX`）
- Direction Filter / Distance Boundary のロジックおよび定数
- Concierge / Compass のruntime挙動
- `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS` / `GoriyakuTag` master
- Knowledge / Evidence データ、Shrine Seed
- Knowledge gate の runtime 実装（本監査はシミュレーションのみ）
- DB書き込み / DB参照 / migration / model

## 12. Reproduction

```bash
DJANGO_SETTINGS_MODULE=shrine_project.settings \
PYTHONPATH=backend USE_GIS=0 \
python scripts/audit_recommendation_eligibility_geographic_impact.py --json out.json
```

出力される `out.json` に、376 cell 全件（origin × direction × baseline/gated の direction/15/30/60km/stage 内訳）と Concierge の都道府県・地方・need別内訳が含まれる。スクリプトはDBへ接続せず、production runtime からは参照されない。
