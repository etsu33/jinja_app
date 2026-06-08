/**
 * buildStateNarrative
 *
 * responsibility:
 * ② 状態整理を生成する
 *
 * boundary:
 * - 推薦判断は扱わない
 * - 行動意味は扱わない
 * - 神社説明は扱わない
 */

import { clean, buildConsultationMeaningSlots } from "./buildRecommendationReasonViewModel";
import type { BuildParams, Candidate, ConsultationMeaningSlots } from "./buildRecommendationReasonViewModel";

export type StateNarrative = {
  consultationSummary: string;
};

function hasConsultationNeed(slots: ConsultationMeaningSlots): boolean {
  return Boolean(clean(slots.needPrimary));
}

function buildStateStuckText(
  params: BuildParams,
  slots: ConsultationMeaningSlots,
  primary: Candidate,
): string {
  const need = clean(slots.needPrimary);

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

  if (!hasConsultationNeed(slots) && primary.key === "distance") {
    return "今は遠くの正解を探すほど動けなくなりやすく、まず無理なく足を運べる選択肢から見た方が流れを切り替えやすい状態です。";
  }

  if (!hasConsultationNeed(slots) && (primary.key === "element_match" || primary.key === "sign_match")) {
    return "今は強い刺激よりも、気質に無理なく馴染む場所の方が受け取りやすく、考えすぎをほどきやすい状態です。";
  }

  return "今は答えを急ぐほど判断が散りやすく、まず状態や優先順位を整えながら見直した方が受け取りやすい状態です。";
}

function buildStatePriorityText(
  params: BuildParams,
  slots: ConsultationMeaningSlots,
  primary: Candidate,
): string {
  const need = clean(slots.needPrimary);

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

  if (!hasConsultationNeed(slots) && primary.key === "distance") {
    return "今は理想の候補を探し切るより先に、実際に動ける場所から流れを切り替えることを優先するのが合っています。";
  }

  if (!hasConsultationNeed(slots) && (primary.key === "element_match" || primary.key === "sign_match")) {
    return "今は強く変わることより先に、無理なく受け取れて気持ちを整えやすい場所を優先するのが合っています。";
  }

  return "今は答えを出すことより先に、状態を整えながら優先順位を見直せる場を優先するのが合っています。";
}

function buildConsultationSummary(
  params: BuildParams,
  slots: ConsultationMeaningSlots,
  primary: Candidate,
  _secondary?: Candidate,
): string {
  const stuck = buildStateStuckText(params, slots, primary);
  const priority = buildStatePriorityText(params, slots, primary);

  return `${stuck} ${priority}`;
}

export function buildStateNarrative(args: {
  params: BuildParams;
  primary: Candidate;
  secondary?: Candidate;
}): StateNarrative {
  const slots = buildConsultationMeaningSlots(args.params);

  return {
    consultationSummary: buildConsultationSummary(args.params, slots, args.primary, args.secondary),
  };
}
