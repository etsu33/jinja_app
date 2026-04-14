/**
 * buildMeaningNarrative
 *
 * responsibility:
 * ③ 行動意味を生成する
 *   - heroMeaningCopy: detail ヘッダー用短コピー
 *   - shrineMeaning: 「今ここに参拝を置く意味」2文構造
 *   - actionMeaning: 距離・人気など補助要因がある場合の付加文
 *
 * boundary:
 * - 推薦判断（①）は扱わない
 * - 状態整理（②）は扱わない
 * - 神社補足情報（④）は扱わない
 *
 * design note (③ narrative):
 * - 文頭 「この神社は、${buildNeedWishBase()}」固定
 * - mapped context がある場合は benefit / feature を完全に無視
 * - raw benefit label は外部に漏らさない（未知ラベルは null を返す）
 */

// ---------------------------------------------------------------------------
// Input types (self-contained; caller maps from BuildParams)
// ---------------------------------------------------------------------------

export type MeaningBuildInput = {
  shrineName: string | null;
  mode: "need" | "compat" | string | null | undefined;
  needTag: string | null;
  benefitLabels: string[];
  featureLabels: string[];
  reasonFacts: {
    shrine_benefit?: string | null;
    shrine_feature?: string | null;
    visit_fit?: string | null;
    matched_benefits?: string[] | null;
  } | null;
  fallbackMode?: string | null;
  distanceM?: number | null;
  popularScore?: number | null;
};

export type MeaningCandidateKey =
  | "need_match"
  | "text_match"
  | "element_match"
  | "sign_match"
  | "distance"
  | "popular";

export type MeaningCandidate = {
  key: MeaningCandidateKey;
};

export type MeaningNarrative = {
  heroMeaningCopy: string;
  shrineMeaning: string;
  actionMeaning?: string;
};

// ---------------------------------------------------------------------------
// Shrine narrative context
// ---------------------------------------------------------------------------

type ShrineNarrativeContext = {
  symbol?: string;
  place?: "mountain" | "forest" | "water" | "city";
  ritual?: string;
  pattern?: string;
};

