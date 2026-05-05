# Concierge Ranking Observation

## 現在のranking構造

実際の並び順は `breakdown.score_total` ではなく、内部値 `_score_total` で決まる。

### 現行 need mode weight

- element: 0.6
- need: 0.3
- popular: 0.1
- distance: 0.35

### 観測結果

- distance は `_score_total` に含まれている
- tone は ranking 本体には入っていない
- popular は MVP の相談体験では優先度が低い
- 現行 need mode は「悩み重視」というより「相性 + 距離」寄り

## MVP向けの仮weight案

### need mode

- need: 0.50
- distance: 0.30
- element: 0.18
- popular: 0.02

### 役割

- need: なぜ行くか
- distance: 実際に行けるか
- element: 納得材料
- popular: 同点時の補助

## visit_style（参拝スタイル）方針（MVP）

### 方針
- 自由入力の自然言語だけに依存せず、**UIチップで選択させる**
- 内部は英語タグで統一し、表示は多言語化で切替
- ranking には soft_signal として接続（将来的に score へ昇格検討）

### 初期タグ（6）
- quiet：静かに参拝したい
- less_crowded：人が少ない場所がいい
- nearby：近くで無理なく行きたい
- nature：自然を感じたい
- reset：気持ちを切り替えたい
- classic：有名・定番が安心

### 役割分担
- need：何を願うか（ご利益）
- visit_style：どう参拝したいか（過ごし方）
- distance：実際に行けるか
- element：納得材料
- popular：同点補助

### 実装メモ
- UI：ConciergeFilterPanel にチップ追加
- backend：extra_condition → soft_signal_tags に変換
- ranking：まずは並び替えには直接使わず、将来的に visit_style_score を検討
- i18n：タグキーは英語固定、表示文言のみ翻訳

## ▼ visit_style ranking加点設計（検討）

### ■ 目的
参拝スタイル（気分・行動意図）をランキングに反映する

### ■ 背景
- 現状は need / element / distance が主軸
- 気分系（静か・自然・リフレッシュ）が順位に効いていない
- UIチップで選択できるようになったため、rankingに接続する

---

### ■ スコア構造（仮）

need: 0.45  
distance: 0.30  
visit_style: 0.15  
element: 0.08  
popular: 0.02  

---

### ■ visit_style の役割

- 主軸ではなく「補助軸」
- need を満たした候補の中で順位を調整する

---

### ■ 競合ルール

NG：
- visit_style が need を上書きする

OK：
- need一致内で visit_style が順位を微調整する

---

### ■ 実装方針（未実装）

- soft_signal_tags / visit_style_tags を breakdown に追加
- score_visit_style を計算
- _score_total に加算（重み0.15）

---


### ■ 検証方法

- A/B: visit_styleあり vs なし
- 同一クエリで順位変化を見る
- location変更と組み合わせて確認

### ■ A/B観測結果（仮weight 0.15）

#### 条件
- クエリ: 金運を整えたい
- extra_condition: 静かな場所がいい
- location: 東京駅付近

#### weight 0.0（現状）
1. 浅草神社: score=2.2142 / need=2 / visit=0
2. 神田神社（神田明神）: score=1.5796 / need=1 / visit=0
3. 日枝神社: score=1.5718 / need=1 / visit=1

#### weight 0.15（仮）
1. 浅草神社: score=2.2142 / need=2 / visit=0
2. 日枝神社: score=1.7218 / need=1 / visit=1
3. 神田神社（神田明神）: score=1.5796 / need=1 / visit=0

#### 観測結果
- visit_style一致（quiet）の日枝神社のみ +0.15 加点
- 日枝神社が3位→2位に上昇
- 浅草神社（need=2）は順位維持


#### 判断
- visit_style は順位の微調整として機能している
- need を上書きしないことを確認
- 補助軸として妥当な挙動

## ▼ visit_style weight 0.35 仮比較結果

### 観測条件

