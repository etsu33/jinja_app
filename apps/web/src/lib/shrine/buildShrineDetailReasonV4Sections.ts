// apps/web/src/lib/shrine/buildShrineDetailReasonV4Sections.ts
//
// Backendのrecommendation_reason_v4_detailを、Shrine Detail画面表示用の
// Fact/Interpretation/Actionセクションへ変換する低レベルAdapter。
//
// Hero Adapter(buildHeroReasonV4Sections)とFact優先順位ロジックを共有するが、
// Hero(要約向け)とDetail(詳細向け)は表示量・画面構造が異なるため、
// 画面用のAdapter自体は別ファイルとして分離する。
import { buildRecommendationReasonDisplay } from "../../../../../packages/shared/recommendationReasonDisplay";
import {
  collectMatchedBenefitNames,
  isCoveredByConfirmedShrineKnowledge,
  isRecommendationReasonFact,
  type ConfirmedShrineKnowledge,
} from "../../../../../packages/shared/recommendationReasonAuthority";
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
  // 「選ばれた背景」に並べる、相談と一致したご利益の名前(reason_facts の matched_benefit_names)。
  // packages/shared/recommendationReasonAuthority.ts の collectMatchedBenefitNames:
  // 主な根拠が意味の一致を表す種類のときだけ、主な根拠の項目を先に、同じ名前は1回だけ。
  // 事実を1つだけ選ぶ処理(fact.deity / fact.goriyaku など)とは切り離している。
  reasonBenefitNames: string[];
  // 推薦の根拠になっていない神社の事実(「この神社について」に出す)。
  // ご利益・歴史のテーマは、主な根拠が意味の一致でない(または分からない)ときにこちら。
  // 御祭神・由緒は、確認済みのデータがあれば前からある「神社について」に出ているため出さない
  // (重ねて出さない)。確認済みのデータが無いときだけ、古い項目から来た値をこちらに出す。
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
 * ご利益・歴史のテーマも aboutShrineFactText へ入る。
 * confirmedKnowledge は、神社の確認済みの御祭神・由緒のデータの有無。御祭神・由緒は、
 * 確認済みのデータがあれば aboutShrineFactText に入れない。
 * 事実を選ぶ順番(御祭神 > 由緒 > ご利益 > 歴史のテーマで1つ)は変えない。外したあとに
 * 次の事実へ選び直すことはしない。
 */
export function buildShrineDetailReasonV4Sections(
  detail: RecommendationReasonV4DetailShape | null | undefined,
  reasonFacts?: unknown,
  confirmedKnowledge?: ConfirmedShrineKnowledge | null,
): ShrineDetailReasonV4Sections {
  // 優先順位の実体はreasonV4FactPriority.tsに集約する(Hero/Shrine Detailで共通)。
  const pickedFact = detail ? pickReasonV4Fact(detail.fact) : null;
  // 「この神社について」の判定(#3450 の動きのまま)。根拠になるご利益・歴史のテーマは
  // 「この神社について」に出さない。「選ばれた背景」の中身は reasonBenefitNames で別に作る。
  const isReasonFact = pickedFact ? isRecommendationReasonFact(pickedFact.source, reasonFacts) : false;
  const reasonBenefitNames = detail
    ? collectMatchedBenefitNames(reasonFacts).flatMap((name) => {
        const shown = safeText(name);
        return shown ? [shown] : [];
      })
    : [];
  const isCovered = pickedFact ? isCoveredByConfirmedShrineKnowledge(pickedFact.source, confirmedKnowledge) : false;
  const aboutShrineFactText = safeText(pickedFact && !isReasonFact && !isCovered ? pickedFact.text : null);
  const aboutShrineFactSource = aboutShrineFactText && pickedFact ? pickedFact.source : null;
  const interpretationText = safeText(detail ? clean(detail.interpretation?.text) : null);
  const actionText = safeText(detail ? clean(detail.action?.text) : null);

  const hasStructured = Boolean(reasonBenefitNames.length > 0 || interpretationText || actionText);

  return {
    reasonBenefitNames,
    aboutShrineFactText,
    aboutShrineFactSource,
    interpretationText,
    actionText,
    hasStructured,
  };
}
