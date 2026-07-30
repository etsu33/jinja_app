// apps/web/src/features/concierge/reasonV4FactPriority.ts
//
// Recommendation Reason V4のfactからFact本文用テキストを選ぶ、低レベルの共通変換関数。
// Hero Adapter(buildHeroReasonV4Sections)とShrine Detail Adapter(buildShrineDetailReasonV4Sections)の
// 両方から利用する。優先順位の実体をここ一箇所に集約し、画面ごとの独自実装による優先順位の乖離を防ぐ。
//
// 優先順位: deity > shrine_history > goriyaku > history_theme
// place_context(住所)とlabel(place_contextへ落ちうる互換field)はFact本文の候補にしない。
// 理由は docs/product/recommendation-v4-frontend-adapter-contract.md を参照。

export type ReasonV4FactLike = {
  deity?: string | null;
  shrine_history?: string | null;
  goriyaku?: string | null;
  history_theme?: string | null;
} | null | undefined;

function clean(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const s = value.trim();
  return s.length ? s : null;
}

export function pickReasonV4FactText(fact: ReasonV4FactLike): string | null {
  if (!fact) return null;
  return (
    clean(fact.deity) ??
    clean(fact.shrine_history) ??
    clean(fact.goriyaku) ??
    clean(fact.history_theme)
  );
}
