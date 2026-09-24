// apps/web/src/features/compass/resolveCompassCandidatePresentation.ts
//
// Compass Candidate Card v2 の表示用値を、既に公開済みの Public Contract
// （#2967）から読み出すだけの pure function 群。推論・ranking・要約・
// 補完は一切しない。
//
//   Meaning     -> reason_facts   （なぜ今回この神社が候補なのか）
//   Shrine Fact -> shrine_facts   （相談とは独立した、その神社の確認済みFact）
//
// legacy `reason` は Meaning の fallback に使わない。Shrine Fact を Meaning へ
// 昇格させない。
import type { CompassRecommendation } from "./types";

export type CompassCandidateMeaning = {
  text: string;
  // history_theme は KAMI MUSUBI 自身の解釈（Derived Meaning）であり、
  // 公式Factとして提示しない。
  isKamiMusubiInterpretation: boolean;
};

export type CompassCandidateShrineFacts = {
  deityName: string | null;
  history: { typeLabel: string | null; content: string } | null;
};

// Compass Candidate Card 専用の history_type 表示ラベル。未知の値は
// ラベルを出さない（生の type 文字列を表示しない）。
// Shrine Detail の HISTORY_TYPE_LABELS（lib/shrine/buildShrineFactSection.ts）
// とは別契約であり、Detail 側の表示は変更しない。
export const COMPASS_HISTORY_TYPE_LABELS: Readonly<Record<string, string>> = {
  official_origin: "由緒",
  founding: "由緒",
  historical_event: "歴史",
  tradition: "伝承",
  regional_context: "地域との関わり",
  editorial_summary: "概要",
};

function nonEmpty(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

/**
 * backend の順序を保ったまま、`is_primary === true` かつ `label_ja` が空でない
 * 最初の reason_fact だけを Meaning とする。無ければ null（ブロックを出さない）。
 */
export function resolveCompassCandidateMeaning(rec: CompassRecommendation): CompassCandidateMeaning | null {
  const facts = Array.isArray(rec.reason_facts) ? rec.reason_facts : [];
  for (const fact of facts) {
    if (!fact || typeof fact !== "object" || fact.is_primary !== true) continue;
    const labelJa = nonEmpty(fact.label_ja);
    if (!labelJa) continue;
    if (fact.type === "history_theme") {
      return { text: `${labelJa.trim()}という文脈`, isKamiMusubiInterpretation: true };
    }
    return { text: labelJa.trim(), isKamiMusubiInterpretation: false };
  }
  return null;
}

/**
 * shrine_facts をそのまま表示用に読み出す。deity / history は存在する側だけ返し、
 * 両方無ければ null（Fact section を出さない）。history.content は切り詰めない
 * （2行表示は CSS line-clamp の責務）。
 */
export function resolveCompassCandidateShrineFacts(rec: CompassRecommendation): CompassCandidateShrineFacts | null {
  const facts = rec.shrine_facts;
  if (!facts || typeof facts !== "object") return null;

  const deityName = nonEmpty(facts.deity?.display_name);
  const content = nonEmpty(facts.history?.content);
  const historyType = facts.history?.history_type;
  const history = content
    ? {
        typeLabel:
          typeof historyType === "string" && Object.prototype.hasOwnProperty.call(COMPASS_HISTORY_TYPE_LABELS, historyType)
            ? COMPASS_HISTORY_TYPE_LABELS[historyType]
            : null,
        content,
      }
    : null;

  if (!deityName && !history) return null;
  return { deityName, history };
}
