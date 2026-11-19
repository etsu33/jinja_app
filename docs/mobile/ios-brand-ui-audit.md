> **Status: Active**
>
> 本ドキュメントは、iOS版をブランドデザインの基準プロダクトへ整備する作業（iOS First Brand UI/UX Refresh）の Phase 0 監査記録である。
>
> 本書の時点でアプリの動作は変更していない。実装は Phase 1 以降の個別PRで行う。
>
> 監査対象は `apps/mobile/` の develop 時点の実装と、未マージのブランチ `claude/lucid-davinci-hk5wkr`（8コミット）である。後者に含まれる変更は本文中で明示する。

# KAMI MUSUBI iOS Brand UI 基盤監査（Phase 0）

## 0. 要旨

Phase 1 へ進む前に、**設計判断が3件未確定**である。いずれも本書だけでは結論を出せないため、Mother Ship へ差し戻す（詳細は9節）。

1. **配色の方向が、指示書と現行の正本で正面衝突している。** 指示書は生成り（#F5F1E8）を背景とする明基調を提示するが、現行の正本 `design/theme.ts` は Dark Forest（#0A0F0C）の暗基調で、32ファイルが参照している。どちらを採るかで Phase 1 以降の工数が一桁変わる。
2. **ブランドアセットが1枚も存在しない。** `apps/mobile/assets/` は `placeholder.png`（1KB）のみ。指示書が求める鳥居・本殿のヒーロービジュアルも、App Storeのアイコンも、素材が無い。
3. **見出しに明朝体を使うには、フォントの同梱とライセンス確認が要る。** 現行はシステムフォント指定なし（`fontFamily` の指定が0件）。

加えて、**未マージのPR #3434 が本作業と直接競合する**（4節）。

---

## 1. 現行iOSの実装構成

### 1.1 スタック

| 項目 | 値 |
|---|---|
| フレームワーク | Expo SDK 58.0.23 / React Native 0.88.1 / React 19.3.0 |
| ルーター | expo-router 58.0.30（SDK 58 から `standard-navigation` ベース。react-navigation への直接依存は持たない） |
| 状態管理 | zustand 5（`store/profileStore.ts` のみ） |
| 課金 | expo-iap 6.4.4（StoreKit 2）。Android autolinking からは除外 |
| 地図 | react-native-maps 1.29.11（iOSはApple Maps。Google Maps SDKは意図的に組み込まない） |
| 計測 | posthog-react-native 4.55 |
| Bundle ID | `com.morietsu.kamimusubi` |
| テスト | vitest（environment: node）。画面はソースをテキストとして読む契約テスト方式 |

### 1.2 画面構成

route 19 / layout 2 / component 11。

```text
app/_layout.tsx            root Stack（下層16routeにネイティブヘッダー）
app/(tabs)/_layout.tsx     Tabs（タブバーに出す4画面のみ）
  ├ index                  ホーム
  ├ concierge/index        相談（推薦結果）
  ├ records/index          記録
  └ mypage/index           マイページ
Stack（下層）
  search / shrines/[id] / favorites / ranking / journey / premium /
  profile / goshuin / goshuin/upload / visit-history /
  consultation-history / consultation-history/[id] /
  recently-viewed / login / signup
```

> この Tabs+Stack 構成は `claude/lucid-davinci-hk5wkr` の変更であり、develop 時点では Tabs 単体＋「隠しタブ」構成（下層15画面をタブバーに出さない `Tabs.Screen` として登録し、各画面が「← 戻る」を手書き）である。

### 1.3 ナビゲーションの既知の問題（ユーザー指摘）

タブバー中央の「相談」が円形の浮きボタン（FAB）になっている。

| 要素 | 寸法 |
|---|---|
| 他3タブのアイコン | 24pt（react-navigation の既定値） |
| 中央の円 | **54pt**（直径）、内側アイコン28pt、`marginTop: -18` |

円が他アイコンの **2.25倍**で、タブバーの上端から約23pt はみ出す。これは Material Design の FAB パターンであり、iOSのタブバーには存在しない形である。さらに、**はみ出した上側はタブボタンの当たり判定の外にあるため、見えていても押せない。**

