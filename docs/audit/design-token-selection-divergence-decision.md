> **Status: Reference**
>
> 本文書は、`docs/audit/design-token-stage3-residual-contract.md`のAction Border項目を再監査した結果、対象instanceの多くが実際にはAction responsibilityではなく、`docs/audit/design-token-stage3-neutral-semantic-decision.md`が既に指摘していたSelection divergence（blue系/emerald系の2系統分裂）の未解決事例であることが判明したため、両者を分離して記録する。
>
> 本文書は決定記録ではない。Genuine Action BorderとConciergeFilterPanel.tsxの再分類のみ、調査事実に基づく確定的な分類として記録し、Selection divergence自体の解決方針（値統一・variant化・現状維持のいずれか）は判断材料の提示に留め、確定しない。

# Design Token — Action Border / Selection Divergence 再分類

## 背景

`docs/audit/design-token-stage3-residual-contract.md`は`border-emerald-300`（`ConciergeEntryCard.tsx`）・`border-emerald-600`（`ConciergeFilterPanel.tsx`）を「Action Border」という1カテゴリとして扱っていた。再監査の結果、この分類は不正確であることが判明した。

## 調査事実

### Instance一覧

| 箇所 | 要素 | Border（state別） | Background | Text | 責務 |
|---|---|---|---|---|---|
| `ConciergeEntryCard.tsx:174` | 送信ボタン（常時同一スタイル、on/off状態なし） | `emerald-300`（固定） | `emerald-50/50` | `emerald-800` | **Action**（CTA） |
| `ConciergeEntryCard.tsx:154-156` | 相談テーマchip（`isSelected`で切替） | `emerald-200/60`（選択時）/`stone-200/35`（非選択） | `emerald-50/40`/`stone-50/25` | `emerald-700`/muted token | Selection |
| `ConciergeFilterPanel.tsx:181,214` | タグchip（`on`で切替、multi-select、×2箇所同一実装） | `emerald-600`（on）/なし（off） | `emerald-50`/`white` | 継承 | Selection |
| `ConciergeSectionsRenderer.tsx:613` | プリセットchip（`active`で切替）**既にToken化済み** | `action-primary`（on、bgと同値）/`border-default`相当 | `action-primary`/`surface-default` | `action-primary-text`/`text-secondary` | Action（塗りと縁が同一要素・同一値のため妥当な適用） |
| `OriginSelector.tsx:99` | 出発地点オプション（`selected`で切替、single-select） | `emerald-500`（選択時）/`stone-300`（非選択） | `emerald-50`/`white` | `emerald-900`/`stone-700` | Selection |
| `ShrineSaveButton.tsx:90,97` | 保存/お気に入りボタン（`fav`で切替、永続状態） | `emerald-200`/`emerald-300`（fav、variant別）/token化済み（unfav） | `emerald-50`/`surface-default` | `emerald-700`/muted・primary token | **要検討**（下記参照） |

### `docs/audit/design-token-stage3-neutral-semantic-decision.md`との連続性

同文書は次の通り既に指摘していた（37行目付近の引用）:

> Web内クロスチェック: 同じconcierge feature内の`OriginSelector.tsx`は、同じ「選択中」状態を既にemerald（`border-emerald-500 bg-emerald-50`、既存のAction Tokenと一致）で実装している。`ThreadListItem.tsx`のみblueを使用しており、Web内で選択状態の色表現が2系統に分裂していた

本文書はこの指摘を継承し、`OriginSelector.tsx`以外にも同じ「selected状態をemeraldで表現する」実装が`ConciergeFilterPanel.tsx`（タグchip）・`ConciergeEntryCard.tsx`（相談テーマchip）に存在することを新たに確認した。これは新しい問題ではなく、PR-B時点で既に存在していたSelection divergenceの、より広い範囲での再発見である。

### 未解決の論点: `ShrineSaveButton.tsx`のfavorite状態は同一責務か

上記4箇所（`OriginSelector.tsx`・`ConciergeFilterPanel.tsx`・`ConciergeEntryCard.tsx`）は、いずれも「複数の選択肢の中から現在どれが選ばれているか」を表す、対話中の一時的な状態（画面遷移でリセットされる）である。

一方`ShrineSaveButton.tsx`の`fav`状態は、サーバー側に永続化される「保存済みかどうか」というステータスであり、選択肢の中からの選択ではない。パレット（emerald）が一致することを理由に同一責務として扱ってよいかは未検証であり、本文書はこれを「Selection Emerald」クラスタへ機械的に含めず、別途確認が必要な項目として記録する。

## 分類

### Genuine Action Border

対象: `ConciergeEntryCard.tsx:174`のみ。

**判定: `KEEP_LITERAL_FOR_NOW`**

