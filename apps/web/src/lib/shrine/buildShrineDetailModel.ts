// apps/web/src/lib/shrine/buildShrineDetailModel.ts
import type { Shrine } from "@/lib/api/shrines";
import type { ShrineMeaningPayloadV2 } from "@/lib/shrineMeaning/payloadV2";
import type { ShrineTag } from "@/lib/shrine/tags/types";
import type { PublicGoshuinItem } from "@/components/shrine/detail/PublicGoshuinSection";
import type {
  DetailMeaningItem,
  DetailMeaningSection,
  DetailProposalSection,
  DetailReasonGroup,
  DetailReasonSection,
  DetailSupplementGroup,
  DetailSupplementSection,
  ShrineDetailSectionModel,
} from "@/components/shrine/detail/types";
import type { ConciergeBreakdown } from "@/lib/api/concierge";
import { buildShrineCardProps } from "@/components/shrine/buildShrineCardProps";
import { getBenefitLabels } from "@/lib/shrine/getBenefitLabels";
import { buildShrineExplanation } from "@/lib/shrine/buildShrineExplanation";
import { buildShrineJudge } from "@/lib/shrine/buildShrineJudge";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import {
  type ConciergeMode,
  type NeedTag,
  type ShrineTone,
  type ExplanationPayload,
  type NarrativeFallback,
} from "@/lib/concierge/narrative/types";
import { buildRankReason } from "@/lib/concierge/narrative/buildRankReason";
import { buildComparisonText } from "@/lib/concierge/narrative/buildComparisonText";
import { buildPsychologicalTags } from "@/lib/concierge/narrative/buildPsychologicalTags";
import { buildSymbolTags } from "@/lib/concierge/narrative/buildSymbolTags";
import { resolveNeedCombinationNarrative } from "@/lib/concierge/narrative/needCombinationMap";

type Args = {
  shrine: Shrine;
  shrineMeaningPayloadV2?: ShrineMeaningPayloadV2 | null;
  publicGoshuins: PublicGoshuinItem[];
  conciergeBreakdown?: ConciergeBreakdown | null;
  conciergeReason?: string | null;
  conciergeDeepReason?: NarrativeFallback | null;
  conciergeExplanationPayload?: ExplanationPayload | null;
  conciergeMode?: ConciergeMode | null;
  recommendationRankExplanation?: RankExplanation | null;
  recommendationRankComparison?: RankComparison | null;
  ctx?: "map" | "concierge" | null;
  tid?: string | null;
  recommendationReasonDetail?: {
    heroMeaningCopy?: string | null;
    consultationSummary?: string | null;
    shrineMeaning?: string | null;
    actionMeaning?: string | null;
  } | null;
  signals?: {
    publicGoshuinsCount?: number;
    views30d?: number;
    fav30d?: number;
  };
};

type ShrineDetailDisplayTier = "free" | "premium";

type ShrineDetailLayer = "public" | "context" | "personal";

type ShrineDetailDisplaySection = {
  tier: ShrineDetailDisplayTier;
  layer: ShrineDetailLayer;
  section: ShrineDetailSectionModel;
};

function buildMeaningSectionsFromPayloadV2(payload?: ShrineMeaningPayloadV2 | null): {
  freeDisplaySections: ShrineDetailDisplaySection[];
  premiumDisplaySections: ShrineDetailDisplaySection[];
} | null {
  const blocks = payload?.display?.blocks ?? [];
  if (!blocks.length) return null;

  const freeItems: DetailMeaningItem[] = [];
  const premiumPrimaryItems: DetailMeaningItem[] = [];
  const premiumSupplementItems: DetailMeaningItem[] = [];

  const premiumPrimaryBlockIds = new Set(["today_flow", "action_meaning", "after_visit_reflection"]);
  const premiumSupplementBlockIds = new Set(["history_context", "deity_symbol", "benefit_action"]);

  blocks.forEach((block) => {
    const body = block.body?.trim();
    if (!body) return;

    const item: DetailMeaningItem = {
      key: block.id,
      title: block.title,
      body,
    };

    if (block.access === "premium") {
      if (premiumPrimaryBlockIds.has(block.id)) {
        premiumPrimaryItems.push(item);
        return;
      }
      if (premiumSupplementBlockIds.has(block.id)) {
        premiumSupplementItems.push(item);
        return;
      }
      premiumPrimaryItems.push(item);
      return;
    }

    freeItems.push(item);
  });

  const freeDisplaySections: ShrineDetailDisplaySection[] = freeItems.length
    ? [
        {
          tier: "free",
          layer: "context",
          section: {
            kind: "meaning",
            heading: "神社との意味の接続",
            items: freeItems,
          },
        },
      ]
    : [];

  const premiumDisplaySections: ShrineDetailDisplaySection[] = [
    ...(premiumPrimaryItems.length
      ? [
          {
            tier: "premium" as const,
            layer: "personal" as const,
            section: {
              kind: "meaning" as const,
              heading: "で見ること",
              items: premiumPrimaryItems,
            },
          },
        ]
      : []),
    ...(premiumSupplementItems.length
      ? [
          {
            tier: "premium" as const,
            layer: "context" as const,
            section: {
              kind: "meaning" as const,
              heading: "補足：神社の背景とご利益",
              items: premiumSupplementItems,
            },
          },
        ]
      : []),
  ];

  if (!freeDisplaySections.length && !premiumDisplaySections.length) return null;

  return {
    freeDisplaySections,
    premiumDisplaySections,
  };
}

type RecommendationWhySection = {
  label:
    | "相談との一致"
    | "相性との重なり"
    | "神社のご利益"
    | "補助的な一致"
    | "補助的な観点"
    | "上位になった理由"
    | "他候補との差";
  text: string;
};

type RecommendationJudgeSection = {
  disclosureTitle: string;
  title: string;
  lead: string;
  items: JudgeSectionItem[];
};

type ShrineRecommendationExplanation = {
  proposal: string;
  proposalLead: string;
  proposalWhy: RecommendationWhySection[];
  judgeSection: RecommendationJudgeSection;
  rankReason: string | null;
};

type JudgeSectionItem = {
  key: string;
  title: string;
  body: string;
};

type RankExplanation = {
  version: number;
  summary?: string;
  primary_axis?: string;
  primary_axis_ja?: string;
  primary_label?: string | null;
  primary_label_ja?: string | null;
};

type RankComparison = {
  version: number;
  rank?: number;
  is_top?: boolean;
  top_name?: string | null;
  gap_from_top?: number;
  comparison_summary?: string | null;
};

