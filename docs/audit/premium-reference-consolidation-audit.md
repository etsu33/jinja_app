# Premium Reference Consolidation Audit

## 目的

Premium関連のReference文書について、現行Active文書との責務重複、独自仕様、将来構想および計測情報を整理し、Reference維持・Audit移動・Deleteの最終分類を確定する。

本監査では、単純なファイル削除を目的としない。

現在も有効な仕様や運用判断をActive文書へ吸収し、現行仕様として使用しない設計履歴・将来構想のみをAuditへ移すことで、Premium関連の正本構造を明確にする。

正確な課金状態、画面表示、API挙動およびAnalytics実装については、関連する実装コードとテストを最終的な正本とする。

---

## 対象文書

### Reference文書

- `docs/monetization-flow-design.md`
- `docs/premium-plan-design.md`
- `docs/premium-retention-strategy.md`

### 比較対象となるActive文書

- `docs/billing-paywall.md`
- `docs/pricing.md`
- `docs/premium-experience.md`

---

## Active文書との責務比較

### Active文書の責務

| 文書 | Status | 主な責務 |
| --- | --- | --- |
| `docs/billing-paywall.md` | Active | 課金状態、Free利用制限、Paywall表示条件、Frontend・Backendの判定責務 |
| `docs/pricing.md` | Active | Free / Premiumの提供価値境界、支払対象、価格表現の原則 |
| `docs/premium-experience.md` | Active | Premium体験原則、画面別の体験差、Premiumとして扱ってよい表現と扱わない表現 |

### Reference文書との関係

| Reference文書 | Active文書との重複 | 独自領域 |
| --- | --- | --- |
| `monetization-flow-design.md` | Premium価値、Free / Premium境界、継続価値の思想が重複する | 提示タイミング、Entry Point、CTA、Subscription Flow、購入後復帰、解約方針、Analytics、Revenue KPI |
| `premium-plan-design.md` | Premium価値、記録の蓄積、過去の自分との比較、体験後に提示する原則が大きく重複する | AI Memory、Journey View、履歴検索、Personal Archive、Statistics、Monthly Review、Annual Journey、家族共有等の将来構想 |
| `premium-retention-strategy.md` | Free / Premium境界、記録蓄積、状態変化の振り返りという価値原則が重複する | 保存・履歴・比較の意味、Retention / Conversion / Engagement KPI、状態変化ログとしての拡張候補 |

---

## 独自情報

## `docs/monetization-flow-design.md`

以下の内容は、現在のActive文書には十分に定義されていない独自情報である。

### Premium提示タイミング

Premiumは、ユーザーが基本体験の価値を得た後に提示する。

提示候補として以下を定義している。

- Reflection保存後
- Timeline閲覧時
- 保存上限到達時
- 月次レビュー表示時
- 再相談時
- 御朱印・写真追加後

### Premiumを強く提示しないタイミング

以下ではPremiumを強く提示しない。

- 初回起動直後
- 相談入力前
- 不安が強い相談直後
- 推薦結果を見る前
- ルート表示前
- 参拝中

これはPremium導線がユーザーの迷いや不安につけ込まないための運用原則である。

### Entry Point

以下の画面ごとにPremium導線の役割を定義している。

- Home
- Concierge Result
- Shrine Detail
- Visit Flow
- Reflection
- Timeline
- My Page

### CTA原則

Premium CTAでは機能名や利用制限ではなく、記録・振り返り・継続文脈の価値を伝える。

避ける表現として、課金の強制、不安を煽る表現、宗教的・運命的な断定を定義している。

### Subscription Flow

以下の基本導線を定義している。

```text
Premium teaser
↓
Premium plan page
↓
Checkout
↓
Payment success
↓
Premium activated
↓
元の体験へ戻る
```

購入後はHomeへ一律に戻さず、課金導線へ入る前の体験文脈へ復帰させる。

### 解約方針

解約導線は分かりやすくし、解約を不当に困難にしない。

解約前には以下の事実情報を表示対象とできる。

- 保存済み記録の扱い
- 停止するPremium機能
- 再開時の復元可否

### AnalyticsとRevenue KPI

以下の計測候補を定義している。

- Premium teaser表示
- CTAクリック
- Plan表示
- Checkout開始
- Checkout成功・中断
- Premium有効化
- Premium機能利用
- 解約導線の利用

また、Revenue KPIとして以下を扱う。

- Premium導線表示率
- CTAクリック率
- Checkout開始率
- Checkout成功率
- 購入転換率
- Premium機能利用率
- 1か月継続率
- 解約率

これらは収益導線の設計・分析に関する独自情報である。

---

## `docs/premium-plan-design.md`

以下の将来構想は、Active文書に完全には含まれていない。

