> **Status: Active**
>
> 本文書はMobile共通Button（`apps/mobile/components/ui/Button.tsx`）への置換候補を洗い出す監査記録である。本PRではコード変更を行わず、調査・分類・次PR分割案の提示のみを行う。

# Mobile CTA共通Button適用候補監査

## 1. 監査目的

`apps/mobile`配下に存在するCTA・Pressableを全域監査し、既存の共通Button（`apps/mobile/components/ui/Button.tsx`）へ安全に置換できる対象を確定する。実装は行わず、次PRの分割設計に必要な事実を記録する。

## 2. 対象範囲

- `apps/mobile/app/**`
- `apps/mobile/components/**`

検索コマンド: `grep -rn "Pressable\|TouchableOpacity\|TouchableHighlight\|onPress=\|disabled=\|loading\|ActivityIndicator\|accessibilityRole=\"button\"" app components --include="*.tsx"`

`TouchableOpacity` / `TouchableHighlight`はアプリ内で1件も使用されておらず、全てのCTAが`Pressable`（または共通`Button`）で実装されている。

## 3. 現行Button API

`apps/mobile/components/ui/Button.tsx`（2026-07時点、`fa334593`/`abb643f6`/`6eb45be9`/`0145e81b`の各PRで整備済み）

```ts
type Props = {
  title: string;
  variant?: "primary" | "accent" | "neutral";
  style?: ViewStyle;
  onPress?: () => void;
  disabled?: boolean;
  loading?: boolean;
  accessibilityLabel?: string;
};
```

- 高さ: `ctaSizes.mediumHeight`（48）固定
- radius: `semanticRadius.control`（16）固定
- variant別配色: primary=`action.primary`系、accent=`premium.accent`系、neutral=`surface.default`系（いずれもSemantic Token参照）
- `loading`時は`ActivityIndicator`が`title`を置き換える
- `disabled`/`loading`時は`opacity: 0.5`、`pressed`時は`opacity: 0.85`
- `accessibilityRole="button"`・`accessibilityState={{ disabled, busy }}`を内蔵
- outline/ghost variant、compact/small size、icon付きレイアウト、3値以上の状態（visited/saved等）には非対応

**既に適用済みの画面**:
- `apps/mobile/app/login.tsx`（`variant="primary"` `disabled` `loading` `accessibilityLabel`を接続、PR #2099）
- `apps/mobile/app/birthday/index.tsx`（`variant="primary"`、PR #2102）

## 4. CTA一覧

凡例: 現行Component＝実装済みStyleSheetキー名。寸法/色は実測値、括弧内はSemantic Token比較（一致/不一致）。

### 4.1 適用済み（対象外・完了）

| ファイル | CTA文言 | 処理名 | 現行Component | 備考 |
|---|---|---|---|---|
| `app/login.tsx` | ログインする | JWT取得・トークン保存 | `Button` | 適用済み |
| `app/birthday/index.tsx` | 保存する | AsyncStorage保存 | `Button` | 適用済み |

### 4.2 A：単純置換可能

