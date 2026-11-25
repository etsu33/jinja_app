# Japanese Address Structured Normalization Contract v1

## 1. Purpose

Stage 2 structured normalization の目的は、日本住所の表記差を安全に比較可能な構造へ変換することである。

Stage 2 は以下を行わない。

```text
- raw address の書き換え
- DB / Seed の更新
- same shrine の確定
- fuzzy identity match
- 欠落住所の推測補完
- 座標による自動identity救済
```

責務は以下の3層へ分離する。

```text
Stage 1
Lexical Normalization
文字表記のみを正規化

Stage 2
Structured Normalization
住所構造を解析・比較可能化

Identity Layer
同一神社かどうかを判定
```

---

# 2. Structured Output Schema

Stage 2 は単一文字列ではなく、次の構造を返す。

```text
AddressNormalizationResult

raw_address
lexical_address

prefecture
municipality
locality
oaza
aza
koaza

block
lot
sub_lot

address_core

building_component
floor_component
unit_component

structured_address

normalization_status
normalization_rules_applied[]
review_reasons[]
```

## 2.1 raw_address

入力された原文をそのまま保持する。

```text
日本、〒135-0047 東京都江東区富岡１丁目２０番３号
```

変更禁止。

---

## 2.2 lexical_address

Stage 1適用後。

例:

```text
東京都江東区富岡1丁目20番3号
```

Stage 1で許可される処理:

```text
NFKC
郵便番号prefix除去
日本、prefix除去
dash異体字統一
前後空白除去
連続空白整理
```

### 2.2.1 dash異体字の範囲

`dash異体字統一` の対象は **実際のdash / minus異体字のみ**とする。

```text
－  U+FF0D
‐  U+2010
‑  U+2011
‒  U+2012
–  U+2013
—  U+2014
―  U+2015
−  U+2212
```

`ー`（U+30FC KATAKANA-HIRAGANA PROLONGED SOUND MARK）は
**dash異体字に含めない**。

理由:

```text
ー は日本語テキストの正規の構成文字であり、建物名に通常出現する
```

一律にASCII `-` へ寄せると次のように `building_component` を破壊し、
将来のIdentity evidenceを信頼できなくする。

```text
パークタワー
→ パークタワ-   ← 禁止
```

Stage 2 canonical実装は `ー` を変換せずそのまま保持する。

`scripts/audit_shrine_positions_v2.py` の既存Stage 1は `ー` を変換する
legacy behaviorを持つが、本ContractのStage 2はそれを引き継がない。
両者の差分は **意図的**である。

---

## 2.3 行政・町字component

```text
prefecture
municipality
locality
oaza
aza
koaza
```

例:

```text
prefecture   = 東京都
municipality = 江東区
locality     = 富岡
oaza         = null
aza          = null
koaza        = null
```

`大字 / 字 / 小字` は削除せずcomponentとして保持する。

---

## 2.4 番地component

```text
block
lot
sub_lot
```

例:

```text
1丁目20番3号
```

を安全に解析できた場合:

```text
block   = 1
lot     = 20
sub_lot = 3
```

### 2.4.1 marker無しhyphen表記のslot

marker（`丁目` / `番` / `番地` / `号`）を持たないhyphen表記は、
位置でslotへ割り当てる。

```text
3 numeric segments → block / lot / sub_lot
2 numeric segments → block / lot
1 numeric segment  → lot
```

**この割当は決定的比較のためのpositional comparison slotであり、
行政上の `丁目 / 番 / 号` の意味を立証したものではない。**

例:

```text
2-16-2
```

は比較のため次のようにserializeしてよい。

```text
block   = 2
lot     = 16
sub_lot = 2
```

しかしこれは次を独立に確立した事実として **含意しない**。

```text
2丁目16番2号
```

意味が確定するのはmarker付きtokenを実際に消費したときだけであり、
その区別は `normalization_rules_applied` に現れる。

```text
marker無し  2-16-2        → normalization_rules_applied = []
marker付き  2丁目16番2号   → ["CHOME_TO_BLOCK", "BAN_TO_LOT", "GO_TO_SUB_LOT"]
```

下流のIdentity Layerは、行政区画の意味を必要とする判断に
marker無し由来のslot値を根拠として使ってはならない。

---

## 2.5 address_core

Shrine identity比較に利用可能な、建物情報を除いた住所本体。

```text
東京都江東区富岡1-20-3
```

ただしこれは保存値ではない。

comparison-only derived value とする。

---

## 2.6 建物component

```text
building_component
floor_component
unit_component
```

例:

```text
東京都千代田区外神田2-16-2 神田明神文化交流館3階
```

の場合:

```text
building_component = 神田明神文化交流館
floor_component    = 3階
unit_component     = null
```

---

# 3. normalization_status

許可値を次の4種類とする。

```text
NORMALIZED
NO_CHANGE
AMBIGUOUS
UNSUPPORTED
```

## NORMALIZED

