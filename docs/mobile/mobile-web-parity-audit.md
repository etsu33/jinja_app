> **Status: Archive**
>
> 本ドキュメントは、Mobile版とWeb版の体験差分を調査した時点の監査記録である。
>
> 記載内容は監査時点のスナップショットであり、現行仕様判断や実装状況の判定には使用しない。
>
> 現在のMobile・Web・Backendの仕様は、各実装コード、テスト、および現行ドキュメントを正本とする。
>
> 主な参照先:
>
> - `apps/mobile/`
> - `apps/web/`
> - `backend/temples/`
> - `docs/core/architecture.md`
> - `docs/core/meaning-layer.md`
> - `docs/core/meaning-layer-connection.md`
> - `docs/product/concierge-first-final-spec.md`
> - `docs/product/concierge-modes.md`
> - `docs/product/visit-reflection-flow.md`
> - `docs/product/action_suggestion_v4.md`

# Mobile Web Parity Audit

## 目的

Mobile版とWeb版について、Concierge、Shrine Detail、Visit、Reflectionの体験差分を整理した監査記録である。

本書は、Mobile側で優先すべき体験改善を判断した背景を保存するArchive文書として扱う。

WebとMobileの画面構成を完全に一致させることではなく、以下の体験思想と契約を揃えることを監査の目的とした。

```text
相談
↓
推薦理由
↓
神社詳細
↓
行動提案
↓
参拝
↓
振り返り
```

---

## 監査時点のWeb版

### Concierge

監査時点のWeb版では、以下の要素が確認された。

- 誕生日・ご利益・参拝スタイルを補助条件として扱う
- 条件を変更して再提案できる
- 地図や近隣神社への導線を持つ
- 入力済み相談条件を表示する
- Need Modeを主導線として扱う
- Compat Modeを補助条件として扱う

### Shrine Detail

監査時点のWeb版では、以下の要素が確認された。

- 推薦理由
- Meaning情報
- Action Suggestion
- ご利益などの事実情報
- 表示状態によるSection制御
- 参拝済み記録
- 参拝後の振り返り
- Reflection保存

この一覧は監査時点の状態を示すものであり、現在のWeb実装を保証するものではない。

---

## 監査時点のMobile版

### Concierge

監査時点のMobile版では、以下の表現・導線が確認された。

- 今の相談とのつながり
- 推薦理由
- 相談から提示された神社
- 推薦処理中の世界観表現
- 条件を変更するための補助導線

### 当時の評価

- 文言と世界観はKAMI MUSUBIの体験に沿っていた
- Web版と比較すると、条件追加・再提案・参拝スタイルの構造が限定的だった
- 体験差分の中心はHomeではなく、Shrine Detail以降にあると判断された

---

### Shrine Detail

監査時点のMobile版では、以下の情報が確認された。

- 神社名
- 所在地
- ご利益情報
- 参拝前の補助情報
- 神社説明
- お気に入り
- 経路確認

一方、当時は以下の体験がWeb版と比べて弱い、または未確認とされた。

- 推薦理由の詳細
- 相談内容との接続
- Action Suggestion
- 参拝完了記録
- 参拝後の振り返り
- Reflection保存

これらは監査時点の差分であり、現在の実装状況は各コードとテストを確認する。

---

## 当時確認された主要な差分

### Meaning Layer

Web版では、推薦理由・Meaning・ActionがShrine Detailへ接続していた。

Mobile版では、神社の事実情報と経路確認が中心で、相談から神社を提示した理由を詳細画面で継続して説明する構造が弱いと評価された。

```text
Concierge
↓
Recommendation Reason
↓
Shrine Detail
↓
Meaning
↓
Action Suggestion
```

この接続をMobile側でも維持することが、当時の主要な改善対象として整理された。

---

### Visit / Reflection

Web版では、参拝完了後にReflectionへ接続する導線が確認された。

Mobile版では、監査時点で以下の接続が十分に確認できなかった。

