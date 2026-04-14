/**
 * buildMeaningNarrative
 *
 * responsibility:
 * ③ 行動意味を生成する
 *
 * boundary:
 * - 推薦判断は扱わない
 * - 状態整理は扱わない
 * - 神社補足は扱わない
 */

import {
  clean,
  buildConsultationMeaningSlots,
  buildShrineMeaningSlots,
} from "./buildRecommendationReasonViewModel";
import type {
  BuildParams,
  Candidate,
  ConsultationMeaningSlots,
  ShrineMeaningSlots,
} from "./buildRecommendationReasonViewModel";

export type MeaningNarrative = {
  heroMeaningCopy: string;
  shrineMeaning: string;
  actionMeaning?: string;
};

type ShrineNarrativeContext = {
  symbol?: string;
  place?: "mountain" | "forest" | "water" | "city";
  ritual?: string;
  pattern?: string;
};

const SHRINE_NARRATIVE_CONTEXT_MAP: Record<string, ShrineNarrativeContext> = {
  "三峯神社": {
    place: "mountain",
    symbol: "古くから節目や鍛錬の場として向き合われてきた場所でもあり",
    ritual: "高低差や道のりを進むこと自体が、気持ちを切り替える参拝体験につながります。",
    pattern: "人生の転機や、気持ちを切り替えたい時に選ばれやすい神社です。",
  },
  "乃木神社": {
    place: "city",
    symbol: "日常の延長で姿勢を整え、目標へ向き直る節目として受け取られやすい神社でもあり",
    ritual: "街の中でも立ち寄りやすく、気持ちと集中を整え直す入口にしやすい参拝です。",
    pattern: "学業や仕事の節目で、姿勢を整えたい時に選ばれやすい神社です。",
  },
  "住吉大社": {
    place: "water",
    symbol: "流れや進路の守りと重ねて受け取られてきた場所でもあり",
    ritual: "水辺の気配を感じながら、流れを整え直すように参拝しやすい神社です。",
    pattern: "切り替えや立て直しの節目に選ばれやすい神社です。",
  },
  "伊勢神宮（内宮）": {
    place: "forest",
    symbol: "静けさの中で姿勢や受け取り方を整える場として重ねられてきた場所でもあり",
    ritual: "木々に包まれた参道を進みながら、落ち着いて向き合い方を整えやすい参拝です。",
    pattern: "気持ちを整え直し、落ち着いて受け止めたい時に選ばれやすい神社です。",
  },
  "亀戸天神社": {
    place: "water",
    symbol: "学びや願掛けの節目として重ねて受け取られてきた場所でもあり",
    ritual: "水辺の気配を感じながら、焦りをほどいて目標へ向き直しやすい参拝です。",
    pattern: "受験や学びの節目で、集中を整えたい時に選ばれやすい神社です。",
  },
};

function buildHeroMeaningFromSlots(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
}): string {
  if (args.mode === "compat") {
    return "相性の無理が少なく、落ち着いて受け取りやすい神社";
  }

  if (args.need === "厄除け") return "気持ちを立て直し、受け取り方を整え直す神社";
  if (args.need === "仕事") return "仕事の流れと判断軸を整え直す神社";
  if (args.need === "金運") return "止まった流れを整え、立て直しの軸を作る神社";
  if (args.need === "転機") return "切り替えの流れを整え、次の見方を作る神社";
  if (args.need === "恋愛") return "関係性の受け取り方を整え、気持ちの置き場を作る神社";
  if (args.need === "健康") return "心身を整え、回復の順番を取り戻す神社";
  if (args.need === "学業") return "集中を整え、目標への向き合い方を立て直す神社";

  if (args.shrine.tone === "strong") {
    return "流れを切り替え、次の一歩を動かしやすい神社";
  }

  if (args.shrine.tone === "quiet") {
    return "落ち着いて受け止め、静かに整え直しやすい神社";
  }

  if (args.shrine.tone === "tight") {
    return "判断を絞り、集中を定め直しやすい神社";
  }

  if (args.shrine.tone === "open") {
    return "巡りを戻し、視野を開き直しやすい神社";
  }

  return "今の流れを整え、次の見方を作る神社";
}

