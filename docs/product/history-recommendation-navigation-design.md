> **Status: Active**
>
> 本ドキュメントは、Concierge履歴（相談履歴）から過去の推薦神社・Recommendation Reason V4 Detailへ再アクセスするためのNavigation設計を管理する正本文書である。
>
> 本書は設計文書であり、実装契約そのものではない。Fact/Interpretation/Action表示の契約は`docs/product/recommendation-v4-frontend-adapter-contract.md`、Recommendation Reasonの生成契約は`docs/core/recommendation-reason-contract.md`を正本とする。

# History Recommendation Navigation Design

## 目的

Concierge履歴（過去の相談スレッド）から、当時推薦された神社の詳細（Fact/Interpretation/Action含む）へWeb/Mobile双方から到達できるようにする設計を定義する。

前提方針（母艦から提示）:

1. 履歴では当時保存されたRecommendation Snapshotを正本にする
2. 神社名・画像・営業情報などは、必要に応じて現在のShrine APIを参照する
3. 過去の推薦理由を現在のロジックで再生成しない
4. 神社詳細では既存の`ctx=concierge&tid=<thread_id>`経路を再利用する
5. 古いThreadにV4 Detailがない場合は既存fallbackを使う
6. 相談本文をURLへ載せない
7. WebとMobileで情報構造を揃え、UI表現だけ分ける

---

## 現状監査で確認した事実

### Backend API契約（実際に配線されているもの）

`GET /api/concierge-threads/`（`ConciergeThreadListView`, `backend/temples/api/views/concierge.py`）

- `permission_classes = [IsAuthenticated]`
- `ConciergeThread.objects.filter(user=user).order_by("-last_message_at", "-id")[:50]`（ページネーションなし、最大50件固定）
- 返却: `{"results": [{id, title, last_message, last_message_at, message_count}]}`

`GET /api/concierge-threads/{pk}/`（`ConciergeThreadDetailView`, 同ファイル）

- `permission_classes = [AllowAny]`だが、内部で以下の順に所有者判定する:
  1. 認証済みユーザーなら`thread.user == request.user`
  2. 未認証でも`concierge_anon_id`Cookieがあれば`thread.anonymous_id`と一致するか
  3. どちらにも一致しなければ404
- 返却: `{id, title, last_message, last_message_at, message_count, messages: [...], recommendations, recommendations_v2}`
- `recommendations`/`recommendations_v2`は保存時のJSONをそのまま返すが、各itemへ`action_state`（favorite/visited/reflected等）だけは**読み取り時に`classify_shrine_action_state`で都度計算**して付与する。推薦順位・Fact/Interpretation/Actionは再計算しない。

### ⚠️ 発見した不具合: デッドコード

`backend/temples/api/views/concierge_history.py`（`ConciergeHistoryListView`/`ConciergeHistoryDetailView`）と`backend/temples/api/serializers/concierge_history.py`（`ConciergeThreadListSerializer`/`ConciergeThreadDetailSerializer`）は、**どのURLにも紐付いていない完全なデッドコード**である。`backend/temples/api/urls.py`は同名に近い別実装（`temples.api.views.concierge`の`ConciergeThreadListView`/`ConciergeThreadDetailView`）を`concierge-threads/`へ登録しており、実際に呼ばれるのはこちらのみ。

本書のBackend API契約は、実際に配線されている`temples/api/views/concierge.py`側を正としている。デッドコードの削除要否は本書のスコープ外とし、「母艦判断待ち」へ記載する。

### Web

- 履歴一覧・詳細のUIページは存在しない（BFF Route (`apps/web/src/app/api/concierge-threads/route.ts`, `apps/web/src/app/api/concierge-threads/[id]/route.ts`) と server関数(`getConciergeThreadsServer`/`getConciergeThreadServer`, `apps/web/src/lib/api/concierge.server.ts`)のみ存在し、呼び出すページが無い）。
- `apps/web/src/app/shrines/[id]/page.tsx`は`ctx=concierge&tid=<id>`のとき、`getConciergeThreadServer(tid)`で当該Threadを再取得し、`thread.recommendations`から`shrine_id`一致するitemを`selectedRecommendation`として使う。History画面から同じ`ctx`/`tid`で遷移すれば、このロジックは無改修でそのまま機能する。