指示書2節の「静けさと品格」および3.4「コンポーネントの統一」と整合しない要素として、Phase 1 の対象候補とする。

---

## 2. 既存デザインシステム

### 2.1 Token の3層構造

正本は `docs/design/design-token.md`（Primitive / Semantic / Platform Theme）。Mobile の実値ファイル：

| カテゴリ | ファイル | Semantic層 | 状態 |
|---|---|---|---|
| Color | `design/theme.ts` + `design/semanticColorTokens.ts` | あり（26キー、`PlatformColorTheme` 型で tsc 強制） | **実装済み** |
| Typography | `design/typography.ts` | あり（14キー） | **実装済み**（未マージ） |
| Spacing | `design/spacing.ts` | あり（7キー） | 実装済み |
| Radius | `design/radius.ts` | あり（6キー） | 実装済み |
| Shadow | `design/shadow.ts` | あり（5キー） | 実装済み |
| Component | `design/cardSizes.ts` / `design/ctaSizes.ts` | なし（Primitiveのみ） | 部分的 |

Color の Semantic 契約が **tsc レベルで網羅を強制されている**点（キーが1つ欠けるとコンパイルエラー）は、本作業で維持すべき資産である。

### 2.2 現行パレット（Color Primitive の実態）

`design/theme.ts` には2つのパレットが同居する。

| パレット | 内容 | 実使用 |
|---|---|---|
| `kamimusubiDark` | Dark Forest（背景 #0A0F0C、面 #131A15、アクセント金 #C9A96A、杉緑 #8FAE84） | **32ファイル** |
| `colors` | 明基調の初期パレット（paper #F6F3EE、primary #E24E33、accent #F2C94C） | **0ファイル（デッドコード）** |

`kamimusubiDark` にはコード内に明示的な Visual Direction 宣言がある。

> Visual Direction: Dark Forest（森影）— 近黒緑からモスチャコールへ至る基盤。狙いは「静かな鎮守の杜の参道」であり、ホラー/ゴシック、および黒×金のラグジュアリー表現は明確に対象外とする。奥行きは装飾やエフェクトではなく、背景・面・浮き面の明度差（大気遠近）で作る。

つまり**現行の暗基調は、偶然そうなったのではなく、意図をもって選ばれ文書化されている**。指示書の明基調パレットはこれを置き換えるものであり、独断で実施しない（9節）。

### 2.3 Token化されていない領域

| 領域 | 現状 |
|---|---|
| FontFamily | 指定0件（システムフォント）。見出しの明朝体は未対応 |
| Icon | `MaterialIcons`（タブバー）＋ 絵文字・記号グリフ（⛩ ♡ ↑ → ✓ ›）＋ 円内の漢字1文字（人・入・新・規・問・退・P）。SF Symbols 未使用 |
| 状態表現 | `StateCard`（title + description）を7画面が使用。`favorites` / `goshuin` / `recently-viewed` の3画面は自前の `<Text>` で書いている |
| Loading | `ActivityIndicator` は `components/ui/Button.tsx` のみ。画面のローディングはテキスト表示 |
| Modal | `AuthPrompt` と `ProfilePickerModal` の2つが個別実装。共通の Modal コンポーネントは無い |
| Input | 共通コンポーネント無し。各画面が `TextInput` を直接スタイルする |
| Header | 共通コンポーネント無し（下層はネイティブヘッダー、タブ画面は各自） |

指示書3.4が挙げる9種のうち、**共通化されているのは Button / Card（寸法Tokenのみ）/ Empty・Error（StateCard、ただし3画面が逸脱）の3種**。Input / Header / Modal / Loading は未共通化である。

---

## 3. Webとの依存関係

### 3.1 共有コード（変更禁止）

`apps/mobile` が `packages/shared` から import しているモジュール：

| モジュール | mobile 参照数 | Web も参照 |
|---|---|---|
| `userOrigin` | 8 | — |
| `recommendationAnalyticsProvenance` | 5 | あり |
| `recommendationReasonDisplay` | 3 | あり |
| `recommendationReasonAuthority` | 3 | あり |
| `directionReference` | 3 | あり |
| `directionAnalytics` | 3 | あり |
| `directionAccessibility` | 2 | あり |

