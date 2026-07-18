

# Score v3 consultation_axis × history_theme Mapping Design

## 1. Purpose

Score v3 の `history_signal` を、相談軸ごとに安全に拡張するための設計メモ。

現行実装では、`consultation_axis` と `history_theme` の対応は `rest_healing` 中心に限定されている。
本ドキュメントでは、既存の `consultation-theme-taxonomy` と `history-theme-taxonomy` をもとに、Score v3 に投入可能な mapping 候補を整理する。

このPRでは実装変更を行わない。

---

## 2. References

### consultation_axis 正本

- `docs/product/consultation-theme-taxonomy.md`
- `backend/temples/domain/consultation_axis.py`

### history_theme 正本

- `docs/product/history-theme-taxonomy.md`

### current Score v3 implementation

- `backend/temples/services/concierge_chat_ranking.py`

---

## 3. Current State

現行の Score v3 では、以下の mapping が実装されている。

```python
SCORE_V3_HISTORY_THEME_BY_AXIS = {
    "rest_healing": {
        "静寂": 1.0,
        "復興": 0.8,
        "守り": 0.6,
        "縁": 0.2,
        "勝負": 0.0,
    },
}
```

同じ構造が `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` にも存在する。

現状の特徴:

- `rest_healing` のみ明示対応している。
- `career_change` / `relationship_repair` / `money_growth` / `study_success` などは未対応。
- 未対応axisでは `history_signal=0.0` になる。
- Score v3 は shadow mode がデフォルトのため、現時点ではランキング本体を壊さない。

---

## 4. Design Principles

### 4.1 history_theme は神社側文脈として扱う

`history_theme` はユーザー状態を断定するものではなく、神社側の意味文脈である。

例:

```text
相談: 疲れを整えたい
consultation_axis: nature_reset / rest_healing
history_theme: 静寂 / 復興 / 守り
```

この場合も、「ユーザーは静寂タイプである」とは扱わない。
あくまで、候補神社の文脈が相談意図と合いやすいかを見る。

### 4.2 primary / secondary / weak の3段階で扱う

Score v3 へ投入する際は、history_theme を以下の3段階で扱う。

| level | score | meaning |
| --- | ---: | --- |
| primary | 1.0 | 相談軸と最も自然に接続する文脈 |
| secondary | 0.6 - 0.8 | 補助的に合う文脈 |
| weak | 0.2 - 0.4 | 場合によって合うが主軸ではない文脈 |
| mismatch | 0.0 | 原則として加点しない文脈 |

### 4.3 need / goriyaku / visit_style を上書きしない

この mapping は Score v3 の `history_signal` のみを補助する。

以下は別レイヤーで扱う。

- `need_tags`
- `goriyaku_tag_ids`
- `visit_style_tags`
- `reason_facts`
- `action_suggestion_v4`

### 4.4 実装前に docs で固定する

本PRでは mapping 候補を設計するだけで、`concierge_chat_ranking.py` は変更しない。

---

## 5. Taxonomy Summary

### consultation_axis candidates

`docs/product/consultation-theme-taxonomy.md` で整理されている主な候補。

| theme_key | primary consultation_axis | fallback |
| --- | --- | --- |
| work | career_change | career |
| relationship | relationship_repair | relationship |
| money | money_growth | money |
| challenge | restart_mindset | career_change / other |
| rest | nature_reset | other |
| health | health | other |
| study | study_success | study |
| future | restart_mindset | career_change / other |

### history_theme candidates

`docs/product/history-theme-taxonomy.md` の正本。

| history_theme | meaning |
| --- | --- |
| 守り | 不安やリスクから距離を取り、生活や心の土台を整える |
| 静寂 | 立ち止まり、自分の内側を見つめ直す |
| 再出発 | 区切りをつけ、新しい方向へ進む |
| 復興 | 失ったエネルギーや自信を取り戻す |
| 勝負 | 決断し、挑戦し、前へ進む |
| 学び | 知識や経験を積み上げ、成長する |
| 縁 | 人・機会・場所とのつながりを見直し、育てる |

