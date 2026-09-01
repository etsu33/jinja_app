/**
 * buildMeaningNarrative
 *
 * responsibility:
 * ③ 行動意味を生成する
 *   - meaningCore    : 「この神社は、...節目として置きやすい場所です。」
 *   - meaningContext : 「...今は、...節目として向き合いやすい場所です。」
 *   - meaningAction  : 距離・人気など補助要因がある場合の付加文
 *   - actionMeaning  : 「今の自分への問い」として表示する内省文
 *
 * boundary:
 * - 推薦判断（①）は扱わない
 * - 状態整理（②）は扱わない
 * - 神社補足情報（④）は扱わない
 *
 * design note:
 * - コンテキスト解決順: SHRINE_CONTEXT_TABLE(shrine_id直接参照) → place text 推定
 * - name マッチ・text マッチによる文字列推定は使わない
 * - raw benefit / feature label は外部に漏らさない（未知ラベルは null）
 */

import {
  clean,
  buildNeedTagMeaningSlots,
  buildShrineMeaningSlots,
} from "./buildRecommendationReasonViewModel";
import type {
  BuildParams,
  Candidate,
  NeedTagMeaningSlots,
  ShrineMeaningSlots,
} from "./buildRecommendationReasonViewModel";
import { toNeedTagLabel } from "./needTagLabelMap";

// ---------------------------------------------------------------------------
// Output type
// ---------------------------------------------------------------------------

export type MeaningNarrative = {
  heroMeaningCopy: string;
  /** 1文目: 「この神社は、...節目として置きやすい場所です。」 */
  meaningCore: string;
  /** 2文目: 「...今は、...節目として向き合いやすい場所です。」 */
  meaningContext: string;
  /** 補助文: 距離・人気など補足要因がある場合のみ */
  meaningAction?: string;
  /** backward compat: `${meaningCore}\n\n${meaningContext}` */
  shrineMeaning: string;
  /** 「今の自分への問い」カードに表示する内省文 */
  actionMeaning?: string;
};
function buildReflectionQuestion(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
  consultation: NeedTagMeaningSlots;
  primary: Candidate;
  context: ShrineNarrativeContext;
}): string {
  if (args.mode === "compat") {
    return "この神社を前にしたとき、今の自分は何を無理なく受け取り、何を急いで決めようとしているのでしょうか。";
  }

  if (args.need === "厄除け") {
    if (args.shrine.tone === "strong") {
      return "今の自分が本当にほどきたい不安は何で、どこから切り替えれば次の一歩が軽くなるのでしょうか。";
    }
    return "今の自分が抱え直してしまっている不安は何で、まず何を手放すと整いやすくなるのでしょうか。";
  }
  if (args.need === "仕事") {
    return "今の仕事で守りたい軸は何で、逆に手放した方がいい優先順位は何でしょうか。";
  }
  if (args.need === "転機") {
    return "今の自分は何を続け、何を終わらせ、どこから流れを切り替えたいのでしょうか。";
  }
  if (args.need === "恋愛") {
    return "相手の反応ではなく、自分の中で大切にしたい関係の置き方は何でしょうか。";
  }
  if (args.need === "健康") {
    return "今の自分に必要なのは頑張ることか、休むことか、どちらを先に整えることなのでしょうか。";
  }
  if (args.need === "学業") {
    return "結果を急ぐ前に、今の自分が集中を戻すために整えるべき一つの軸は何でしょうか。";
  }

  if (args.shrine.tone === "strong") {
    return "今の自分が切り替えたい流れは何で、そのために最初に動かす一歩は何でしょうか。";
  }
  if (args.shrine.tone === "quiet") {
    return "急いで答えを出す前に、今の自分が静かに受け止め直すべきことは何でしょうか。";
  }
  if (args.shrine.tone === "tight") {
    return "今の自分が広げすぎていることは何で、まず一つに絞るなら何を選ぶのでしょうか。";
  }
  if (args.shrine.tone === "open") {
    return "今の自分が閉じ込めている見方は何で、少し視野を開くなら何から見直せるでしょうか。";
  }

  if (!clean(args.consultation.needPrimary)) {
    if (args.primary.key === "distance") {
      return "遠くの正解を探す前に、今の自分がまず足を運べる場所で確かめたいことは何でしょうか。";
    }
    if (args.primary.key === "element_match" || args.primary.key === "sign_match") {
      return "強い刺激ではなく無理なく受け取れる場所で、今の自分は何を整え直したいのでしょうか。";
    }
  }

  if (args.context.ritual) {
    return "この参拝の中で、今の自分が一度立ち止まって見直したいことは何でしょうか。";
  }

  return "今の自分が整え直したい流れは何で、次に見方を変えるならどこから始めるのでしょうか。";
}



