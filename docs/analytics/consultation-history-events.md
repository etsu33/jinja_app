> **Status: Active / Contract**

# Consultation History導線のイベント契約

Web／Mobile共通の「相談履歴」導線(MyPageからの入口、履歴一覧、履歴詳細、履歴詳細からの神社詳細遷移)を対象とするEvent契約を管理する。実装は`apps/web/src/lib/analytics/consultationHistoryEvents.ts`(Web)・`apps/mobile/lib/consultationHistoryAnalytics.ts`(Mobile)を正本とし、送信はそれぞれの既存`track()`パイプライン(`apps/web/src/lib/analytics/track.ts`、`apps/mobile/lib/analytics.ts`)へ委譲する。

画面からPostHog SDK等を直接呼ばず、必ずこれらのhelper経由でEventを送信する。Event名と固定`source`/`platform`はhelper内に集約し、画面コードへ分散させない。

## 対象範囲

- Web: `apps/web/src/components/views/MyPageView.tsx`(相談履歴導線)、`ConsultationHistoryListView.tsx`、`ConsultationHistoryDetailView.tsx`
- Mobile: `apps/mobile/app/mypage/index.tsx`(相談履歴導線)、`apps/mobile/app/consultation-history/index.tsx`、`apps/mobile/app/consultation-history/[id].tsx`