### Mobile

- `apps/mobile/app/consultation-history/index.tsx`はThread一覧のみを表示し、`ConsultationCard`に`onPress`が無いため神社詳細への遷移導線が存在しない。
- `apps/mobile/lib/consultationHistory.ts`の`listConciergeThreads()`は`GET /concierge-threads/`を叩く。

### ⚠️ 発見した型不整合

`apps/mobile/lib/consultationHistory.ts`の`ConciergeThreadListItem`型は`created_at`/`updated_at`を宣言しているが、実際のBackendレスポンス（上記参照）にはこの2フィールドが存在しない。`ConsultationCard`の日付表示は`thread.last_message_at ?? thread.updated_at ?? thread.created_at`という優先順位で、実際には常に`last_message_at`が使われるため実害は出ていないが、型定義として不正確である。

### ⚠️ 発見した潜在バグ: 未ログイン時に「履歴0件」と誤表示されうる

`getConciergeThreadsServer`（Web）と`listConciergeThreads`（Mobile）はいずれも401/403エラーを空配列へ握りつぶす。History画面を新設する際、この関数だけで未ログイン状態を判定すると「まだ相談履歴がありません」という**誤った空状態メッセージ**が、未ログイン/セッション切れの場合にも表示されてしまう。History画面側で認証状態を別途判定してから空状態メッセージを出し分ける必要がある（後述）。

---

## Snapshot責務

- **正本はRuntime Snapshot（`ConciergeThread.recommendations`/`recommendations_v2`、JSONField）**。`append_chat`実行時に一度だけ書き込まれ、以後再計算されない。
- History経由で神社詳細へ遷移した際も、Fact/Interpretation/Action（`recommendation_reason_v4_detail`）は当時保存された値をそのまま表示する。Backend側のFact優先順位ロジックが将来変わっても、過去のSnapshotの表示内容は変わらない（`docs/core/recommendation-reason-contract.md`の既存方針と一致）。
- 推薦順位（配列順）も再計算しない。
- 例外: `action_state`（お気に入り・参拝済み・振り返り済み等の状態バッジ）のみ、Thread Detail取得時に現在のユーザー状態から都度計算する。これは「推薦理由の再生成」ではなく「現在のユーザーとその神社の関係」を表す別軸の情報であり、Snapshot正本方針と矛盾しない。
- **神社名・画像・営業情報等は、必要に応じて現在のShrine API（`getShrinePublicServer`/Mobile `GET /shrines/{id}/`）を参照する**。理由: これらは編集・修正される可能性があり、Snapshot時点の値が古くなりうるため。一方、Fact/Interpretation/Action（推薦理由）はその時点の相談文脈に紐づく解釈結果であり、現在の神社情報とは独立して保存・表示する。
- **削除・非公開になった神社の表示方針**: Shrine Detailページは既に`getShrinePublicServer`が失敗した場合に「神社の詳細情報が見つかりませんでした。」というfallback UIを表示する実装が存在する（`apps/web/src/app/shrines/[id]/page.tsx`）。History経由でもこの既存fallbackをそのまま利用する。Thread Detail一覧内の推薦神社カード側では、Shrine APIの現在情報が取得できない場合はSnapshot内の`name`/`address`をそのまま表示し、詳細への遷移リンクは維持する（遷移後にShrine Detail側のfallback UIが処理する）。
- **古いThreadでV4 Detailが欠落する場合のfallback**: 既存の`normalizeRecommendationReasonV4Detail`（Web: `buildShrineDetailReasonV4Sections.ts`、Mobile: `recommendationReasonV4.ts`）が`recommendation_reason_v4_detail`欠損・不正型を安全に`null`へ変換し、`hasStructured=false`のとき既存の`recommendationReasonDetail`/`reasonFacts`ベースの旧表示へ自動fallackする。History専用の新しいfallbackロジックは不要で、既存のものをそのまま再利用する。

---

## 情報設計

### 相談履歴一覧に表示する項目

`title` / `last_message`（先頭一部、既存Mobile実装は3行truncate） / `last_message_at` / `message_count`。相談本文全文は一覧に出さない（既存Mobile実装を踏襲）。