function inferPlaceFromShrineText(text: string | null): ShrineNarrativeContext["place"] | undefined {
  const value = clean(text)?.toLowerCase() ?? "";
  if (!value) return undefined;

  if (
    value.includes("山") ||
    value.includes("峰") ||
    value.includes("岳") ||
    value.includes("mountain") ||
    value.includes("okumiya")
  ) {
    return "mountain";
  }

  if (
    value.includes("森") ||
    value.includes("forest") ||
    value.includes("杜") ||
    value.includes("林")
  ) {
    return "forest";
  }

  if (
    value.includes("水") ||
    value.includes("川") ||
    value.includes("滝") ||
    value.includes("海") ||
    value.includes("池") ||
    value.includes("water")
  ) {
    return "water";
  }

  if (
    value.includes("街") ||
    value.includes("市") ||
    value.includes("駅") ||
    value.includes("都市") ||
    value.includes("city")
  ) {
    return "city";
  }

  return undefined;
}

function buildPlacePhrase(place?: ShrineNarrativeContext["place"]): string | null {
  if (place === "mountain") return "山の気配の中で";
  if (place === "forest") return "森に包まれた空気の中で";
  if (place === "water") return "水の流れを感じながら";
  if (place === "city") return "街の中でも立ち寄りやすく";
  return null;
}

function buildSymbolPhrase(context: ShrineNarrativeContext): string | null {
  return clean(context.symbol) || null;
}

function buildRitualPhrase(context: ShrineNarrativeContext): string | null {
  return clean(context.ritual) || null;
}

function buildPatternPhrase(context: ShrineNarrativeContext): string | null {
  return clean(context.pattern) || null;
}

function resolveShrineNarrativeContextFromMap(texts: string[]): ShrineNarrativeContext | null {
  const candidates = texts.map((text) => clean(text)).filter(Boolean) as string[];

  for (const candidate of candidates) {
    const matchedEntry = Object.entries(SHRINE_NARRATIVE_CONTEXT_MAP).find(([name]) => candidate.includes(name));
    if (matchedEntry) {
      return matchedEntry[1];
    }
  }

  return null;
}

function buildShrineNarrativeContext(params: BuildParams): ShrineNarrativeContext {
  const shrineNameCandidates = Array.from(
    new Set(
      [
        clean((params.rec as { display_name?: string | null }).display_name),
        clean((params.rec as { title?: string | null }).title),
        clean((params.rec as { name?: string | null }).name),
      ].filter(Boolean) as string[],
    ),
  );

  const featureTexts = (params.shrineFeatureLabels ?? []).map(clean).filter(Boolean) as string[];
  // name resolver: 神社名のみで照合（benefit label は混入させない）
  const mapped = resolveShrineNarrativeContextFromMap(shrineNameCandidates);
  if (mapped) {
    return mapped;
  }

  // text resolver: featureTexts のみで place 推定（benefit label は参照しない）
  const joined = featureTexts.join(" ");
  const place = inferPlaceFromShrineText(joined);

  let symbol: string | undefined;
  let ritual: string | undefined;
  let pattern: string | undefined;

  if (place === "mountain") {
    symbol = "古くから節目や鍛錬の場として向き合われてきた場所でもあり";
    ritual = "高低差や道のりを進むこと自体が、気持ちを切り替える参拝体験につながります。";
    pattern = "人生の転機や、気持ちを切り替えたい時に選ばれやすい神社です。";
  } else if (place === "forest") {
    symbol = "静けさの中で気持ちを整える場として受け取られてきた場所でもあり";
    ritual = "木々に包まれた参道を進みながら、落ち着いて気持ちを整えやすい参拝です。";
    pattern = "落ち着いて考えを整えたい時に選ばれやすい神社です。";
  } else if (place === "water") {
    symbol = "流れや浄化の象徴と重ねて受け取られやすい場所でもあり";
    ritual = "水辺や流れを感じながら、滞りをほどくように参拝しやすい神社です。";
    pattern = "切り替えや立て直しの節目に選ばれやすい神社です。";
  } else if (place === "city") {
    symbol = "日常の延長で節目を作りやすい場所として親しまれてきた神社でもあり";
    ritual = "日常の動線の中でも立ち寄りやすく、今の流れを切り替える入口にしやすい参拝です。";
    pattern = "忙しい時期でも節目を作りたい人に選ばれやすい神社です。";
  }

  return {
    symbol,
    place,
    ritual,
    pattern,
  };
}

