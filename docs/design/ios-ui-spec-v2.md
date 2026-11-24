> **Status: Active**
>
> 本ドキュメントは、iOS（`apps/mobile`）のUI統合設計の正本である。
>
> 配色の実値と根拠は `docs/design/color-direction-v1.md`、Token の構造は `docs/design/design-token.md` を参照する。
> 本書と食い違う場合は、04節の注記に従う。
>
> 対象：`apps/mobile` のみ。Web / Backend は変更しない。

# KAMI MUSUBI iOS UI統合設計 v2.0

Guided Journey × Quiet Editorial

---

> **個別承認（2026-11-24）**：iOSホームのみ、既存ロゴ・深藍・淡金・控えめな雲文様によるIndigo & Goldへ調整する。ホームの背景グラデーションと淡金CTAは本書の通常配色・装飾制限の例外とする。他画面・Web・Androidへは展開しない。実装範囲は `apps/mobile/README.md` を参照。

## 01 目的

iOSのUIを「静かな紙面をめくりながら、自分の状態を整理し、神社との接点へ進む体験」として統一する。

UIは情報入力フォームでも、神社情報を並べた検索アプリでもない。体験全体を一つの流れとして設計する。

```text
問い → 選択 → 状態整理 → 推薦 → 理解 → 参拝 → 記録 → 再相談
```

## 02 二つのUI原則

画面の役割に応じて2つを使い分ける。

### A. Guided Journey

対象：初回起動 / Onboarding / Concierge入力 / 条件設定 / Recommendation Processing / 完了Transition / Premium導入

目的：ユーザーを迷わせず、少ない判断単位で次へ導く。

```text
1画面 = 1質問 + 1判断 + 1 Primary Action
```

### B. Quiet Editorial

対象：Home / Recommendation Result / Shrine Detail / Record / MyPage / 保存した神社 / 御朱印 / 履歴・振り返り

目的：情報を急かさず、読める状態にする。

```text
見出し → 意味 → 本文 → 区切り → 次の情報
```

カードを大量に並べず、縦方向のストーリーとして構成する。

## 03 ブランドコンセプト

**生成りの紙に、深藍の骨格と朱の印。**

神社らしさを、鳥居アイコン・金色・和柄・筆文字・装飾で直接表現しすぎない。
写真・言葉・色・余白・歴史・参拝体験から生み出す。

## 04 ブランドカラー

| Role | Color |
|---|---|
| Background（鳥の子色） | `#F5EEDC` |
| Background Subtle | `#EBE2CC` |
| Surface Default | `#FFFFFF` |
| Surface Elevated | `#FFFFFF` |
| Structure（深藍） | `#172A40` |
| Primary Accent（朱） | `#B53A2D` |
| Text Primary | `#242424` |
| Text Secondary | `#55514A` |
| Text Muted | `#656057` |
| Border Default | `#CFC2A4` |
| Border Strong | `#8E8472` |
| Border Accent（金茶） | `#B39665` |

> **注記（2026-11-19）**：指示書 v2.0 初版は Background `#F5F1E8` / Surface `#FBF8F2` / Border `#CFC6B5` を挙げていた。
> この組み合わせは白カードと地のコントラスト比が 1.11 で、15節が求めるSurface Cardが面として読めなかった（実機で確認）。
> 地を一段沈めて比 1.18 を確保した値へ改めた。
> さらに 2026-11-19、起動時のSplash（和の朝焼け）の下端に合わせて地を鳥の子色 `#F5EEDC` へ温めた（比 1.16）。
> 経緯は `docs/design/color-direction-v1.md`。

## 05 色の責務

**深藍**：Page Title / Section Heading / Navigation / 選択状態 / Secondary Action / Premiumの構造 / Progress。画面の骨格を作る。

**朱**：Primary CTA / Focus / 小さなSelected Indicator / 最重要状態。**1画面につき強い朱は原則1箇所。**
背景全面・複数カード・大量のアイコン・大見出し全部へ使用しない。

**墨**：本文の基本色。

**金茶**：Border / Divider / Premium Border のみ。文字・アイコンに使用しない。

## 06 画面レイヤー

明度は必ず `background.subtle < background.base < surface.default <= surface.elevated` の順とする。Surfaceを増やしすぎない。

## 07 基本画面構造（Guided Journey）

```text
Safe Area
Progress / Step
↓ 16〜24px
Page Title
↓ 12〜16px
Supporting Text
↓ 24〜40px
Main Selection / Input
↓
Flexible Space
↓
Primary CTA
↓ 12px
Secondary Action
↓ Safe Area
```

## 08 1画面1テーマ

相談画面で、相談内容・誕生日・ご利益・参拝スタイル・距離・交通手段・条件を同時に表示しない。段階化する。

```text
STEP 1 今、どんなことを整理したいですか？
STEP 2 どんな時間を過ごしたいですか？
STEP 3 どんな参拝をしたいですか？
STEP 4 必要なら条件を追加
→ この相談からご縁を見る
```

## 09 初回体験