| # | ファイル | Component名/CTA文言 | 処理名 | 分類 | loading | disabled | pressed | a11y | 高さ | radius | bg | text | shadow | icon | 複合layout | 置換可否 | 必要variant | 必要props | 見た目差分 | 業務リスク | 推奨PR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | `components/common/AuthPrompt.tsx` `loginButton` | ログインする | `router.push("/login")` | primary/navigation | 無 | 無 | 無 | `accessibilityRole="button"`のみ | minHeight 48 | `radius.md`=16(**一致**) | `theme.gold`(**一致**=action.primary) | `theme.background`(**一致**=action.primaryText) | 無 | 無 | 無 | 可 | primary | title, onPress, accessibilityLabel | fontSize 15→16(+1px、許容範囲) | 低（画面遷移のみ） | PR候補1 |
| A2 | `app/concierge/index.tsx` `ctaPrimary`(ResultCard) | この神社を詳しく見る | `onDetail`（詳細画面遷移） | primary/navigation | 無 | 無 | 無 | 無 | 50(vs48, +2px) | 16(**一致**) | `theme.gold`(**一致**) | `theme.background`(**一致**) | `shadowColor: theme.gold` + `shadows.goldCta`（`semanticShadow.brand`と値は一致だが`shadowColor`追加分は共通Buttonに無し） | 無 | 無 | 可 | primary | title, onPress | 高さ+2px、影に金色着色が追加でBrand感が強い（共通Buttonは無色影） | 低 | PR候補5（Concierge統一と合わせる） |
| A3 | `app/goshuin/upload.tsx` `saveBtn` | この御朱印を保存する | 画像+メタデータ保存API | primary | 無（保存中の視覚表現なし） | 無 | 有(`pressed`で共通styles.pressed) | 無 | 52(vs48, +4px) | 16(**一致**) | `theme.gold`(**一致**) | `theme.background`(**一致**) | `shadowColor: theme.gold`+goldCta相当（A2と同様の差分） | 無 | 無 | 可 | primary | title, onPress | 高さ+4px、影の金色着色 | 中（保存中に連打できてしまう可能性。移行時に`loading`接続を検討） | PR候補1（見た目のみ） |
| A4 | `app/goshuin/index.tsx` `emptyCta` | 最初の記録を追加する | `/goshuin/upload`へ遷移 | primary/navigation | 無 | 無 | 無 | 無 | 50(vs48, +2px) | 16(**一致**) | `theme.gold`(**一致**) | `theme.background`(**一致**) | 無 | 無 | 無 | 可 | primary | title, onPress | 高さ+2pxのみ | 低 | PR候補1 |
| A5 | `app/index.tsx`（Home） `primaryCta` | この相談からご縁を見る | `openConcierge`（Concierge画面へ遷移） | primary/navigation | 無 | 無 | 無 | 無 | 54(vs48, +6px) | 14(vs16, -2px) | `theme.gold`(**一致**) | `theme.background`(**一致**) | `shadowColor: theme.gold`+goldCta相当 | 無 | 無 | 可 | primary | title, onPress | 高さ+6px／radius-2px／影の金色着色。**アプリ最重要CTAのため見た目差分の許容判断は要レビュー** | 中（アプリの主要導線、見た目変化の影響範囲が最大） | PR候補1（単独PRでの先行確認を推奨） |

### 4.3 B：状態API接続で置換可能

| # | ファイル | Component名/CTA文言 | 処理名 | 分類 | loading | disabled | pressed | a11y | 高さ | radius | bg | text | shadow | icon | 複合layout | 置換可否 | 必要variant | 必要props | 見た目差分 | 業務リスク | 推奨PR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | `app/premium/index.tsx` `checkoutButton` | Premiumに登録する | Stripe Checkoutセッション開始 | primary | 有（`ActivityIndicator color={theme.background}`、共通Buttonと同一パターン） | 有(`checkoutLoading`) | 有(`checkoutButtonPressed` opacity 0.85=共通Buttonと**完全一致**) | `accessibilityRole="button"` | minHeight 48(**一致**) | `radius.md`=16(**一致**) | `theme.gold`(**一致**) | `theme.background`(**一致**) | 無 | 無 | 無 | 可 | primary | title, onPress, disabled, loading, accessibilityLabel | fontSize 15→16(+1px)、disabled opacity 0.6→0.5(僅差) | 低（`disabled`/`loading`とも既存ロジックのままAPI直結可能） | PR候補2（最優先） |
| B2 | `app/concierge/index.tsx` `resuggestButton` | この条件で再提案する | 条件変更→再検索API呼び出し | primary | 有だが**ボタン内蔵ではなく別行のテキスト**（「新しい相談内容から、ご縁を結び直しています…」） | 有(`loading \|\| (!consultationText && !hasAnyCondition)`) | 無 | 無 | 46(vs48, -2px) | 15(vs16, -1px) | `theme.gold`(**一致**) | `theme.background`(**一致**) | 無 | 無 | 無 | 可（ただし`loading`接続は要検討） | primary | title, onPress, disabled | 高さ-2px／radius-1px。**`loading`をButtonへ渡すと現在の説明テキスト行が失われる**ため、`disabled`のみ接続し`loading`表示は現状の別行テキストを維持する設計が安全 | 中（loading UXの意図的な非対称。テキスト付き説明を削らない実装注意が必要） | PR候補2 |