- query: 静かな場所で参拝したい
- extra_condition: 静かな場所がいい
- location: 東京駅周辺
- 比較: visit_style weight 0.15 → 0.35

### 結果

- weight 0.15 でも quiet 一致候補は TOP3 に入った
- weight 0.35 では quiet 一致候補のスコア差がより明確になった
- need=2 候補は visit_style 一致候補に上書きされず、上位維持を確認
- fallback / 候補不足は発生しなかった

### 判断

現時点ではフィルタ寄せではなく、ブースト方式を継続する。  
visit_style は hard filter ではなく、need を壊さない補助ランキング軸として扱う。

### 採用方針

- visit_style weight は 0.35 を仮採用
- need 一致の強さを上書きしないことをテストで固定
- 神社側 visit_style_tags の網羅率が上がるまでは filter 化しない

## ▼ visit_style_tags 30件拡張後の観測

### KPI

- visit_style_tags付与率: 31 / 100 = 31%

### rankingでvisit_styleが効いた割合

- quiet: 3 / 3 = 100%
- business: 2 / 3 = 66.7%
- study: 1 / 3 = 33.3%
- nature: 1 / 3 = 33.3%
- reset: 1 / 3 = 33.3%

平均: 8 / 15 = 53.3%

### 無効ケース

- business:
  - 3位 乃木神社
  - visit_style contribution = 0
  - need側では残るが business タグ不一致

- study:
  - 2位 神田神社（神田明神）
  - visit_style contribution = 0
  - business寄りタグのため study には寄与しない

- nature:
  - 2位 神田神社（神田明神）
  - visit_style contribution = 0
  - natureタグ未付与

- reset:
  - 2位 神田神社（神田明神）
  - visit_style contribution = 0
  - resetタグ未付与

### 判断

- 31%付与時点で、visit_styleはTOP候補に反映される
- quiet / business は比較的効きやすい
- study / nature / reset はTOP3内での一致数がまだ少ない
- 無効ケースの主因は「needで残るが visit_style_tags が未一致」

### breakdownログ可視化案

- `visit_style.matched_tags`
- `visit_style.contribution`
- `score_total_ranked`
- `matched_need_tags`
- `recommendation rank`

上記をCSVまたはJSONLで出力し、以下を集計する。

- visit_style一致率
- contribution分布
- タグ別hit率
- need一致あり / visit_style不一致の件数

## ▼ visit_style_tags 50%拡張後の観測

### KPI

- visit_style_tags付与率: 51 / 100 = 51%

### rankingでvisit_styleが効いた割合

- quiet: 3 / 3 = 100%
- business: 2 / 3 = 66.7%
- study: 1 / 3 = 33.3%
- nature: 1 / 3 = 33.3%
- reset: 1 / 3 = 33.3%

平均: 8 / 15 = 53.3%

### 30件拡張時点との差分

- visit_style_tags付与率は 31% → 51% に改善
- rankingでvisit_styleが効いた割合は 53.3% のまま横ばい
- quiet / business は引き続きTOP3内で効きやすい
- study / nature / reset はタグを増やしてもTOP3内hit数は改善しなかった

### 観測結果

- 付与率を50%まで引き上げても、東京駅周辺のTOP3ではhit率が大きく変わらなかった
- study / nature / reset は、タグ不足だけでなく候補プール / 距離 / need側スコアの影響を受けている可能性がある
- visit_style weight = 0.35 は引き続きneedを上書きしていない
- 50%拡張後も、visit_styleはhard filterではなく補助ランキング軸として扱う方針を維持する

### 無効ケース

- study:
  - 2位 神田神社（神田明神）
  - visit_style contribution = 0
  - studyタグ不一致だが、need / classic / business文脈で残る

- nature:
  - 2位 神田神社（神田明神）
  - visit_style contribution = 0
  - natureタグ不一致だが、候補上位に残る

- reset:
  - 2位 神田神社（神田明神）
  - visit_style contribution = 0
  - resetタグ不一致だが、候補上位に残る

