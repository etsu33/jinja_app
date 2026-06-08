

import type { ShrineMeaningSchema } from "../types";

/**
 * Sample Shrine Meaning Schemas
 *
 * These examples are for validating the meaning layer shape before connecting
 * it to recommendation narrative or backend shrine records.
 *
 * shrineId values are temporary sample ids. Replace them with real DB ids when
 * connecting to production shrine data.
 */
export const SAMPLE_SHRINE_MEANINGS: ShrineMeaningSchema[] = [
  {
    shrineId: 17,
    meaningKey: "quiet-recovery-guardian",
    title: "静かに整え直す神社",
    summary:
      "強く背中を押すというより、疲れや迷いをいったん落ち着けて、足元の感覚を取り戻しやすい場所として扱います。",
    coreMeanings: ["回復", "静けさ", "守り", "状態整理"],
    emotionalTone: {
      silence: "high",
      intensity: "low",
      openness: "mid",
      grounding: "high",
    },
    actionMeanings: ["rest", "reflect", "continue"],
    historicalContexts: ["protection", "local_guardian"],
    spatialFeelings: ["quiet_forest", "enclosed_space", "solemn_space"],
    stateFit: {
      continuation: "high",
      progression: "low",
      recovery: "high",
      regression: "mid",
      transition: "mid",
    },
    visitStyle: {
      alone: true,
      morning: true,
      shortStay: true,
      slowWalk: true,
      writeAfterVisit: true,
    },
    narrativeHints: [
      "前へ進めるより先に、静かに状態を戻す参拝と相性がある。",
      "同じテーマが続いている時は、急いで変えるより残すものを確認する流れに向く。",
    ],
    sourceNotes: ["sample: shrine meaning schema validation"],
  },
  {
    shrineId: 101,
    meaningKey: "boundary-transition-reset",
    title: "流れを切り替える神社",
    summary:
      "前の流れを否定せずに区切りをつけ、意識の向きを少し変えるための節目として扱います。",
    coreMeanings: ["切り替え", "境界", "再出発", "区切り"],
    emotionalTone: {
      silence: "mid",
      intensity: "mid",
      openness: "high",
      grounding: "mid",
    },
    actionMeanings: ["reset", "release", "begin"],
    historicalContexts: ["boundary", "journey", "protection"],
    spatialFeelings: ["open_sky", "wide_path", "deep_approach"],
    stateFit: {
      continuation: "mid",
      progression: "mid",
      recovery: "low",
      regression: "mid",
      transition: "high",
    },
    visitStyle: {
      alone: true,
      morning: false,
      evening: true,
      shortStay: false,
      slowWalk: true,
      writeAfterVisit: true,
    },
    narrativeHints: [
      "前回とは違うテーマが出ている時に、意識の向きを確認する参拝と相性がある。",
      "結論を急がず、今日で一度区切るものを一つ決める流れに向く。",
    ],
    sourceNotes: ["sample: shrine meaning schema validation"],
  },
  {
    shrineId: 202,
    meaningKey: "progression-commerce-courage",
    title: "現実の一歩を決める神社",
    summary:
      "気持ちを整えるだけで終わらせず、仕事・挑戦・収入など現実の行動へ一つ接続するための場所として扱います。",
    coreMeanings: ["前進", "商い", "決断", "現実行動"],
    emotionalTone: {
      silence: "mid",
      intensity: "high",
      openness: "mid",
      grounding: "mid",
    },
    actionMeanings: ["decide", "begin", "continue"],
    historicalContexts: ["commerce", "victory", "local_guardian"],
    spatialFeelings: ["urban_oasis", "bright_space", "wide_path"],
    stateFit: {
      continuation: "mid",
      progression: "high",
      recovery: "low",
      regression: "low",
      transition: "mid",
    },
    visitStyle: {
      alone: false,
      morning: true,
      shortStay: true,
      slowWalk: false,
      writeAfterVisit: true,
    },
    narrativeHints: [
      "行動側へ意識が向き始めている時に、参拝後の一手を決める流れと相性がある。",
      "大きな決断ではなく、24時間以内にできる小さな行動へ接続しやすい。",
    ],
    sourceNotes: ["sample: shrine meaning schema validation"],
  },
];

export function getSampleShrineMeaningById(
  shrineId: number,
): ShrineMeaningSchema | null {
  return SAMPLE_SHRINE_MEANINGS.find((item) => item.shrineId === shrineId) ?? null;
}
