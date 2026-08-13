import { buildReasonNarrative } from "./buildReasonNarrative";
import { buildStateNarrative } from "./buildStateNarrative";
import { buildMeaningNarrative } from "./buildMeaningNarrative";
import { adaptReasonFactsForViewModel, type RecommendationReasonViewFacts } from "./adaptReasonFactsForViewModel";
import type { ConciergeReasonFacts } from "@/lib/api/concierge";
import {
  HERO_COMPAT_SUBTITLE,
  HERO_EYEBROW_LABELS,
  getHeroThemeSubtitle,
  type HeroTheme,
} from "@/lib/concierge/copy/heroThemeCopies";

export type ReasonInputType = "query" | "birthdate" | "fallback";

export type ReasonKey =
  | "need_match"
  | "text_match"
  | "sign_match"
  | "distance"
  | "popular"
  | "element_match";

export type RecommendationLike = {
  id?: number | null;
  name?: string | null;
  display_name?: string | null;
  title?: string | null;
  address?: string | null;
  location?: string | null;
  reason?: string | null;
  explanation?: { summary?: string | null } | null;
  distance_m?: number | null;
  popular_score?: number | null;
  fallback_mode?: string | null;
  astro_elements?: string[] | null;
  astro_priority?: number | null;
  breakdown?: {
    matched_need_tags?: string[] | null;
  } | null;
  breakdown_detail?: any | null;
  /** Display-only aggregate shape. Not a Backend/API contract. */
  reason_facts?: RecommendationReasonViewFacts & {
    primary_axis?: "need" | "benefit" | "feature" | "element" | "distance" | "popularity" | "fallback" | null;
    confidence?: "high" | "mid" | "low" | null;
    matched_element?: string | null;
    distance_label?: string | null;
    popularity_label?: string | null;
    shrine_benefit?: string | null;
    shrine_feature?: string | null;
    visit_fit?: string | null;
    matched_benefits?: string[] | null;
    fallback_reason?: string | null;
  } | null;
};

export type RecommendationReasonViewModel = {
  inputType: ReasonInputType;
  hero: {
    topReasonLabel?: string;
    eyebrowLabel?: string;
    subtitle?: string;
    catchCopy: string;
  };
  list: {
    primaryPhrase: string;
    summary: string;
    secondaryPhrase?: string;
  };
  detail: {
    heroMeaningCopy: string;
    consultationSummary: string;
    shrineMeaning: string;
    actionMeaning?: string;
  };
  rank: {
    whyTop?: string;
    differenceFromOthers?: string;
  };
  debug?: {
    reasonKeys: {
      primary: ReasonKey;
      secondary?: ReasonKey;
      summary: ReasonKey;
    };
  };
};

export type BuildParams = {
  rec: RecommendationLike;
  reasonFacts?: ConciergeReasonFacts | null;
  index: number;
  mode?: "need" | "compat" | string | null;
  /**
   * 相談要約・Heroテーマの生成に使う有効な入力タグ（呼び出し側で解決したeffectiveNeedTags）。
   * 入力側need_tagsを優先し、入力が無い旧Payloadに限りmatched_need_tagsをfallbackとして渡す。
   * Backend APIのフィールド名ではない。
   */
  needTags: string[];
  birthdate?: string | null;
  shrineBenefitLabels?: string[];
  shrineFeatureLabels?: string[];
};

export type Candidate = {
  key: ReasonKey;
  text: string;
};

export type ConsultationMeaningSlots = {
  needPrimary: string | null;
  needSecondary?: string | null;
  state: string | null;
  wish: string | null;
  urgency?: "low" | "mid" | "high" | null;
  posture?: "quiet" | "active" | "reset" | "focus" | null;
  emotionalTone?: "anxious" | "tired" | "stuck" | "hopeful" | null;
};

export type ShrineMeaningSlots = {
  benefitPrimary: string | null;
  benefitSecondary?: string | null;
  feature?: string | null;
  symbol?: string | null;
  tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null;
  actionRole?: string | null;
  visitStyle?: "quiet" | "active" | "grounding" | "decision" | null;
};

export type RecommendationMatchModel = {
  primaryReasonType:
    | "need_benefit_match"
    | "need_feature_match"
    | "compat_element_match"
    | "distance_fit"
    | "popularity_fit"
    | "fallback_choice";
  secondaryReasonTypes: Array<
    | "secondary_need_match"
    | "benefit_support"
    | "feature_support"
    | "sign_support"
    | "distance_support"
    | "popularity_support"
  >;
  rankingReasonType?:
    | "strongest_theme_match"
    | "strongest_compat_match"
    | "most_actionable"
    | "most_stable_choice";
  confidence?: "high" | "mid" | "low" | null;
};

