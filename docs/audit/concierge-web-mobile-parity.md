# Concierge Web / Mobile recommendation parity audit

> 更新: 2026-11-21 の表示契約実装は末尾 §11。§1–10 は PR #3499 時点の監査履歴。入力・認証等の範囲外事項は今回変更しない。

監査日: 2026-11-20 (Asia/Tokyo)。対象: 取得時の最新 `origin/develop`
`f5cd3d2a5a5f52ae8d2fc117b71fbfe941a876ea`。ブランチ:
`audit/concierge-web-mobile-parity`。

## 1. Executive summary

**結論: FAIL（無条件の platform parity は成立しない）。**

共通の入力・同じ候補集合・匿名状態・LLM 無効・score v3 shadow という固定条件では、
比較可能なシナリオの推薦 ID 集合・順位・説明は一致した。入力表現が違うシナリオも、
今回の候補では同じ推薦になった。ただし、それを一般的な同値性の証明とはしない。
Web の登録候補優先・重複除去は、混在候補の Backend 順序を変える。Mobile は同じ配列を
そのまま表示モデルへ写すため、同一応答でも並び方が一致しない反例を再現した。

本 PR は **テスト・合成 fixture・本監査書のみ**。Backend の順位・重み・DB・フィルター、
Compass、認証・課金、設定、production UI は変更していない。仕様が未確定の差は修正しない。

## 2. Current architecture and request paths

### Web

1. `apps/web/src/app/concierge/page.tsx` → `ConciergeClientFull.tsx`。
2. `ConciergeClientFull` の `baseFilters` (1023行付近): 選択 ID、trim した追加条件、
   文字列から導出する crowd / duration / free_text。
3. `apps/web/src/features/concierge/buildConciergeRequestPayload.ts::buildConciergeRequestPayload`
   (59行): query、top-level と filters の重複値、visit_preferences、visit_date、location。
4. `apps/web/src/features/concierge/hooks.ts::useConciergeChat.send`: trim、mode=need、
   誕生日/profile_context 削除、filters の null/undefined/空文字/空配列除去、thread_id 注入。
5. `apps/web/src/lib/api/concierge.ts::postConciergeChat` → `apiPost` → axios `/api`。
6. `apps/web/src/app/api/concierge/chat/route.ts::POST`: body を文字列のまま
   `djFetch(..., '/api/concierge/chat/')` へ転送。401 の refresh 経路も同じ body。
   `_anon_cookie_value` は応答 body から除いて HttpOnly cookie へ移す。

### Mobile

1. `apps/mobile/app/(tabs)/index.tsx` などの入口 → route params / origin session →
   `apps/mobile/app/(tabs)/concierge/index.tsx::ConciergeScreen`。
2. 同 screen の送信処理 (790–834行付近): query trim、空なら条件用既定文、
   `resolveGoriyakuTagIds`、`buildConditionFilters`、`buildConditionProfileContext`。
3. `apps/mobile/lib/conditionPayload.ts`: ご利益ラベル→タグ API ID、参拝スタイル→
   visit_style_tags、および全条件のラベル付き `extra_condition` 連結。
4. screen 内 `fetchConciergeRecommendations` (431行): need request を組み立て、
   `apps/mobile/lib/http.ts::post('/concierge/chat/', payload)`。
   base は `EXPO_PUBLIC_API_BASE_URL`（未設定時 `http://localhost:8000/api`）。
   この関数は `postAuth` を使用せず、Authorization の注入・token refresh はしない。

### Authoritative Backend

`backend/shrine_project/urls.py` の `api/` include → `temples/api/urls.py` の
`concierge/chat/` → `temples/api/views/compat.py::concierge_chat_compat` →
`temples/api_views_concierge.py::chat = ConciergeChatView.as_view()`。
既知の `temples/urls.py` だけを見て entry point と判断してはいけない。

`ConciergeChatView.post` → `normalize_concierge_request` → 誕生日関連 strip / mode / flow /
consultation interpretation → quota → location/radius → `_build_chat_candidates_pipeline`
→ `temples/services/concierge_chat.py::build_chat_recommendations` (709行)
→ extra-condition / structured preference 統合 → scoring / `_sort_chat_recommendations`
→ explanations / top-3 → instance ID 注入 / thread 保存 → `_build_chat_response`。