### 判断

- 現時点のボトルネックは単純なタグ付与率だけではない
- 特に study / nature / reset は、候補抽出・距離・needスコアとの相互作用を見る必要がある
- 次の改善では、タグ追加よりも「visit_style一致候補が候補プールに入っているか」を観測する
- rankingロジック変更はまだ行わず、まずはログ可視化で原因を分解する

## ▼ visit_style 50%拡張後の追加観測（before_trim）

### 観測結果

- study / nature / reset はいずれも pool_size=12 に対して hit_count=1
- 一致候補はすべて rank1 に上がっている
- visit_style weight=0.35 はランキング上で有効に機能している

### 解釈

- visit_style 自体は「効いていない」のではなく「効く対象が少ない」状態
- 一致候補が1件しかないため、TOPに上がるが全体の分布には影響しない

### ボトルネック

- hit率横ばいの主因は ranking weight ではない
- 候補プール内の visit_style 一致候補の不足が支配的

### 次の改善対象

- ranking weight の調整ではなく、以下にフォーカスする

1. candidate pool の拡張
2. prefilter で visit_style を弱条件として考慮する
3. visit_style 一致候補が pool に含まれる確率の向上

### 判断

- 現段階で weight の再調整は不要
- visit_style は十分に機能しているため、改善は「供給側（候補生成）」に寄せる

## ▼ candidate pool 12→20 A/B観測

### 観測条件

- query: 合格祈願をしたい
- extra_condition: 勉強や試験に向いた神社がいい

- query: 自然を感じながら参拝したい
- extra_condition: 自然や緑を感じられる神社がいい

- query: 気持ちを切り替えたい
- extra_condition: リセットできる神社がいい

### A案: candidate pool 12→20

#### 結果

- study:
  - pool 12: hit_count 1
  - pool 20: hit_count 2
  - 追加で湯島天満宮が候補に入り、TOP2が study 一致

- nature:
  - pool 12: hit_count 1
  - pool 20: hit_count 2
  - 根津神社 / 明治神宮が nature 一致としてTOP2に表示

- reset:
  - pool 12: hit_count 1
  - pool 20: hit_count 3
  - 小網神社 / 愛宕神社 / 品川神社が reset 一致としてTOP3に表示

### 観測結果

- candidate pool を 12 から 20 に広げることで、study / nature / reset すべてで visit_style 一致候補が増えた
- 50%拡張後にhit率が横ばいだった主因は、ranking weight ではなく candidate pool 側の候補不足だった
- visit_style weight = 0.35 は、一致候補が候補プールに入っていればTOPへ押し上げる挙動を確認できた

### B案: prefilter に visit_style を弱ブースト

- 現時点では未実施
- A案だけで hit_count が改善したため、まずは candidate pool 拡張を優先して評価する
- B案は、pool 20 でも一致候補が不足するタグが残った場合に検討する

### 判断

- A案 `candidate pool 12→20` は採用候補
- B案 `prefilter visit_style 弱ブースト` は保留
- 次は pool 20 の副作用として、処理時間・不要候補増加・TOP3品質低下がないかを確認する

## ▼ 神社側 visit_style タグ保持方針（検討）

### ■ 目的
ユーザーが選んだ visit_style を、候補神社ごとの差分として ranking に反映できるようにする。

現状はユーザー側の visit_style は抽出できているが、神社側に対応する特徴タグがないため、全候補に同じ visit_style が乗り、順位差が出ない。

---

### ■ 比較

| 方式 | メリット | デメリット | 判断 |
|---|---|---|---|
| seed に `visit_style_tags` を追加 | 既存 seed 管理に乗せやすい / MVPで手動整備しやすい / 代表神社から始められる | import処理の対応が必要 / seed未投入環境では反映されない | MVPで採用 |
| DB に `Shrine.visit_style_tags` JSONField を追加 | rankingで参照しやすい / admin編集に拡張しやすい / 長期運用に向く | migration が必要 / 初期データ投入が必要 | MVP〜中期で採用 |
| コード内 map で持つ | 最速で検証できる / migration不要 | DB/seedと二重管理になる / 長期負債化しやすい / 運用者が編集しにくい | 採用しない |

