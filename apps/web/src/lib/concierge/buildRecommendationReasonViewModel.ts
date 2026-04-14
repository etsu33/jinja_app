// apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts
import {
  buildMeaningNarrative,
  type MeaningBuildInput,
} from "./buildMeaningNarrative";
/**
 * buildRecommendationReasonViewModel
 *
 * responsibility:
 * - backend から返る reason_facts / breakdown / fallback 情報を受け取り、
 *   frontend 表示向けの推薦理由 view model を組み立てる
 *
 * boundary:
 * - reason_facts は「推薦判断の事実」を表す構造化データであり、
 *   UI 表示用の完成文は含めない
 * - hero / why / interpretation / rank は frontend 側で生成する
 *
 * design note:
 * - backend は推薦の根拠となる evidence を返す
 * - frontend はその evidence を画面用途に応じた説明文へ翻訳する
 * - 一覧 / 詳細 / 1位表示の差分はこの view model 層で吸収する
 */
export type ReasonInputType = "query" | "birthdate" | "fallback";
export type ReasonKey = "need_match" | "text_match" | "element_match" | "sign_match" | "distance" | "popular";

/**
 * UI section mapping (fixed contract)
 *
 * ① 推薦判断
 * - list.primaryPhrase
 * - list.secondaryPhrase
 * - rank.whyTop
 * - rank.differenceFromOthers
 *
 * role:
 * - なぜこの神社が候補に入ったのかを説明する
 * - 推薦判断の主理由 / 補助理由 / 1位理由を返す
 * - 状態診断や行動意味はここに混ぜない
 *
 * ② 状態整理
 * - detail.consultationSummary
 *
 * role:
 * - 今どういう状態なのかを整理する
 * - 判断が散りやすい理由 / 今の優先順位を返す
 * - 神社説明や推薦判断はここに混ぜない
 *
 * ③ 行動意味
 * - detail.shrineMeaning
 *
 * role:
 * - 今この神社をどう置くかを説明する
 * - meaningCore / whyNow / actionRole を使って組み立てる
 * - 推薦判断や神社情報はここに混ぜない
 *
 * ④ 神社情報
 * - Shrine API / shrine detail UI 側で扱う
 *
 * role:
 * - ご利益 / 象徴 / 相性タグ / 基本情報を補助表示する
 * - この view model では責務を持たない
 */
export type RecommendationReasonViewModel = {
  inputType: ReasonInputType;

  hero: {
    topReasonLabel?: string;
    catchCopy: string;
  };

  // ① 推薦判断: 主理由 / 補助理由
  list: {
    primaryPhrase: string;
    summary: string;
    secondaryPhrase?: string;
  };

  // ② 状態整理 + ③ 行動意味
  detail: {
    heroMeaningCopy: string;
    consultationSummary: string;
    shrineMeaning: string;
    actionMeaning?: string;
  };

  // ① 推薦判断: 1位理由 / 他候補との差
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

  /**
   * compatibility:
   * - why は ① 推薦判断の互換フィールド
   * - 呼び出し側を list / rank に寄せ終えたら削除する
   */
  why: {
    summary: string;
    primaryReason: string;
    secondaryReason?: string;
    reasonKeys: {
      primary: ReasonKey;
      secondary?: ReasonKey;
      summary: ReasonKey;
    };
  };
  /**
   * compatibility:
   * - interpretation.consultationSummary は ② 状態整理の互換フィールド
   * - interpretation.shrineMeaning は ③ 行動意味の互換フィールド
   * - 呼び出し側を detail に寄せ終えたら削除する
   */
  interpretation: {
    consultationSummary: string;
    shrineMeaning: string;
    actionMeaning?: string;
  };
};

type BreakdownLike = {
  matched_need_tags?: string[];
  score_need?: number;
  score_element?: number;
  score_popular?: number;
  score_total?: number;
  weights?: {
    element?: number;
    need?: number;
    popular?: number;
  };
};