`concierge_chat_candidates.py::build_chat_candidates_with_eligibility` は Shrine の
`goriyaku_tags__id__in` で絞る (315行付近)。候補生成・eligibility と、候補内順位付けは別責務。
既定 radius は 8000m、1–50000m に clamp。既存 L3 テストが、radius を候補 DB の
hard filter に渡さないことを固定している。

## 3. Field-by-field payload comparison

以下の W は Web builder + send hook、M は Mobile screen + conditionPayload、
B は上記 Backend view / canonical contract を指す。効果は実装の読み取りとテストを区別した。

| Field / intent | Web source and transformation | Mobile source and transformation | Backend consumption / effect | Assessment |
| --- | --- | --- | --- | --- |
| `query` | needText を trim。日付だけなら空。条件があれば「追加した条件に合う神社を提案してください。」 | 入力を trim。条件だけなら「条件から合う神社を知りたい」。fetch 内は受け取った consultation を使用 | message があればそちら優先。need/interpretation、候補・順位・説明の主軸 | 通常相談は一致。条件だけの既定文は `DEFAULT_VALUE_DIFFERENCE`、意図未確定 |
| `mode`, `version`, `flow` | version=1、mode=need を hook で再固定。通常 flow 未送信 | version=1、mode=need、flow 未送信 | compat 指定を無効化。追加条件/タグあり→flow B、その他→A | mode/version は一致。同じ予定日だけでも M の extra により flow が異なる |
| birthday / `birthdate` | builder/send は top-level・filters の birthdate と profile_context を送らない | 条件の birthday を両方へ送る。保存プロフィールは context で補完。明示 birthday は extra にも連結 | 正規化後、view で birthdate=None、出生関連・derived/direction profile を削除。extra 内の文字列はこの strip 対象外 | Backend で不使用は意図された現行契約。M の送信残存は `INPUT_DIFFERENCE`。extra 内個人情報の扱いは未決 |
| benefit / `goriyaku_tag_ids` | 選択された DB ID 配列（複数可）。top-level と filters に複製 | 単一ラベルを `/goriyaku-tags/` で完全一致優先、なければ前方一致。失敗時 undefined。ID を複製しラベルを extra にも追加 | top-level 非空を優先、なければ filters。候補 DB hard filter と推薦説明/選択根拠に関与 | 同じ ID を得られれば共通制約。ラベル解決失敗・単一/複数選択は `INPUT_DIFFERENCE`、同一視しない |
| `extra_condition` | preset の自然文を改行連結・trim。top-level と filters | style / birthday / date / benefit / supportText を「参拝スタイル: … / …」で連結。supportText のみ trim | top-level 優先で昇格。keyword parser が sort_override / hard_filter / soft_signal / visit_style を抽出、説明の条件情報にも使用 | `INPUT_DIFFERENCE`。同じ意味でも文字列・flow が変わる。任意の連結内容に対する同値性は未証明 |
| `filters.free_text` | extra の複製（呼出 override は可能） | 連結 extra の複製 | 現行 view/canonical→ranker はこの field を独立で読まない | 名前が extra と似ていても別 field。現経路では追加効果なし |
| `visit_preferences` | Web preset mapping が canonical quiet/nature/reset/less_crowded/nearby/classic を送る | 未送信 | top-level のみ canonical vocabulary を正規化。extra 由来 tags と set union、重複加点なし | `INPUT_DIFFERENCE`。共通意図は parser 経由で表現可能だが UI/制約は一致しない |
| `visit_style_tags` | 通常 request では未送信 | condition から filters と profile_context.user_profile に送る | canonical 入力はこの filters field を visit_preferences として読まない。現 ranker の profile 補助も user_profile.visit_style_tags を参照しない | `INPUT_DIFFERENCE`。M の style 効果は extra parser から来る。フィールド名だけで同等と扱わない |
| `crowd` | extra に「ひとり」「空いて」があれば filters.quiet。現在の preset は trigger を含まない | undefined | 現行 chat の独立入力ではない。混雑意図は extra/preferences から作用 | `INPUT_DIFFERENCE`、独立した hard crowd filter と誤認しない |
| `duration_max_min` | extra に「駅近」があれば30。現在の preset は trigger を含まない | undefined | 現行 canonical/view は独立した時間制約として読まない | `INPUT_DIFFERENCE`。duration contract の拡張は別判断 |
| planned date / `visit_date` | plannedVisitDate が非空なら canonical field | trim 後 canonical field、さらに extra へ追加 | visit_date 優先、planned_visit_date は alias。L3 debug context と direction 計算。現 chat は birthdate を除去するため birthday 由来方位を計算できない | canonical 日付は一致し得るが extra/flow は異なる。日付が順位へ必ず効くとは言えない |
| location / accuracy | UserOrigin を共有 `toOriginPayload` へ | 同じ共有 helper。origin session / selector 由来 | finite・範囲内なら `{lat,lng}`。source/displayName/accuracy は両方で捨てる。B は direct lat/lng > nested location > area geocode。bias/距離が順位等に関与 | 共通 helper の意図された精度 metadata 省略。異なる実座標を同条件とは扱わない |
| profile context | send が削除 | condition 優先で不足する出生情報を global profile で補う。derived_profile を生成 | strip 後、出生情報・derived は除去。非出生 user tags は残るが現 profile scoring は derived/direction を読む | `INPUT_DIFFERENCE` + `BACKEND_BEHAVIOR`。保存プロフィールのみの fixture は有効推薦 semantics が一致 |
| optional / omitted / null | builder の undefined は JSON から消える。hook は filters の null/undefined/空文字/空配列を削除。空 filters 自体も削除 | JSON.stringify は undefined を消すが空 filters/context/ID 配列は残る。常時 profileContext を生成する caller | canonical の空制約は効果なし。top-level 空値は非空 filters から補完されるため「null で filter を無効化」は成立しない | wire 差は `NORMALIZATION_DIFFERENCE`。null と undefined を一般に同義とは扱わない |
| `thread_id`, language, radius, area | hook は既存 thread_id を注入。通常 language/radius/area は未送信 | thread_id 未送信、他も通常未送信 | thread所有/履歴、ja default、8000m default、area fallback。user の履歴は scoring の条件になり得る | transport/session 差。今回比較は既存 thread なし・匿名・履歴なし |

