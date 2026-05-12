export type NeedDisplayTag = "money" | "courage" | "career" | "mental" | "rest" | "love" | "study";

export type ShrineTone = "strong" | "quiet" | "tight" | "neutral";

export const NEED_DISPLAY_LABELS: Record<string, string> = {
  career: "転機・仕事",
  mental: "不安・心",
  rest: "休息",
  love: "恋愛",
  marriage: "縁結び・結婚",
  relationship: "人間関係",
  communication: "会話・発信",
  money: "金運",
  study: "学業・試験",
  health: "健康",
  protection: "厄除け・守護",
  courage: "前進・後押し",
  focus: "集中・継続",
  family: "子宝・安産",
  travel_safe: "旅行・安全",
};

export function labelNeedDisplayTag(tag: string): string {
  return NEED_DISPLAY_LABELS[tag] ?? tag;
}

export function isNeedDisplayTag(tag: string): tag is NeedDisplayTag {
  return ["money", "courage", "career", "mental", "rest", "love", "study"].includes(tag);
}

export function buildNeedPrimaryShortCopy(args: {
  primaryTag: NeedDisplayTag | null;
  shrineTone: ShrineTone;
  fallbackText?: string | null;
}): string | null {
  const { primaryTag, shrineTone, fallbackText = null } = args;

  if (!primaryTag) return fallbackText;

  if (primaryTag === "courage") {
    if (shrineTone === "strong") return "止まった流れを動かす";
    if (shrineTone === "tight") return "次の一歩を定める";
    if (shrineTone === "quiet") return "気持ちを整えて一歩を決める";
    return "次の一歩を後押しする";
  }

  if (primaryTag === "mental") {
    if (shrineTone === "strong") return "気持ちを切り替える";
    if (shrineTone === "tight") return "気持ちを引き締めて整える";
    return "不安や気持ちを整える";
  }

  if (primaryTag === "career") {
    if (shrineTone === "strong") return "仕事の停滞を動かす";
    if (shrineTone === "tight") return "仕事や転機の判断を定める";
    return "仕事や転機を整える";
  }

  if (primaryTag === "money") {
    if (shrineTone === "strong") return "金運や流れを動かす";
    if (shrineTone === "quiet") return "金運や巡りを整える";
    return "金運や流れを立て直す";
  }

  if (primaryTag === "rest") {
    if (shrineTone === "quiet") return "心身を休める";
    return "心身を整える";
  }

  if (primaryTag === "love") {
    if (shrineTone === "quiet") return "関係性を見直す";
    return "良縁や関係性を進める";
  }

  if (primaryTag === "study") {
    if (shrineTone === "tight") return "集中や目標を定める";
    return "集中や学業の流れを整える";
  }

  return fallbackText;
}