### 4.4 C：Button API拡張が必要

| # | ファイル | Component名/CTA文言 | 処理名 | 分類 | loading | disabled | pressed | a11y | 高さ | radius | bg | text | shadow | icon | 複合layout | 置換可否 | 必要variant | 必要props | 見た目差分 | 業務リスク | 推奨PR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | `app/premium/index.tsx` `retryButton` | 再試行 | ステータス再取得API | secondary/outline | 無 | 無 | 無 | `accessibilityRole="button"` | 自動（padding基準、~32px相当） | `radius.pill`=999(pill) | 無（枠線のみ、透過） | `theme.gold` | 無 | 無 | 無 | 不可（現状） | outline小型 | outline variant, small size | 現行はpill形状・自動高さ。共通Buttonは固定48高の塗りvariantのみで表現不可 | 低 | PR候補3（API拡張後） |
| C2 | `app/shrines/[id].tsx` `ctaPrimary` | 参拝したことを記録する／参拝済みとして記録しました | 参拝記録API | primary→success(3値目) | 無 | 無（visited状態で色が変わるのみ） | 無 | 無 | 48(**一致**) | `ctaSizes.mediumRadius`(**一致**) | `theme.gold`→visited時`theme.borderGoldDark`+枠線 | `theme.background`(**一致**) | 無 | 無 | 無 | 不可（現状） | primary＋"done/success"状態 | success/completed variant | visited時に第3の配色（塗り替え+枠線追加）へ変化。現行Buttonの`primary/accent/neutral`いずれにも該当しない | 中（状態遷移の見た目がビジネス上重要な「達成感」表現） | PR候補3 |
| C3 | `app/shrines/[id].tsx` `ctaSecondary` | 地図で経路を確認する | Google Maps/Apple Maps起動 | secondary/outline | 無 | 無 | 無 | 無 | 48(**一致**) | `ctaSizes.mediumRadius`(**一致**) | 透過（枠線のみ） | `theme.gold` | 無 | 無 | 無 | 不可（現状） | outline | outline variant | 塗りvariant前提の共通Buttonでは表現不可 | 低 | PR候補3 |
| C4 | `app/shrines/[id].tsx` `reflectionButton` | 振り返りを保存する／保存中…／振り返りを保存しました | 振り返り保存API | secondary/outline→success | 有（テキスト差し替えのみ、`ActivityIndicator`無し） | 有(`!reflectionAnswer.trim() \|\| reflectionSaving`、opacity 0.5=共通Buttonと**一致**) | 無 | 無 | 48(**一致**) | `ctaSizes.mediumRadius`(**一致**) | 透過→saved時`theme.borderGoldDark` | `theme.gold` | 無 | 無 | 無 | 不可（現状） | outline＋success状態 | outline variant, success state, text-swap loading（ActivityIndicator無し） | outline基調で共通Buttonの塗りvariantと非対応。loading表現もActivityIndicatorではなく文言差し替え | 中 | PR候補3 |
| C5 | `app/concierge/index.tsx` `conditionEditButton` | 条件を変える | 条件編集シート表示 | tertiary/outline | 無 | 無 | 無 | 無 | 自動（padding基準、~28px相当） | 999(pill) | 透過 | `theme.gold` | 無 | 無 | 無 | 不可（現状） | outline小型pill | outline variant, small/pill size | 固定48高の共通Buttonでは表現不可 | 低 | PR候補3 |
| C6 | `app/concierge/index.tsx` `sendBtn` | （アイコンのみ「→」） | 追加相談送信API | primary/icon | 無 | 有(`loading \|\| (!input.trim() && !hasAnyCondition)`) | 無 | 無 | 50×50正方形 | 25(circle) | `theme.gold`(**一致**) | `theme.background`(**一致**) | 無 | 有（絵文字的テキスト「→」） | 無 | 不可（現状） | primary＋icon compact | icon API, compact/square size | 正方形・アイコンのみレイアウトは共通Button未対応 | 中（チャット入力の主送信導線） | PR候補3 |
| C7 | `app/goshuin/upload.tsx` `pickBtn`（カメラ／アルバム、2箇所同一パターン） | カメラ／アルバム | 画像ピッカー起動 | neutral/icon+label | 無 | 無 | 有(`pressed`共通styles) | 無 | 自動（flex:1、2カラム） | 20(vs16, +4px) | `theme.surface`（Semantic Token不一致） | `theme.text`（Semantic Token不一致） | 無 | 有（絵文字的テキスト「□」+ラベル2段組） | 有（アイコン+テキスト縦積み） | 不可（現状） | neutral＋icon | icon API, 複合ラベル(2行) | 2カラムアイコン付きレイアウトは共通Button未対応 | 低 | PR候補3 |
| C8 | `app/goshuin/index.tsx` `addButton` | ＋ 記録する | `/goshuin/upload`へ遷移 | primary/navigation小型 | 無 | 無 | 無 | 無 | 自動（padding基準、~32px相当） | 999(pill) | `theme.borderGoldDark`（Semantic Token不一致） | `theme.gold` | 無 | 有（「＋」プレフィックス、テキスト内埋め込み） | 無 | 不可（現状） | primary小型pill | small/pill size | 固定48高・fill色も`action.primary`と異なる専用トーン | 低 | PR候補3 |
| C9 | `app/index.tsx`（Home） `sendButton` | （アイコンのみ「↑」） | Concierge画面へ遷移（送信相当） | primary/icon | 無 | 無 | 無 | 無 | 54×54正方形 | 27(circle) | `theme.gold`(**一致**) | `theme.background`(**一致**) | 無 | 有（絵文字的テキスト「↑」） | 無 | 不可（現状） | primary＋icon compact | icon API, compact/square size | C6と同一課題（アプリ最上流の送信導線） | 中 | PR候補3 |