- Reflectionの長文・複数画像・音声・追記・編集履歴
- Timelineの長期的な人生節目表示
- 全相談履歴の保存
- 過去の相談・参拝・Reflectionを利用するAI Memory
- Journey View
- 過去の自分とのComparison
- 神社、相談テーマ、感情、年月等による履歴検索
- Personal Archive
- 参拝回数、相談回数、テーマ推移等のStatistics
- Monthly Review
- Annual Journey
- 家族・パートナーとの記録共有
- 巡礼、地域別Journey、御朱印帳拡張

ただし、これらは現在の実装契約ではなく、将来構想として記述されている。

以下の価値原則は、すでに`docs/pricing.md`および`docs/premium-experience.md`へ吸収済みである。

- Premiumは単なる機能追加ではない
- Free体験を不当に不便にしない
- 記録と振り返りの蓄積を価値とする
- 他人ではなく過去の自分と比較する
- 利用継続によって価値が増える
- 体験途中ではなく価値実感後に提示する

---

## `docs/premium-retention-strategy.md`

以下の内容に独自性がある。

### 保存・履歴・比較の意味

保存は、単なる神社コレクションではなく、その時点のユーザー状態と選択理由を残す記録として扱う。

履歴は、単なる操作ログではなく、ユーザー自身の相談・感情・行動テーマの変化履歴として扱う。

比較は他人との比較ではなく、過去の自分との差分を理解するために利用する。

### Retention KPI

- 7日再訪率
- 30日再訪率
- Thread再開率
- Comparison表示率
- Premium継続率
- 再相談率

### Conversion KPI

- Premium Previewクリック
- Premium Upgrade CVR
- 保存率
- 神社詳細遷移率

### Engagement KPI

- 平均Thread数
- Comparison利用率
- 保存神社再訪率
- 履歴操作率

PVだけではなく、再相談、履歴再訪、比較、保存記録の再利用といった継続行動を主要指標とする。

### 将来拡張

- 月次サマリー
- 状態推移グラフ
- 半年比較
- 神社履歴マップ
- 行動変化Timeline
- 感情テーマ推移
- 継続テーマ分析
- 季節変化との比較

---

## 吸収先

## `docs/premium-experience.md`への吸収

以下の原則を追加する。

### 保存の意味

保存は神社情報を集めるためだけの機能ではなく、その時の相談、状態、推薦理由、参拝および振り返りを後から確認するための体験記録として扱う。

### 履歴の意味

履歴は操作ログの一覧ではなく、相談・参拝・Reflectionを時間軸で接続し、ユーザーが自身の変化を振り返るための体験として扱う。

### 比較の意味

Premiumにおける比較対象は他のユーザーではなく、過去の自分とする。

比較は優劣の評価ではなく、相談テーマ、行動、参拝傾向および振り返りの差分を理解するために使用する。

---

## `docs/monetization-flow-design.md`への吸収

`premium-retention-strategy.md`のKPIを、MonetizationとRetentionを統合した指標として追加する。

### Retention KPI

- 7日再訪率
- 30日再訪率
- Thread再開率
- Comparison表示率
- Premium継続率
- 再相談率

### Engagement KPI

- 平均Thread数
- 保存神社再訪率
- 履歴操作率
- Comparison利用率
- Premium機能利用率

### 計測原則

PVやCheckout成功だけでなく、Premium化後に記録、比較、再相談および履歴再訪が発生しているかを確認する。

---

## `docs/pricing.md`への吸収

価格表現の原則として、以下を明示する。

Premiumの価格は単純な機能数ではなく、相談履歴、記録、比較、Reflectionおよび継続文脈を長期的に利用できる価値に対して説明する。

具体的な料金、請求周期およびプラン構成は、決済実装と運用判断が確定するまで本書では固定しない。

---

## 分類判断

## Reference維持

### `docs/monetization-flow-design.md`

Referenceを維持する。

本書はPremiumの価値原則だけでなく、課金提示タイミング、画面別Entry Point、CTA、Subscription Flow、購入後復帰、解約方針、AnalyticsおよびRevenue KPIを持つ。

これらは`billing-paywall.md`、`pricing.md`、`premium-experience.md`には完全に吸収されていない。

一方、記載されたEvent名、Payload、Checkout経路およびPremium機能の一部は現行実装との一致確認が完了していない。

したがって、現行契約としてActiveにはせず、収益導線の設計補足を管理するReference文書とする。

---

## Audit移動

### `docs/premium-plan-design.md`

`docs/audit/premium-plan-design.md`へ移動する。

現行Premium価値原則は`docs/pricing.md`および`docs/premium-experience.md`へ吸収済みである。

残る独自内容は、AI Memory、Annual Journey、Statistics、履歴検索、家族共有等の将来構想であり、現行仕様ではない。

そのため、root直下のReferenceとしては利用せず、Premium構想時点の設計記録としてAuditへ移動する。

