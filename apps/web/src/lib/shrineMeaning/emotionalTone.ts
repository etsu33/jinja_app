import type { EmotionalTone, ToneLevel } from "./types";

export type EmotionalToneKey = "quiet" | "strong" | "open" | "grounded" | "solemn" | "neutral";

export type EmotionalToneTaxonomyItem = {
  key: EmotionalToneKey;
  label: string;
  description: string;
  tone: EmotionalTone;
  narrativeHint: string;
};

const low: ToneLevel = "low";
const mid: ToneLevel = "mid";
const high: ToneLevel = "high";

export const EMOTIONAL_TONE_TAXONOMY: Record<EmotionalToneKey, EmotionalToneTaxonomyItem> = {
  quiet: {
    key: "quiet",
    label: "静かに整う",
    description: "刺激を増やすより、気持ちを落ち着けて受け取りやすい空気感。",
    tone: {
      silence: high,
      intensity: low,
      openness: mid,
      grounding: high,
    },
    narrativeHint: "結論を急ぐより、静かに整え直したい状態と相性がある。",
  },
  strong: {
    key: "strong",
    label: "背中を押す",
    description: "停滞を切り替えたい時に、前へ進む感覚を持ちやすい空気感。",
    tone: {
      silence: mid,
      intensity: high,
      openness: mid,
      grounding: mid,
    },
    narrativeHint: "止まった流れを動かす節目として置きやすい。",
  },
  open: {
    key: "open",
    label: "視界が開ける",
    description: "考えが閉じている時に、少し広い見方へ戻りやすい空気感。",
    tone: {
      silence: mid,
      intensity: mid,
      openness: high,
      grounding: mid,
    },
    narrativeHint: "選択肢や見方を広げたい状態と相性がある。",
  },
  grounded: {
    key: "grounded",
    label: "足元を整える",
    description: "焦りや揺れを抑え、今できることへ戻りやすい空気感。",
    tone: {
      silence: mid,
      intensity: low,
      openness: low,
      grounding: high,
    },
    narrativeHint: "大きく変える前に、足元の状態を整えたい時に向く。",
  },
  solemn: {
    key: "solemn",
    label: "背筋が伸びる",
    description: "気持ちを引き締め、決める前の姿勢を整えやすい空気感。",
    tone: {
      silence: high,
      intensity: high,
      openness: low,
      grounding: mid,
    },
    narrativeHint: "迷いを減らし、向き合う姿勢を整えたい状態と相性がある。",
  },
  neutral: {
    key: "neutral",
    label: "偏りが少ない",
    description: "強い意味を押し出しすぎず、幅広い状態で扱いやすい空気感。",
    tone: {
      silence: mid,
      intensity: mid,
      openness: mid,
      grounding: mid,
    },
    narrativeHint: "状態がまだ定まりきらない時でも、無理なく接続しやすい。",
  },
};

export function getEmotionalToneItem(key: EmotionalToneKey): EmotionalToneTaxonomyItem {
  return EMOTIONAL_TONE_TAXONOMY[key];
}