いずれも推薦理由の表示判断・経路案内・計測の契約であり、**Web側（`apps/web/src/components/shrine/` など）も同じモジュールを参照している**。指示書5節の変更禁止（Recommendation Score / Meaning Layer / Analytics Event Contract）に該当するため、本作業では一切変更しない。推薦結果画面（4.3）の改善は、これらが返す値の**並べ方と見せ方**に限定する。

### 3.2 Design Token の関係

Web と Mobile は **Semantic Token の「名前」だけを共通**とし、実値は Platform Theme 層で別々に持つ（`docs/design/design-token.md` 設計原則2）。現行は Web Emerald / Mobile Gold で意図的に異なる。

したがって **Mobile のパレット変更は Web に波及しない。** ただし「Web Emerald / Mobile Gold の統一可否」は同文書の保留事項1であり、Mobile を朱色基調にすると Web との乖離がさらに広がる。これは記録に留め、Web は現状維持とする（指示書「最終ルール」）。

---

## 4. iOS精査との競合リスク

指示書6節が言う「進行中のiOS精査」は、同一セッションで実施中の作業である。実体は以下。

### 4.1 未マージブランチ `claude/lucid-davinci-hk5wkr`（8コミット）

develop からの差分。**ユーザーのMacはこのブランチをチェックアウトしており、iOS Simulator で動作確認済み。**

| コミット | 内容 | 本作業との関係 |
|---|---|---|
| `cb77caf7` | Tabs単体 → Tabs+Stack 構成へ移行 | **前提**。4.x の画面構造はこれを基準にする |
| `c7434546` | Typography Token 新設（HIG準拠、本文17pt） | **前提**。指示書3.3の土台 |
| `dd7869e5` | 審査ブロッカー（version/buildNumber、orientation、userInterfaceStyle: dark、規約リンク、プレースホルダ削除） | **衝突注意**。`userInterfaceStyle: "dark"` は明基調採用時に要変更 |
| `306d4b2c` / `a621d69b` | タブ画面のセーフエリア | 前提 |
| `c0a1246d` | Typography移行漏れの回収 | 前提 |
| `2bf82291` | 到達不能画面への導線追加 / 振り返り履歴の削除 | **衝突注意**。4.5 の画面一覧が変わる |
| `3b5a8aba` | 44pt未満のタップ領域の解消 | 前提 |

**判断**：本作業（Phase 1以降）は、このブランチを前提にすべきである。develop を基準にすると Tabs+Stack と Typography Token を作り直すことになる。

### 4.2 PR #3434 `feature/mobile-ios-hide-purchase`（Open、2026-11-04）

> feat(mobile): iOSでは購入要素を表示しない

**develop の現状と矛盾している。** このPRは App Store Guideline 3.1.1 への対応として iOS の購入UI（購入ボタン・外部決済導線・購入を促す文言）を全て隠す設計だが、develop には 2026-11 に **StoreKit 2 による iOS 内課金が3本マージ済み**である（`90ef9fb` / `d9f304a` / `2d52430`）。方向が逆。

さらにこのPRは `apps/mobile/app/mypage/index.tsx` と `apps/mobile/app/premium/index.tsx` を変更するが、前者は `claude/lucid-davinci-hk5wkr` で `app/(tabs)/mypage/index.tsx` へ移動済みのため、**マージ時にコンフリクトする**。

**差し戻し事項**：このPRを閉じるか、StoreKit前提に作り直すか。指示書4.5（Premium画面）の作業は、この決着が付くまで着手しない。

### 4.3 PR #3488 dependabot `mobile-deps`（10件更新）

Expo 58.0.23 → 58.0.26 ほか。UI変更は無いが、**Phase 1 を始める前にマージするか後回しにするかを決める必要がある**。後からマージすると Phase 1 のPRと衝突しうる。

### 4.4 ローカル未コミットの作業（ユーザーのMac）