function buildMeaningReceiver(args: {
  need: string | null;
  benefit: string | null;
  feature: string | null;
  mode?: BuildParams["mode"];
}): string {
  const baseWish = buildNeedWishBase(args.need, args.mode);
  const qualifier = buildNeedSupportQualifier({ benefit: args.benefit, feature: args.feature });

  if (!qualifier) return baseWish;
  return `${qualifier}${baseWish}`;
}

function buildMeaningCoreFromSlots(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
  receiver: string;
  context: ShrineNarrativeContext;
}): string {
  const symbol = buildSymbolPhrase(args.context);
  const place = buildPlacePhrase(args.context.place);
  const intro = [symbol, place].filter(Boolean).join(" ");
  const introText = intro ? `${intro} ` : "";

  if (args.mode === "compat") {
    return `この神社は、${introText}${args.receiver}を落ち着いて受け止め直し、自分にとって無理のない向き合い方を整える節目として置きやすい場所です。`;
  }

  if (args.need === "厄除け") {
    return `この神社は、${introText}${args.receiver}を抱え直すのではなく、ほどきながら整え直す節目として置きやすい場所です。`;
  }

  if (args.need === "仕事") {
    return `この神社は、${introText}${args.receiver}を見直し、仕事の流れと判断軸を立て直す節目として置きやすい場所です。`;
  }

  if (args.need === "転機") {
    return `この神社は、${introText}${args.receiver}を見直し、切り替えの流れを整え直す節目として置きやすい場所です。`;
  }

  if (args.need === "恋愛") {
    return `この神社は、${introText}${args.receiver}を見つめ直し、関係性の受け取り方を整える節目として置きやすい場所です。`;
  }

  if (args.need === "健康") {
    return `この神社は、${introText}${args.receiver}を急がず見直し、心身を整え直す順番を取り戻す節目として置きやすい場所です。`;
  }

  if (args.need === "学業") {
    return `この神社は、${introText}${args.receiver}を見直し、集中の軸と取り組み方を定め直す節目として置きやすい場所です。`;
  }

  if (args.shrine.tone === "strong") {
    return `この神社は、${introText}${args.receiver}をため込み続けるのではなく、流れを切り替える節目として置きやすい場所です。`;
  }

  if (args.shrine.tone === "quiet") {
    return `この神社は、${introText}${args.receiver}を静かに受け止め直し、落ち着いて整える節目として置きやすい場所です。`;
  }

  if (args.shrine.tone === "tight") {
    return `この神社は、${introText}${args.receiver}を広げすぎず、判断と集中の軸を定め直す節目として置きやすい場所です。`;
  }

  if (args.shrine.tone === "open") {
    return `この神社は、${introText}${args.receiver}を抱えたまま閉じるのではなく、巡りと視野を開き直す節目として置きやすい場所です。`;
  }

  return `この神社は、${introText}${args.receiver}を見直し、今の流れを整える節目として置きやすい場所です。`;
}

function buildFallbackWhyNowFromPrimary(args: {
  consultation: ConsultationMeaningSlots;
  primary: Candidate;
}): string {
  if (!clean(args.consultation.needPrimary) && args.primary.key === "distance") {
    return "遠くの正解を探すほど動けなくなりやすい今は、";
  }

  if (!clean(args.consultation.needPrimary) && (args.primary.key === "element_match" || args.primary.key === "sign_match")) {
    return "強い刺激よりも無理なく受け取れる場所の方が整いやすい今は、";
  }

  return "答えを急ぐほど判断が散りやすい今は、";
}

