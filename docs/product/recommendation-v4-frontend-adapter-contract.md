> **Status: Active**
>
> 本ドキュメントは、`recommendation_reason_v4_detail`をWeb/Mobileの画面へ表示変換する際のFrontend Adapter契約を管理する正本文書である。
>
> 正確な実装は、関連するWeb/Mobile実装およびテストを最終的な正本とする。本書は契約と実装の既知の差異を追跡する目的も兼ねる。

# Recommendation V4 Frontend Adapter Contract

## 目的

`docs/core/recommendation-reason-contract.md`が定義する`recommendation_reason_v4_detail`（Backend出力）を、Web/Mobileの画面へどう変換して表示するかを定義する。

Fact本文をどのFactキーから組み立てるか、structured表示と旧表示をどう切り替えるかを、Web/Mobileで同一の契約にすることを目的とする。

## 対象範囲

### 対象

- `recommendation_reason_v4_detail.fact`から表示用テキストを組み立てる優先順位
- structured表示（Fact/Interpretation/Action）と旧表示の切り替え条件
- fallback順序

### 対象外

- Backend側の`recommendation_reason_v4_detail`生成ロジック（`docs/core/recommendation-reason-contract.md`を参照）
- UIレイアウト・見出し文言そのもの
- ranking / Score

## Fact本文の組み立て契約

Fact本文は、以下の優先順位で最初に見つかった非空値を採用する。

```text
deity > shrine_history > goriyaku > history_theme
```

`place_context`（住所）と`label`（`place_context`へ落ちうる互換field）は、Fact本文の組み立て候補に含めない。住所は神社固有の由緒・祭神・意味的根拠ではなく、これを本文に使うと「神社の特徴」として誤って提示することになるため（詳細な経緯は`docs/audit/recommendation-reason-v4-quality-report.md`を参照）。

いずれのFactキーも空の場合、Fact本文は表示しない（住所や神社名だけで固有情報があるように見せない）。

## structured表示 / 旧表示の切り替え

`hasStructured`は、Fact本文・Interpretation本文・Action本文のいずれか1つ以上が非空の場合に`true`とする。

- `hasStructured === true`: structured表示（Fact/Interpretation/Action）を使う。旧表示（reasonFacts、consultationSummary以外の旧Detail文言）とは重複表示しない。
- `hasStructured === false`: 旧表示（`recommendation_reason_v4`文字列、`reasonFacts`、`recommendationReasonDetail`）へfallbackする。

## fallback順序

structured表示が成立しない場合のfallback順序は以下とする。

```text
1. recommendation_reason_v4_detail.reason_text
2. recommendation_reason_v4（文字列）
3. reasonFacts由来の解決済み理由
4. reason（旧文字列）
5. 固定fallback文言
```

## 実装状況（監査時点）

| Platform | 実装箇所 | Fact優先順位 | 状態 |
| --- | --- | --- | --- |
| Mobile | `apps/mobile/lib/recommendationReasonV4.ts`（`buildReasonV4Sections`） | `deity > shrine_history > goriyaku > history_theme` | 契約準拠（#2207で修正済み） |
| Web (Hero card) | `apps/web/src/features/concierge/buildHeroReasonV4Sections.ts`（`buildHeroReasonV4Sections`） | `deity > shrine_history > goriyaku > history_theme` | 契約準拠（#2208で修正済み） |
| Web (Shrine Detail page) | `apps/web/src/app/shrines/[id]/page.tsx` | 該当実装なし | **`recommendation_reason_v4_detail`を未使用。structured表示なし** |
| Web (Candidate/Compact card) | `ConciergeSectionsRenderer.tsx`（`ShrineCardCompact`経路） | 該当実装なし | 設計上structured表示の対象外（Heroのみ） |

Web (Hero card)はPR #2208で契約準拠済みである。Web (Shrine Detail page)は`recommendation_reason_v4_detail`未対応のため、契約と実装が一致していない既知の差異として残る。対応範囲と実装時期は母艦判断待ちとする。