移動後は以下のStatusを付与する。

```markdown
> **Status: Archive**
>
> 本ドキュメントは、Premiumの長期構想、AI Memory、Journey View、比較、統計、月次・年次レビュー等を整理した設計記録である。
>
> 現行のPremium価値境界は`docs/pricing.md`および`docs/premium-experience.md`、課金状態とPaywall判定は`docs/billing-paywall.md`を正本とする。
>
> 本書に記載された将来機能は、実装済みまたは提供確定を意味しない。
```

### `docs/premium-retention-strategy.md`

有効な原則とKPIをActive・Reference文書へ吸収した後、`docs/audit/premium-retention-strategy.md`へ移動する。

Premiumの継続価値に関する基本思想は、`docs/pricing.md`および`docs/premium-experience.md`と重複している。

Retention KPIと保存・履歴・比較の意味は独自性を持つため、移動前に以下へ吸収する。

- 体験原則：`docs/premium-experience.md`
- Retention / Engagement KPI：`docs/monetization-flow-design.md`

移動後は以下のStatusを付与する。

```markdown
> **Status: Archive**
>
> 本ドキュメントは、Premium継続価値、保存・履歴・比較およびRetention KPIを整理した戦略記録である。
>
> 現行のPremium体験境界は`docs/premium-experience.md`、提供価値境界は`docs/pricing.md`、収益導線と継続計測は`docs/monetization-flow-design.md`を参照する。
>
> 本書の有効な原則とKPIは上記文書へ移管済みであり、現行仕様の判断には使用しない。
```

---

## Delete

Delete候補は0件とする。

`premium-plan-design.md`には現行仕様ではないものの、AI Memory、Annual Journey、Statistics、家族共有等の独自構想が残っている。

`premium-retention-strategy.md`にも、Retention KPIや状態変化ログサービスへの将来拡張という監査価値がある。

そのため、いずれも完全削除せず、過去設計としてAuditへ保存する。

---

## 実行順序

1. `docs/premium-experience.md`へ保存・履歴・比較の原則を追加する
2. `docs/monetization-flow-design.md`へRetention / Engagement KPIを追加する
3. 必要に応じて`docs/pricing.md`へ価格説明原則を追加する
4. `docs/premium-plan-design.md`を`docs/audit/premium-plan-design.md`へ移動する
5. `docs/premium-retention-strategy.md`を`docs/audit/premium-retention-strategy.md`へ移動する
6. 移動した2文書へ`Status: Archive`ヘッダーを追加する
7. `docs/README.md`から移動した2文書のReference入口を削除する
8. `docs/audit/root-docs-classification-audit.md`および`docs/audit/archive-final-classification.md`の分類結果を更新する
9. 旧パスへの参照を検索し、新しい参照先へ修正する
10. `git diff --check`を実行する
11. 差分をコミットし、PRを作成する

---

## 完了条件

以下をすべて満たした時点で、本監査を完了とする。

- `docs/monetization-flow-design.md`がReferenceとして残っている
- `docs/premium-plan-design.md`が`docs/audit/`へ移動している
- `docs/premium-retention-strategy.md`が`docs/audit/`へ移動している
- 保存・履歴・比較の有効な体験原則が`docs/premium-experience.md`へ反映されている
- Retention / Engagement KPIが`docs/monetization-flow-design.md`へ反映されている
- 移動した文書の旧パスを現行仕様として参照する文書が残っていない
- `docs/README.md`のPremium Reference入口が現行分類と一致している
- `docs/audit/root-docs-classification-audit.md`と`docs/audit/archive-final-classification.md`の件数・内訳が一致している
- Delete対象が0件であることが監査文書に明記されている
- `git diff --check`がエラーなしで完了している

---

## 結論

Premium関連Reference 3文書のうち、`docs/monetization-flow-design.md`は、課金提示、CTA、Subscription Flow、購入後復帰、解約、AnalyticsおよびRevenue KPIという独自責務を持つためReferenceを維持する。

`docs/premium-plan-design.md`は、現行価値原則がActive文書へ吸収済みであり、残る内容が将来構想を中心とするためAuditへ移動する。

`docs/premium-retention-strategy.md`は、保存・履歴・比較の原則とRetention KPIを対応する現行文書へ吸収した後、戦略履歴としてAuditへ移動する。

Delete対象はない。

この整理により、Premium関連の現行判断は以下へ集約される。

- 課金状態・Paywall：`docs/billing-paywall.md`
- 提供価値・支払対象：`docs/pricing.md`
- 画面別Premium体験：`docs/premium-experience.md`
- 課金提示・CTA・Subscription・計測：`docs/monetization-flow-design.md`

将来構想と過去のRetention戦略は`docs/audit/`へ分離し、現行仕様との混同を防ぐ。