type RecommendationMeta = {
  rankExplanation?: RankExplanation | null;
  rankComparison?: RankComparison | null;
  rankTitle?: string | null;
  rankBody?: string | null;
};

function buildRecommendationMeta(args: {
  rankExplanation?: RankExplanation | null;
  rankComparison?: RankComparison | null;
}): RecommendationMeta | null {
  const rankExplanation = args.rankExplanation ?? null;
  const rankComparison = args.rankComparison ?? null;

  const isTop = Boolean(rankComparison?.is_top);
  const rankTitle = isTop ? "この神社が1位の理由" : "1位との違い";

  const rankBody = isTop ? (rankExplanation?.summary ?? null) : (rankComparison?.comparison_summary ?? null);

  if (!rankTitle || !rankBody) return null;

  return {
    rankExplanation,
    rankComparison,
    rankTitle,
    rankBody,
  };
}

function resolveConciergeMode(value: unknown): ConciergeMode {
  return value === "compat" ? "compat" : "need";
}

function normalizeShrineName(name?: string | null): string {
  return (name ?? "").replace(/\s+/g, "").trim();
}

function getShrineTone(shrineName?: string | null): ShrineTone {
  const name = normalizeShrineName(shrineName);

  if (name.includes("三峯")) return "strong";
  if (name.includes("伊勢神宮") || name.includes("内宮")) return "quiet";
  if (name.includes("乃木")) return "tight";

  return "neutral";
}

function needLabelJa(tag: NeedTag): string {
  if (tag === "money") return "金運";
  if (tag === "courage") return "前に進むきっかけ";
  if (tag === "career") return "仕事や転機";
  if (tag === "mental") return "不安や気持ちの揺れ";
  if (tag === "rest") return "休息";
  if (tag === "love") return "良縁や恋愛";
  return "学業や合格";
}

function buildNeedThemeLabel(tag: NeedTag | null): string | null {
  if (!tag) return null;
  if (tag === "money") return "流れの立て直し";
  if (tag === "courage") return "前進のきっかけ";
  if (tag === "career") return "仕事や転機";
  if (tag === "mental") return "気持ちの立て直し";
  if (tag === "rest") return "休息";
  if (tag === "love") return "関係性";
  if (tag === "study") return "学業";
  return needLabelJa(tag);
}

function buildPrimaryBenefitLabel(benefitLabels: string[]): string | null {
  const first = benefitLabels.find((label) => typeof label === "string" && label.trim().length > 0);
  return first ? first.trim() : null;
}

function buildReasonIntersectionText(args: { primary: NeedTag | null; benefitLabels: string[] }): string {
  const themeLabel = buildNeedThemeLabel(args.primary);
  const benefitLabel = buildPrimaryBenefitLabel(args.benefitLabels);

  if (themeLabel && benefitLabel) {
    return `今回の相談の中心にある「${themeLabel}」のテーマと、この神社の「${benefitLabel}」の性質が重なるため、この神社が候補に入っています。`;
  }

  if (themeLabel) {
    return `今回の相談の中心にある「${themeLabel}」のテーマと重なるため、この神社が候補に入っています。`;
  }

  if (benefitLabel) {
    return `この神社の「${benefitLabel}」の性質が、今回の相談と重なるため、この神社が候補に入っています。`;
  }

  return "今回の相談内容との重なりから、この神社が候補に入っています。";
}

function isNeedTag(tag: string): tag is NeedTag {
  return ["money", "courage", "career", "mental", "rest", "love", "study"].includes(tag);
}

function getMatchedNeedTags(breakdown?: ConciergeBreakdown | null): NeedTag[] {
  return (breakdown?.matched_need_tags ?? [])
    .filter((v): v is string => typeof v === "string" && v.trim().length > 0)
    .filter(isNeedTag);
}

function getPrimaryNeedTag(breakdown?: ConciergeBreakdown | null): NeedTag | null {
  const tags = getMatchedNeedTags(breakdown);

  if (tags.includes("courage")) return "courage";
  if (tags.includes("money")) return "money";
  if (tags.includes("career")) return "career";
  if (tags.includes("mental")) return "mental";
  if (tags.includes("rest")) return "rest";
  if (tags.includes("love")) return "love";
  if (tags.includes("study")) return "study";

  return tags[0] ?? null;
}

function getSecondaryNeedTags(breakdown?: ConciergeBreakdown | null): NeedTag[] {
  const primary = getPrimaryNeedTag(breakdown);
  return getMatchedNeedTags(breakdown).filter((tag) => tag !== primary);
}

function buildNeedMatchText(
  argsOrPrimary: { primary?: NeedTag | null; benefitLabels?: string[] | null } | NeedTag | null,
  _legacySecondary?: NeedTag[],
): string {
  if (!argsOrPrimary || typeof argsOrPrimary !== "object") {
    return buildReasonIntersectionText({
      primary: argsOrPrimary ?? null,
      benefitLabels: [],
    });
  }

  const safePrimary: NeedTag | null = "primary" in argsOrPrimary ? (argsOrPrimary.primary ?? null) : null;

  const safeBenefitLabels: string[] =
    "benefitLabels" in argsOrPrimary && Array.isArray(argsOrPrimary.benefitLabels)
      ? argsOrPrimary.benefitLabels.filter(
          (label): label is string => typeof label === "string" && label.trim().length > 0,
        )
      : [];

  return buildReasonIntersectionText({
    primary: safePrimary,
    benefitLabels: safeBenefitLabels,
  });
}

function buildCompatMatchText(args: {
  userElementLabel?: string | null;
  shrineElementLabels?: string[] | null;
  primaryReasonLabel?: string | null;
}): string {
  const user = args.userElementLabel ?? "今回の生年月日傾向";
  const shrine = (args.shrineElementLabels ?? []).filter(Boolean).slice(0, 2).join("・");

  if (shrine) {
    return `${user}と、${shrine}の要素を持つこの神社の噛み合いを主軸に見ています。`;
  }

  if (args.primaryReasonLabel) {
    return `${user}を主軸に見つつ、${args.primaryReasonLabel}の観点も補助要素として見ています。`;
  }

  return `${user}と、この神社が持つ要素の噛み合いを主軸に見ています。`;
}

function toBenefitTag(label: string): ShrineTag {
  const v = label.trim();
  return {
    id: `benefit:${encodeURIComponent(v)}`,
    label: v,
    type: "benefit",
    source: "official",
    confidence: "high",
  };
}

