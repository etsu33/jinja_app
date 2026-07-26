> **Status: Active / Contract**

# Mobile Reflection保存後の再相談導線イベント契約

神社詳細画面(`apps/mobile/app/shrines/[id].tsx`)でReflection保存が成功した直後に表示される、任意の再相談CTA(「この体験をもとに、もう一度相談する」)のEvent契約を管理する。実装は`apps/mobile/lib/visitReflectionAnalytics.ts`を正本とし、送信はMobile既存の`track()`パイプライン(`apps/mobile/lib/analytics.ts`)へ委譲する。

体験責務(CTAを表示する条件、自動遷移しない方針、Conciergeへ本文を引き継がない方針)は`docs/product/visit-reflection-flow.md`「次回相談との接続」節を正本とする。本書はEvent名・Payload・禁止属性のみを規定する。

| Event | 発火条件 | Payload | 重複の単位 |
| --- | --- | --- | --- |
| `reflection_to_consultation_click` | Reflection保存成功後に表示されるCTA「この体験をもとに、もう一度相談する」を押した操作 | `source: "shrine_detail"`, `platform: "mobile"`, `shrineId`, `threadId`(取得できた場合のみ), `historyTheme`(取得できた場合のみ), `reflectionSaved: true` | クリックごと |

## 表示Eventを追加しない理由

CTAの表示条件は`reflectionSaved`(Reflection保存成功)のみであり、これは既存の`reflection_saved`(`docs/analytics/reflection-funnel-dashboard.md`が定義するFunnelの一部)と1:1で連動する。CTA表示だけを対象にした新規Eventは`reflection_saved`と完全に重複するため追加しない。CTAが実際にクリックされたかどうかのみを本書のEventで計測する。

## Conciergeへ渡す情報

CTA押下時、`router.push("/concierge")`をparamsなしで呼び出し、Conciergeを通常状態(未入力)で開く。Reflection本文・相談文・住所・緯度経度・誕生日等の自由入力・個人情報はURL・Payloadいずれにも含めない。

Concierge側の`theme`/`q`クエリは`docs/product/concierge-first-final-spec.md`が「相談本文の自然文として扱う」と定義しており、ここへReflection由来の文字列を渡すと自由入力本文をURLへ含めることになるため使用しない。`threadId`等の安全な参照契約は今回時点でConcierge画面側に存在しないため、本文・スレッドいずれも引き継がない。

## 禁止属性

次の値はEvent名を問わず送信しない。

- Reflection本文(`answer`)、相談文、自由入力条件
- 住所、駅名、都道府県名、緯度・経度
- 誕生日、参拝予定日
- mood_before / mood_after の自由記述値
- ユーザー名、メールアドレス、トークン、Cookie
- APIレスポンス全文、推薦理由本文、`reasonFacts`全文

`shrineId`・`source`・`platform`・`threadId`・`historyTheme`・`reflectionSaved`のみを許可する。

## Payload型

- primitive型(string/number/boolean)のみを許可する
- nested object・配列を送らない
- `null`/`undefined`は送信前に除外する(`apps/mobile/lib/analytics.ts`の`serializeAnalyticsPayload`が構造的に担う)

## 重複防止

- CTAは`reflectionSaved === true`の間のみ描画され、保存前・保存中・保存失敗時には描画されない
- CTA押下時に短時間の重複防止ガード(`consultationNavigatingRef`)を設け、連打による多重発火・多重遷移を防ぐ
- `reflection_saved`(保存成功)と`reflection_to_consultation_click`(CTAクリック)は別Eventであり、混同しない

## 変更ルール

- Event名またはPayloadを変更する場合は、`apps/mobile/lib/visitReflectionAnalytics.ts`と本書を同じPRで更新する
- CTAの表示条件・配置画面が変更された場合は、`docs/product/visit-reflection-flow.md`との整合を確認したうえで本書を更新する
- 本書はMobile Reflection保存後の再相談導線のEvent契約のみを管理する。Visit/Reflection保存自体のEvent契約(`visit_done`/`reflection_prompt_view`/`reflection_saved`)は本書で重複管理しない
