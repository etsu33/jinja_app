# 本番500トリアージ

## 目的
本番で発生している複数APIの500を、原因別に分類して修正PRを分離する。

## 発生API一覧

| 優先 | API | Method | 観測元 | 状態 | 次に見るログ |
|---:|---|---|---|---|---|
| 1 | /api/billings/checkout | POST | Chrome Console / Network | 200確認 / 500再現なし | 対象外（再発時のみ確認） |
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
| /api/billings/checkout | 200確認 | 200確認 | 現時点で500再現なし | 対象外（再発時のみ） |
| /api/concierge/chat/ | 500確認 / backendへ到達 | 500 HTML応答 | backend例外。DB/schema以外の可能性も残る | 未確定 |
| /api/my/goshuins/ | 500確認 / backendへ到達 | 500 HTML応答 | backend例外。実テーブルは存在確認済みのため列/serializer/query要確認 | 未確定 |
| /api/shrine-submissions | 500確認 / backendへ到達 | 500 HTML応答 | backend例外。実テーブルは存在確認済みのため列/serializer/query要確認 | 未確定 |

## DB / migration 確認結果

### ローカル確認

- `python manage.py showmigrations temples`: 0080 まで適用済み
- `python manage.py migrate --plan`: No planned migration operations
- `python manage.py check`: no issues
- `temples_goshuin`: 存在
- `temples_goshuinimage`: 存在
- `temples_shrinesubmission`: 存在
- `temples_conciergethread`: 存在
- `temples_conciergemessage`: 存在
- `temples_featureusage`: 存在

### 判断

- migration履歴上の未適用は確認できていない
- 対象テーブルの欠損は確認できていない
- したがって、`relation does not exist` だけを本命とはしない
- 次は対象modelの列差分、serializer、queryset、permission、view内例外を確認する

## 判断ルール
- 原因が違うものは同じPRで直さない
- DB差分は docs に記録してから修復する
- BFF修正と backend schema 修復は分離する
- billing analytics とは混ぜない
- migration履歴が正常でも、列差分・serializer・querysetで500になる可能性を切り分ける
