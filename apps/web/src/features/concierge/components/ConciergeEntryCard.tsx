"use client";

type ConciergeEntryExample = {
  label: string;
  text: string;
};

type ConciergeSessionStateLike = {
  sessionNickname: string | null;
};

type Props = {
  displayName: string | null;
  displayLabel: string;
  sessionState: ConciergeSessionStateLike;
  setSessionNickname: (value: string) => void;
  canSaveConciergeThread: boolean;
  isUiPaywall: boolean;
  redirectToAuth: (kind: "login" | "register") => void;
  needText: string;
  setNeedText: (value: string) => void;
  feelExamples: readonly ConciergeEntryExample[];
  onPickExample: (example: ConciergeEntryExample) => void;
  isBusy: boolean;
  canSend: boolean;
  onSubmit: () => void;
  onClear: () => void;
};

// Concierge Entry Frontend IA v2 (docs/product/concierge-input-architecture.md,
// Frontend IA Implementation Addendum; docs/audit/concierge-l1-freetext-final-readiness.md
// Decision: CONDITIONAL GO, Free-text Primary = Yes, Assist chips visibility
// = medium). This card renders Initial (Level 1 Consultation, Primary CTA)
// and Assist (Consultation Theme Chips, medium visibility) only.
// Level 3-C Recommendation Context (visit date / origin) and Level 2/3-A/3-B
// (visit preference / birthdate / goriyaku) live in the Personalize section
// rendered by ConciergeClientFull -- not in this card. Non-Recommendation
// fields (nickname, login prompt) render last, below the consultation flow,
// with reduced visual prominence (Task 9): they still need a place because
// sessionNickname has a real runtime dependency (anonymous snapshot restore,
// displayLabel greeting elsewhere), so it is not removed, only deprioritized.
export default function ConciergeEntryCard({
  displayName,
  displayLabel,
  sessionState,
  setSessionNickname,
  canSaveConciergeThread,
  isUiPaywall,
  redirectToAuth,
  needText,
  setNeedText,
  feelExamples,
  onPickExample,
  isBusy,
  canSend,
  onSubmit,
  onClear,
}: Props) {
  return (
    <>
      <div className="space-y-1.5 rounded-3xl border border-stone-200/10 bg-stone-50/30 px-4 py-4">
        <div>
          <p className="text-[9px] font-normal tracking-[0.24em] text-[var(--kt-color-text-muted)] opacity-70">KAMI MUSUBI GUIDE</p>
          <h1 className="mt-1.5 text-lg font-medium leading-7 text-[var(--kt-color-text-primary)]">相談から、向かう神社を見つける</h1>
        </div>
        <p className="text-sm leading-6 text-[var(--kt-color-text-muted)] opacity-85">
          {displayName
            ? `${displayLabel}さんの相談をもとに、今向かいやすい神社との出会いを整えます。`
            : "相談をもとに、今向かいやすい神社との出会いを整えます。"}
        </p>
      </div>

      {/* Level 1 Consultation -- Primary Input */}
      <div className="mt-5 space-y-4">
        <div>
          <label htmlFor="concierge-input" className="mb-1.5 block text-sm font-medium text-[var(--kt-color-text-primary)]">
            今、どんなことが気になっていますか？
          </label>
          <textarea
            id="concierge-input"
            value={needText}
            onChange={(e) => setNeedText(e.target.value)}
            placeholder="例: 仕事の迷いを整理したい、少し休みたい"
            rows={4}
            autoFocus
            className="w-full rounded-3xl border border-stone-200/30 bg-white px-3 py-2.5 text-sm leading-7 text-[var(--kt-color-text-primary)] outline-none transition placeholder:text-stone-400 placeholder:opacity-60 focus:border-emerald-300/60 focus:ring-1 focus:ring-emerald-100/60"
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:flex-row">
          <button
            type="button"
            className="min-h-11 w-full rounded-[var(--kt-radius-pill)] border border-emerald-300 bg-emerald-50/50 px-3 py-2 text-sm font-medium text-emerald-800 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2 hover:bg-emerald-100/40 disabled:cursor-not-allowed disabled:opacity-40"
            disabled={isBusy || !needText.trim() || !canSend}
            onClick={onSubmit}
          >
            この相談で神社を提案してもらう
          </button>

          <button
            type="button"
            className="min-h-11 w-full rounded-[var(--kt-radius-pill)] border border-[var(--kt-color-border-strong)] bg-stone-50/25 px-3 py-2 text-sm font-medium text-[var(--kt-color-text-secondary)] transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2 hover:bg-stone-100/30 disabled:cursor-not-allowed disabled:border-stone-200 disabled:bg-stone-100 disabled:text-stone-400 disabled:opacity-40"
            disabled={isBusy}
            onClick={onClear}
          >
            クリア
          </button>
        </div>

        {/* Assist: Consultation Writing Assist chips (medium visibility) --
            not an alternative search route. Picking one replaces the
            textarea with an editable starting sentence (onPickExample),
            the same signal path as typing it manually. */}
        <section aria-label="相談テーマから選ぶ" className="pt-1">
          <p className="text-[11px] font-medium text-[var(--kt-color-text-muted)] opacity-75">うまく言葉にならないとき</p>
          <p className="text-[11px] text-[var(--kt-color-text-muted)] opacity-60">近いテーマから選べます</p>
          <div className="mt-2.5 flex flex-wrap gap-2">
            {feelExamples.map((example) => {
              const isSelected = needText.trim() === example.text;
              return (
                <button
                  key={example.label}
                  type="button"
                  className={[
                    "min-h-11 rounded-[var(--kt-radius-pill)] border px-3 py-2 text-sm font-normal transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2 active:scale-[0.98]",
                    isSelected
                      ? "border-emerald-200/60 bg-emerald-50/40 text-emerald-700"
                      : "border-stone-200/35 bg-stone-50/25 text-[var(--kt-color-text-muted)] hover:bg-stone-100/30 opacity-65",
                    "disabled:border-stone-200 disabled:bg-stone-100 disabled:text-stone-400 disabled:opacity-50",
                  ].join(" ")}
                  onClick={() => onPickExample(example)}
                  disabled={isBusy || !canSend}
                  aria-pressed={isSelected}
                  title={example.text}
                >
                  {example.label}
                </button>
              );
            })}
          </div>
        </section>
      </div>

      {/* Non-Recommendation fields -- below the consultation flow, reduced
          visual prominence (Task 9). Kept (not removed): sessionNickname has
          a runtime dependency (anonymous snapshot restore, greeting copy in
          ConciergeClientFull). */}
      <div className="mt-6 space-y-3 border-t border-stone-200/20 pt-4">
        <div>
          <label
            htmlFor="concierge-entry-nickname"
            className="mb-0.5 block text-[11px] font-medium text-[var(--kt-color-text-muted)] opacity-65"
          >
            呼び名（任意）
          </label>
          <input
            id="concierge-entry-nickname"
            type="text"
            value={sessionState.sessionNickname ?? ""}
            onChange={(e) => setSessionNickname(e.target.value)}
            placeholder="例: なまえ"
            className="w-full rounded-2xl border border-stone-200/30 bg-stone-50/25 px-2.5 py-1.5 text-sm text-[var(--kt-color-text-primary)] placeholder:text-stone-400 placeholder:opacity-60"
            maxLength={20}
          />
        </div>

        {!canSaveConciergeThread && !isUiPaywall ? (
          <div className="rounded-[var(--kt-radius-panel)] border border-amber-200/50 bg-amber-50/50 px-3 py-2 text-xs text-amber-800 opacity-85">
            <p>未ログインでも相談できます。保存にはログインが必要です。</p>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                className="rounded-lg bg-[var(--kt-color-surface-emphasis)] px-2.5 py-1 text-xs font-medium text-[var(--kt-color-text-inverse)] hover:bg-[var(--kt-color-surface-emphasis-hover)]"
                onClick={() => redirectToAuth("login")}
              >
                ログイン
              </button>
              <button
                type="button"
                className="rounded-lg border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-stone-100"
                onClick={() => redirectToAuth("register")}
              >
                新規登録
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </>
  );
}
