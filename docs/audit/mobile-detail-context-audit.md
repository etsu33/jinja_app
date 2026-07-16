# Mobile Detail Context Audit

## 結論

現時点のMobile神社詳細画面は、コンシェルジュ結果カードの相談文脈を引き継いでいない。

そのため、詳細画面に reasonFacts UI を追加する前に、詳細遷移時の context 引き継ぎ設計が必要。

## 確認結果

- コンシェルジュ結果カードから詳細への遷移は `/shrines/${card.shrineId}`
- threadId / tid は詳細画面に渡されていない
- reasonFacts / recommendationReasonV4 は詳細画面に直接渡されていない
- 詳細画面は `/shrines/{id}/` から神社単体APIを取得している
- 詳細画面の recommendation_reason_v4 / reason_facts は神社単体API由来

## 判断

現時点では、Mobile神社詳細に reasonFacts UI を追加しない。

理由は、相談文脈つきの根拠ではなく、神社単体情報としての根拠表示になりやすいため。

## 次PR候補

- コンシェルジュ結果カードから詳細画面へ context を渡す設計
- query parameter または storage 経由で reasonFacts / recommendationReasonV4 / threadId を保持
- 詳細画面で「この相談から見た理由」と「神社そのものの説明」を分離表示する
