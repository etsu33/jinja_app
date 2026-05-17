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
      title: "行動側へ意識が向き始める流れ",
      summary:
        "前回よりも、内側で整えることから、外へ向けて小さく動くことへ意識が移り始めています。勢いで大きく変える段階というより、まず一つだけ行動を決めやすい段階です。",
    };
  }

  if (type === "recovery") {
    return {
      type,
      title: "余白を戻そうとする流れ",
      summary:
        "今は無理に前へ進めるより、気持ちや体力の緊張を少し戻すことが先に来ています。休むだけで終わらせるというより、整えてから動ける状態を作る段階です。",
    };
  }

  if (type === "regression") {
    return {
      type,
      title: "一度立ち止まって整え直す流れ",
      summary:
        "前へ進む意識があったところから、少し不安や消耗が前に出ている可能性があります。後退と決めつけず、今は無理に進める前に、足元の状態を整え直す段階として扱うのが合っています。",
    };
  }

  if (type === "continuation") {
    return {
      type,
      title: "同じテーマをもう少し丁寧に見る流れ",
      summary:
        "前回から近いテーマが続いています。まだ答えを急いで変える段階ではなく、同じ課題の中で、何を残して何を軽くするかを少しずつ見直す段階です。",
    };
  }

  if (type === "transition") {
    return {
      type,
      title: "意識の向きが切り替わり始める流れ",
      summary:
        "前回とは違うテーマが出ています。急いで結論を決めるより、今どちらの方向へ意識が向き始めているのかを確かめ、次の一歩を小さく置く段階です。",
    };
  }

  return {
    type: "unknown",
    title: "今の流れを静かに確認する段階",
    summary:
      "今回は大きな変化として断定するより、今出ているテーマを静かに確認する段階です。",
  };
}