// ---------------------------------------------------------------------------
// SHRINE_CONTEXT_TABLE: shrine_id による直接参照（source of truth）
// ---------------------------------------------------------------------------

type ShrineContextEntry = {
  place: "mountain" | "forest" | "water" | "city";
  symbol: string;
  ritual: string;
  pattern: string;
};

/**
 * キー: API レスポンスの rec.id (shrine_id)
 * 名前マッチや text 推定は不要 — shrine ID が確定しているものを列挙する。
 * 未登録の shrine は place text 推定にフォールバックする。
 *
 * 追加方法: バックエンドで shrine_id を確認して以下に追記する。
 */
const SHRINE_CONTEXT_TABLE: Record<number, ShrineContextEntry> = {
  17: {
    place: "mountain",
    symbol: "古くから節目や鍛錬の場として向き合われてきた場所でもあり",
    ritual: "高低差や道のりを進みながら、切り替えたい流れをいったん引き受け直す参拝につなげやすい場所です。",
    pattern: "人生の転機や、流れを切り替える節目を置きたい時に選ばれやすい神社です。",
  },

  100017: {
    place: "mountain",
    symbol: "古くから節目や鍛錬の場として向き合われてきた場所でもあり",
    ritual: "高低差や道のりを進みながら、切り替えたい流れをいったん引き受け直す参拝につなげやすい場所です。",
    pattern: "人生の転機や、流れを切り替える節目を置きたい時に選ばれやすい神社です。",
  },

  59: {
    place: "city",
    symbol: "姿勢を整え、目標へ向き直る節目として受け取られやすい神社でもあり",
    ritual: "日常の動線の中でも立ち寄りやすく、集中を整え直す参拝につなげやすい場所です。",
    pattern: "学業や仕事の節目で選ばれやすい神社です。",
  },

  3: {
    place: "forest",
    symbol: "静けさの中で受け取り方を整える場として受け止められやすい神社でもあり",
    ritual: "木々に包まれながら、気持ちの置き場や向き合い方を落ち着いて整え直す参拝につなげやすい場所です。",
    pattern: "気持ちを整え直し、受け取り方を静かに見直したい時に選ばれやすい神社です。",
  },

  47: {
    place: "water",
    symbol: "巡りや流れを整える節目として受け取られやすい神社でもあり",
    ritual: "水辺の気配の中で、滞りをほどくように気持ちや流れを整え直す参拝につなげやすい場所です。",
    pattern: "学びや願いの流れを立て直したい時に選ばれやすい神社です。",
  },
};

// ---------------------------------------------------------------------------
// Fallback context: place text 推定（SHRINE_CONTEXT_TABLE 未登録時のみ）
// ---------------------------------------------------------------------------

type ShrineNarrativeContext = Partial<ShrineContextEntry>;

function inferPlaceFromText(text: string): ShrineContextEntry["place"] | undefined {
  const t = text.toLowerCase();

  if (t.includes("山") || t.includes("峰") || t.includes("岳")) return "mountain";
  if (t.includes("森") || t.includes("杜") || t.includes("林")) return "forest";
  if (t.includes("水") || t.includes("川") || t.includes("滝") || t.includes("海") || t.includes("池")) return "water";
  if (t.includes("街") || t.includes("市") || t.includes("駅")) return "city";

  return undefined;
}

