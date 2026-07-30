// apps/mobile/lib/recommendationReasonV4.ts
import { buildRecommendationReasonDisplay } from "../../../packages/shared/recommendationReasonDisplay";

export type RecommendationReasonV4Fact = {
  label: string;
  name: string | null;
  deity: string | null;
  shrine_history: string | null;
  place_context: string | null;
  history_theme: string | null;
  goriyaku: string | null;
  visit_style_tags: string[];
  evidence: string[];
};

export type RecommendationReasonV4Interpretation = {
  theme: string;
  text: string;
};

export type RecommendationReasonV4Action = {
  text: string;
  source: string;
};

export type RecommendationReasonV4Detail = {
  version: "v4";
  reason_text: string;
  fact: RecommendationReasonV4Fact;
  interpretation: RecommendationReasonV4Interpretation;
  action: RecommendationReasonV4Action;
};

export type ReasonV4Sections = {
  factText: string | null;
  interpretationText: string | null;
  actionText: string | null;
  hasStructured: boolean;
  fallbackText: string | null;
};

function clean(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const s = value.trim();
  return s.length ? s : null;
}

function cleanArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function pickFirst(...values: unknown[]): string | null {
  for (const v of values) {
    const s = clean(v);
    if (s) return s;
  }
  return null;
}

// 方位・断定表現の除外は既存のbuildRecommendationReasonDisplayに委譲する(Mobileで新規フィルタを作らない)
function safeText(value: string | null): string | null {
  if (!value) return null;
  return buildRecommendationReasonDisplay({ matchReason: null, reason: value, directionReference: null }).reason;
}

/**
 * Backendの`recommendation_reason_v4_detail`を欠損に強い形へ正規化する。
 * `raw`がobjectでない場合(field欠落・古いAPIレスポンス)はnullを返す。
 * object内の各fieldは欠落・空文字・不正型でもクラッシュしない。
 */
export function normalizeRecommendationReasonV4Detail(raw: unknown): RecommendationReasonV4Detail | null {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;

  const value = raw as Record<string, unknown>;
  const factRaw = (value.fact && typeof value.fact === "object" ? value.fact : {}) as Record<string, unknown>;
  const interpretationRaw = (value.interpretation && typeof value.interpretation === "object" ? value.interpretation : {}) as Record<string, unknown>;
  const actionRaw = (value.action && typeof value.action === "object" ? value.action : {}) as Record<string, unknown>;

  return {
    version: "v4",
    reason_text: clean(value.reason_text) ?? "",
    fact: {
      label: clean(factRaw.label) ?? "",
      name: clean(factRaw.name),
      deity: clean(factRaw.deity),
      shrine_history: clean(factRaw.shrine_history),
      place_context: clean(factRaw.place_context),
      history_theme: clean(factRaw.history_theme),
      goriyaku: clean(factRaw.goriyaku),
      visit_style_tags: cleanArray(factRaw.visit_style_tags),
      evidence: cleanArray(factRaw.evidence),
    },
    interpretation: {
      theme: clean(interpretationRaw.theme) ?? "",
      text: clean(interpretationRaw.text) ?? "",
    },
    action: {
      text: clean(actionRaw.text) ?? "",
      source: clean(actionRaw.source) ?? "",
    },
  };
}

/**
 * Hero/その他候補を問わず、推薦カード表示用のReason V4セクションを組み立てる。
 *
 * 優先順位:
 * 1. 構造化fact / interpretation / action
 * 2. recommendation_reason_v4_detail.reason_text
 * 3. recommendation_reason_v4(文字列) ※ fallbackReasonに事前解決済みとして渡す
 * 4. reasonFacts由来の既存理由 ※ fallbackReasonに事前解決済みとして渡す
 * 5. reason(旧文字列) ※ fallbackReasonに事前解決済みとして渡す
 * 6. 既存固定fallback ※ fallbackReasonに事前解決済みとして渡す
 *
 * fallbackReasonには、呼び出し側で既に解決済みの理由文字列(3〜6段階を内包する値)を渡す。
 * 構造化セクションが1つ以上表示できる場合はfallbackTextを返さない(重複表示防止)。
 */
export function buildReasonV4Sections(params: {
  detail?: RecommendationReasonV4Detail | null;
  fallbackReason?: string | null;
}): ReasonV4Sections {
  const detail = params.detail ?? null;

  const factText = safeText(
    detail
      ? pickFirst(
          detail.fact.shrine_history,
          detail.fact.place_context,
          detail.fact.goriyaku,
          detail.fact.history_theme,
          detail.fact.label,
        )
      : null,
  );
  const interpretationText = safeText(detail ? clean(detail.interpretation.text) : null);
  const actionText = safeText(detail ? clean(detail.action.text) : null);

  const hasStructured = Boolean(factText || interpretationText || actionText);

  const fallbackText = hasStructured
    ? null
    : safeText(pickFirst(detail?.reason_text, params.fallbackReason));

  return { factText, interpretationText, actionText, hasStructured, fallbackText };
}

/**
 * Concierge→Shrine Detailのroute paramsへ渡すJSON文字列を組み立てる。
 * 既存のreasonFacts/recommendationReasonDetail等と同じ「値が無ければ空文字」規約に合わせる。
 */
export function serializeReasonV4Detail(detail: RecommendationReasonV4Detail | null | undefined): string {
  return detail ? JSON.stringify(detail) : "";
}
