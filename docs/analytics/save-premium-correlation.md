> **Status: Active**
>
> 本ドキュメントは、保存行動とPremium転換に関するEvent間の相関分析の読み方を管理する正本文書である。
>
> 正確なEvent名、PayloadおよびPropertyは、`docs/analytics/monetization-funnel.md`および関連するFrontend実装コードとテストを最終的な正本とする。

# Save / Premium Correlation

## 目的

保存行動（Save）が、神社詳細・経路確認への行動、およびPremium転換（Preview → Checkout → Premium有効化）とどう結びついているかを分析するための、相関の読み方を定義する。

本書は、Event名やPayloadを新たに定義しない。Event間の関係を分析する際の単位、欠損時の扱いおよび相関と因果を混同しない原則を管理する。

---

## 対象とするEvent群

以下のEvent群を対象とする。正確なEvent名、PayloadおよびPropertyは、各正本を参照する。

### 保存・詳細・経路確認

保存意図の表明、保存の実行、神社詳細の閲覧および経路確認は、それぞれ独立したEventとして送信される。

正確なEvent名およびPayloadは、関連するFrontend実装コードとテストを参照する。

### Premium Preview・Checkout・Premium有効化

Premium導線への関心表明から決済開始、決済成功、Premium有効化までの一連の流れを対象とする。

正確なEvent名は`docs/analytics/monetization-funnel.md`を参照する。

---

## 保存から詳細・経路確認への行動接続

保存は、それ単独で完結する行動ではなく、神社を後から見返す、または経路確認へ進むための起点として扱う。

分析では、以下の順序を前提とする。

```text
保存意図の表明
↓
保存の実行
↓
神社詳細の閲覧
↓
経路確認
```

ただし、ユーザーは必ずしもこの順序どおりに行動しない。保存せずに経路確認へ進む、または詳細だけを確認して離脱するケースも正常な行動として扱う。

保存行動には、意図の表明（保存したいという反応）と実行（保存が確定した反応）の2段階があり、この2つを混同しない。

---

## Premium PreviewからCheckout・Premium有効化への接続

Premium導線への関心は、以下の順序で深まっていくと仮定して分析する。

```text
Premium Previewへの反応
↓
Checkoutの開始
↓
Premiumの有効化
```

この順序は仮説であり、確定した転換経路として扱わない。Premium Previewを経由せずCheckoutへ進むケースも存在しうる。

Web / Mobileでは、この経路に対応するEvent名およびPayload形状が一致していない箇所がある。正確な差異は`docs/analytics/monetization-funnel.md`を参照する。

Mobileは、Premiumドメイン以外のEvent送信が確認されていない。そのため、保存・詳細・経路確認とPremium転換をまたぐ相関分析は、現時点ではWebのみを対象として成立する。

---

## Event間の相関を読む際の分析単位

相関を読む際は、以下の優先順位で分析単位を選ぶ。

1. 同一セッション内の順序
2. 安定したユーザー識別子が取得できる場合の、一定期間内（例: 7日以内）の順序

初期の分析では、同一セッション内の順序のみを対象とする。

匿名利用からログイン・会員登録を経て行動が継続する場合、セッションをまたいだ同一ユーザーの識別は保証されない。ユーザー単位の分析へ拡張する場合は、識別が継続している前提が成立しているかを個別に確認する。

---

## Event欠損時の扱い

Analytics Eventは、送信失敗、通信エラーまたは計測未実装により欠損することがある。

Eventが存在しないことを、その行動が発生しなかったことの証拠として扱わない。

保存・詳細・経路確認の一部は、Analytics Eventとは別に、Backend側にも行動の記録が残る。Eventが欠損している場合、Backend記録の有無をあわせて確認できないか検討する。

Premium・Checkoutの経路には、Analytics Event以外に行動そのものを記録する仕組みがない。Eventが欠損した場合、そのステップは確認不能として扱う。

---

## 同一ユーザー・同一神社・同一相談文脈を関連付ける際の注意

Event同士を関連付ける際は、以下の識別子を手掛かりとする。

- 神社を識別する項目
- 相談の文脈を識別する項目
- セッションを識別する項目

これらの識別子は、Eventの種類によって送信されている場合と送信されていない場合がある。識別子が欠けているEventを、関連するEventと無理に紐付けない。

同一の神社であっても、異なる相談文脈または異なるセッションから発生した行動は、同一の意思決定として扱わない。

---

## 相関と因果を混同しない原則

あるEventの後に別のEventが多く発生していることは、前者が後者の原因であることを意味しない。

例えば、Premium Previewを見たユーザーがCheckoutへ進む割合が高いことは、Premium Previewの表示がCheckoutを引き起こしたことを証明しない。両者に共通する別の要因（もともとPremiumへの関心が高いユーザー層である等）が影響している可能性を排除できない。

相関分析の結果は、施策の効果を確定させる根拠としてではなく、次に検証すべき仮説を見つけるための手がかりとして扱う。

---

## 責務外

本書では以下を管理しない。

- 正確なEvent名、Payload、Property
- KPIの具体値、成功基準
- PostHog Dashboardの操作手順
- API Endpoint、Model、Serializer、Component名
- 実装コード

---

## 関連ドキュメント

- `docs/analytics/README.md`
- `docs/analytics/monetization-funnel.md`
- `docs/analytics/analytics-payload-audit.md`
- `docs/analytics/premium-analytics-dashboard.md`
- `docs/product/premium-experience.md`

---

## 更新ルール

- 本書は保存行動とPremium転換に関するEvent間の相関分析の読み方のみを管理する。
- 分析単位、欠損時の扱いまたは相関と因果を混同しない原則が変更された場合は、本書を更新する。
- 正確なEvent名、Payload、Property、KPIの具体値は本書で重複管理しない。
- Web / Mobileの計測範囲が変化した場合は、対象とするEvent群の記載を見直す。
- TODO、PR計画、実装進捗および作業履歴は本書へ記載しない。
