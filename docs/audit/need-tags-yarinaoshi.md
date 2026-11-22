# やり直し系の言葉を相談の種類の辞書に足す

> Status: Audit — 実装記録
> 日付: 2026-11-22 JST
> Branch: `feature/need-tags-yarinaoshi`
> 決まりの正本: ドライブ「KAMI MUSUBI 相談の種類を取る辞書の決まり」（2026-11-22 作成。ルールの目次の31行目）

## 目的

「やり直したい」の相談から相談の種類が取れず、推薦に見どころ（花園神社の芸能浅間神社）を出せなかった（2026-11-22 本番で確認。新宿駅の近くから相談）。

## 決めたこと（2026-11-22 えつこさん）

- 「やり直し」「やり直す」「再出発」「再挑戦」「立て直し」を、挑戦（courage）と気持ち（mental）の両方につなぐ
- 「もう一度」は足さない（「もう一度行きたい」のような、相談ではない文でも当たるため）

## 変更

- `temples/domain/need_tags.py` の `KEYWORDS["courage"]`・`KEYWORDS["mental"]` に5語を足す
- `temples/services/consultation_interpreter.py` の `NEED_KEYWORDS`（shadow 用）にも同じ5語を足す（既存の慣例どおり、同じ語を持たせる）

## 結果（ローカルで確認）

| 相談 | 前 | 後 |
|---|---|---|
| やり直したい | なし | mental, courage |
| 再出発したい | なし | mental, courage |
| 仕事でもう一度やり直したい | career | career, mental, courage |
| もう一度行きたい | なし | なし |
| 転職したい | career | career（変わらない） |
| もう一度挑戦したい | courage | courage（変わらない） |

`NEED_PRIORITY` では気持ち（mental）が挑戦（courage）より上。見どころは、承認済みのアンサーがある相談の種類の中で優先順の高いものを選ぶので、気持ちのアンサーが無いうちは挑戦のアンサーが出る。気持ちのアンサーを足すと、そちらが優先される。

## 影響

- 「やり直し」などを含む相談で、推薦の主な相談の種類が変わる（今までは何も取れていなかった）。順位も変わりうる。マージ後に本番で同じ相談を試して確かめる
- Migration なし

## テスト

- `temples/tests/test_need_tags_yarinaoshi.py`（新規）
- バックエンド全体：9件の失敗は develop でも同じく失敗する環境依存のもの（test_concierge_api ×3、test_removed_shrines_import ×4、nsrc_000002、audit_tls_evidence）
