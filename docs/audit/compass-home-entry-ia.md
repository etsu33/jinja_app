> **Status: Audit → Implementation（本ドキュメント内でREADY判定に基づき実装まで実施）**
>
> Compass Full Experience Gateをクローズする前に、KAMI MUSUBIのメインエントリー（Home）からConciergeとCompassの両方が発見可能であることを検証・実装した記録。Product Navigation / IA監査が主目的であり、Premium gating・Analytics実装・Concierge/Compass内部の再設計・Recommendation変更のいずれも行わない。

# Compass Home Entry IA Audit

## 1. Current Home Audit

- **Home実装**: `apps/web/src/app/page.tsx` → `apps/web/src/features/home/HomePage.tsx`（Server Component、データ取得なし）→ `HomeMainClient.tsx`（Client、実際の構成）。
- **現在の主要CTAインベントリ**:
  1. `HomeHeroConsultationInput`内「この相談ではじめる」ボタン — テーマ未入力時disabled、入力後`/concierge?theme=...`へ遷移。
  2. 相談テーマ選択チップ6個（「疲れを整えたい」等）— クリックでテキストエリアに反映するのみ（即遷移はしない）。
  3. 「＋ 条件を追加する」— 折りたたみ式の補足説明を開くのみ（遷移なし）。
  4. SUB PATHSセクション内「地図でも確認する」→ `/map`。
  5. SUB PATHSセクション内「神社一覧も見る」→ `/shrines`。
- **既存Concierge導線**: HomeのHero自体が実質的にConciergeの入口そのものであり、`/concierge`内の`ConciergeEntryCard.tsx`とほぼ同型の相談入力（テキストエリア＋テーマチップ＋CTA）がHomeに直接埋め込まれている（別ページへ飛ばす前に、既にHome上で相談を書き始められる設計）。これはHome自体が「Concierge Entry」の役割を既に持っていることを意味する。
- **Compassの現在のHome導線**: **存在しない**。`HomeMainClient.tsx`・`HomeHero.tsx`・SUB PATHSセクションのいずれにも`/compass`への言及・リンクは一切無い（`grep -rn "compass" apps/web/src/features/home/`で確認、ヒット無し）。
- **現在の情報階層**: Hero（Concierge、最大の視覚的重み、`rounded-3xl bg-stone-100/80 px-6 py-16`の大型カード）→ SUB PATHS（「相談のあとに、場所でも確かめる」という**Concierge前提の見出し**の下に、地図・神社一覧という2つの補助的発見リンク、小型カード）。
- **375/390/430px密度の実測**（実ブラウザ確認）: 375pxで、Hero単体の高さが約800px（`h1`のy座標184px、SUB PATHS見出しのy座標981.5px）— **Concierge Hero自体が1ビューポート以上を占め、CTAボタンでさえ初回ビューポート下端でほぼ見切れる**。ドキュメント全体の高さは1438px。
- **2つ目の製品エントリー追加が初回ビューポートを圧迫するか**: **既に圧迫されている状態が前提**。Concierge Hero単体で既に375pxの1ビューポートを超えているため、Compassをどこに置いてもCompass自体が「初回ビューポート内」に収まることは無い（Concierge Heroの高さを削らない限り）。これは今回の変更が新たに生む問題ではなく、既存Home Heroの高さに起因する既存特性であり、Hero自体の再設計はスコープ外（"Do not redesign Concierge or Compass internals"）。したがって目標は「初回ビューポートに両方を詰め込む」ことではなく、「Concierge Heroの直後、SUB PATHSより前に、迷わず発見できる形でCompassを提示する」こととする。
- **補足**: `HomeGoshuinFeedSection.tsx`・`HomeRankingSection.tsx`が`features/home/components/`に存在するが、`HomeMainClient.tsx`を含むどこからも参照されていない（未使用・死んだコード、本監査の対象外）。