`fix/mobile-home-hig-touch-targets`（ローカル専用、originに無し。コミット0件）の未コミット差分は、`3b5a8aba` で取り込み済み・`git stash` にバックアップ済み。**競合なし。**

### 4.5 未確認のドキュメント

ユーザーのMacに `docs/audit/ios-ui-readiness.md` が untracked で存在する。**内容未確認。** 本書と重複または矛盾する可能性があるため、Phase 1 着手前に突き合わせる（9節）。

---

## 5. UI改善候補

観察された問題を4分類に整理する。重大度は、指示書の目的（商用アプリ品質）に対する影響度で付けた。

### A. ブランドの不在（重大）

| # | 事実 | 影響 |
|---|---|---|
| A-1 | `assets/` に `placeholder.png`（1KB）しか無い。アプリアイコン・スプラッシュ・ヒーロービジュアルの素材が無い | 指示書3.1の必須モチーフ（鳥居・本殿・朱色）を実装できない。App Store提出もできない |
| A-2 | ブランドロゴが絵文字 `⛩️`（`logoMark`、fontSize 22）。端末のフォントに依存し、OSによって字形が変わる | ブランドの同一性が保てない |
| A-3 | 神社写真は API の `imageUrl` 依存で、無い場合は `⛩` の絵文字プレースホルダ（`heroPlaceholder`）。静的シード `data/shrines.ts` は4件のみ | 4.4（神社詳細）の「神社建築の写真」が成立しない神社がある |

### B. 構成の不統一（中）

| # | 事実 |
|---|---|
| B-1 | 状態表現が二系統。`StateCard` を使う7画面と、自前の `<Text>` で書く3画面（favorites / goshuin / recently-viewed） |
| B-2 | Input / Header / Modal / Loading の共通コンポーネントが無く、画面ごとに個別実装 |
| B-3 | アイコン体系が3系統混在（MaterialIcons / 絵文字・記号グリフ / 円内の漢字1文字） |
| B-4 | `design/theme.ts` に未使用の `colors` パレットが残置（0ファイル参照） |

### C. iOS規範からの逸脱（中）

| # | 事実 |
|---|---|
| C-1 | タブバー中央の54pt円形FAB。他アイコン24ptの2.25倍。Material パターン。はみ出し部分は押せない（1.3節） |
| C-2 | タブバーアイコンが MaterialIcons（Androidイディオム）。SF Symbols 未使用 |
| C-3 | Dynamic Type 非対応。`allowFontScaling` / `maxFontSizeMultiplier` の参照が0件 |
| C-4 | `shadow.ts` が黒影（opacity 0.25〜0.28）を定義するが、`theme.ts` 自身が「奥行きは明度差で作る」と宣言しており、暗背景で黒影はほぼ不可視。宣言と実装が二重 |

### D. 情報設計（中）

| # | 事実 |
|---|---|
| D-1 | 推薦結果（concierge）が1,487行の単一ファイル。事実・解釈・行動提案の区分は Reason V4 で構造化されているが、視覚的な階層が弱い |
| D-2 | 神社詳細が1,180行。御祭神・由緒・ご利益・経路・御朱印が同じ重みで並ぶ |
| D-3 | ホーム画面の情報量が多く、初回表示で主要CTA（「この相談からご縁を見る」）が画面外。Simulator（iPhone 17 / iOS 26）で確認済み |

> D-3 は Typography を HIG 準拠（本文17pt）に上げた結果として発生した。指示書4.1の「初回表示時に主要CTAが認識できること」に直接該当する。

---

## 6. デザイントークン案

**現時点では案を確定しない。** 6.1の衝突が未解決のため、2つの選択肢を提示する。

### 6.1 衝突の内容

| 項目 | 現行の正本（`design/theme.ts`） | 指示書3.2 |
|---|---|---|
| 背景 | `#0A0F0C` 近黒緑（Dark Forest） | `#F5F1E8` 生成り |
| 文字 | `#F3EEE3` 霧の生成り | `#242424` 墨色 |
| 主アクセント | `#C9A96A` 褪せた金 | `#B53A2D` 朱色 |
| 副アクセント | `#8FAE84` 杉緑 | `#B39665` 金茶 |
| 基調 | 暗 | 明 |