## 4. Deterministic scenarios and results

共有 fixture: `docs/audit/fixtures/concierge-web-mobile-parity.json`。
合成 Shrine IDs 31 / 24 / 12。既存 Shrine データの抽出ではない。

Web の実 builder→実 hook の JSON と、Mobile の実 condition helpers→screen 内の
`fetchConciergeRecommendations` の JSON を同じ fixture に照合。
Mobile の private functions は TypeScript AST から実宣言を読み取り、native UI/imports を
除いて transpile する。関数本体のコピーはない。pure dependency は実 module、HTTP は mock。
タグ ID は解決済みの値を固定し、タグ一覧 API の live lookup / failure は実行しない。
Mobile の外側の screen interaction / route state を実機で操作したテストではない。

Backend は実 URL resolver→compat wrapper→view→実 ranker→実 response builder を実行。
候補検索だけを固定3候補へ置換し、need_tags=['career']、LLM=false、SCORE_V3_MODE=shadow、
quota allowed を固定。実際の応答の identity/legacy reason/reason_facts/v4 text projection を
fixture の2種類の response に保存し、Backend 再実行と両 frontend の normalization に照合する。
API 内部配列と公開応答の ID 順序も照合する。

| Scenario | 有効 request semantics | Web IDs | Mobile IDs | ID-set / rank | Backend explanation comparison |
| --- | --- | --- | --- | --- | --- |
| text-only | 同値 | 31,24,12 | 31,24,12 | 1 / 1 | 一致 |
| benefit-tags | ID は同じ、M は extra も送信 | 31,24,12 | 31,24,12 | 1 / 1 | 今回一致 |
| additional-conditions | W quiet preset / M 補助条件の自然文。raw extra は異なる | 12,31,24 | 12,31,24 | 1 / 1 | 今回一致 |
| specified-location | 同値、35.68/139.76 | 31,24,12 | 31,24,12 | 1 / 1 | 一致 |
| planned-date | canonical date 同値、extra/flow は異なる | 31,24,12 | 31,24,12 | 1 / 1 | 今回一致 |
| empty-optionals | 同値、空配列/空文字の wire 差あり | 31,24,12 | 31,24,12 | 1 / 1 | 一致 |
| unavailable-location | 同値、location omitted | 31,24,12 | 31,24,12 | 1 / 1 | 一致 |
| invalid-location | 同値、範囲外座標は両 helper が除外 | 31,24,12 | 31,24,12 | 1 / 1 | 一致 |
| visit-style-quiet | W structured+legacy / M legacy、raw request 非同値 | 12,31,24 | 12,31,24 | 1 / 1 | 今回一致 |
| web-only-reset | M に同じ UI choice がない。比較対象条件が不足 | 31,24,12 | 31,24,12 | 1 / 1* | 今回一致* |
| mobile-birthday | W 未送信 / M explicit birthdate+extra | 31,24,12 | 31,24,12 | 1 / 1* | 今回一致* |
| mobile-saved-profile | wire は違うが strip 後同値 | 31,24,12 | 31,24,12 | 1 / 1 | 一致 |