## 2. Product Entry Responsibility

| | Home上での問い | 明確さ | 重複の有無 |
|---|---|---|---|
| Concierge | 「今、何について悩んでいますか？」 | 既存Hero自体が「今の気持ちを少しだけ書く」という具体的なプロンプトで既に体現している。明確。 | - |
| Compass | 「今月、どちらへ動いてみたいですか？」 | 現状Home上に存在しないため未評価。追加するコピー（Section 3）で体現できるか検証する。 | Conciergeの「悩み」とCompassの「今月・方向」は起点が異なり（相談内容 vs 時間・方位）、重複しない。 |

両者は「検索モードの選択」（例:キーワード検索 vs 条件検索）のような同質な選択肢としてではなく、**起点そのものが異なる別の入口**として提示する必要がある。既存Concierge Heroの体験の質（今の気持ちをすぐ書き始められる）と、追加するCompassカードの体験の質（今月の方向をすぐ見に行ける）が、文言レベルで並列比較されないよう注意する（Section 4で詳述）。

## 3. Entry Copy評価

| 項目 | Concierge候補 | Compass候補 |
|---|---|---|
| Title | 相談から探す | 今月から探す |
| Description | 悩みや願いから、今のあなたと接点のある神社を見つけます。 | 今月の流れと方向から、参拝のきっかけを見つけます。 |
| CTA | 相談して探す | 参拝コンパスを見る |

**評価**:
- **明確さ**: 両方とも1文で製品の起点を説明できており、専門用語（九星気学等）を含まない。合格。
- **375px文字数**: Title最大6文字、Description最大24文字程度、CTA最大8文字 — いずれも375px幅で折り返し1〜2行に収まり、問題なし（実装後に実測、Section 10参照）。
- **重複**: 「探す」という動詞をタイトルで共有しているが、修飾語（相談から／今月から）が明確に異なる起点を示しており、実質的な重複ではない。
- **断定的表現**: いずれのコピーにも「必ず」「絶対」等の断定的語彙は無い。Compass側コピーは「今月の流れと方向から」という既存Runtime Contractの表現（「今月の流れを参考に」）と整合しており、確定的な予言表現になっていない。
- **世界観整合**: 両コピーとも既存Home/Conciergeの文体（体言止めを避けた平易な敬体、短文）と一致している。

**採用方針**: **ConciergeについてはHome上に新しいカード・新しいコピーを追加しない**。既存Hero自体が既に「相談から探す」に相当する体験（テキストエリア＋CTA）を直接提供しており、候補コピーのタイトル・説明文だけを別途カードとして追加すると、Home上にConciergeへの入口が「Hero本体」と「新しい小カード」の2つ重複して存在することになり、Section 6の「説明文の重複を作らない」「無駄なカードの壁を作らない」という要件に反する。Compass側のコピー（Title/Description/CTA）はそのまま採用する。

## 4. Visual Hierarchy

