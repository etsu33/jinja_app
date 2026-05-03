# Concierge Ranking Observation

## 現在のranking構造

実際の並び順は `breakdown.score_total` ではなく、内部値 `_score_total` で決まる。

### 現行 need mode weight

- element: 0.6
- need: 0.3
- popular: 0.1
- distance: 0.35

### 観測結果

- distance は `_score_total` に含まれている
- tone は ranking 本体には入っていない
- popular は MVP の相談体験では優先度が低い
- 現行 need mode は「悩み重視」というより「相性 + 距離」寄り

## MVP向けの仮weight案

### need mode

- need: 0.50
- distance: 0.30
- element: 0.18
- popular: 0.02

### 役割

- need: なぜ行くか
- distance: 実際に行けるか
- element: 納得材料
- popular: 同点時の補助

## visit_style（参拝スタイル）方針（MVP）

### 方針
- 自由入力の自然言語だけに依存せず、**UIチップで選択させる**
- 内部は英語タグで統一し、表示は多言語化で切替
- ranking には soft_signal として接続（将来的に score へ昇格検討）

### 初期タグ（6）
- quiet：静かに参拝したい
- less_crowded：人が少ない場所がいい
- nearby：近くで無理なく行きたい
- nature：自然を感じたい
- reset：気持ちを切り替えたい
- classic：有名・定番が安心

### 役割分担
- need：何を願うか（ご利益）
- visit_style：どう参拝したいか（過ごし方）
- distance：実際に行けるか
- element：納得材料
- popular：同点補助

### 実装メモ
- UI：ConciergeFilterPanel にチップ追加
- backend：extra_condition → soft_signal_tags に変換
- ranking：まずは並び替えには直接使わず、将来的に visit_style_score を検討
- i18n：タグキーは英語固定、表示文言のみ翻訳

## ▼ visit_style ranking加点設計（検討）

### ■ 目的
参拝スタイル（気分・行動意図）をランキングに反映する

### ■ 背景
- 現状は need / element / distance が主軸
- 気分系（静か・自然・リフレッシュ）が順位に効いていない
- UIチップで選択できるようになったため、rankingに接続する

---

### ■ スコア構造（仮）

need: 0.45  
distance: 0.30  
visit_style: 0.15  
element: 0.08  
popular: 0.02  

---

### ■ visit_style の役割

- 主軸ではなく「補助軸」
- need を満たした候補の中で順位を調整する

---

### ■ 競合ルール

NG：
- visit_style が need を上書きする

OK：
- need一致内で visit_style が順位を微調整する

---

### ■ 実装方針（未実装）

- soft_signal_tags / visit_style_tags を breakdown に追加
- score_visit_style を計算
- _score_total に加算（重み0.15）

---

### ■ 検証方法

- A/B: visit_styleあり vs なし
- 同一クエリで順位変化を見る
- location変更と組み合わせて確認

## 次に確認すること

- 既存テストで weight を固定している箇所
- need mode weight変更時の上位候補差分
- 同一クエリで location を変えた時の上位3件差分