---

## 6. Proposed Mapping

### 6.1 career_change

仕事、転職、独立、働き方、次のキャリア判断に関する相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 勝負 | 1.0 | 決断・挑戦・前進と最も接続しやすい |
| 再出発 | 0.8 | 転職・独立・働き方の切り替えと相性がよい |
| 学び | 0.6 | スキル習得・積み上げ型のキャリア相談に合う |
| 守り | 0.3 | 仕事不安・生活基盤の安定には補助的に合う |
| 静寂 | 0.2 | 一度立ち止まって整理する相談では弱く合う |
| 縁 | 0.2 | 仕事上の人脈・機会には一部接続する |
| 復興 | 0.2 | 自信回復型の仕事相談には一部接続する |

### 6.2 relationship_repair

恋愛、家族、職場、友人など、人との関係を整える相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 縁 | 1.0 | 人・機会・関係性の再構築と最も接続する |
| 静寂 | 0.7 | 感情を落ち着け、関係を見直す相談に合う |
| 守り | 0.5 | 境界線・安心感・生活基盤の保護に合う |
| 再出発 | 0.4 | 関係の区切りや再構築に合う |
| 復興 | 0.4 | 傷ついた関係・自己回復に合う |
| 学び | 0.2 | 関係から学ぶ文脈には弱く合う |
| 勝負 | 0.1 | 対人関係では強すぎるため原則弱い |

### 6.3 money_growth

収入、売上、金運、経済活動、生活基盤に関する相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 守り | 1.0 | お金の不安・生活基盤の安定と最も接続する |
| 勝負 | 0.8 | 商売・売上・事業の前進と相性がよい |
| 再出発 | 0.6 | 収入構造の見直しや再設計に合う |
| 学び | 0.4 | 金融学習・事業学習には補助的に合う |
| 縁 | 0.3 | 商売上の縁・機会には一部接続する |
| 静寂 | 0.2 | 不安を落ち着ける文脈では弱く合う |
| 復興 | 0.2 | 経済的立て直しには一部接続する |

### 6.4 restart_mindset

一歩踏み出したい、やり直したい、将来を考えたい相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 再出発 | 1.0 | 区切り・切り替え・新しい方向性と最も接続する |
| 勝負 | 0.8 | 決断・挑戦・行動開始に合う |
| 静寂 | 0.6 | 方向性を見直す相談に合う |
| 学び | 0.5 | 次の成長テーマを探す相談に合う |
| 復興 | 0.5 | 自信や気力を取り戻して進む相談に合う |
| 守り | 0.3 | 不安を整えた上で進む相談には補助的に合う |
| 縁 | 0.2 | 新しい出会い・機会には一部接続する |

### 6.5 nature_reset / rest_healing

疲れ、休息、静けさ、回復、気持ちを落ち着けたい相談。

現行 `rest_healing` mapping を基準とする。

| history_theme | score | reason |
| --- | ---: | --- |
| 静寂 | 1.0 | 立ち止まり、内側を整える文脈と最も接続する |
| 復興 | 0.8 | エネルギーや自信の回復に合う |
| 守り | 0.6 | 心身や生活基盤を守る文脈に合う |
| 縁 | 0.2 | 人とのつながりが回復要因になる場合に弱く合う |
| 学び | 0.2 | 自分を見つめる学びには弱く合う |
| 再出発 | 0.2 | 休息後の切り替えには弱く合う |
| 勝負 | 0.0 | 休息相談には強すぎるため原則加点しない |

### 6.6 health