| Option | 内容 | 評価 |
|---|---|---|
| A. Equal primary cards | ConciergeとCompassを同格の2カードとして提示 | 現状のConcierge Heroは単なるリンクカードではなく、テキストエリア・チップ・条件追加を含む完成されたインタラクティブ入口である。Compass側を同格にするには、Compassの入力（目的・出発地点・生年月日）もHomeへ埋め込む必要があり、`/compass`page自体の機能をHomeへ複製することになる。実装コスト・保守コスト・重複リスクが大きく、"Do not redesign Concierge or Compass internals"の精神にも反する。**不採用**。 |
| B. Concierge primary + Compass secondary | Concierge Heroを現状維持、CompassをHero直後に独立したセクションとして追加（SUB PATHSより格上、ただしHero本体よりは軽量） | 現状の非対称な実装（Concierge=埋め込み型、Compassは`/compass`への導線のみ）に最も忠実。実装は「1カード追加」のみで完結し、Concierge/Compass双方の内部に触れない。**採用**。 |
| C. Two tabs/modes | ConciergeとCompassをタブ切り替えで提示 | Product Contractが明示的に否定する構図（"CompassはCompat Modeの拡張ではない"、"ConciergeとCompassは別の製品体験"）に近づく。タブは「同じ画面の2つのモード」という印象を与え、Product Boundaryを曖昧にするリスクがある。**不採用**。 |
| D. One primary CTA + secondary discovery link | Concierge Heroのみを主CTAとし、Compassは控えめなテキストリンク1本 | Compassが「サブパス扱いの地図/一覧リンク」と同列に埋没し、独立した製品としての発見可能性が弱まる。QA（`compass-full-experience-qa.md`）が確認したCompassの製品としての完成度に見合わない扱いになる。**不採用**（Bより弱い） |
| E. 既存パターンの転用 | 既存の「SUB PATHS」カード（`HomeNearbySection`等）と同型のカードをCompass用に1つ追加し、Hero直後・SUB PATHSより前の独立位置に配置 | 実質的にBの具体的な実装形。既存カードコンポーネントの視覚言語（`rounded-3xl border border-stone-200/25 bg-white/60 px-5 py-7`、タイトル＋説明＋pill CTA）をそのまま流用でき、新しいトークン・新しい視覚パターンを一切発明しない。**採用（Bの実装として）**。 |

**結論**: B（Eの具体形として実装）。ConciergeのHero（`text-3xl`の`h1`、大型カード、テキストエリア）はそのまま、直後に独立したセクション見出し＋Compassカード（`HomeNearbySection`と同型の中型カード、ただしSUB PATHSの傘下ではなく独立した見出しを持つ）を追加する。

この配置は、Product Contract Section 5の「Compassの方位前面化はCompassという製品の中でのみ許可される。Concierge内での方位前面化制約は不変」という既存境界にも抵触しない — Home上のCompassカードは方位情報そのものを表示せず、製品への入口（タイトル・説明・CTA）のみを提示する。

## 5. Navigation Contract

- **Home → Concierge**: 既存のまま（`/concierge`または`/concierge?theme=...`）。変更なし。
- **Home → Compass**: 新規追加する`Link href="/compass"`。クエリパラメータは付与しない（Compassは`/compass`到達後にpurpose/origin/birthdateをその場で収集する設計であり、Home側で先読みして渡すべき状態は無い — Runtime Contractの入力責務分離とも整合）。
- **戻り導線**: ヘッダーの`HomeLogoLink`（`<Link href="/">`）が全ページ共通でHomeへ戻る導線として機能することを確認済み（`apps/web/src/components/layout/HomeLogoLink.tsx`）。ブラウザの戻るボタンも標準のNext.js App Router挙動でHomeへ正しく戻る。追加のロジックは不要。
- **状態の非共有**: Compassカードのリンクは`/compass`への単純な`<Link>`であり、Concierge側のセッション状態（`sessionState`等）・クエリパラメータのいずれも共有・伝播しない。Compass側もHome側の相談テーマ状態を一切参照しない。両者は完全に独立した状態を持つ。
- **クエリパラメータhack**: 不要と判断。追加しない。

## 6. Mobile First View

- 375pxで、Concierge Hero自体が既に1ビューポートを超えるため、「両方を1画面内で理解できる」ことは物理的に不可能（Section 1で確認済み、既存Heroの高さに起因）。
- ただし「過度なスクロールなしで両方を理解できる」という基準は、**Concierge Hero → （1回のスクロール）→ Compassカードが即座に視界に入る**という配置であれば満たせる。SUB PATHSのさらに先まで探させる必要はない。
- Compassカードの説明文はHomeHeroの説明文（「迷っていることを一言にすると...」）と文体・長さを揃え、重複する語彙（「見つけます」以外）を避ける。
- 主要アクション（「参拝コンパスを見る」）はカード内で唯一のCTAとして視認できる高さに収める。
- 「カードの壁」を作らない: Compassカードは1枚のみ追加し、SUB PATHSの2枚と合わせても合計3枚の発見カードに留める（過剰な選択肢の羅列にしない）。

