# KAMI MUSUBI 全体ユーザー導線監査

> **Status: Draft(監査記録)**
>
> 本ドキュメントは、KAMI MUSUBIのMobile／Expo Webを中心としたユーザー導線を、実装・テスト・現行の正本文書に基づいて復元した監査記録である。
>
> 最終的なUI方針・機能削除・優先順位の決定は行っていない。本書は判断材料の整理であり、判断そのものは母艦(プロジェクトオーナー)へ差し戻す。

---

## 1. Status

Draft(監査記録)。本書自体は正本(Active仕様書)ではない。今後、母艦の判断を経て`docs/product/`または`docs/core/`配下の正本文書へ反映される可能性があるが、本書だけでは仕様変更の根拠にならない。

## 2. 監査目的

KAMI MUSUBIの現行リポジトリ全体(Mobile／Expo Web中心)を確認し、以下を比較可能な状態に整理する。

- ホーム画面の入口
- コンシェルジュ導線
- 神社一覧・検索導線
- 地図導線
- 人気神社導線
- 神社詳細への遷移
- 記録導線
- マイページ導線
- Premium導線
- ログイン要求と認証後復帰
- 外部地図・経路案内
- 各導線の重複、競合、孤立、延期候補

UIを変更すること、最終方針・機能削除・優先順位を決定することは目的に含まない。

## 3. 対象commit