function buildFallbackActionRoleFromPrimary(args: {
  consultation: ConsultationMeaningSlots;
  primary: Candidate;
}): string {
  if (!clean(args.consultation.needPrimary) && args.primary.key === "distance") {
    return "まず足を運べる場所から流れを整え直す節目として向き合いやすい場所です。";
  }

  if (!clean(args.consultation.needPrimary) && (args.primary.key === "element_match" || args.primary.key === "sign_match")) {
    return "無理なく受け取れる場所で、気持ちと判断を整える節目として向き合いやすい場所です。";
  }

  return "気持ちと流れを整えながら、次の見方を見直す節目として向き合いやすい場所です。";
}

function buildWhyNowFromSlots(args: {
  mode: BuildParams["mode"];
  need: string | null;
  consultation: ConsultationMeaningSlots;
  primary: Candidate;
}): string {
  if (args.mode === "compat") {
    return "勢いで合う・合わないを決めるほど感覚がぶれやすい今は、";
  }

  if (args.need === "厄除け") {
    return "不安や引っかかりを抱えたまま考えるほど判断が散りやすい今は、";
  }

  if (args.need === "仕事") {
    return "次の一手を急ぐほど優先順位が崩れやすい今は、";
  }

  if (args.need === "転機") {
    return "結論を急ぐほど何を切り替えるかが見えにくくなる今は、";
  }

  if (args.need === "恋愛") {
    return "相手の反応を追うほど自分の受け取り方が揺れやすい今は、";
  }

  if (args.need === "健康") {
    return "整えようとするほど休むことと立て直すことの順番が崩れやすい今は、";
  }

  if (args.need === "学業") {
    return "結果を急ぐほど集中の軸がぶれやすい今は、";
  }

  return buildFallbackWhyNowFromPrimary({
    consultation: args.consultation,
    primary: args.primary,
  });
}

function buildActionRoleFromSlots(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
  consultation: ConsultationMeaningSlots;
  primary: Candidate;
}): string {
  if (args.mode === "compat") {
    return "自分の感覚を整えながら、相性の受け取り方を見直す節目として向き合いやすい場所です。";
  }

  if (args.need === "厄除け") {
    return "気持ちの流れを整えながら、立て直す順番を見直す節目として向き合いやすい場所です。";
  }

  if (args.need === "仕事") {
    return "仕事の流れと判断軸を整え直す節目として向き合いやすい場所です。";
  }

  if (args.need === "転機") {
    return "流れを整えながら、どこを切り替えるかを見直す節目として向き合いやすい場所です。";
  }

  if (args.need === "恋愛") {
    return "気持ちの置き場を整えながら、関係の見方を見直す節目として向き合いやすい場所です。";
  }

  if (args.need === "健康") {
    return "無理を増やさず整える順番を見直す節目として向き合いやすい場所です。";
  }

  if (args.need === "学業") {
    return "集中の軸と取り組み方を整え直す節目として向き合いやすい場所です。";
  }

  if (args.shrine.tone === "strong") {
    return "切り替えや踏み出しの方向へ、気持ちを動かし直す節目として向き合いやすい場所です。";
  }

  if (args.shrine.tone === "quiet") {
    return "気持ちを静かに受け止め直しながら、整える順番を見直す節目として向き合いやすい場所です。";
  }

  if (args.shrine.tone === "tight") {
    return "判断を絞りながら、優先順位を定め直す節目として向き合いやすい場所です。";
  }

  if (args.shrine.tone === "open") {
    return "滞りをほどきながら、巡りや視野を開き直す節目として向き合いやすい場所です。";
  }

  return buildFallbackActionRoleFromPrimary({
    consultation: args.consultation,
    primary: args.primary,
  });
}

