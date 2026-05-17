

export type StateTransitionType =
  | "continuation"
  | "progression"
  | "recovery"
  | "regression"
  | "transition"
  | "unknown";

export type StateTransitionNarrative = {
  type: StateTransitionType;
  title: string;
  summary: string | null;
};

type BuildStateTransitionNarrativeArgs = {
  previousNeedTags?: string[] | null;
  currentNeedTags?: string[] | null;
  changedNeedTags?: string[] | null;
  continuedNeedTags?: string[] | null;
  combinationChanged?: boolean | null;
};

function unique(values: string[] | null | undefined): string[] {
  return Array.from(new Set((values ?? []).filter(Boolean)));
}

function hasAny(values: string[], targets: string[]): boolean {
  return targets.some((target) => values.includes(target));
}

function isRecovery(previousTags: string[], currentTags: string[]): boolean {
  return (
    hasAny(previousTags, ["mental", "rest"]) &&
    hasAny(currentTags, ["rest", "mental"]) &&
    !hasAny(currentTags, ["courage", "career", "money"])
  );
}

function isProgression(previousTags: string[], currentTags: string[]): boolean {
  return (
    hasAny(currentTags, ["courage", "career", "money"]) &&
    hasAny(previousTags, ["mental", "rest"])
  );
}

function isRegression(previousTags: string[], currentTags: string[]): boolean {
  return (
    hasAny(previousTags, ["courage", "career", "money"]) &&
    hasAny(currentTags, ["mental", "rest"])
  );
}

export function resolveStateTransitionType(
  args: BuildStateTransitionNarrativeArgs,
): StateTransitionType {
  const previousTags = unique(args.previousNeedTags);
  const currentTags = unique(args.currentNeedTags);
  const changedNeedTags = unique(args.changedNeedTags);
  const continuedNeedTags = unique(args.continuedNeedTags);

  if (previousTags.length === 0 && currentTags.length === 0) {
    return "unknown";
  }

  if (continuedNeedTags.length > 0 && changedNeedTags.length === 0 && !args.combinationChanged) {
    return "continuation";
  }

  if (isProgression(previousTags, currentTags)) {
    return "progression";
  }

  if (isRegression(previousTags, currentTags)) {
    return "regression";
  }

  if (isRecovery(previousTags, currentTags)) {
    return "recovery";
  }

  if (changedNeedTags.length > 0 || args.combinationChanged) {
    return "transition";
  }

  return "unknown";
}

export function buildStateTransitionNarrative(
  args: BuildStateTransitionNarrativeArgs,
): StateTransitionNarrative {
  const type = resolveStateTransitionType(args);

  if (type === "progression") {
    return {
      type,
      title: "少し前へ向かう流れ",
      summary:
        "前回よりも、止まることより動き出したい気持ちが少し前に出ています。急いで切り替えるというより、小さな一歩を決めやすい段階です。",
    };
  }

  if (type === "recovery") {
    return {
      type,
      title: "立て直しを優先する流れ",
      summary:
        "今は無理に前へ進めるより、気持ちや体力の余白を戻すことが先に来ています。整えてから動く準備を作る段階です。",
    };
  }

  if (type === "regression") {
    return {
      type,
      title: "揺り戻しを整える流れ",
      summary:
        "前に進む意識があったところから、少し不安や消耗が戻ってきている可能性があります。悪い変化と決めつけず、一度整え直す段階として扱うのが合っています。",
    };
  }

  if (type === "continuation") {
    return {
      type,
      title: "同じテーマを丁寧に見る流れ",
      summary:
        "前回から近いテーマが続いています。大きく変えるより、同じ課題を少し違う角度から見直す段階です。",
    };
  }

  if (type === "transition") {
    return {
      type,
      title: "状態が切り替わり始める流れ",
      summary:
        "前回とは違うテーマが出ています。まだ結論を急ぐより、今どちらへ意識が向き始めているのかを静かに確かめる段階です。",
    };
  }

  return {
    type: "unknown",
    title: "今の流れを整理中",
    summary: null,
  };
}