構造解析に成功し、安全な比較用表現が生成された。

## NO_CHANGE

Stage 2変換を必要とせず、入力がすでに比較可能。

## AMBIGUOUS

複数の住所構造解釈が成立する。

推測して確定しない。

## UNSUPPORTED

現行Contractで安全に解析できない住所形式。

---

# 4. normalization_rules_applied

Stage 2で実際に適用したルールを列挙する。

例:

```text
[
  "CHOME_TO_BLOCK",
  "BAN_TO_LOT",
  "GO_TO_SUB_LOT"
]
```

候補:

```text
CHOME_TO_BLOCK
BAN_TO_LOT
BANCHI_TO_LOT
GO_TO_SUB_LOT
STRUCTURED_NUMERIC_KANJI
BUILDING_COMPONENT_SPLIT
FLOOR_COMPONENT_SPLIT
UNIT_COMPONENT_SPLIT
```

適用していないルールを記録してはならない。

---

# 5. review_reasons

AMBIGUOUS / UNSUPPORTED の理由を構造化する。

候補:

```text
OAZA_STRUCTURE_AMBIGUOUS
AZA_STRUCTURE_AMBIGUOUS
KOAZA_STRUCTURE_AMBIGUOUS
SPECIAL_ADDRESS_NOTATION
BUILDING_BOUNDARY_AMBIGUOUS
UNBANCHED_ADDRESS
UNSUPPORTED_LOT_STRUCTURE
UNKNOWN_ADDRESS_PATTERN
```

free textだけで判定させない。

---

# 6. Safe Transformation Rules

安全に構造解析できた場合のみ以下を許可する。

```text
1丁目20番3号
→ block=1, lot=20, sub_lot=3

1丁目20番地3
→ block=1, lot=20, sub_lot=3

1丁目20番3
→ block=1, lot=20, sub_lot=3
```

漢数字は住所数値tokenとして認識された場合のみ変換する。

```text
二丁目
→ block=2
```

以下は禁止する。

```text
二本松 → 2本松
三島 → 3島
八幡 → 8幡
```

---

# 7. 大字 / 字 / 小字

以下はidentity構成要素として保持する。

```text
大字
字
小字
```

自動削除禁止。

例:

```text
大字石神976
```

と

```text
石神976
```

はStage 2単独では同一住所と確定しない。

結果:

```text
AMBIGUOUS
```

またはIdentity Layerで追加evidenceを要求する。

---

# 8. 建物名・階・部屋番号

建物関連情報はaddress_coreから分離する。

通常のShrine identity primary keyには使用しない。

ただし差分は捨てない。

```text
CORE_ADDRESS_MATCH
BUILDING_COMPONENT_DIFFERS
```

のようなIdentity evidenceとして利用可能。

建物内神社・企業内神社等ではHuman Review対象とする。

---

# 9. Identity Layer Connection Contract

Stage 2の結果はEntity判定ではなくEvidenceとして扱う。

## 9.1 address identity status

Identity Layerへ渡す住所比較結果は次の候補とする。

```text
ADDRESS_EXACT_MATCH
ADDRESS_NORMALIZED_MATCH
ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF
ADDRESS_DIFFERENT
ADDRESS_AMBIGUOUS
ADDRESS_UNSUPPORTED
```

---

## 9.2 ADDRESS_EXACT_MATCH

rawまたは既存canonical identityが完全一致。

最も強い住所evidence。

ただし住所単独でSAME entityを確定しない。

---

## 9.3 ADDRESS_NORMALIZED_MATCH

Stage 2 structured normalization後にaddress_coreが一致。

例:

```text
東京都江東区富岡1丁目20番3号
東京都江東区富岡1-20-3
```

→

```text
ADDRESS_NORMALIZED_MATCH
```

---

## 9.4 ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF

address_core一致だがbuilding/floor/unitが異なる。

例:

```text
東京都中央区銀座1-2-3 Aビル1F
東京都中央区銀座1-2-3 Bビル2F
```

これをSAMEにはしない。

Human Reviewまたは追加Identity Evidenceへ送る。

---

# 10. Identity判定ルール

Stage 2だけで以下を返してはならない。

```text
SAME
DIFFERENT
NON_SHRINE
```

Identity Layerが組み合わせるもの:

```text
name identity
address identity
official source
Place ID
coordinate evidence
existing resolution evidence
```

---

# 11. Automatic SAME禁止

以下は禁止する。

```text
ADDRESS_NORMALIZED_MATCH
→ SAME
```

正しい流れ:

```text
ADDRESS_NORMALIZED_MATCH
+
name identity
+
trusted source corroboration
+
必要に応じて Place ID / coordinate
↓
Identity Layer
↓
SAME / DIFFERENT / AMBIGUOUS
```

---

# 12. Production Join Connection

Stage 2導入後も既存:

```text
JOIN_MATCH_EXACT
```

を変更しない。

新しい判定は別statusとする。

候補:

```text
JOIN_MATCH_EXACT
JOIN_MATCH_NORMALIZED
JOIN_CORROBORATED
JOIN_IDENTITY_REVIEW_REQUIRED
JOIN_MISSING_PRODUCTION
```

`JOIN_MATCH_NORMALIZED` は:

```text
name identity sufficient
AND
ADDRESS_NORMALIZED_MATCH
```

だけでは最終Production identity確定にしない。

追加corroborationが不足する場合:

```text
JOIN_IDENTITY_REVIEW_REQUIRED
```

へ送る。

---

# 13. Production Absence Contract

次は禁止する。

```text
JOIN_MISSING_PRODUCTION
→ Production不存在
```

Stage 2後でも、Production不存在を確定するには:

```text
Production snapshot available
AND
exact identity absent
AND
normalized identity absent
AND
corroborated identity candidate absent
AND
identity ambiguity absent
```

を満たす必要がある。

それでも「検索Contract上で不存在」であり、外部世界の不存在を意味しない。

---

# 14. ARTIFACT_PRODUCTION_DRIFT

`ARTIFACT_PRODUCTION_DRIFT` は次の場合のみ将来発火可能とする。

```text
Production snapshot available
AND
target canonical shrine identity established
AND
Production上の該当identity absence established
AND
identity ambiguity = none
```

Stage 1 exact join失敗だけでは発火しない。

---

# 15. Golden Cases

## GC-A01: exact address

Input A:

```text
東京都千代田区外神田2-16-2
```

Input B:

```text
東京都千代田区外神田2-16-2
```

Expected:

```text
ADDRESS_EXACT_MATCH
```

---

## GC-A02: full-width + postal prefix

A:

```text
日本、〒101-0021 東京都千代田区外神田２－１６－２
```

B:

```text
東京都千代田区外神田2-16-2
```

Expected:

```text
Stage 1 match
ADDRESS_NORMALIZED_MATCH
```

---

## GC-A03: 丁目 / 番 / 号

A:

```text
東京都江東区富岡1丁目20番3号
```

B:

```text
東京都江東区富岡1-20-3
```

Expected:

```text
NORMALIZED
ADDRESS_NORMALIZED_MATCH
```

---

## GC-A04: numeric Kanji in structured token

A:

```text
東京都某区某町二丁目3番4号
```

B:

```text
東京都某区某町2-3-4
```

Expected:

```text
NORMALIZED
ADDRESS_NORMALIZED_MATCH
```

---

## GC-A05: Kanji in locality name

A:

```text
福島県二本松市○○1-2
```

Expected:

```text
二本松 remains unchanged
```

No conversion to:

```text
2本松
```

---

## GC-A06: 大字

A:

```text
埼玉県某市大字石神976
```

B:

```text
埼玉県某市石神976
```

Expected:

```text
not automatic ADDRESS_NORMALIZED_MATCH
ADDRESS_AMBIGUOUS
```

---

## GC-A07: 字

A:

```text
青森県某市大字藤崎字西村井8-2
```

B:

```text
青森県某市藤崎西村井8-2
```

Expected:

```text
ADDRESS_AMBIGUOUS
```

`字` must not be silently removed.

---

## GC-A08: 小字

A:

```text
宮城県某市○○小字△△12
```

B:

```text
宮城県某市○○△△12
```

Expected:

```text
ADDRESS_AMBIGUOUS
```

---

## GC-A09: building component

A:

```text
東京都千代田区外神田2-16-2
```

B:

```text
東京都千代田区外神田2-16-2 神田明神文化交流館3階
```

Expected:

```text
address_core equal
building_component present
ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF
```

---

## GC-A10: different buildings on same lot

A:

```text
東京都中央区銀座1-2-3 Aビル1F
```

B:

```text
東京都中央区銀座1-2-3 Bビル2F
```

Expected:

```text
ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF
not SAME
```

---

## GC-A11: unsupported special address

A:

```text
○○県○○市○○町無番地
```

Expected:

```text
UNSUPPORTED
ADDRESS_UNSUPPORTED
```

No guessed numeric structure.

---

## GC-A12: Tomioka Hachimangu precedent

A:

```text
東京都江東区富岡 1丁目20番3号
```

B:

```text
日本、〒135-0047 東京都江東区富岡１丁目２０−３
```

C:

```text
東京都江東区富岡1-20-3
```

Expected:

```text
all address_core
= 東京都江東区富岡1-20-3

ADDRESS_NORMALIZED_MATCH
```

But:

```text
ADDRESS_NORMALIZED_MATCH alone
MUST NOT produce SAME entity
```

---

# 16. Non-Goals

This Contract does not:

```text
modify Shrine.address
modify Seed address
modify Production
change existing JOIN_MATCH_EXACT semantics
change Recommendation
change Compass
change Ranking
perform network lookups
perform coordinate adoption
```

Implementation must remain fail-safe.

When uncertain:

```text
AMBIGUOUS
or
UNSUPPORTED
```

not inferred normalization.