### 4.5 D：対象外

| カテゴリ | 件数 | 代表ファイル |
|---|---|---|
| 戻る | 12 | consultation-history, favorites, journey, recently-viewed, reflection-history, concierge, premium, profile, shrines/[id], search, goshuin/index, goshuin/upload（各画面で個別実装、共有Componentなし） |
| 閉じる | 2 | `AuthPrompt.tsx` closeButton（「あとで」）、`reflection-history/index.tsx` modalCloseButton |
| モーダル背景 | 1 | `AuthPrompt.tsx` backdrop |
| カード全体のタップ／ナビゲーション／リスト行 | 8 | `favorites`, `ranking`, `recently-viewed`, `records`（RecordCard）, `reflection-history`, `search`（検索結果card。**「検索結果CTA」は独立したボタンではなく、結果行カード全体のタップで遷移する設計**）, `mypage`（MyPageCard。右側の「確認」「設定」等はカード内の装飾Textでボタンではない）, `concierge`（行動提案プレビューカード） |
| トグル | 5 | `index.tsx`（テーマ選択チップ／条件追加アコーディオン）, `ranking`（お気に入りのみ表示）, `ConditionFieldsCard.tsx`（訪問スタイル／ご利益タグ選択、各2箇所） |
| お気に入りアイコン | 3 | `shrines/[id].tsx` favBtn, `favorites/index.tsx` 解除ボタン, `ranking/index.tsx` FavoriteHeartButton |

合計 **31件**（同一画面内で繰り返しレンダリングされるリスト行等は1パターンとして計上）。

## 5. A/B/C/D分類件数

| 分類 | 件数 |
|---|---|
| 適用済み（参考） | 2 |
| A：単純置換可能 | 5 |
| B：状態API接続で置換可能 | 2 |
| C：Button API拡張が必要 | 9（コード上のPressable箇所としては`pickBtn`×2を含め10） |
| D：対象外 | 31 |
| **CTA分析対象合計（適用済み含む）** | **50** |

## 6. 適用対象（A+B、計7件）