type ReasonFactsLike = {
  version?: 1;
  primary_axis?: "need" | "benefit" | "feature" | "element" | "distance" | "popularity" | "fallback" | null;
  secondary_axis?: "need" | "benefit" | "feature" | "element" | "distance" | "popularity" | "fallback" | null;
  matched_need_tags?: string[];
  matched_benefits?: string[];
  shrine_feature?: string | null;
  shrine_benefit?: string | null;
  visit_fit?: string | null;
  matched_element?: string | null;
  matched_sign?: string | null;
  distance_label?: string | null;
  popularity_label?: string | null;
  fallback_reason?: string | null;
  confidence?: "high" | "mid" | "low" | null;
};

type RecommendationLike = {
  name?: string | null;
  display_name?: string | null;
  reason?: string | null;
  breakdown?: BreakdownLike | null;
  distance_m?: number | null;
  popular_score?: number | null;
  astro_elements?: string[] | null;
  astro_priority?: number | null;
  fallback_mode?: string | null;
  explanation?: {
    summary?: string | null;
    reasons?: Array<{ text?: string | null }> | null;
  } | null;
  reason_facts?: ReasonFactsLike | null;
};

type BuildParams = {
  rec: RecommendationLike;
  index: number;
  mode?: "need" | "compat" | string | null;
  birthdate?: string | null;
  needTags?: string[];
  shrineBenefitLabels?: string[];
  shrineFeatureLabels?: string[];
};

type Candidate = {
  key: ReasonKey;
  text: string;
};

const ELEMENT_LABELS: Record<string, string> = {
  fire: "火",
  earth: "土",
  air: "風",
  water: "水",
};



function clean(value?: string | null): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function uniq<T>(arr: T[]): T[] {
  return [...new Set(arr)];
}

function formatDistance(distanceM?: number | null): string | null {
  if (typeof distanceM !== "number" || Number.isNaN(distanceM)) return null;
  if (distanceM < 1000) return `${Math.round(distanceM)}m`;
  return `${(distanceM / 1000).toFixed(1)}km`;
}

function resolveInputType(params: BuildParams): ReasonInputType {
  const { rec, mode, birthdate } = params;

  if (rec.fallback_mode === "nearby_unfiltered") return "fallback";
  if (mode === "compat") return "birthdate";
  if (birthdate && !clean(params.needTags?.join(" "))) return "birthdate";
  return "query";
}

function getPrimaryElement(rec: RecommendationLike): string | null {
  const raw = rec.astro_elements?.[0];
  if (!raw) return null;
  return ELEMENT_LABELS[String(raw).toLowerCase()] ?? String(raw);
}



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

  return normalized;
}

function buildShrineAxisLabel(args: { benefit?: string | null; feature?: string | null }): string | null {
  const benefit = clean(args.benefit);
  const feature = clean(args.feature);

  if (benefit) return benefit;
  if (feature) return feature;
  return null;
}

