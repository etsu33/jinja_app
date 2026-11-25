import type {
  PreviousConsultationSummary,
  StateDelta,
} from "./stateComparison";
import { toNeedTagLabel } from "./needTagLabelMap";
import { buildStateTransitionNarrative } from "./stateTransitionNarrative";

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

type BuildSummaryArgs = {
  changedNeedTags: string[];
  continuedNeedTags: string[];
  hasPreviousAction: boolean;
};

function buildSummary({
  changedNeedTags,
  continuedNeedTags,
  hasPreviousAction,
}: BuildSummaryArgs): string | null {
  if (changedNeedTags.length > 0) {
    const labels = changedNeedTags.map(toNeedTagLabel).filter((label): label is string => Boolean(label));
    if (labels.length > 0) {
      return hasPreviousAction
        ? `前回の行動を踏まえると、今回は「${labels.join("」「")}」を意識する流れが強まっています。`
        : `今回は小さく行動へ移すために、「${labels.join("」「")}」を意識する流れが強まっています。`;
    }
  }

  if (continuedNeedTags.length > 0) {
    const labels = continuedNeedTags.map(toNeedTagLabel).filter((label): label is string => Boolean(label));
    if (labels.length > 0) {
      return hasPreviousAction
        ? `前回の行動を踏まえて、今回も「${labels.join("」「")}」が継続したテーマになっています。`
        : `今回は小さく行動へ移すために、前回から継続して「${labels.join("」「")}」を見直す流れです。`;
    }
  }

  return null;
}

function buildCombinationChange(
  previous: PreviousConsultationSummary | null,
  current: PreviousConsultationSummary | null,
): StateDelta["combinationChange"] {
  const previousCombination = previous?.combination ?? null;
  const currentCombination = current?.combination ?? null;
  const previousTitle = previousCombination?.title ?? null;
  const currentTitle = currentCombination?.title ?? null;

  if (!previousCombination && !currentCombination) {
    return {
      previousTitle,
      currentTitle,
      changed: false,
      summary: null,
    };
  }

  if (!previousCombination && currentCombination) {
    return {
      previousTitle,
      currentTitle,
      changed: true,
      summary: `今回は「${currentTitle}」が状態の重なりとして見えています。`,
    };
  }

  if (previousCombination && !currentCombination) {
    return {
      previousTitle,
      currentTitle,
      changed: true,
      summary: previousTitle
        ? `前回見えていた「${previousTitle}」とは違い、今回は単一のテーマが中心に出ています。`
        : null,
    };
  }

  const changed = previousCombination?.key !== currentCombination?.key;

  if (!changed) {
    return {
      previousTitle,
      currentTitle,
      changed: false,
      summary: currentTitle ? `前回から「${currentTitle}」が継続して見えています。` : null,
    };
  }

  return {
    previousTitle,
    currentTitle,
    changed: true,
    summary:
      previousTitle && currentTitle
        ? `前回は「${previousTitle}」が見えていましたが、今回は「${currentTitle}」が強く出ています。`
        : null,
  };
}

function calculateDaysSincePrevious(
  previous: PreviousConsultationSummary | null,
  current: PreviousConsultationSummary | null,
): number | null {
  if (!previous?.createdAt || !current?.createdAt) return null;

  const previousTime = new Date(previous.createdAt).getTime();
  const currentTime = new Date(current.createdAt).getTime();

  if (!Number.isFinite(previousTime) || !Number.isFinite(currentTime)) return null;

  const diffMs = currentTime - previousTime;
  if (diffMs < 0) return null;

  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

function buildActionReflection(
  previous: PreviousConsultationSummary | null,
): StateDelta["actionReflection"] {
  const actionState = previous?.actionState ?? null;

  if (actionState === "reflected") {
    return {
      type: "reflected",
      title: "前回の提案を振り返りまでつなげています",
      summary:
        "前回の神社について、参拝後の振り返りが保存されています。今回は、その時に見えた変化を踏まえて、次に整えたいテーマを確認する流れです。",
      nextActionLabel: "前回の変化を踏まえて相談する",
    };
  }

  if (actionState === "visited") {
    return {
      type: "visited",
      title: "前回の提案を実際の行動につなげています",
      summary:
        "前回の神社を訪れた記録があります。今回は、行ったことで少し見えたことや、まだ残っているテーマを整理する流れです。",
      nextActionLabel: "参拝後の変化を振り返る",
    };
  }

  if (actionState === "saved") {
    return {
      type: "saved",
      title: "前回の候補を保存して見返す準備ができています",
      summary:
        "前回の神社は保存されています。まだ参拝までは進んでいないため、今回は行くかどうかを決める前の整理として扱えます。",
      nextActionLabel: "保存した理由を見直す",
    };
  }

  if (actionState === "none") {
    return {
      type: "none",
      title: "前回はまだ行動ログが残っていません",
      summary:
        "前回の候補に対して、保存や参拝の記録はまだありません。今回は、気になった候補を一つ残すことから始めると見返しやすくなります。",
      nextActionLabel: "気になる候補を一つ保存する",
    };
  }

  return null;
}

export function compareState(
  previous: PreviousConsultationSummary | null,
  current: PreviousConsultationSummary | null,
): StateDelta {
  const previousTags = unique(previous?.matchedNeedTags ?? []);
  const currentTags = unique(current?.matchedNeedTags ?? []);

  const changedNeedTags = currentTags.filter(
    (tag) => !previousTags.includes(tag),
  );

  const continuedNeedTags = currentTags.filter((tag) =>
    previousTags.includes(tag),
  );

  const daysSincePrevious = calculateDaysSincePrevious(previous, current);
  const within7DaysSincePrevious = daysSincePrevious !== null && daysSincePrevious <= 7;
  const combinationChange = buildCombinationChange(previous, current);
  const transitionNarrative = buildStateTransitionNarrative({
    previousNeedTags: previousTags,
    currentNeedTags: currentTags,
    changedNeedTags,
    continuedNeedTags,
    combinationChanged: combinationChange.changed,
  });
  const previousActionState = previous?.actionState ?? null;
  const hasPreviousAction = previousActionState === "saved" || previousActionState === "visited" || previousActionState === "reflected";

  return {
    previous,
    current,
    changedNeedTags,
    continuedNeedTags,
    daysSincePrevious,
    within7DaysSincePrevious,
    summary: buildSummary({
      changedNeedTags,
      continuedNeedTags,
      hasPreviousAction,
    }),
    combinationChange,
    transitionNarrative,
    hasPreviousAction,
    actionReflection: buildActionReflection(previous),
  };
}