```text
Shrine Detail
↓
Visit Done
↓
Reflection Prompt
↓
Reflection Saved
```

Visit / Reflectionの現在の契約は、以下を参照する。

- `docs/product/visit-reflection-flow.md`
- BackendのVisit / Reflection API
- Mobileの関連画面・Client・Test

---

### 補助条件

Web版では、相談テーマとは別に補助条件を扱う構造が存在した。

主な補助条件は以下だった。

- 誕生日
- ご利益
- 参拝スタイル
- その他の条件

Mobile版では、監査時点でこれらの表示・変更・再提案導線がWeb版より限定的と評価された。

補助条件は相談内容を上書きせず、Need Modeを補完するものとして扱う。

---

## 当時の優先順位

監査時点では、Mobileの改善対象としてShrine Detailを優先する判断が行われた。

### 優先された理由

- Web版との差が最も大きい領域だった
- Conciergeの文言と世界観は一定水準に達していた
- HomeのStyle整理は保守性改善であり、体験差分の中心ではなかった
- 推薦から参拝・振り返りまでの接続が、継続利用価値に直結すると考えられた

### 当時の優先構造

```text
Shrine Detail
↓
Recommendation Reason
↓
Action Suggestion
↓
Visit
↓
Reflection
```

この優先順位は監査時点の判断であり、現在のRoadmapや実装優先順位を示すものではない。

---

## Web / Mobileの責務境界

WebとMobileは、同じBackend契約と体験思想を共有する。

ただし、UI構造やNavigationを完全に同一にする必要はない。

### 共有するもの

- Recommendation契約
- Meaning Layerの責務
- Action Suggestion契約
- Visit / Reflection契約
- Analytics Eventの意味
- 神社情報の事実性
- 心理・宗教・効果を断定しない表現

### Clientごとに分離するもの

- Navigation
- Layout
- Component構造
- Token管理
- Authentication Client
- Device固有の操作
- Loading・Error表現

---

## Parityの定義

本監査では、Parityを画面の完全一致とは定義しない。

Parityは、以下の状態を指す。

- 同じ相談に対して同じ契約を利用する
- 推薦理由の意味がClient間で矛盾しない
- 神社詳細で推薦文脈が失われない
- Action Suggestionの責務が一致する
- Visit / Reflection Eventの意味が一致する
- Access Levelによる表示境界が矛盾しない
- WebとMobileが同じBackendの業務ロジックを利用する

---

## 当時の設計判断

- Mobile版の世界観表現は維持する
- Web版の画面をそのまま複製しない
- Shrine Detailで相談文脈を継続する
- Recommendation Reasonを事実情報と分離して表示する
- Action Suggestionを詳細画面から行動へ接続する
- Visit完了をReflectionの入口として扱う
- 補助条件は主導線にしない
- HomeのStyle整理より、相談から振り返りまでの接続を優先する

---

## 現行仕様との責務境界

### 本書が保持するもの

- Web / Mobile差分を監査した背景
- 当時確認された体験差分
- Shrine Detailを優先した判断理由
- Parityを画面一致ではなく契約・体験整合とした考え方
- RecommendationからReflectionまでの接続を重視した判断

### 本書が扱わないもの

- 現在のMobile実装状況
- 現在のWeb実装状況
- 現在のAPI Response
- 現在のNavigation
- 現在のTab構成
- 現在のAnalytics送信状況
- 現在のVisit / Reflection実装
- 現在のAction Suggestion表示
- 未実装機能の作業指示
- 実装計画
- PR候補
- 開発タスク

---

## 関連ドキュメント

### 現行の体験・責務

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/action_suggestion_v4.md`

### 現行実装

- `apps/mobile/`
- `apps/web/`
- `backend/temples/`

---

## 更新ルール

- 本書はMobile / Web Parity監査時点の記録として保持する
- 現行仕様や実装変更に合わせて更新しない
- 当時の監査内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装優先順位、未実装機能一覧、作業進捗は記載しない