function contextFromPlace(place: ShrineContextEntry["place"] | undefined): ShrineNarrativeContext {
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

// ---------------------------------------------------------------------------
// Context resolution
// ---------------------------------------------------------------------------

function resolveShrineContext(params: BuildParams): ShrineNarrativeContext {
  // 1. SHRINE_CONTEXT_TABLE: shrine_id による直接参照（最優先）
  const shrineId = (() => {
    const rawId = params.rec.id;
    if (typeof rawId === "number") return rawId;
    if (typeof rawId === "string") {
      const parsed = Number(rawId);
      return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
  })();
  if (shrineId !== null && shrineId in SHRINE_CONTEXT_TABLE) {
    return SHRINE_CONTEXT_TABLE[shrineId];
  }

  // 2. featureTexts による place 推定（フォールバック）
  //    benefit label は渡さない（御利益名が place 推定に混入しないよう）
  const featureTexts = (params.shrineFeatureLabels ?? []).map(clean).filter(Boolean) as string[];
  const place = inferPlaceFromText(featureTexts.join(" "));
  return contextFromPlace(place);
}

// ---------------------------------------------------------------------------
// Hero meaning copy
// ---------------------------------------------------------------------------

function buildHeroMeaningCopy(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
}): string {
  if (args.mode === "compat") return "相性の無理が少なく、落ち着いて受け取りやすい神社";

  if (args.need === "厄除け") return "気持ちを立て直し、受け取り方を整え直す神社";
  if (args.need === "仕事")   return "仕事の流れと判断軸を整え直す神社";
  if (args.need === "金運")   return "止まった流れを整え、立て直しの軸を作る神社";
  if (args.need === "転機")   return "切り替えの流れを整え、次の見方を作る神社";
  if (args.need === "恋愛")   return "関係性の受け取り方を整え、気持ちの置き場を作る神社";
  if (args.need === "健康")   return "心身を整え、回復の順番を取り戻す神社";
  if (args.need === "学業")   return "集中を整え、目標への向き合い方を立て直す神社";

  if (args.shrine.tone === "strong") return "流れを切り替え、次の一歩を動かしやすい神社";
  if (args.shrine.tone === "quiet")  return "落ち着いて受け止め、静かに整え直しやすい神社";
  if (args.shrine.tone === "tight")  return "判断を絞り、集中を定め直しやすい神社";
  if (args.shrine.tone === "open")   return "巡りを戻し、視野を開き直しやすい神社";

  return "今の流れを整え、次の見方を作る神社";
}


// ---------------------------------------------------------------------------
// meaning-core: 「この神社は、...節目として置きやすい場所です。」
// ---------------------------------------------------------------------------

function buildMeaningCore(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
  context: ShrineNarrativeContext;
}): string {
  const needFact = (() => {
    if (args.mode === "compat") return "生年月日から見た相性を補助線にしながら";
    if (args.need) {
      const label = toNeedTagLabel(args.need);
      if (label) return `「${label}」という相談テーマに対して`;
    }
    return "今の状態を整理する入口として";
  })();

  const shrineFact = (() => {
    const feature = clean(args.shrine.feature);
    if (feature) return `「${feature}」という意味・特徴を持つ場所で`;

    const place = (() => {
      if (args.context.place === "mountain") return "山や高低差の文脈";
      if (args.context.place === "forest") return "森や木々に囲まれた文脈";
      if (args.context.place === "water") return "水辺や流れを感じる文脈";
      if (args.context.place === "city") return "日常の動線から立ち寄りやすい文脈";
      return null;
    })();

    const symbol = clean(args.context.symbol);

    if (symbol && place) return `${symbol}${place}を持つ場所で`;
    if (symbol) return `${symbol}文脈を持つ場所で`;
    if (place) return `${place}を持つ場所で`;

    return "今回の候補の中で相談内容との接点が見られる場所で";
  })();

  const meaning = (() => {
    if (args.mode === "compat") {
      return "相性を決めつけず、自分にとって無理なく受け取れる距離感を確かめる候補として置きやすい場所です。";
    }

    if (args.need === "厄除け") {
      return "不安や引っかかりを抱え込まず、いったん置き直す候補として置きやすい場所です。";
    }
    if (args.need === "仕事") {
      return "仕事の判断軸や優先順位を落ち着いて選び直す候補として置きやすい場所です。";
    }
    if (args.need === "金運") {
      return "お金そのものの結果ではなく、暮らしや働き方の土台を見直す候補として置きやすい場所です。";
    }
    if (args.need === "転機") {
      return "何を残し、何を切り替えるかを確認する候補として置きやすい場所です。";
    }
    if (args.need === "恋愛") {
      return "相手の反応だけでなく、自分の受け取り方や距離感を確認する候補として置きやすい場所です。";
    }
    if (args.need === "健康") {
      return "無理に整えようとせず、心身を立て直す順番を確認する候補として置きやすい場所です。";
    }
    if (args.need === "学業") {
      return "集中の軸や取り組み方を確認する候補として置きやすい場所です。";
    }

    if (args.shrine.tone === "strong") {
      return "次の一歩に向けて気持ちの向きを切り替える候補として置きやすい場所です。";
    }
    if (args.shrine.tone === "quiet") {
      return "判断を急がず、静かに受け止め直す候補として置きやすい場所です。";
    }
    if (args.shrine.tone === "tight") {
      return "広げすぎた考えを絞り、判断軸を確認する候補として置きやすい場所です。";
    }
    if (args.shrine.tone === "open") {
      return "閉じた見方を少し広げる候補として置きやすい場所です。";
    }
    return "今の状態を整理し、次の見方を確認する候補として置きやすい場所です。";
  })();

  return `この神社は、${needFact}、${shrineFact}${meaning}`;
}

