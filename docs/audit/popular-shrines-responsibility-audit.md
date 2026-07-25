# Popular Shrines Responsibility Audit

> **Status: Draft(監査記録)**
>
> 本ドキュメントは、Mobile Search画面内「人気の神社」セクションの責務、データ契約およびPlatform間の重複を、実装コードと既存の正本・監査文書に基づいて整理した監査記録である。
>
> 最終的な削除・維持・実装方針の決定は行っていない。本書は判断材料の整理であり、判断そのものは母艦(プロジェクトオーナー)へ差し戻す。

---

## 1. Status

Draft(監査記録)。本書自体は正本(Active仕様書)ではない。今後、母艦の判断を経て`docs/product/mobile-user-flow.md`等の正本文書へ反映される可能性があるが、本書だけでは仕様変更・実装変更の根拠にならない。

## 2. 目的

Mobile Search画面(`apps/mobile/app/search/index.tsx`)内の「人気の神社」セクションについて、以下を事実として整理する。

- 責任範囲(独立導線か、Search補助導線か)
- データ取得元・算出根拠
- `/ranking`画面、Web `/populars`・`HomeRankingSection`との責務重複
- Concierge・神社詳細・Analyticsとの整合
- 既存の正本文書・監査文書だけで責務が管理できているか
- 初期公開範囲かDeferred範囲か

削除・維持・実装方針の決定は本書の目的に含まない。

## 3. 対象commit・対象範囲