function buildIntersectionPrimaryText(args: {
  need?: string | null;
  benefit?: string | null;
  feature?: string | null;
}): string | null {
  const needLabel = buildNeedThemeLabel(args.need);
  const shrineLabel = buildShrineAxisLabel({ benefit: args.benefit, feature: args.feature });

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

/**
 * ① 推薦判断
 * - query ベースの主理由 / 補助理由候補を組み立てる
 * - 「なぜこの神社が候補に入ったのか」を説明する
 * - 状態整理や行動意味はここで作らない
 */
function buildQueryCandidates(rec: RecommendationLike, needTags?: string[]): Candidate[] {
  const matched = uniq((rec.breakdown?.matched_need_tags ?? []).map(clean).filter(Boolean));
  const needs = uniq((needTags ?? []).map(clean).filter(Boolean));
  const mainNeed = matched[0] ?? needs[0];

  const out: Candidate[] = [];

  if (mainNeed) {
    out.push({
      key: "need_match",
      text: `今回の相談の中心にある「${mainNeed}」のテーマと最も強く重なるため、この神社が候補に入っています。`,
    });
  }

  if (matched.length >= 2) {
    out.push({
      key: "text_match",
      text: `加えて、「${matched[1]}」の観点でも補助的な重なりが見られます。`,
    });
  } else if (matched.length === 1) {
    out.push({
      key: "text_match",
      text: "相談内容の流れに沿って受け取りやすい点も、この神社が候補に入った理由です。",
    });
  }

  if (typeof rec.astro_priority === "number" && rec.astro_priority > 0) {
    out.push({
      key: "sign_match",
      text: "気質とのなじみも補助的に見られます。",
    });
  }

  const distance = formatDistance(rec.distance_m);
  if (distance) {
    out.push({
      key: "distance",
      text: `${distance}圏内で実際に動きやすい条件もあります。`,
    });
  }

  if (typeof rec.popular_score === "number") {
    out.push({
      key: "popular",
      text: "参拝先として選びやすい安定感もあります。",
    });
  }

  return out;
}

/**
 * ① 推薦判断
 * - birthdate / compat ベースの主理由 / 補助理由候補を組み立てる
 * - 「なぜこの神社が候補に入ったのか」を相性軸で説明する
 */
function buildBirthdateCandidates(rec: RecommendationLike): Candidate[] {
  const out: Candidate[] = [];
  const element = getPrimaryElement(rec);

  if (element) {
    out.push({
      key: "element_match",
      text: `生年月日から見た「${element}」の要素との相性が強く重なるため、この神社が候補に入っています。`,
    });
  }

  if (typeof rec.astro_priority === "number" && rec.astro_priority > 0) {
    out.push({
      key: "sign_match",
      text: "気質とのなじみも補助的に見られます。",
    });
  }

  const distance = formatDistance(rec.distance_m);
  if (distance) {
    out.push({
      key: "distance",
      text: `${distance}圏内で、落ち着いて向かいやすい条件もあります。`,
    });
  }

  if (typeof rec.popular_score === "number") {
    out.push({
      key: "popular",
      text: "参拝先として選びやすい安定感もあります。",
    });
  }

  return out;
}

function buildFallbackCandidates(rec: RecommendationLike): Candidate[] {
  const out: Candidate[] = [];
  const distance = formatDistance(rec.distance_m);
  const hasPopular = typeof rec.popular_score === "number";

  if (distance) {
    out.push({
      key: "distance",
      text: "今回はまず動きやすさを優先して、この神社が候補に入っています。",
    });
    if (hasPopular) {
      out.push({
        key: "popular",
        text: "その中でも、選びやすい安定感があります。",
      });
    }
    return out;
  }

  if (hasPopular) {
    out.push({
      key: "popular",
      text: "今回はまず選びやすさを優先して、この神社が候補に入っています。",
    });
    out.push({
      key: "distance",
      text: "無理なく足を運びやすい条件もあります。",
    });
    return out;
  }

  out.push({
    key: "distance",
    text: "今回はまず動きやすさを優先して、この神社が候補に入っています。",
  });
  return out;
}

/**
 * ① 推薦判断
 * - backend reason_facts を UI 用の推薦判断文へ翻訳する
 * - evidence を推薦理由へ変換する層
 * - 状態整理や行動意味は扱わない
 */
function buildFactsCandidates(rec: RecommendationLike): Candidate[] {
  const f = rec.reason_facts;
  if (!f) return [];

  const out: Candidate[] = [];

  const matchedNeed = clean(f.matched_need_tags?.[0]);
  const secondaryNeed = clean(f.matched_need_tags?.[1]);
  const benefit = clean(f.shrine_benefit);
  const feature = clean(f.shrine_feature);
  const visitFit = clean(f.visit_fit);
  const fallbackReason = clean(f.fallback_reason);
  const element = clean(f.matched_element);
  const distanceLabel = clean(f.distance_label);
  const popularityLabel = clean(f.popularity_label);
  const primaryIntersectionText = buildIntersectionPrimaryText({ need: matchedNeed, benefit, feature });

  switch (f.primary_axis) {
    case "need":
      if (primaryIntersectionText) {
        out.push({
          key: "need_match",
          text: primaryIntersectionText,
        });
      } else if (matchedNeed) {
        out.push({
          key: "need_match",
          text: `今回の相談の中心にある「${matchedNeed}」と最も強く重なるため、この神社が候補に入っています。`,
        });
      }
      break;
    case "benefit":
      if (primaryIntersectionText) {
        out.push({
          key: "need_match",
          text: primaryIntersectionText,
        });
      } else if (benefit) {
        out.push({
          key: "need_match",
          text: `${benefit}の方向が今回の相談と強く重なるため、この神社が候補に入っています。`,
        });
      }
      break;
    case "feature":
      if (primaryIntersectionText) {
        out.push({
          key: "need_match",
          text: primaryIntersectionText,
        });
      } else if (feature) {
        out.push({
          key: "text_match",
          text: `${feature}の性質が、今の相談の流れと重なって見られます。`,
        });
      }
      break;
    case "element":
      if (element) {
        out.push({
          key: "element_match",
          text: `${element}の相性軸で強い重なりがあるため、この神社が候補に入っています。`,
        });
      }
      break;
    case "distance":
      out.push({
        key: "distance",
        text: distanceLabel ? `${distanceLabel}圏で実際に動きやすい条件があります。` : "無理なく足を運びやすい条件があります。",
      });
      break;
    case "popularity":
      out.push({
        key: "popular",
        text: popularityLabel || "参拝先として選びやすい安定感があります。",
      });
      break;
    case "fallback":
      out.push({
        key: "distance",
        text: fallbackReason || "今回はまず選びやすさを優先して、この神社が候補に入っています。",
      });
      break;
  }

  if (visitFit) out.push({ key: "text_match", text: `${visitFit}点でも補助的な重なりが見られます。` });
  if (feature && f.primary_axis !== "feature") out.push({ key: "text_match", text: `${feature}の性質も補助的に重なって見られます。` });
  if (benefit && f.primary_axis !== "benefit" && clean(primaryIntersectionText) !== clean(`${benefit}の方向とも補助的な重なりが見られます。`)) {
    out.push({ key: "need_match", text: `${benefit}の方向とも補助的な重なりが見られます。` });
  }
  if (secondaryNeed) out.push({ key: "text_match", text: `加えて、「${secondaryNeed}」の観点でも補助的な重なりが見られます。` });
  if (element && f.primary_axis !== "element") {
    out.push({ key: "sign_match", text: `${element}の相性傾向も補助的に見られます。` });
  }
  if (popularityLabel && f.primary_axis !== "popularity") out.push({ key: "popular", text: popularityLabel });

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
  inputType: ReasonInputType,
  primary: Candidate,
  secondary?: Candidate,
): { key: ReasonKey; text: string } {
  const blocked = new Set([clean(primary.text), clean(secondary?.text)]);

  const byType: Record<ReasonInputType, Array<{ key: ReasonKey; text: string }>> = {
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

function buildTopReasonLabel(inputType: ReasonInputType, primaryKey: ReasonKey, index: number) {
  if (index !== 0) return undefined;
  if (inputType === "query") return primaryKey === "need_match" ? "相談との一致が強い" : "内容との一致が強い";
  if (inputType === "birthdate") return "相性との一致が強い";
  if (inputType === "fallback") {
    if (primaryKey === "distance") return "まず動きやすい";
    if (primaryKey === "popular") return "まず選びやすい";
    return "おすすめ";
  }
  return undefined;
}

function buildHeroCatchCopy(params: BuildParams, primary: Candidate): string {
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


function buildStateStuckText(params: BuildParams, primary: Candidate): string {
  const need = clean(params.needTags?.[0]);

  if (params.mode === "compat") {
    return "今は勢いで答えを出すほど感覚がぶれやすく、合う・合わないを静かに見極めたい状態です。";
  }

  if (need === "厄除け") {
    return "不安や引っかかりが続く時は、考えるほど判断が散って、気持ちの消耗が先に進みやすくなります。";
  }

  if (need === "仕事") {
    return "仕事のことを考え続けている時は、動き方より先に優先順位が崩れて、判断が散りやすくなります。";
  }

  if (need === "金運") {
    return "流れを変えたい時ほど、焦って手を打つほど空回りしやすく、立て直しの軸がぼやけやすくなります。";
  }

  if (need === "転機") {
    return "切り替えたい気持ちが強い時ほど、急いで結論を出そうとして判断が粗くなり、流れの見極めが雑になりやすくなります。";
  }

  if (need === "恋愛") {
    return "関係のことを気にし続けている時は、相手より先に自分の受け取り方が揺れて、気持ちの置き場が散りやすくなります。";
  }

  if (need === "健康") {
    return "心身の不調が気になる時は、整えたい気持ちが先走るほど、休むことと立て直すことの順番が崩れやすくなります。";
  }

  if (need === "学業") {
    return "結果を意識し続けている時は、やるべきことより不安の処理が先に膨らみ、集中の軸がぶれやすくなります。";
  }

  if (primary.key === "distance") {
    return "今は遠くの正解を探すほど動けなくなりやすく、まず無理なく足を運べる選択肢から見た方が流れを切り替えやすい状態です。";
  }

  if (primary.key === "element_match" || primary.key === "sign_match") {
    return "今は強い刺激よりも、気質に無理なく馴染む場所の方が受け取りやすく、考えすぎをほどきやすい状態です。";
  }

  return "今は答えを急ぐほど判断が散りやすく、まず状態や優先順位を整えながら見直した方が受け取りやすい状態です。";
}

function buildStatePriorityText(params: BuildParams, primary: Candidate): string {
  const need = clean(params.needTags?.[0]);

  if (params.mode === "compat") {
    return "今は結論を急ぐより、相性として無理がないか、落ち着いて受け取れる場所かを先に整理するのが合っています。";
  }

  if (need === "厄除け") {
    return "今は解決策を増やすより先に、気持ちを落ち着かせて、何を立て直したいのかを整理できる場を優先するのが合っています。";
  }

  if (need === "仕事") {
    return "今は次の一手を増やすより先に、何を進めて何を止めるかを整理できる場を優先するのが合っています。";
  }

  if (need === "金運") {
    return "今は一発で変えることより先に、止まった流れを整え直して、立て直しの軸を作れる場を優先するのが合っています。";
  }

  if (need === "転機") {
    return "今は答えを急いで決めるより先に、どこを切り替えて何を残すかを整理できる場を優先するのが合っています。";
  }

  if (need === "恋愛") {
    return "今は相手の反応を追うより先に、自分の気持ちの置き場を整えて、関係をどう見たいかを整理できる場を優先するのが合っています。";
  }

  if (need === "健康") {
    return "今は無理に立て直そうとするより先に、消耗を増やさず整える順番を取り戻せる場を優先するのが合っています。";
  }

  if (need === "学業") {
    return "今は量を増やすより先に、集中を削っている要因を静かに整理できる場を優先するのが合っています。";
  }

  if (primary.key === "distance") {
    return "今は理想の候補を探し切るより先に、実際に動ける場所から流れを切り替えることを優先するのが合っています。";
  }

  if (primary.key === "element_match" || primary.key === "sign_match") {
    return "今は強く変わることより先に、無理なく受け取れて気持ちを整えやすい場所を優先するのが合っています。";
  }

  return "今は答えを出すことより先に、状態を整えながら優先順位を見直せる場を優先するのが合っています。";
}


function buildMeaningInputFromParams(params: BuildParams, primary: Candidate, secondary?: Candidate): {
  input: MeaningBuildInput;
  primary: { key: Candidate["key"] };
  secondary?: { key: Candidate["key"] };
} {
  return {
    input: {
      shrineName: clean(params.rec.display_name) || clean(params.rec.name) || null,
      mode: params.mode ?? null,
      needTag: clean(params.needTags?.[0]) || null,
      benefitLabels: (params.shrineBenefitLabels ?? []).map(clean).filter(Boolean),
      featureLabels: (params.shrineFeatureLabels ?? []).map(clean).filter(Boolean),
      reasonFacts: params.rec.reason_facts ?? null,
      fallbackMode: params.rec.fallback_mode ?? null,
      distanceM: params.rec.distance_m ?? null,
      popularScore: params.rec.popular_score ?? null,
    },
    primary: { key: primary.key },
    secondary: secondary ? { key: secondary.key } : undefined,
  };
}


/**
 * ② 状態整理
 * - buildStateStuckText + buildStatePriorityText を束ねて現在地を返す
 * - 今どういう状態か / 今何を優先すべきかを説明する
 */
function buildConsultationSummary(params: BuildParams, primary: Candidate, _secondary?: Candidate): string {
  const stuck = buildStateStuckText(params, primary);
  const priority = buildStatePriorityText(params, primary);

  return `${stuck} ${priority}`;
}


/**
 * ① 推薦判断
 * - 1位理由 / 他候補との差を返す
 * - ranking の説明責務を持つ
 * - 行動意味や神社情報はここに混ぜない
 */
function buildRankReason(
  params: BuildParams,
  primary: Candidate,
  _secondary?: Candidate,
): { whyTop?: string; differenceFromOthers?: string } {
  if (params.index !== 0) {
    return {};
  }

  if (primary.key === "need_match") {
    return {
      whyTop: "今回の候補の中でも、相談内容との一致が最も強く見られる候補です。",
      differenceFromOthers: "他候補よりも、今回いちばん優先したいテーマにまっすぐ重なりやすい位置づけです。",
    };
  }

  if (primary.key === "element_match" || primary.key === "sign_match") {
    return {
      whyTop: "今回の候補の中でも、生年月日との相性の重なりが最も強く見られる候補です。",
      differenceFromOthers: "他候補よりも、気質に無理なく馴染みやすい点が上位理由になっています。",
    };
  }

  if (primary.key === "distance") {
    return {
      whyTop: "今回の候補の中でも、まず実際に動きやすい条件が強い候補です。",
      differenceFromOthers: "他候補よりも、行けること自体が負担になりにくい点を優先しています。",
    };
  }

  if (primary.key === "popular") {
    return {
      whyTop: "今回の候補の中でも、選びやすさの安定感が強い候補です。",
      differenceFromOthers: "他候補よりも、迷いがある段階でも選択しやすい点を優先しています。",
    };
  }

  return {
    whyTop: "今回の候補の中でも、今の相談との重なりが最も強く見られる候補です。",
    differenceFromOthers: "他候補よりも、今回の相談を整理する軸に沿って受け取りやすい位置づけです。",
  };
}

/**
 * section contract summary
 *
 * ① 推薦判断
 * - list.primaryPhrase
 * - list.secondaryPhrase
 * - rank.whyTop
 * - rank.differenceFromOthers
 *
 * ② 状態整理
 * - detail.consultationSummary
 *
 * ③ 行動意味
 * - detail.shrineMeaning
 *
 * ④ 神社情報
 * - Shrine API / shrine detail UI 側
 *
 * note:
 * - この関数は ①〜③ の view model を組み立てる
 * - ④ 神社情報はこの関数の責務に含めない
 */
export function buildRecommendationReasonViewModel(params: BuildParams): RecommendationReasonViewModel {
  const inputType = resolveInputType(params);
  const factsCandidates = buildFactsCandidates(params.rec);

  const raw =
    factsCandidates.length > 0
      ? factsCandidates
      : inputType === "query"
        ? buildQueryCandidates(params.rec, params.needTags)
        : inputType === "birthdate"
          ? buildBirthdateCandidates(params.rec)
          : buildFallbackCandidates(params.rec);

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

  const meaningArgs = buildMeaningInputFromParams(params, primary, secondary);
  const meaning = buildMeaningNarrative(meaningArgs);

  return {
    inputType,
    hero: {
      topReasonLabel: buildTopReasonLabel(inputType, primary.key, params.index),
      catchCopy: buildHeroCatchCopy(params, primary),
    },
    list: {
      primaryPhrase: primary.text,
      summary: summary.text,
      secondaryPhrase: secondary?.text,
    },
    detail: {
      heroMeaningCopy: meaning.heroMeaningCopy,
      consultationSummary: buildConsultationSummary(params, primary, secondary),
      shrineMeaning: meaning.shrineMeaning,
      actionMeaning: meaning.actionMeaning,
    },
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
    interpretation: {
      consultationSummary: buildConsultationSummary(params, primary, secondary),
      shrineMeaning: meaning.shrineMeaning,
      actionMeaning: meaning.actionMeaning,
    },
    rank,
  };
}