// ---------------------------------------------------------------------------
// meaning-context: 「...今は、...節目として向き合いやすい場所です。」
// ---------------------------------------------------------------------------

function buildWhyNow(args: {
  mode: BuildParams["mode"];
  need: string | null;
  consultation: NeedTagMeaningSlots;
  primary: Candidate;
}): string {
  if (args.mode === "compat") return "勢いで合う・合わないを決めるほど感覚がぶれやすい今は、";

  if (args.need === "厄除け") return "不安や引っかかりを抱えたまま考えるほど判断が散りやすい今は、";
  if (args.need === "仕事")   return "次の一手を急ぐほど優先順位が崩れやすい今は、";
  if (args.need === "転機")   return "結論を急ぐほど何を切り替えるかが見えにくくなる今は、";
  if (args.need === "恋愛")   return "相手の反応を追うほど自分の受け取り方が揺れやすい今は、";
  if (args.need === "健康")   return "整えようとするほど休むことと立て直すことの順番が崩れやすい今は、";
  if (args.need === "学業")   return "結果を急ぐほど集中の軸がぶれやすい今は、";

  if (!clean(args.consultation.needPrimary)) {
    if (args.primary.key === "distance")   return "遠くの正解を探すほど動けなくなりやすい今は、";
    if (args.primary.key === "element_match" || args.primary.key === "sign_match") {
      return "強い刺激よりも無理なく受け取れる場所の方が整いやすい今は、";
    }
  }

  return "答えを急ぐほど判断が散りやすい今は、";
}