明暗が反転する。加えて `app.config.ts` の `userInterfaceStyle: "dark"`（`dd7869e5`）も変更対象になる。

### 6.2 選択肢

#### 案1：明基調へ転換（指示書どおり）

- 全26 Semantic Color の実値を差し替え。32ファイルが `kamimusubiDark` を直接参照しているため、Primitive 直参照の棚卸しが先に必要
- `shadow.ts` を実効化できる（明背景なら黒影が見える）。C-4 が解消する
- `userInterfaceStyle` を `light` へ。OSのキーボード・アラートも明に戻す
- 「和のエディトリアル」の指向には合う
- 工数：大。Phase 1 のほぼ全てを占める

#### 案2：暗基調を維持し、朱色をアクセントに導入

- `kamimusubiDark` の構造（明度順の面、大気遠近）を保ったまま、`action.primary` を金 `#C9A96A` から朱色系へ寄せる
- 既存の `colors.primary = #E24E33`（現在デッドコード）を Primitive に昇格させる余地がある
- 鳥居の朱は暗背景でこそ映える、という読み方は成立する
- `userInterfaceStyle: "dark"` を維持。審査対応（`dd7869e5`）に手を入れない
- 工数：中

### 6.3 どちらでも共通して行うこと

- `colors`（未使用パレット）の削除
- Component Token（Input / Header / Modal / Loading）の Semantic 層追加
- Icon 体系の一本化方針の決定（SF Symbols 採用可否）
- FontFamily Token の新設（6.4）

### 6.4 タイポグラフィ

`design/typography.ts`（14 Token、HIG準拠）は既に存在するため、**サイズとウェイトのスケールは流用できる**。追加が必要なのは FontFamily 層のみ。

明朝体を採用する場合の確認事項：

- 同梱するフォントのライセンス（商用アプリへの埋め込み可否、再配布条項）
- ファイルサイズ（日本語フォントは数MB〜十数MB。アプリサイズに直接響く）
- `expo-font` での読み込みとスプラッシュ中のフォント待ち
- 英語表示時のフォールバック（指示書3.3「日本語と英語の双方で表示崩れを防ぐ」）

**ライセンス確認が済むまで明朝体は採用しない。** 候補が決まり次第、本書に追記する。

---

## 7. 画面ごとの改善範囲

各画面について、**変更してよい範囲**と**触らない範囲**を分ける。

| 画面 | 変更する | 変更しない |
|---|---|---|
| ホーム（4.1） | ヒーロービジュアル追加、情報の優先順位、主要CTAの初回表示、テーマチップの体裁 | 相談テーマの文言・個数、`buildSearchFilters` の受け渡し契約 |
| 相談・推薦結果（4.2 / 4.3） | 入力欄のコントラスト、キーボード時のレイアウト、推薦理由の視覚階層、神社カードの体裁 | 入力項目の増減、バリデーション、`ConditionFieldsCard` の props 契約、Reason V4 の解釈、推薦順位、生成文章 |
| 神社詳細（4.4） | 写真の扱い、情報の階層、経路・保存・御朱印の導線の体裁 | 表示項目の増減、`packages/shared` の表示判断、未確認の宗教的・歴史的事実の追加 |
| Premium（4.5） | 料金の明示、無料との区分、CTAの視認性 | 料金・プラン・決済処理・StoreKit のフロー。**ただし PR #3434 の決着が前提**（4.2） |
| マイページ・記録 | 共通コンポーネントの適用、カードの体裁 | 退会フロー、規約リンク、計測イベント |

### 既存データの制約

- 推薦結果に出せるのは Recommendation API が返す情報のみ。`packages/shared/recommendationReasonDisplay` と `recommendationReasonAuthority` の判断に従う
- 神社詳細の表示項目は既存の API 契約に従う
- 神社写真が無い場合のフォールバックが必要（A-3）。**架空の建築画像を実在神社の写真として使わない**

---

## 8. PR分割計画

1機能・1責務・1PR。**本書のPRが Phase 0 の完了物であり、以降は 9節の差し戻しが解決してから着手する。**

