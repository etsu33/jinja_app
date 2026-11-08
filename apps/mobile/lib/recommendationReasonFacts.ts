export type ConciergeReasonFact = {
  type: string;
  label: string;
  // Backend が返す表示用の日本語名。古いデータでは無いことがある。
  label_ja?: string;
  evidence: string[];
  score: number;
  is_primary?: boolean;
  // 相談と一致した神社のご利益の名前(#3451)。古いデータでは無いことがある。
  matched_benefit_names?: string[];
};

export type ConciergeReasonFacts = ConciergeReasonFact[];

function trimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function normalizeRecommendationReasonFacts(raw: unknown): ConciergeReasonFacts {
  if (!Array.isArray(raw)) return [];

  return raw.flatMap((item): ConciergeReasonFact[] => {
    if (!item || typeof item !== "object" || Array.isArray(item)) return [];

    const value = item as Record<string, unknown>;
    const type = trimmedString(value.type);
    const label = trimmedString(value.label);
    if (!type || !label) return [];
    const labelJa = trimmedString(value.label_ja);

    const evidence = Array.isArray(value.evidence)
      ? value.evidence
          .map(trimmedString)
          .filter((entry): entry is string => entry !== null)
      : [];
    const score =
      typeof value.score === "number" && Number.isFinite(value.score)
        ? value.score
        : 0;

    return [{
      type,
      label,
      ...(labelJa ? { label_ja: labelJa } : {}),
      evidence,
      score,
      ...(typeof value.is_primary === "boolean"
        ? { is_primary: value.is_primary }
        : {}),
      ...(Array.isArray(value.matched_benefit_names)
        ? {
            matched_benefit_names: value.matched_benefit_names
              .map(trimmedString)
              .filter((name): name is string => name !== null),
          }
        : {}),
    }];
  });
}

export function findPrimaryReasonFact(
  facts: ConciergeReasonFacts | null | undefined,
): ConciergeReasonFact | null {
  return facts?.find((fact) => fact.is_primary === true) ?? null;
}

const DISPLAY_LABEL_BY_TYPE: Record<string, string> = {
  element: "生年月日との相性",
  need_tag: "相談との一致",
  user_selected_tag: "明示した条件",
  goriyaku_tag: "ご利益・意味",
  history_theme: "神社固有の文脈",
  text_hint: "ご利益・意味",
  visit_style: "参拝との相性",
  fallback: "参考情報",
};

export type ReasonFactItem = {
  // React の key 用。「表示名＋label（英語の内部名）」で一意。
  key: string;
  label: string;
  // 表示名と同じ文字列になるときは null（同じ語を2回並べないため、画面では値を出さない）。
  value: string | null;
};

/**
 * 「根拠として見ている情報」の表示行を作る。
 *
 * Backend は同じ相談テーマについて、ご利益タグでの一致(goriyaku_tag)と説明文での一致(text_hint)を
 * 別の根拠として両方返す（生データを両方残す設計）。モバイルではどちらも「ご利益・意味」と表示するため、
 * 表示名＋label が同じ根拠はここで1行にまとめる。
 * - 比較には label（英語の内部名）を使う。日本語名は表記揺れでまとまらない可能性があるため
 * - is_primary: true の根拠があればそちらを残す（行の位置は最初に現れた位置のまま）
 * - 値は label_ja（日本語名）を表示し、無ければ label を表示する
 * - 値が表示名とまったく同じ文字列になるときは value を null にする（例: element の「生年月日との相性」）
 * - 件数の絞り込み(slice)は呼び出し側で、まとめた後に行う
 *
 * まとめる処理はこの関数の中だけで行う。findPrimaryReasonFact やイベント送信は生データのまま扱う。
 */
export function buildReasonFactItems(facts: ConciergeReasonFacts | null | undefined): ReasonFactItem[] {
  const order: string[] = [];
  const chosen = new Map<string, { displayLabel: string; fact: ConciergeReasonFact }>();

  for (const fact of facts ?? []) {
    const displayLabel = DISPLAY_LABEL_BY_TYPE[fact.type];
    if (!displayLabel) continue;

    const key = `${displayLabel}-${fact.label}`;
    const current = chosen.get(key);
    if (!current) {
      order.push(key);
      chosen.set(key, { displayLabel, fact });
    } else if (current.fact.is_primary !== true && fact.is_primary === true) {
      chosen.set(key, { displayLabel, fact });
    }
  }

  return order.map((key) => {
    const { displayLabel, fact } = chosen.get(key)!;
    const value = fact.label_ja ?? fact.label;
    return { key, label: displayLabel, value: value === displayLabel ? null : value };
  });
}

export function resolveActionEventHistoryTheme(args: {
  facts: ConciergeReasonFacts | null | undefined;
  actionSourceKeys: string[] | null | undefined;
}): string {
  if (!args.actionSourceKeys?.includes("ranked_history_theme")) return "";

  const primary = findPrimaryReasonFact(args.facts);
  return primary?.type === "history_theme" ? primary.label : "";
}