function uniqueNonEmpty(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.map((v) => (typeof v === "string" ? v.trim() : "")).filter(Boolean))];
}

function uniqueReasonItems(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const out: string[] = [];

  values.forEach((value) => {
    const normalized = typeof value === "string" ? value.trim() : "";
    if (!normalized) return;
    if (seen.has(normalized)) return;
    seen.add(normalized);
    out.push(normalized);
  });

  return out;
}

function buildReasonSection(args: {
  mode: ConciergeMode;
  breakdown?: ConciergeBreakdown | null;
  explanationPayload?: ExplanationPayload | null;
  benefitLabels: string[];
  shrineName?: string | null;
  rankReason?: string | null;
  comparisonText?: string | null;
  isTop?: boolean | null;
}): DetailReasonSection | null {
  const primary = getPrimaryNeedTag(args.breakdown);
  const secondary = getSecondaryNeedTags(args.breakdown);
  const payload = args.explanationPayload ?? null;
  const shrineText = args.shrineName?.trim() || "この神社";
  const shrineTone = getShrineTone(shrineText);
  const benefitText = buildBenefitText(shrineText, args.benefitLabels, primary, shrineTone);
  const secondaryText = buildSecondaryText(primary, secondary, shrineText);
  const topReasonText =
    args.rankReason?.trim() ||
    buildRankReasonText({
      mode: args.mode,
      breakdown: args.breakdown,
      primaryNeed: primary,
      secondaryNeedTags: secondary,
    });
  const comparisonReasonText =
    args.comparisonText?.trim() ||
    buildComparisonText({
      mode: args.mode,
      primaryNeed: primary,
      shrineName: shrineText,
      shrineTone,
    });
  const rankGroupTitle = args.isTop ? "1位理由" : "上位理由";

  if (args.mode === "compat") {
    const compatMatchText = buildCompatMatchText({
      userElementLabel: payload?.primary_need_label_ja ?? null,
      shrineElementLabels: args.benefitLabels,
      primaryReasonLabel: payload?.primary_reason?.label_ja ?? null,
    });

    const groups: DetailReasonGroup[] = [
      {
        title: "主理由",
        items: uniqueReasonItems([compatMatchText]),
      },
      {
        title: "補助理由",
        items: uniqueReasonItems([
          benefitText,
          payload?.primary_reason?.label_ja
            ? `${payload.primary_reason.label_ja}の観点も、相性軸を補う要素として見ています。`
            : "生年月日との相性を補う要素も見ています。",
        ]),
      },
      {
        title: rankGroupTitle,
        items: uniqueReasonItems([topReasonText, comparisonReasonText]),
      },
    ].filter((group) => group.items.length > 0);

    return groups.length > 0
      ? {
          kind: "reason",
          heading: "① この神社が出てきた理由",
          groups,
        }
      : null;
  }

  const needMatchText = buildNeedMatchText({ primary, benefitLabels: args.benefitLabels });

  const groups: DetailReasonGroup[] = [
    {
      title: "主理由",
      items: uniqueReasonItems([needMatchText]),
    },
    {
      title: "補助理由",
      items: uniqueReasonItems([benefitText, secondaryText]),
    },
    {
      title: rankGroupTitle,
      items: uniqueReasonItems([topReasonText, comparisonReasonText]),
    },
  ].filter((group) => group.items.length > 0);

  return groups.length > 0
    ? {
        kind: "reason",
        heading: "① この神社が出てきた理由",
        groups,
      }
    : null;
}

function buildProposalSection(args: {
  lead?: string | null;
  consultationSummary?: string | null;
  proposal?: string | null;
  combination?: {
    title: string;
    summary: string;
    priorityHint: string;
  } | null;
  ctx?: "map" | "concierge" | null;
}): DetailProposalSection | null {
  if (args.ctx !== "concierge") return null;

  const combinationBody = args.combination
    ? `${args.combination.title}。${args.combination.summary} 優先したいことは「${args.combination.priorityHint}」です。`
    : null;
  const body = [combinationBody, args.proposal].filter(Boolean).join("\n\n") || null;

  return {
    kind: "proposal",
    heading: "② 今回の相談の整理",
    lead: args.consultationSummary ?? args.lead ?? "",
    body,
  };
}

function buildProposalFromBreakdown(breakdown?: ConciergeBreakdown | null): string {
  const set = new Set(getMatchedNeedTags(breakdown));

  if (set.has("money") && set.has("courage")) {
    return "流れを立て直し、次の一歩を決めたい時の参拝先";
  }

  if (set.has("career") && set.has("courage")) {
    return "仕事や転機に向き合う参拝先";
  }

  if (set.has("mental") && set.has("rest")) {
    return "気持ちを整えて休息したい時の参拝先";
  }

  if (set.has("love")) {
    return "良縁を願う参拝先";
  }

  if (set.has("study")) {
    return "学業や合格に集中したい時の参拝先";
  }

  if (set.has("mental")) {
    return "不安や気持ちの揺れを整えたい時の参拝先";
  }

  if (set.has("rest")) {
    return "落ち着いて休みたい時の参拝先";
  }

  return "今回の相談に応じた参拝先";
}

function buildProposalLead(args: { mode: ConciergeMode; explanationPayload?: ExplanationPayload | null }): string {
  const payload = args.explanationPayload ?? null;

  if (args.mode === "compat") {
    return "今回の提案では、生年月日との相性を主軸に見ています。";
  }

  return payload?.primary_need_label_ja
    ? `今回の相談では、${payload.primary_need_label_ja}が中心テーマです。`
    : "今の状態を整理すると、まず向き合うべきテーマがあります。";
}

function resolveDetailLead(args: {
  ctx?: "map" | "concierge" | null;
  recommendationReasonDetail?: {
    consultationSummary?: string | null;
  } | null;
  conciergeDeepReason?: NarrativeFallback | null;
  conciergeReason?: string | null;
  generatedLead?: string | null;
}): string {
  if (args.ctx === "concierge") {
    const detailLead = args.recommendationReasonDetail?.consultationSummary?.trim();
    if (detailLead) return detailLead;

    const deepReasonLead = args.conciergeDeepReason?.interpretation?.trim();
    if (deepReasonLead) return deepReasonLead;

    const conciergeReason = args.conciergeReason?.trim();
    if (conciergeReason) return conciergeReason;
  }

  return args.generatedLead?.trim() || "";
}