- ブランチ: `audit/mobile-user-flow-inventory`
- 調査開始時点のcommit SHA: `0610dfd93463346c84dac0b669914392a4cd9305`(develop、`docs/audit/web-map-tile-provider-selection.md`追記PR #2174マージ直後)
- 本書の記述はすべてこのコミット時点のコード・文書に基づく。以降にdevelopへマージされた変更は反映していない。

## 4. 監査対象

- `apps/mobile`(Expo Router、Native/Expo Web両対応)の全画面・導線
- `apps/mobile`が依存する`packages/shared`
- Backendのうち、Mobile導線が直接呼び出すAPI(Concierge chat、Shrine detail、Visits、Reflections等)の契約レベルの確認
- `docs/core`・`docs/product`・`docs/knowledge`・`docs/analytics`・`docs/audit`・`docs/mobile`配下の関連文書の分類
- ルート`README.md`の記述とMobileの実態の整合性
- Analytics(`apps/mobile`のtrack呼び出し全件、および比較参考として`apps/web`のイベント名一覧)

## 5. 除外範囲

- `apps/web`(Next.js)の画面別CTA・状態の詳細監査(本書では構造確認とREADME記載内容の引用に留める。`apps/web`は`apps/mobile`とは別サーフェスであり、README.mdの「主要画面説明」は`apps/web`側の記述である点に注意)
- Backendの実装詳細(Concierge chatエンドポイントの契約レベル確認は実施したが、スコアリングロジック・推薦アルゴリズム内部・DBスキーマ等の深掘りは対象外)
- 最終UI方針・機能削除・優先順位の決定(本書は監査であり決定文書ではない)
- 実機・エミュレータでの動作確認(過去のセッションでiOS Simulatorの操作が不安定だった経緯があり、本書はコード・テストの静的確認に基づく。実機確認が必要な項目は「未確認」として明記する)

## 6. リポジトリ構造

`find`・`grep`・実在するpackage設定・route構造から確認した事実のみを記載する。

### 6.1 root

```text
apps/            → mobile, web
backend/         → Django backend
packages/shared/ → Mobile/Web共有ロジック(UI以外)
docs/            → 設計・運用ドキュメント
.github/workflows/
README.md
package.json
pnpm-workspace.yaml
```

### 6.2 `pnpm-workspace.yaml`(root、事実)

```yaml
packages:
  - "apps/*"
  - "!apps/mobile"
  - "packages/*"
  - "backend"
```

`apps/mobile`はrootのpnpmワークスペースから明示的に除外されている。`apps/mobile`は独自の`pnpm-lock.yaml`を持つ独立したワークスペースであり、CI(`.github/workflows/mobile-ci.yml`)は`pnpm install --frozen-lockfile --ignore-workspace`で個別にインストールする。

### 6.3 `packages/shared/`(事実)

```text
directionAccessibility.ts
directionAnalytics.ts
directionAnalyticsForbiddenKeys.json
directionAnalyticsQuality.ts
directionReference.ts
location.ts
recommendationReasonDisplay.ts
userOrigin.ts
```

Mobile/Web間で共有されるのは「方位分析」「推薦理由表示」「位置情報」まわりのロジックのみで、UIコンポーネントは共有されていない。

### 6.4 `apps/mobile`(Expo Router)

`apps/mobile/app/`配下がRoute定義(ファイルベースルーティング)。詳細は8節・9節。

主要設定ファイル:

- `apps/mobile/app.json` — `expo.name: "KAMI MUSUBI"`, `scheme: "ai-sanpai-navi"`, `owner: "morietsu"`, `extra.eas.projectId`あり。ドメイン設定の記載なし。
- `apps/mobile/eas.json` — `build.development/preview/production`の3プロファイル、各`environment`フィールドでEAS Environmentsと連携(`docs/audit/web-map-tile-provider-selection.md`24節で確認済み)。root直下に`eas.json`は存在しない(`apps/mobile/eas.json`のみ)。
- `apps/mobile/package.json` — `"deploy": "npx expo export -p web && npx eas-cli@latest deploy"`。Web版はEAS Hosting経由、Vercelではない。

### 6.5 `apps/web`(Next.js、事実確認のみ、深掘りは対象外)

`apps/web/src/app`配下に、`apps/mobile`とは独立した以下のRouteが実在する(構造確認のみ):

```text
/、/auth/login、/auth/register、/billing/{cancel,manage,success,upgrade}、
/concierge、/concierge/full、/consultation、/debug/*、/favorites、
/g/[username]、/goshuin、/goshuin/new、/goshuins、/goshuins/public、
/login、/map、/media/[...path]、/mypage、/mypage/tests、/navi/[id]
（以降未列挙分あり、本書では構造の実在確認のみ）
```

**重要な事実**: root`README.md`の「主要画面説明」節(376行目〜)が記述しているトップページ(`/`)・地図ページ(`/map`)・神社詳細ページ(`/shrines/[id]`)・コンシェルジュページ(`/concierge`)・マイページ(`/mypage`)・お気に入りページ(`/favorites`)は、**すべて`apps/web`(Next.js)側のRouteである**。`apps/mobile`側の画面ではない。両者は別のRoute体系・別の実装を持つ別サーフェスであり、本書が主対象とする`apps/mobile`の画面一覧は8節・9節に別途記載する。

README.md該当箇所の引用(事実):

> ### 地図ページ（`/map`）
>
> - 探索用の補助機能
> - 近くの神社を地図で確認するためのページ
> - 主導線ではなく、補助的に利用する

これは`apps/web`の`/map`についての記述であり、`apps/mobile`のSearch画面の地図とは別実装である。ただし、**同じKAMI MUSUBIプロダクトの中で「地図は補助機能」という設計思想が既に明文化されている**という事実は、12節の案A/B/C比較において参考情報として扱う(Web(Next.js)側の記述であることを明記した上で)。

### 6.6 README.mdとMobileの状態(重要な発見・事実)

root`README.md`(322行目〜)は次のように明記している(引用):

> ## Mobile（WIP / 休眠運用）
>
> `apps/mobile/` は未着手〜プロトタイプ段階のため、通常は workspace から除外して運用します。
>
> ### 休眠中の目印
>
> - `apps/mobile/.hibernated`
>
> ### 復帰手順（最小）
>
> 1. `pnpm-workspace.yaml` から `!apps/mobile` を外す
> 2. `apps/mobile` で `pnpm install`（必要なら `expo install`）
> 3. `expo start` / `expo run:*` を実行
> 4. Dependabot/CI対象の見直し

事実確認:

- `apps/mobile/.hibernated`ファイルは実在する(空ファイル)。
- `pnpm-workspace.yaml`は現在も`!apps/mobile`を含んでおり、README記載の「復帰手順1」は実行されていない。
- 一方で、`.github/workflows/mobile-ci.yml`は`apps/mobile/**`変更時に毎回起動する現行のCI設定として存在し、直近(2026-07-22)もdependency bump(`actions/checkout`更新)を受けている。
- `apps/mobile`のgit履歴には、本書の直前まで(このセッション内で作成されたPRを含め)継続的な機能追加コミットが存在する(神社地図、Home→Search導線、選択同期、MapLibre Web地図等)。
- `README.md`自体は2026-07-16に「Product現行正本文書を移動し参照と入口を統一 (#2042)」というPRで更新されており、古い放置文書ではない。

**この時点で確認できる事実の矛盾**: README.mdは「Mobileは未着手〜プロトタイプ段階で休眠運用」「通常はworkspaceから除外」と明記し、復帰手順が実行されていないことを示す一方、`apps/mobile`は独立したpnpmワークスペースとして専用CIを持ち、継続的に活発な機能開発を受けている。この矛盾は「文書が古い」のか「休眠運用の定義自体がREADMEの想定と異なる運用へ変化した」のかを、本書のみでは判断できない。**この矛盾の解消は母艦判断事項とする(26節)。**

さらに、`docs/core/roadmap.md`(Status: Active)は次のように記述している(事実、引用):

> ## Phase 8: Mobile展開
>
> ### ゴール
>
> Web版で検証済みの体験をモバイルへ展開する。
>
> ### 前提条件
>
> - Web版の主要ファネルが完成している
> - 継続利用の兆候が確認できる
> - Premium価値が検証できている
> - Web / Mobileでbackend正本を共有できる

および:

> ## 現在の実装順序
>
> ### 主フェーズ
>
> ```text
> Recommendation品質改善
> ↓
> Shrine Data Quality
> ↓
> Release Readiness
> ↓
> Mobile本番配布準備
> ```

**文書間の不一致(事実)**: `docs/core/roadmap.md`(Active)は「Mobile展開」を前提条件付きの将来フェーズ(Phase 8)として位置づけつつ、同時に「現在の実装順序」の主フェーズ末尾に「Mobile本番配布準備」を掲げている。root`README.md`はMobileを「休眠運用」と明記している。この2つの正本(または準正本)級文書の間で、Mobileの現在地についての記述が一致していない。**いずれが現状を正しく表しているかを本書は判定しない**。実態としては、`docs/core/roadmap.md`の「Mobile本番配布準備」という表現の方が、直近のコミット履歴(活発な機能追加)と整合的であるように見えるが、これは観察に基づく所見であり断定ではない。

### 6.7 docs配下の全体構成(事実)

```text
docs/analytics/  docs/audit/  docs/ci/  docs/concierge/  docs/core/
docs/design/     docs/infra/  docs/knowledge/  docs/llm/  docs/meaning-layer/
docs/migration-audit/  docs/mobile/  docs/ops/  docs/product/  docs/runbooks/
docs/triage/  docs/ui/
```

`docs/audit/`配下だけで80件超のファイルが存在する。本書はこのうち、Mobile導線に直接関連する範囲のみを7節で分類する。

## 7. 文書の正本分類

各文書の「Status」は、原則としてその文書自身のヘッダー、または既存のメタ分類監査文書(`docs/audit/docs-directory-consistency-audit.md`、`docs/audit/core-document-responsibility-audit.md`、`docs/audit/product-document-responsibility-audit.md`、`docs/audit/analytics-document-responsibility-audit.md`、`docs/audit/archive-final-classification.md`、`docs/audit/root-docs-classification-audit.md`)の記載を根拠とする。本書独自の判断は行っていない。

### 7.1 docs/core/

| 文書 | Status | 一言要約 | コード照合 |
| --- | --- | --- | --- |
| `docs/core/README.md` | Active | core文書全体の入口 | 未照合(メタ文書) |
| `docs/core/architecture.md` | Active | システム全体構造・責務分離 | 一致(委譲先文書の実在を確認) |
| `docs/core/roadmap.md` | Active | 開発フェーズ・実装順序 | 6.6節で不一致を記録 |
| `docs/core/concierge-spec.md` | Active | Concierge入力・API基本契約 | 一致(バックエンドview実在確認、11節で詳細) |
| `docs/core/meaning-layer.md` | Active | Meaning Layerの思想・非断定原則 | 未照合(思想文書) |
| `docs/core/auth-flow.md` | Reference | 認証画面遷移・returnTo補足仕様 | 一致(Web側`/auth/login`等の実在確認) |
| `docs/core/authentication-flow.md` | Active | Web認証アーキテクチャの正本(auth-flow.mdとは責務分離、統合されていない) | 一致 |

### 7.2 docs/product/

| 文書 | Status | 一言要約 | コード照合 |
| --- | --- | --- | --- |
| `docs/product/README.md` | Active | product文書の入口・読む順番 | 未照合(メタ文書) |
| `docs/product/concierge-first.md` | Archive | Concierge First初期設計 | 対象外(明示的に非現行) |
| `docs/product/concierge-first-final-spec.md` | Active | Concierge First統合正本 | **一部不一致**(11.5節で詳述) |
| `docs/product/concierge-first-wireframe.md` | Archive | 初期ワイヤーフレーム | 対象外 |
| `docs/product/concierge-entry-final-wireframe.md` | Reference | ConciergeEntry画面構成 | 未照合 |
| `docs/product/home-hero-final-wireframe.md` | Reference | Home Hero画面構成 | 未照合 |
| `docs/product/mobile-bottom-navigation.md` | Reference | Mobile下部5タブ構成案 | **明確に不一致**(下記) |
| `docs/product/visit-reflection-flow.md` | Active | Visit→Reflection→次相談の体験責務 | 15節で「次相談への接続」が未実装である点を記録 |
| `docs/product/premium-experience.md` | Active | Free/Premium体験境界 | 16節で照合 |
| `docs/product/billing-paywall.md` | Active | Billing状態・Paywall表示原則 | 未照合(原則文書) |
| `docs/product/shrine-detail-v3-design.md` | Active | Shrine Detail v3設計 | Web側route実在確認のみ |
| `docs/product/shrine-detail-layer.md` | Active | Public/Context/Personal情報レイヤー | Web側route実在確認のみ |
| `docs/product/shrine-detail-meaning-layer.md` | Reference | 意味レイヤー表示順原則 | 未照合 |

**`docs/product/mobile-bottom-navigation.md`の明確な不一致(事実)**: この文書は自身のヘッダーで既に次のように開示している(引用):

> 現行実装では...4タブを表示しており、本書が定義する5タブ構成...とは一致していない

コード照合: `apps/mobile/app/_layout.tsx`は可視タブとして`index`(ホーム)・`concierge/index`(相談)・`records/index`(記録)・`mypage/index`(マイページ)の**4タブのみ**を登録している。文書自身が既に不一致を認めており、本書もこれを踏襲する。

### 7.3 docs/audit/(Mobile導線関連の抜粋)

| 文書 | Status | 一言要約 |
| --- | --- | --- |
| `docs/audit/mobile-release-readiness-audit.md` | Archive | Mobileリリース前チェックリスト(過去時点) |
| `docs/audit/mobile-concierge-first-route-design.md` | Status不明(未分類) | Home/Concierge/詳細のConcierge First適合監査 |
| `docs/audit/mobile-shrine-detail-web-parity.md` | Status不明(未分類) | Web/Mobile Shrine Detail情報構造比較 |
| `docs/audit/mobile-web-concierge-ui-quality.md` | Status不明(未分類) | Web/Mobile Concierge結果表示品質比較 |
| `docs/audit/premium-plan-design.md` | Archive | Premium長期コンセプト設計(将来ビジョン) |
| `docs/audit/premium-card-matrix.md` | Archive | Access Tier別カード表示設計 |
| `docs/audit/premium-retention-strategy.md` | Archive | Premiumリテンション戦略 |
| `docs/audit/web-mobile-experience-parity.md` | Status不明(未分類) | Web/Mobile主要10画面の体験差(2026-07-22付、Mobileは静的コード読解のみで確認と自己申告) |
| `docs/audit/web-mobile-recommendation-display-parity.md` | Status不明(未分類) | 推薦API統一後のWeb/Mobile表示整合監査 |
| `docs/audit/web-search-map-library-selection.md` | (本セッションで作成、比較監査。最終採用は未決定) | Google Maps vs MapLibre比較 |
| `docs/audit/web-map-tile-provider-selection.md` | (本セッションで作成、比較監査+運用手順追記。最終採用は未決定) | タイル提供元比較・EAS運用手順 |

**注記**: `docs/audit/premium-plan-design.md`・`docs/audit/premium-retention-strategy.md`は、より古いメタ文書`archive-final-classification.md`ではReferenceと記載されているが、より新しい`docs/audit/premium-reference-consolidation-audit.md`がArchiveへ再分類しており、各文書自身のヘッダーも現在Archiveとなっている。メタ文書間でも分類の更新にタイムラグがあることが確認できる。

**地図/検索機能を参照する文書の全件確認(事実)**: `docs/product`・`docs/core`・`docs/knowledge`・`docs/analytics`配下を`ShrineSearchMap`・`MapLibre`・`selectedShrineId`で検索した結果、**該当文書は0件**。地図/検索機能(`ShrineSearchMap.web.tsx`/`.native.tsx`、`lib/shrineMap.ts`、Home→Search導線)は、本セッションで作成した2件の`docs/audit/`比較監査文書以外、いかなるProduct/Core/Knowledge/Analytics正本文書からも参照されていない。

### 7.4 docs/mobile/

| 文書 | Status |
| --- | --- |
| `docs/mobile/authenticated-api-client-design.md` | Archive |
| `docs/mobile/cta-radius-audit.md` | Archive |
| `docs/mobile/design-system-audit.md` | Archive |
| `docs/mobile/direction-accessibility-device-check.md` | Status不明(未分類、実機確認チェックリスト) |
| `docs/mobile/mobile-web-parity-audit.md` | Archive |
| `docs/mobile/route-cleanup-audit.md` | Archive(「現在のRoute構成・Navigation・Layoutは`apps/mobile/app/`を正本とする」と自己申告) |
| `docs/mobile/route-structure-audit.md` | Archive(同上) |

`docs/mobile/route-cleanup-audit.md`・`route-structure-audit.md`はいずれもArchiveであり、「現行仕様判断には使用しない」「現在のRoute構成はコードを正本とする」と明記している。本書の8節・9節はこの指示に従い、コード(`apps/mobile/app/`)を直接確認して作成した。

**なお、`docs/mobile/search-map-flow-device-check.md`という名称の文書は存在しない**(過去のPR指示書で「必要な場合のみ」作成候補として言及されていたが、実際には一度も作成されていない)。

## 8. 全画面一覧

`apps/mobile/app/`配下の全Routeファイルを直接確認した(推測ではなくfind/読解による)。`apps/mobile/app/_layout.tsx`のTabs登録:

- 可視タブ(下部4タブ): `index`(ホーム)、`concierge/index`(相談)、`records/index`(記録)、`mypage/index`(マイページ)
- 非可視Route(`options={{ href: null }}`、プログラム的遷移でのみ到達): `journey/index`、`premium/index`、`favorites/index`、`goshuin/index`、`goshuin/upload`、`visit-history/index`、`reflection-history/index`、`consultation-history/index`、`recently-viewed/index`、`profile/index`、`search/index`、`shrines/[id]`、`ranking/index`、`login`

全18画面の詳細(責務・CTA・遷移元/先・認証/Premium要否・空/エラー状態・Analytics・到達可否)は9節の一覧表、および10〜17節の個別導線監査を参照。ここでは「実装として存在するがユーザーが到達できない画面」を先に明示する(事実):

**孤立(在庫はあるが到達経路がない)画面**: `/visit-history`、`/reflection-history`、`/consultation-history`、`/recently-viewed`、`/ranking`の5画面。`apps/mobile/app`・`apps/mobile/components`全体を`router.push`/`router.replace`/`Link`で検索した結果、これら5画面へ遷移する箇所はコード中に一切見つからなかった(`_layout.tsx`でのRoute登録のみ)。特に`/recently-viewed`(最近見た神社)は`/records`の3カード(ご縁の歩み・保存した神社・御朱印)のいずれにも含まれておらず、`/ranking`も同様にどのタブ・どの画面からもリンクされていない。Deep Link経由以外での到達手段が現状存在しない。

## 9. Route一覧

| Route | 実装ファイル | Tab登録 | 現在ユーザーから到達可能か |
| --- | --- | --- | --- |
| `/` | `app/index.tsx` | 可視(ホーム) | 可能(初期画面) |
| `/concierge` | `app/concierge/index.tsx` | 可視(相談) | 可能(タブ、Homeから) |
| `/search` | `app/search/index.tsx` | 非可視 | 可能(Homeの「神社を地図・一覧から探す」) |
| `/records` | `app/records/index.tsx` | 可視(記録) | 可能(タブ) |
| `/mypage` | `app/mypage/index.tsx` | 可視(マイページ) | 可能(タブ) |
| `/premium` | `app/premium/index.tsx` | 非可視 | 可能(マイページの「Premium」カード) |
| `/favorites` | `app/favorites/index.tsx` | 非可視 | 可能(記録の「保存した神社」) |
| `/goshuin` | `app/goshuin/index.tsx` | 非可視 | 可能(記録の「御朱印」) |
| `/goshuin/upload` | `app/goshuin/upload.tsx` | 非可視 | 可能(御朱印画面のCTA) |
| `/journey` | `app/journey/index.tsx` | 非可視 | 可能(記録の「ご縁の歩み」、ログイン必須) |
| `/profile` | `app/profile/index.tsx` | 非可視 | 可能(マイページの「プロフィール」) |
| `/login` | `app/login.tsx` | 非可視 | 可能(AuthPromptの「ログインする」) |
| `/shrines/[id]` | `app/shrines/[id].tsx` | 非可視 | 可能(7経路、14節) |
| `/visit-history` | `app/visit-history/index.tsx` | 非可視 | **不可(孤立、Deep Linkのみ)** |
| `/reflection-history` | `app/reflection-history/index.tsx` | 非可視 | **不可(孤立、Deep Linkのみ)** |
| `/consultation-history` | `app/consultation-history/index.tsx` | 非可視 | **不可(孤立、Deep Linkのみ)** |
| `/recently-viewed` | `app/recently-viewed/index.tsx` | 非可視 | **不可(孤立、Deep Linkのみ)** |
| `/ranking` | `app/ranking/index.tsx` | 非可視 | **不可(孤立、Deep Linkのみ)** |

`Link`コンポーネントの使用は`apps/mobile/app`・`apps/mobile/components`全体で0件(すべて命令的な`router.push`/`router.replace`)。

## 10. Home CTA一覧

`apps/mobile/app/index.tsx`の全CTAを抽出した(事実)。

| CTA(表示文言) | 遷移先 | 渡すstate/params | Analytics | 見た目上の優先度 | 未入力状態での挙動 |
| --- | --- | --- | --- | --- | --- |
| `↑`(送信ボタン、chatCard内) | `openConcierge()` → `/concierge`(query付き、または無し) | `q, theme, birthdate, plannedVisitDate, visitStyle, goriyaku, support`(URLSearchParams)。originは`setOriginSession(origin)`でURL外の**メモリ内シングルトン変数**に格納(`lib/originSession.ts`、永続化なし) | なし(track呼び出し0件) | 中(入力カード内の補助ボタン) | 全項目未入力でも遷移可能(バリデーションなし) |
| テーマチップ(6種、例「疲れを整えたい」) | なし(選択トグルのみ) | `selectedTheme`をローカルstateに保持 | なし | 中 | — |
| `条件を追加`/`条件を閉じる`(件数表示付き) | なし(アコーディオン開閉) | — | なし | 低 | — |
| `この相談からご縁を見る`(primaryCta) | `openConcierge()` → `/concierge` | 上記と同一 | なし | **高(gold背景の主CTA)** | 全項目未入力でも遷移可能 |
| `神社を地図・一覧から探す`(searchEntryCta、outline Button) | `openSearch()` → `/search` | なし(paramsなし) | なし | 中(outline、主CTAの下に配置) | — |

**事実として確認できること**: 主CTA「この相談からご縁を見る」はDOM順・視覚的重み(gold塗りつぶし背景)ともに、サブCTA「神社を地図・一覧から探す」(outline、枠線のみ)より優先度が高い配置になっている。この点はユーザーの指示にある仮説(主導線=相談、サブ導線=一覧/地図探索)と一致する。

**Concierge Firstとの整合の観点で確認できた不一致(11.5節で詳述)**: `docs/product/concierge-first-final-spec.md`は「HomeHeroが担当しないもの」として誕生日入力・ご利益選択本体・参拝スタイル詳細を明記しているが、実際のHome画面は`ConditionFieldsCard`(Concierge画面と同一コンポーネント)をアコーディオン内にそのまま埋め込んでおり、これらの入力項目をHome自身が保持している。

**別CTAとの重複**: 送信ボタン(`↑`)と主CTA「この相談からご縁を見る」は、いずれも同一の`openConcierge()`を呼ぶ完全に同じ機能の重複CTAである(input欄の下に1つ、画面下部に1つ)。

## 11. コンシェルジュ導線

`apps/mobile/app/index.tsx` → `apps/mobile/app/concierge/index.tsx` → Backend `/concierge/chat/` → 結果表示 → `/shrines/[id]`、をコードから復元した。

### 11.1 入力項目・必須/任意

Home・Concierge双方で入力可能な項目(`ConditionFieldsCard`共通コンポーネント使用): 相談文(自由入力)、テーマチップ、誕生日、参拝予定日、出発地点(現在地/都道府県/駅名等)、参拝スタイル、ご利益、補助条件文。**すべて任意**。Concierge画面の送信ガードは`if (!trimmed && !hasAnyCondition) return;`(`concierge/index.tsx`)のみで、テキストが空でも何らかの条件が1つでもあれば送信可能。テキストが空で条件のみある場合は、固定文字列`"条件から合う神社を知りたい"`が自動的にクエリとして送信される。

### 11.2 API payload / Runtime state

`POST {EXPO_PUBLIC_API_BASE_URL}/concierge/chat/`(認証不要、`fetch`直接呼び出し)。Django側解決: `backend/config/urls.py` → `temples/api_urls.py` → `temples/api/urls.py`の`concierge/chat/` → `concierge_chat_compat`(`backend/temples/api/views/compat.py`) → `ConciergeChatView`(`backend/temples/api_views_concierge.py`、`permission_classes = [AllowAny]`)。

payload概形(`ConciergeChatRequestPayload`、`concierge/index.tsx`):

```text
{ version: 1, mode: "need"(クライアント固定、backendで再導出),
  query, birthdate?, filters: {...}, goriyaku_tag_ids?, extra_condition?,
  visit_date?, location?: {lat,lng}, profile_context? }
```

**重要な事実**: Home画面で選択した現在地(`origin`)はURLクエリに含まれず、`setOriginSession()`によるメモリ内シングルトンでConcierge画面へ受け渡される。Concierge画面の`useLocalSearchParams`型は`originLat`/`originLng`もフォールバックとして宣言しているが、Home側は一度もこれをURLへセットしていない。

### 11.3 推薦件数・表示

Backend `_diversify_by_need(recommendations, limit=3)`(`backend/temples/services/concierge_chat.py`、デフォルトソート経路)により**上限3件**。全カードは同一の`ResultCard`コンポーネント・同一スタイルで表示され、**hero/他候補のような視覚的な差別化はない**(9節の一覧では「表示位置」として言及したが、実装上は横並びの同格カードである)。

### 11.4 神社詳細CTA・保存・経路案内

- 神社詳細CTA: 「この神社を詳しく見る」(primary Button) → `router.push({pathname: "/shrines/[id]", params: {id, recommendationReasonV4, reasonFacts, recommendationReasonDetail, actionSuggestionV4Preview}})`。4つの追加コンテキストparamsを渡す唯一の入口(14節で詳述)。
- 保存/お気に入り: **Concierge結果画面にはお気に入りボタンが存在しない**。`docs/core/concierge-spec.md`の「Concierge結果一覧ではfavorite操作を提供しない」という記述と一致する(MATCHES)。
- 経路案内: Concierge結果画面自体には経路案内ボタンはない。「次に取りやすい行動」プレビュー(`actionSuggestionV4Preview`)のボタンは`actionType: "route_open"`を持ちうるが、押下しても`trackActionEvent`(analytics)を呼ぶのみでナビゲーション・外部リンクは発生しない。実際の経路案内(Google Maps起動)は神社詳細画面(`/shrines/[id]`)の「地図で経路を確認する」ボタンのみが担う。

### 11.5 文書とコードの不一致(併記)

`docs/core/concierge-spec.md`(Active)との照合は概ね一致(mode/flow導出ロジック、favorite非提供)。一方、`docs/product/concierge-first-final-spec.md`(Active)との照合では以下の不一致を確認した:

| 文書の記述(引用) | コードの実際 | 判定 |
| --- | --- | --- |
| 「Home→Concierge遷移で渡すqueryはtheme(自然文として扱う)/openFilter」 | `theme`は6種の固定チップ値、自由文は別途`q`として送信。`openFilter`パラメータはコード中に0件 | 不一致 |
| 「HomeHeroが担当しないもの: 誕生日入力/ご利益選択本体/参拝スタイル詳細」 | Home画面は`ConditionFieldsCard`をアコーディオン内にそのまま埋め込み、これら全項目を直接保持 | 不一致 |
| 「ConciergeEntryが担当するもの: 未ログイン時の保存案内」 | Concierge画面にログイン関連のUI/文言は0件(grep結果) | 不一致 |
| 「ConciergeEntryが担当しないもの: 推薦結果表示」(Entry画面と結果表示が別責務という設計) | 実装は1画面(`concierge/index.tsx`)が入力編集と結果表示を兼任し、マウント時自動送信も行う | 不一致 |

これらはコードだけを見て「文書が間違っている」と断定するものではなく、**文書に記載された設計意図がその後の実装過程で変化した可能性**を示す事実の併記である。どちらを正とするかは母艦判断とする。

### 11.6 失敗時fallback・ログイン・Premium

- 失敗時: `errorMessage`固定文言「通信に失敗しました。前回の結果を表示したまま、もう一度相談できます。」。過去の結果は消去されない。
- ログイン要求: 推薦フロー自体は認証不要(`AllowAny`)。`trackActionEvent`のみ認証付きAPIを使うが、未認証エラーは握りつぶされ画面には影響しない。
- Premium差分: **Concierge画面にPremiumゲーティングのコードは存在しない**(grep 0件)。Backend側にはクォータ/`limitReached`/`remaining`フィールドが応答に含まれるが、**Mobile側の型定義・実装はこれらのフィールドを一切読み取っていない**。Premium上限に達した場合の挙動がMobile側に実装されているかは、この時点のコードからは確認できない(未確認)。

### 11.7 テスト

Concierge関連のテストは`apps/mobile/lib/__tests__/routerStructure.test.ts`のみで、Route登録の存在確認に留まる。`conditionPayload.ts`のpayload構築ロジック、Concierge画面のsubmitロジック、`/concierge/chat/`のレスポンス処理を検証するMobile側テストは存在しない。

## 12. Search／一覧導線

### 12.1 実装ファイル

`apps/mobile/app/search/index.tsx`(画面本体) / `apps/mobile/components/search/ShrineSearchMap.native.tsx` / `apps/mobile/components/search/ShrineSearchMap.web.tsx` / `apps/mobile/components/search/SelectedShrineMapCard.tsx` / `apps/mobile/lib/shrineMap.ts`。本セッション内の複数PR(develop取り込み済み、コミット`324a05ce`〜`c4e7c68d`)で実装。

### 12.2 selectedShrineIdの正本

`apps/mobile/app/search/index.tsx`の`useState<string | null>`が唯一の正本。`SelectedShrineMapCard`表示用の神社は`findShrineMapPointById(mapPoints, selectedShrineId)`(`lib/shrineMap.ts`)で導出。二重管理はない。

### 12.3 座標欠損神社・有効座標0件

`lib/shrineMap.ts`の`toShrineMapPoints`は、id/nameが揃っていれば座標が欠損・不正でも項目を除外せず`latitude: null, longitude: null`として一覧に残す。`hasValidCoordinates`で有効座標のみをMarker対象に絞り込む。有効座標0件でも一覧・選択・詳細遷移は維持される(実装済み、`lib/__tests__/shrineMap.test.ts`でテスト済み)。

### 12.4 style URL未設定・無効・provider通信失敗

`EXPO_PUBLIC_WEB_MAP_STYLE_URL`未設定時、Web版は地図を初期化せず「地図を読み込めないため一覧を表示しています。」を表示し一覧を維持する(`ShrineSearchMap.web.tsx`)。style読込失敗時も同一メッセージへ切り替わる(個別tile1件の失敗では切り替えない設計)。Native版はreact-native-mapsを常時使用するため、この分岐は**Web版のみに存在する**。

### 12.5 画面構造・地図が主役か補助か(事実、根拠付き)

`apps/mobile/app/search/index.tsx`のJSX上の縦方向の並び順(事実、コード読解に基づく):

1. `← 戻る`
2. Hero(見出し「神社を探す」/サブコピー)
3. 「検索条件」サマリーカード
4. **`地図で探す`セクション**(`mapSection`、見出しテキスト`"地図で探す"`) — 内部でloading/error/empty/ready状態を分岐し、readyかつ有効座標ありの場合に`<ShrineSearchMap>`と`<SelectedShrineMapCard>`を描画
5. `人気の神社`セクション(3件、`SHRINES`固定データ由来)
6. `神社一覧`セクション(座標を問わずAPIの全件、各カードに「地図で選択」ボタン付き)

**事実**: スクロール順・コンポーネント順としては「地図で探す」セクションが「人気の神社」「神社一覧」より**先に**配置されている。見出しの言語表現も「地図で探す」であり、地図が主入口であるかのような配置になっている。

**ただし実際の描画内容は環境依存である(事実)**:

- Native: `react-native-maps`による実地図とMarkerが常に表示される(コスト・provider設定は不要)。
- Web: `EXPO_PUBLIC_WEB_MAP_STYLE_URL`が設定されmap初期化に成功した場合のみ実地図。**未設定がデフォルト状態であるため、Web版の「地図で探す」セクションは現状、実質的に一覧UIとして機能している**(タイトル文言「地図を読み込めないため一覧を表示しています。」が示す通り)。

つまり、**配置順という見た目の事実としては地図(または地図の代替一覧)が一覧より先に来ている**が、**実際に地図として機能しているのはNativeのみで、Web版は現状(未契約状態)では見た目は先頭だが中身は一覧である**、という二重構造が事実として存在する。これは評価ではなく、コード分岐条件から直接確認できる事実である。

### 12.6 Marker・選択カード・一覧の同期

Native: 有効座標を持つ点のみMarker化。座標欠損分は地図下の補助リスト「位置情報のない神社」として選択可能。Web: fallback一覧すべてが選択可能で、選択状態を「選択中」ラベル+border色の両方で表現(色のみに依存しない)。いずれもMarker/一覧選択→`onSelect(id)`→`selectedShrineId`更新→`SelectedShrineMapCard`更新、という単一経路。

### 12.7 神社詳細遷移・戻る操作

`SelectedShrineMapCard`の「詳細を見る」、人気神社カード、神社一覧カードの3経路すべてが`/shrines/${id}`へ遷移(追加paramsなし、14節参照)。戻る操作は`router.canGoBack() ? router.back() : router.replace("/")`。

### 12.8 検索条件の保持・フィルター

`q`(キーワード)・`filters`(タグ、カンマ区切り文字列)をクエリパラメータとして受け取り、`SHRINES`固定データに対してテキスト一致・タグ一致でフィルタする。フィルタUI自体(検索窓・タグ選択UI)は`search/index.tsx`内には存在せず、**このスクリーンへ遷移する側(現状はHomeの「神社を地図・一覧から探す」ボタンのみ)が`q`/`filters`を渡す実装になっていない**(Home側の`openSearch`は無条件で`/search`へ遷移し、paramsを一切渡さない、10節参照)。つまり、フィルター機能はコードとして実装されているが、**現在到達可能な唯一の入口(Home)からは絶対に使われない状態**にある。

### 12.9 Analytics

`apps/mobile/app/search/index.tsx`・`ShrineSearchMap.native.tsx`・`ShrineSearchMap.web.tsx`・`SelectedShrineMapCard.tsx`いずれにも、analytics/track呼び出しは**0件**(全ファイルgrep済み)。Search画面への入口、地図の使用、Marker選択、一覧選択のいずれも計測されていない。

## 13. 地図導線

12.5節・12.6節と重複するため、ここでは地図固有の論点のみを補足する。

- **Mobile地図(Native)**: `react-native-maps`。常時稼働、外部費用は発生しない(Apple/Google純正地図SDK経由)。
- **Web地図**: MapLibre GL JS(本セッションでdevelop取り込み済み、コミット`c4e7c68d`)。`EXPO_PUBLIC_WEB_MAP_STYLE_URL`が未設定の間は一覧fallbackのまま。MapTiler Cloud等の商用タイル提供元契約が発生するのはこの変数を設定した時のみ(`docs/audit/web-map-tile-provider-selection.md`)。
- **外部地図・経路案内との関係**: Search画面の地図はあくまで神社を選ぶための地図であり、実際の参拝経路案内(Google Maps起動)は神社詳細画面(`/shrines/[id]`)の「地図で経路を確認する」ボタンが担う(`openDirections()`、`Linking.openURL`)。Search画面の地図とは別の、独立した外部連携である。
- Analyticsが0件である点は12.9節の通り。地図が実際にどれだけ使われているか(Marker選択率、一覧との使用比率)は**計測手段が存在しないため現状測定不能**という事実がある。

## 14. 神社詳細への合流経路

`apps/mobile/app/shrines/[id].tsx`(1115行)を全経路から検証した(事実)。

### 14.1 到達する7経路(すべて同一route形状)

| # | 遷移元 | 追加params |
| --- | --- | --- |
| 1 | `app/ranking/index.tsx`(孤立route) | なし |
| 2 | `app/favorites/index.tsx` | なし |
| 3 | `app/search/index.tsx`(`SelectedShrineMapCard`「詳細を見る」) | なし |
| 4 | `app/search/index.tsx`(人気の神社) | なし |
| 5 | `app/search/index.tsx`(神社一覧) | なし |
| 6 | `app/recently-viewed/index.tsx`(孤立route) | なし |
| 7 | `app/concierge/index.tsx` | **recommendationReasonV4, reasonFacts, recommendationReasonDetail, actionSuggestionV4Preview(4つのJSON/文字列params)** |

すべて`/shrines/${id}`(または同義の`{pathname: "/shrines/[id]", params: {id, ...}}`)という同一route形状に到達する。この点は一致している。

### 14.2 唯一の差分: コンシェルジュ経由だけが追加コンテキストを持つ

`shrines/[id].tsx`は`recommendationReasonV4`等のparamsが存在する場合のみ、以下を追加描画する(条件付きレンダリング、事実):

- 「① 今回の相談の整理」カード
- 「③ この神社で受け取る意味」カード
- 「④ 参拝するときの視点」カード
- 拡張版「参拝前にできること」(NEXT ACTION)ブロック

**7経路のうち6経路(ranking/favorites/search×3/recently-viewed)は、いずれもidのみを渡し、上記4項目のparamsを渡さない。** その結果、コンシェルジュ経由でのみ詳細画面はリッチな表示になり、他の6経路はすべて同一の汎用フォールバック表示になる。

### 14.3 Analytics sourceは経路によらず固定

`shrines/[id].tsx`は`trackShrineDetailView`/`trackShrineRouteOpen`のいずれも`source: "mobile_shrine_detail"`という**ハードコードされた固定値**を送信する(`lib/shrineInteractions.ts`の型は`"mobile_map"`/`"mobile_concierge_result"`/`"mobile_shrines"`という他候補値も型定義上は用意しているが、詳細画面自体からは一度も使われていない=未使用のunion member)。つまり、**7つの入口のどこから来たかは、Analyticsデータ上は一切区別できない**。

### 14.4 「共通合流地点」として整理できるか(事実の整理、評価は保留)

- Routeの一致という意味では、神社詳細は明確に単一の合流地点として機能している(事実)。
- ただし、表示内容(コンテキストの豊富さ)とAnalytics識別性の両面で、コンシェルジュ経由とそれ以外の経路の間に非対称性がある(事実)。
- 「神社詳細を独立した優先導線として扱わず、複数入口の共通合流地点として整理できるか」という問いに対しては、**Routeレベルでは既にそう整理されているが、コンテキスト伝播とAnalytics識別の両面ではまだ経路間で不均一である**、というのが事実に基づく回答である。断定的な良し悪しの評価は行わない。

## 15. 記録・Reflection導線

### 15.1 各画面の要約

| 画面 | 責務 | ログイン | Empty state |
| --- | --- | --- | --- |
| `/records` | ジャーニー/お気に入り/御朱印へのハブ | `journey`のみゲート | — |
| `/journey` | 相談・推薦・参拝・振り返りの統合タイムライン | **明示的にゲート**(未ログイン時`AuthPrompt`) | 「ご縁の歩みはまだありません」 |
| `/visit-history` | 参拝履歴(日付グループ) | 未ゲート(下記参照) | 「参拝履歴はまだありません」 |
| `/reflection-history` | 振り返り履歴 | 未ゲート(下記参照) | 「振り返りはまだありません」 |
| `/consultation-history` | 相談スレッド履歴(カードは非押下) | 未ゲート(下記参照) | 「相談履歴はまだありません」 |
| `/goshuin` | 御朱印ギャラリー(ローカルストレージ) | 不要(ローカル完結) | 「まだ記録はありません」 |
| `/favorites` | お気に入り一覧 | 不要(ローカルID+API解決) | 「お気に入りの神社はまだありません」 |
| `/recently-viewed` | 最近見た神社 | 不要(ローカル) | 「最近見た神社はまだありません」 |

### 15.2 未ログイン時の挙動に関する重要な事実

`/visit-history`・`/reflection-history`・`/consultation-history`の3画面は、画面コード自体には`isLoggedIn()`チェックや`AuthPrompt`がない。しかし内部で呼ぶ`listVisits()`/`listShrineReflections()`/`listConciergeThreads()`(各lib関数)は認証付きエンドポイントを叩いており、**エラーを全て握りつぶして空配列を返す**実装になっている(例: `catch (error) { ... return []; }`)。結果として、未ログインユーザーはこれら3画面で「ログインが必要です」ではなく、**通常の空状態(「まだありません」)を見る**。画面内に定義されているエラー状態(「〜を読み込めませんでした」)の分岐は、この経路では実質的に到達不能になっている。これは実装上の事実であり、意図した仕様か見落としかは本書では判定しない。

### 15.3 相談→参拝→記録→再相談は一本につながっているか(事実)

- 参拝記録(`onVisitDone`)・振り返り保存(`onSaveReflection`)はいずれも`apps/mobile/app/shrines/[id].tsx`内で完結し、保存後に画面遷移は発生しない(ボタンのラベルと見た目が変わるのみ)。
- `shrines/[id].tsx`内に`"concierge"`という文字列は1件も存在しない(grep結果)。
- 記録・履歴系9画面いずれにも、`/concierge`または`/`への遷移コードは存在しない(back-to-`/records`系の遷移のみ)。

**結論(事実)**: 「相談 → 参拝 → 記録 → 再相談」という循環は、**「再相談」の部分でコード上切れている**。参拝や振り返りを保存した後、新しい相談を始めるよう誘導する画面遷移・CTAは現状存在しない。

## 16. Premium導線

- 入口: `/mypage`の「Premium」カードのみ(「確認」ボタン → `/premium`)。
- `/premium`は状態表示(Free/Premium二値)のみで、機能比較表・プレビュー・ロック表示は存在しない(コードにそのようなUIは無い)。
- Checkoutは実装済み(Stripe、`createBillingCheckoutSession` → `Linking.openURL`で外部ブラウザへ、`AppState`復帰検知で状態再取得)。スタブではない。
- Concierge・Search・地図機能いずれにもPremiumゲーティングは存在しない(grep 0件、確認済み)。
- `docs/product/premium-experience.md`(Active)の「Premiumは地図の高機能化ではなく、パーソナル理由・履歴・比較・継続理解・保存/記録拡張を担う」という記述と、実装(地図機能に一切のPremium紐付けがない)は**一致している**(MATCHES)。
- Analytics: `premium_screen_view`/`premium_status_view`/`premium_upgrade_click`/`premium_checkout_started`/`premium_checkout_failed`/`premium_checkout_returned`/`premium_active`の7イベントが整備されている(18節)。

## 17. 認証導線

- ログイン画面: `/login`(ユーザー名+パスワード)。
- ログイン成功後は**常に`/mypage`へ固定遷移**。呼び出し元へ戻る仕組み(`returnTo`等)は一切実装されていない(コード上、`login.tsx`は`useLocalSearchParams`を呼んでいない)。
- ログイン要求は共通コンポーネント`AuthPrompt`(`apps/mobile/components/common/AuthPrompt.tsx`)経由の1箇所(`router.push("/login")`、paramsなし)に集約されている。呼び出し元は`/records`(journeyゲート)・`/journey`・`/premium`・`/shrines/[id]`(お気に入り/参拝記録/振り返り保存の3箇所)の計5箇所。
- `AuthPrompt`の`onClose`(ログインせず閉じた場合の挙動)は呼び出し元ごとに異なる(例: journeyは`/records`へ、premiumは`/mypage`へ、shrine detailはその場でモーダルを閉じるのみ)が、これは「ログインをキャンセルした時」の挙動であり、「ログインに成功した時」の復帰先ではない。
- **結論(事実)**: ログイン後、元の画面(例: 神社詳細やジャーニー)へ自動的に戻る仕組みは存在しない。ユーザーはログインのたびに`/mypage`から再度目的の画面へ移動し直す必要がある。

## 18. Analytics対応表

Mobileには構造として**2系統の計測経路**が存在する(事実)。

1. `track()`ベース(`lib/analytics.ts` → Console/PostHog) — `premiumAnalytics.ts`、`visitReflectionAnalytics.ts`、`directionEvents.ts`が使用。
2. Backend直POSTベース(`lib/actionEvents.ts`、`lib/shrineInteractions.ts`) — 独自DBへ保存され、PostHog等の集計基盤には現れない。

### 18.1 イベント一覧(抜粋、全件は各節参照)

| Event名 | 発火箇所 | 系統 | 重複発火リスク |
| --- | --- | --- | --- |
| `premium_screen_view`/`premium_status_view`/`premium_upgrade_click`/`premium_checkout_started`/`premium_checkout_failed`/`premium_checkout_returned`/`premium_active` | `app/premium/index.tsx`のみ | track() | 低(単一画面) |
| `visit_done`/`reflection_prompt_view`/`reflection_saved` | `app/shrines/[id].tsx`のみ | track() | 低 |
| `direction_visit_date_set` | `app/concierge/index.tsx`のみ | track() | 低 |
| `direction_condition_submitted` | `app/concierge/index.tsx`のみ | track() | 低 |
| `direction_match_impression`/`direction_match_detail_opened`/`direction_match_route_clicked` | `app/concierge/index.tsx`のみ | track() | 低 |
| **`direction_origin_result`** | `app/concierge/index.tsx`(3箇所: denied/success/failed)+`app/concierge/index.tsx`(selected、ConditionFieldsCard経由)+`components/MobileOriginSelector.tsx`(disabled) | track() | **高(同一event名が5箇所から発火、payload値でしか区別できない)** |
| `shrine_detail_view`(metadata.event) | `app/shrines/[id].tsx`のみ | Backend POST(`/shrine-interactions/`) | 低。ただしPostHog等には現れない |
| `route_open`(metadata.event) | `app/shrines/[id].tsx`のみ | Backend POST | 同上 |
| `action_started`/`action_completed` | `app/concierge/index.tsx`のみ | Backend POST(`/action-events/`) | 低 |

### 18.2 未実装・計測できない領域(事実)

- `apps/mobile/app/search/index.tsx`、`ShrineSearchMap.native.tsx`、`ShrineSearchMap.web.tsx`、`SelectedShrineMapCard.tsx` — analytics呼び出し**0件**。Search画面の入口クリック数、地図/一覧の使用比率、Marker選択数、いずれも現状測定不能。
- `apps/mobile/app/index.tsx`(Home) — 「この相談からご縁を見る」「神社を地図・一覧から探す」いずれのクリックもanalytics呼び出し**0件**。
- Home画面の`ConditionFieldsCard`利用(誕生日/出発地点の変更)は、Concierge画面の同一コンポーネント利用とは異なりtrack呼び出しがない(同じUIコンポーネントなのに計測有無が画面によって異なる、という一貫性の欠如)。
- `actionEvents.ts`・`shrineInteractions.ts`(Backend POST系)にはテストファイルが存在しない(`visit_done`/`reflection_saved`等track()系イベントにはテストがある一方、`shrine_detail_view`/`route_open`/`action_started`/`action_completed`は未テスト)。
- Webの`apps/web/src/lib/analytics/searchEvents.ts`等には`shrine_detail_transition`・`concierge_result_impression`・`card_view`系・`premium_preview_click`等、Mobileに存在しない多数のイベントが定義されている。Mobile側のAnalytics網羅性はWeb側より明確に狭い。

## 19. 導線分類

抽出した導線を分類する(事実整理。分類自体は本書の判断だが、最終的な優先度決定ではない)。

| 導線 | 分類 | 根拠 |
| --- | --- | --- |
| 相談条件入力(Home) | Primary | DOM順・視覚的重みで最優先、README.mdの主導線記述とも一致 |
| コンシェルジュ結果 | Primary | Primaryの直接の帰結、唯一リッチな神社詳細コンテキストを渡す経路 |
| 神社一覧(Search内リスト) | Secondary | Homeのサブボタン経由、地図未設定時は事実上こちらが主表示になる |
| Web地図 | Secondary(条件付き) | 未設定時は非表示(一覧へfallback)。設定時のみ機能、費用発生 |
| Mobile地図(Native) | Secondary | 常時表示だがAnalytics計測なし、Homeのサブボタン経由でのみ到達 |
| 人気神社(Search内) | Secondary | 固定データ(`SHRINES`)由来、地図/一覧と同一画面内の補助セクション |
| 神社詳細 | Shared(共通合流地点) | 7経路すべてが同一routeへ到達(14節) |
| 外部地図/経路案内 | Utility | 神社詳細からの単発アクション、Search画面の地図とは独立 |
| お気に入り | Secondary/Orphan寄り | `/records`経由で到達可能だが、記録画面内では最も目立たない位置 |
| 記録(ハブ) | Secondary | タブとして常設だが下位3画面のうち2つ(favorites/goshuin)は未ゲート、journeyのみゲート |
| 御朱印 | Utility | ローカル完結の記録機能、Analytics/API連携なし |
| Reflection(振り返り) | Utility | 参拝詳細内で完結、記録一覧への遷移はあるが再相談への接続なし |
| マイページ | Shared | Premium/Profileへのハブ、設定/利用規約/お問い合わせは**Dead(非活性)** |
| Premium | Premium | 唯一の商用導線、ゲーティングコードあり |
| ログイン | Utility | 共通AuthPrompt経由、returnTo機構なし |
| 参拝履歴(`/visit-history`) | **Orphan** | 到達経路0件 |
| 振り返り履歴(`/reflection-history`) | **Orphan** | 到達経路0件 |
| 相談履歴(`/consultation-history`) | **Orphan** | 到達経路0件 |
| 最近見た神社(`/recently-viewed`) | **Orphan** | 到達経路0件、`/records`にも未掲載 |
| ランキング(`/ranking`) | **Orphan** | 到達経路0件 |
| Search内フィルター機能(q/filtersクエリ) | **Candidate for defer(または要修復)** | 実装はあるが呼び出し元が渡していないため機能しない(12.8節) |
| Home「送信ボタン」と「この相談からご縁を見る」 | **Duplicate** | 完全に同一機能の重複CTA(10節) |
| `direction_origin_result`イベント | **Conflicting(計測上)** | 5箇所から同一イベント名が発火、payloadでしか区別不可(18節) |

## 20. 重複・競合・孤立

19節の表に加え、本節では根拠と影響範囲を明示する。

### 20.1 孤立(Orphan) — 5画面

`/visit-history`・`/reflection-history`・`/consultation-history`・`/recently-viewed`・`/ranking`。いずれも実装・空状態・エラー状態まで作り込まれているが、`apps/mobile/app`・`apps/mobile/components`全体をrouter遷移で検索しても到達経路が1件もない。削除提案ではなく、事実の指摘に留める。**影響範囲**: これら5画面のコード(合計5ファイル、関連する`lib`関数群)は現状ユーザーに一切表示されない。

### 20.2 Dead CTA — マイページ3件

`/mypage`の「設定」「利用規約」「お問い合わせ」の3カードは、`actionLabel`(「開く」「確認」「送る」)を表示しつつ`onPress`が渡されておらず、`MyPageCard`の`disabled={!onPress}`により非活性化されている。**影響範囲**: `apps/mobile/app/mypage/index.tsx`内の該当3カードのみ。

### 20.3 重複CTA — Home送信ボタン

10節の通り、chatCard内の`↑`ボタンと画面下部の「この相談からご縁を見る」は完全に同一の`openConcierge()`を呼ぶ。**影響範囲**: `apps/mobile/app/index.tsx`のみ。UXとしての重複であり、コード上のバグではない。

### 20.4 Analytics競合 — `direction_origin_result`

18.1節の通り、同一イベント名が5箇所(`concierge/index.tsx`内3箇所+ConditionFieldsCard経由1箇所+`MobileOriginSelector.tsx`1箇所)から発火し得る。同一のUI操作に対して複数コンポーネントが同時にマウントされている場合、二重発火の可能性がある(コードの静的読解からは実際に二重発火するかまでは確認できないため、「可能性がある」という事実の指摘に留める)。

### 20.5 機能しないフィルター — Search画面

12.8節の通り、`q`/`filters`クエリパラメータを処理するコードはSearch画面に実装済みだが、現在到達可能な唯一の入口(Home)がこれらを渡していない。**影響範囲**: `apps/mobile/app/search/index.tsx`のフィルタリングロジック全体が事実上デッドコード化している。

### 20.6 文書とコードの不一致(再掲、詳細は各節)

- README.md「Mobile休眠運用」 vs 実際の活発な開発活動(6.6節)
- `docs/core/roadmap.md` vs README.mdのMobile位置づけの不一致(6.6節)
- `docs/product/mobile-bottom-navigation.md`「5タブ」 vs 実装「4タブ」(7.2節、文書自身が既に自己申告)
- `docs/product/concierge-first-final-spec.md`の複数記述 vs 実装(11.5節)

## 21. 現行画面構造

12.5節で詳述したSearch画面の構造に加え、Home画面の構造も事実として記録する。

**Home画面のDOM順(事実)**: ブランドヘッダー → Hero(見出し+サブコピー) → テーマチップ → 自由入力カード(送信ボタン内包) → 条件追加アコーディオン → 主CTA「この相談からご縁を見る」 → サブCTA「神社を地図・一覧から探す」。

**Search画面のDOM順(事実、12.5節と同一)**: 戻る → Hero → 検索条件サマリー → 地図で探す(地図または一覧fallback+選択カード) → 人気の神社(3件) → 神社一覧(全件+地図で選択ボタン)。

この2画面のDOM順を突き合わせると、「相談 → 地図/一覧の順で探索」という導線は、Home画面のCTA優先順位(相談が先、地図/一覧探索が後)と、Search画面内部の構造(地図/一覧fallbackが人気/一覧より先)の両方で、一貫して「相談または地図的な入口が視覚的に先」という配置になっている。ただし12.5節で述べた通り、Web版の地図は現状(未契約)では実質的に一覧と同じ内容を表示している。

## 22. 案A／B／C比較

ユーザー指示の3案を、確認した事実に基づいて比較する。**最終案の決定は行わない。**

| 比較項目 | 案A: リスト主導・地図非表示 | 案B: リスト主導・地図補助表示 | 案C: 現行地図主導を維持 |
| --- | --- | --- | --- |
| KAMI MUSUBIのコンセプト整合 | Web(Next.js)側の既存README記述「地図ページは主導線ではなく補助的」(6.5節)と方向性が一致 | 同上、かつ地図実装を活かせる | 現行のWeb README記述とは緊張関係が生じる可能性(ただしMobile Native地図はこの記述の対象外) |
| Concierge Firstとの整合 | 相談を主導線とする現行の意図(11.5節で確認した文書上の設計思想)と整合しやすい | 同左、地図は補助的位置づけとして両立可能 | 地図の視覚的優先度が高いままだと、Concierge First文書の意図と現行UIの実態(12.5節の不一致)がさらに固定化するリスク |
| 初期ユーザーの迷いやすさ | 一覧のみでシンプル、迷いは少ないと推測されるが未検証(**推測**) | 地図の存在は示しつつ一覧を主とするため中間的(**推測**) | Web版は未契約時「地図を読み込めないため一覧を表示しています」という説明文が毎回表示され、ユーザーが地図機能の不在を意識する可能性(**推測**) |
| 実装変更量 | 環境変数を未設定のまま(現状維持)なので**最小**。ただし12.8節のセクション順を変える場合はコード変更が発生 | セクション順・折りたたみUIの実装変更が必要(中程度) | 変更なし(現状維持)だが、MapTiler契約作業が発生 |
| 外部費用 | なし(`EXPO_PUBLIC_WEB_MAP_STYLE_URL`未設定のまま) | 発生する(Web地図を有効化する場合) | 発生する(MapTiler Cloud契約、`docs/audit/web-map-tile-provider-selection.md`参照) |
| 外部障害点 | なし(Web地図非稼働のため) | MapTiler側の障害・料金超過リスクがある(ただし一覧fallbackで吸収可能な設計は実装済み) | 同左 |
| QA範囲 | 現状の一覧fallback QAのみで足りる(既に実施済み範囲) | 地図の表示/折りたたみ双方のQAが必要 | 地図の日本国内品質・アクセシビリティ等のPoC確認が別途必要(`docs/audit/web-map-tile-provider-selection.md`19節で「未実施」と明記済み) |
| Analyticsで検証可能か | **現状不可**(18.2節、Search/地図系イベントが0件のため、案の効果測定自体ができない) | 同左 | 同左 |
| 将来の再有効化難易度 | 低い(環境変数を設定するだけで有効化できる設計、`docs/audit/web-map-tile-provider-selection.md`で確認済み) | — | — |
| Mobile/Web差異 | Native地図は案によらず常時表示されるため、**Web版のみ**の方針変更になる(Native側の変更は指示書の制約上も対象外) | 同左 | 同左 |
| リリースリスク | 低い(既に発生している現状維持) | 中(新規実装のQA未実施) | 中〜高(外部契約・費用・障害点が増える) |
| Rollback容易性 | 容易(環境変数のみで制御) | UI変更を伴うためコードのrevertが必要 | 契約解除・環境変数除去の両方が必要 |

**事実の整理としての所見(断定ではない)**: 案Aは現状の実装(`EXPO_PUBLIC_WEB_MAP_STYLE_URL`未設定)をそのまま維持する案であり、追加の実装コスト・外部費用が最小である。ただし、Analytics計測が0件である以上、**いずれの案を採用しても効果を検証する手段が現状存在しない**という制約は3案共通である。

## 23. 地図非表示時の影響

現状(`EXPO_PUBLIC_WEB_MAP_STYLE_URL`未設定)がまさにこの状態である。確認できる事実:

- Web版Search画面は「地図を読み込めないため一覧を表示しています。」を表示し、一覧(座標欠損含む全件)を提示する。
- 選択・選択カード・神社詳細遷移は地図の有無に関わらず機能する(`hasValidCoordinates`による分離設計のため)。
- Native版には影響しない(react-native-mapsは常時稼働のため)。
- 12.8節の通り、フィルター機能自体がHome経由では使われていないため、地図の有無に関わらずSearch画面は「全件一覧+人気3件」の表示になる。

## 24. 地図再有効化時の影響

`EXPO_PUBLIC_WEB_MAP_STYLE_URL`を設定した場合の影響(事実+`docs/audit/web-map-tile-provider-selection.md`からの参照):

- MapTiler Cloud等の商用タイル提供元との契約・費用が発生する(未契約)。
- `docs/audit/web-map-tile-provider-selection.md`19節に記載の「PoC確認項目」(日本国内地図品質、キャッシュ挙動、Preview環境のdomain制限可否)が契約前に未実施のまま残っている。
- development/preview/production環境ごとのEAS環境変数分離、および母艦判断事項(同文書24.6節)が未解決のまま残っている。
- Analytics計測が0件のままでは、再有効化後も地図機能の利用状況を検証できない(18.2節)。

## 25. P0／P1／P2／P3

以下は「対応の緊急度についての監査者の所見」であり、実装着手の決定ではない。母艦の判断材料として提示する。

- **P0(事実の整合性に関わる、判断待ちの前提)**: README.mdの「Mobile休眠運用」記述と実態の乖離(6.6節)。この前提が確定しない限り、Mobile関連のあらゆる優先順位判断が不安定になる。
- **P1(計測基盤の欠如)**: Search/地図/Home CTAのAnalytics計測が0件(18.2節、22節)。案A/B/Cいずれを選んでも効果検証ができない状態。
- **P1(導線の断絶)**: 参拝・振り返り保存から再相談へのつながりが実装上存在しない(15.3節)。`docs/product/visit-reflection-flow.md`(Active)が想定する体験と実態の差分。
- **P2(孤立画面の扱い)**: 5つのOrphan画面(19節・20.1節)。削除するか、導線を追加するかの判断が必要。
- **P2(認証復帰)**: ログイン後に元画面へ戻らない(17節)。
- **P3(軽微な重複・Dead CTA)**: Home送信ボタンの重複(20.3節)、マイページのDead CTA 3件(20.2節)、Search画面の未使用フィルター機能(20.5節)。

## 26. 未確定事項

- README.mdの「Mobile休眠運用」とMobileの実態(継続的な機能開発)のどちらを現状の正としてよいか(6.6節)。
- `docs/core/roadmap.md`の「Mobile本番配布準備」というフェーズ表記と、README.mdの休眠運用表記の関係。
- `docs/product/concierge-first-final-spec.md`に記載された`theme`/`openFilter`パラメータ設計と、実装済みのHome→Concierge遷移パラメータのどちらを正とするか(11.5節)。
- Backend Concierge chatのクォータ/`limitReached`/`remaining`をMobile側で実際にどう扱うべきか(11.6節、現状未読み取り)。
- Search画面の未使用状態にあるフィルター機能(`q`/`filters`)を、Homeから接続するか削除するか(12.8節、20.5節)。
- 5つのOrphan画面を、導線接続の対象とするか、削除対象とするか(20.1節)。
- `direction_origin_result`イベントの5箇所発火が実際に二重計上を起こしているかどうかの実測確認(18.1節、20.4節、コード読解のみでは確定できない)。
- Web(Next.js)`/map`の「補助的」という設計思想を、Mobile/Expo Webの地図導線にも適用する前提でよいか(6.5節、22節)。

## 27. 次PR候補

母艦判断を経て着手する場合の候補(順不同、優先順位の決定ではない)。

- Search/地図/Home CTAへのAnalytics計装追加(18.2節の欠落を埋める)。実装済みの`lib/analytics.ts`パターンを踏襲すれば影響範囲は限定的。
- README.mdのMobile記述更新(6.6節の矛盾解消、母艦判断後)。
- Home→Search間のフィルターパラメータ接続、またはSearch画面側フィルターロジックの削除判断(12.8節)。
- ログイン後returnTo機構の追加検討(17節)。
- Orphan 5画面の扱い決定と、決定に応じた導線追加またはコード整理(20.1節)。
- `direction_origin_result`の発火元集約または命名分離の検討(20.4節)。

## 28. 残存リスク

- 本書はコードの静的読解とテストの存在確認に基づくものであり、実機・エミュレータでの動作確認は行っていない。特にiOS Simulatorでの実地確認は過去のセッションで不安定であったため、今回は実施していない(未確認として明記)。
- Backend側の実装(クォータ処理、`limitReached`のMobile側での扱い、スコアリング詳細)は契約レベルの確認に留まり、内部ロジックまでは深掘りしていない。
- `apps/web`(Next.js)側は構造確認のみで、画面別のCTA・Analytics詳細までは監査していない。本書がWeb側について述べた内容はREADME.mdからの引用および構造確認に基づく限定的なものである。
- 6つの並行調査エージェントの報告に基づく記述が大半を占める。エージェントの調査自体もコード読解に基づくが、本書作成者(私)が全ての行番号・引用を再検証したわけではない点は限界として明記する。
- 本書の対象commit(`0610dfd9`)以降にdevelopへマージされた変更は反映していない。

## 29. 参照ファイル

### コード

- `apps/mobile/app/_layout.tsx`
- `apps/mobile/app/index.tsx`
- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/search/index.tsx`
- `apps/mobile/app/records/index.tsx`
- `apps/mobile/app/mypage/index.tsx`
- `apps/mobile/app/premium/index.tsx`
- `apps/mobile/app/favorites/index.tsx`
- `apps/mobile/app/goshuin/index.tsx`
- `apps/mobile/app/goshuin/upload.tsx`
- `apps/mobile/app/visit-history/index.tsx`
- `apps/mobile/app/reflection-history/index.tsx`
- `apps/mobile/app/consultation-history/index.tsx`
- `apps/mobile/app/recently-viewed/index.tsx`
- `apps/mobile/app/profile/index.tsx`
- `apps/mobile/app/journey/index.tsx`
- `apps/mobile/app/ranking/index.tsx`
- `apps/mobile/app/login.tsx`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/components/search/ShrineSearchMap.native.tsx`
- `apps/mobile/components/search/ShrineSearchMap.web.tsx`
- `apps/mobile/components/search/SelectedShrineMapCard.tsx`
- `apps/mobile/components/common/AuthPrompt.tsx`
- `apps/mobile/components/MobileOriginSelector.tsx`
- `apps/mobile/lib/shrineMap.ts`
- `apps/mobile/lib/conditionPayload.ts`
- `apps/mobile/lib/originSession.ts`
- `apps/mobile/lib/analytics.ts`
- `apps/mobile/lib/premiumAnalytics.ts`
- `apps/mobile/lib/visitReflectionAnalytics.ts`
- `apps/mobile/lib/directionEvents.ts`
- `apps/mobile/lib/actionEvents.ts`
- `apps/mobile/lib/shrineInteractions.ts`
- `apps/mobile/lib/posthogAnalyticsProvider.ts`
- `packages/shared/directionAnalytics.ts`
- `backend/temples/api_views_concierge.py`
- `backend/temples/api/views/compat.py`
- `backend/temples/api/urls.py`
- `backend/temples/services/concierge_chat.py`
- `apps/mobile/lib/__tests__/routerStructure.test.ts`
- `apps/mobile/lib/__tests__/shrineMap.test.ts`
- `apps/mobile/lib/__tests__/analytics.test.ts`
- `apps/mobile/lib/__tests__/premiumAnalytics.test.ts`
- `apps/mobile/lib/__tests__/visitReflectionAnalytics.test.ts`
- `apps/mobile/lib/__tests__/directionEvents.test.ts`

### 設定

- `pnpm-workspace.yaml`
- `apps/mobile/package.json`
- `apps/mobile/app.json`
- `apps/mobile/eas.json`
- `apps/mobile/.hibernated`
- `.github/workflows/mobile-ci.yml`

### 文書

- `README.md`
- `docs/README.md`
- `docs/core/README.md`、`architecture.md`、`roadmap.md`、`concierge-spec.md`、`meaning-layer.md`、`auth-flow.md`、`authentication-flow.md`
- `docs/product/README.md`、`concierge-first.md`、`concierge-first-final-spec.md`、`concierge-first-wireframe.md`、`concierge-entry-final-wireframe.md`、`home-hero-final-wireframe.md`、`mobile-bottom-navigation.md`、`visit-reflection-flow.md`、`premium-experience.md`、`billing-paywall.md`、`shrine-detail-v3-design.md`、`shrine-detail-layer.md`、`shrine-detail-meaning-layer.md`
- `docs/mobile/route-cleanup-audit.md`、`route-structure-audit.md`、`mobile-web-parity-audit.md`
- `docs/audit/docs-directory-consistency-audit.md`、`core-document-responsibility-audit.md`、`product-document-responsibility-audit.md`、`analytics-document-responsibility-audit.md`、`archive-final-classification.md`、`root-docs-classification-audit.md`、`premium-reference-consolidation-audit.md`
- `docs/audit/web-search-map-library-selection.md`、`web-map-tile-provider-selection.md`(本セッション既存監査)
- `docs/analytics/README.md`、`direction-events.md`

## 30. 監査結論

- KAMI MUSUBIのMobile/Expo Webは、Home(相談入力)を主入口、Search(地図/一覧)をサブ入口、神社詳細を共通合流地点とする、ユーザー指示の仮説におおむね沿った構造を持つ(9〜14節で確認)。
- ただし、この構造は完全には一様ではない。神社詳細への合流はroute形状としては統一されているが、コンシェルジュ経由のみがリッチなコンテキストを持ち、Analytics上の識別も経路によらず固定文字列になっている(14節)。
- Search画面の地図は、コード上の配置順としては一覧より先に置かれているが、Web版はコスト回避のため現状「地図」という体裁の一覧にとどまっている(12.5節)。
- Home→Search間で本来渡せるはずのフィルターパラメータが実際には渡されておらず、Search画面のフィルタリング機能は現在使われていない(12.8節)。
- 記録・Reflection・Premium・ログインの各導線は個別には機能しているが、「参拝後に再び相談へ戻る」という循環はコード上つながっていない(15.3節)。
- 5つの画面(参拝履歴・振り返り履歴・相談履歴・最近見た神社・ランキング)は実装済みだが、現在到達する経路が存在しない(20.1節)。
- Search/地図/Home CTAのAnalyticsが未計装であり、今後どの案(案A/B/C)を採るにせよ、その効果を検証する手段が現状存在しない(18.2節、22節)。
- root README.mdの「Mobile休眠運用」という記述と、Mobileの実際の開発状況・`docs/core/roadmap.md`の記述との間に明確な不一致がある。この不一致の解消は、他のあらゆる優先順位判断に先立つ前提事項である(6.6節、25節P0)。

本書は以上の事実整理をもって完了とし、最終的なUI方針・機能削除・優先順位の決定は行わない。26節の未確定事項を中心に、母艦(ChatGPTレビュー)へ判断を差し戻す。