| PR | 内容 | 前提 | 規模 |
|---|---|---|---|
| **PR-0**（本PR） | Phase 0 監査と設計方針（ドキュメントのみ） | — | 小 |
| PR-1 | Color / FontFamily の Platform Theme 差し替え | 9節①の決定、アセット（9節②） | 大 |
| PR-2 | Component Token 追加（Input / Header / Modal / Loading）と StateCard の全画面適用 | PR-1 | 中 |
| PR-3 | タブバーの再設計（C-1 のFAB）とアイコン体系の一本化 | PR-1、9節④ | 中 |
| PR-4 | ホーム画面（ヒーロー、CTA、情報の優先順位） | PR-1〜3、アセット | 中 |
| PR-5 | 相談・推薦結果の視覚階層 | PR-1〜3 | 大 |
| PR-6 | 神社詳細（写真と情報の階層） | PR-1〜3、A-3の方針 | 中 |
| PR-7 | Premium | PR-1〜3、**PR #3434 の決着** | 小 |

**ベースブランチ**：PR-1 以降は `claude/lucid-davinci-hk5wkr` をマージしてからの develop を基準にする（4.1）。本PR（PR-0）はドキュメントのみのため develop から直接切っている。

---

## 9. 差し戻し事項（Mother Ship判断）

Phase 1 に着手する前に、以下の決定が必要である。

| # | 項目 | 選択肢 | 影響 |
|---|---|---|---|
| ① | **配色の方向** | 6.2 の案1（明基調へ転換）/ 案2（暗基調＋朱色アクセント） | Phase 1 の工数が一桁変わる。`design/theme.ts` の Visual Direction 宣言と `docs/design/design-token.md` の更新が伴う |
| ② | **ブランドアセットの調達** | 鳥居・本殿のヒーロービジュアル、1024pxのアプリアイコン、神社写真の供給源と権利 | 無ければ 4.1 / 4.4 と App Store 提出が成立しない |
| ③ | **PR #3434 の扱い** | 閉じる / StoreKit前提に作り直す | Premium画面（4.5 / PR-7）の前提 |
| ④ | **アイコン体系** | SF Symbols へ移行 / MaterialIcons を維持 | iOSらしさと、Androidとの共通化のトレードオフ |
| ⑤ | **明朝体のライセンス** | 候補フォントの選定と商用埋め込み可否の確認 | 確認が済むまで採用しない（6.4） |
| ⑥ | **`claude/lucid-davinci-hk5wkr` のマージ可否** | マージしてから Phase 1 / 並行して進める | 並行すると Tabs+Stack と Typography を二重に作ることになる |
| ⑦ | **`docs/audit/ios-ui-readiness.md`** | 内容の突き合わせ | 本書と重複・矛盾する可能性（4.5） |
| ⑧ | **dependabot PR #3488** | Phase 1 前にマージ / 後回し | 後からだと Phase 1 のPRと衝突しうる |

---

## 10. テスト結果

本PRはドキュメントのみの変更であり、アプリのコードを含まない。

| 項目 | 結果 |
|---|---|
| `git diff --check` | 実施・問題なし |
| markdownlint | 実施・問題なし |
| TypeScript型チェック | **未実施**（コード変更なし） |
| ESLint | **未実施**（コード変更なし） |
| Unit Test | **未実施**（コード変更なし） |
| Expo起動確認 | **未実施**（コード変更なし） |
| iOS Simulator | **未実施**（コード変更なし） |

> 5節 D-3 と 1.3 の FAB の当たり判定は、`claude/lucid-davinci-hk5wkr` を iPhone 17 / iOS 26 シミュレータで動かして観察した事実である。本PRの変更によるものではない。

---

## 11. 関連ドキュメント

- `docs/design/design-token.md` — Design Token v1 の正本（3層構造、保留事項）
- `docs/mobile/design-system-audit.md` — Token構成の監査記録（Archive）
- `docs/mobile/route-structure-audit.md` — Route構成の移設記録（Archive）
- `docs/mobile/cta-radius-audit.md` — CTA専用Radiusの判断経緯（Archive）
- `apps/mobile/design/` — Token実値の正本