`AuthPrompt.loginButton` / `concierge ctaPrimary(ResultCard)` / `goshuin/upload saveBtn` / `goshuin/index emptyCta` / `index.tsx primaryCta` / `premium checkoutButton` / `concierge resuggestButton`

## 7. 非適用対象（D、計31件）

セクション4.5の表を参照。理由は全て「対象外候補」定義（戻る／閉じる／モーダル背景／カード全体タップ／トグル／アイコンのみの操作）に合致する。

## 8. 見た目差分まとめ

- **高さ**: 共通Buttonは48固定。実測は46〜54の範囲でばらつく（多くは+2〜+6px、`resuggestButton`のみ-2px）。数px単位の差分はA/B分類では許容範囲と判断したが、`index.tsx primaryCta`（+6px、アプリ最重要CTA）は個別レビューを推奨する。
- **radius**: 多くは`radius.md`(16)と一致。`index.tsx primaryCta`(14)、`goshuin/upload pickBtn`(20)は不一致。
- **shadow**: `index.tsx primaryCta` / `concierge ctaPrimary` / `goshuin/upload saveBtn`の3箇所は`shadowColor: theme.gold`を明示追加しており、共通Buttonの`semanticShadow.brand`（`shadowColor`未指定）より金色の発光感が強い。共通Button化するとこの発光効果が失われる。
- **disabled opacity**: 共通Button=0.5。`premium checkoutButton`=0.6、`concierge resuggestButton`は`resuggestButtonDisabled`でopacity明記なし（デフォルト値要確認）。
- **pressed opacity**: 共通Button=0.85。`premium checkoutButton`は0.85で完全一致。
- **色（bg/text）**: A/B分類の7件は全て`theme.gold`/`theme.background`＝Semantic Token(`action.primary`/`action.primaryText`)と値が完全一致している。C分類の一部（`goshuin/upload pickBtn`, `goshuin/index addButton`）はSemantic Tokenと異なる専用トーンを使用しており、見た目を変えずに共通Button化することはできない。

## 9. API不足（C分類が要求する拡張）

1. **outline/ghost variant**（背景透過、枠線+テキストのみ）— C1, C3, C4, C5で必要
2. **success/completed（3値目）state**（視覚的な「完了」表現）— C2, C4で必要
3. **small/pill size**（固定48高ではない小型CTA）— C1, C5, C8で必要
4. **icon API**（アイコンのみ、または icon+ラベル複合レイアウト）— C6, C7, C9で必要
5. **正方形/circle形状**（icon専用ボタン）— C6, C9で必要
6. **text-swap loading**（ActivityIndicatorを使わずtitleを差し替えるloading表現。既存の`loading` propとは非互換のため、既存Button APIへ単純追加はできない）— C4で確認

## 10. PR分割案

### PR候補1：単純置換のみ（A分類）

対象: `AuthPrompt.loginButton`, `concierge ctaPrimary(ResultCard)`, `goshuin/upload saveBtn`, `goshuin/index emptyCta`
（`index.tsx primaryCta`は影響範囲が最大のため独立検討を推奨、下記参照）

### PR候補1-b：Home主CTA単独置換

対象: `index.tsx primaryCta`（見た目差分が他のA分類より大きいため、単独PRでの表示確認を推奨）

### PR候補2：disabled / loading付きCTA（B分類）

対象: `premium checkoutButton`（最優先、既存実装が共通Buttonと最も近い）, `concierge resuggestButton`（`loading`は接続せず`disabled`のみ接続する設計注意）

### PR候補3：Button API拡張

対象: outline variant追加（C1, C3, C4, C5向け）、small/pillサイズ追加（C1, C5, C8向け）、icon API追加（C6, C7, C9向け）、success/completed state追加（C2, C4向け）
※ API拡張は影響範囲が広いため、outline variant・icon API・success stateを個別の小PRへさらに分割することも検討可能。

### PR候補4：神社詳細CTA統一

対象: `shrines/[id].tsx`の`ctaSecondary`(C3) / `ctaPrimary`(C2) / `reflectionButton`(C4)。PR候補3のAPI拡張（outline + success state）完了後、同一画面単位でまとめて適用する。

