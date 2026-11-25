# 場所ごとの物差しで、コンシェルジュの候補の範囲を決める

> Status: Audit — 実装記録
> 日付: 2026-11-23 JST
> Branch: `feature/concierge-adaptive-radius`
> 決まりの正本: `docs/product/recommendation-signal-authority.md` §9「Semantic Fit vs Distance」（このPRで追記）
> 試算: ドライブ KAMIMUSUBI「KAMI MUSUBI 場所ごとの物差しの試算（2026-11-23）」

## 何が起きていたか

新宿駅の近くから「転職したい」と相談すると約310km先の椿大神社が1位になり、「やり直したい」（気持ちにもつないだとき）では約44〜108km先の神社が上位3件を占めた（2026-11-22 本番で確認）。

- 近さの点は `0.35 × e^(−距離÷2.5km)` で、最大0.35
- 相談の種類が1つ当たると約0.6〜0.72
- 相談した人の位置は候補を絞るのに使っていなかった

そのため、相談の種類が1つ多く当たるだけで、どれだけ近い神社にも勝つ。

## 決めたこと（2026-11-23 えつこさん）

- 決まったkm（例：30km）では絞らない。神社の数が地域で大きく違い、地方では候補が1〜3社になるため
- 物差し：相談した人の位置から近い方に10社目の神社までの距離
- 候補に残す範囲：物差しの3倍以内
- 相談した人の位置が無いときは今までどおり（範囲で絞らず、近さの点も入らない）。出発地を選ぶよう促す案内は別の作業

## 変更

- `temples/services/concierge_adaptive_radius.py`（新規）：`apply_adaptive_radius(candidates)`
  - 位置の付いた候補が10社に満たないとき、物差しが0のときは絞らない
  - `distance_m` が無い候補・不正な値の候補は外さない
  - 並び順は変えない
- `temples/services/concierge_chat.py`：`build_chat_recommendations` で候補を受け取った直後に適用。英語の相談（travel モード）には当てない。`_debug.adaptive_radius` に記録（`_debug` は応答から外れる）

## 変えていないこと

- 点数の式（近さの点の `_distance_decay` を含む）、重み、推薦理由
- 候補の集め方（`build_chat_candidates`）
- 英語の相談（travel モード）

## 試算（本番131社、N＝10・倍率＝3）

| 場所 | 物差し | 候補に残す範囲 | 残る神社 |
|---|---|---|---|
| 新宿 | 6km | 17km | 26社 |
| 京都 | 14km | 42km | 15社 |
| 新潟 | 78km | 233km | 43社 |
| 広島 | 204km | 611km | 50社 |

地方では範囲が数百kmになり、結果はほとんど変わらない。都市で遠い神社が上位に来るのを止める仕組み。

## テスト

- `temples/tests/test_concierge_adaptive_radius.py`（新規）：都市で遠い神社が外れる、地方の物差しでは残る、位置が無いと絞らない、距離つきが10社未満なら絞らない、距離が無い候補は残す、並び順を変えない、`build_chat_recommendations` との結合
- `tests/services/test_concierge_candidate_universe_f2.py`：対象の神社の既定の位置を約167km先から約56km先に移した。この test は人気順の件数上限で候補を切らないことを確かめるもので、距離は関係しない。新しい範囲（この fixture では約70km）の内側で、すべての filler（約22〜33km）より遠い位置にした
- バックエンド全体：残る失敗9件は develop でも同じく失敗する環境依存のもの（test_concierge_api ×3、test_removed_shrines_import ×4、nsrc_000002、audit_tls_evidence）