健康、心身の安定、生活リズム、体調不安に関する相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 守り | 1.0 | 心身や生活基盤を守る文脈と最も接続する |
| 復興 | 0.9 | 回復・立て直し・元気を取り戻す文脈に合う |
| 静寂 | 0.6 | 休息・落ち着き・生活リズムの整理に合う |
| 再出発 | 0.3 | 生活習慣の立て直しには補助的に合う |
| 学び | 0.2 | 体調管理の学びには弱く合う |
| 縁 | 0.1 | 支援者・家族とのつながりには一部接続する |
| 勝負 | 0.0 | 体調相談では強すぎるため原則加点しない |

### 6.7 study_success

学業、資格、集中、継続、技術習得、積み上げに関する相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 学び | 1.0 | 知識・経験・技能の積み上げと最も接続する |
| 勝負 | 0.7 | 試験・合格・本番の勝負に合う |
| 静寂 | 0.5 | 集中・内省・継続のための環境に合う |
| 再出発 | 0.4 | 学び直し・再挑戦に合う |
| 守り | 0.3 | 不安を整えながら学ぶ文脈に合う |
| 復興 | 0.2 | 自信回復型の学習には弱く合う |
| 縁 | 0.1 | 師・仲間・学習機会には一部接続する |

### 6.8 protection

厄除け、守り、不安、リスク回避、安心したい相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 守り | 1.0 | 不安・リスクから距離を取る文脈と最も接続する |
| 静寂 | 0.7 | 心を落ち着け、状況を整理する文脈に合う |
| 復興 | 0.5 | 弱った状態から立て直す相談に合う |
| 再出発 | 0.3 | 厄落とし後の切り替えには補助的に合う |
| 縁 | 0.2 | 人間関係の守りには一部接続する |
| 学び | 0.1 | 予防・備えの学びには弱く合う |
| 勝負 | 0.0 | 守りの相談では強すぎるため原則加点しない |

### 6.9 travel_safe

移動、安全、旅行、出張、交通安全に関する相談。

| history_theme | score | reason |
| --- | ---: | --- |
| 守り | 1.0 | 安全・保護・リスク回避と最も接続する |
| 縁 | 0.5 | 旅先・土地・人とのご縁に接続する |
| 静寂 | 0.3 | 旅前の落ち着き・準備には補助的に合う |
| 再出発 | 0.3 | 新しい場所への移動には補助的に合う |
| 勝負 | 0.2 | 出張・勝負旅には一部接続する |
| 学び | 0.2 | 旅からの学びには弱く合う |
| 復興 | 0.1 | 療養・回復旅には一部接続する |

---

## 7. Implementation Candidate

実装する場合は、以下のように `SCORE_V3_HISTORY_THEME_BY_AXIS` を拡張する。

```python
SCORE_V3_HISTORY_THEME_BY_AXIS = {
    "career_change": {
        "勝負": 1.0,
        "再出発": 0.8,
        "学び": 0.6,
        "守り": 0.3,
        "静寂": 0.2,
        "縁": 0.2,
        "復興": 0.2,
    },
    "relationship_repair": {
        "縁": 1.0,
        "静寂": 0.7,
        "守り": 0.5,
        "再出発": 0.4,
        "復興": 0.4,
        "学び": 0.2,
        "勝負": 0.1,
    },
    "money_growth": {
        "守り": 1.0,
        "勝負": 0.8,
        "再出発": 0.6,
        "学び": 0.4,
        "縁": 0.3,
        "静寂": 0.2,
        "復興": 0.2,
    },
    "restart_mindset": {
        "再出発": 1.0,
        "勝負": 0.8,
        "静寂": 0.6,
        "学び": 0.5,
        "復興": 0.5,
        "守り": 0.3,
        "縁": 0.2,
    },
    "nature_reset": {
        "静寂": 1.0,
        "復興": 0.8,
        "守り": 0.6,
        "縁": 0.2,
        "学び": 0.2,
        "再出発": 0.2,
        "勝負": 0.0,
    },
    "rest_healing": {
        "静寂": 1.0,
        "復興": 0.8,
        "守り": 0.6,
        "縁": 0.2,
        "学び": 0.2,
        "再出発": 0.2,
        "勝負": 0.0,
    },
    "health": {
        "守り": 1.0,
        "復興": 0.9,
        "静寂": 0.6,
        "再出発": 0.3,
        "学び": 0.2,
        "縁": 0.1,
        "勝負": 0.0,
    },
    "study_success": {
        "学び": 1.0,
        "勝負": 0.7,
        "静寂": 0.5,
        "再出発": 0.4,
        "守り": 0.3,
        "復興": 0.2,
        "縁": 0.1,
    },
    "protection": {
        "守り": 1.0,
        "静寂": 0.7,
        "復興": 0.5,
        "再出発": 0.3,
        "縁": 0.2,
        "学び": 0.1,
        "勝負": 0.0,
    },
    "travel_safe": {
        "守り": 1.0,
        "縁": 0.5,
        "静寂": 0.3,
        "再出発": 0.3,
        "勝負": 0.2,
        "学び": 0.2,
        "復興": 0.1,
    },
}
```