- ブランチ: `audit/popular-shrines-responsibility`
- 作業開始時点のcommit SHA: `0768fd024f382b0714bb310073fcbb3cacd1f922`(develop、`Mobile Search導線のAnalytics計測を追加` PR #2178マージ直後)
- 対象範囲: `apps/mobile/app/search/index.tsx`の「人気の神社」セクション、`apps/mobile/app/ranking/index.tsx`、`apps/mobile/data/shrines.ts`、関連するProduct/Analytics/Audit文書
- 対象外: `apps/web`側の実装変更、Backend実装変更、UI変更、削除・実装の実行

本書の記述はすべてこのコミット時点のコード・文書に基づく。以降にdevelopへマージされた変更は反映していない。

## 4. 参照した既存文書(要旨)

| 文書 | Status | 本監査との関係 |
| --- | --- | --- |
| `docs/product/mobile-user-flow.md` | Active | 13節が「人気神社の責務」を既に正本として定義済み。18節・20節で算出ロジック改善を明示的にDeferred/未確定事項として扱う |
| `docs/product/visit-reflection-flow.md` | Active | 人気神社への言及なし。責務重複なし(4.2節で確認) |
| `docs/product/premium-experience.md` | Active | 人気神社への言及なし。Premiumゲーティング対象外(4.2節で確認) |
| `docs/product/README.md` | Active | `docs/product`文書構成の入口。人気神社固有の記載なし |
| `docs/analytics/mobile-search-events.md` | Active | `shrine_card_click`の`position: "popular"`をMobile専用値として定義済み(19節参照) |
| `docs/analytics/README.md` | Active | Analytics文書のActive/Reference/Archive分類の入口 |
| `docs/audit/mobile-user-flow-inventory.md` | Draft(監査記録) | 12.5節・12.7節・19節・20節が現行実装の画面構造・分類を記録(ただし後述の通り一部陳腐化) |
| `docs/audit/web-mobile-experience-parity.md` | (Status行なし、監査記録) | `WM-RANK-102`〜`108`・`WM-SEARCH-201`〜`209`がRanking/Searchの詳細差異を記録。本監査の中心的な参照根拠 |

Archive文書は参照していない。

## 5. 現行実装の事実

### 5.1 データ取得元(`apps/mobile/app/search/index.tsx:72-76`)

```ts
const popularShrines = [...SHRINES]
  .sort((a, b) => (b.favorites ?? 0) - (a.favorites ?? 0) || (b.rating ?? 0) - (a.rating ?? 0))
  .slice(0, 3);
```

`SHRINES`は`apps/mobile/data/shrines.ts`(45行)で定義された、ファイル冒頭に「簡易モック。必要に応じて増やしてOK」と明記された静的配列である。`favorites`・`rating`は各神社エントリにハードコードされた固定値であり、API呼び出し・バックエンド集計は一切ない。したがって「人気の神社」の並び順は、実際のユーザー行動に関わらず常に固定(伏見稲荷大社→明治神宮→神田明神)である。

### 5.2 画面構成・表示順序(現行、`apps/mobile/app/search/index.tsx`)

現行のJSX上の縦方向の並び順は以下である(コード読解に基づく事実)。

1. `← 戻る`
2. Hero
3. 「検索条件」サマリーカード
4. **神社一覧セクション**(`visibleShrines`、APIの全件から人気3件を除いたもの)
5. 選択中の地図カード(`selectedMapShrine`がある場合のみ)
6. **人気の神社セクション**(3件、`SHRINES`固定データ由来)
7. 地図で探すセクション(`isMapSectionAvailable`が真の場合のみ)

**`docs/audit/mobile-user-flow-inventory.md` 12.5節との差分(事実)**: 同節は「地図で探す→人気の神社→神社一覧」という順序を記録しているが、これは同文書の対象commit(`0610dfd9`)時点の事実であり、本セッション内で完了した「Search地図をPlatform別実装へ分離してWeb fallbackを追加」(PR #2168)および先行するlist-first再構成により、現行の並び順は「神社一覧→人気の神社→地図」へ変更されている。これは`mobile-user-flow-inventory.md`が監査記録(Draft)であり正本ではないため、想定通りの陳腐化であって同文書の誤りではない。ただし、本監査時点の事実として明記する。

### 5.3 `/ranking`画面との関係(事実)

`apps/mobile/app/ranking/index.tsx:58`は以下を実装する。

```ts
const items = React.useMemo(() => [...SHRINES].sort((a, b) => (b.favorites ?? 0) - (a.favorites ?? 0)), []);
```

画面タイトルは「人気神社ランキング」、説明文は「保存数の多い神社を、参拝先選びの補助として見られます。」である。

**事実**: Search内「人気の神社」(top3)と`/ranking`(全件+お気に入りフィルタ)は、以下の点で同一の責務を独立に実装している。

- 同一データソース(`SHRINES`)
- 同一ソートキー(`favorites`降順)
- 同一の「人気」概念(タイトル文言・UI意図とも一致)
- 両者を接続するコード上の共有(共通コンポーネント・共通関数)は存在しない。それぞれが個別に`SHRINES`を読み込み、個別に`sort`している

`docs/audit/mobile-user-flow-inventory.md` 20.1節によれば`/ranking`はコード全体に到達経路が1件も存在しない孤立(Orphan)画面である。したがって、同一責務の実装が「Search内の常時表示される3件版」と「到達不能な全件版」という非対称な形で並存している。

### 5.4 Web `/populars`・`HomeRankingSection`との関係(事実、`docs/audit/web-mobile-experience-parity.md`より)

Webには`apps/web/src/app/populars/page.tsx`(独立ページ)と`apps/web/src/features/home/components/HomeRankingSection.tsx`(Home埋め込み)が存在し、いずれも実バックエンドAPI(`/api/populars/`、`visits_30d_dyn`等の実集計値)からデータを取得する。

既存監査`docs/audit/web-mobile-experience-parity.md`の`WM-RANK-103`(P1、データ契約)は以下を記録済みである。

> Web: 実バックエンドAPI(`/api/populars/`)から取得、`visits_30d_dyn`等の実集計 / Mobile: `data/shrines.ts`の静的モック`favorites`フィールドをソートのみ、API呼び出しなし

この記録は`/ranking`画面を対象に書かれたものだが、5.1節・5.3節で確認した通り、Search内「人気の神社」セクションも**同一の`SHRINES.favorites`ソートロジックを使用しており、`WM-RANK-103`が指摘するデータ契約の問題(実データではなく固定モック)をそのまま共有する**。この対応関係は`web-mobile-experience-parity.md`の記述からは明示的に読み取れず、本監査で新たに確認した事実である。

同監査の8節には、この問題への既存の是正計画が既に存在する。

> **PR3：Mobile Rankingの実データ接続**(`fix/mobile-ranking-real-api`)。目的: `data/shrines.ts`静的モックへの依存を廃し、Web同様`/api/populars/`を呼び出してloading/error/fallback状態を実装。重大度: P1(`WM-RANK-103`, `WM-RANK-104`)。

本監査時点で、このPR3は着手されていない(該当ブランチ・PRは存在しない、6節で確認)。

### 5.5 Search画面到達性に関する既存監査記録の陳腐化(事実)

`web-mobile-experience-parity.md`(対象commit`b7ea1548`)は`WM-SEARCH-202`(P1)として「Mobile `/search`への`router.push`系コードが全社的に0件で到達経路が特定できないオーファン画面の疑い」を記録し、8節の**PR2**(`fix/ranking-search-navigation-reachability`)・**PR4**(`fix/mobile-search-entry-point`)として是正PR案を提示していた。

**事実**: `b7ea1548`以降、本セッション内で完了した以下のPRにより、この指摘は実質的に解消されている。

- PR #2168「Search地図をPlatform別実装へ分離してWeb fallbackを追加」
- PR #2169「ホームから神社検索画面への導線を追加」(`apps/mobile/app/index.tsx`の`openSearch`が`/search`へ`router.push`する)

本セッション中のブラウザ実地確認(前タスクのAnalytics実装検証時)でも、Home画面の「神社を地図・一覧から探す」ボタンから`/search`へ到達できることを確認済みである。したがって、Search画面自体(および内包する「人気の神社」)は、もはや「到達不能なオーファン画面」ではなく、初期公開surfaceとして現に到達可能な状態にある。

一方で、`WM-RANK-103`(データ契約、`/ranking`・Search内人気神社に共通)は本セッションのPR群では対応されておらず、依然として未解消のP1事項である。

### 5.6 Concierge・神社詳細との重複(事実)

`apps/mobile/app`・`apps/mobile/components`全体を`grep -rl "人気"`で検索した結果、「人気」という語を含むファイルは`app/ranking/index.tsx`と`app/search/index.tsx`の2件のみであった。Concierge(`app/concierge/index.tsx`)・神社詳細(`app/shrines/[id].tsx`)には「人気」概念の実装・言及は存在せず、責務重複はない。

### 5.7 Analyticsとの整合(事実)

`docs/analytics/mobile-search-events.md`は`shrine_card_click`の`position`値として`"list" | "popular" | "map"`を定義し、`position: "popular"`をMobile専用値として明記している(Webの`position`型には存在しない値であることも明記済み)。`apps/mobile/app/search/index.tsx:191`の人気カードクリック時の`trackShrineCardClick({ shrineId: s.id, position: "popular" })`呼び出しは、この契約と一致している。Analytics側の責務定義と実装の間に不整合はない。

## 6. 既存文書との整合確認

### 6.1 `docs/product/mobile-user-flow.md` 13節との一致

同節は以下を既に正本として定義している。

- 人気神社は主導線ではない
- 一覧探索を補助する発見導線として扱う
- 人気の算出根拠が未確定、または固定データに基づく場合、主UIより先に配置することを前提としない
- 表示継続・配置・`/ranking`との統合は別PRで判断する
- 本書では削除を決定しない
- 初期公開での位置づけは`Secondary`または`Candidate for defer`とする

5.1節・5.2節で確認した現行実装(固定データ由来・現行では神社一覧より後に配置)は、この記述と**一致している(MATCHES)**。「算出根拠が固定データの場合は主UIより先に配置しない」という条件は、5.2節で確認した現行の並び順(神社一覧が先、人気の神社が後)によって満たされている。

同18節(Deferred)は「人気神社の算出ロジック改善」を明示的にDeferredとして扱っており、20節(未確定事項)は「人気神社の算出ロジックと`/ranking`実装との統合方針」を別PR・母艦判断へ差し戻し済みである。5.3節・5.4節で確認した事実(`/ranking`との同一ロジック・`WM-RANK-103`の未着手)は、この既存の未確定事項の具体的根拠を補強するものであり、方針そのものを変更する必要はない。

### 6.2 `docs/audit/web-mobile-experience-parity.md`との関係

5.4節で確認した通り、`WM-RANK-103`の是正計画(PR3)は`/ranking`向けに書かれているが、Search内「人気の神社」にも同じ修正が波及する(同一データ取得ロジックのため)。この対応関係は既存文書には明記されていなかった新事実であり、PR3着手時にはSearch画面側の変更も同時に検討する必要があることを本書で記録する。

### 6.3 `docs/audit/mobile-user-flow-inventory.md`との関係

5.2節・5.5節で確認した通り、同文書12.5節(画面順序)・`WM-SEARCH-202`関連の記述(到達不能)は、本セッション内の後続PRにより一部陳腐化している。これは監査記録(Draft)の設計上想定された挙動であり、両文書自体の訂正は不要と判断する(「本監査後に変更された実装・文書については、後続PRまたは別監査で再確認する」という両文書共通の前提と整合)。

## 7. 判断(事実整理、削除・維持は判断しない)

- **独立した導線として必要か**: 独立導線ではない。Search画面内の1セクションとして実装されており、Home等から直接「人気の神社」へ到達する専用CTAは存在しない(事実)。
- **Search補助導線として十分か**: UI・Analytics計測としては機能している(5.7節)。ただし、算出根拠が実データでない(5.1節)ため、「発見導線」として実際の人気を反映しているとは言えない。この点は`mobile-user-flow.md`13節が既に条件付けている「固定データに基づく場合は主UIより先に配置しない」を、現行の配置順序(神社一覧が先)によって形式的には満たしているが、機能面の限界(常に同じ3件が表示される)は解消されていない(事実)。
- **初期公開対象かDeferredか**: 現行実装は既にSearch画面の一部として公開されており、5.5節で確認した通りSearch画面自体は到達可能である。`mobile-user-flow.md`17節(初期公開範囲)は「人気神社」を明示的な初期公開候補として列挙していないが、18節(Deferred)は「算出ロジック改善」のみをDeferred対象としており、表示自体の停止・除外は求めていない。したがって、現状は「表示は初期公開に含まれた状態で稼働しているが、実データ接続という改善だけがDeferredとして残っている」という状態として事実整理できる。
- **削除候補か維持候補かは判断しない**(本監査のスコープ外、`mobile-user-flow.md`13節も同様の立場)。

## 8. 新しい契約文書の要否

**不要と判断する。**

- 責務定義(独立導線でないこと、発見導線としての位置づけ、削除を決定しないこと)は`docs/product/mobile-user-flow.md`13節が既にActiveな正本として管理している。
- データ契約の是正方針(実API接続)は`docs/audit/web-mobile-experience-parity.md`のPR3提案が既に具体的に示している。
- Analytics契約は`docs/analytics/mobile-search-events.md`が既に`position: "popular"`を定義済みである。

本監査で新たに確認した事実(Search内人気神社が`WM-RANK-103`のデータ契約問題を`/ranking`と共有すること、および`WM-SEARCH-202`関連の到達不能問題がPR #2168/#2169で解消済みであること)は、いずれも既存文書の枠組み内で説明可能な事実であり、新しい正本文書を必要としない。

## 9. 実装の要否

**本監査では実装を行わない。**

- 5.4節で確認した通り、実データ接続(`WM-RANK-103`)の是正は`web-mobile-experience-parity.md`のPR3として既に計画されている。本監査のスコープ(責務の事実整理)でこれを先取りして実装すると、PR3が対象とする`/ranking`側の実装(loading/error/fallback状態を含む)との重複・不整合が生じる可能性がある。
- 5.2節で確認した画面順序は、既存正本(`mobile-user-flow.md`13節)の条件を現行のまま満たしており、本監査で修正が必要な不整合は見つからなかった。
- コード変更を伴わないため、`pnpm typecheck` / `pnpm test` / `pnpm exec expo export -p web` / `git diff --check`はいずれも変更なしの状態で実行し、既存の合格状態に変化がないことのみを確認する。

## 10. 関連ドキュメント

本書と既存文書の責務は重複させない。

- `docs/product/mobile-user-flow.md` — 人気神社の責務(Secondary/発見導線/削除非決定)を管理する正本。本書はこの正本の記述と現行実装が一致していることを確認するのみで、責務自体を再定義しない。
- `docs/audit/web-mobile-experience-parity.md` — `WM-RANK-102`〜`108`・`WM-SEARCH-201`〜`209`、および是正PR案(PR2〜PR4)の一次情報源。本書はSearch内人気神社が同監査の`WM-RANK-103`を共有するという対応関係を補足する。
- `docs/audit/mobile-user-flow-inventory.md` — 監査時点(コミット`0610dfd9`)の事実記録。本書は同文書12.5節の記述が後続PRにより陳腐化していることを5.2節・6.3節で補足する。
- `docs/analytics/mobile-search-events.md` — `position: "popular"`の契約を管理する正本。本書はこの契約と実装の整合を5.7節で確認するのみで、契約自体を変更しない。

## 11. 更新ルール

- 本書は監査記録(Draft)であり、対象commit時点の事実記録として固定する。
- 本書の内容を現行契約として扱わない。責務変更・データ契約変更・削除判断は、`docs/product/mobile-user-flow.md`または新規PRで別途判断する。
- 本監査後にSearch内人気神社・`/ranking`・Web `/populars`関連の実装が変更された場合、本書の記述は再確認せず、必要であれば別の監査文書を新規作成する。
