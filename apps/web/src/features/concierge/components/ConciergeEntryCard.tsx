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
  onPickExample: (text: string) => void;
  isBusy: boolean;
  canSend: boolean;
  onSubmit: () => void;
  onClear: () => void;
};

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
          <p className="text-[9px] font-normal tracking-[0.24em] text-stone-500 opacity-70">KAMI MUSUBI GUIDE</p>
          <h1 className="mt-1.5 text-lg font-medium leading-7 text-stone-900">静かに言葉を整える</h1>
        </div>
        <p className="text-sm leading-6 text-stone-500 opacity-85">
          {displayName ? `${displayLabel}さんの言葉を、ゆっくり整えます。` : "言葉を、ゆっくり整えます。"}
        </p>
      </div>

      <div className="mt-4">
        <label
          htmlFor="concierge-entry-nickname"
          className="mb-0.5 block text-[11px] font-medium text-stone-500 opacity-65"
        >
          呼び名（任意）
        </label>
        <input
          id="concierge-entry-nickname"
          type="text"
          value={sessionState.sessionNickname ?? ""}
          onChange={(e) => setSessionNickname(e.target.value)}
          placeholder="例: なまえ"
          className="w-full rounded-2xl border border-stone-200/30 bg-stone-50/25 px-2.5 py-1.5 text-sm text-stone-900 placeholder:text-stone-400 placeholder:opacity-60"
          maxLength={20}
        />
      </div>

      {!canSaveConciergeThread && !isUiPaywall ? (
        <div className="mt-3 rounded-xl border border-amber-200/50 bg-amber-50/50 px-3 py-2 text-xs text-amber-800 opacity-85">
          <p>未ログインでも検索できます。保存にはログインが必要です。</p>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs font-medium text-white hover:bg-slate-900"
              onClick={() => redirectToAuth("login")}
            >
              ログイン
            </button>
            <button
              type="button"
              className="rounded-lg border border-slate-200 bg-stone-50 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-stone-100"
              onClick={() => redirectToAuth("register")}
            >
              新規登録
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-5 space-y-4">
        <div>
          <label
            htmlFor="concierge-input"
            className="mb-0.5 block text-[11px] font-medium text-stone-500 opacity-65"
          >
            今の言葉を、静かに書く
          </label>
          <textarea
            id="concierge-input"
            value={needText}
            onChange={(e) => setNeedText(e.target.value)}
            placeholder="例：気持ちを切り替えたい、静かな時間を持ちたい"
            rows={4}
            className="w-full rounded-3xl border border-stone-200/20 bg-stone-50/30 px-3 py-2.5 text-sm leading-7 text-stone-900 outline-none transition placeholder:text-stone-400 placeholder:opacity-60 focus:border-emerald-200/40 focus:ring-1 focus:ring-emerald-100/40"
          />
        </div>

        <div>
          <p className="text-[11px] font-medium text-stone-500 opacity-75">ことばのきっかけ</p>
          <div className="mt-2.5 flex flex-wrap gap-2">
            {feelExamples.map((example) => {
              const isSelected = needText.trim() === example.text;
              return (
                <button
                  key={example.label}
                  type="button"
                  className={[
                    "rounded-full border px-2.5 py-1 text-xs font-normal transition active:scale-[0.98]",
                    isSelected
                      ? "border-emerald-200/60 bg-emerald-50/40 text-emerald-700"
                      : "border-stone-200/35 bg-stone-50/25 text-stone-500 hover:bg-stone-100/30 opacity-65",
                    "disabled:border-stone-200 disabled:bg-stone-100 disabled:text-stone-400 disabled:opacity-50",
                  ].join(" ")}
                  onClick={() => onPickExample(example.text)}
                  disabled={isBusy || !canSend}
                  aria-pressed={isSelected}
                  title={example.text}
                >
                  {example.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-1.5 sm:flex-row">
          <button
            type="button"
            className="w-full rounded-full border border-emerald-200/40 bg-emerald-50/50 px-3 py-2 text-xs font-medium text-emerald-700 transition hover:bg-emerald-100/40 disabled:cursor-not-allowed disabled:opacity-40"
            disabled={isBusy || !needText.trim() || !canSend}
            onClick={onSubmit}
          >
            言葉を整える
          </button>

          <button
            type="button"
            className="w-full rounded-full border border-stone-200/30 bg-stone-50/25 px-3 py-2 text-xs font-medium text-stone-500 transition hover:bg-stone-100/30 disabled:cursor-not-allowed disabled:border-stone-200 disabled:bg-stone-100 disabled:text-stone-400 disabled:opacity-40"
            disabled={isBusy}
            onClick={onClear}
          >
            クリア
          </button>
        </div>
      </div>
    </>
  );
}