// Map: 神社名 → narrative context（name resolver の唯一のデータソース）
const SHRINE_NARRATIVE_CONTEXT_MAP: Record<string, ShrineNarrativeContext> = {
  三峯神社: {
    place: "mountain",
    symbol: "古くから節目や鍛錬の場として向き合われてきた場所でもあり",
    ritual: "高低差や道のりを進むこと自体が、気持ちを切り替える参拝体験につながります。",
    pattern: "人生の転機や、気持ちを切り替えたい時に選ばれやすい神社です。",
  },
  乃木神社: {
    place: "city",
    symbol: "日常の延長で姿勢を整え、目標へ向き直る節目として受け取られやすい神社でもあり",
    ritual: "街の中でも立ち寄りやすく、気持ちと集中を整え直す入口にしやすい参拝です。",
    pattern: "学業や仕事の節目で、姿勢を整えたい時に選ばれやすい神社です。",
  },
  住吉大社: {
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
  亀戸天神社: {
    place: "water",
    symbol: "学びや願掛けの節目として重ねて受け取られてきた場所でもあり",
    ritual: "水辺の気配を感じながら、焦りをほどいて目標へ向き直しやすい参拝です。",
    pattern: "受験や学びの節目で、集中を整えたい時に選ばれやすい神社です。",
  },
};

// ---------------------------------------------------------------------------
// Task 2: shrineNameCandidates uniq 化
// ---------------------------------------------------------------------------

function cleanStr(value?: string | null): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function buildShrineNameCandidates(shrineName: string | null): string[] {
  const raw = [shrineName].map(cleanStr).filter(Boolean);
  return [...new Set(raw)];
}

// ---------------------------------------------------------------------------
// Task 4: context resolver 分離（name 解析と text 解析を独立させる）
// ---------------------------------------------------------------------------

/**
 * name resolver: SHRINE_NARRATIVE_CONTEXT_MAP の名前照合のみ担当。
 * benefit / feature テキストは参照しない。
 */
function resolveContextByName(shrineNameCandidates: string[]): ShrineNarrativeContext | null {
  for (const candidate of shrineNameCandidates) {
    const entry = Object.entries(SHRINE_NARRATIVE_CONTEXT_MAP).find(([name]) =>
      candidate.includes(name),
    );
    if (entry) return entry[1];
  }
  return null;
}

/**
 * text resolver: featureTexts のみを参照して place を推定する。
 * benefit label は「御利益の説明文字列」になるため渡さない。
 */
function resolveContextByText(featureTexts: string[]): ShrineNarrativeContext {
  const joined = featureTexts.join(" ").toLowerCase();

  let place: ShrineNarrativeContext["place"];

  if (
    joined.includes("山") ||
    joined.includes("峰") ||
    joined.includes("岳")
  ) {
    place = "mountain";
  } else if (
    joined.includes("森") ||
    joined.includes("杜") ||
    joined.includes("林")
  ) {
    place = "forest";
  } else if (
    joined.includes("水") ||
    joined.includes("川") ||
    joined.includes("滝") ||
    joined.includes("海") ||
    joined.includes("池")
  ) {
    place = "water";
  } else if (
    joined.includes("街") ||
    joined.includes("市") ||
    joined.includes("駅")
  ) {
    place = "city";
  }

  if (place === "mountain") {
    return {
      place,
      symbol: "古くから節目や鍛錬の場として向き合われてきた場所でもあり",
      ritual: "高低差や道のりを進むこと自体が、気持ちを切り替える参拝体験につながります。",
      pattern: "人生の転機や、気持ちを切り替えたい時に選ばれやすい神社です。",
    };
  }
  if (place === "forest") {
    return {
      place,
      symbol: "静けさの中で気持ちを整える場として受け取られてきた場所でもあり",
      ritual: "木々に包まれた参道を進みながら、落ち着いて気持ちを整えやすい参拝です。",
      pattern: "落ち着いて考えを整えたい時に選ばれやすい神社です。",
    };
  }
  if (place === "water") {
    return {
      place,
      symbol: "流れや浄化の象徴と重ねて受け取られやすい場所でもあり",
      ritual: "水辺や流れを感じながら、滞りをほどくように参拝しやすい神社です。",
      pattern: "切り替えや立て直しの節目に選ばれやすい神社です。",
    };
  }
  if (place === "city") {
    return {
      place,
      symbol: "日常の延長で節目を作りやすい場所として親しまれてきた神社でもあり",
      ritual: "日常の動線の中でも立ち寄りやすく、今の流れを切り替える入口にしやすい参拝です。",
      pattern: "忙しい時期でも節目を作りたい人に選ばれやすい神社です。",
    };
  }

  return {};
}

/**
 * buildShrineNarrativeContext: name 解析を優先し、不一致なら text 解析にフォールバック。
 * mapped context がある場合は benefit / feature を完全に無視する。
 */
function buildShrineNarrativeContext(args: {
  shrineName: string | null;
  featureLabels: string[];
}): ShrineNarrativeContext {
  const candidates = buildShrineNameCandidates(args.shrineName);
  const fromName = resolveContextByName(candidates);
  if (fromName) return fromName;

  return resolveContextByText(args.featureLabels);
}

function hasMappedContext(ctx: ShrineNarrativeContext): boolean {
  return Boolean(ctx.symbol || ctx.ritual || ctx.pattern);
}

// ---------------------------------------------------------------------------
// Task 3: benefit / feature phrase 変換（raw label を外部に漏らさない）
// ---------------------------------------------------------------------------

/**
 * 既知の benefit label → narrative phrase に変換する。
 * 未知のラベルは null を返す（raw label を素通りさせない）。
 */
function buildMeaningBenefitPhrase(benefit: string | null): string | null {
  const value = cleanStr(benefit);
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

/**
 * 既知の feature label → narrative phrase に変換する。
 * 未知のラベルは null を返す。
 */
function buildMeaningFeaturePhrase(feature: string | null): string | null {
  const value = cleanStr(feature);
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

// ---------------------------------------------------------------------------
// Wish base（文頭固定: 「この神社は、${buildNeedWishBase()}」）
// ---------------------------------------------------------------------------

function buildNeedWishBase(need: string | null, mode?: string | null): string {
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

function buildNeedSupportQualifier(args: {
  benefit: string | null;
  feature: string | null;
}): string {
  const benefitPhrase = buildMeaningBenefitPhrase(args.benefit);
  const featurePhrase = buildMeaningFeaturePhrase(args.feature);

  if (benefitPhrase && featurePhrase) return `${benefitPhrase}や${featurePhrase}を足場に`;
  if (benefitPhrase) return `${benefitPhrase}を足場に`;
  if (featurePhrase) return `${featurePhrase}を足場に`;

  return "";
}

function buildMeaningReceiver(args: {
  need: string | null;
  benefit: string | null;
  feature: string | null;
  mode?: string | null;
}): string {
  const baseWish = buildNeedWishBase(args.need, args.mode);
  const qualifier = buildNeedSupportQualifier({ benefit: args.benefit, feature: args.feature });

  if (!qualifier) return baseWish;
  return `${qualifier}${baseWish}`;
}

// ---------------------------------------------------------------------------
// Hero meaning copy
// ---------------------------------------------------------------------------

function buildHeroMeaningCopy(args: {
  mode: string | null | undefined;
  need: string | null;
  context: ShrineNarrativeContext;
}): string {
  if (args.mode === "compat") {
    return "相性の無理が少なく、落ち着いて受け取りやすい神社";
  }

  const { need } = args;
  if (need === "厄除け") return "気持ちを立て直し、受け取り方を整え直す神社";
  if (need === "仕事") return "仕事の流れと判断軸を整え直す神社";
  if (need === "金運") return "止まった流れを整え、立て直しの軸を作る神社";
  if (need === "転機") return "切り替えの流れを整え、次の見方を作る神社";
  if (need === "恋愛") return "関係性の受け取り方を整え、気持ちの置き場を作る神社";
  if (need === "健康") return "心身を整え、回復の順番を取り戻す神社";
  if (need === "学業") return "集中を整え、目標への向き合い方を立て直す神社";

  // context tone で補う
  if (args.context.place === "mountain") return "流れを切り替え、次の一歩を動かしやすい神社";
  if (args.context.place === "forest") return "落ち着いて受け止め、静かに整え直しやすい神社";
  if (args.context.place === "water") return "滞りをほどき、巡りを整え直しやすい神社";
  if (args.context.place === "city") return "日常の中で節目を作り、流れを切り替えやすい神社";

  return "今の流れを整え、次の見方を作る神社";
}

// ---------------------------------------------------------------------------
// ③ meaningCore: 「この神社は、${wish}…節目として置きやすい場所です。」
// ---------------------------------------------------------------------------

function buildMeaningCore(args: {
  mode: string | null | undefined;
  need: string | null;
  benefit: string | null;
  feature: string | null;
  context: ShrineNarrativeContext;
}): string {
  const mapped = hasMappedContext(args.context);

  // mapped context がある場合 → benefit / feature を完全に無視し wish base のみ使う
  const receiver = mapped
    ? buildNeedWishBase(args.need, args.mode)
    : buildMeaningReceiver({
        need: args.need,
        benefit: args.benefit,
        feature: args.feature,
        mode: args.mode,
      });

  const symbolPhrase = args.context.symbol ? `${args.context.symbol} ` : "";
  const placeMap: Record<string, string> = {
    mountain: "山の気配の中で",
    forest: "森に包まれた空気の中で",
    water: "水の流れを感じながら",
    city: "街の中でも立ち寄りやすく",
  };
  const placePart = args.context.place ? `${placeMap[args.context.place] ?? ""} ` : "";
  const intro = [symbolPhrase.trim(), placePart.trim()].filter(Boolean).join(" ");
  const introText = intro ? `${intro} ` : "";

  if (args.mode === "compat") {
    return `この神社は、${introText}${receiver}を落ち着いて受け止め直し、自分にとって無理のない向き合い方を整える節目として置きやすい場所です。`;
  }

  if (args.need === "厄除け") {
    return `この神社は、${introText}${receiver}を抱え直すのではなく、ほどきながら整え直す節目として置きやすい場所です。`;
  }
  if (args.need === "仕事") {
    return `この神社は、${introText}${receiver}を見直し、仕事の流れと判断軸を立て直す節目として置きやすい場所です。`;
  }
  if (args.need === "転機") {
    return `この神社は、${introText}${receiver}を見直し、切り替えの流れを整え直す節目として置きやすい場所です。`;
  }
  if (args.need === "恋愛") {
    return `この神社は、${introText}${receiver}を見つめ直し、関係性の受け取り方を整える節目として置きやすい場所です。`;
  }
  if (args.need === "健康") {
    return `この神社は、${introText}${receiver}を急がず見直し、心身を整え直す順番を取り戻す節目として置きやすい場所です。`;
  }
  if (args.need === "学業") {
    return `この神社は、${introText}${receiver}を見直し、集中の軸と取り組み方を定め直す節目として置きやすい場所です。`;
  }

  return `この神社は、${introText}${receiver}を見直し、今の流れを整える節目として置きやすい場所です。`;
}

// ---------------------------------------------------------------------------
// ③ whyNow: 「…今は、」
// ---------------------------------------------------------------------------

function buildWhyNow(args: {
  mode: string | null | undefined;
  need: string | null;
  primaryKey: MeaningCandidateKey;
}): string {
  if (args.mode === "compat") {
    return "勢いで合う・合わないを決めるほど感覚がぶれやすい今は、";
  }

  if (args.need === "厄除け") return "不安や引っかかりを抱えたまま考えるほど判断が散りやすい今は、";
  if (args.need === "仕事") return "次の一手を急ぐほど優先順位が崩れやすい今は、";
  if (args.need === "転機") return "結論を急ぐほど何を切り替えるかが見えにくくなる今は、";
  if (args.need === "恋愛") return "相手の反応を追うほど自分の受け取り方が揺れやすい今は、";
  if (args.need === "健康") return "整えようとするほど休むことと立て直すことの順番が崩れやすい今は、";
  if (args.need === "学業") return "結果を急ぐほど集中の軸がぶれやすい今は、";

  if (args.primaryKey === "distance") return "遠くの正解を探すほど動けなくなりやすい今は、";
  if (args.primaryKey === "element_match" || args.primaryKey === "sign_match") {
    return "強い刺激よりも無理なく受け取れる場所の方が整いやすい今は、";
  }

  return "答えを急ぐほど判断が散りやすい今は、";
}

// ---------------------------------------------------------------------------
// ③ actionRole: 「…節目として向き合いやすい場所です。」
// ---------------------------------------------------------------------------

function buildActionRole(args: {
  mode: string | null | undefined;
  need: string | null;
  context: ShrineNarrativeContext;
  primaryKey: MeaningCandidateKey;
}): string {
  if (args.mode === "compat") {
    return "自分の感覚を整えながら、相性の受け取り方を見直す節目として向き合いやすい場所です。";
  }

  if (args.need === "厄除け") return "気持ちの流れを整えながら、立て直す順番を見直す節目として向き合いやすい場所です。";
  if (args.need === "仕事") return "仕事の流れと判断軸を整え直す節目として向き合いやすい場所です。";
  if (args.need === "転機") return "流れを整えながら、どこを切り替えるかを見直す節目として向き合いやすい場所です。";
  if (args.need === "恋愛") return "気持ちの置き場を整えながら、関係の見方を見直す節目として向き合いやすい場所です。";
  if (args.need === "健康") return "無理を増やさず整える順番を見直す節目として向き合いやすい場所です。";
  if (args.need === "学業") return "集中の軸と取り組み方を整え直す節目として向き合いやすい場所です。";

  if (args.context.ritual) return args.context.ritual;

  if (args.primaryKey === "distance") {
    return "まず足を運べる場所から流れを整え直す節目として向き合いやすい場所です。";
  }
  if (args.primaryKey === "element_match" || args.primaryKey === "sign_match") {
    return "無理なく受け取れる場所で、気持ちと判断を整える節目として向き合いやすい場所です。";
  }

  return "気持ちと流れを整えながら、次の見方を見直す節目として向き合いやすい場所です。";
}

// ---------------------------------------------------------------------------
// actionMeaning（補助的付加文）
// ---------------------------------------------------------------------------

function buildActionMeaning(args: {
  secondaryKey?: MeaningCandidateKey;
  context: ShrineNarrativeContext;
  fallbackMode?: string | null;
  distanceM?: number | null;
  popularScore?: number | null;
}): string | undefined {
  if (args.secondaryKey === "distance") {
    return args.context.ritual ?? "まず無理なく足を運べること自体が、参拝の入口になります。";
  }
  if (args.secondaryKey === "popular") {
    return args.context.pattern ?? "迷いがある時でも、参拝先として思い描きやすい安定感があります。";
  }

  if (args.fallbackMode && args.fallbackMode !== "none") {
    if (typeof args.distanceM === "number") {
      return args.context.ritual ?? "まず無理なく足を運べること自体が、参拝の入口になります。";
    }
    if (typeof args.popularScore === "number") {
      return args.context.pattern ?? "迷いがある時でも、参拝先として思い描きやすい安定感があります。";
    }
  }

  return undefined;
}

// ---------------------------------------------------------------------------
// Resolve benefit / feature from input
// ---------------------------------------------------------------------------

function resolveBenefit(input: MeaningBuildInput): string | null {
  const fromLabels = input.benefitLabels.map(cleanStr).find(Boolean) ?? null;
  if (fromLabels) return fromLabels;

  const fromFacts = cleanStr(input.reasonFacts?.shrine_benefit) || null;
  if (fromFacts) return fromFacts;

  const fromMatched = cleanStr(input.reasonFacts?.matched_benefits?.[0]) || null;
  return fromMatched;
}

function resolveFeature(input: MeaningBuildInput): string | null {
  const fromLabels = input.featureLabels.map(cleanStr).find(Boolean) ?? null;
  if (fromLabels) return fromLabels;

  const fromFacts = cleanStr(input.reasonFacts?.shrine_feature) || null;
  if (fromFacts) return fromFacts;

  const visitFit = cleanStr(input.reasonFacts?.visit_fit) || null;
  return visitFit;
}

// ---------------------------------------------------------------------------
// Public export
// ---------------------------------------------------------------------------

export function buildMeaningNarrative(args: {
  input: MeaningBuildInput;
  primary: MeaningCandidate;
  secondary?: MeaningCandidate;
}): MeaningNarrative {
  const { input, primary, secondary } = args;
  const mode = input.mode ?? null;
  const need = cleanStr(input.needTag) || null;
  const benefit = resolveBenefit(input);
  const feature = resolveFeature(input);

  // Context resolution: name 優先、fallback は feature text（benefit は渡さない）
  const context = buildShrineNarrativeContext({
    shrineName: input.shrineName,
    featureLabels: input.featureLabels,
  });

  const heroMeaningCopy = buildHeroMeaningCopy({ mode, need, context });

  const meaningCore = buildMeaningCore({ mode, need, benefit, feature, context });
  const whyNow = buildWhyNow({ mode, need, primaryKey: primary.key });
  const actionRole = buildActionRole({ mode, need, context, primaryKey: primary.key });
  const shrineMeaning = `${meaningCore}\n\n${whyNow}${actionRole}`;

  const actionMeaning = buildActionMeaning({
    secondaryKey: secondary?.key,
    context,
    fallbackMode: input.fallbackMode,
    distanceM: input.distanceM,
    popularScore: input.popularScore,
  });

  return { heroMeaningCopy, shrineMeaning, actionMeaning };
}
