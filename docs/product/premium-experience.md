> **Status: Active**
>
> 本ドキュメントは、Free / Premiumの体験価値と画面別の境界を管理する正本文書である。
>
> 具体的な料金・プラン構成は`docs/product/pricing.md`、Billing / Paywallの判定原則は`docs/product/billing-paywall.md`、収益導線の設計は`docs/product/monetization-flow-design.md`を参照する。正確な物理実装と挙動は、関連する実装コードおよびテストを最終的な正本とする。

# Premium Experience 境界

## 目的

Premium 体験の責務を、UI / API / copy の判断基準として固定する。

Premium は、ユーザーにとって「神社を探せる」ことではなく、「なぜ自分に合うのかが分かり、記録として積み上がる」ことに価値を置く。

---

## 体験原則

1. パーソナル理由を厚くする
2. 相性を説明する
3. 継続利用で価値が増える
4. 保存・記録の深さを広げる
5. Map / Search を主価値にしない

---

## Free / Premium の体験差

### Free

Free は、相談から神社詳細、経路案内までの基本導線を提供する。

- 今の相談に対する基本推薦
- 神社ごとの基本説明
- 補助的な検索・地図探索
- 最小限の保存・御朱印管理

### Premium

Premium は、同じ推薦でも「自分にとっての意味」を深める。

- 推薦理由の深掘り
- 願い・悩み・関心との相性説明
- 相談履歴を踏まえた継続分析
- お気に入り、御朱印、訪問メモ、相談結果の保存拡張
- 過去の記録から次の参拝を考える導線

---

## 置いてよい Premium 表現

Premium として扱ってよい表現:

- 「前回の相談と比べて、今回はこの観点が強い」
- 「保存した神社と比べると、この神社は仕事運より心身の切り替えに寄っている」
- 「過去の御朱印記録から見ると、静かな参拝先を好む傾向がある」
- 「この推薦理由を保存して、あとから見返せる」

これらは、ユーザーの文脈・相性・継続記録に紐づくため Premium 価値として扱える。

---

## 置かない Premium 表現

Premium の中心に置かない表現:

- 「地図が高機能になる」
- 「検索条件が増える」
- 「近い神社をもっと探せる」
- 「経路案内が便利になる」

Map / Search は到達手段であり、Premium 訴求の主語にしない。必要な場合でも、パーソナル理由や保存記録を補助する導線として扱う。

---

## 保存・履歴・比較の原則

### 保存

保存は神社情報を集めるためだけの機能ではない。

その時の相談、状態、推薦理由、参拝および振り返りを、後から確認するための体験記録として扱う。

### 履歴

履歴は操作ログの一覧ではない。

相談・参拝・Reflectionを時間軸で接続し、ユーザーが自身の状態や行動の変化を振り返るための体験として扱う。

### 比較

Premiumにおける比較対象は、他のユーザーではなく過去の自分とする。

比較は優劣を評価するためではなく、相談テーマ、行動、参拝傾向および振り返りの差分を理解し、自身の変化を振り返るために使用する。

---

## 画面別の境界

### コンシェルジュ

Premium の中心画面。

- Free: 相談内容に基づく基本推薦
- Premium: 理由の深掘り、相性、継続文脈、保存された相談との比較

### 神社詳細

神社の公開情報を正確に伝える画面。

- Free: 由緒、所在地、ご利益、公開御朱印、基本導線
- Premium: コンシェルジュ起点の個人向け補足理由、保存済み記録との接続

詳細は `docs/product/shrine-detail-layer.md` を参照する。

### マイページ

Premium の継続価値を見せる画面。

- Free: 最小限の保存・管理
- Premium: 保存上限、記録整理、傾向分析、過去相談との接続

### Map / Search

補助導線。

- Free: 候補発見、比較、近隣確認
- Premium: 主価値にしない。必要な場合も「保存済み文脈からの再発見」などに限定する

---

## 実装判断メモ

- Premium 判定そのものは `docs/product/billing-paywall.md` を参照する
- Premium UI を追加する場合は、まず本ドキュメントの中心価値に該当するか確認する
- 投稿機能は現時点では Premium 条件と結びつけない

---

## 責務境界

### Product

Productでは以下を管理する。

- Free / Premiumの体験価値と価値観
- 画面別のFree / Premium境界
- 置いてよい表現、置かない表現の原則
- 保存・履歴・比較の意味責務

### Pricing

具体的な料金、請求周期、プラン構成および価格表現の原則は、`docs/product/pricing.md`を正本とする。

### Billing・Paywall

Billing状態の判定原則、Paywall表示の判定原則および利用制限の扱いは、`docs/product/billing-paywall.md`を正本とする。

正確なAPI Endpoint、Field、判定ロジックの実装およびテストケースは、関連するBackend・Frontend実装とテストを正本とする。

### Monetization

Premium提示タイミング、CTA方針および収益導線の設計背景は、`docs/product/monetization-flow-design.md`を参照する。

正確なEvent、Payload、FunnelおよびKPIは、`docs/analytics/`配下の正本文書を参照する。

---

## 責務外

本書では以下を管理しない。

- 具体的な料金、請求周期およびプラン構成
- Billing状態、Paywall表示の判定ロジック
- API Endpoint、レスポンスField
- Event、Payload、Funnel、KPI
- 実装コンポーネント、テストケース

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/pricing.md`
- `docs/product/billing-paywall.md`
- `docs/product/monetization-flow-design.md`
- `docs/product/shrine-detail-layer.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/journey-timeline-design.md`

---

## 更新ルール

- 本書はFree / Premiumの体験価値と画面別の境界を管理する。
- Premiumの中心価値または画面別境界が変更された場合は、本書を更新する。
- 具体的な料金、プラン構成、Billing判定ロジック、Event、Payload、FunnelおよびKPIは本書で重複管理しない。
- 物理実装のみを変更した場合は、本書の体験価値への影響を確認する。
- TODO、PR計画、実装進捗および作業履歴は本書へ記載しない。
