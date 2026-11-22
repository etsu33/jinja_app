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

## 追記：挑戦だけにつなぎ直す（2026-11-22・PR #3512 のあと）

### 何が起きたか
PR #3512 のマージ後、本番で新宿駅の近くから「やり直したい」と相談すると、上位3件が妙義神社（約108km）・寒川神社（約44km）・三峯神社（約74km）になり、花園神社（マージ前は1位）が外れた。3社とも気持ち（mental）と挑戦（courage）の両方に当たっていた。気持ちの相談はご利益ではなく神社の雰囲気で選ぶので、花園神社は気持ちに当たらず、両方に当たる遠い神社に負けたと考えている（推測）。

### 決めたこと（2026-11-22 えつこさん）
- 5語を気持ち（mental）から外し、挑戦（courage）だけにつなぐ
- あわせて、遠い神社が1位になる原因（近さが順位に効いていない件）を調べる。気持ちのほうで花園神社に点が入るよう、神社の雰囲気のデータを足すことも検討する

### 変更
- `need_tags.py` の `KEYWORDS["mental"]` と、`consultation_interpreter.py` の `NEED_KEYWORDS["mental"]` から5語を外す
- テストを「挑戦だけ」に合わせる

| 相談 | PR #3512 | この変更のあと |
|---|---|---|
| やり直したい | mental, courage | courage |
| 不安でやり直したい | mental, courage | mental, courage（「不安」で気持ちが取れる） |
| 仕事でやり直したい | career, mental, courage | career, courage |