function buildBenefitText(
  shrineText: string,
  benefitLabels: string[],
  primary: NeedTag | null,
  shrineTone: ShrineTone,
): string {
  const labels = benefitLabels.filter(Boolean).slice(0, 3);
  const joined =
    labels.length >= 3
      ? `${labels[0]}・${labels[1]}・${labels[2]}`
      : labels.length === 2
        ? `${labels[0]}と${labels[1]}`
        : labels.length === 1
          ? labels[0]
          : null;

  if (!joined) {
    return `${shrineText}は、今回の相談内容に照らして、気持ちや優先順位を整え直す節目として置きやすい神社です。`;
  }

  if (primary === "courage") {
    if (shrineTone === "strong") {
      return `${shrineText}は${joined}に関わるご利益で知られ、止まっている流れを動かし始める節目や、背中を押す場として据えやすい神社です。`;
    }
    if (shrineTone === "tight") {
      return `${shrineText}は${joined}に関わるご利益で知られ、迷いを断ち切って一歩を決めたい段階で判断材料にしやすい神社です。`;
    }
    if (shrineTone === "quiet") {
      return `${shrineText}は${joined}に関わるご利益で知られ、勢いで進むより気持ちを整えてから一歩を決めたい段階で節目として置きやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、次の一歩を踏み出すきっかけを持ちたい段階で参拝先として据えやすい神社です。`;
  }

  if (primary === "money") {
    if (shrineTone === "strong") {
      return `${shrineText}は${joined}に関わるご利益で知られ、停滞した巡りを切り替えて流れを再開したい段階で節目として置きやすい神社です。`;
    }
    if (shrineTone === "quiet") {
      return `${shrineText}は${joined}に関わるご利益で知られ、金運や巡りを焦らず整え直したい段階で判断材料にしやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、金運や巡りの停滞を立て直したい段階で意識を向けやすい神社です。`;
  }

  if (primary === "mental") {
    if (shrineTone === "quiet") {
      return `${shrineText}は${joined}に関わるご利益で知られ、揺れた気持ちを静かに整え直し、落ち着きを取り戻したい段階で一度立ち止まる場として使いやすい神社です。`;
    }
    if (shrineTone === "strong") {
      return `${shrineText}は${joined}に関わるご利益で知られ、沈んだ流れを切り替えつつ気持ちを立て直したい段階で節目として置きやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、気持ちを整えながら無理のない形で立て直したい段階で気持ちを向けやすい神社です。`;
  }

  if (primary === "career") {
    if (shrineTone === "tight") {
      return `${shrineText}は${joined}に関わるご利益で知られ、仕事や転機への姿勢を引き締め、判断をぶらさず整理したい段階で判断材料にしやすい神社です。`;
    }
    if (shrineTone === "quiet") {
      return `${shrineText}は${joined}に関わるご利益で知られ、仕事や転機への向き合い方を急がず見直したい段階で一度立ち止まる場として使いやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、仕事や転機への向き合い方を整理し、次の判断を落ち着いて考えたい段階で節目として置きやすい神社です。`;
  }

  if (primary === "rest") {
    if (shrineTone === "quiet") {
      return `${shrineText}は${joined}に関わるご利益で知られ、消耗した状態を静かに整え直したい段階で一度立ち止まる場として使いやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、無理に進まず消耗を立て直したい段階で参拝先として置きやすい神社です。`;
  }

  if (primary === "love") {
    if (shrineTone === "quiet") {
      return `${shrineText}は${joined}に関わるご利益で知られ、良縁や恋愛に対して気持ちを静かに整えたい段階で気持ちを向けやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、良縁や恋愛を丁寧に見直しながら前へ進めたい段階で参拝先として据えやすい神社です。`;
  }

  if (primary === "study") {
    if (shrineTone === "tight") {
      return `${shrineText}は${joined}に関わるご利益で知られ、学業や合格に向けて気持ちを引き締め直したい段階で判断材料にしやすい神社です。`;
    }
    return `${shrineText}は${joined}に関わるご利益で知られ、学業や合格に向けて乱れた集中やペースを立て直したい段階で参拝先として置きやすい神社です。`;
  }

  return `${shrineText}は${joined}に関わるご利益で知られ、今回の相談内容に照らして参拝先として検討しやすい神社です。`;
}

function buildSecondaryText(primary: NeedTag | null, secondary: NeedTag[], shrineName?: string): string {
  const shrineText = shrineName?.trim() || "この神社";
  const secondaryLabel = secondary[0] ? needLabelJa(secondary[0]) : null;

  if (secondaryLabel) {
    return `${shrineText}のご利益や性質も、「${secondaryLabel}」の観点で補助的に重なっています。`;
  }
  // (fallback to original logic if no secondary tag, or just return empty string or generic)
  return "";
}

function buildRankReasonText(args: {
  mode: ConciergeMode;
  breakdown?: ConciergeBreakdown | null;
  primaryNeed?: NeedTag | null;
  secondaryNeedTags?: NeedTag[];
}): string {
  if (args.mode === "compat") {
    return "今回の候補の中でも、生年月日との相性の重なりが最も強い候補です。";
  }

  const label = args.primaryNeed ? needLabelJa(args.primaryNeed) : null;

  if (label) {
    return `今回の候補の中でも、「${label}」のテーマとの一致が最も強い候補です。`;
  }

  return "今回の候補の中でも、相談内容との重なりが最も強い候補です。";
}

function buildProposalWhyFromBreakdown(args: {
  mode: ConciergeMode;
  breakdown?: ConciergeBreakdown | null;
  benefitLabels?: string[];
  shrineName?: string | null;
  explanationPayload?: ExplanationPayload | null;
}): RecommendationWhySection[] {
  const primary = getPrimaryNeedTag(args.breakdown);
  const secondary = getSecondaryNeedTags(args.breakdown);
  const shrineText = args.shrineName?.trim() || "この神社";
  const shrineTone = getShrineTone(shrineText);
  const benefitLabels = args.benefitLabels ?? [];
  const payload = args.explanationPayload ?? null;
  const userElementLabel = payload?.primary_need_label_ja ?? null;
  const primaryReasonLabel = payload?.primary_reason?.label_ja ?? null;

  if (args.mode === "compat") {
    return [
      {
        label: "相性との重なり",
        text: buildCompatMatchText({
          userElementLabel,
          shrineElementLabels: benefitLabels,
          primaryReasonLabel,
        }),
      },
      {
        label: "神社のご利益",
        text: buildBenefitText(shrineText, benefitLabels, primary, shrineTone),
      },
      {
        label: "補助的な観点",
        text: primaryReasonLabel
          ? `${primaryReasonLabel}の観点も、相性軸を補う要素として見ています。`
          : "生年月日との相性を補う要素も見ています。",
      },
      {
        label: "上位になった理由",
        text: buildRankReasonText({
          mode: args.mode,
          breakdown: args.breakdown,
          primaryNeed: primary,
          secondaryNeedTags: secondary,
        }),
      },
      {
        label: "他候補との差",
        text: buildComparisonText({
          mode: args.mode,
          primaryNeed: primary,
          shrineName: shrineText,
          shrineTone,
        }),
      },
    ];
  }

  return [
    {
      label: "相談との一致",
      text: buildNeedMatchText({ primary, benefitLabels }),
    },
    {
      label: "神社のご利益",
      text: buildBenefitText(shrineText, benefitLabels, primary, shrineTone),
    },
    {
      label: "補助的な一致",
      text: buildSecondaryText(primary, secondary, shrineText),
    },
    {
      label: "上位になった理由",
      text: buildRankReasonText({
        mode: args.mode,
        breakdown: args.breakdown,
        primaryNeed: primary,
        secondaryNeedTags: secondary,
      }),
    },
    {
      label: "他候補との差",
      text: buildComparisonText({
        mode: args.mode,
        primaryNeed: primary,
        shrineName: shrineText,
        shrineTone,
      }),
    },
  ];
}

function buildProposalWhyFromNarrativeSources(args: {
  recommendationReasonDetail?: {
    consultationSummary?: string | null;
  } | null;
  deepReason?: NarrativeFallback | null;
  rankReason?: string | null;
  comparisonText?: string | null;
}): RecommendationWhySection[] | null {
  const items: RecommendationWhySection[] = [];

  // fallback order:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. no value here; caller must fall back to generated proposalWhy
  const consultationText =
    args.recommendationReasonDetail?.consultationSummary?.trim() || args.deepReason?.interpretation?.trim() || "";

  const hasNarrativeSource = Boolean(consultationText || args.rankReason || args.comparisonText);
  if (!hasNarrativeSource) {
    return null;
  }

  if (consultationText) {
    items.push({
      label: "相談との一致",
      text: consultationText,
    });
  }

  if (args.rankReason) {
    items.push({
      label: "上位になった理由",
      text: args.rankReason,
    });
  }

  if (args.comparisonText) {
    items.push({
      label: "他候補との差",
      text: args.comparisonText,
    });
  }

  return items.length > 0 ? items : null;
}

function buildJudgeSectionOrder(args: {
  mode: ConciergeMode;
  explanationPayload?: ExplanationPayload | null;
  breakdown?: ConciergeBreakdown | null;
  goriyakuText?: string | null;
}): JudgeSectionItem[] {
  const mode = args.mode;
  const payload = args.explanationPayload ?? null;
  const primaryNeedLabel = payload?.primary_need_label_ja ?? null;
  const primaryReasonLabel = payload?.primary_reason?.label_ja ?? null;
  const secondaryReasons = Array.isArray(payload?.secondary_reasons) ? payload.secondary_reasons : [];
  const secondaryReasonText =
    secondaryReasons.length > 0
      ? secondaryReasons
          .map((r) => r.label_ja)
          .filter((v): v is string => Boolean(v))
          .slice(0, 2)
          .join("・")
      : null;

  const sectionsForNeed: JudgeSectionItem[] = [
    {
      key: "lead",
      title: "主軸",
      body: primaryNeedLabel
        ? `今回の相談では、${primaryNeedLabel}に関わる悩みが主軸にあります。`
        : "今回の相談では、今の状態を整えたい意図が主軸にあります。",
    },
    {
      key: "reason",
      title: "相談との一致",
      body: primaryReasonLabel
        ? `${primaryReasonLabel}に関わる相談内容との重なりが見られます。`
        : "相談内容に近い要素が見られます。",
    },
    {
      key: "goriyaku",
      title: "この神社のご利益",
      body: args.goriyakuText ?? "この神社のご利益が、今回の相談内容に近い方向です。",
    },
    {
      key: "secondary",
      title: "補助的な方向性",
      body: secondaryReasonText ?? "主軸を補う方向性があります。",
    },
    {
      key: "rank",
      title: "上位になった理由",
      body: buildRankReasonText({
        mode,
        breakdown: args.breakdown,
        primaryNeed: getPrimaryNeedTag(args.breakdown),
        secondaryNeedTags: getSecondaryNeedTags(args.breakdown),
      }),
    },
  ];

  const sectionsForCompat: JudgeSectionItem[] = [
    {
      key: "compat",
      title: "生年月日との相性",
      body: primaryNeedLabel
        ? `${primaryNeedLabel}を主軸に、生年月日との相性から候補を整理しています。`
        : "今回の提案では、生年月日との相性を主軸に候補を整理しています。",
    },
    {
      key: "element",
      title: "神社の要素",
      body: args.goriyakuText ?? "この神社が持つ要素と、ご利益面の噛み合いを見ています。",
    },
    {
      key: "reason",
      title: "補助的な観点",
      body: primaryReasonLabel
        ? `${primaryReasonLabel}の観点も、相性軸を補う要素として見ています。`
        : "生年月日との相性を補う要素も見ています。",
    },
    {
      key: "secondary",
      title: "補助的な方向性",
      body: secondaryReasonText ?? "相性軸を補う方向性があります。",
    },
    {
      key: "rank",
      title: "上位になった理由",
      body: buildRankReasonText({
        mode,
        breakdown: args.breakdown,
        primaryNeed: getPrimaryNeedTag(args.breakdown),
        secondaryNeedTags: getSecondaryNeedTags(args.breakdown),
      }),
    },
  ];

  return mode === "compat" ? sectionsForCompat : sectionsForNeed;
}

function buildJudgeItemsFromNarrativeSources(args: {
  recommendationReasonDetail?: null;
  deepReason?: NarrativeFallback | null;
}): JudgeSectionItem[] | null {
  const items: JudgeSectionItem[] = [];

  // fallback order:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. no value here; caller must fall back to generated judge items
  const shrineMeaningText = args.deepReason?.shrineMeaning?.trim() || "";
  const actionText = args.deepReason?.action?.trim() || "";

  if (shrineMeaningText) {
    items.push({
      key: "meaning",
      title: "この神社をすすめる理由",
      body: shrineMeaningText,
    });
  }

  if (actionText) {
    items.push({
      key: "action",
      title: "参拝を置く意味",
      body: actionText,
    });
  }

  return items.length > 0 ? items : null;
}

function buildMeaningSection(args: {
  lead?: string | null;
  deepReason?: NarrativeFallback | null;
  recommendationReasonDetail?: {
    shrineMeaning?: string | null;
    actionMeaning?: string | null;
  } | null;
  shrineName?: string | null;
  benefitLabels: string[];
  mode: ConciergeMode;
  breakdown?: ConciergeBreakdown | null;
}): DetailMeaningSection {
  // ③ の表示優先順位:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. buildMeaningSection 内 fallback
  const detailItems: DetailMeaningItem[] = [
    args.recommendationReasonDetail?.shrineMeaning
      ? {
          key: "meaning",
          title: "この神社をすすめる理由",
          body: args.recommendationReasonDetail.shrineMeaning,
        }
      : null,
    args.recommendationReasonDetail?.actionMeaning
      ? {
          key: "action",
          title: "参拝を置く意味",
          body: args.recommendationReasonDetail.actionMeaning,
        }
      : null,
  ].filter((item): item is DetailMeaningItem => Boolean(item));

  const deepReasonItems = buildJudgeItemsFromNarrativeSources({
    recommendationReasonDetail: null,
    deepReason: args.deepReason,
  });

  const fallbackItems: DetailMeaningItem[] =
    detailItems.length > 0
      ? detailItems
      : (deepReasonItems ?? [
          {
            key: "meaning",
            title: "この神社をすすめる理由",
            body: buildBenefitText(
              args.shrineName?.trim() || "この神社",
              args.benefitLabels,
              getPrimaryNeedTag(args.breakdown),
              getShrineTone(args.shrineName ?? null),
            ),
          },
          {
            key: "action",
            title: "参拝を置く意味",
            body: buildSecondaryText(
              getPrimaryNeedTag(args.breakdown),
              getSecondaryNeedTags(args.breakdown),
              args.shrineName ?? undefined,
            ),
          },
        ]);

  return {
    kind: "meaning",
    heading: "③ 神社との意味の接続",
    lead: args.lead?.trim() || undefined,
    items: fallbackItems,
  };
}

function buildSupplementSection(args: {
  benefitLabels: string[];
  psychologicalTags?: string[] | null;
  symbolTags?: string[] | null;
  mode: ConciergeMode;
  explanationPayload?: ExplanationPayload | null;
}): DetailSupplementSection | null {
  const groups: DetailSupplementGroup[] = [
    {
      title: "ご利益",
      items: uniqueNonEmpty(args.benefitLabels.slice(0, 5)),
    },
    {
      title: "象徴",
      items: uniqueNonEmpty((args.symbolTags ?? []).slice(0, 5)),
    },
    {
      title: "相性・補助情報",
      items: uniqueNonEmpty((args.psychologicalTags ?? []).slice(0, 5)),
    },
  ].filter((g) => g.items.length > 0);

  return groups.length > 0
    ? {
        kind: "supplement",
        heading: "④ 補足（象徴・ご利益）",
        groups,
      }
    : null;
}

function buildFreeDisplaySections(args: {
  reasonSection: DetailReasonSection | null;
  proposalSection: DetailProposalSection | null;
  meaningSection: DetailMeaningSection;
  supplementSection: DetailSupplementSection | null;
}): ShrineDetailDisplaySection[] {
  const sections: ShrineDetailDisplaySection[] = [];

  // Free では公開情報・ご利益などの補足に限定する。
  // 「神社との意味の接続」は concierge 文脈が強いため premiumSections 側へ寄せる。

  if (args.supplementSection) {
    sections.push({
      tier: "free",
      layer: "public",
      section: args.supplementSection,
    });
  }

  return sections;
}

function buildPremiumDisplaySections(args: {
  isConciergeContext: boolean;
  reasonSection: DetailReasonSection | null;
  proposalSection: DetailProposalSection | null;
  meaningSection: DetailMeaningSection;
}): ShrineDetailDisplaySection[] {
  const sections: ShrineDetailDisplaySection[] = [];

  // Premium は「自分の相談文脈との接続」に限定する。
  // 検索・map から直接来た場合は、過度な個人向け理由を出さない。
  if (!args.isConciergeContext) return sections;

  if (args.reasonSection) {
    sections.push({
      tier: "premium",
      layer: "context",
      section: args.reasonSection,
    });
  }

  if (args.proposalSection) {
    sections.push({
      tier: "premium",
      layer: "context",
      section: args.proposalSection,
    });
  }

  if (args.meaningSection) {
    sections.push({
      tier: "premium",
      layer: "context",
      section: args.meaningSection,
    });
  }

  return sections;
}

const HERO_MEANING_BY_TAG: Record<NeedTag, string> = {
  courage: "止まった流れを切り替え、次の一歩を定め直す神社",
  money: "巡りと流れを整え、立て直しの軸を取り戻す神社",
  career: "判断を整え、仕事や転機の方向を見直す神社",
  mental: "気持ちを静め、受け取り方を整え直す神社",
  rest: "心身をゆるめ、回復の順番を取り戻す神社",
  love: "関係性を見つめ直し、縁の受け取り方を整える神社",
  study: "集中を整え、目標に向き直る神社",
};

const HERO_MEANING_BY_LABEL_JA: Record<string, string> = {
  金運: "巡りと流れを整え、立て直しの軸を取り戻す神社",
  前に進むきっかけ: "止まった流れを切り替え、次の一歩を定め直す神社",
  仕事や転機: "判断を整え、仕事や転機の方向を見直す神社",
  不安や気持ちの揺れ: "気持ちを静め、受け取り方を整え直す神社",
  休息: "心身をゆるめ、回復の順番を取り戻す神社",
  良縁や恋愛: "関係性を見つめ直し、縁の受け取り方を整える神社",
  学業や合格: "集中を整え、目標に向き直る神社",
};

function compressShrineMeaning(text?: string | null): string | null {
  const raw = (text ?? "").trim();
  if (!raw) return null;

  const cleaned = raw
    .replace(/^.*?は、/, "")
    .replace(/今の状態で|今回の相談では|今回の相談において/g, "")
    .replace(/参拝先として|候補として/g, "")
    .replace(/重ねやすい|据えやすい|置きやすい/g, "")
    .replace(/段階で/g, "")
    .replace(/です。?$/, "")
    .replace(/\s+/g, " ")
    .trim();

  if (!cleaned) return null;

  if (cleaned.includes("決断や覚悟")) {
    return "止まった流れを切り替え、決断と覚悟を定め直す神社";
  }

  if (cleaned.includes("原点に戻りたい") || cleaned.includes("巡りを整え")) {
    return "焦りを静めて、巡りと原点を整え直す神社";
  }

  if (cleaned.includes("集中") || cleaned.includes("目標設定")) {
    return "気持ちを引き締め、目標に向き直る神社";
  }

  const normalized = cleaned
    .replace(/ための$/, "")
    .replace(/ために$/, "")
    .replace(/したい$/, "")
    .trim();

  return normalized.endsWith("神社") ? normalized : `${normalized}神社`;
}

function resolveHeroMeaningFallbackKey(args: {
  conciergeExplanationPayload?: ExplanationPayload | null;
  conciergeBreakdown?: ConciergeBreakdown | null;
  recommendationRankExplanation?: {
    primary_axis?: string;
    primary_label_ja?: string | null;
  } | null;
}): NeedTag | null {
  const labelJa =
    args.conciergeExplanationPayload?.primary_need_label_ja ??
    args.conciergeExplanationPayload?.primary_reason?.label_ja ??
    args.recommendationRankExplanation?.primary_label_ja ??
    null;

  if (labelJa && HERO_MEANING_BY_LABEL_JA[labelJa]) {
    const matched = Object.entries(HERO_MEANING_BY_TAG).find(
      ([, value]) => value === HERO_MEANING_BY_LABEL_JA[labelJa],
    );
    return (matched?.[0] as NeedTag | undefined) ?? null;
  }

  return getPrimaryNeedTag(args.conciergeBreakdown);
}

function buildHeroMeaningCopy(args: {
  conciergeMode: ConciergeMode | null;
  recommendationReasonDetail?: {
    heroMeaningCopy?: string | null;
  } | null;
  conciergeDeepReason: NarrativeFallback | null;
  conciergeExplanationPayload?: ExplanationPayload | null;
  conciergeBreakdown?: ConciergeBreakdown | null;
  recommendationRankExplanation?: {
    primary_axis?: string;
    primary_label_ja?: string | null;
  } | null;
  shrineName?: string | null;
}): string | null {
  const mode = resolveConciergeMode(args.conciergeMode);

  // fallback order:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. generated fallback from explanation/breakdown/mode
  const detailHeroMeaningCopy = args.recommendationReasonDetail?.heroMeaningCopy?.trim();
  if (detailHeroMeaningCopy) return detailHeroMeaningCopy;

  const explicitHeroMeaning = args.conciergeDeepReason?.heroMeaningCopy?.trim();
  if (explicitHeroMeaning) return explicitHeroMeaning;
  const fromShrineMeaning = compressShrineMeaning(args.conciergeDeepReason?.shrineMeaning);
  if (fromShrineMeaning) return fromShrineMeaning;

  const fallbackKey = resolveHeroMeaningFallbackKey({
    conciergeExplanationPayload: args.conciergeExplanationPayload ?? null,
    conciergeBreakdown: args.conciergeBreakdown ?? null,
    recommendationRankExplanation: args.recommendationRankExplanation ?? null,
  });

  if (fallbackKey && HERO_MEANING_BY_TAG[fallbackKey]) {
    return HERO_MEANING_BY_TAG[fallbackKey];
  }

  if (mode === "compat") {
    return "相性の面から無理なく受け取りやすい神社";
  }

  return "今の流れを整え、次の見方を作る神社";
}

export function buildShrineDetailModel({
  shrine,
  shrineMeaningPayloadV2 = null,
  publicGoshuins,
  conciergeBreakdown = null,
  conciergeReason = null,
  conciergeDeepReason = null,
  conciergeExplanationPayload = null,
  conciergeMode = null,
  recommendationRankExplanation = null,
  recommendationRankComparison = null,
  recommendationReasonDetail = null,
  ctx = null,
  tid = null,
  signals,
}: Args) {
  const { cardProps } = buildShrineCardProps(shrine);

  const qs = new URLSearchParams();
  if (ctx) qs.set("ctx", ctx);
  if (tid) qs.set("tid", String(tid));

  const query = Object.fromEntries(qs.entries());
  const publicGoshuinsViewAllHref = buildShrineHref(shrine.id, {
    subpath: "goshuins",
    query: Object.keys(query).length ? query : undefined,
  });

  const benefitLabels = getBenefitLabels(shrine);
  const tags: ShrineTag[] = benefitLabels.map(toBenefitTag);

  const latestGoshuinImage =
    publicGoshuins
      .filter((g) => typeof g?.image_url === "string" && g.image_url.trim().length > 0)
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")))[0]?.image_url ?? null;

  const heroImageUrl = latestGoshuinImage ?? cardProps.imageUrl ?? null;

  const exp = buildShrineExplanation({
    shrine,
    signals: {
      publicGoshuinsCount: signals?.publicGoshuinsCount ?? publicGoshuins.length,
      views30d: signals?.views30d,
      fav30d: signals?.fav30d,
    },
  });

  const judge = buildShrineJudge(exp, conciergeBreakdown);

  const fallbackProposal = buildProposalFromBreakdown(conciergeBreakdown);

  const mode = resolveConciergeMode(conciergeMode);
  const explanationPayload = conciergeExplanationPayload ?? null;

  const recommendationMeta = buildRecommendationMeta({
    rankExplanation: recommendationRankExplanation,
    rankComparison: recommendationRankComparison,
  });

  const heroMeaningCopy = buildHeroMeaningCopy({
    conciergeMode: mode,
    recommendationReasonDetail,
    conciergeDeepReason,
    conciergeExplanationPayload: explanationPayload,
    conciergeBreakdown,
    recommendationRankExplanation,
    shrineName: cardProps.title ?? null,
  });

  const primaryNeed = getPrimaryNeedTag(conciergeBreakdown);
  const secondaryNeedTags = getSecondaryNeedTags(conciergeBreakdown);
  const combinationNarrative = resolveNeedCombinationNarrative(
    primaryNeed ? [primaryNeed, ...secondaryNeedTags] : secondaryNeedTags,
  );
  const isConciergeContext = ctx === "concierge";

  const rankReason = buildRankReason({
    mode,
    breakdown: conciergeBreakdown,
    primaryNeed,
    secondaryNeedTags,
  });

  const comparisonText = buildComparisonText({
    mode,
    primaryNeed,
    shrineName: cardProps.title ?? null,
    shrineTone: getShrineTone(cardProps.title ?? null),
  });

  const psychologicalTags = buildPsychologicalTags({
    primaryNeed,
    secondaryNeeds: secondaryNeedTags,
  });

  const symbolTags = buildSymbolTags({
    psychologicalTags,
  });

  const consultationSummary = isConciergeContext ? (recommendationReasonDetail?.consultationSummary ?? null) : null;

  // concierge narrative existence check follows the same order:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. conciergeReason text
  const hasConciergeNarrative =
    isConciergeContext &&
    Boolean(
      recommendationReasonDetail?.consultationSummary ||
      recommendationReasonDetail?.shrineMeaning ||
      recommendationReasonDetail?.actionMeaning ||
      conciergeDeepReason?.interpretation ||
      conciergeDeepReason?.shrineMeaning ||
      conciergeDeepReason?.action ||
      (typeof conciergeReason === "string" && conciergeReason.trim().length > 0),
    );

  const proposal = hasConciergeNarrative ? "今回の相談の整理" : fallbackProposal;

  // lead fallback order:
  // 1. recommendationReasonDetail.consultationSummary
  // 2. conciergeDeepReason.interpretation / conciergeReason
  // 3. generated lead
  const proposalLead = resolveDetailLead({
    ctx,
    recommendationReasonDetail,
    conciergeDeepReason,
    conciergeReason,
    generatedLead: buildProposalLead({ mode, explanationPayload }),
  });

  const fallbackProposalWhy = buildProposalWhyFromBreakdown({
    mode,
    breakdown: conciergeBreakdown,
    benefitLabels,
    shrineName: cardProps.title ?? null,
    explanationPayload,
  });

  // proposalWhy fallback order:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. generated breakdown-based fallback
  const narrativeProposalWhy = buildProposalWhyFromNarrativeSources({
    recommendationReasonDetail,
    deepReason: conciergeDeepReason,
    rankReason,
    comparisonText,
  });

  const proposalWhy = isConciergeContext && narrativeProposalWhy ? narrativeProposalWhy : fallbackProposalWhy;

  // lead fallback order:
  // 1. recommendationReasonDetail.consultationSummary
  // 2. conciergeDeepReason.interpretation / conciergeReason
  // 3. generated lead
  const judgeLead = resolveDetailLead({
    ctx,
    recommendationReasonDetail,
    conciergeDeepReason,
    conciergeReason,
    generatedLead: buildProposalLead({ mode, explanationPayload }),
  });

  const goriyakuText =
    mode === "compat"
      ? benefitLabels.length > 0
        ? `${benefitLabels.slice(0, 3).join("・")}のご利益も、生年月日との相性を補う要素として見ています。`
        : "この神社が持つ性質も、生年月日との相性を補う要素として見ています。"
      : benefitLabels.length > 0
        ? `${benefitLabels.slice(0, 3).join("・")}のご利益が、今回の相談内容に近い方向です。`
        : "この神社のご利益が、今回の相談内容に近い方向です。";

  // judgeItems fallback order:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. generated judge items
  const narrativeJudgeItems = buildJudgeItemsFromNarrativeSources({
    recommendationReasonDetail: null,
    deepReason: conciergeDeepReason,
  });

  const judgeItems =
    isConciergeContext && narrativeJudgeItems
      ? narrativeJudgeItems
      : buildJudgeSectionOrder({
          mode,
          explanationPayload,
          breakdown: conciergeBreakdown,
          goriyakuText,
        });

  const judgeSection: RecommendationJudgeSection = {
    disclosureTitle: mode === "compat" ? "相性の根拠" : "おすすめの根拠",
    title: mode === "compat" ? "今回の相性に応じた参拝先" : "今回の相談に応じた参拝先",
    lead: judgeLead,
    items: judgeItems,
  };

  const explanation: ShrineRecommendationExplanation = {
    proposal,
    proposalLead,
    proposalWhy,
    judgeSection,
    rankReason,
  };

  const reasonSection = buildReasonSection({
    mode,
    breakdown: conciergeBreakdown,
    explanationPayload,
    benefitLabels,
    shrineName: cardProps.title ?? null,
    rankReason,
    comparisonText,
    isTop: recommendationRankComparison?.is_top ?? null,
  });

  const proposalSection = buildProposalSection({
    lead: proposalLead,
    consultationSummary,
    proposal,
    combination: combinationNarrative,
    ctx,
  });

  // meaningSection fallback order is handled inside buildMeaningSection:
  // 1. recommendationReasonDetail
  // 2. conciergeDeepReason
  // 3. generated fallback
  const meaningSection = buildMeaningSection({
    lead: undefined,
    deepReason: conciergeDeepReason,
    recommendationReasonDetail,
    shrineName: cardProps.title ?? null,
    benefitLabels,
    mode,
    breakdown: conciergeBreakdown,
  });

  const supplementSection = buildSupplementSection({
    benefitLabels,
    psychologicalTags,
    symbolTags,
    mode,
    explanationPayload,
  });

  const payloadV2DisplaySections = buildMeaningSectionsFromPayloadV2(shrineMeaningPayloadV2);

  const meaningPayloadSource: "v2" | "fallback" = payloadV2DisplaySections ? "v2" : "fallback";

  const freeDisplaySections =
    payloadV2DisplaySections?.freeDisplaySections ??
    buildFreeDisplaySections({
      reasonSection,
      proposalSection,
      meaningSection,
      supplementSection,
    });

  const premiumDisplaySections =
    payloadV2DisplaySections?.premiumDisplaySections ??
    buildPremiumDisplaySections({
      isConciergeContext,
      reasonSection,
      proposalSection,
      meaningSection,
    });

  const sections: ShrineDetailSectionModel[] = [
    ...freeDisplaySections.map((item) => item.section),
    ...premiumDisplaySections.map((item) => item.section),
  ];

  return {
    shrineId: shrine.id,
    cardProps,
    heroImageUrl,
    heroMeaningCopy,
    benefitLabels,
    tags,
    judge,
    conciergeBreakdown,
    exp,
    meaningPayloadSource,
    sections,
    freeDisplaySections,
    premiumDisplaySections,
    reasonSection,
    proposalSection,
    meaningSection,
    supplementSection,
    proposal: explanation.proposal,
    proposalLead: explanation.proposalLead,
    proposalWhy: explanation.proposalWhy,
    explanation,
    publicGoshuinsPreview: publicGoshuins,
    publicGoshuinsViewAllHref,
    judgeSection: explanation.judgeSection,
    rankReason: explanation.rankReason,
    recommendationMeta,
    psychologicalTags,
    symbolTags,
  };
}
