

# 本番 Smoke 実施ログ

## 目的

本番デプロイ後に実施した smoke 確認の結果を記録し、障害・再発・復旧判断の履歴を残す。

確認手順は `docs/ops/production-smoke-checklist.md` を参照する。

## 記録ルール

- 本番デプロイ後に1行追加する
- 失敗があった場合は、下の incident history に詳細を残す
- 原因未確定の場合は `未確定` と書く
- 推測と事実を混ぜない
- 修正PRが必要な場合は次アクションに書く

## Smoke実施一覧

| 日時 | 環境 | commit / deploy | login | users/me | concierge/chat | my/goshuins | shrine-submissions | billing/status | billing/checkout | 判定 | メモ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD HH:mm | production | `<sha or deploy url>` | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | 未確定 |  |

## Incident History

### YYYY-MM-DD HH:mm - タイトル

| 項目 | 内容 |
|---|---|
| 環境 | production |
| commit / deploy | `<sha or deploy url>` |
| API | `/api/...` |
| method | GET / POST |
| status |  |
| Browser |  |
| Vercel Logs |  |
| Render Logs |  |
| Cookie状態 |  |
| 事実 |  |
| 推測 |  |
| 仮説 |  |
| 原因 | 未確定 |
| 対応 |  |
| 修正PR |  |
| 再発防止 |  |

## 次アクション

```markdown
- [ ] 失敗APIの原因分類
- [ ] 修正PR作成
- [ ] 再smoke実施
- [ ] checklist更新が必要なら反映
```

## 関連docs

- `docs/ops/production-smoke-checklist.md`
- `docs/ops/production-bff-hardening.md`
- `docs/triage/production-500-triage.md`