`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` も同一mappingから派生させる方針が望ましい。

---

## 8. Open Questions

### 8.1 `career` / `money` / `relationship` との互換

既存LLM promptでは以下の古いaxisも存在する。

```text
career
money
relationship
study
health
protection
travel_safe
other
```

一方で product docs では以下の詳細axisが整理されている。

```text
career_change
money_growth
relationship_repair
restart_mindset
nature_reset
study_success
```

実装前に、`normalize_consultation_axis()` の正規化結果と、このmappingのkeyを揃える必要がある。

### 8.2 `other` の扱い

`other` は明示mappingしない。

理由:

- 雑に全themeへ弱加点すると推薦品質がぼやける
- `other` は query / need_tags / goriyaku_tag_ids を優先すべき

### 8.3 `history_signal` と `reason_facts` の二重加点

`history_theme` は reason_facts でも説明材料になる。

Score v3 で history_signal を強める場合、説明側で過剰に同じ根拠を繰り返さないように注意する。

---

## 9. Decision

このPRでは以下を行わない。

- `concierge_chat_ranking.py` の変更
- Score v3 weight変更
- Score v3 active化
- `SCORE_V3_HISTORY_THEME_BY_AXIS` の実装追加
- `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` の実装追加

まず mapping 設計を docs に固定する。

---

## 10. Next Actions

```markdown
- [x] develop最新化
- [x] ブランチ作成
- [x] 既存 consultation_axis 一覧確認
- [x] 既存 history_theme 一覧確認
- [x] rest_healing 既存mappingを基準として記録
- [x] career_change / relationship_repair / money_growth / study_success / restart_mindset / nature_reset の対応表を設計
- [x] health / protection / travel_safe の対応表を設計
- [x] 実装変更はしない
- [x] docsへ設計結果を記録
- [ ] PR作成・マージ
```

---

## 11. Proposed Implementation PR

次PRで実装する場合の候補。

### Branch

```text
feature/score-v3-consultation-axis-history-theme-mapping
```

### Scope

```text
backend/temples/services/concierge_chat_ranking.py
backend/temples/tests/services/test_score_v3_history_signal.py
```

### Implementation Plan

- mapping定数を拡張
- candidate boost mapping は main mapping から派生させる
- `resolve_score_v3_history_signal()` の既存挙動を維持
- 未定義axisは 0.0 を返す
- `other` は明示mappingしない

### Test Plan

- `career_change × 勝負 = 1.0`
- `relationship_repair × 縁 = 1.0`
- `money_growth × 守り = 1.0`
- `restart_mindset × 再出発 = 1.0`
- `nature_reset × 静寂 = 1.0`
- `study_success × 学び = 1.0`
- `health × 復興 = 0.9`
- `protection × 守り = 1.0`
- `travel_safe × 守り = 1.0`
- 未定義axisは `0.0`
- 未定義themeは `0.0`