---

### ■ MVP方針（仮固定）

MVPでは **seed + DB JSONField** を採用する。

- `Shrine.visit_style_tags` を JSONField として追加する
- `shrines_seed_clean.json` に `visit_style_tags` を追加する
- `import_shrines_seed` で `visit_style_tags` を取り込む
- まずは代表神社だけ手動タグ付けする
- ranking加点は神社側タグ投入後に実施する

---

### ■ 初期運用

- 全神社を一気にタグ付けしない
- 東京・主要候補など、コンシェルジュに出やすい神社から整備する
- 不明な神社は `visit_style_tags: []` として扱う
- 空配列の場合は visit_style 加点なし

---

### ■ ranking加点の前提

ranking加点は、以下が揃ってから実施する。

- user側 `visit_style_tags` が抽出できている
- shrine側 `visit_style_tags` が候補に載っている
- `breakdown_detail.features.visit_style` で一致タグを観測できる
- 代表クエリで visit_style あり / なしの差分を確認できる

---

### ■ ranking導入順序

visit_style は以下の順序で導入する。

1. 神社側に `visit_style_tags` を入れる
2. 候補辞書に `visit_style_tags` を載せる
3. `breakdown_detail.features.visit_style` で可視化する
4. visit_style あり / なしの差分を確認する
5. 問題なければ `_score_total` に加点する

加点は最後に行う。  
タグ投入直後に ranking へ反映しない。

### ■ 実装順

1. `Shrine.visit_style_tags` JSONField を追加
2. migration を作成
3. `import_shrines_seed` に取り込み対応を追加
4. seed に代表神社の `visit_style_tags` を追記
5. `build_chat_candidates` で候補辞書に `visit_style_tags` を載せる
6. breakdown_detail で user側 × shrine側の一致を観測
7. 問題なければ `_score_total` に visit_style 加点を入れる

## 次に確認すること

- 既存テストで weight を固定している箇所
- need mode weight変更時の上位候補差分
- 同一クエリで location を変えた時の上位3件差分

## ▼ candidate pool 20 副作用確認

### 観測結果

- nature: pool20で hit_count=2、TOP2が nature一致
- total_ms=85.9ms のため、処理時間の大きな悪化は見られない
- TOP3の3位に visit_style 不一致候補が残るため、pool20採用前に quiet / business でも品質確認した
- quota_checkで弾かれたログは candidates=0 / recs=0 のため観測対象外
- quiet: pool20で hit_count=7、TOP3すべて quiet 一致
- business: pool20で hit_count=9、TOP1/TOP2は business + career 一致
- business TOP3の乃木神社は business 不一致だが、career 一致のため完全なノイズではない
- total_ms は quiet=82.9ms / business=77.5ms で、大きな処理時間悪化は見られない
- pool20で“無関係な強い神社”がTOP3に紛れ込む挙動は、今回の観測では確認されなかった
- ただし business はTOP3をvisit_style一致で揃えきれていないため、採用後も継続観測する

### 判断

- candidate pool 12→20 は採用候補として妥当
- 処理時間・TOP3品質・候補ノイズの大きな悪化は今回の観測では確認されなかった
- B案の prefilter visit_style 弱ブーストは現時点では保留


### 補足: poolログの見方

- `[pool]` は candidate生成直後 / ranking前の観測ログ
- `visit_style_hits` は、候補プール内にユーザーの visit_style と一致する神社が何件あるかを見る
- `need_hits` はこの位置では `matched_need_tags` 付与前のため、0になりやすい
- need一致の評価は ranking後の `breakdown.matched_need_tags` / `visit_style_observation_before_trim` 側で確認する
- poolログは candidate pool 20 採用判断までの一時観測ログとして扱う