export function clean(value?: string | null): string {
  return (value ?? "").trim();
}

function compactText(value?: string | null, maxLength = 54): string {
  const text = clean(value);
  if (!text) return "";
  if (text.length <= maxLength) return text;

  const sentenceEndIndex = text.slice(0, maxLength).search(/[。.!?！？]/);
  if (sentenceEndIndex > 0) return text.slice(0, sentenceEndIndex + 1).trim();

  return text;
}

function compactOptionalText(value?: string | null, maxLength = 54): string | undefined {
  const text = compactText(value, maxLength);
  return text || undefined;
}

function compactReasonViewModel(reason: ReturnType<typeof buildReasonNarrative>) {
  return {
    hero: {
      ...reason.hero,
      catchCopy: compactText(reason.hero.catchCopy, 32),
    },
    list: {
      ...reason.list,
      primaryPhrase: compactText(reason.list.primaryPhrase, 44),
      summary: compactText(reason.list.summary, 38),
      secondaryPhrase: compactOptionalText(reason.list.secondaryPhrase, 42),
    },
    rank: {
      ...reason.rank,
      whyTop: compactOptionalText(reason.rank.whyTop, 48),
      differenceFromOthers: compactOptionalText(reason.rank.differenceFromOthers, 42),
    },
  };
}

function resolveHeroTheme(needTags?: string[] | null): HeroTheme {
  const tags = (Array.isArray(needTags) ? needTags : []).map((tag) => clean(tag)).filter(Boolean);
  const joined = tags.join(" ");

  if (tags.includes("money") || joined.includes("金運") || joined.includes("巡り")) return "money";
  if (tags.includes("career") || joined.includes("仕事") || joined.includes("転機")) return "work";
  if (tags.includes("love") || joined.includes("恋愛") || joined.includes("関係") || joined.includes("縁")) return "relationship";
  if (tags.includes("mental") || tags.includes("rest") || joined.includes("静か") || joined.includes("休息") || joined.includes("落ち着")) return "quiet";
  if (tags.includes("courage") || joined.includes("切り替え") || joined.includes("前向き") || joined.includes("厄除")) return "reset";

  return "default";
}


function buildHeroCopy(args: {
  mode?: BuildParams["mode"];
  inputType: ReasonInputType;
  needTags?: string[] | null;
  hero: ReturnType<typeof compactReasonViewModel>["hero"];
}): RecommendationReasonViewModel["hero"] {
  if (args.mode === "compat" || args.inputType === "birthdate") {
    return {
      ...args.hero,
      topReasonLabel: "生年月日との重なりが強い",
      eyebrowLabel: HERO_EYEBROW_LABELS.compat,
      subtitle: HERO_COMPAT_SUBTITLE,
    };
  }

  return {
    ...args.hero,
    eyebrowLabel: HERO_EYEBROW_LABELS.need,
    subtitle: getHeroThemeSubtitle(resolveHeroTheme(args.needTags)),
  };
}

export function uniq<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}

export function formatDistance(distanceM?: number | null): string | null {
  if (typeof distanceM !== "number" || Number.isNaN(distanceM)) return null;
  if (distanceM < 1000) return `${Math.round(distanceM)}m`;
  return `${(distanceM / 1000).toFixed(1)}km`;
}

export function resolveInputType(params: BuildParams): ReasonInputType {
  if (params.birthdate) return "birthdate";
  if (params.mode === "compat") return "birthdate";
  if (params.rec.fallback_mode && params.rec.fallback_mode !== "none") return "fallback";
  return "query";
}

export function getPrimaryElement(rec: RecommendationLike): string | null {
  const element = clean(rec.reason_facts?.matched_element);
  if (element) return element;
  const first = rec.astro_elements?.[0];
  return clean(first) || null;
}

function getPrimaryNeedBenefitLabel(rec: RecommendationLike, shrineBenefitLabels?: string[]): string | null {
  const preferredBenefit = (shrineBenefitLabels ?? []).map(clean).find(Boolean);
  if (preferredBenefit) return preferredBenefit;

  const shrineBenefit = clean(rec.reason_facts?.shrine_benefit);
  if (shrineBenefit) return shrineBenefit;

  const matchedBenefit = clean(rec.reason_facts?.matched_benefits?.[0]);
  if (matchedBenefit) return matchedBenefit;

  return null;
}