function buildDetailHeroMeaningCopy(params: BuildParams, _primary: Candidate): string {
  const consultation = buildConsultationMeaningSlots(params);
  const shrine = buildShrineMeaningSlots(params);
  const need = clean(consultation.needPrimary) || clean(params.needTags?.[0]) || null;

  return buildHeroMeaningFromSlots({
    mode: params.mode,
    need,
    shrine,
  });
}

function getPrimaryNeedBenefitLabel(params: BuildParams): string | null {
  const preferredBenefit = (params.shrineBenefitLabels ?? []).map(clean).find(Boolean);
  if (preferredBenefit) return preferredBenefit;

  const shrineBenefit = clean(params.rec.reason_facts?.shrine_benefit);
  if (shrineBenefit) return shrineBenefit;

  const matchedBenefit = clean(params.rec.reason_facts?.matched_benefits?.[0]);
  if (matchedBenefit) return matchedBenefit;

  return null;
}


function getShrineFeatureLabel(params: BuildParams): string | null {
  const preferredFeature = (params.shrineFeatureLabels ?? []).map(clean).find(Boolean);
  if (preferredFeature) return preferredFeature;

  const feature = clean(params.rec.reason_facts?.shrine_feature);
  if (feature) return feature;

  const visitFit = clean(params.rec.reason_facts?.visit_fit);
  if (visitFit) return visitFit;

  return null;
}

function buildMeaningBenefitPhrase(benefit: string | null): string | null {
  const value = clean(benefit);
  if (!value) return null;

  if (value.includes("厄除け")) return "不安や引っかかりをほどきながら整え直す流れ";
  if (value.includes("開運")) return "流れを切り替え整え直す流れ";
  if (value.includes("仕事")) return "仕事の流れと判断軸を立て直す流れ";
  if (value.includes("金運")) return "止まった巡りを立て直す流れ";
  if (value.includes("交通安全")) return "移動や進む向きを整え直す流れ";
  if (value.includes("航海安全")) return "進む流れを安定して通し直す流れ";
  if (value.includes("家内安全")) return "暮らしの流れを落ち着かせ整え直す流れ";
  if (value.includes("健康")) return "心身の巡りを整え直す流れ";
  if (value.includes("恋愛")) return "関係性の受け取り方を整える流れ";
  if (value.includes("縁結び")) return "関係の結び目を整え直す流れ";
  if (value.includes("学業")) return "集中の軸を整え直す流れ";
  if (value.includes("合格")) return "目標への焦点を定め直す流れ";
  if (value.includes("勝運")) return "背中を押して前へ進みやすくする流れ";

  // 未知ラベルは null（raw 文字列を ③ narrative に混入させない）
  return null;
}

function buildMeaningFeaturePhrase(feature: string | null): string | null {
  const value = clean(feature);
  if (!value) return null;

  if (value.includes("切り替え") || value.includes("踏み出し")) {
    return "流れを切り替え次の一歩へ動き直す足場";
  }

  if (value.includes("落ち着") || value.includes("静か") || value.includes("受け止め")) {
    return "気持ちを静かに受け止め整え直す足場";
  }

  if (value.includes("集中") || value.includes("判断") || value.includes("絞")) {
    return "判断と集中の軸を定め直す足場";
  }

  if (value.includes("巡り") || value.includes("視野") || value.includes("開")) {
    return "巡りや視野を開き直す足場";
  }

  // 未知ラベルは null
  return null;
}

function buildNeedWishBase(need: string | null, mode?: BuildParams["mode"]): string {
  if (mode === "compat") return "今の自分に無理なく向き合いたい願い";

  if (need === "厄除け") return "不安や引っかかりをほどき、気持ちを整え直したい願い";
  if (need === "仕事") return "仕事の流れや優先順位を整え直したい願い";
  if (need === "金運") return "止まった巡りを整え、立て直しの軸を作りたい願い";
  if (need === "転機") return "切り替えや節目を整え、次の見方を作りたい願い";
  if (need === "恋愛") return "関係性の受け取り方を整え、気持ちの置き場を作りたい願い";
  if (need === "健康") return "心身の消耗を増やさず、整える順番を取り戻したい願い";
  if (need === "学業") return "集中を整え、学びへの向き合い方を立て直したい願い";

  return "今の流れを整え直したい願い";
}