根拠: 1 instance・1ファイルであり、既存の`Premium subtle ring`（1箇所→`KEEP_LITERAL_FOR_NOW`採用済み）と同水準の再利用根拠の弱さ。Focus（`border-focus`=emerald-300、値は数値上一致するが本箇所はfocus用途ではない）およびSelectionとは責務が異なることを確認済み。`action-primary`をborder用途へ機械的に流用しない方針を維持する。

### Selection Emerald（`SELECTION_DIVERGENCE`）

対象: `ConciergeEntryCard.tsx`相談テーマchip、`ConciergeFilterPanel.tsx`タグchip（×2）、`OriginSelector.tsx`。`ShrineSaveButton.tsx`は上記「未解決の論点」の通り、暫定的に本クラスタの参考事例として記録するに留め、正式に同一クラスタへ含めることは確定しない。

**判定: `SELECTION_DIVERGENCE`**（PR-B時点の指摘の延長、新規カテゴリではない）

解決方針（値統一/variant化/現状維持のいずれか）は本文書では確定しない。「同一Semantic名・Platform別実値として扱えるか」という枠組みについては、`docs/design/design-token.md`の`Platform Theme`層が現状Web/Mobile差のみを指す概念であり（`docs/audit/design-token-stage3-residual-contract.md`のDark Surface候補B検討時と同じ制約）、Web内のblue/emerald差をPlatform Theme差として扱うには、この定義自体の拡張が別途必要になる。

## `ConciergeFilterPanel.tsx`の再分類

`docs/audit/design-token-stage3-residual-contract.md`のPhase 7は`ConciergeFilterPanel.tsx`の`border-emerald-600`/`bg-emerald-50`を`ACCIDENTAL_REMAINDER`（取りこぼし）として分類していた。

**再分類: `ACCIDENTAL_REMAINDER` → `KNOWN_SELECTION_DIVERGENCE`**

根拠: 当該箇所は「同一要素内でborderとbgの値が一致しない」という表面的な特徴からAction Border候補として扱われていたが、実体は`on`状態によるタグchipの選択表現であり、`OriginSelector.tsx`と同一パターンである。「意図せず見落とされていた箇所」ではなく、「PR-B時点で既に存在していたSelection divergenceの、当時未発見だった追加インスタンス」として扱うのが正確である。

## Stage 3 Exit Contractへの影響

`docs/audit/design-token-stage3-residual-contract.md`が記録した候補A（`STAGE3_DONE_WITH_DOCUMENTED_LITERAL_EXCEPTIONS`）の前提条件チェックのうち、「accidental remainder 0」は本再分類により満たされる（`ConciergeFilterPanel.tsx`の残存インスタンスは「意図せぬ取りこぼし」ではなく「既知のSelection divergenceの一部」として説明可能になったため）。

ただし、これのみで候補Aが選択可能になるわけではない。同文書が既に指摘した通り、候補Aの採用には`docs/design/design-token.md`のDONE定義そのものの改定という別のGovernance判断が必要であり、本文書はこれを変更しない。また、Selection divergence自体は未解決のまま残るため、Stage 3を`STAGE3_DONE_WITH_DOCUMENTED_LITERAL_EXCEPTIONS`へ引き上げるかどうかは、Selection divergenceの扱い方（今解決するか、Stage 4以降の横断課題として送るか）が定まってから改めて判断する。

現時点でStage 3は`STAGE3_PARTIALLY_DONE`のまま据え置く。

## Stage 3 / Stage 4 境界

`ShrineSaveButton.tsx`はShrine Detail（Stage 4スコープ）のコンポーネントである。Selection divergenceはStage 3固有の問題ではなく、Web横断のDesign Token課題であることを確認した。Stage 3の範囲内でemerald selectionの解決（値統一・variant化等）を行わない。

## 関連文書

- `docs/design/design-token.md`（正本）
- `docs/audit/design-token-stage3-neutral-semantic-decision.md`（Selection divergenceの初出）
- `docs/audit/design-token-stage3-residual-contract.md`（Action Border/Accidental Remainderの旧分類）

## 品質確認

- [x] Genuine Action BorderとConciergeFilterPanel.tsxの再分類は調査事実に基づく確定的な記録である
- [x] Selection divergence自体の解決方針（値統一/variant化/現状維持）は確定していない
- [x] `ShrineSaveButton.tsx`のfavorite状態をSelection Emeraldクラスタへ機械的に含めていない
- [x] PR-Bの既存指摘と矛盾しない
- [x] Stage 4のScope（`ShrineSaveButton.tsx`の実装変更）を先取りしていない
- [x] Component・`tokens.css`の変更は行っていない
- [x] `git diff --check`
