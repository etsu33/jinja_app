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
import { resolveCanonicalHistoryTypeLabel } from "@/lib/shrine/shrineHistoryTypeLabels";
import { toOriginPayload, type UserOrigin } from "../../../../../packages/shared/userOrigin";
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

function nonEmpty(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

/**
 * backend の順序を保ったまま、`is_primary === true` かつ `label_ja` が空でない
 * 最初の reason_fact だけを Meaning とする。無ければ null（ブロックを出さない）。
 *
 * `type === "fallback"`（backend が一致理由を持たない候補に付ける「近い候補」）は
 * Recommendation Meaning ではないため、primary であっても採用しない。
 * legacy `reason` や別の fallback 文言で置き換えない。
 */
export function resolveCompassCandidateMeaning(rec: CompassRecommendation): CompassCandidateMeaning | null {
  const facts = Array.isArray(rec.reason_facts) ? rec.reason_facts : [];
  for (const fact of facts) {
    if (!fact || typeof fact !== "object" || fact.is_primary !== true) continue;
    if (fact.type === "fallback") continue;
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
        // Shrine Detail と同じ canonical ラベル。未知の値は内部type文字列を出さずラベルなし。
        typeLabel: resolveCanonicalHistoryTypeLabel(historyType),
        content,
      }
    : null;

  if (!deityName && !history) return null;
  return { deityName, history };
}

/**
 * Google Maps 経路URLの出発地（route origin）だけを決める。
 *
 * 送信済みの UserOrigin が `accuracy === "precise"`（現在地・駅名・住所）のときだけ
 * その座標を返す。`approximate`（都道府県の代表座標など）はユーザーの実際の出発地
 * ではないため null を返し、呼び出し側は destination のみの経路URLにする。
 * 候補選定・方向・距離（backend request の origin）には使わない。
 */
export function resolveCompassRouteOrigin(origin: UserOrigin | null | undefined): { lat: number; lng: number } | null {
  if (!origin || origin.accuracy !== "precise") return null;
  return toOriginPayload(origin) ?? null;
}
