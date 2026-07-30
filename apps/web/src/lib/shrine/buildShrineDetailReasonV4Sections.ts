// apps/web/src/lib/shrine/buildShrineDetailReasonV4Sections.ts
//
// Backendのrecommendation_reason_v4_detailを、Shrine Detail画面表示用の
// Fact/Interpretation/Actionセクションへ変換する低レベルAdapter。
//
// Hero Adapter(buildHeroReasonV4Sections)とFact優先順位ロジックを共有するが、
// Hero(要約向け)とDetail(詳細向け)は表示量・画面構造が異なるため、
// 画面用のAdapter自体は別ファイルとして分離する。
import { buildRecommendationReasonDisplay } from "../../../../../packages/shared/recommendationReasonDisplay";
import { pickReasonV4FactText } from "@/features/concierge/reasonV4FactPriority";

export type RecommendationReasonV4DetailFact = {
  label?: string | null;
  name?: string | null;
  deity?: string | null;
  shrine_history?: string | null;
  place_context?: string | null;
  history_theme?: string | null;
  goriyaku?: string | null;
};

export type RecommendationReasonV4DetailShape = {
  version?: "v4";
  reason_text?: string | null;
  fact?: RecommendationReasonV4DetailFact | null;
  interpretation?: { theme?: string | null; text?: string | null } | null;
  action?: { text?: string | null; source?: string | null } | null;
};

export type ShrineDetailReasonV4Sections = {
  factText: string | null;
  interpretationText: string | null;
  actionText: string | null;
  hasStructured: boolean;
};

function clean(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const s = value.trim();
  return s.length ? s : null;
}

// 方位・断定表現の除外は既存のbuildRecommendationReasonDisplayに委譲する(新規フィルタを作らない)
function safeText(value: string | null): string | null {
  if (!value) return null;
  return buildRecommendationReasonDisplay({ matchReason: null, reason: value, directionReference: null }).reason;
}

/**
 * Backendから受け取った値をもとに、欠損・不正型に強い形へ正規化する。
 * `raw`がobjectでない場合(field欠落・旧Thread互換)はnullを返す。
 */
export function normalizeRecommendationReasonV4Detail(raw: unknown): RecommendationReasonV4DetailShape | null {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;

  const value = raw as Record<string, unknown>;
  const factRaw = value.fact && typeof value.fact === "object" ? (value.fact as Record<string, unknown>) : {};
  const interpretationRaw =
    value.interpretation && typeof value.interpretation === "object"
      ? (value.interpretation as Record<string, unknown>)
      : {};
  const actionRaw = value.action && typeof value.action === "object" ? (value.action as Record<string, unknown>) : {};

  return {
    version: "v4",
    reason_text: clean(value.reason_text),
    fact: {
      label: clean(factRaw.label),
      name: clean(factRaw.name),
      deity: clean(factRaw.deity),
      shrine_history: clean(factRaw.shrine_history),
      place_context: clean(factRaw.place_context),
      history_theme: clean(factRaw.history_theme),
      goriyaku: clean(factRaw.goriyaku),
    },
    interpretation: {
      theme: clean(interpretationRaw.theme),
      text: clean(interpretationRaw.text),
    },
    action: {
      text: clean(actionRaw.text),
      source: clean(actionRaw.source),
    },
  };
}

/**
 * Shrine Detail画面表示用のFact/Interpretation/Actionセクションを組み立てる。
 *
 * place_context(住所)とlabelはFact本文の候補にしない(優先順位の実体はreasonV4FactPriority.ts)。
 * いずれか1つ以上のセクションが表示できる場合にhasStructured=trueとする。
 */
export function buildShrineDetailReasonV4Sections(
  detail: RecommendationReasonV4DetailShape | null | undefined,
): ShrineDetailReasonV4Sections {
  const factText = safeText(detail ? pickReasonV4FactText(detail.fact) : null);
  const interpretationText = safeText(detail ? clean(detail.interpretation?.text) : null);
  const actionText = safeText(detail ? clean(detail.action?.text) : null);

  const hasStructured = Boolean(factText || interpretationText || actionText);

  return { factText, interpretationText, actionText, hasStructured };
}