`*` は **同じ入力条件の parity 判定対象外**。同じ結果になったことは、未対応入力に効果がない
ことや、全入力で一致することの証明ではない。7件の同値ケースは request semantics / ID / rank /
説明の一致を assert。残る5件は raw semantics が違うことを assert し、現 fixture 応答を固定。

ID-set agreement は `|set(W) ∩ set(M)| / |set(W) ∪ set(M)|` (Jaccard)。
Rank agreement は `同一 position の同一 ID 数 / max(len(W),len(M))`。
空配列同士の metric は定義せず、本比較の出力はすべて3候補。全件同一集合の小規模 fixture
なので ID-set=1 だけから候補 DB 検索の同値性は推定できない。

説明比較は shrine_id、reason、reason_facts、recommendation_reason_v4、v4 detail、
breakdown、breakdown_detail。毎回変わる recommendation_instance_id、trace、quota、
thread ID は equality の対象外。instance ID は既存 propagation contract のまま。

## 5. Frontend identity, ordering and final display

- `apps/web/src/lib/api/concierge/normalize.ts::normalizeRecommendations` は object を順に map。
  `reason` / one_liner / explanation の fallback を適用し、reason_facts を検証。
- `buildPayloadFromUnified.ts::normalizeRecommendation` (131行) は Shrine ID または Place ID を
  持たない候補を除外。`dedupeItems` (242行) は registered を先に確保し、place を後に追加。
  重複 Shrine ID / normalized Place ID を除去する。
- `components/ConciergeSectionsRenderer.tsx` (781行付近) は最初の registered を hero、
  残り registered を折りたたみ内、place を別枠に描画する。
- Mobile の `toRecommendationCard` (364行) / `normalizeRecommendations` (413行) は map のみ。
  `shrineId ?? shrine_id ?? id ?? place_id` を表示/遷移 ID に使用。screen の `results.map`
  (1046行付近) は全件を配列順に表示。

**標準の registered 3件**: 両 normalization で ID/order/reason facts/v4 text を維持。
Web DOM も secondary results 展開後、リンク ID と名称 DOM 順序が fixture 順であることを検証。
Mobile は実 mapping までを検証し、native rendering 自体は未実行。

**混在 + 重複の反例**:

- Backend 相当 fixture: `place:audit-place, shrine:31, shrine:12, shrine:31`
- Web sections / renderer のカテゴリ順: `shrine:31, shrine:12, place:audit-place`
- Mobile cards: `place:audit-place, shrine:31, shrine:12, shrine:31`
- entity ID-set=1、entity rank=0。登録 Shrine の集合だけも1だが、重複数は異なる。

これは frontend 変換の反例であり、現 candidate pipeline が必ずこの混在配列を返すという主張ではない。
Backend に既存 dedupe があることと、frontend の不変条件が弱いことは区別する。

**id-only legacy 反例**: `{id:88}` は Web sections から除去、M は shrineId='88' と解釈。
現 live registered producer の `id == shrine_id == Shrine.id` 契約では発生しないが、
legacy/代替 response を無条件に同じ identity contract として扱えない。

**explanation-only legacy 反例**: explanation.summary だけなら Web normalizer は採用するが
M の card mapper は汎用文に落ちる。現在の標準 v4 response での説明不一致を意味しない。

## 6. Root-cause findings