### 相談履歴詳細に表示する項目

- 会話履歴: `messages[]`（role/content/created_at）をそのまま時系列表示する。ユーザー自身の過去の入力であり、機密性は一覧より低いため全文表示してよい。
- 当時推薦された神社カード一覧: `recommendations`（`recommendations_v2`があればそちらを優先、既存Shrine Detail側の優先順位に合わせる）。

### 過去の推薦神社カードに表示する項目

- 神社名・所在地（現在のShrine APIが取得できればそちらを優先、できなければSnapshot値）
- Fact要約1行（`recommendation_reason_v4_detail.fact`から`pickReasonV4FactText`相当のロジックで1つだけ抽出。Interpretation/Actionはカードには出さず、詳細遷移後に見せる）
- `action_state`バッジ（既にBackendが計算済みの値をそのまま表示）
- 「神社の詳細を見る」リンク

### 神社詳細への遷移パラメータ

**新しいパラメータは追加しない。** 既存の`ctx=concierge&tid=<thread_id>`をそのまま使う。

- Web: `<Link href={`/shrines/${shrineId}?ctx=concierge&tid=${threadId}`}>`
- Mobile: 後述（Mobile設計参照）

Shrine Detail側は、遷移元がライブのConcierge結果画面か履歴画面かを区別せず、`tid`から同じ`getConciergeThreadServer`/`GET /concierge-threads/{id}/`で再取得する。**この設計により、Shrine Detail側のコードは無改修で済む。**

### WebとMobileで共通にする情報構造

Backend APIレスポンスの形状（`{id, title, last_message, last_message_at, message_count}` / `{..., messages, recommendations, recommendations_v2}`）は共通であり、Web/Mobileとも同じ値を消費する。プラットフォーム間で共有すべきは「どのフィールドから何を表示するか」という情報構造であり、実装コード自体を共有する必要はない（Hero Adapter/Shrine Detail Adapterと同じ考え方）。

推薦神社カードのFact要約抽出ロジック（`deity > shrine_history > goriyaku > history_theme`、`place_context`/`label`除外）は、Web/Mobile双方の既存Adapter（`reasonV4FactPriority.ts` / `recommendationReasonV4.ts`）をそのまま再利用する。History専用の新しい優先順位ロジックは作らない。

### consultationSummaryの表示範囲

Thread Detail画面内でのみ表示する（一覧には出さない）。Shrine Detail側の「①今回の相談の整理」は、既存の`ctx==="concierge"`ゲートと`recommendationReasonDetail`の仕組みをそのまま使うため、History経由でも無改修で動作する。

### 相談入力全文の表示・非表示ルール

- 一覧: 非表示（`last_message`の先頭のみ）
- Thread詳細: 表示する（自分自身の過去の入力であるため）
- Analytics送信: 相談本文・queryは一切送信しない（Analytics接続点の節を参照）

---

## Navigation契約

```text
履歴一覧
  ↓ Threadカードタップ
Thread詳細（会話履歴 + 推薦神社カード一覧）
  ↓ 神社カードタップ（ctx=concierge&tid=<thread_id>）
神社詳細（既存Shrine Detail、無改修）
```

