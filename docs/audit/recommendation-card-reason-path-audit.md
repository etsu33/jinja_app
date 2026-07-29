> **Status: Audit / Read-only**
>
> 本ドキュメントは、Recommendation Cardの理由表示が実際にどの経路・型・条件で生成・表示されているかを、コード読み取りのみで監査した記録である。
> 監査時点の実装事実を記録するものであり、監査時点で未実施の実装・修正は含まない。
> 実装可否・優先順位は本ドキュメントでは決定せず、母艦判断事項として分離する。

# Recommendation Card Reason Path Audit

## 監査メタデータ

- 監査日: 2026-07-29
- 対象コミット: `3b72bcd83f9e0aebfe51fe4e523d2ca2a40d16a2`(develop HEAD, PR #2188反映済み)
- 監査ブランチ: `audit/recommendation-card-three-slot-contract`
- 監査範囲: Phase 1(ブランチ準備)、Phase 2(現行構造監査)
- 実施したこと: コード検索・読み取り・呼び出し元追跡のみ
- 実施していないこと: ソースコード変更、テスト変更、既存ドキュメント変更、固定3枠化の実装

## 背景・調査動機

Recommendation Cardの理由表示について、「候補神社データ → Recommendation Reason生成 → reason_items生成 → 選別・並び替え・件数制限(`_take3()`) → Serializer → Web/Mobile表示」という単一パイプラインを前提とした固定3枠化(SHRINE_FEATURE / INTERPRETATION / ACTION の3type)の検討が持ち上がった。

実装着手前に、この前提がコード上の事実と一致するかを確認するために本監査を実施した。

結論として、**この前提となる単一パイプラインおよび `reason_items` 配列、`INTERPRETATION`/`ACTION` というtype自体がコード上に存在しない**ことが判明した。以下に詳細を記録する。

---

## 1. 現在アクティブな4つの理由生成系統

Recommendation Reasonに関わるコードは、統合されていない4つの並行系統として存在する。

### 系統A: `_take3()` / `concierge_explanations.py`

- 定義: [backend/temples/services/concierge_explanations.py:35](../../backend/temples/services/concierge_explanations.py)(`_take3()`)
- 生成: `build_explanation_for_chat_rec()`(358行)/ `build_explanation_for_plan_rec()`(464行)
- 出力: `rec["explanation"] = {version, summary, reasons[], disclaimer}`
- `reasons[]`の各要素は `code` フィールドを持つ(USER_CONDITION / USER_SELECTED_TAG / AREA_MATCH / GOGYOU_CONTEXT / HISTORY_CONTEXT / ELEMENT_MATCH / NEED_MATCH / WISH_MATCH / VISIT_STYLE_MATCH / REASON_SOURCE / SHRINE_FEATURE のいずれか)
- `_take3()`はappend後の配列をstrength優先度→code優先度でsortし、先頭3件を返す単純slice。fallback補充・重複排除はしない

### 系統B: `_build_reason_facts()` / `concierge_chat_ranking.py`

- 定義: [backend/temples/services/concierge_chat_ranking.py:544](../../backend/temples/services/concierge_chat_ranking.py)
- 出力: `rec["reason_facts"]` / `rec["_reason_facts"]`(同一内容の複製)、**配列** `List[Dict]`(各要素は `type/label/evidence/score/is_primary`)
- typeは history_theme / culture_translation / user_selected_tag / need_tag / goriyaku_tag / text_hint / element(小文字snake_case、系統Aのcodeとは別名前空間)
- `_resolve_primary_reason()`が空配列時に `{type:"fallback", label_ja:"近い候補"}` を合成し、必ず1件以上になるよう補完する
- この配列は [concierge_explanation_payload.py:229](../../backend/temples/services/concierge_explanation_payload.py)(`build_explanation_payload()`)で正規化され、`primary_reason`(dict|null)と`secondary_reasons`(配列、`[:3]`)に分割され `rec["_explanation_payload"]` にセットされる。系統Aはこの`_explanation_payload`を入力として利用する

### 系統C: `recommendation_reason_v4.py`(現行正本)

- 定義: [backend/temples/services/recommendation_reason_v4.py:488](../../backend/temples/services/recommendation_reason_v4.py)(`build_recommendation_reason_v4()`)
- 正本ドキュメント: [docs/core/recommendation-reason-contract.md](../core/recommendation-reason-contract.md)(Status: Active)
- 出力契約: 単一dict `{reason_text, fact, interpretation, action, used_fact, used_interpretation, used_action, source, quality}`。**配列(reason_items)ではなく、typeを持つ複数要素構造でもない**
- API到達範囲(重要な事実):
  - 構造化本体(`fact`/`interpretation`/`action`込み)は [concierge_chat.py:690](../../backend/temples/services/concierge_chat.py)(`_build_reason_v4_preview_payload()`)経由で `recs["_debug"]["reason_v4_preview"]` にのみ格納される(debug限定)
  - 通常の `rec` に付与されるのは [concierge_chat.py:408](../../backend/temples/services/concierge_chat.py)(`_attach_recommendation_reason_quality()`、686行で無条件呼び出し)による `rec["recommendation_reason_v4"] = str(preview.get("reason_text") or "")` という**文字列のみ**、および `rec["recommendation_reason_quality"]`(品質dict)
  - `fact`/`interpretation`/`action`の構造化データそのものは、通常の推薦アイテムには一切乗らない

### 系統D: `build_reason_facts()` / `api_views_concierge.py`(デッドコード候補)

- 定義: [backend/temples/api_views_concierge.py:437](../../backend/temples/api_views_concierge.py)
- 出力: オブジェクト形状 `{version, primary_axis, matched_need_tags, shrine_benefit, shrine_feature, visit_fit, matched_element, distance_label, popularity_label, fallback_reason, confidence}`
- Web([apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts:39](../../apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts))・Mobile([apps/mobile/app/concierge/index.tsx:51](../../apps/mobile/app/concierge/index.tsx))の`reason_facts`型定義はこのオブジェクト形状と一致する
- しかし本関数は `__all__`(api_views_concierge.py:1189)にも含まれず、`backend/temples/api/views/__init__.py`のimportにも含まれず、**コード全体を検索してもこの`def`行以外に呼び出し箇所が存在しない**。詳細は「6. デッドコード候補」参照

---

## 2. Web本番の実表示経路

- 実装コンポーネント: [apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx](../../apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx)(789-1009行)
- **`PrimaryRecommendationCard.tsx`は本番経路からimportされておらず未使用**(詳細は「6. デッドコード候補」参照)
- データ経路:
  1. [buildPayloadFromUnified.ts:139](../../apps/web/src/features/concierge/buildPayloadFromUnified.ts) `pickFirstString(r?.reason)` により `heroItem.description = rec.reason`(旧型文字列)のみを抽出。`explanation`/`reason_facts`/`recommendation_reason_v4`は`heroItem`に転記されない
  2. `ConciergeSectionsRenderer.tsx`が [buildRecommendationReasonViewModel.ts](../../apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts) を呼び出し、`needTags`(相談入力タグ)ベースの独自テンプレート文(`buildReasonNarrative.ts`等)を生成する
  3. `heroItem.description`(=`rec.reason`)は [packages/shared/recommendationReasonDisplay.ts](../../packages/shared/recommendationReasonDisplay.ts) 経由で`secondaryReason`/`summary`として画面表示される
- 結論: **Web本番の理由文は `rec.reason`(旧型文字列)+ needTagsベースの独自テンプレートで構成され、系統A(`explanation.reasons[]`)・系統B(`reason_facts`)・系統C(`recommendation_reason_v4`)のいずれも本番描画では消費されていない**

## 3. Mobile本番の実表示経路

- 実装コンポーネント: [apps/mobile/app/concierge/index.tsx](../../apps/mobile/app/concierge/index.tsx)(`ResultCard`, 461行 / `toRecommendationCard`, 365行)。[apps/mobile/app/shrines/[id].tsx](../../apps/mobile/app/shrines/[id].tsx) に同種ロジックが重複実装されている
- Mobileが実際に画面へ反映する唯一の実データフィールドは `recommendation_reason_v4`(系統C由来の文字列)
- `reason_facts`(系統B由来の配列)へは `Array.isArray(reasonFactsRaw) ? (reasonFactsRaw[0] ?? null) : reasonFactsRaw` という変換コードが存在するが、取り出した先頭要素は`{type,label,evidence,score,is_primary}`形状であり、その後アクセスする`shrine_feature`等のプロパティは存在しないため常に`undefined`になる(詳細は「4. reason_factsの型不整合」参照)
- `slice(0,3)`による理由項目の3件制限コードは存在するが、入力が実質常に空になるため事実上デッドパス
- Mobile独自の最終フォールバック文言 `"相談内容と神社情報をもとに選ばれた神社です。"` が存在する(Web側には同一文字列なし)
- 結論: **Mobile本番の理由表示は `recommendation_reason_v4`(文字列)のみに依存し、`reason_facts`の詳細表示は型不整合により死んだパスになっている**

## 4. `_take3()` が本番表示へ影響しないことの記録

- `_take3()`は系統A(`explanation.reasons[]`)にのみ作用する
- Web本番経路(`ConciergeSectionsRenderer.tsx`)・Mobile本番経路(`concierge/index.tsx`)のいずれも `rec.explanation` を読むコードが存在しない(grep結果0件、`heroItem`に`explanation`自体が転記されていない)
- したがって **`_take3()`の挙動(3件制限・sort順)を変更しても、現行のRecommendation Card表示には影響しない**。これは固定3枠化の設計対象を検討する上で重要な事実である

## 5. `reason_items` が実在しないことの記録

- リポジトリ全体(backend / apps/web / apps/mobile)を `reason_items` / `reasonItems` で検索した結果、**ヒット0件**(PILライブラリ内の無関係な偽陽性を除く)
- `INTERPRETATION` / `ACTION` という文字列定数・Enum値もリポジトリ全体で検索したが、系統Cの出力dict内のキー名 `interpretation` / `action`(単なる辞書キーであり、type列挙値ではない)以外に存在しない
- `SHRINE_FEATURE` は存在するが、これは系統Aの `code` 値の1つであり、系統C(recommendation_reason_v4)とは無関係な別系統に属する
- 結論: **「reason_items配列 + SHRINE_FEATURE/INTERPRETATION/ACTIONの3type構造」はコード上に実在しない**。固定3枠化はゼロからの新設計になる

## 6. `reason_facts` の型不整合(Contract Drift)

- Backend実データ: [concierge_chat_ranking.py:1440](../../backend/temples/services/concierge_chat_ranking.py) `rec["reason_facts"] = reason_facts` は**配列**(`List[{type,label,evidence,score,is_primary}]`)
- Web型定義: [buildRecommendationReasonViewModel.ts:39-50](../../apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts) は `reason_facts` を**オブジェクト**(`{primary_axis, shrine_feature, shrine_benefit, visit_fit, matched_element, distance_label, popularity_label, confidence, ...}`)として型付け
- Mobile型定義: [concierge/index.tsx:51-66](../../apps/mobile/app/concierge/index.tsx) も同一のオブジェクト形状で型付け(Webと一致)
- この型定義は、実際には呼び出されていないデッドコード `build_reason_facts()`(api_views_concierge.py:437)の出力形状と一致する。**Web/Mobile双方が、実データではなくデッドコードの出力形状を型付けしてしまっている**
- 実行時の影響: `rec.reason_facts?.shrine_feature` 等のプロパティアクセスは、配列に対して行われるため常に`undefined`を返す。例外は発生しないが、意図した値は一切取得できない

## 7. OpenAPI契約の欠落

- `ConciergeChatView`([api_views_concierge.py:564-569](../../backend/temples/api_views_concierge.py))は `@extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})` のみで、フィールド単位の契約は未定義
- `ConciergePlanResponseSerializer`([serializers/concierge.py:115-127](../../backend/temples/serializers/concierge.py))・`schema.yml`(1476-1496行)は `query/transportation/main/alternatives/route_hints` のみを宣言し、実際にレスポンスへ含まれる `ok/data/stops/recommendations/explanation/reason_facts/_explanation_payload/recommendation_reason_v4` 等は**未定義**
- `ConciergePlanView`は`@extend_schema`でSerializerを指定しているが、実装は`Response(body,...)`で生dictをそのまま返すため、**Serializerによる実フィールドフィルタ・バリデーションは行われていない**(ドキュメント目的のみ)
- `reason_facts`/`explanation`/`_explanation_payload`/`recommendation_reason_v4`専用のSerializerはbackend全体に存在しない
- 一方、`_explanation_payload`(アンダースコア始まり=内部用に見えるキー)が実HTTPレスポンスに含まれることは、`test_concierge_chat_need_breakdown_contract.py:289`(`assert "_explanation_payload" in rec`、実Djangoテストクライアント経由)によって契約テスト化されている。これはOpenAPIには一切現れない「テストのみが握っている契約」である

## 8. Web・Mobile間の表示差異

| 項目 | Web | Mobile |
|---|---|---|
| 本番コンポーネント | `ConciergeSectionsRenderer.tsx` | `concierge/index.tsx: ResultCard`(`shrines/[id].tsx`に重複実装) |
| 実データの理由フィールド | `rec.reason`(旧文字列)+ needTagsベース独自テンプレート | `recommendation_reason_v4`(文字列)のみ |
| `reason_facts`の扱い | 型不整合により無視 | 型不整合により無視(配列→先頭要素取得の変換コードはあるが結果的に無効) |
| `explanation.reasons[]`の扱い | 型定義のみ、読むコードなし | 型定義自体なし |
| 空配列/0件時の挙動 | needTagsベース汎用文で自動的に埋まる(明示fallbackなし) | ブロック非表示、または独自フォールバック文言 |
| フォールバック文言 | Web独自(needTagsテンプレート由来) | Mobile独自(`"相談内容と神社情報をもとに選ばれた神社です。"`)、Webと非共有 |
| ラベル文言統一性 | — | Mobile内でも画面間で不統一(「根拠として見ている情報」/「選定のポイント」) |

**共通点**: `reason_facts`型定義の誤り(デッドコード形状の参照)はWeb/Mobile共通。実装・フォールバック文言・ラベルは完全に非共有。

## 9. デッドコード候補

| 対象 | 判定根拠 |
|---|---|
| `build_reason_facts()`([api_views_concierge.py:437](../../backend/temples/api_views_concierge.py)) | `__all__`未掲載、`backend/temples/api/views/__init__.py`のimport対象外、リポジトリ全体grepで呼び出し箇所なし(定義行のみヒット)。名称が酷似する`_build_reason_facts`(concierge_chat_ranking.py、アンダースコア付き)とは別関数であり混同注意 |
| `PrimaryRecommendationCard.tsx`([apps/web/src/features/concierge/components/PrimaryRecommendationCard.tsx](../../apps/web/src/features/concierge/components/PrimaryRecommendationCard.tsx)) | 自ファイル以外からのimportが存在しない |
| `apps/web/src/viewmodels/conciergeToShrineList.ts` → `ConciergeShrineCard` | 本番ルートでの利用箇所なし。`apps/web/src/app/debug/concierge-fixture/page.tsx`(デバッグ用固定fixtureページ)とStorybookからのみ参照 |
| explanation.reasons[]内のcode: `START_POINT` / `DISTANCE` / `POPULARITY` / `SCORE` | `code_pri`優先度マップに定義はあるが生成箇所が存在しない。`DISTANCE`/`SCORE`は`test_concierge_need_contract.py:860,862`で「出現しないこと」を明示的にアサートしており、未使用が契約として固定化されている |

これらは監査時点での事実の記録であり、削除可否は母艦判断とする。

## 10. 固定3枠実装を保留する理由

1. 前提となる「reason_items配列 + SHRINE_FEATURE/INTERPRETATION/ACTIONの3type」構造がコード上に実在しない(セクション5)
2. `_take3()`を変更しても本番表示に影響しない(セクション4)。3枠化の実装対象がそもそも本番表示経路と接続されていない
3. 本番のRecommendation Card理由文は、調査対象のいずれの系統(A/B/C)にも依らず、旧型文字列(`rec.reason`)とクライアント側独自テンプレートで構成されている(セクション2, 3)
4. `reason_facts`の型不整合(セクション6)という既存の契約ドリフトが未解消のまま新構造を追加すると、同種の齟齬を重ねるリスクがある
5. OpenAPI契約が現状全般的に欠落しており(セクション7)、新設する`reason_items`契約をどこにどう固定するかの土台がない

以上より、固定3枠化は「母艦判断事項(セクション12)を先に確定し、既存の契約ドリフトを解消したうえで着手する」のが安全と判断する。本監査ではこの判断の実装(コード変更)は行っていない。

## 11. `recommendation_reason_v4` を正本候補として記録

- [docs/core/recommendation-reason-contract.md](../core/recommendation-reason-contract.md)が現行の意味生成正本として明記しているのは `backend/temples/services/recommendation_reason_v4.py` である
- Fact / Interpretation / Actionの3層構造という概念は、`_take3()`系(系統A)ではなく**この`recommendation_reason_v4.py`の出力契約(`fact`/`interpretation`/`action`)にすでに存在する**
- ただし現状は構造化本体が`_debug.reason_v4_preview`止まりで、通常応答には`reason_text`という文字列のみが流れている(セクション1系統C)
- 固定3枠化を検討する場合、`_take3()`(系統A、本番未接続)を土台にするのではなく、**`recommendation_reason_v4.py`の`fact`/`interpretation`/`action`構造をdebug限定から通常応答へ格上げする方向**の方が、既存の正本ドキュメントと矛盾しない可能性が高い。これは母艦判断事項として記録するに留め、本監査では方向性の提案のみとする

## 12. 母艦判断事項(未確定事項の分離)

1. Factがない場合も必ずFact枠を表示するか
2. Fact不足fallbackをFact typeとして返すか
3. fallback専用typeを新設するか
4. Interpretationがない場合の代替文をどう定義するか(現状「INTERPRETATION」という独立typeは存在しない)
5. Actionがない場合の代替文(同上、「ACTION」という独立typeも存在しない)
6. 常に3件返すか、1〜3件可変長を許容するか
7. 配列順をAPI契約として固定するか(現状OpenAPI未定義)
8. typeの重複を禁止するか(現状`_take3()`・`reason_facts`とも重複排除なし)
9. Web・Mobileを同一PRで移行するか、段階的に分けるか
10. 既存クライアントとの互換性(`recommendation_reason_v4`文字列、`rec.reason`旧文字列)をどう保つか、旧フィールドの互換維持期間をどう設定するか
11. analyticsが配列indexに依存していないか(本監査では未調査、別監査が必要)
12. `build_reason_facts()`(デッドコード)と、それに追従したWeb/Mobile型定義の契約ドリフトをどう解消するか(型定義を実データ形状に合わせるか、Backend側にオブジェクト変換層を新設するか)
13. `concierge_plan.py:584-593`の`try/except`が`explanation`生成失敗を握りつぶし200 OKで返している挙動を許容するか
14. `recommendation_reason_v4.py`の`fact`/`interpretation`/`action`構造をdebug限定から通常応答へ格上げする方向性を採用するか(セクション11)
15. 旧経路(系統A `_take3()`/`explanation.reasons[]`、系統D `build_reason_facts()`)の削除順序・削除可否

## 13. 実装状況

- 本ドキュメント作成時点で、ソースコード・テスト・既存ドキュメントへの変更は一切行っていない
- 固定3枠化の実装には着手していない
- 本ドキュメントは監査記録であり、上記「母艦判断事項」の決定を経てから実装フェーズへ進むことを前提とする

## 関連ドキュメント

- [docs/core/recommendation-reason-contract.md](../core/recommendation-reason-contract.md) — 現行正本
- [docs/audit/recommendation-reason-v4-contract.md](recommendation-reason-v4-contract.md) — Archive(v4導入時設計)
- [docs/audit/recommendation-v5-design.md](recommendation-v5-design.md) — Archive(未実装のv5設計)
