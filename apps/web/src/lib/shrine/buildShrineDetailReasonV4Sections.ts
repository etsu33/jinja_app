// apps/web/src/lib/shrine/buildShrineDetailReasonV4Sections.ts
//
// Backendのrecommendation_reason_v4_detailを、Shrine Detail画面表示用の
// Fact/Interpretation/Actionセクションへ変換する低レベルAdapter。
//
// Hero Adapter(buildHeroReasonV4Sections)とFact優先順位ロジックを共有するが、
// Hero(要約向け)とDetail(詳細向け)は表示量・画面構造が異なるため、
// 画面用のAdapter自体は別ファイルとして分離する。
import { buildRecommendationReasonDisplay } from "../../../../../packages/shared/recommendationReasonDisplay";
import { isRecommendationReasonFact } from "../../../../../packages/shared/recommendationReasonAuthority";
import { pickReasonV4Fact, type ReasonV4FactSource } from "@/features/concierge/reasonV4FactPriority";

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
  // 推薦の根拠になっている事実だけ(「② 選ばれた背景」に出す)。判定は
  // packages/shared/recommendationReasonAuthority.ts の isRecommendationReasonFact:
  // 表示する項目がご利益/歴史のテーマ、かつ主な根拠(reason_facts の is_primary)が意味の一致を表す種類。
  factText: string | null;
  // 推薦の根拠になっていない神社の事実(「この神社について」に出す)。御祭神・由緒は常にこちら。
  // ご利益・歴史のテーマも、主な根拠が意味の一致でない(または分からない)ときはこちら。
  aboutShrineFactText: string | null;
  aboutShrineFactSource: ReasonV4FactSource | null;
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
 * いずれか1つ以上のセクションが表示できる場合にhasStructured=trueとする(aboutShrineFactText
 * は含めない -- buildHeroReasonV4Sections.tsと同じFallback Contract。根拠でない情報
 * だけでRecommendationが相談に意味的一致したかのように見せない)。
 *
 * reasonFacts は、同じ推薦の reason_facts(Backend wire)。無いときは根拠が分からないため、
 * 事実はすべて aboutShrineFactText へ入る。
 */
export function buildShrineDetailReasonV4Sections(
  detail: RecommendationReasonV4DetailShape | null | undefined,
  reasonFacts?: unknown,
): ShrineDetailReasonV4Sections {
  // 優先順位の実体はreasonV4FactPriority.tsに集約する(Hero/Shrine Detailで共通)。
  const pickedFact = detail ? pickReasonV4Fact(detail.fact) : null;
  const isReasonFact = pickedFact ? isRecommendationReasonFact(pickedFact.source, reasonFacts) : false;
  const factText = safeText(isReasonFact ? (pickedFact?.text ?? null) : null);
  const aboutShrineFactText = safeText(pickedFact && !isReasonFact ? pickedFact.text : null);
  const aboutShrineFactSource = aboutShrineFactText && pickedFact ? pickedFact.source : null;
  const interpretationText = safeText(detail ? clean(detail.interpretation?.text) : null);
  const actionText = safeText(detail ? clean(detail.action?.text) : null);

  const hasStructured = Boolean(factText || interpretationText || actionText);

  return { factText, aboutShrineFactText, aboutShrineFactSource, interpretationText, actionText, hasStructured };
}