| Finding | Classification | Exact responsibility | Fact / intent |
| --- | --- | --- | --- |
| P-01 条件の連結・異なる field/選択数 | `INPUT_DIFFERENCE` | W builder、M `buildExtraConditionText` / `buildConditionFilters` / `resolveGoriyakuTagIds` | 観測事実。platform 全体として許容するか `UNDETERMINED` |
| P-02 condition-only query fallback | `DEFAULT_VALUE_DIFFERENCE` | W builder fallback、M `CONSULTATION_FALLBACK` / screen submit | ソースで確認。自然文の解釈差の影響は本 fixture では未検証 |
| P-03 birthday の送信残存と Backend 除去 | `INPUT_DIFFERENCE`, `BACKEND_BEHAVIOR` | M profile/filters builder、B `strip_concierge_birthdate_inputs` と view birthdate=None | 除去は既存テスト付き。M の extra 内 birthday は未解決 |
| P-04 Mobile Chat は `postAuth` を呼ばない | `API_TRANSPORT_DIFFERENCE` | M screen fetch / `http.ts::post`、W BFF POST / djFetch | Authorization/refresh 差は観測事実。実 cookie jar や deployed base URL の差は推測せず未検証 |
| P-05 registered 優先 / 重複除去 / id alias | `NORMALIZATION_DIFFERENCE` | W `normalizeRecommendation` / `dedupeItems`、M `toRecommendationCard` / map | 反例テストあり。既存 Web dedupe は明示的実装・既存回帰付き。全 platform の意図として承認済みとは断定しない |
| P-06 他候補の可視性 / place 別枠 | `DISPLAY_DIFFERENCE` | W `ConciergeSectionsRenderer`、M screen results.map | Web の折りたたみは既存回帰で明示的な product behavior。platform 間差の承認は `UNDETERMINED` |
| P-07 legacy explanation fallback | `NORMALIZATION_DIFFERENCE` | W normalize.ts::pickReason、M resolveRecommendationReason | legacy 反例のみ。v4 fixture は一致 |
| P-08 accuracy metadata と誕生日の責務 | `INTENTIONAL_PRODUCT_DIFFERENCE`（Concierge/Compass 間の責務分担） | shared userOrigin、B input strip、既存 birthdate/Compass contract tests | platform 間の隠れた補正ではない。accuracy の削除は両 platform 共通 |

認証主体が変わると quota/保存先だけでなく user 行動・reflection の scoring 条件も変わり得る。
同一の相談文だけを入力して「同条件」とすることはできない。この影響の具体的な本番発生率は未検証。

## 7. Intentional vs unintended differences

既存 contract で明確なのは、mode=need、Concierge の birthday 不使用、canonical preferences の
vocabulary / union / no double counting、共通 origin helper、Web の重複排除と折りたたみの現行動作。
Web の動作が明示的であることと、Web/Mobile の差を product が承認したことは別。

Mobile の異なる field 名を Web と同じと読み替える spec は見つからない。
Mobile UI の birthday/context 送信は Web/Backend の現行責務とずれているが、
削除・移行範囲（特に extra 内文言）をこの監査で発明しない。

`docs/core/concierge-spec.md` の birthdate rescue / compat 記述は現行 strip と衝突する。
本監査は実経路と `test_concierge_ignores_birthdate.py` を現行実装の根拠にした。
旧 spec を新しい product 判断に書き換えることは本 PR に含めず、競合をここに記録する。

## 8. Risks, limitations and unresolved Mother Ship decisions

1. **Order contract**: 登録優先・place 別枠・dedupe は許されるか。Backend の rank を絶対に保持するか。
   決定するまで Web dedupe の変更は実装しない。
2. **Input contract**: Mobile を canonical visit_preferences に揃えるか。単一 benefit と複数 benefit、
   Web reset/classic と Mobile の4 style、free-text 条件の対応範囲を決める。
3. **Birthday boundary**: Mobile の birthday UI/送信/profile/extra をどこまで Concierge から外すか。
   Compass の機能を巻き込まず、競合する旧 spec の更新主体を決める。
4. **Transport identity**: Mobile Concierge が匿名 post を使うことが製品意図か。認証変更は別 PR。
   cookie/anonymous credential の native 保持、deployed API base、auth parity の実機確認が必要。
5. **Dates/default query**: visit_date の効果、条件のみ fallback 文、extra の date/benefit 連結を
   recommendation semantics として保証するか。現 fixture の同順位だけで意図を確定しない。
6. **Legacy response**: id-only、place-only、recommendations_v2、top-level recommendations の対応方針。
   Web client は v2 を優先する経路を持ち、M fetch は body.data.recommendations のみを読む。
   標準 fixture は canonical data.recommendations。異なる v2 配列の最終表示 parity は未検証。