function buildNeedSupportQualifier(args: { benefit: string | null; feature: string | null }): string {
  const benefitPhrase = buildMeaningBenefitPhrase(args.benefit);
  const featurePhrase = buildMeaningFeaturePhrase(args.feature);

  if (benefitPhrase && featurePhrase) return `${benefitPhrase}や${featurePhrase}を足場に`;
  if (benefitPhrase) return `${benefitPhrase}を足場に`;
  if (featurePhrase) return `${featurePhrase}を足場に`;

  return "";
}

function buildMeaningCore(params: BuildParams, _primary: Candidate): string {
  const consultation = buildConsultationMeaningSlots(params);
  const shrine = buildShrineMeaningSlots(params);
  const need = clean(consultation.needPrimary) || clean(params.needTags?.[0]) || null;
  const benefit = getPrimaryNeedBenefitLabel(params);
  const feature = getShrineFeatureLabel(params);
  const context = buildShrineNarrativeContext(params);

  const hasMappedNarrativeContext = Boolean(
    clean(context.symbol) || clean(context.ritual) || clean(context.pattern),
  );

  const receiver = hasMappedNarrativeContext
    ? buildNeedWishBase(need, params.mode)
    : buildMeaningReceiver({
        need,
        benefit,
        feature,
        mode: params.mode,
      });

  return buildMeaningCoreFromSlots({
    mode: params.mode,
    need,
    shrine,
    receiver,
    context,
  });
}

function buildWhyNow(params: BuildParams, primary: Candidate): string {
  const consultation = buildConsultationMeaningSlots(params);
  const need = clean(consultation.needPrimary) || clean(params.needTags?.[0]) || null;

  return buildWhyNowFromSlots({
    mode: params.mode,
    need,
    consultation,
    primary,
  });
}


function buildActionRole(params: BuildParams, primary: Candidate): string {
  const consultation = buildConsultationMeaningSlots(params);
  const shrine = buildShrineMeaningSlots(params);
  const need = clean(consultation.needPrimary) || clean(params.needTags?.[0]) || null;

  return buildActionRoleFromSlots({
    mode: params.mode,
    need,
    shrine,
    consultation,
    primary,
  });
}

function buildActionMeaning(params: BuildParams, secondary?: Candidate): string | undefined {
  const context = buildShrineNarrativeContext(params);
  const ritual = buildRitualPhrase(context);
  const pattern = buildPatternPhrase(context);

  if (secondary?.key === "distance") {
    return ritual ?? "まず無理なく足を運べること自体が、参拝の入口になります。";
  }

  if (secondary?.key === "popular") {
    return pattern ?? "迷いがある時でも、参拝先として思い描きやすい安定感があります。";
  }

  if (params.rec.fallback_mode && params.rec.fallback_mode !== "none") {
    if (typeof params.rec.distance_m === "number") {
      return ritual ?? "まず無理なく足を運べること自体が、参拝の入口になります。";
    }

    if (typeof params.rec.popular_score === "number") {
      return pattern ?? "迷いがある時でも、参拝先として思い描きやすい安定感があります。";
    }
  }

  return undefined;
}

function buildShrineMeaning(params: BuildParams, primary: Candidate): string {
  const meaningCore = buildMeaningCore(params, primary);
  const whyNow = buildWhyNow(params, primary);
  const actionRole = buildActionRole(params, primary);

  return `${meaningCore}\n\n${whyNow}${actionRole}`;
}

export function buildMeaningNarrative(args: {
  params: BuildParams;
  primary: Candidate;
  secondary?: Candidate;
}): MeaningNarrative {
  return {
    heroMeaningCopy: buildDetailHeroMeaningCopy(args.params, args.primary),
    shrineMeaning: buildShrineMeaning(args.params, args.primary),
    actionMeaning: buildActionMeaning(args.params, args.secondary),
  };
}
