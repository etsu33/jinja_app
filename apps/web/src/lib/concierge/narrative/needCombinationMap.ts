

import type { NeedTag } from "./types";

/**
 * NeedTag combination policy
 *
 * Do not add new NeedTag values here.
 * This file increases expression depth by interpreting combinations of the
 * existing NeedTag set instead of expanding the tag taxonomy.
 */
export type NeedCombinationKey = `${NeedTag}+${NeedTag}`;

export type NeedCombinationNarrative = {
  key: NeedCombinationKey;
  tags: [NeedTag, NeedTag];
  title: string;
  summary: string;
  priorityHint: string;
  actionHint: string;
};

function toCombinationKey(a: NeedTag, b: NeedTag): NeedCombinationKey {
  return [a, b].sort().join("+") as NeedCombinationKey;
}

const NEED_COMBINATION_MAP: Record<string, NeedCombinationNarrative> = {
  [toCombinationKey("mental", "rest")]: {
    key: toCombinationKey("mental", "rest"),
    tags: ["mental", "rest"],
    title: "不安と疲れが重なっている状態",
    summary: "考え続ける疲れと、落ち着きたい気持ちが同時に出ています。まずは刺激を増やすより、気持ちを静かに戻せる場所との相性が高い状態です。",
    priorityHint: "回復と安心感を優先する",
    actionHint: "短時間でもよいので、静かに歩ける参拝先を選ぶ",
  },
  [toCombinationKey("mental", "courage")]: {
    key: toCombinationKey("mental", "courage"),
    tags: ["mental", "courage"],
    title: "不安はあるが、止まり続けたくない状態",
    summary: "迷いや不安を抱えながらも、次に進むきっかけを探している状態です。強く背中を押すより、気持ちを整えて一歩を決められる神社と相性があります。",
    priorityHint: "安心して踏み出すことを優先する",
    actionHint: "願いごとを増やすより、次の一歩を一つだけ決める",
  },
  [toCombinationKey("career", "courage")]: {
    key: toCombinationKey("career", "courage"),
    tags: ["career", "courage"],
    title: "仕事や転機に向けて前進したい状態",
    summary: "仕事や役割の流れを変えたい気持ちと、行動に移したい気持ちが重なっています。現状維持より、判断と前進を後押しする神社が合いやすい状態です。",
    priorityHint: "決断と前進を優先する",
    actionHint: "参拝後に一つだけ実行する行動を決める",
  },
  [toCombinationKey("money", "career")]: {
    key: toCombinationKey("money", "career"),
    tags: ["money", "career"],
    title: "仕事と収入の流れを整えたい状態",
    summary: "仕事の流れと現実的な安定を同時に見直したい状態です。勢いだけで進むより、積み上げや商いの流れを整える神社と相性があります。",
    priorityHint: "現実的な立て直しを優先する",
    actionHint: "収入につながる行動を一つ具体化する",
  },
  [toCombinationKey("money", "courage")]: {
    key: toCombinationKey("money", "courage"),
    tags: ["money", "courage"],
    title: "現実を動かす勇気が必要な状態",
    summary: "お金や成果への意識と、行動へ移したい気持ちが重なっています。願うだけでなく、現実の動きを作る参拝テーマと相性があります。",
    priorityHint: "成果につながる一歩を優先する",
    actionHint: "小さくても収益や仕事に直結する行動を決める",
  },
  [toCombinationKey("love", "mental")]: {
    key: toCombinationKey("love", "mental"),
    tags: ["love", "mental"],
    title: "関係性への不安を整理したい状態",
    summary: "人とのつながりに対する迷いや不安が出ています。縁を急いで動かすより、自分の気持ちを整えながら関係性を見直せる神社と相性があります。",
    priorityHint: "関係性より先に自分の状態を整える",
    actionHint: "相手を変える願いより、自分の向き合い方を言葉にする",
  },
  [toCombinationKey("study", "rest")]: {
    key: toCombinationKey("study", "rest"),
    tags: ["study", "rest"],
    title: "頑張りたいが、集中力の回復が必要な状態",
    summary: "学びや準備を進めたい気持ちはありますが、今は回復も必要です。無理に追い込むより、集中し直すための余白を作れる神社と相性があります。",
    priorityHint: "回復してから集中を戻す",
    actionHint: "参拝後に学習時間を短く区切って再開する",
  },
  [toCombinationKey("career", "mental")]: {
    key: toCombinationKey("career", "mental"),
    tags: ["career", "mental"],
    title: "仕事の迷いを整理したい状態",
    summary: "仕事や進路について考えるほど、迷いや不安が強くなりやすい状態です。すぐに答えを出すより、判断軸を整える神社と相性があります。",
    priorityHint: "判断軸の整理を優先する",
    actionHint: "参拝後に、今やめることと続けることを一つずつ書き出す",
  },
};

export function resolveNeedCombinationNarrative(
  tags: NeedTag[],
): NeedCombinationNarrative | null {
  const uniqueTags = Array.from(new Set(tags)).filter(Boolean) as NeedTag[];

  for (let i = 0; i < uniqueTags.length; i += 1) {
    for (let j = i + 1; j < uniqueTags.length; j += 1) {
      const key = toCombinationKey(uniqueTags[i], uniqueTags[j]);
      const hit = NEED_COMBINATION_MAP[key];
      if (hit) return hit;
    }
  }

  return null;
}

export { NEED_COMBINATION_MAP };