```text
Splash → Brand Intro → 利用目的 → 相談テーマ → 参拝スタイル → 補助条件
→ Recommendation Processing → Recommendation Result
```

5〜7ステップ程度を上限目安とする。機能説明スライドを大量に挟まない。

## 10 Splash

ロゴのみを基本とする。余計なコピー・ボタン・機能説明を置かない。

> **実装（2026-11-19）**：和の朝焼けのグラデーション（濃藍 → 藍鉄 → 薄縹 → 白群 → 東雲色 → 鳥の子色）に
> 白の文字組を置く。実体は `apps/mobile/components/common/DawnSplash.tsx`、色は `design/theme.ts` の `dawn`。
> ロゴは上から32%の位置（地の色 `#334663`、白文字とのコントラスト 9.56）。
> **白文字を置けるのは上から44%まで**で、50%の薄縹では 4.46 となり AA を割る。
> 焼けの帯（東雲色・曙色）に文字を置くなら墨文字にする。

## 11 Brand Intro

写真の大きな使用を許容する。Full Bleed Photo は Brand Intro と特別な完了画面など限定的に使う。

## 12 写真

優先：日中 / 自然光 / 参道 / 鳥居 / 石段 / 境内 / 木 / 森 / 水 / 白砂利 / 手水

避ける：過度な暗部処理 / 強い黒Overlay / 抽象CG / オーラ / 宇宙 / 光の粒 / 神秘演出目的だけの画像

## 13 質問タイトル

質問文そのものを画面の主役にする。24〜30px / Medium〜Semibold / 深藍 / Line Height 1.35〜1.5 / 原則左揃え。

中央揃えは Splash / Brand Intro / Completion に限定する。

## 14 Supporting Text

タイトル下に2〜3行以内。色は `text.secondary`。説明文が質問より強くならないようにする。

## 15 通常選択カード

| | 指定 |
|---|---|
| Default 面 | `surface.default` |
| Default 線 | `border.default` |
| Radius | 16〜20px |
| Padding | 16〜20px |
| Text | 深藍 |
| Selected 線 | 深藍 |
| Selected 面 | 薄い深藍系Surface |
| Selected 印 | 小さな朱または深藍 |

**朱でカード全面を塗らない。**

## 16 写真付き選択カード

参拝スタイル / 旅の目的 / 興味 / 海外版カテゴリ / 感覚的な利用目的で使用してよい。

Default：Photo + 薄い深藍Overlay + 白文字。Selected：深藍Border 2px + 小さな朱Check。

## 17 2列Grid

写真選択などで許容する。選択肢は最大6程度を目安にする。

## 18 Bubble Selection

気分 / 感覚 / 関心カテゴリに限定して使用できる。円の大きさを重要度・推奨度・優先順位として使用しない。サイズ差は10〜15%以内。

## 19 Primary CTA

原則、画面下部に配置する。

| 項目 | 指定 |
|---|---|
| Background | `action.primary` |
| Text | `action.primaryText` |
| Height | 52〜56px |
| Radius | 26〜28px |
| Horizontal Margin | 20〜24px |

**1画面にPrimary CTAを複数置かない。**

## 20 Secondary Action

「あとで設定する」「条件を追加する」「スキップ」など。色は深藍または `text.secondary`。Underlineは原則使用しない。

## 21 Progress

相談・Onboardingでは細いProgressを使う。Filled は深藍、Remaining は `border.default`。Progressを画面の主役にしない。

## 22 Back操作

各ステップで戻れる状態を基本とする。左上に戻る。Navigation Headerを大きく作らない。

## 23 Skip

Recommendationに必須でない条件はSkip可能とする。必須Signalと補助SignalをUI上でも区別する。

## 24 Recommendation Processing

`Loading...` やSpinnerのみを表示しない。何が起きているかを示す。

**表示する工程は、実際のシステム処理と大きく矛盾しない表現に限定する。**

## 25 Processing Animation

許容：Fade / Check transition / Slight Slide。派手な演出は使用しない。

Processingは待ち時間を隠すためではなく、何が起きているかをユーザーが理解する補助として設計する。

## 26 Completion Transition

推薦取得後に短いTransitionを挟むことは許容する。1〜2秒以内。宗教的な確定表現を避ける。

## 27 Recommendation Result

Quiet Editorialへ切り替える。カード一覧ではなく読み物として設計する。

```text
今回のご縁 / 神社名 / 所在地 / 神社写真
あなたの相談との接点
なぜ今回提案されたのか
この神社について
参拝するときの問い
[神社の詳細を見る] [経路を見る]
```

## 28 Recommendation Resultの責務

```text
何が提案されたか → なぜ提案されたか → 神社自体はどんな場所か
→ 自分とどう接続するか → 次に何をするか
```

大量の独立カードに分断しない。

## 29 Shrine Detail

完全にQuiet Editorialを採用する。

```text
神社名 / 所在地 / Hero Photo / 概要 / 由緒 / 御祭神 / ご利益
/ 今回の相談との接点 / アクセス / 御朱印 / 保存・経路
```