- **ctx=concierge / tidの再利用可否**: 再利用可能（現状監査で確認済み）。Backend/Frontendとも「ライブ結果」と「履歴」を区別しない設計になっており、そのまま機能する。
- **不正または存在しないtid**: Thread Detail画面側では、fetchが404/権限エラーの場合は「この相談は見つかりませんでした」のようなError状態を表示する（Mobile既存の`StateCard`パターンを再利用）。Shrine Detail側では、既存の`getConciergeThreadServer`が401/403/404を`null`にfallbackする実装が既にあるため、無効なtidでも通常のDirect Navigation相当の表示に自然に落ちる（無改修）。
- **未ログイン・権限不一致時の挙動**: 一覧APIは`IsAuthenticated`のため、未ログインユーザーは履歴一覧へアクセスできない。History画面は表示前に認証状態を明示チェックし、未ログインならログイン導線を表示する（「現状監査で確認した事実」の潜在バグ参照。一覧取得関数の空配列fallackだけに頼らない）。詳細APIは`AllowAny`だが所有者一致が必須のため、他人のtidを直接叩いても404になる（既存の安全な挙動）。
- **Direct Navigationとの差異**: History経由の神社詳細遷移は常に`ctx=concierge`を伴うため、Direct Navigation（`ctx`なし）とは区別される。新しい差異は生まれない。
- **戻る操作時の遷移先**（要検討・母艦判断待ち）: Shrine Detail側の「閉じる」導線（`buildShrineClose({ctx, tid})`）は、`ctx=concierge&tid=X`というパラメータだけでは「ライブConciergeチャットから来た」のか「History Thread詳細から来た」のかを区別できない。現状のまま実装すると、Historyから神社詳細へ来たユーザーが「戻る」でライブのConcierge画面（`/concierge?tid=X`）へ送られてしまう可能性がある。この設計書では対応方針を確定させず、次の選択肢を母艦判断待ちとして残す。
  1. ブラウザ/Router標準の「戻る」に任せ、`buildShrineClose`のリンク先は変更しない（実装コストが最小）
  2. `ctx`の値を`concierge`のまま維持しつつ、追加で`from=history`のような軽量パラメータを足す（既存の`ctx` enumは変更しない）

---

## Web設計

- **一覧Route（案）**: `apps/web/src/app/mypage/history/page.tsx`（Server Component）。`getConciergeThreadsServer()`を呼ぶ前に認証状態を確認し、未ログインならログイン導線を表示する。正確なパス（`/mypage/history` か `/history` か）はIA判断のため母艦判断待ち。
- **Thread詳細Route（案）**: `apps/web/src/app/mypage/history/[tid]/page.tsx`（Server Component）。`getConciergeThreadServer(tid)`を呼び、`null`ならError状態を表示する。
- **Server/Client責務**: 一覧・詳細ともServer Componentでデータ取得する（既存Shrine Detailページと同じパターン）。推薦神社カードの表示自体はServer Componentで完結できる想定だが、将来的にインタラクション（展開/折りたたみ等）が必要になった場合のみ小さなClient Componentへ切り出す。
- **既存BFF再利用**: `getConciergeThreadsServer`/`getConciergeThreadServer`とその裏のBFF Route（`/api/concierge-threads`, `/api/concierge-threads/[id]`）をそのまま利用する。新規BFF Routeは不要。
- **Loading/Empty/Error**:
  - Loading: SSRのため専用ローディングUIは基本不要（Next.jsの`loading.tsx`規約を使うなら追加）
  - Empty: 「まだ相談履歴がありません」+ コンシェルジュへの導線（未ログインとは明確に区別する）
  - Error: 未ログイン→ログイン導線／取得失敗（tid不正等）→「見つかりませんでした」

---

## Mobile設計

- **既存consultation-history画面の責務**: 一覧表示のみ、データ取得元は無変更（`listConciergeThreads()`）。
- **ConsultationCardのonPress契約**: `Pressable`化し、`router.push({ pathname: "/consultation-history/[id]", params: { id: String(thread.id) } })`を追加する。
- **Thread詳細画面**: 新設する（`apps/mobile/app/consultation-history/[id].tsx`）。データ取得用に`getConciergeThread(id)`を`apps/mobile/lib/consultationHistory.ts`へ追加する必要がある（`GET /concierge-threads/{id}/`を叩く、`listConciergeThreads`と同じ実装パターン）。
- **推薦神社カードからShrine Detailへの遷移**: Mobileの既存Concierge→Shrine Detail連携（PR #2194, #2207）は、URLクエリではなく**Expo Routerのroute paramsへ構造化JSONをシリアライズして渡す**方式が既に採用されている（`serializeReasonV4Detail`等）。これは「相談本文（クエリ文字列）をURLへ載せない」という方針とは矛盾しない（route paramsに載るのはユーザー入力の生テキストではなく、Backend生成済みの構造化推薦理由であるため）。History Thread詳細画面は取得済みのThreadデータ（`recommendations`）をメモリ上に保持しているため、神社カードタップ時に**追加の通信なしで**既存Concierge画面と全く同じparams構造（`recommendationReasonV4Detail`, `reasonFacts`, `recommendationReasonDetail`, `actionSuggestionV4Preview`等）をShrine Detailへ渡せる。**Shrine Detail側（`apps/mobile/app/shrines/[id].tsx`）は無改修で済む。**
  - Web（tidから毎回サーバー再取得）とMobile（一度取得したデータをそのままparamsで渡す）とで transport は異なるが、渡している情報構造（fact/interpretation/action等の中身）は同一であり、方針7「情報構造を揃え、UI表現だけ分ける」を満たす。