対象は既存の相談履歴実装([PR #2215](https://github.com/etsu33/jinja_app/pull/2215) Web、[PR #2216](https://github.com/etsu33/jinja_app/pull/2216) Mobile)であり、本書はEvent契約のみを追加する。既存UI・文言・Navigation契約(Route名、`ctx=concierge&tid=`、Shrine Detailへのroute params等)は変更しない。

## Event一覧

| Event | 発火条件 | Payload | 重複の単位 |
| --- | --- | --- | --- |
| `consultation_history_entry_clicked` | MyPageの相談履歴導線を明示操作したとき | `platform`, `source: "mypage"` | 操作ごと |
| `consultation_history_list_viewed` | 認証済みかつ一覧取得が成功し、一覧状態が表示可能になったとき(0件でも発火) | `platform`, `source: "consultation_history"`, `historyCount` | 画面マウント中に1回 |
| `consultation_history_detail_opened` | 一覧のカードを明示操作し、詳細画面へ遷移するとき | `platform`, `source: "consultation_history_list"`, `threadId`, `position` | 操作ごと |
| `consultation_history_detail_viewed` | 認証済みかつ詳細取得が成功し、threadが正常表示されたとき(Direct Navigationでも発火) | `platform`, `source: "consultation_history_detail"`, `threadId`, `recommendationCount`, `messageCount` | 同一tidの同一画面マウント中に1回 |
| `consultation_history_shrine_opened` | 詳細画面内の「神社の詳細を見る」を明示操作したとき | `platform`, `source: "consultation_history_detail"`, `threadId`, `shrineId`, `recommendationRank` | 操作ごと |

`platform`は`"web"`または`"mobile"`を実装側の定数として固定する(呼び出し元からは受け取らない)。

## 発火条件の詳細

### 表示Event(`list_viewed`/`detail_viewed`)

- 発火は「認証済み」かつ「取得成功」かつ「表示可能な状態になった」ときのみ
- `loading`状態では発火しない
- `unauthenticated`(未ログイン)状態では発火しない
- `fetchFailed`/`error`(API取得失敗)状態では発火しない
- `detail_viewed`はさらに`not_found`(不正または存在しないtid)状態でも発火しない
- `list_viewed`は履歴0件(Empty状態)でも`historyCount: 0`で発火する(0件と取得失敗を区別するため)
- Direct Navigation(URL直接アクセス、Mobileの`/consultation-history/[id]`への直接遷移)でも、認証済み・取得成功・正常表示であれば`detail_viewed`は通常どおり発火する

### 実行Event(`entry_clicked`/`detail_opened`/`shrine_opened`)

- いずれもユーザーの明示操作(タップ・クリック)を契機とし、既存の遷移(Web: `<Link>`のhref、Mobile: `router.push`)を維持したまま、遷移前にEventを送信する
- 表示のみでは発火しない(カードが画面に表示されただけでは`detail_opened`は発火しない)

## Payload

### `consultation_history_entry_clicked`

```json
{ "platform": "web" | "mobile", "source": "mypage" }
```

### `consultation_history_list_viewed`

```json
{ "platform": "web" | "mobile", "source": "consultation_history", "historyCount": number }
```

`historyCount`は一覧に含まれるThread件数(0以上の整数)。

### `consultation_history_detail_opened`

```json
{ "platform": "web" | "mobile", "source": "consultation_history_list", "threadId": string | number, "position": number }
```

`position`は一覧内の並び順で1始まり(0始まりではない)。Mobileは日付ごとにグルーピング表示するが、`position`は一覧全体(グルーピング前)における通し番号を送る。

### `consultation_history_detail_viewed`

```json
{ "platform": "web" | "mobile", "source": "consultation_history_detail", "threadId": string | number, "recommendationCount": number, "messageCount": number }
```

`recommendationCount`はThread Detailの`recommendations_v2`(存在すれば優先)または`recommendations`の件数。`messageCount`は`messages`配列の件数(Backend側の`message_count`フィールドではなく、実際に表示するmessages配列の長さを送る)。

### `consultation_history_shrine_opened`

```json
{ "platform": "web" | "mobile", "source": "consultation_history_detail", "threadId": string | number, "shrineId": string | number, "recommendationRank": number }
```

`recommendationRank`は詳細画面内の推薦神社カード一覧における並び順で1始まり。

## 重複発火防止

- `list_viewed`・`detail_viewed`は、画面が表示可能状態(`ready`)になった時点で1回だけ発火するよう、`React.useRef`による送信済みフラグで制御する
- Pull to Refresh(Mobile)・Retry操作(Web/Mobile共通の「もう一度読み込む」)による再取得や、その他の理由による再レンダーでは、既に送信済みであれば再発火しない
- `detail_viewed`は「同一tidの同一マウント中に1回」を単位とする。マウントされたまま`tid`が変わる導線は現状存在しないが、`tid`ごとに送信済みフラグを保持することで将来の導線変更にも耐える
- `entry_clicked`・`detail_opened`・`shrine_opened`はユーザー操作ごとに発火する実行Eventであり、重複防止の対象ではない(意図的な複数回操作はそれぞれ計測する)

## Direct Navigationの扱い

- Web: `/mypage/history/[tid]`へURLを直接開いた場合も、Server ComponentがThread Detailを取得し、Client Componentが`ready`状態に到達すれば`detail_viewed`を発火する。一覧を経由していないため`detail_opened`は発火しない
- Mobile: `/consultation-history/[id]`へ直接遷移した場合(Deep Link等)も同様に、`ready`状態に到達すれば`detail_viewed`のみが発火し、`detail_opened`は発火しない
- 不正または存在しないtidの場合(`not_found`状態)は、Direct Navigationであっても`detail_viewed`は発火しない

## 0件と取得失敗の区別

- 履歴0件(Empty状態、認証済み・取得成功・件数0)は`list_viewed`を`historyCount: 0`で発火する
- 未ログイン(`unauthenticated`)・API取得失敗(`fetchFailed`/`error`)はいずれも`list_viewed`を発火しない
- 上記3状態(0件・未ログイン・取得失敗)はUI表示文言が異なるだけでなく、Analytics上も明確に区別される(未ログイン/取得失敗は`historyCount`という概念自体が存在しないため、`0`と区別なく送ることを避ける)

## WebとMobileの共通契約

- Event名は完全に同一の文字列を使用する
- Payloadのkey名・意味・型(`threadId`/`shrineId`は`string | number`、`historyCount`/`position`/`recommendationRank`/`recommendationCount`/`messageCount`は`number`)を一致させる
- `source`の固定値もWeb/Mobile間で同一の文字列を使用する
- 差分は`platform`の値(`"web"` / `"mobile"`)のみ
- 実装は共有せず(型・helperはWeb/Mobileそれぞれの言語・基盤に合わせて個別実装する)、契約(Event名・Payloadの意味)のみを揃える

## Privacy／禁止Payload

次の値はEvent名を問わず送信しない。

- 相談本文、相談タイトル、メッセージ本文(`messages[].content`)
- 推薦理由本文(`recommendation_reason_v4`、`recommendation_reason_v4_detail`、`reason_facts`等の全文)
- 住所、緯度・経度
- ユーザー名、メールアドレス、トークン、Cookie
- APIレスポンス全文

`platform`・`source`・`threadId`・`shrineId`・`historyCount`・`position`・`recommendationCount`・`messageCount`・`recommendationRank`のみを許可する。

Web側の`track()`はセッションID(`analyticsSessionId`/`sessionId`)を自動付与するが、これはWebの既存セッション追跡機構であり、相談Thread ID(`threadId`)とは独立したPropertyとして扱う。WebのsessionIdを相談threadIdの代用として使用しない。

## Funnel定義

1. `consultation_history_entry_clicked`(MyPageから相談履歴を開く)
2. `consultation_history_list_viewed`(履歴一覧を正常表示する)
3. `consultation_history_detail_opened`(一覧から履歴詳細を開く)
4. `consultation_history_detail_viewed`(履歴詳細を正常表示する)
5. `consultation_history_shrine_opened`(履歴詳細から神社詳細を開く)

各段階は前段階を経由しなくても発火しうる(Direct Navigationにより3を経由せず4が発火する等)。Funnel分析ではDirect Navigation経由の`detail_viewed`が2→4に直接接続する経路として扱われることを前提とする。

## Payload型

- primitive型(string/number/boolean)のみを許可する
- nested object・配列を送らない
- `null`/`undefined`は送信前に除外する(Web: `track()`のシリアライズ、Mobile: `apps/mobile/lib/analytics.ts`の`serializeAnalyticsPayload`が構造的に担う)
- 送信失敗はいずれのhelperも内部で握り潰し、呼び出し元(画面のUI・Navigation)を止めない

## 実装ファイル一覧

- `apps/web/src/lib/analytics/consultationHistoryEvents.ts`(Web helper、正本)
- `apps/web/src/components/views/MyPageView.tsx`(`entry_clicked`)
- `apps/web/src/components/views/ConsultationHistoryListView.tsx`(`list_viewed`/`detail_opened`)
- `apps/web/src/components/views/ConsultationHistoryDetailView.tsx`(`detail_viewed`/`shrine_opened`)
- `apps/mobile/lib/consultationHistoryAnalytics.ts`(Mobile helper、正本)
- `apps/mobile/app/mypage/index.tsx`(`entry_clicked`)
- `apps/mobile/app/consultation-history/index.tsx`(`list_viewed`/`detail_opened`)
- `apps/mobile/app/consultation-history/[id].tsx`(`detail_viewed`/`shrine_opened`)

## 変更ルール

- Event名またはPayloadを変更する場合は、Web/Mobile双方のhelper実装と本書を同じPRで更新する
- WebとMobileで同じEvent名を使う場合は意味とPayloadを一致させる(本書の「WebとMobileの共通契約」節を参照)
- 表示Event(`list_viewed`/`detail_viewed`)と実行Event(`entry_clicked`/`detail_opened`/`shrine_opened`)を区別し、混同しない
- 相談履歴の既存UI・文言・Navigation契約(Route名、Shrine Detail route params等)は本書の対象外であり、変更する場合は`docs/product/history-recommendation-navigation-design.md`を更新する
