

# KAMI MUSUBI Experience Design

## 目的

KAMI MUSUBIを「神社検索アプリ」ではなく、
相談から参拝、振り返りまでを一本の体験として提供するプロダクトへ発展させる。

体験設計を最上位の設計書（正本）とし、UI・API・DB・画面遷移は本ドキュメントに従って整理する。

---

# Experience Flow

```
相談
    ↓
神社との出会い
    ↓
詳細を知る
    ↓
参拝する
    ↓
振り返る
    ↓
次の相談へつながる
```

各画面は単独で完結するのではなく、次の体験へ自然に繋ぐ役割を持つ。

---

# Experience Design Tasks

## 1. URL設計修正

### ゴール
- URLは画面状態ではなくリソース識別子のみ保持する。

### 方針
- recommendationReason全文をURLへ渡さない
- shrine_id・thread_idなど必要最小限のみURLに保持
- 推薦理由・Action SuggestionはAPIまたは状態管理から取得
- URL共有でも画面が再構築できる構造にする

---

## 2. カード情報量整理

### ゴール
カードは「興味を持たせる入口」に限定する。

### カードに残す
- 神社名
- 写真
- 一致理由（短文1つ）
- 詳細を見るCTA

### 詳細へ移す
- Recommendation Reason全文
- Recommendation Facts
- Action Suggestion
- Reflection導線

原則は「要約→詳細」の二段階構成とする。

---

## 3. 詳細ページ v3

### ゴール
参拝ガイドとして体験を深める画面にする。

### セクション案
1. Hero（写真・神社名）
2. 今回選ばれた理由
3. 神社について（FACT）
4. この神社で意識したいこと
5. NEXT ACTION
6. 参拝前の問い
7. 振り返り入力

内部フィールド名やフォールバック文言を表示しない。

---

## 4. 記録タイムライン v1

### ゴール
記録を一覧ではなく「変化の履歴」として見せる。

### 1つのタイムライン
- 相談
- 推薦神社
- Favorite
- Visit
- Reflection

神社単位・時系列で振り返れる設計を採用する。

---

## 5. 画像 Placeholder設計

### ゴール
画像未登録でもブランド体験を維持する。

### 方針
- 神社写真がある場合はHero表示
- 未登録時はブランドPlaceholder表示
- 将来的に実写真へ置き換え可能な構造にする

---

# 実装優先順位

1. URL設計修正
2. カード情報量整理
3. 詳細ページ v3
4. 記録タイムライン v1
5. 画像Placeholder設計

---

# 設計原則

- カードは興味を引く
- 詳細ページは理解を深める
- 記録は変化を可視化する
- 神社ではなく『ユーザーの変化』を主役にする
- 相談→参拝→振り返り→再相談が循環する体験を設計する

## 6. 画面ごとの責務
# Screen Responsibility

## Concierge
役割：相談内容から神社との出会いを作る

## Shrine Detail
役割：なぜこの神社なのかを理解し、参拝への期待を高める

## Visit
役割：実際の行動を記録する

## Reflection
役割：行動後の変化を言語化する

## Records
役割：過去から現在までの変化を可視化する

---
## 7. Backend / Frontend の責務

# Source of Truth

Backend
- Recommendation
- Action Suggestion
- Reflection
- Behavior
- Score
- History

Frontend
- 表示
- 入力
- 状態管理
- 画面遷移

URL
- shrine_id
- thread_id

URLに持たない
- recommendationReason全文
- ActionSuggestion全文
- Reflection本文
---