- **Loading/Empty/Error**: 一覧画面と同じ`StateCard`コンポーネントを再利用する。

---

## Analytics接続点

このPRでは実装しない。次のAnalytics契約PRへ以下を引き渡す。

| イベント名（案） | 発火タイミング | 備考 |
| --- | --- | --- |
| `history_list_view` | 履歴一覧画面の表示 | |
| `history_thread_open` | Threadカードタップ→詳細画面表示 | `thread_id`のみ、`title`/本文は送らない |
| `history_recommendation_open` | 推薦神社カードタップ | `thread_id`, `shrine_id`, `rank`程度 |
| `history_shrine_detail_transition` | 神社詳細への遷移 | 既存の`shrine_detail_transition`イベントを再利用し、`source: "concierge_history"`（既存の`source: "concierge_result"`と対になる値）を追加する形を推奨。新規イベントを増やさない |

**送信禁止事項**: `raw_query`・相談本文・メッセージ内容など、ユーザーの自由記述テキストはいかなるAnalyticsイベントにも含めない（既存の`trackShrineDetailView`等の慣習と同一）。

---

## Web/Mobileの実装差分一覧

| 項目 | Web | Mobile |
| --- | --- | --- |
| 一覧画面 | 未実装（新設） | 実装済み（遷移導線なし） |
| Thread詳細画面 | 未実装（新設） | 未実装（新設） |
| Thread詳細取得API client | 実装済み(`getConciergeThreadServer`) | 未実装（新設: `getConciergeThread`） |
| 神社詳細への遷移方式 | tidからサーバー再取得（既存） | route paramsへJSON直渡し（既存Concierge連携を再利用） |
| Shrine Detail側の変更要否 | 不要 | 不要 |

---

## 実装PR分割案

1. **PR-History-Web**: `apps/web/src/app/mypage/history/page.tsx`（一覧）+ `[tid]/page.tsx`（詳細）+ 推薦神社カード表示（Fact要約含む）。BFF/Backend変更なし。
2. **PR-History-Mobile**: `apps/mobile/lib/consultationHistory.ts`へ`getConciergeThread(id)`追加 + `apps/mobile/app/consultation-history/[id].tsx`新設 + `ConsultationCard`への`onPress`追加。Shrine Detail側変更なし。
3. **PR-History-Analytics**（別PR、母艦の希望通りAnalytics契約は独立して進める）: 上記4イベントの実装。
4. **（任意・低優先度）PR-Cleanup**: `backend/temples/api/views/concierge_history.py` / `backend/temples/api/serializers/concierge_history.py` のデッドコード削除。History機能そのものとは無関係のため独立PRとするか判断が必要。

---

## 母艦判断待ち項目

1. Web/Mobileの正確なルートパス名・IA（`/mypage/history` か `/history` か等）
2. 一覧のページネーション方針（現状Backendは50件固定・オフセットページネーションなし。無限スクロール等を追加するか）
3. Shrine Detailの「戻る」導線がHistory経由かライブ経由かを区別する必要があるか（区別しないなら対応不要、区別するなら`ctx`拡張または新パラメータが必要）
4. 未認証匿名ユーザー（`concierge_anon_id`のみ）は一覧APIに`IsAuthenticated`のためアクセスできないが、Thread詳細APIは匿名IDでもアクセス可能という非対称性を、既存仕様として許容するか、別途対応するか
5. デッドコード（`concierge_history.py`のView/Serializer）の削除要否・タイミング
6. `apps/mobile/lib/consultationHistory.ts`の`ConciergeThreadListItem`型不整合（`created_at`/`updated_at`）の修正要否・タイミング
