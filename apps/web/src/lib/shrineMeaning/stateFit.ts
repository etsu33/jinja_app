

import type { StateTransitionType } from "@/lib/concierge/stateTransitionNarrative";
import type { StateFit, ToneLevel } from "./types";

export type StateFitKey = Exclude<StateTransitionType, "unknown">;

export type StateFitTaxonomyItem = {
  key: StateFitKey;
  label: string;
  description: string;
  narrativeHint: string;
};

export const STATE_FIT_TAXONOMY: Record<StateFitKey, StateFitTaxonomyItem> = {
  continuation: {
    key: "continuation",
    label: "継続して向き合う",
    description: "前回から近いテーマを、急いで変えずにもう少し丁寧に見直す状態。",
    narrativeHint: "同じテーマが続いている時は、新しい答えを探すより、残すものと軽くするものを整理する参拝と相性がある。",
  },
  progression: {
    key: "progression",
    label: "行動へ移り始める",
    description: "内側で整える状態から、外へ向けて小さく動き始める状態。",
    narrativeHint: "行動側へ意識が向き始めている時は、参拝後に一つだけ実行することを決める流れと相性がある。",
  },
  recovery: {
    key: "recovery",
    label: "余白を戻す",
    description: "前へ進めるより先に、気持ちや体力の緊張を少し戻す状態。",
    narrativeHint: "回復寄りの状態では、刺激を増やすより、静かに滞在して整える参拝と相性がある。",
  },
  regression: {
    key: "regression",
    label: "立ち止まって整え直す",
    description: "後退と断定せず、進む前に足元の状態を見直す必要が出ている状態。",
    narrativeHint: "不安や消耗が前に出ている時は、無理に前進させるより、状態を整え直す場所と相性がある。",
  },
  transition: {
    key: "transition",
    label: "意識の向きを切り替える",
    description: "前回とは違うテーマが出ていて、意識の向きが変わり始めている状態。",
    narrativeHint: "切り替わりの状態では、結論を急ぐより、今どちらへ向き始めているかを確かめる参拝と相性がある。",
  },
};

export function getStateFitTaxonomyItem(key: StateFitKey): StateFitTaxonomyItem {
  return STATE_FIT_TAXONOMY[key];
}

export function getStateFitLevel(stateFit: StateFit, key: StateFitKey): ToneLevel {
  return stateFit[key];
}
