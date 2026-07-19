

"use client";

import { useEffect, useMemo, useState } from "react";

import { createShrineReflection } from "@/lib/api/reflections";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";

type Props = {
  shrineId: number | string;
  historyTheme?: string | null;
  threadId?: string | null;
  ctx?: string | null;
  accessLevel?: "anonymous" | "free" | "premium" | null;
  onSaved?: () => void;
};

const PROMPT_TEXT = "参拝して、今どんな変化がありましたか？";

export function ShrineReflectionPrompt({
  shrineId,
  historyTheme = null,
  threadId = null,
  ctx = null,
  accessLevel = null,
  onSaved,
}: Props) {
  const mode = ctx === "concierge" ? "need" : undefined;
  const [answer, setAnswer] = useState("");
  const [moodBefore, setMoodBefore] = useState("");
  const [moodAfter, setMoodAfter] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<"idle" | "saved" | "error">("idle");

  const trimmedAnswer = answer.trim();
  const answerLength = useMemo(() => trimmedAnswer.length, [trimmedAnswer]);
  const canSubmit = answerLength > 0 && !submitting;

  useEffect(() => {
    trackSearchEvent("reflection_prompt_view", {
      source: "shrine_detail",
      shrineId,
      threadId: threadId ?? undefined,
      historyTheme: historyTheme ?? undefined,
      reflectionFormType: "mood_delta",
      reflectionContext: "visit_done",
      mode,
      accessLevel,
    });
  }, [accessLevel, historyTheme, mode, shrineId, threadId]);

  async function handleSubmit() {
    if (!canSubmit) return;

    try {
      setSubmitting(true);
      setStatus("idle");

      const numericThreadId = threadId != null ? Number(threadId) : undefined;

      await createShrineReflection(shrineId, {
        thread_id: numericThreadId != null && Number.isFinite(numericThreadId) ? numericThreadId : undefined,
        history_theme: historyTheme ?? "",
        prompt: PROMPT_TEXT,
        answer: trimmedAnswer,
        mood_before: moodBefore || undefined,
        mood_after: moodAfter || undefined,
      });

      trackSearchEvent("reflection_saved", {
        source: "shrine_detail",
        shrineId,
        threadId: threadId ?? undefined,
        historyTheme: historyTheme ?? undefined,
        reflectionFormType: "mood_delta",
        reflectionContext: "visit_done",
        answerLength,
        moodBefore: moodBefore || undefined,
        moodAfter: moodAfter || undefined,
        mode,
        accessLevel,
      });

      setStatus("saved");
      onSaved?.();
    } catch {
      setStatus("error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4">
      <p className="text-sm font-semibold text-emerald-800">参拝後の振り返り</p>
      <p className="mt-1 text-xs leading-5 text-slate-600">{PROMPT_TEXT}</p>

      <textarea
        value={answer}
        onChange={(event) => setAnswer(event.target.value)}
        rows={4}
        placeholder="例：少し落ち着いた / 次にやることが見えた / まだ迷いはあるけれど一度区切れた"
        className="mt-3 w-full rounded-[var(--kt-radius-panel)] border border-emerald-100 bg-[var(--kt-color-surface-default)] px-3 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-[var(--kt-color-border-focus)]"
      />

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        <input
          value={moodBefore}
          onChange={(event) => setMoodBefore(event.target.value)}
          placeholder="参拝前の気分 任意"
          className="rounded-[var(--kt-radius-panel)] border border-emerald-100 bg-[var(--kt-color-surface-default)] px-3 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-[var(--kt-color-border-focus)]"
        />
        <input
          value={moodAfter}
          onChange={(event) => setMoodAfter(event.target.value)}
          placeholder="参拝後の気分 任意"
          className="rounded-[var(--kt-radius-panel)] border border-emerald-100 bg-[var(--kt-color-surface-default)] px-3 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-[var(--kt-color-border-focus)]"
        />
      </div>

      {status === "saved" ? (
        <p className="mt-3 text-xs font-semibold text-emerald-700">振り返りを保存しました。</p>
      ) : null}
      {status === "error" ? (
        <p className="mt-3 text-xs font-semibold text-rose-700">振り返りの保存に失敗しました。</p>
      ) : null}

      <button
        type="button"
        disabled={!canSubmit}
        onClick={handleSubmit}
        className="mt-3 w-full rounded-2xl bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "保存中..." : "振り返りを保存する"}
      </button>
    </div>
  );
}