神社情報とKAMI MUSUBIの解釈を視覚的に分離する。

## 30 Home

機能一覧にしない。最重要行動を上部に置く。

```text
KAMI MUSUBI
今の相談を、神社とのご縁につなげる。
[相談入力]
[この相談からご縁を見る]
────
最近の記録
────
保存した神社
```

## 31 Record

```text
記録
相談から育ったご縁をここから振り返れます。
[ご縁の歩み] [保存した神社] [御朱印]
```

各機能は同じSurface Card体系で構成する。

## 32 Bottom Navigation

通常画面：ホーム / 相談 / 記録 / マイページ

**Guided Journey中は原則非表示**（Onboarding / Consultation Steps / Processing / Completion）。Recommendation Result以降、通常Navigationへ戻す。

Default：Muted Icon + Muted Text。Active：深藍（必要なら小さな朱Indicator）。**Active Tab全体を朱にしない。**

## 33 Premium導線

Onboarding直後に強制提示しない。`無料相談 → 推薦 → 価値理解 → Premium案内` とする。

## 34 Premium画面

Premiumの構造色は深藍。Primary CTAとして必要な場合のみ朱を使用する。金茶はBorderまたはDividerのみ。

> **注記**：価格は StoreKit が返すローカライズ済みの値を表示する（`lib/appleStoreKit.ts` の `loadPrices()`）。
> UIに金額を直書きしない。App Store Connect の設定と食い違うとガイドライン 3.1.2 に抵触する。

## 35 Card Hierarchy

強いShadowを多用しない。`background.base → surface.default → surface.elevated` で階層を作る。

Shadow使用対象：Modal / Bottom Sheet / Floating CTA / Elevated Surface。**通常カード全部へShadowを付けない。**

## 36 Radius

| 対象 | 指定 |
|---|---|
| Selection Card | 16〜20px |
| Photo Card | 18〜20px |
| Modal | 20〜24px |
| CTA | 26〜28px |

丸みは統一する。画面ごとに異なるRadius体系を作らない。

## 37 Animation

許容：Fade / Slight Slide / Scale 0.98 → 1 / Selection Transition / Bottom Sheet。Duration 180〜300ms程度。

禁止：鳥居が光る / 桜が舞う / 金粉 / 光線 / オーラ / Glow / 過剰なParallax。

## 38 Error State

宗教的な意味をエラーへ接続しない。

禁止：`ご縁がありませんでした`

推奨：`うまく読み込めませんでした。通信状況を確認して、もう一度お試しください。` CTA は `もう一度試す`。

## 39 コピー原則

説明ではなく問いを中心にする。文章は短くするが、意味を削りすぎない。

## 40 禁止事項

> **Gradient の例外（2026-11-19）**：和の朝焼けを表すグラデーションは、**区切りの画面に限って**使ってよい。
> 対象は Splash / Brand Intro / Immersive Photo Moment の Overlay / Completion Transition の4つ。
> 通常画面（Home / 相談 / 記録 / マイページ / 神社詳細 / Premium）の地は単色のまま。
> 向きは上から下への一方向のみ。斜め・放射状は使わない。

Gradient / Neon / Gold Text / Glow / 強いGlassmorphism / 全面Dark UI / 多色Icon / 大量の装飾 / 鳥居Iconの反復 / 全CardへのShadow / 1画面複数Primary CTA / 1画面8個以上の選択肢 / SpinnerだけのLoading / 初回直後の強制Premium / 神秘性を演出する抽象CG / 意味のない写真

## 41 画面ごとの設計モード

| 画面 | Mode |
|---|---|
| Splash | Guided |
| Brand Intro | Guided |
| Onboarding | Guided |
| Concierge Input | Guided |
| Additional Conditions | Guided |
| Processing | Guided |
| Completion | Guided |
| Recommendation Result | Editorial |
| Shrine Detail | Editorial |
| Home | Editorial |
| Record | Editorial |
| MyPage | Editorial |
| Premium説明 | Editorial + Guided CTA |

## 42 UI評価基準

1. ユーザーが「今、何をすればいいか」一目で分かるか
2. 1画面で考えることが多すぎないか
3. 情報を読む余白があるか
4. GuidedとEditorialの役割が混ざっていないか
5. 深藍・朱・生成りの責務が守られているか
6. 装飾を取り除いても画面が成立するか
7. ユーザーが「入力した」感覚より「自分の状態を整理した」感覚を持てるか

## 43 デザインキーワード

Quiet / Editorial / Guided / Japanese / Natural / Reflective / Warm / Minimal / Structured / Human

静けさ / 余白 / 紙 / 墨 / 印 / 参道 / 内省 / 導き / 記録

## 44 最終体験

「神社っぽいアプリ」ではない。検索アプリでも占いアプリでもない。

```text
今の状態を整理する → 場所との接点を知る → 実際に訪れる
→ 体験を記録する → あとから振り返る
```

UIはその体験を邪魔せず、静かに次の一歩へ案内する道具として設計する。
