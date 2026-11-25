// apps/web/src/features/concierge/highlightPick.ts
//
// 見どころ単位の推薦 段階A（PR-3）：backend の推薦に付く `highlight_pick` を画面用に整える。
// - backend（temples/services/highlight_pick.py）が選んだものをそのまま使う。ここでは選び直さない
// - 推薦理由ではない。参拝で何を見るか（Action Layer）として出す
// - 詳細ページへのリンクは、神社の詳細リンクと同じ決まり（detailHref.ts）で作る
import { highlightHrefFromRecommendation } from "@/features/concierge/detailHref";

export type ConciergeHighlightPick = {
  highlightId: number;
  name: string;
  needTag: string;
  answerText: string;
  href: string;
};

type AnyObj = Record<string, any>;

function asText(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const s = v.trim();
  return s ? s : null;
}

function asPositiveInt(v: unknown): number | null {
  const n = typeof v === "string" && v.trim() ? Number(v) : v;
  return typeof n === "number" && Number.isInteger(n) && n > 0 ? n : null;
}

/**
 * 推薦1件から「ここで見る」見どころを取り出す。足りないものがあれば null（何も出さない）。
 * - 名前・アンサーの文・見どころの id のどれかが無い
 * - 見どころの神社と、推薦の神社が食い違う
 * - 詳細ページへのリンクを作れない（登録済みの神社でない）
 */
export function normalizeHighlightPick(
  recommendation: AnyObj,
  ctx?: { ctx?: string; tid?: string | number },
): ConciergeHighlightPick | null {
  const raw = recommendation?.highlight_pick ?? recommendation?.highlightPick ?? null;
  if (!raw || typeof raw !== "object") return null;

  const highlightId = asPositiveInt(raw.highlight_id ?? raw.highlightId);
  const name = asText(raw.name);
  const answerText = asText(raw.answer_text ?? raw.answerText);
  const needTag = asText(raw.need_tag ?? raw.needTag);
  if (!highlightId || !name || !answerText || !needTag) return null;

  const pickShrineId = asPositiveInt(raw.shrine_id ?? raw.shrineId);
  const href = highlightHrefFromRecommendation(recommendation, highlightId, {
    ...ctx,
    expectedShrineId: pickShrineId,
  });
  if (!href) return null;

  return { highlightId, name, needTag, answerText, href };
}