## 7. World-View Consistency

- 新規Compassカードは`HomeNearbySection.tsx`と同一のクラス構成（`rounded-3xl border border-stone-200/X bg-white/Y px-5 py-7`、`text-sm font-medium text-stone-800`のタイトル、`text-xs text-stone-500`の説明、`rounded-full border border-stone-200/55 bg-stone-50/80`のpill CTA）を流用する。新しい色・新しいradius・新しいshadowは一切導入しない。
- Concierge Hero（`stone-100`背景の大型カード、内省的なトーン）と、追加するCompassカード（白背景の中型カード、行動を促すトーン）の対比は、Concierge=内省・意味、Compass=方向・行動という既存の世界観コントラスト（Phase 6 QA「Compass should feel more directional than Concierge, not more magical」）を、色を変えずにカードサイズ・文言のみで表現する。
- CTAボタンの色は、既存SUB PATHSカードのCTA（`stone`系の控えめなボタン）と同じ視覚的重みに揃える。Compass内部ページ（`/compass`）で使われる`--kt-color-action-primary`（emerald強調）をHome上のカードCTAにそのまま適用すると、SUB PATHSの他カードより浮いて見え、Section 8のPremium neutrality要件（過度な強調＝将来のPremium訴求と誤解されるリスク）にも触れかねないため、Home側のCTAは既存カードと同じ`stone`トーンのpillボタンとする。

## 8. Premium Neutrality

Premiumバッジ・ロック表現・Compassの非表示・課金導線のいずれも追加しない。Compassカードの視覚的重みはConcierge Hero（既存、埋め込み型）より軽いが、これはPremium階層を示すものではなく、既存実装の非対称性（Conciergeが埋め込み型、Compassがページ遷移型）を反映した結果に過ぎない。SUB PATHS（地図・一覧）とも明確に区別された独立したセクション見出しを持たせることで、「Compassが単なるユーティリティリンクではなく製品」であることを示す。

## 9. Implementation Decision

**HOME ENTRY READY FOR IMPLEMENTATION**

**最小実装スコープ**:
- 新規コンポーネント: `apps/web/src/features/home/components/HomeCompassSection.tsx`（`HomeNearbySection.tsx`と同型、`/compass`へのリンクカード）。
- `HomeMainClient.tsx`: `HomeHero`の直後・SUB PATHSセクションの前に、独立した見出し＋`HomeCompassSection`を追加。既存Hero・SUB PATHSの内容は一切変更しない。
- Backend/API/DB/Migration/Recommendation/Compass Runtimeへの変更なし。

## 10. Implementation Scope（実施結果）

- [x] Concierge向けの新規Home導線は追加しない（既存Heroで充足、Section 3の結論通り）。
- [x] Compass向けのHome導線を追加。
- [x] 既存Home内容（Hero・SUB PATHS）を変更せず保持。
- [x] 説明文の重複を作らない（Compassカードの文言はHome Hero・`/compass`page双方と語彙が重ならないよう調整）。
- [x] `/concierge`遷移の確認（既存のまま、影響なし）。
- [x] `/compass`遷移の確認（新規リンクが実際に`/compass`へ遷移することを実ブラウザで確認）。
- [x] 375/390/430pxでの確認。
- [x] component/navigationテストを追加。
- [x] Premium/Analyticsには一切触れていない。

実装の詳細・実測結果は本PRのコミット本文および最終回答に記載する。

## 11. Full Experience Gate（実施結果）

Home→Concierge、Home→Compass→方向結果→Recommendation→Shrine Detailの再検証結果、および最終Gate判定は本PRのコミット本文・最終回答に記載する。