7. **Verification boundary**: 固定候補・匿名・履歴なし・LLM無効での検証。DB候補選択、地理的分布、
   live AI、active score-v3、auth 別履歴、native rendering、OS permission と実座標取得は保証しない。
   live AI を呼んで一致したとは主張しない。

既存 DB/本番設定へ接続しない。合成データは隔離 PostgreSQL の pytest transaction 内でのみ処理。
analytics 呼出は frontend mock。監査データを organic usage として投入・集計していない。

## 9. Recommended implementation PR boundaries

- 本 PR: audit / test / fixture だけで終了。
- product 決定後 PR-A: 入力 contract と Mobile canonical payload（birthday/profile/extra を含む）。
- 決定後 PR-B: identity/order/display 方針。混在候補と legacy fixtures を先に期待値へ昇格する。
- 必要なら PR-C: transport/auth identity。認証・課金レビューと native verification を別に行う。
- 旧 spec の整合は責務を確定してから既存文書へ反映。重複仕様文書を増やさない。

## 10. Evidence and test commands

新規テスト:

- `apps/web/src/features/concierge/__tests__/webMobileParity.test.tsx`: 実 payload の shared fixture
  一致、Backend 応答 projection の両表示 normalization、DOM order、混在/重複、id-only、legacy reason、
  invalid/NaN origin と accuracy 省略。
- `backend/temples/tests/api/test_concierge_web_mobile_parity.py`: 12 paired requests + null/空 optional 3件。
  実 API/実 ranker、canonical semantics、public response の順序、説明比較、共有応答 fixture を検証。

既存 contract evidence:

- Web buildConciergeRequestPayload / useConciergeChat.noBirthdate / hooksNormalization /
  buildPayloadFromUnified.dedupe tests。
- Web `ConciergeSectionsRenderer.otherRecommendations.test.tsx`: 初期非表示・展開/折りたたみ。
- Web chat route.test / route.anonCredential.test: raw body、refresh replay、応答の credential 分離。
- Mobile conditionPayload / recommendationReasonFacts / recommendationReasonV4 / userOrigin / http tests。
- Backend test_concierge_chat_request_normalization / test_concierge_chat_l3_context_contract /
  test_concierge_ignores_birthdate / test_concierge_visit_preference_contract /
  test_concierge_breakdown_rank_contract。

実行コマンド（repository root、Node/pnpm と backend requirements/test requirements を準備）:

```bash
pnpm -C apps/web test -- \
  src/features/concierge/__tests__/webMobileParity.test.tsx \
  src/features/concierge/__tests__/buildConciergeRequestPayload.test.ts \
  src/features/concierge/__tests__/buildPayloadFromUnified.dedupe.test.ts \
  src/features/concierge/__tests__/hooksNormalization.test.ts \
  src/features/concierge/__tests__/useConciergeChat.noBirthdate.test.tsx \
  src/features/concierge/components/__tests__/ConciergeSectionsRenderer.otherRecommendations.test.tsx \
  src/app/api/concierge/chat/__tests__
pnpm -C apps/mobile test -- \
  lib/__tests__/conditionPayload.test.ts \
  lib/__tests__/recommendationReasonFacts.test.ts \
  lib/__tests__/recommendationReasonV4.test.ts \
  lib/__tests__/userOrigin.test.ts lib/__tests__/http.test.ts
pnpm -C apps/web typecheck
pnpm -C apps/mobile typecheck
DISABLE_GIS_FOR_TESTS=1 USE_GIS=0 python -m pytest \
  backend/temples/tests/api/test_concierge_web_mobile_parity.py \
  backend/temples/tests/api/test_concierge_chat_request_normalization.py \
  backend/temples/tests/api/test_concierge_chat_l3_context_contract.py \
  backend/temples/tests/api/test_concierge_ignores_birthdate.py \
  backend/temples/tests/test_concierge_visit_preference_contract.py \
  backend/temples/tests/services/test_concierge_breakdown_rank_contract.py
```

今回のローカル環境では既定 DB host `db` が解決できず、別ポートの一時 PostgreSQL を作成し
`DATABASE_URL` をテストプロセスだけ上書きした。URL import に必要な固定依存
`app-store-server-library==3.1.2` も未導入だったため、一時 `--target` + `PYTHONPATH` で補完。
設定・lockfile・既存 venv は変更していない。環境ブロッカー解消後の最終結果は下記。