function getShrineFeatureLabel(rec: RecommendationLike, shrineFeatureLabels?: string[]): string | null {
  const preferredFeature = (shrineFeatureLabels ?? []).map(clean).find(Boolean);
  if (preferredFeature) return preferredFeature;

  const feature = clean(rec.reason_facts?.shrine_feature);
  if (feature) return feature;

  const visitFit = clean(rec.reason_facts?.visit_fit);
  if (visitFit) return visitFit;

  return null;
}

export function buildConsultationMeaningSlots(params: BuildParams): ConsultationMeaningSlots {
  const needPrimary = clean(params.needTags?.[0]) || null;
  const needSecondary = clean(params.needTags?.[1]) || null;

  if (params.mode === "compat") {
    return {
      needPrimary,
      needSecondary,
      state: "感覚がぶれやすい",
      wish: "今の自分に無理なく向き合いたい",
      urgency: "mid",
      posture: "quiet",
      emotionalTone: "stuck",
    };
  }

  if (needPrimary === "厄除け") {
    return {
      needPrimary,
      needSecondary,
      state: "不安や引っかかりが続きやすい",
      wish: "気持ちを整え直したい",
      urgency: "mid",
      posture: "reset",
      emotionalTone: "anxious",
    };
  }
  if (needPrimary === "仕事") {
    return {
      needPrimary,
      needSecondary,
      state: "優先順位が崩れやすい",
      wish: "仕事の流れを整え直したい",
      urgency: "mid",
      posture: "focus",
      emotionalTone: "stuck",
    };
  }
  if (needPrimary === "金運") {
    return {
      needPrimary,
      needSecondary,
      state: "流れの立て直しが必要",
      wish: "巡りを整え直したい",
      urgency: "mid",
      posture: "reset",
      emotionalTone: "stuck",
    };
  }
  if (needPrimary === "転機") {
    return {
      needPrimary,
      needSecondary,
      state: "切り替えの見極めが必要",
      wish: "流れを切り替えたい",
      urgency: "mid",
      posture: "active",
      emotionalTone: "hopeful",
    };
  }
  if (needPrimary === "恋愛") {
    return {
      needPrimary,
      needSecondary,
      state: "受け取り方が揺れやすい",
      wish: "関係の見方を整えたい",
      urgency: "mid",
      posture: "quiet",
      emotionalTone: "anxious",
    };
  }
  if (needPrimary === "健康") {
    return {
      needPrimary,
      needSecondary,
      state: "整える順番が崩れやすい",
      wish: "心身を整え直したい",
      urgency: "mid",
      posture: "quiet",
      emotionalTone: "tired",
    };
  }
  if (needPrimary === "学業") {
    return {
      needPrimary,
      needSecondary,
      state: "集中の軸がぶれやすい",
      wish: "集中と向き合い方を整えたい",
      urgency: "mid",
      posture: "focus",
      emotionalTone: "stuck",
    };
  }

  return {
    needPrimary,
    needSecondary,
    state: "判断が散りやすい",
    wish: "今の流れを整え直したい",
    urgency: "mid",
    posture: "reset",
    emotionalTone: "stuck",
  };
}

export function buildShrineMeaningSlots(params: BuildParams): ShrineMeaningSlots {
  const benefitPrimary = getPrimaryNeedBenefitLabel(params.rec, params.shrineBenefitLabels);
  const benefitSecondary = clean(params.rec.reason_facts?.matched_benefits?.[0]) || undefined;
  const feature = getShrineFeatureLabel(params.rec, params.shrineFeatureLabels) || undefined;
  const shrineName = clean(params.rec.display_name ?? params.rec.name ?? params.rec.title);

  let tone: ShrineMeaningSlots["tone"] = "neutral";
  if (shrineName.includes("三峯")) tone = "strong";
  else if (shrineName.includes("伊勢") || shrineName.includes("内宮")) tone = "quiet";
  else if (shrineName.includes("乃木")) tone = "tight";

  let actionRole: string | undefined;
  let visitStyle: ShrineMeaningSlots["visitStyle"] = "grounding";

  if (tone === "strong") {
    actionRole = "流れを切り替える節目";
    visitStyle = "active";
  } else if (tone === "quiet") {
    actionRole = "静かに整え直す節目";
    visitStyle = "quiet";
  } else if (tone === "tight") {
    actionRole = "判断を定める節目";
    visitStyle = "decision";
  }

  return {
    benefitPrimary,
    benefitSecondary,
    feature,
    symbol: undefined,
    tone,
    actionRole,
    visitStyle,
  };
}

