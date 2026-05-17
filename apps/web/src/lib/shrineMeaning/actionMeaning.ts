

import type { ActionMeaning } from "./types";

export type ActionMeaningTaxonomyItem = {
  key: ActionMeaning;
  label: string;
  description: string;
  narrativeHint: string;
  visitPrompt: string;
};

export const ACTION_MEANING_TAXONOMY: Record<ActionMeaning, ActionMeaningTaxonomyItem> = {
  rest: {
    key: "rest",
    label: "休む",
    description: "刺激や判断を増やさず、まず状態を落ち着ける行動意味。",
    narrativeHint: "今は無理に進めるより、静かに余白を戻すことが合いやすい。",
    visitPrompt: "短くてもよいので、静かに滞在する時間を取る。",
  },
  reflect: {
    key: "reflect",
    label: "見つめ直す",
    description: "今の気持ちや判断軸を、急がずに整理する行動意味。",
    narrativeHint: "答えを急ぐより、何を大事にしたいかを見直す段階に合いやすい。",
    visitPrompt: "参拝後に、今気になっていることを一つだけ言葉にする。",
  },
  reset: {
    key: "reset",
    label: "切り替える",
    description: "停滞感や迷いから少し離れ、流れを置き直す行動意味。",
    narrativeHint: "前の流れをすべて否定せず、いったん区切りをつける参拝と相性がある。",
    visitPrompt: "帰る前に、今日で一度区切ることを一つ決める。",
  },
  decide: {
    key: "decide",
    label: "決める",
    description: "迷いを減らし、次の一歩を具体化する行動意味。",
    narrativeHint: "大きな決断を急ぐより、次に置く小さな一手を決める段階に合いやすい。",
    visitPrompt: "参拝後に、24時間以内にできる行動を一つ決める。",
  },
  begin: {
    key: "begin",
    label: "始める",
    description: "止まっていた意識を、現実の小さな行動へ移す行動意味。",
    narrativeHint: "気持ちが外へ向き始めた時に、小さく始めるきっかけになりやすい。",
    visitPrompt: "完璧に整える前に、最初の一歩だけを小さく始める。",
  },
  continue: {
    key: "continue",
    label: "続ける",
    description: "大きく変えるより、今ある流れを丁寧に続ける行動意味。",
    narrativeHint: "新しい答えを探すより、続いているテーマを少し深く見る段階に合いやすい。",
    visitPrompt: "今続けていることの中で、残したいものを一つ確認する。",
  },
  release: {
    key: "release",
    label: "手放す",
    description: "抱え込みすぎた思考や感情を、少し軽くする行動意味。",
    narrativeHint: "すぐ解決するより、今持ちすぎているものを少し下ろす参拝と相性がある。",
    visitPrompt: "参拝中に、今いったん手放したい考えを一つだけ決める。",
  },
  connect: {
    key: "connect",
    label: "つなぎ直す",
    description: "人・場所・自分自身との関係性を見直し、接続し直す行動意味。",
    narrativeHint: "関係を急いで動かすより、どう関わり直すかを静かに整える段階に合いやすい。",
    visitPrompt: "参拝後に、関わり方を見直したい相手や場所を一つ思い浮かべる。",
  },
};

export function getActionMeaningItem(key: ActionMeaning): ActionMeaningTaxonomyItem {
  return ACTION_MEANING_TAXONOMY[key];
}