最終結果: Web **83 passed**、Mobile **94 passed**、Backend **93 passed**、
Web/Mobile typecheck **PASS**。新規テストの ESLint / Ruff も PASS。
追加で `.husky/pre-push` も実行し、OpenAPI lint は error なし、Web 契約テスト全体は
**249 files / 2403 passed / 10 expected fail**。ローカル pnpm の既定 Node 20.19.5 は
root engines (>=22.13.0) に対する警告を出した。Node 22.23.4 を明示した Web 新規17件・
Mobile 関連94件・両 typecheck も PASS。全 repository suite / build / full Backend mypy は未実行。


## 11. Recommendation order contract implementation — 2026-11-21

Base: `develop e69982870`（PR #3499）。Branch: `fix/concierge-recommendation-order-parity`。
Mother Ship 2026-11-20 の決定 A/B/C を実装。canonical rule は既存の
[identity contract §14](shrine-identity-compass-concierge-contract.md#14-concierge-presentation-contract--mother-ship-2026-11-20)
に集約する。

| 項目 | Web | Mobile |
| --- | --- | --- |
| Identity / first-occurrence dedup / partition | shared conciergeCandidates | 同じ shared adapter |
| 登録順序・rank | Backend 相対順、1から連番 | 同左 |
| 参考順序 | Backend 相対順、linked reference は既存互換で抑制 | 同左 |
| 登録 Hero | 最初の登録、残りは既存 secondary UI | 登録カード列の先頭 |
| 外部表示 | 「参考候補」、登録順位なし | 同左 |
| 外部詳細 | 既存 Place resolve route | 検証済み route がないため導線なし |
| 後発 metadata | 補完・置換しない | 同左 |
| legacy id-only / invalid/conflict | 登録表示・イベントなし | 同左 |

旧 §5 の混在反例は登録 `[31,12]`・参考 `[audit-place]` の同値出力になる。
2セクションの画面結合順と元の interleaved 配列が同じとは主張しない。
Web の後発重複からの explanation/instance/history 等の補完を削除し、最初の記録を保持する。
resolver の共有化は同じ実装の再利用。Backend ranking、Compass、payload、birthday、auth、billing は変更なし。

元の12 request/Backend fixtures は保持し、17 presentation fixtures を追加。
Web Hero/secondary/reference、Mobile 実表示関数、外部のみ/空の表示、ID/rank/instance、
impression dedup、quality attribution、detail/action safety を検証する。
入力・認証など表示以外の全体 parity が PASS になったとは主張しない。

### Validation

Node 22.23.4 / pnpm 9.12.3 で再検証済み。

- Web 全体: **249 files / 2427 passed / 10 expected fail**（既存の期待失敗）。
- Mobile 全体: **61 files / 785 passed**。
- Backend 既存 parity replay: **15 passed**（隔離一時 PostgreSQL）。Backend source の差分なし。
- Web/Mobile `typecheck`: **PASS**。
- 変更 Web ファイルの既存 ESLint: **PASS**。Mobile/shared は専用 lint script がないため、
  Web 相当の TS recommended / unused-vars / React hooks ルールを一時 ESLint API 設定で適用し **PASS**。
- OpenAPI lint: **error なし**。`git diff --check`: **PASS**。
- 未解決のテスト失敗なし。iOS/Android 実機、live Place resolve、全 Backend suite / mypy / build は未実行。

```bash
volta run --node 22.23.4 pnpm -C apps/web test:contract
volta run --node 22.23.4 pnpm -C apps/mobile test
volta run --node 22.23.4 pnpm -C apps/web typecheck
volta run --node 22.23.4 pnpm -C apps/mobile typecheck
volta run --node 22.23.4 pnpm lint:openapi
DISABLE_GIS_FOR_TESTS=1 USE_GIS=0 python -m pytest \
  backend/temples/tests/api/test_concierge_web_mobile_parity.py
```

Backend 検証はテストプロセスの DATABASE_URL を一時DBへ向け、終了後停止した。
未導入の既存固定依存 `app-store-server-library==3.1.2` は一時 target/PYTHONPATH で補った。
本番・既存 DB・設定・lockfile・既存 venv は変更していない。
再開時に `/private/tmp` の未コミット worktree が削除されていたため、永続 worktree へ復元し、
上記テストをすべて再実行してからコミットした。
表示以外の input/auth/birthday 等の既知差は、この実装の範囲外として残る。