export function buildRecommendationMatchModel(args: {
  params: BuildParams;
  consultation: ConsultationMeaningSlots;
  shrine: ShrineMeaningSlots;
  inputType: ReasonInputType;
  rec: RecommendationLike;
}): RecommendationMatchModel {
  const { consultation, shrine, inputType, rec } = args;
  const f = rec.reason_facts;

  let primaryReasonType: RecommendationMatchModel["primaryReasonType"] = "fallback_choice";

  if (inputType === "birthdate") {
    primaryReasonType = "compat_element_match";
  } else if (f?.primary_axis === "popularity") {
    primaryReasonType = "popularity_fit";
  } else if (f?.primary_axis === "distance") {
    primaryReasonType = "distance_fit";
  } else if (consultation.needPrimary && shrine.benefitPrimary) {
    primaryReasonType = "need_benefit_match";
  } else if (consultation.needPrimary && shrine.feature) {
    primaryReasonType = "need_feature_match";
  } else if (consultation.needPrimary) {
    primaryReasonType = "need_benefit_match";
  } else if (rec.fallback_mode === "nearby_unfiltered") {
    primaryReasonType = "fallback_choice";
  }

  const secondaryReasonTypes: RecommendationMatchModel["secondaryReasonTypes"] = [];
  if (consultation.needSecondary) secondaryReasonTypes.push("secondary_need_match");
  if (shrine.benefitPrimary && f?.primary_axis !== "benefit") secondaryReasonTypes.push("benefit_support");
  if (shrine.feature && f?.primary_axis !== "feature") secondaryReasonTypes.push("feature_support");
  if (typeof rec.astro_priority === "number" && rec.astro_priority > 0) secondaryReasonTypes.push("sign_support");
  if ((typeof rec.distance_m === "number" || clean(rec.reason_facts?.distance_label)) && f?.primary_axis !== "distance") {
    secondaryReasonTypes.push("distance_support");
  }
  if (typeof rec.popular_score === "number" && f?.primary_axis !== "popularity") {
    secondaryReasonTypes.push("popularity_support");
  }

  let rankingReasonType: RecommendationMatchModel["rankingReasonType"] | undefined;
  if (primaryReasonType === "need_benefit_match" || primaryReasonType === "need_feature_match") {
    rankingReasonType = "strongest_theme_match";
  } else if (primaryReasonType === "compat_element_match") {
    rankingReasonType = "strongest_compat_match";
  } else if (primaryReasonType === "distance_fit") {
    rankingReasonType = "most_actionable";
  } else {
    rankingReasonType = "most_stable_choice";
  }

  return {
    primaryReasonType,
    secondaryReasonTypes,
    rankingReasonType,
    confidence: f?.confidence ?? null,
  };
}

/**
 * buildRecommendationReasonViewModel
 *
 * responsibility:
 * - reason を呼ぶ
 * - state を呼ぶ
 * - meaning を呼ぶ
 * - UI shape に詰める
 */
export function buildRecommendationReasonViewModel(params: BuildParams): RecommendationReasonViewModel {
  const adaptedReasonFacts = adaptReasonFactsForViewModel(params.reasonFacts);
  const adaptedParams: BuildParams = adaptedReasonFacts
    ? { ...params, rec: { ...params.rec, reason_facts: adaptedReasonFacts } }
    : params.reasonFacts !== undefined
      ? { ...params, rec: { ...params.rec, reason_facts: null } }
      : params;
  const reason = buildReasonNarrative(adaptedParams);
  const compactReason = compactReasonViewModel(reason);

  const inputType = resolveInputType(adaptedParams);
  const hero = buildHeroCopy({
    mode: adaptedParams.mode,
    inputType,
    needTags: adaptedParams.needTags,
    hero: compactReason.hero,
  });

  const state = buildStateNarrative({
    params: adaptedParams,
    primary: reason._meta.primary,
    secondary: reason._meta.secondary,
  });

  const meaning = buildMeaningNarrative({
    params: adaptedParams,
    primary: reason._meta.primary,
    secondary: reason._meta.secondary,
  });

  return {
    inputType,
    hero,
    list: compactReason.list,
    detail: {
      heroMeaningCopy: meaning.heroMeaningCopy,
      consultationSummary: state.consultationSummary,
      shrineMeaning: meaning.shrineMeaning,
      actionMeaning: meaning.actionMeaning,
    },
    rank: compactReason.rank,
    debug: reason.debug,
  };
}
