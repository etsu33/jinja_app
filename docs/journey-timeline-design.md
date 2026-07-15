> **Status: Reference**
>
> 本ドキュメントは、対象機能の設計背景・補足方針を記録した参照資料である。
>
> 現行仕様は関連するActive文書、実装コードおよびテストを最終的な正本とする。
# Journey Timeline Design

## 1. Background

なぜ変更するか

---

## 2. Current Problems

- 記録カテゴリが多い
- 時系列になっていない
- 行動が分断されている

---

## 3. Design Principles

相談からご縁が育つ体験を記録する

Event と State を分離する

途中で終わることを正常系とする

---

## 4. Information Architecture

記録

├ ご縁の歩み
└ 保存した神社

---

## 5. Journey Event

consultation_created

recommendation_shown

visit_completed

goshuin_registered

reflection_created

---

## 6. State

favorite

---

## 7. Timeline UI

イベントのみ並べる

お気に入りはマーカー表示

---

## 8. MVP Scope

Phase1

相談

提案

参拝

振り返り

Phase2

御朱印

写真

---

## 9. Migration Plan

既存画面

相談履歴

参拝履歴

振り返り履歴

↓

Journey Timeline
