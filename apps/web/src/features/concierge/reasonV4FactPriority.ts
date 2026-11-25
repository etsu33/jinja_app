// apps/web/src/features/concierge/reasonV4FactPriority.ts
//
// Recommendation Reason V4のfactからFact本文用テキストを選ぶ、低レベルの共通変換関数。
// Hero Adapter(buildHeroReasonV4Sections)とShrine Detail Adapter(buildShrineDetailReasonV4Sections)の
// 両方から利用する。優先順位の実体をここ一箇所に集約し、画面ごとの独自実装による優先順位の乖離を防ぐ。
//
// 優先順位: deity > shrine_history > goriyaku > history_theme
// place_context(住所)とlabel(place_contextへ落ちうる互換field)はFact本文の候補にしない。
// 理由は docs/product/recommendation-v4-frontend-adapter-contract.md を参照。
//
// この優先順位はどのfieldを「採用するか」の選択ロジックであり、Recommendation Signal
// Authority(docs/product/recommendation-signal-authority.md §6/§8)を再決定するものでは
// ない。deity/shrine_historyはExplanation-only、goriyaku/history_themeはRanking-related
// Signalという正本の分類(§8)は、ここでは変えず、どちらが採用されたかをsourceとして併せて
// 返すだけに留める(Result IA v2 §15 PR5、Finding 9)。

export type ReasonV4FactLike = {
  deity?: string | null;
  shrine_history?: string | null;
  goriyaku?: string | null;
  history_theme?: string | null;
} | null | undefined;

export type ReasonV4FactSource = "deity" | "shrine_history" | "goriyaku" | "history_theme";

export type ReasonV4Fact = {
  text: string;
  source: ReasonV4FactSource;
};

function clean(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const s = value.trim();
  return s.length ? s : null;
}

// Signal Authority正本§8: deity/shrine_history(および同§6のknowledge_deities/
// knowledge_histories)はExplanation-only。Rank/Eligibilityに一切寄与しない。
export function isExplanationOnlyFactSource(source: ReasonV4FactSource): boolean {
  return source === "deity" || source === "shrine_history";
}

export function pickReasonV4Fact(fact: ReasonV4FactLike): ReasonV4Fact | null {
  if (!fact) return null;

  const deity = clean(fact.deity);
  if (deity) return { text: deity, source: "deity" };

  const shrineHistory = clean(fact.shrine_history);
  if (shrineHistory) return { text: shrineHistory, source: "shrine_history" };

  const goriyaku = clean(fact.goriyaku);
  if (goriyaku) return { text: goriyaku, source: "goriyaku" };

  const historyTheme = clean(fact.history_theme);
  if (historyTheme) return { text: historyTheme, source: "history_theme" };

  return null;
}

export function pickReasonV4FactText(fact: ReasonV4FactLike): string | null {
  return pickReasonV4Fact(fact)?.text ?? null;
}
