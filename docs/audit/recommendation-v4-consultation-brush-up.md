# Recommendation v4 / Consultation Brush-up

> **Status: Archive**
>
> 本ドキュメントは、Consultation改善作業のScope・KPIを整理した短期計画である。
>
> Scope記載の各Profile項目は `backend/temples/services/consultation_interpreter.py` 等の実装を正本とする。

## Goal

相談文の解釈精度と推薦理由の深さを改善し、detail_open_rate / save_rate / route_open_rate / reflection_saved_rate の改善につなげる。

## Current State

- Score v3 runtime integration 済み
- Score v3 observer 統一済み
- Recommendation Quality Audit 追加済み
- CI report-only 追加済み

## Problems

- 推薦理由がご利益説明に寄る
- 行動提案が抽象的になる
- history_theme が相談文脈と弱く接続される
- 同じ意味の説明が重複する

## Scope

- consultation_interpreter の出力項目整理
- raw_query / state_profile / need_profile / direction_profile / emotion_profile / action_intent の責務定義
- history_theme の改善ルール
- recommendation reason の深さ基準
- action_suggestion の具体化ルール

## Out of Scope

- 本番ranking logicの変更
- Score v3 weight変更
- CI fail化
- 課金導線UI変更

## KPI

- detail_open_rate
- save_rate
- route_open_rate
- reflection_saved_rate
