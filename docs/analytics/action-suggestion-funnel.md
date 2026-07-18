> **Status: Active**
>
> 本ドキュメントは、Action SuggestionのEvent名を管理する正本文書である。
>
> 正確なPayload、Propertyおよび実装状況は、関連するFrontend・Backend実装コードおよびテストを最終的な正本とする。

# Action Suggestion Funnel

## 目的

Action Suggestionカードの表示から行動着手・完了までを観測するため、送信されているEvent名を一意に整理する。

---

## Web

Action Suggestionカードが表示されたとき、以下の2つのEventが同時に送信される。

| Event | 意味 |
|---|---|
| `action_suggestion_preview_view` | Action Suggestionカード（primary / secondary行動、振り返り観点のプレビューを含む）が表示された |
| `action_suggestion_reflection_preview_view` | Action Suggestion内の振り返り観点のプレビューが表示された |

`action_suggestion_reflection_preview_view`は、実際のReflection入力UIが表示されたことを意味しない。実際のReflection入力UI表示は別のEventで計測しており、混同しない。正確な区別は`docs/product/visit-reflection-flow.md`および`docs/analytics/reflection-funnel-dashboard.md`を参照する。

Webでは、Primary / Secondary行動へのクリック、または行動の着手・完了を計測するEventは現時点で存在しない。

### action_suggestion_preview_view Payload

| 項目 | 内容 |
|---|---|
| source | Eventが発生した画面・導線 |
| threadId | 相談セッションID |
| resultSetId | 推薦結果セットID |
| shrineId | 神社ID |
| recommendationRank | 推薦順位 |
| position | 表示位置 |
| historyTheme | 履歴テーマ |
| actionSuggestionVersion | Action Suggestionのバージョン |
| primaryActionType | primary行動の種別 |
| secondaryActionType | secondary行動の種別 |
| actionPromptType | 振り返り観点の種別 |
| actionSource | 行動提案の根拠 |
| sourceKeys | 行動提案の根拠キー |
| summaryLine | 要約文 |

### action_suggestion_reflection_preview_view Payload

上記のPayloadに加えて、以下を送信する。

| 項目 | 内容 |
|---|---|
| reflectionPromptSourceSeed | 振り返り観点生成の元になった手掛かり |

---

## Mobile

Mobileでは、Action Suggestionカードの表示を計測するEventは存在しない。

Primary / Secondary行動をタップした場合、着手・完了に相当する記録がBackendへ送信される。これはPostHog Eventではなく、Backend側に永続化される記録である。

正確な送信内容、永続化条件および実装状況は、関連するMobile・Backend実装とテストを参照する。

---

## Web / Mobileの計測範囲の違い

| 観点 | Web | Mobile |
|---|---|---|
| カード表示の計測 | あり（PostHog Event） | なし |
| 行動の着手・完了の計測 | なし | あり（Backend永続化、PostHog Eventではない） |

WebとMobileでは、計測の対象および方式（PostHog Event / Backend永続化）がともに異なる。同一の指標として比較しない。

---

## 責務外

本書では以下を管理しない。

- KPIの具体値、成功基準
- Backend永続化の実装詳細
- 実装コード、テストケース

---

## 関連ドキュメント

- `docs/analytics/README.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`
- `docs/analytics/reflection-funnel-dashboard.md`
- `docs/audit/cross-platform-event-contract.md`

---

## 更新ルール

- 本書はAction SuggestionのEvent名およびWeb側Payloadのみを管理する。
- Event名が追加・変更・削除された場合は、実装確認のうえ本書を更新する。
- KPIの具体値、成功基準およびBackend永続化の実装詳細は本書で重複管理しない。
- Web / Mobileの計測範囲が変化した場合は、本書の記載を実態に合わせて更新する。
- TODO、PR計画、実装進捗および作業履歴は本書へ記載しない。
