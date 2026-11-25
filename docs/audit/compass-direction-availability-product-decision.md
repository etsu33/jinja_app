> **Status: `PROPOSED — MOTHER SHIP DECISION REQUIRED`**
>
> [compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)（PR
> [#2496](https://github.com/etsu33/jinja_app/pull/2496)、merged）は、既知の
> Production QAリクエストが`direction_filter_unavailable`になった理由を
> 「年盤∩月盤の吉方位交差が空集合」という構造的な性質として確定し、これを
> `A — EXPECTED FAIL-SAFE`と分類した。本監査はその続きとして、**この空集合
> 発生頻度を体系的に定量化し**、現在のCompass Product Promise・UIコピーとの
> 整合性を評価し、Mother Shipが採り得る5つの製品オプション（現状維持・
> 第一級結果化・月盤フォールバック・年盤フォールバック・スコアモデル）を
> 比較した。
>
> **中心的な発見**: 9種類の本命星 × 12節気月バケット × 9年（合計972ケース）
> という決定的な行列で、無改変の本番`kyusei.py`関数を直接実行した結果、
> **全体の46.5%（452/972）が空の交差（direction_filter_unavailable相当）**
> になった。これはコイントスに近い頻度であり、現在のUIコピー・Product
> Promiseが暗黙に示唆する「通常は方向が返る」という期待とは食い違っている。
>
> 現在の失敗時UIコピー「生年月日または出発地点をご確認のうえ、もう一度
> お試しください」は、実際の主要因（有効な入力からの正当な計算結果）とは
> 異なる「入力ミス」を示唆しており、**MISLEADING**と判定する。
>
> 本監査はコード変更を一切行っていない。最終判断はMother Shipに委ねる。

---

## 1. Executive Summary

[compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)
が確立した根本原因（年盤∩月盤の交差が空集合になり得る、EXPECTED FAIL-SAFE）
を出発点として、以下を実施した。

1. 実際の無改変production `kyusei.py`関数を用いた、9本命星×12節気月バケット
   ×9年（972ケース）の決定的な行列による頻度定量化
2. 現在のProduct Promise・Runtime Contract・実装・UIコピーの4層比較
3. 5つの製品オプション（現状維持／第一級結果化／月盤フォールバック／年盤
   フォールバック／スコアモデル）の評価
4. Concierge Compat Modeとの共有関数リスクの実地確認（`kyusei.py`の
   `planned_visit_lucky_directions`は`api_views_concierge.py`からも直接
   呼び出されていることを確認 — §19）

**推奨（Mother Ship判断待ち）**: **B — 「今月は年盤と月盤で重なる方位が
ありません」を第一級のCompass結果としてモデル化する**。理由は§22で詳述する。

本監査ではコード変更・契約変更・実装を一切行っていない。

---

## 2. Background / #2496

[compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)
（PR [#2496](https://github.com/etsu33/jinja_app/pull/2496)、merged）が確立
した事実を正本として引き継ぐ（再調査していない）:

```
direction_context = None
  ← build_compass_direction_runtime()がplanned_visit_lucky_directions()の
    luckyDirections（年盤∩月盤の交差）が空リストの場合にNoneを返す
  → orchestratorがSTATE_DIRECTION_FILTER_UNAVAILABLEへマッピング
  → frontend UIが「方向の参考情報を計算できませんでした」を表示

Final Classification（#2496）: A — EXPECTED FAIL-SAFE, Confidence: HIGH
```

本監査は、この「EXPECTED」という判定自体は変更しない。問うのは
「頻度がどの程度か」「その頻度に対して現在のProduct Promiseとfail-safe
コピーが適切か」「Mother Shipが取り得る選択肢は何か」である。

---

## 3. Current Product Promise

[compass-product-contract.md](../product/compass-product-contract.md)
Section 2より、**DOCUMENTED PROMISE（一文定義）**:

```
時間・方位runtime signalと目的から、今月意識したい方向と参拝候補を示す。
```

User-facing候補コピー（同文書、評価済み: SUPPORTED WITH CLARIFICATION）:

```
今月の流れと目的から、向かう方向と参拝候補を見つけます。
```

いずれの文言も、「方向が見つからない場合がある」というヘッジ・条件節を
含まない。断定形（「示す」「見つけます」）で記述されている。

[compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md)
Section 8 Fail-safe Contractは、以下のケースを**明示的に**列挙している:

```
生年月日が欠落 / originが欠落 / 方位計算が例外で失敗 / target_dateが不正 /
節気月境界付近
```

**「有効なbirthdate・有効なtarget_dateだが年盤∩月盤の交差が空」というケース
は、この表に明示的な行として存在しない。** これは前回監査
（[compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)
§23 Open Question 3）で既に指摘した通りである。

---

## 4. Current Runtime Behavior

**IMPLEMENTED BEHAVIOR**（現行`develop`、コード直読）:

`build_compass_direction_runtime()`（[compass_runtime.py:50-52](../../backend/temples/services/compass_runtime.py)）
は、`planned_visit_lucky_directions()`が返す`luckyDirections`（年盤∩月盤の
交差）が空リストの場合、**欠落ケース（birthdate/target_date無効）と全く
同じ`None`を返す**。呼び出し元（orchestrator）から見ると、この2つのケース
——「入力自体が不十分」と「入力は十分だが計算結果が空」——は**区別不能**
である。両方とも同一の`STATE_DIRECTION_FILTER_UNAVAILABLE`にマッピングされ、
同一のUI状態・同一のコピーが表示される。

**CURRENT USER-FACING EXPERIENCE**:

```
「方向の参考情報を計算できませんでした」
「生年月日または出発地点をご確認のうえ、もう一度お試しください。」
```

（[CompassClient.tsx:225-231](../../apps/web/src/features/compass/CompassClient.tsx)）

このコピーは、原因を「生年月日または出発地点」という**入力の問題**に
明示的に帰属させている。しかし§6-10で示す通り、この状態の主要因（実運用
上のボリューム）は入力の問題ではなく、正当な計算結果である可能性が高い。

---

## 5. Methodology

**目的**: `annual lucky directions ∩ monthly lucky directions = 空集合`が
現行の本番アルゴリズムの下でどの程度の頻度で発生するかを定量化する。

**原則**:

- 実際のユーザーbirthdate・座標・PostHog `distinct_id`・自由記述は一切
  使用しない（本監査全体を通じて、これらのいずれも参照していない）。
- アルゴリズムを簡略化・再実装せず、無改変の本番
  `backend/temples/domain/kyusei.py`関数（`honmei_star`・
  `planned_visit_lucky_directions`）を直接呼び出す。
- 分析はセッション外のスクラッチパッド（`/private/tmp/...`）に置いた
  一時スクリプトで実行し、リポジトリには一切コミットしない（§30の要件）。

**サンプリング設計**（9本命星 × 12節気月バケット × 9年 = 972ケース）:

1. **9本命星**: `honmei_star(birthdate)`は生まれ年（節分境界考慮）にのみ
   依存するため、実在しない合成birthdate（`1975-06-15`〜`1999-06-15`の
   範囲で年を走査）から、9種類の`num`（1-9）それぞれについて1つの代表
   birthdateを機械的に選定した。実在ユーザーのbirthdateとは一切対応しない。
2. **12節気月バケット**: `kyusei._solar_month_index()`のソースコードが
   定義する実際の境界（固定近似日: 2/4, 3/6, 4/5, 5/6, 6/6, 7/7, 8/8, 9/8,
   10/8, 11/7, 12/7、および年またぎの「12/7〜1/5」バケット）を直接読み取り、
   各バケットの中間付近の代表日付（例: バケット6「8/8〜9/7」→8月20日、
   これは既知QAリクエストが属したバケットと同一）を選定した。単純な暦月
   （1日〜末日）のマッピングは使用していない。
3. **9年**（2022年〜2030年）: `year_star()`のki_yearに基づく年盤が9を法
   として周期を持つため、9年分を走査することで年盤側の周期を完全に一巡
   させた。

**実行コマンド（再現用、PII非公開）**:

```python
from django.conf import settings
settings.configure(USE_TZ=True, TIME_ZONE="Asia/Tokyo")
import django; django.setup()
from temples.domain.kyusei import honmei_star, planned_visit_lucky_directions

# 9本命星の代表birthdate（合成、1975-1999年の中から機械的に選定）
# 12節気月バケットの代表日付（_solar_month_index()の境界定義から導出）
# 2022-2030年（9年、年盤の9周期を一巡）
# の全組み合わせ(9x12x9=972)について
# planned_visit_lucky_directions(birthdate, target_date) を実行し、
# luckyDirectionsが空かどうかを集計する。
```

実行環境: `backend`ディレクトリから`PYTHONPATH`をセットし、Django設定は
`settings.configure(USE_TZ=True, TIME_ZONE="Asia/Tokyo")`の最小構成のみ
（DBアクセスなし、production settingsは使用していない）。

**サンプルが代表するもの／しないもの**: この972ケースは、「9本命星×12
節気月バケット×9年」という**決定的（deterministic）な網羅**であり、実際
のユーザー分布（生年の偏り、利用時期の偏り）を統計的にサンプリングした
ものではない。したがって「実際のユーザーの何%がこの状態に遭遇するか」
という問いには直接答えない——答えるのは「アルゴリズム自体が、入力空間を
均等に走査した場合にどの程度の頻度でこの状態になるか」という、アルゴ
リズムの構造的性質のみである（§10 Interpretation Boundary参照）。

---

## 6. Availability Frequency Results

```
TOTAL CASES: 972
AVAILABLE（非空の交差）:   520 (53.5%)
EMPTY INTERSECTION（direction_filter_unavailable相当）: 452 (46.5%)
NONE RESULT（合成birthdate自体が無効というエラー）: 0
```

972ケース中、**46.5%が空の交差**になった。これは前回監査
（[#2496](https://github.com/etsu33/jinja_app/pull/2496)）が単一の日付
（2026-08-20、本命星9種類中5種類=55.6%）で示した結果と同じ桁数であり、
本監査のより広い行列によって「日付固有の偶然ではなく、アルゴリズム全体
を通じて概ね45〜55%程度で推移する構造的性質である」ことが裏付けられた。

---

## 7. Honmei Breakdown

| 本命星 | 利用可能率（108ケース中） |
|---|---|
| 1 | 47.2% (51/108) |
| 2 | 57.4% (62/108) |
| 3 | 36.1% (39/108) |
| 4 | **33.3% (36/108)** — 最低 |
| 5 | **87.0% (94/108)** — 最高 |
| 6 | 56.5% (61/108) |
| 7 | 56.5% (61/108) |
| 8 | 58.3% (63/108) |
| 9 | 49.1% (53/108) |

本命星による差が大きい（33.3%〜87.0%、約2.6倍の開き）。本命星5（五黄土星）
は五行相生ロジック上、除外条件との重なりが構造的に少ないため高い利用可能率
を示す一方、本命星4（四緑木星）は最も低い。これは占術的な優劣の主張では
なく、アルゴリズムの構造（§8/§16の除外ロジックと五行相生フィルタの相互
作用）から生じる純粋に計算上の結果である。

---

## 8. Month Breakdown

| 節気月バケット | 期間（近似） | 利用可能率（81ケース中） |
|---|---|---|
| 0 | 2/4〜3/5 | 61.7% |
| 1 | 3/6〜4/4 | 54.3% |
| 2 | 4/5〜5/5 | 56.8% |
| 3 | 5/6〜6/5 | 56.8% |
| 4 | 6/6〜7/6 | 53.1% |
| 5 | 7/7〜8/7 | 55.6% |
| 6 | 8/8〜9/7（**既知QAリクエストが属したバケット**） | 51.9% |
| 7 | 9/8〜10/7 | **43.2%** — 最低 |
| 8 | 10/8〜11/6 | 49.4% |
| 9 | 11/7〜12/6 | 54.3% |
| 10 | 12/7〜1/5 | 51.9% |
| 11 | 1/6〜2/3 | 53.1% |

月バケット間の差は本命星ほど大きくない（43.2%〜61.7%、約1.4倍）。既知QA
リクエストが属したバケット6は51.9%で、ほぼ中央値。特定の月が極端に悪い
わけではない。

---

## 9. Year Breakdown

| 年 | 利用可能率（108ケース中） |
|---|---|
| 2022 | 60.2% |
| 2023 | 48.1% |
| 2024 | 61.1% |
| 2025 | 49.1% |
| 2026（**既知QAリクエストが属した年**） | 50.9% |
| 2027 | 50.9% |
| 2028 | 50.0% |
| 2029 | 54.6% |
| 2030 | 56.5% |

年による変動は48.1%〜61.1%の範囲。2026年は50.9%で、9年間の中でもほぼ中央
値であり、外れ値ではない。

---

## 10. Result-count Distribution

| 結果に含まれる方位の数 | ケース数 | 割合 |
|---|---|---|
| 0（direction_filter_unavailable） | 452 | 46.5% |
| 1 | 347 | 35.7% |
| 2 | 122 | 12.6% |
| 3+ | 51 | 5.2% |

「利用可能」な場合でも、その大多数（520件中347件、66.7%）は**方位が
ちょうど1つだけ**返る。2つ以上返るのは全体の17.8%のみ。これはCompassの
「今月意識したい方向」という表現が、実際には多くの場合単一方位への収束
であることを示す（占術的評価ではなく、アルゴリズムの出力分布の記述）。

**Worst / Best segment（本命星×月バケットの組み合わせ、9年集計）**:

```
Worst 5（最も利用可能率が低い組み合わせ）:
  star=1 bucket=1（3/6-4/4）: 11.1%
  star=3 bucket=2（4/5-5/5）: 11.1%
  star=4 bucket=4（6/6-7/6）: 11.1%
  star=4 bucket=11（1/6-2/3）: 11.1%
  star=1 bucket=11（1/6-2/3）: 22.2%

Best 5（最も利用可能率が高い組み合わせ）:
  star=6 bucket=2（4/5-5/5）: 88.9%
  star=6 bucket=11（1/6-2/3）: 88.9%
  star=5 bucket=0（2/4-3/5）: 100.0%
  star=5 bucket=1（3/6-4/4）: 100.0%
  star=5 bucket=9（11/7-12/6）: 100.0%
```

特定の本命星×月の組み合わせでは、9年中ほぼ全て（または全て）が利用不可
（11.1%はn=9中1件のみ利用可能）というセグメントが存在する。逆に本命星5
の一部の月バケットは9年間常に利用可能（100%）だった。**この変動幅の大き
さ自体が、「ランダムな稀なエラー」ではなく「本命星と月の組み合わせに強く
依存する、予測可能な構造的パターン」であることを示している。**

---

## 11. Interpretation Boundary（再確認）

§6-10の数値が測定しているのは**アルゴリズム的な方向利用可能性
（ALGORITHMIC DIRECTION AVAILABILITY）のみ**である。以下は測定して
おらず、主張しない:

```
実ユーザーのコンバージョン率
ユーザー満足度
占術的な正確性
リテンション
Recommendation品質
文化的/宗教的な正しさ
```

§9の「2026年は50.9%」という数値も、実際に2026年にCompassを使った実
ユーザーの遭遇率ではなく、「2026年内の代表12時点×9本命星」という
決定的なアルゴリズム走査の結果である。

---

## 12. Current UX Assessment

**判定: MISLEADING**

理由:

1. 現在のコピー「**方向の参考情報を計算できませんでした**」は、動詞
   「計算できませんでした」により**技術的な計算失敗**を示唆する表現で
   ある。しかし実態（§6-10）は、多くの場合「計算は正常に完了し、結果が
   正当に空だった」というケースである。「できませんでした」という否定的
   な失敗表現は、正当な結果を技術的障害であるかのように誤って伝える。
2. 続く案内文「**生年月日または出発地点をご確認のうえ、もう一度お試し
   ください。**」は、原因をユーザーの**入力ミス**に明示的に帰属させて
   いる。しかし[compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)
   が確立した通り、この既知QAリクエストではbirthdate・originいずれも
   構造的に妥当だったと高確信度で判断されており、真因は年盤∩月盤の
   交差という第三の要因だった。ユーザーが言われた通り「生年月日・出発
   地点を確認」しても、それらに問題がない限り**再試行しても同じ月内
   では同じ結果になる**（本命星と対象月が変わらない限り、交差の結果は
   決定的に同一）。
3. 「もう一度お試しください」という再試行の呼びかけは、失敗が一時的・
   偶発的であることを暗示する。しかし§10で示した通り、特定の本命星×月
   の組み合わせでは9年間ほぼ一貫して利用不可（例: 本命星4×節気月4は
   9年中8年が利用不可）であり、**再試行しても状況は変わらない**（対象
   月・年が変わるまでは）。

これら3点はいずれも、実際の主要因（正当な計算結果としての空集合）とは
異なる印象（技術的失敗・入力ミス・一時的な問題）をユーザーに与える。
したがって**ALIGNED**でも**PARTIALLY ALIGNED**でもなく、**MISLEADING**
と判定する。

（本監査はこのコピーを編集しない。判定のみを行う。）

---

## 13. Product Promise Audit

**質問**: ユーザーが「今月の方向を確認する」ボタンを押すとき、現在のUIは
何を暗示しているか。

**判定: A（通常は方向が返ることを暗示している）**

根拠:

- ボタンラベル「**今月の方向を確認する**」——「確認する」は、確認対象
  （方向）が存在することを前提とした動詞である。「方向があるか確認する」
  ではない。
- 見出しコピー「**今月の流れと目的から、向かう方向と参拝候補を見つけ
  ます。**」——断定形の「見つけます」であり、条件節（「見つかる場合が
  あります」等）を伴わない。
- [compass-product-contract.md](../product/compass-product-contract.md)
  Section 2のProduct Promise「時間・方位runtime signalと目的から、今月
  意識したい方向と参拝候補を**示す**」も同様に断定形。

| 層 | 期待 |
|---|---|
| UI（ボタン・見出し） | A: 方向が通常返る |
| Product Contract（Section 2 Promise） | A: 方向が通常返る（断定形） |
| Runtime Contract（Section 8 Fail-safe） | 欠落・不正系のfail-safeは列挙するが、有効入力での空集合は列挙せず——暗黙にAを支持（rareケースとして扱っている） |
| 実際のアルゴリズム的利用可能性（§6） | B寄りの実態: 53.5%のみ利用可能、46.5%は空集合 |

**不整合の特定**: UI・Product Contract・Runtime Contractの3層はいずれも
（明示的または暗黙的に）Aを前提としているが、実際のアルゴリズム的利用
可能性はほぼ五分五分（B寄り）である。この不整合が、§12のMISLEADING判定
の根本にある構造的原因である。

---

## 14. Option A — Keep Current Behavior

```
annual ∩ monthly
if empty: return no direction (現行のdirection_filter_unavailable)
```

| 項目 | 内容 |
|---|---|
| Meaning | 年盤・月盤の両方が支持する方位のみを「参考方位」として認める、最も厳格な条件 |
| Benefits | 実装済み・追加コストゼロ。返す方位は年盤・月盤双方の支持を得た、最も確信度の高い信号のみ |
| Risks | §6-10の通り約46.5%のケースでユーザーが何も得られない。§12の通り現在のコピーは原因を誤って伝える（このコピー自体は本オプションに内在する問題ではなく、次善策として§17のOption Eで分離して扱う） |
| UX consequences | ユーザーの半数近くが「失敗」に見える体験をする。ボタンを押した結果が不確実 |
| Contract impact | なし（現状維持） |
| Engineering impact | なし |
| 測定された方向利用可能性 | 53.5%（§6） |

本オプションは引き続き有効な選択肢として維持する。

---

## 15. Option B — Monthly Fallback

```
annual ∩ monthly
if non-empty: use intersection
if empty: use monthly lucky directions (月盤単独)
```

**実装しない。概念評価のみ。**

- **意味論**: 年盤の支持は必須ではなくなり、月盤（今月固有の信号）を
  常に優先する。これは「今月」を前面に出すCompassのProduct Promise
  （Section 4「時間モデル: MONTH」）とは整合的である。
- **利用可能性への影響**: 月盤単独のlucky directionsが常に非空である
  という保証はコード上ない（`planned_visit_lucky_directions()`内部の
  `monthly_lucky`計算も同じ除外・五行相生ロジックを使うため、理論上は
  月盤単独でも空になり得る——本監査ではこの頻度を個別に測定していない、
  Open Questionとして§26に記録）。ただし年盤との交差を取らない分、
  Option Aより利用可能率は上がると推定される（未測定）。
- **Product Promise影響**: [compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md)
  Section 5は「年盤単独結果を出力として採用しない」という既存契約
  （`direction_reference.py:59`の`calculationMethod == "annual_monthly_kyusei_v1"`
  のみ受理する制約と整合させるため）を明記している。月盤単独へのフォール
  バックはこの精神と矛盾しないが（年盤単独ではなく、月盤単独へのフォール
  バック）、契約文書の明示的な更新が必要。
- **Runtime Contract影響**: `CompassDirectionRuntime.calculationMethod`
  の意味論を拡張する必要がある（現在は`"annual_monthly_kyusei_v1"`のみ）。
  フォールバック発生時に新しい`calculationMethod`値（例:
  `"monthly_only_fallback_v1"`）を導入するか、既存値のまま曖昧にするかの
  判断が必要。
- **UX複雑性**: 中程度。「年盤の支持なし」という情報をユーザーに見せる
  か隠すかの判断が追加で必要になる（§24）。
- **年盤情報の副次化**: はい——年盤は「交差が非空なら影響する」補助信号
  に格下がりし、月盤が事実上の主信号になる。
- **エンジニアリング複雑性**: 低〜中。`compass_runtime.py`内で
  `annual_lucky_directions()`と`planned_visit_lucky_directions()`の両方
  を呼び、交差が空なら月盤側の結果を使う分岐を追加する程度。`kyusei.py`
  自体を変更する必要はない（後述§19、Concierge分離の観点で重要）。

本オプションは「占術的に正しい」という主張を一切行わない。製品/Runtime
上の設計選択肢としてのみ評価する。

---

## 16. Option C — Annual Fallback

```
annual ∩ monthly
if non-empty: use intersection
if empty: use annual lucky directions (年盤単独)
```

**実装しない。概念評価のみ。**

Option Bと対称の評価:

- **意味論**: 月盤（今月固有）の支持は必須ではなくなり、年盤（その年
  全体の傾向）を常時のフォールバックとする。
- **利用可能性への影響**: 未測定（Option Bと同様、年盤単独の空集合頻度
  は本監査では個別測定していない）。
- **Product Promise影響**: **より深刻な矛盾がある**。
  [compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md)
  Section 5は「Compassは年盤単独結果を出力として採用しない」ことを、
  既存の`direction_reference.py`の`grounded inputsのみ`契約と明示的に
  整合させる形で**既に決定済み**である。Option Cはこの既存決定を直接
  覆すことになるため、他のオプションよりも契約変更の重みが大きい。
- **Runtime Contract影響**: Section 5の該当記述そのものの改訂が必要
  （単なる追記ではなく、既存の禁止事項の撤回）。
- **UX複雑性**: Option Bと同様。
- **年盤情報の副次化**: 逆——月盤が副次化され、年盤が主信号に近づく。
  これはCompassの「今月」という時間モデル（Section 4）との整合性が
  Option Bより弱い。
- **エンジニアリング複雑性**: Option Bと同程度（低〜中）。`kyusei.py`
  自体の変更は不要。

**Option BとCの比較上の注記**: Compassの時間モデルが明示的にMONTHである
こと（Section 4）を踏まえると、Option Cは「月」というCompassの中心的な
時間粒度を弱める方向の変更であり、Option Bより既存契約との緊張が大きい。

---

## 17. Option D — Score / Weight Model

```
概念的な例（実装しない、実際の重みを提案しない）:
  annual ∩ monthly の一致 = 最も強い信号
  monthly のみ = 中程度の信号
  annual のみ = より弱い信号
```

**実装しない。アーキテクチャ比較のみ。実際の重みは提案しない。**

**重要な区別（タスク指示§16に基づき明記）**: これは**方位（direction）
自体の信頼度スコアリング**の話であり、**Shrine Recommendation Ranking
（神社の推薦順位）とは完全に別の関心事**である。Compass Runtime Authority
が「どの方位を参考方位として提示するか、どの程度の確信度で」を決める
段階と、Recommendation Authorityが「絞り込まれた候補群の中でどの神社を
上位に出すか」を決める段階は、[compass-product-contract.md](../product/compass-product-contract.md)
Section 6のAuthority境界により明確に分離されている。Option Dはこの境界
の**方位側**のみに関する概念であり、Ranking側の重み・計算式には一切
言及しない。

- **意味論**: 「方位が存在するか/しないか」という二値から、「方位ごとの
  確信度」という連続的な表現へ移行する。
- **利用可能性への影響**: 交差が空でも月盤単独・年盤単独のいずれかが
  非空であれば「低確信度の方位」として提示可能になるため、Option A対比
  で利用可能性は理論上最も高くなる（Option B・Cの合成に近い）。
- **Product Promise影響**: 最も大きい。「今月意識したい方向」という
  単一の答えを示す現在のPromiseから、「複数の確信度レベルの候補方位」
  という異なる情報設計への転換になり得る。
- **Runtime Contract影響**: 最も大きい。`CompassDirectionRuntime`の
  Schema自体（現在は`referenceDirections: string[]`という単純なフラット
  配列）を、確信度付きの構造（例:
  `{direction: string, confidence: "high"|"medium"|"low"}[]`）へ変更する
  必要があり、[compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md)
  Section 5の出力Schemaの根本改訂を意味する。
- **UX複雑性**: 最も高い。確信度をユーザーにどう見せるか（見せないか）
  という新たなPresentation Authority上の判断が必要（`compass-product-contract.md`
  Section 8 Signal-to-Explanation Ruleとの整合確認も必要）。
- **エンジニアリング複雑性**: 最も高い。`compass_direction_filter.py`
  （現在は`reference_directions: Optional[Sequence[str]]`という単純な
  文字列集合を受理するのみ）も確信度を扱えるよう変更が必要になる可能性
  がある。

Option Dは4つの選択肢の中で最も大きな設計変更であり、契約・実装両面の
影響が最大である。

---

## 18. Option E — Legitimate No-Direction Result

```
「今月は年盤と月盤で重なる参考方位がありません」
（最終的な製品コピーではない、方向性の例示のみ）
```

**実装しない。最終的な占い文言は書かない。**

Option Aとの違いを明確にする:

| | Option A（現状） | Option E |
|---|---|---|
| 判定ロジック | annual∩monthly、空なら`None` | annual∩monthly、空なら`None`（**同一**） |
| Runtime Contract | 変更不要 | 変更不要（`CompassDirectionRuntime`のSchema自体は変わらない——`referenceDirections`が空、または`direction_context`全体がなくなる、のいずれかは実装判断だが、いずれもSchema拡張なしで表現可能） |
| Backend状態名 | `direction_filter_unavailable`（「利用不可」＝技術的響き） | `direction_filter_unavailable`という状態名自体は変えなくてよい——**意味の再定義**が本質。または新たな状態名（例: `direction_not_applicable_this_month`）を追加する選択肢もあるが、これはRuntime Contract変更を伴う |
| UI意味論 | エラー的な見た目・「もう一度お試しください」 | 「今月はこの結果でした」という中立的な製品結果として提示（§23 UX原則） |
| Recommendation表示 | 現状: Recommendation自体を一切表示しない（direction_contextがない場合、候補プールすら構築されない、§11 [#2496監査]参照） | **要検討**: 方位なしでも神社候補は表示するか（§23で原則のみ提示） |

**評価**: Option Eは、**同一の下層アルゴリズム（annual∩monthly、変更
なし）を保持したまま**、その結果の**製品的な意味づけ**だけを変更する
という点で、Option A/B/C/Dのいずれよりも既存Runtime Contractへの侵襲が
小さい。「新しい計算ロジックを導入する」のではなく、「既に起きている
正当な結果を、エラーではなく製品の一部として扱う」という再解釈である。

---

## 19. Comparison Matrix

Option記号は以下の本文セクションに対応する:
`A=§14（現状維持） / B=§15（月盤フォールバック） / C=§16（年盤フォールバック） / D=§17（スコア/重みモデル） / E=§18（第一級結果化）`。

| Option | 内容 | 方向利用可能性 | 意味論の明確さ | Promise整合 | Runtime Contract変更 | Frontend変更 | Backend変更 | Ranking影響 | Concierge risk | 実装複雑性 | 主なリスク |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A** | 現状維持（厳格な交差） | 53.5%（測定済み） | 低 | 弱い | 不要 | 不要 | 不要 | NONE | NO CONCIERGE IMPACT | なし | 約半数がエラーに見える体験 |
| **B** | 月盤フォールバック | 未測定（Aより高いと推定） | 中 | 改善（MONTH時間モデルと整合） | 必要（`calculationMethod`拡張） | 必要 | 必要（Compass層内で完結可能） | NONE | 設計次第でNO CONCIERGE IMPACT | 中 | 「年盤の支持なし」の伝え方 |
| **C** | 年盤フォールバック | 未測定 | 中 | **既存Section 5の年盤単独禁止と矛盾** | 必要（Section 5改訂） | 必要 | 必要 | NONE | 設計次第でNO CONCIERGE IMPACT | 中 | 既存の明示的決定を覆す説明責任 |
| **D** | スコア/重みモデル | 理論上最高 | 最高（確信度明示） | 最大の変更 | 最大（Schema根本改訂） | 最大 | 最大 | NONE（方位側のみ） | **SHARED FUNCTION RISKが最も高い** | 最大 | 過剰設計コスト |
| **E** | 第一級結果化（ロジック不変） | 53.5%（不変） | 高 | 改善（Promise表現調整と併用） | 軽微（任意） | 必要（コピー・状態のみ） | 不要 | NONE | **NO CONCIERGE IMPACT**（kyusei.py無変更） | 低 | 根本の低い利用可能性自体は解消しない |

**Ranking影響はいずれのOptionも一貫してNONE**（§22の境界の通り、Direction
availability policyはRecommendation Rankingより前段・別関心事であり、
いずれのOptionもRanking計算式・候補スコアリングには一切触れない）。

---

## 20. Runtime Contract Impact

| Option | Runtime Contract変更 | Product Contract変更 | Analytics contract変更 | Frontend state変更 | Backend runtime変更 | DB変更 | Migration |
|---|---|---|---|---|---|---|---|
| A（現状維持） | NO | NO | NO | NO | NO | NO | NO |
| B（月盤フォールバック） | YES（Section 5, `calculationMethod`語彙拡張） | POSSIBLE（Section 2 Promiseの表現調整を伴う場合） | POSSIBLE（`result_state`に新値を追加する場合のみ——既存`compass-posthog-query-contract.md`のresult_state語彙拡張が必要になる） | YES | YES（Compass層のみ、`kyusei.py`は無変更で実装可能） | NO | NO |
| C（年盤フォールバック） | YES（Section 5の年盤単独禁止の撤回、より重い契約変更） | POSSIBLE | POSSIBLE | YES | YES（同上） | NO | NO |
| D（スコアモデル） | YES（`CompassDirectionRuntime`のSchema根本改訂） | YES（Promise自体が「単一方位」から「確信度付き複数候補」へ） | POSSIBLE（新しいpropertyが必要になる可能性） | YES | YES | NO | NO |
| E（第一級結果化） | POSSIBLE（状態解釈の明文化のみ、Schema変更は任意） | YES（Promiseの表現をヘッジ形に調整することが望ましい、§23） | POSSIBLE（`result_state`の意味づけドキュメント更新、値自体の追加は不要） | YES（コピー・UI状態の意味づけ変更） | NO | NO | NO |

いずれのOptionも**DB変更・Migrationは不要**（既存のEphemeral Runtime
契約、[compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md)
Section 7「永続化しない」方針を維持できる）。

---

## 21. Concierge Isolation

**調査結果（実地確認、本監査で新たに確認）**:

```
$ grep -rln "from temples.domain.kyusei" backend --include="*.py" | grep -v test
backend/temples/api_views_concierge.py
backend/temples/services/compass_runtime.py
```

`api_views_concierge.py:30,563-565`:

```python
from temples.domain.kyusei import annual_lucky_directions, planned_visit_lucky_directions
...
calculated_direction = (
    planned_visit_lucky_directions(profile_birthdate or birthdate, visit_date)
    if visit_date
    else annual_lucky_directions(profile_birthdate or birthdate)
)
```

**確認された事実**: Concierge（`ConciergeChatView`、Compat Mode文脈）は、
リクエストに`visit_date`（または`planned_visit_date`）が含まれる場合、
**Compassと全く同じ関数`planned_visit_lucky_directions()`を直接呼び出す**。
これは前回監査（[#2496](https://github.com/etsu33/jinja_app/pull/2496)）
のOpen Question 2「kyusei.pyの関数がConcierge Compat Modeからも実際に
呼び出されているか」への回答であり、**YES、呼び出されている**ことを
本監査で確認した。

**ただし、Concierge側の扱いはCompassと異なる**: Concierge側の
`if calculated_direction:`という真偽判定は、`planned_visit_lucky_directions()`
が返す**dict自体**（`luckyDirections`キーの中身ではなく）の真偽を見て
おり、`luckyDirections`が空リスト`[]`であっても、dict自体は非空の辞書
（他のキーを持つ）なので`True`と評価される。したがってConcierge側では、
交差が空でも`direction_profile`は`raw_profile_context`に一旦セットされる。
最終的にユーザーへ見える形になるかどうかは、その後`direction_reference.py`
の`build_direction_reference()`が`reference_directions`（空なら）を理由に
`None`を返し、`attach_direction_references()`が該当神社から
`direction_reference`キーを削除する、という**別の、より下流の安全弁**に
委ねられている。結果として、Concierge側ではこの状態が**エラーとしてすら
表面化せず、単に方位情報が黙って表示されない**という、Compassとはさらに
異なる第三の挙動になっている。

**Isolation分類（各Optionについて）**:

| Option | 分類 |
|---|---|
| A（現状維持） | **NO CONCIERGE IMPACT** — 変更自体が発生しない |
| B（月盤フォールバック）— `compass_runtime.py`内でのみannual/monthly個別取得しfallback判断する設計 | **NO CONCIERGE IMPACT**（`kyusei.py`のシグネチャ・返り値契約は無変更） |
| B — 仮に`kyusei.py`の`planned_visit_lucky_directions()`自体の返り値契約を変更する設計を選んだ場合 | **SHARED FUNCTION RISK**（Concierge側の`if calculated_direction:`判定・`direction_reference.py`の下流処理に影響し得る） |
| C（年盤フォールバック）— 同上、実装場所次第で両方あり得る | 同上（設計次第でNO CONCIERGE IMPACTまたはSHARED FUNCTION RISK） |
| D（スコアモデル） | **SHARED FUNCTION RISKが最も高い** — `CompassDirectionRuntime`のSchemaを確信度付きへ拡張する場合、`kyusei.py`自体の出力形状を変える誘惑が最も強く、Concierge側の`calculated_direction`の消費コード（`direction_reference.py`含む）が前提とする現在のdict形状と非互換になるリスクが最大 |
| E（第一級結果化） | **NO CONCIERGE IMPACT** — `kyusei.py`・`planned_visit_lucky_directions()`自体は完全に無変更。Compass側の状態解釈・UIコピーのみを変更する |

**設計上の推奨（実装しない、方針のみ）**: 将来いずれかのOptionを実装する
場合、**Compass固有のポリシー（fallback判断・スコア付け）は
`compass_runtime.py`層に閉じ込め、`kyusei.py`の低レベル計算関数
（`annual_lucky_directions`・`planned_visit_lucky_directions`）自体の
シグネチャ・返り値契約は変更しない**ことを強く推奨する。これは
`compass-product-contract.md` Section 1が既に確立している
「Signal Reuse（計算モジュールの再利用）は許可、Authority Reuse（製品
責務の継承）は禁止」という原則の、Concierge分離への直接的な適用である。
この分離を維持する限り、B・Cは**NO CONCIERGE IMPACT**で実装可能である。

---

## 22. Ranking Boundary

```
Recommendation Ranking影響: NONE（全Option共通）
```

Direction availability policy（方位が利用可能かどうか、どの方位を提示
するか）は、`compass_recommendation_orchestrator.py`の中で
**candidate scoringより前段**に位置する（[compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)
§3で確認済み: `direction_context`が`None`の場合、`build_chat_candidates()`
自体が呼ばれない）。いずれのOptionも、`filter_candidates_by_direction()`
より後段の`build_chat_recommendations()`（候補スコアリング・Recommendation
Reason生成）には一切触れない。本監査はcandidate scoring・recommendation
weights・ranking order・recommendation reason logicのいずれも変更せず、
将来のいかなるOptionの実装においても、これらを変更しないことを明確な
境界として維持することを推奨する。

---

## 23. UX Principles（If No-Direction is Allowed — Option E関連）

原則のみ。最終コピー・実装は行わない。

1. **エラー的に見せない**: 赤色・警告アイコン・「エラー」「失敗」という
   語を避け、他の正当な結果状態（例: `recommendation_success`）と視覚的
   トーンを揃えることを検討する。
2. **再試行を過度に促さない**: 「もう一度お試しください」という表現は、
   §12で述べた通り「再試行すれば変わるかもしれない」という誤った期待を
   生む。同じ月・同じ本命星であれば結果は決定的に不変であるため、この
   表現の要否を再検討する余地がある。
3. **「重ならない」ことを正直に伝えるか**: 年盤と月盤という2つの信号が
   存在すること自体をユーザーに開示するかどうかは、Signal-to-Explanation
   Rule（`compass-product-contract.md` Section 8）の「実際に使用された
   信号を理解可能な言葉へ翻訳する」原則との整合を個別に検討する必要が
   ある。九星気学・月盤という語はSection 8の分類表で「Optional」
   「Secondary」とされており、Primary見出しには使わない方針と整合させる
   必要がある。
4. **別の月・別の入力を提案するか**: 「来月は確認できる可能性がある」
   といった示唆は、断定的な未来予測を避けるという既存の非断定原則
   （`docs/core/meaning-layer.md`、`compass-product-contract.md` Section 9）
   と矛盾しない範囲でのみ検討する。
5. **方位なしでも神社候補を見せるか**: 現状（Option A/E共通の下層ロジック
   では）`direction_context`が`None`の場合、候補プール自体が構築されない
   （[#2496](compass-direction-filter-unavailable-root-cause.md) §11）。
   これを維持するか、方位なしでも別の基準（purposeのみ）で候補を見せる
   ように変更するかは、Compass Runtime Authorityの境界
   （`compass-product-contract.md` Section 6「候補集合の絞り込みにのみ
   関与」）に照らして慎重な検討が必要——後者へ変更する場合、事実上
   Compassの候補フィルタ設計そのものの見直しになり、Option Eの範囲を
   超える可能性がある。

---

## 24. UX Principles（If Fallback is Required — Option B/C関連）

原則のみ。最終コピー・実装は行わない。

1. **フォールバック発動条件**: 年盤∩月盤が空集合になった場合にのみ発動
   し、非空の場合は既存の交差ロジックをそのまま使う（既存の「grounded
   inputsのみ」原則を維持し、フォールバックを既定動作にしない）。
2. **ユーザーへの開示要否**: フォールバックが発動したこと自体をユーザー
   に伝えるべきか——伝えない場合、ユーザーは常に同じ強さの方位情報を
   受け取っていると誤解する可能性があり、Signal-to-Explanation Rule
   （実際に使用された信号を偽らない）との緊張が生じ得る。伝える場合、
   「年盤の支持なし」という情報がSection 8の用語分類表のどこに位置
   づけられるかを個別に検討する必要がある。
3. **年盤/月盤の強さの露出**: 内部的な確信度スコア（Option Dで想定する
   ような）をフォールバック時にだけユーザーへ見せるという中間的な設計
   もあり得るが、これはOption B/CとDの境界を曖昧にするため、明確に
   区別して検討すべきである。
4. **結果の確信度差**: フォールバック結果（月盤単独または年盤単独）は、
   交差結果よりも「弱い」信号であることをUI上区別するかどうか——区別
   しない場合、すべての方位提示が同じ強さに見えてしまい、実際には
   異なる確信度の情報を均質に見せることになる。

---

## 25. Decision Criteria（適用結果）

タスク指示の優先順位（1. Product Promise一貫性 → 8. 実装複雑性）に沿って
評価すると:

1. **Product Promise一貫性**: Option Eが最も一貫性を回復しやすい
   （ロジックは変えず、意味づけとPromiseの表現を揃えるだけで済む）。
   Option B/Cは一貫性を「改善」できるが、Promise自体の再定義を伴う。
   Option Dは最大の一貫性改善余地があるが、Promise自体の再設計が必要。
   Option Aは不整合を放置する。
2. **意味論の整合性**: Option D＞Option E＞Option B/C＞Option A。
3. **予測可能なUX**: Option Eは「同じ入力なら同じ結果」という既存の
   決定的性質をそのまま維持しつつ、体験としての予測可能性（エラーで
   はなく既知の製品状態）を改善する。Option B/Cは新たな分岐を追加する
   ため予測可能性はやや複雑化する。
4. **Runtime Contractの明確さ**: Option A・Eが最も明確（変更最小）。
   Option Dが最も不明確（Schema根本改訂の途中で一時的な複雑さが生じる）。
5. **Concierge分離**: Option A・E＞Option B/C（設計次第）＞Option D
   （§21）。
6. **テスト容易性**: Option Eは既存の`direction_filter_unavailable`分岐
   のテスト（[#2496](compass-direction-filter-unavailable-root-cause.md)
   §13で確認済み、既に十分カバーされている）をほぼそのまま再利用でき、
   新たな分岐条件を追加しない分、テスト容易性が最も高い。
7. **保守性**: Option Eが最も低リスク（下層アルゴリズム不変）。
8. **実装複雑性**: Option E＜Option B≈Option C＜Option D。

---

## 26. Proposed Recommendation

**Status: PROPOSED — MOTHER SHIP DECISION REQUIRED**

### RECOMMENDED OPTION: **E — 「重なる方位なし」を第一級のCompass結果としてモデル化する**

理由:

- 下層アルゴリズム（年盤∩月盤の交差）自体は変更しない——§6-10で実証した
  46.5%という高頻度は、算術的な正当性を持つ結果であり、「バグを直す」
  対象ではなく「製品としてどう扱うか」の対象である。
- §12で確認したMISLEADING判定の根本原因（エラー的な見た目・入力ミスへの
  誤帰属・無意味な再試行の示唆）を、下層ロジックに触れずに解消できる。
- §21の通り、`kyusei.py`自体を変更しない限りConcierge Compat Modeへの
  影響はゼロ（NO CONCIERGE IMPACT）に保てる。
- §25の評価基準のほぼ全てにおいて、Option Aの不整合を解消しつつ、最も
  低リスク・低複雑性で実現できる。

**ただし、Option Eの採用は§13で確認した「A: 方向が通常返る」という
現在のPromiseの表現（ボタンラベル・見出しコピー）を、ヘッジを含む表現へ
調整することとセットで検討することを推奨する。** コピー・状態の意味づけ
だけを変えて、Promise自体の断定的な表現をそのまま残すと、根本の不整合
（§13）は解消されない。

### ALTERNATIVE OPTION: **B — 月盤フォールバック**

`compass_runtime.py`層のみで実装し、`kyusei.py`のシグネチャを変更しない
設計を条件とするなら、Concierge分離を保ったまま利用可能性そのものを
（未測定だが恐らく）改善できる。ただし[compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md)
Section 5・`calculationMethod`語彙の契約改訂と、月盤単独フォールバックが
発動した場合のUX（§24）を個別に設計する追加コストを伴う。Option Eより
実装・契約変更コストが大きいが、根本の利用可能性自体を引き上げたい場合
の選択肢として記録する。

いずれも**最終判断はMother Shipに委ねる**。本監査はこの2案を推奨する
証拠を提示するのみであり、実装を承認するものではない。

---

## 27. Alternative（再掲）

上記§26参照。**B — 月盤フォールバック**を代替案として明記する。

---

## Mother Ship Decision Gate

```
A — KEEP CURRENT STRICT INTERSECTION
B — MODEL NO-DIRECTION AS FIRST-CLASS RESULT       ← 本監査の推奨
C — FALLBACK POLICY RECOMMENDED（月盤フォールバック、代替案）
D — SCORE MODEL RECOMMENDED
E — INSUFFICIENT EVIDENCE FOR PRODUCT DECISION
```

**本監査のゲート判定: B — MODEL NO-DIRECTION AS FIRST-CLASS RESULT**
（Alternative: C相当＝月盤フォールバック）

これは監査としての推奨であり、Mother Shipが最終決定する。

---

## Future PR Plan（実装しない、将来のための最小構成案）

**Option E（推奨）を将来実装する場合の最小PR構成案**（このPRでは一切
着手しない）:

```
PR-1: Product/Runtime Contract更新のみ（docs-only）
  - compass-product-contract.md Section 2 Promiseの表現をヘッジ形へ
    調整する契約変更
  - compass-mvp-runtime-contract.md Section 8 Fail-safe Contractに
    「有効な入力での交差空集合」を明示的な行として追加
  - direction_filter_unavailableという状態名の意味づけを
    「技術的失敗」ではなく「正当な結果」として明文化
  - コード変更なし

PR-2: Frontend UI状態・コピー変更のみ
  - direction_filter_unavailable時の表示を、エラー的トーンから
    §23のUX原則に沿った中立的な製品結果表示へ変更
  - 「もう一度お試しください」という再試行の示唆を、§23の原則に基づき
    見直す
  - backend/kyusei.py・orchestrator・analytics instrumentationは無変更

PR-3: Analytics検証（変更が必要な場合のみ）
  - result_state自体の値は変更しない場合、Analyticsコード変更は不要
  - PostHog Query Contract側のドキュメント更新のみ（`direction_filter_unavailable`
    の解釈記述を、PR-1のContract変更に合わせて更新）が必要な場合のみ
    追加PRを検討
```

**Option B（代替案）を将来実装する場合の追加PR**（Option Eの上に積む
想定、こちらも一切着手しない）:

```
PR-4: compass_runtime.py内でのannual/monthly個別取得とfallback判断
  - kyusei.pyのシグネチャ変更なし（Concierge分離維持、§21）
  - calculationMethod語彙拡張（Runtime Contract改訂を伴う、PR-1相当の
    追加契約変更が必要）
  - 月盤単独フォールバック発動時のUX（§24の原則に基づく）
```

この分割は本監査の所見から導出した一案であり、確定的な実装計画ではない。
Mother Shipの決定内容によって構成は変わり得る。

---

## Non-goals

本監査では以下を一切行っていない:

- Production code（frontend/backend）の変更
- Recommendation Rankingの変更
- Analytics instrumentationの変更
- DB modelsやmigrationの追加
- Premiumの変更
- Personal Continuityの実装
- Conciergeの変更
- 最終的な製品コピー・UI実装
- kyusei.pyまたはその他既存関数の変更
- Mother Shipに代わる最終決定

---

## Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(出力なし = whitespaceエラーなし)
```

**pytest実行の試行**: [compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)
§22で報告した通り、本セッションのサンドボックス環境にはdocker-compose
Postgres（host=`db`）が起動しておらず、pytest-django harnessによる
`temples/tests/services/test_kyusei_direction.py`等の実行は
`OperationalError: failed to resolve host 'db'`で失敗する状態のまま
変わっていない（本監査でもDocker daemonを起動していない、インフラ変更は
監査範囲外と判断）。

**代替として実施した検証**: 本監査の全定量分析（§5-10）は、無改変の
production `backend/temples/domain/kyusei.py`の`honmei_star()`・
`planned_visit_lucky_directions()`関数を、pytest harnessを介さず直接
呼び出す形で実行した（`django.conf.settings.configure(USE_TZ=True,
TIME_ZONE="Asia/Tokyo")`の最小構成、DBアクセスなし）。分析スクリプトは
セッションのスクラッチパッドディレクトリ（`/private/tmp/...`）に置き、
**リポジトリには一切コミットしていない**（タスク指示§30・§32の要件通り）。

**実行した分析コマンドの要約**（再現可能、PII非公開）:

```
9本命星（合成birthdate、1975-1999年から機械的選定）
× 12節気月バケット（kyusei._solar_month_index()の実際の境界定義から導出、
  代表中間日付を使用）
× 9年（2022-2030、年盤の9周期を一巡）
= 972ケース

各ケースで honmei_star() と planned_visit_lucky_directions() を
無改変のまま直接呼び出し、luckyDirectionsが空リストになる頻度を集計。
```

---

## Diff Scope Gate（確認）

```
$ git status --short
?? docs/audit/compass-direction-availability-product-decision.md

$ git diff --stat
(コミット前、untracked 1件のみ)
```

分析に使用した一時スクリプト（`compass_availability_matrix.py`）および
生データ（`compass_availability_raw.json`）は、セッションのスクラッチ
パッドディレクトリ（`/private/tmp/...`）にのみ存在し、リポジトリ外である
ため`git status`には一切現れない。本ドキュメント1件のみがコミット対象
である。