function buildActionRole(args: {
  mode: BuildParams["mode"];
  need: string | null;
  shrine: ShrineMeaningSlots;
  consultation: NeedTagMeaningSlots;
  primary: Candidate;
  context: ShrineNarrativeContext;
}): string {
  if (args.mode === "compat") return "自分の感覚を整えながら、相性の受け取り方を見直す節目として向き合いやすい場所です。";

  if (args.need === "厄除け") {
    if (args.shrine.tone === "strong") {
      return "不安や引っかかりを抱えたまま抱え込まず、切り替えや踏み出しの方向へ気持ちを動かし直す節目として向き合いやすい場所です。";
    }
    return "気持ちの流れを整えながら、立て直す順番を見直す節目として向き合いやすい場所です。";
  }
  if (args.need === "仕事")   return "仕事の流れと判断軸を整え直す節目として向き合いやすい場所です。";
  if (args.need === "転機")   return "流れを整えながら、どこを切り替えるかを見直す節目として向き合いやすい場所です。";
  if (args.need === "恋愛")   return "気持ちの置き場を整えながら、関係の見方を見直す節目として向き合いやすい場所です。";
  if (args.need === "健康")   return "無理を増やさず整える順番を見直す節目として向き合いやすい場所です。";
  if (args.need === "学業")   return "集中の軸と取り組み方を整え直す節目として向き合いやすい場所です。";

  // tone ベース
  if (args.shrine.tone === "strong") return "切り替えや踏み出しの方向へ、気持ちを動かし直す節目として向き合いやすい場所です。";
  if (args.shrine.tone === "quiet")  return "気持ちを静かに受け止め直しながら、整える順番を見直す節目として向き合いやすい場所です。";
  if (args.shrine.tone === "tight")  return "判断を絞りながら、優先順位を定め直す節目として向き合いやすい場所です。";
  if (args.shrine.tone === "open")   return "滞りをほどきながら、巡りや視野を開き直す節目として向き合いやすい場所です。";

  // context ritual があればそれを使う
  if (args.context.ritual) return args.context.ritual;

  if (!clean(args.consultation.needPrimary)) {
    if (args.primary.key === "distance") return "まず足を運べる場所から流れを整え直す節目として向き合いやすい場所です。";
    if (args.primary.key === "element_match" || args.primary.key === "sign_match") {
      return "無理なく受け取れる場所で、気持ちと判断を整える節目として向き合いやすい場所です。";
    }
  }

  return "気持ちと流れを整えながら、次の見方を見直す節目として向き合いやすい場所です。";
}

// ---------------------------------------------------------------------------
// meaning-action: 補助付加文（距離・人気など）
// ---------------------------------------------------------------------------

function buildMeaningAction(args: {
  secondary?: Candidate;
  context: ShrineNarrativeContext;
  rec: BuildParams["rec"];
}): string | undefined {
  const ritual  = clean(args.context.ritual)  || null;
  const pattern = clean(args.context.pattern) || null;

  if (args.secondary?.key === "distance") {
    return ritual  ?? "まず無理なく足を運べること自体が、参拝の入口になります。";
  }
  if (args.secondary?.key === "popular") {
    return pattern ?? "迷いがある時でも、参拝先として思い描きやすい安定感があります。";
  }

  if (args.rec.fallback_mode && args.rec.fallback_mode !== "none") {
    if (typeof args.rec.distance_m    === "number") return ritual  ?? "まず無理なく足を運べること自体が、参拝の入口になります。";
    if (typeof args.rec.popular_score === "number") return pattern ?? "迷いがある時でも、参拝先として思い描きやすい安定感があります。";
  }

  return undefined;
}


// ---------------------------------------------------------------------------
// Public export
// ---------------------------------------------------------------------------

export function buildMeaningNarrative(args: {
  params: BuildParams;
  primary: Candidate;
  secondary?: Candidate;
}): MeaningNarrative {
  const { params, primary, secondary } = args;

  const consultation = buildNeedTagMeaningSlots(params);
  const shrine       = buildShrineMeaningSlots(params);
  const need         = clean(consultation.needPrimary) || clean(params.needTags?.[0]) || null;
  const context      = resolveShrineContext(params);

  const heroMeaningCopy = buildHeroMeaningCopy({ mode: params.mode, need, shrine });
  const meaningCore = buildMeaningCore({ mode: params.mode, need, shrine, context });

  const whyNow     = buildWhyNow({ mode: params.mode, need, consultation, primary });
  const actionRole = buildActionRole({ mode: params.mode, need, shrine, consultation, primary, context });
  const meaningContext = `${whyNow}${actionRole}`;
  const reflectionQuestion = buildReflectionQuestion({ mode: params.mode, need, shrine, consultation, primary, context });

  const meaningAction = buildMeaningAction({ secondary, context, rec: params.rec });

  return {
    heroMeaningCopy,
    meaningCore,
    meaningContext,
    meaningAction,
    // backward compat
    shrineMeaning: meaningCore,
    actionMeaning: reflectionQuestion,
  };
}
