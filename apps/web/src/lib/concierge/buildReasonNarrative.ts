/**
 * buildReasonNarrative
 *
 * responsibility:
 * ① 推薦判断を生成する
 * - 主理由
 * - 補助理由
 * - 上位理由
 *
 * boundary:
 * - 状態整理は扱わない
 * - 行動意味は扱わない
 * - 神社補足は扱わない
 */

import {
  clean,
  formatDistance,
  resolveInputType,
  getPrimaryElement,
  buildNeedTagMeaningSlots,
  buildShrineMeaningSlots,
  buildRecommendationMatchModel,
} from "./buildRecommendationReasonViewModel";
import type { BuildParams, ReasonKey, Candidate } from "./buildRecommendationReasonViewModel";
import { toNeedTagLabel } from "./needTagLabelMap";

export type ReasonNarrative = {
  hero: {
    topReasonLabel?: string;
    catchCopy: string;
  };

  list: {
    primaryPhrase: string;
    summary: string;
    secondaryPhrase?: string;
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

  why: {
    primaryReason: string;
    secondaryReason?: string;
    summary: string;
    reasonKeys: {
      primary: ReasonKey;
      secondary?: ReasonKey;
      summary: ReasonKey;
    };
  };

  _meta: {
    primary: Candidate;
    secondary?: Candidate;
    summary: { key: ReasonKey; text: string };
  };
};


// App-wide Evidence & Dark UI Regression Audit Bug-3: 内部need_tag(ASCII slug、例: "money")の
// ラベル化は共有正本(needTagLabelMap.ts、PR #2581でinternal tag leak防止のため導入)へ委譲する。
// 同じtagがRuntime Match(buildRuntimeMatchLine.ts)・相談から見た意味(buildMeaningNarrative.ts)
// ブロックと同じ文言になるよう統一し、画面内での表記ゆれを解消する。未知ASCIIはtoNeedTagLabelが
// nullを返し非表示になる(既存のraw key非表示contractをそのまま踏襲)。
//
// 以下のJA分岐(厄除け/仕事/金運/転機/恋愛/健康/学業)はASCII need_tag slugではなく、旧Thread
// snapshot等が持つ非canonicalなJA category文言向けの意味変換であり、needTagLabelMap.tsの対象
// (ASCII slug専用)外のため統一しない(既存test群がこの分岐を広くカバーしている、後方互換)。
function buildNeedThemeLabel(need?: string | null): string | null {
  const normalized = clean(need);
  if (!normalized) return null;

  if (normalized === "厄除け") return "立て直し";
  if (normalized === "仕事") return "仕事";
  if (normalized === "金運") return "流れの立て直し";
  if (normalized === "転機") return "切り替え";
  if (normalized === "恋愛") return "関係性";
  if (normalized === "健康") return "心身調整";
  if (normalized === "学業") return "学業";

  return toNeedTagLabel(normalized);
}

function buildBenefitMeaningLabel(benefit?: string | null, tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null): string | null {
  const normalized = clean(benefit);
  if (!normalized) return null;

  if (normalized.includes("厄除け")) {
    if (tone === "strong") return "停滞を断ち切る";
    if (tone === "quiet") return "不安を静かにほどく";
    return "流れを立て直す";
  }

  if (normalized.includes("開運")) {
    if (tone === "strong") return "流れを切り替える";
    if (tone === "open") return "流れを通し直す";
    return "流れを整え直す";
  }

  if (normalized.includes("仕事")) {
    if (tone === "tight") return "優先順位を定め直す";
    return "仕事の流れを立て直す";
  }

  if (normalized.includes("勝運")) return "背中を押す";
  if (normalized.includes("学業")) return "集中を定める";
  if (normalized.includes("合格")) return "目標に焦点を合わせる";
  if (normalized.includes("恋愛")) return "関係の流れを整える";
  if (normalized.includes("縁結び")) return "関係の結び目を整える";
  if (normalized.includes("健康")) return "心身の巡りを整える";
  if (normalized.includes("交通安全")) return "移動や流れの乱れを整える";
  if (normalized.includes("航海安全")) return "進む流れを安定させる";
  if (normalized.includes("家内安全")) return "暮らしの流れを落ち着かせる";

  return normalized;
}

function buildFeatureMeaningLabel(feature?: string | null, tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null): string | null {
  const normalized = clean(feature);
  if (!normalized) return null;

  if (tone === "strong") return "切り替えや踏み出し";
  if (tone === "quiet") return "落ち着いて受け止めること";
  if (tone === "tight") return "判断を絞り集中すること";
  if (tone === "open") return "巡りを戻し視野を開くこと";
  return normalized;
}

function buildShrineAxisLabel(args: {
  benefit?: string | null;
  feature?: string | null;
  tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null;
}): string | null {
  const benefitMeaning = buildBenefitMeaningLabel(args.benefit, args.tone);
  const featureMeaning = buildFeatureMeaningLabel(args.feature, args.tone);

  if (benefitMeaning) return benefitMeaning;
  if (featureMeaning) return featureMeaning;
  return null;
}

function getMatchedVisitStyleTags(rec: BuildParams["rec"]): string[] {
  const features = (rec as any)?.breakdown_detail?.features;
  const visitStyle = features && typeof features === "object" ? (features as any).visit_style : null;
  const matched = visitStyle && typeof visitStyle === "object" ? (visitStyle as any).matched_tags : null;
  if (!Array.isArray(matched)) return [];
  return matched.filter((tag): tag is string => typeof tag === "string" && clean(tag).length > 0);
}

function normalizeVisitStyleTag(tag: string): string {
  const normalized = clean(tag);
  if (!normalized) return "";

  if (normalized === "quiet" || normalized === "静か") return "quiet";
  if (normalized === "nature" || normalized === "自然") return "nature";
  if (normalized === "reset" || normalized === "切り替え") return "reset";
  if (normalized === "less_crowded" || normalized === "混雑少なめ" || normalized === "人混み少なめ") return "less_crowded";
  if (normalized === "classic" || normalized === "定番") return "classic";
  if (normalized === "nearby" || normalized === "近場") return "nearby";

  return normalized;
}

function buildVisitStyleLabel(tag: string): string | null {
  const normalized = normalizeVisitStyleTag(tag);
  if (!normalized) return null;

  if (normalized === "quiet") return "静かに落ち着いて過ごしたい気持ち";
  if (normalized === "nature") return "自然を感じながら整えたい気持ち";
  if (normalized === "reset") return "気持ちを切り替えたい流れ";
  if (normalized === "less_crowded") return "人混みを避けて落ち着きたい条件";
  if (normalized === "classic") return "定番感があり安心して選びたい条件";
  if (normalized === "nearby") return "近場で無理なく向かいたい条件";

  return null;
}

function buildVisitStylePrimaryText(rec: BuildParams["rec"]): string | null {
  const tag = getMatchedVisitStyleTags(rec)[0];
  const label = tag ? buildVisitStyleLabel(tag) : null;
  if (!label) return null;
  return `選んだ参拝スタイルの「${label}」にも合うため、この神社が候補に入っています。`;
}

function buildVisitStyleCatchCopy(rec: BuildParams["rec"]): string | null {
  const tag = getMatchedVisitStyleTags(rec)[0];
  const normalized = tag ? normalizeVisitStyleTag(tag) : "";
  if (!normalized) return null;

  if (normalized === "quiet") return "静かに落ち着いて過ごしたい時の神社";
  if (normalized === "nature") return "自然を感じながら整えたい時の神社";
  if (normalized === "reset") return "気持ちを切り替えたい時の神社";
  if (normalized === "less_crowded") return "人混みを避けて落ち着きたい時の神社";
  if (normalized === "classic") return "安心して選びたい時の神社";
  if (normalized === "nearby") return "無理なく向かいやすい神社";

  return null;
}

function buildIntersectionPrimaryText(args: {
  need?: string | null;
  benefit?: string | null;
  feature?: string | null;
  tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null;
}): string | null {
  const needLabel = buildNeedThemeLabel(args.need);
  const shrineLabel = buildShrineAxisLabel({ benefit: args.benefit, feature: args.feature, tone: args.tone ?? null });

  if (needLabel && shrineLabel) {
    return `今回の相談の中心にある「${needLabel}」のテーマと、この神社の「${shrineLabel}」の性質が重なるため、この神社が候補に入っています。`;
  }

  if (needLabel) {
    return `今回の相談の中心にある「${needLabel}」のテーマと重なるため、この神社が候補に入っています。`;
  }

  if (shrineLabel) {
    return `この神社の「${shrineLabel}」の性質が、今回の相談と重なるため、この神社が候補に入っています。`;
  }

  return null;
}

function buildSecondaryNeedText(need: string): string {
  return `加えて、「${need}」の観点でも補助的な重なりがあります。`;
}

function buildBenefitSupportText(
  benefit: string,
  tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null,
): string {
  const meaning = buildBenefitMeaningLabel(benefit, tone) || benefit;
  return `加えて、${meaning}方向でも、この神社らしい重なりがあります。`;
}

function buildFeatureSupportText(
  feature: string,
  tone?: "strong" | "quiet" | "tight" | "open" | "neutral" | null,
): string {
  const meaning = buildFeatureMeaningLabel(feature, tone) || feature;
  return `加えて、${meaning}という向き合い方も、この神社らしい重なり方です。`;
}

function buildQueryCandidates(params: BuildParams): Candidate[] {
  const consultation = buildNeedTagMeaningSlots(params);
  const shrine = buildShrineMeaningSlots(params);
  const rec = params.rec;
  const out: Candidate[] = [];

  const primary = buildIntersectionPrimaryText({
    need: consultation.needPrimary,
    benefit: shrine.benefitPrimary,
    feature: shrine.feature,
    tone: shrine.tone,
  });

  if (primary) {
    out.push({ key: "need_match", text: primary });
  } else {
    const needLabel = buildNeedThemeLabel(consultation.needPrimary);
    if (needLabel) {
      out.push({
        key: "need_match",
        text: `今回の相談の中心にある「${needLabel}」のテーマと重なるため、この神社が候補に入っています。`,
      });
    }
  }

  if (consultation.needSecondary) {
    out.push({ key: "text_match", text: buildSecondaryNeedText(consultation.needSecondary) });
  } else if (shrine.benefitPrimary && primary) {
    out.push({ key: "need_match", text: buildBenefitSupportText(shrine.benefitPrimary, shrine.tone) });
  } else if (shrine.feature) {
    out.push({ key: "text_match", text: buildFeatureSupportText(shrine.feature, shrine.tone) });
  }

  const visitStyleText = buildVisitStylePrimaryText(rec);
  if (visitStyleText) {
    out.push({ key: "text_match", text: visitStyleText });
  }

  if (typeof rec.astro_priority === "number" && rec.astro_priority > 0) {
    out.push({ key: "sign_match", text: "気質とのなじみも補助的に見られます。" });
  }

  const distance = formatDistance(rec.distance_m);
  if (distance) {
    out.push({ key: "distance", text: `${distance}圏内で、実際に向かいやすい条件もあります。` });
  }

  if (typeof rec.popular_score === "number") {
    out.push({ key: "popular", text: "参拝先として選びやすい安定感もあります。" });
  }

  return out;
}

function buildBirthdateCandidates(params: BuildParams): Candidate[] {
  const rec = params.rec;
  const out: Candidate[] = [];
  const element = getPrimaryElement(rec);

  if (element) {
    out.push({
      key: "element_match",
      text: `生年月日から見た「${element}」の要素との相性が強く重なるため、この神社が候補に入っています。`,
    });
  }

  if (typeof rec.astro_priority === "number" && rec.astro_priority > 0) {
    out.push({ key: "sign_match", text: "気質とのなじみも補助的に見られます。" });
  }

  const distance = formatDistance(rec.distance_m);
  if (distance) {
    out.push({ key: "distance", text: `${distance}圏内で、落ち着いて向かいやすい条件もあります。` });
  }

  if (typeof rec.popular_score === "number") {
    out.push({ key: "popular", text: "参拝先として選びやすい安定感もあります。" });
  }

  return out;
}

function buildFallbackCandidates(params: BuildParams): Candidate[] {
  const rec = params.rec;
  const out: Candidate[] = [];
  const distance = formatDistance(rec.distance_m);
  const hasPopular = typeof rec.popular_score === "number";

  if (distance) {
    out.push({ key: "distance", text: "今回はまず動きやすさを優先して、この神社が候補に入っています。" });
    if (hasPopular) {
      out.push({ key: "popular", text: "その中でも、選びやすい安定感があります。" });
    }
    return out;
  }

  if (hasPopular) {
    out.push({ key: "popular", text: "今回はまず選びやすさを優先して、この神社が候補に入っています。" });
    out.push({ key: "distance", text: "無理なく足を運びやすい条件もあります。" });
    return out;
  }

  out.push({ key: "distance", text: "今回はまず動きやすさを優先して、この神社が候補に入っています。" });
  return out;
}

function buildFactsCandidates(params: BuildParams, inputType: ReturnType<typeof resolveInputType>): Candidate[] {
  const consultation = buildNeedTagMeaningSlots(params);
  const shrine = buildShrineMeaningSlots(params);
  const match = buildRecommendationMatchModel({
    params,
    consultation,
    shrine,
    inputType,
    rec: params.rec,
  });
  const rec = params.rec;
  const out: Candidate[] = [];
  const element = clean(rec.reason_facts?.matched_element) || getPrimaryElement(rec);
  const distance = formatDistance(rec.distance_m);
  const distanceLabel = clean(rec.reason_facts?.distance_label) || distance;
  const primaryFactType = clean(rec.reason_facts?.primary_fact_type);
  const primaryFactLabel = clean(rec.reason_facts?.primary_fact_label);

  if (primaryFactLabel) {
    switch (primaryFactType) {
      case "element":
        out.push({ key: "element_match", text: `生年月日から見た「${primaryFactLabel}」の要素との相性が強く重なるため、この神社が候補に入っています。` });
        break;
      case "need_tag":
        out.push({ key: "need_match", text: `相談内容の「${primaryFactLabel}」と一致するため、この神社が候補に入っています。` });
        break;
      case "user_selected_tag":
        out.push({ key: "need_match", text: `明示的に指定した「${primaryFactLabel}」と一致するため、この神社が候補に入っています。` });
        break;
      case "goriyaku_tag":
        out.push({ key: "need_match", text: `「${primaryFactLabel}」のご利益が相談に重なるため、この神社が候補に入っています。` });
        break;
      case "history_theme":
      case "text_hint":
        out.push({ key: "text_match", text: `「${primaryFactLabel}」という意味・特徴が相談に重なるため、この神社が候補に入っています。` });
        break;
      case "visit_style":
        out.push({ key: "text_match", text: `参拝Preferenceの「${primaryFactLabel}」に合うため、この神社が候補に入っています。` });
        break;
      case "fallback":
        out.push({ key: "distance", text: primaryFactLabel });
        break;
    }
  }

  if (out.length === 0) switch (match.primaryReasonType) {
    case "need_benefit_match": {
      const text = buildIntersectionPrimaryText({
        need: consultation.needPrimary,
        benefit: shrine.benefitPrimary,
        feature: null,
        tone: shrine.tone,
      });
      if (text) {
        out.push({ key: "need_match", text });
      } else {
        const needLabel = buildNeedThemeLabel(consultation.needPrimary);
        if (needLabel) {
          out.push({
            key: "need_match",
            text: `今回の相談の中心にある「${needLabel}」のテーマと重なるため、この神社が候補に入っています。`,
          });
        }
      }
      break;
    }
    case "need_feature_match": {
      const text = buildIntersectionPrimaryText({
        need: consultation.needPrimary,
        benefit: null,
        feature: shrine.feature,
        tone: shrine.tone,
      });
      if (text) out.push({ key: "text_match", text });
      break;
    }
    case "compat_element_match": {
      if (element) {
        out.push({
          key: "element_match",
          text: `生年月日から見た「${element}」の要素との相性が強く重なるため、この神社が候補に入っています。`,
        });
      }
      break;
    }
    case "distance_fit": {
      out.push({
        key: "distance",
        text: distanceLabel ? `${distanceLabel}圏内で実際に動きやすい条件があり、この神社が候補に入っています。` : "無理なく足を運びやすい条件があり、この神社が候補に入っています。",
      });
      break;
    }
    case "popularity_fit": {
      out.push({
        key: "popular",
        text: clean(rec.reason_facts?.popularity_label) || "参拝先として選びやすい安定感があり、この神社が候補に入っています。",
      });
      break;
    }
    case "fallback_choice":
    default:
      out.push({
        key: typeof rec.popular_score === "number" ? "popular" : "distance",
        text:
          typeof rec.popular_score === "number"
            ? "今回はまず選びやすさを優先して、この神社が候補に入っています。"
            : "今回はまず動きやすさを優先して、この神社が候補に入っています。",
      });
      break;
  }

  const visitStyleText = buildVisitStylePrimaryText(rec);
  if (visitStyleText) {
    out.push({ key: "text_match", text: visitStyleText });
  }

  for (const secondaryType of match.secondaryReasonTypes) {
    switch (secondaryType) {
      case "secondary_need_match":
        if (consultation.needSecondary) {
          out.push({ key: "text_match", text: buildSecondaryNeedText(consultation.needSecondary) });
        }
        break;
      case "benefit_support":
        if (shrine.benefitPrimary) {
          out.push({ key: "need_match", text: buildBenefitSupportText(shrine.benefitPrimary, shrine.tone) });
        }
        break;
      case "feature_support":
        if (shrine.feature) {
          out.push({ key: "text_match", text: buildFeatureSupportText(shrine.feature, shrine.tone) });
        }
        break;
      case "sign_support":
        out.push({ key: "sign_match", text: "気質とのなじみも補助的に見られます。" });
        break;
      case "distance_support":
        if (distanceLabel) {
          out.push({ key: "distance", text: `${distanceLabel}圏内で、実際に向かいやすい条件もあります。` });
        }
        break;
      case "popularity_support":
        out.push({ key: "popular", text: "参拝先として選びやすい安定感もあります。" });
        break;
    }
  }

  return out;
}

function dedupeCandidates(candidates: Candidate[]): Candidate[] {
  const seenKeys = new Set<string>();
  const seenTexts = new Set<string>();

  return candidates.filter((c) => {
    const text = clean(c.text);
    if (!text) return false;
    if (seenKeys.has(c.key)) return false;
    if (seenTexts.has(text)) return false;
    seenKeys.add(c.key);
    seenTexts.add(text);
    return true;
  });
}

function buildSummary(
  inputType: ReturnType<typeof resolveInputType>,
  primary: Candidate,
  secondary?: Candidate,
): { key: ReasonKey; text: string } {
  const blocked = new Set([clean(primary.text), clean(secondary?.text)]);

  const byType: Record<ReturnType<typeof resolveInputType>, Array<{ key: ReasonKey; text: string }>> = {
    query: [
      { key: "need_match", text: "相談内容と神社の性質が重なるため、この神社が選ばれています。" },
      { key: "text_match", text: "今の相談の流れに沿って受け取りやすい点が、この神社が選ばれた理由です。" },
    ],
    birthdate: [
      { key: "element_match", text: "生年月日との相性の重なりを主軸に、この神社が選ばれています。" },
      { key: "sign_match", text: "気質とのなじみも含めて見やすい点が、この神社が選ばれた理由です。" },
    ],
    fallback: [
      { key: "distance", text: "今回はまず動きやすさを優先して、この神社が選ばれています。" },
      { key: "popular", text: "今回はまず選びやすさを優先して、この神社が選ばれています。" },
    ],
  };

  const found = byType[inputType].find((x) => !blocked.has(clean(x.text)));
  return found ?? byType[inputType][0];
}

function buildTopReasonLabel(inputType: ReturnType<typeof resolveInputType>, primaryKey: ReasonKey, index: number) {
  if (index !== 0) return undefined;
  if (inputType === "query") return primaryKey === "need_match" ? "相談との一致が強い" : "内容との一致が強い";
  if (inputType === "birthdate") return "相性との一致が強い";
  if (inputType === "fallback") {
    if (primaryKey === "distance") return "まず動きやすい";
    if (primaryKey === "popular") return "まず選びやすい";
    return "見やすい候補";
  }
  return undefined;
}

function buildHeroCatchCopy(params: BuildParams, primary: Candidate): string {
  const visitStyleCatchCopy = buildVisitStyleCatchCopy(params.rec);
  if (visitStyleCatchCopy) return visitStyleCatchCopy;

  if (params.mode === "compat") {
    return "相性から静かに選びたい時の神社";
  }

  const need = clean(params.needTags?.[0]);

  if (need === "厄除け") return "気持ちを立て直したい時の神社";
  if (need === "仕事") return "仕事の流れを整えたい時の神社";
  if (need === "金運") return "流れを切り替えたい時の神社";

  if (primary.key === "distance") return "まず行きやすさを優先したい時の神社";
  if (primary.key === "element_match") return "相性から無理なく選びたい時の神社";

  return "今の状態に重ねて見やすい神社";
}

function buildRankReason(
  params: BuildParams,
  _primary: Candidate,
  _secondary?: Candidate,
): { whyTop?: string; differenceFromOthers?: string } {
  if (params.index !== 0) {
    return {};
  }

  const inputType = resolveInputType(params);
  const consultation = buildNeedTagMeaningSlots(params);
  const shrine = buildShrineMeaningSlots(params);
  const match = buildRecommendationMatchModel({
    params,
    consultation,
    shrine,
    inputType,
    rec: params.rec,
  });

  const tone = shrine.tone;
  const needPrimary = clean(consultation.needPrimary);

  switch (match.rankingReasonType) {
    case "strongest_theme_match": {
      if (tone === "strong") {
        return {
          whyTop: "今回の候補の中でも、切り替えや踏み出しに向けた重なりが見えやすい候補です。",
          differenceFromOthers: "他候補と比べると、流れを切り替える方向へ気持ちを向けやすい位置づけです。",
        };
      }
      if (tone === "quiet") {
        return {
          whyTop: "今回の候補の中でも、落ち着いて受け止めやすい重なりが見えやすい候補です。",
          differenceFromOthers: "他候補と比べると、今の状態を静かに整えながら向き合いやすい位置づけです。",
        };
      }
      if (tone === "tight") {
        return {
          whyTop: "今回の候補の中でも、判断を絞りやすい重なりが見えやすい候補です。",
          differenceFromOthers: "他候補と比べると、優先順位を定め直しながら向き合いやすい位置づけです。",
        };
      }
      if (tone === "open") {
        return {
          whyTop: "今回の候補の中でも、巡りや視野を開きやすい重なりが見えやすい候補です。",
          differenceFromOthers: "他候補と比べると、滞りをほどいて流れを通し直しやすい位置づけです。",
        };
      }
      if (needPrimary === "学業") {
        return {
          whyTop: "今回の候補の中でも、学業への集中に重ねやすい候補です。",
          differenceFromOthers: "他候補と比べると、目標に向けて意識を絞りやすい位置づけです。",
        };
      }
      return {
        whyTop: "今回の候補の中でも、相談内容との重なりが見えやすい候補です。",
        differenceFromOthers: "他候補と比べると、今回優先したいテーマにまっすぐ重なりやすい位置づけです。",
      };
    }
    case "strongest_compat_match":
      return {
        whyTop: "今回の候補の中でも、生年月日との相性の重なりが見えやすい候補です。",
        differenceFromOthers: "他候補と比べると、気質に無理なく馴染みやすい位置づけです。",
      };
    case "most_actionable":
      return {
        whyTop: "今回の候補の中でも、実際に動きやすい条件が見えやすい候補です。",
        differenceFromOthers: "他候補と比べると、足を運ぶこと自体が負担になりにくい位置づけです。",
      };
    case "most_stable_choice":
    default:
      return {
        whyTop: "今回の候補の中でも、選びやすさの安定感が見えやすい候補です。",
        differenceFromOthers: "他候補と比べると、迷いがある段階でも選択しやすい位置づけです。",
      };
  }
}

export function buildReasonNarrative(params: BuildParams): ReasonNarrative {
  const inputType = resolveInputType(params);
  const factsCandidates = buildFactsCandidates(params, inputType);

  const raw =
    factsCandidates.length > 0
      ? factsCandidates
      : inputType === "query"
        ? buildQueryCandidates(params)
        : inputType === "birthdate"
          ? buildBirthdateCandidates(params)
          : buildFallbackCandidates(params);

  const candidates = dedupeCandidates(raw);

  const primary =
    candidates[0] ??
    ({
      key: inputType === "birthdate" ? "element_match" : inputType === "fallback" ? "distance" : "need_match",
      text:
        inputType === "birthdate"
          ? "生年月日との相性を軸に選びやすい候補です"
          : inputType === "fallback"
            ? "まずは動きやすさを優先して見られる候補です"
            : "今の気持ちに沿って選びやすい候補です",
    } satisfies Candidate);

  const secondary = candidates
    .slice(1)
    .find((x) => x.key !== primary.key && clean(x.text) !== clean(primary.text));
  const summary = buildSummary(inputType, primary, secondary);
  const rank = buildRankReason(params, primary, secondary);

  return {
    hero: {
      topReasonLabel: buildTopReasonLabel(inputType, primary.key, params.index),
      catchCopy: buildHeroCatchCopy(params, primary),
    },
    list: {
      primaryPhrase: primary.text,
      summary: summary.text,
      secondaryPhrase: secondary?.text,
    },
    rank,
    debug: {
      reasonKeys: {
        primary: primary.key,
        secondary: secondary?.key,
        summary: summary.key,
      },
    },
    why: {
      summary: summary.text,
      primaryReason: primary.text,
      secondaryReason: secondary?.text,
      reasonKeys: {
        primary: primary.key,
        secondary: secondary?.key,
        summary: summary.key,
      },
    },
    _meta: {
      primary,
      secondary,
      summary,
    },
  };
}
