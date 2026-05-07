# 本番500トリアージ

## 目的
本番で発生している複数APIの500を、原因別に分類して修正PRを分離する。

## 発生API一覧

| 優先 | API | Method | 観測元 | 状態 | 次に見るログ |
|---:|---|---|---|---|---|
| 1 | /api/billings/checkout | POST | Chrome Console / Network | 500確認 | Vercel Function Logs → Render backend logs |
| 2 | /api/concierge/chat/ | POST | Chrome Console | 500確認 | Vercel Function Logs → Render backend logs |
| 3 | /api/my/goshuins/ | GET | Chrome Console | 500確認 | Vercel Function Logs → Render backend logs |
| 4 | /api/shrine-submissions... | GET/POST要確認 | Chrome Console | 500確認 | Vercel Function Logs → Render backend logs |

## 調査順
1. /api/billings/checkout
2. /api/concierge/chat/
3. /api/my/goshuins/
4. /api/shrine-submissions

## ログ確認

### Vercel Function Logs
- BFF Route Handler の例外
- upstream URL
- upstream response status
- env不足
- cookie / auth forward

### Render backend logs
- Django traceback
- DB relation does not exist
- auth / permission error
- billing provider error
- serializer / migration mismatch

## 原因分類

| API | Vercel側 | Render側 | 仮説 | 修正PR |
|---|---|---|---|---|
| /api/billings/checkout | 未確認 | 未確認 | 未確定 | 未確定 |
| /api/concierge/chat/ | 未確認 | 未確認 | 未確定 | 未確定 |
| /api/my/goshuins/ | 未確認 | 未確認 | 未確定 | 未確定 |
| /api/shrine-submissions | 未確認 | 未確認 | 未確定 | 未確定 |

## 判断ルール
- 原因が違うものは同じPRで直さない
- DB差分は docs に記録してから修復する
- BFF修正と backend schema 修復は分離する
- billing analytics とは混ぜない