### PR候補5：Concierge CTA統一

対象: `concierge/index.tsx`の`ctaPrimary`(ResultCard, A2) / `resuggestButton`(B2) / `conditionEditButton`(C5) / `sendBtn`(C6)。PR候補1のA2先行適用後、PR候補3のAPI拡張（outline + icon）完了を待って画面単位でまとめる。

## 11. 実装順序（推奨）

1. PR候補2（`premium checkoutButton`）— 最もリスクが低く、共通Buttonの`disabled`/`loading` APIを最も素直に検証できる
2. PR候補1（AuthPrompt / goshuin 2件）— 見た目差分が数px以内の低リスク単純置換
3. PR候補1-b（Home `primaryCta`）— 影響範囲が大きいため、1・2で共通Button運用に慣れた後に単独検証
4. PR候補3（API拡張: outline variant → icon API → success state の順）— 拡張は分割しつつ、既存3 variantのToken値・API・見た目を壊さないことをvariant追加ごとに検証
5. PR候補4（神社詳細CTA統一）
6. PR候補5（Concierge CTA統一）

## 12. リスク

- **見た目最重要**: `index.tsx primaryCta`（アプリ最上流の主CTA）は数px〜金色影の差分があり、共通Button化で「発光感」が失われる可能性がある。デザインレビューを推奨。
- **loading UXの非対称**: `concierge resuggestButton`は現在ボタン外の説明テキストでloadingを表現しており、共通Buttonの`loading` prop（ActivityIndicatorでtitleを置換）をそのまま繋ぐと説明文が失われる。`disabled`のみ接続する設計が必要。
- **3値state未対応**: `shrines/[id].tsx`の`ctaPrimary`/`reflectionButton`は「完了/保存済み」の第3状態を持つが、共通ButtonのAPIには存在しない。API拡張なしに置換すると視覚的な「達成感」表現が失われる。
- **icon専用CTAの業務重要度**: `sendBtn`(concierge)と`sendButton`(Home)は非テキストCTAだが、いずれもアプリの主要な送信導線であり、対象外候補（アイコンのみの操作＝除外）と機械的に判定すると重要な導線が監査対象から漏れる。本監査ではicon API拡張が必要なC分類として扱った。
- **Token不一致の一部CTA**: `goshuin/upload pickBtn`と`goshuin/index addButton`はSemantic Tokenと異なる専用配色を使っており、共通Button化する場合は配色自体の変更判断（デザイン意思決定）が別途必要になる。

## 13. 次PR指示書（下書き）

次PRでは本監査のPR候補2（`premium/index.tsx`の`checkoutButton`）から着手することを推奨する。理由:

- 既存実装が高さ・radius・bg・text色・pressed opacityのいずれも共通Buttonと一致または近似しており、見た目変化が最小
- `disabled`/`loading`とも既存ロジックをそのまま`Button`の該当propへ渡すだけで実現可能
- 既に`login.tsx`/`birthday/index.tsx`で確立された「1画面1PR」パターンを踏襲できる

次PR指示書には以下を含めることを推奨する:
- 対象ファイル: `apps/mobile/app/premium/index.tsx`のみ
- やること: `checkoutButton`のPressable+ActivityIndicator実装を`<Button variant="primary" title="Premiumに登録する" onPress={...} disabled={checkoutLoading} loading={checkoutLoading} accessibilityLabel="Premiumに登録する" />`へ置換
- 対象外: `retryButton`（C1、API拡張待ち）、`backButton`（対象外）
- API保護: `Button.tsx`自体は変更しない
- 検証: Mobile typecheck、Expo起動、Premium画面の各State（loading/error/unauthenticated/ready/checkout中）の表示確認

## 検証

- [x] 変更ファイルは本監査文書（`docs/audit/mobile-button-adoption-candidates.md`）のみ
- [x] `git diff --check`成功
- [x] Markdown構文確認（テーブル区切り列数の目視確認）
- [x] 既存コード（`apps/mobile/**`のソースファイル）は無変更
- [x] `apps/mobile`配下に本監査文書以外の差分なし
