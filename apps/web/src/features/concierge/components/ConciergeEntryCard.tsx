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
      <div className="space-y-2 rounded-2xl border border-emerald-100 bg-gradient-to-b from-emerald-50/80 to-white px-4 py-3 shadow-sm shadow-emerald-900/5">
        <div>
          <p className="text-xs font-semibold tracking-[0.18em] text-emerald-700">神社コンシェルジュ</p>
          <h1 className="mt-1.5 text-lg font-semibold leading-7 text-slate-950">今の気持ちに合う神社を見つける</h1>
        </div>
        <p className="text-sm leading-6 text-slate-600">
          {displayName
            ? `${displayLabel}さんの今の状態をもとに、行き先の候補を静かに整理します。`
            : "今の状態をもとに、行き先の候補を静かに整理します。"}
        </p>
      </div>

      <div className="mt-3">
        <label htmlFor="concierge-entry-nickname" className="mb-1 block text-xs font-semibold text-slate-600">
          呼び名（任意）
        </label>
        <input
          id="concierge-entry-nickname"
          type="text"
          value={sessionState.sessionNickname ?? ""}
          onChange={(e) => setSessionNickname(e.target.value)}
          placeholder="例: えつこ"
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900"
          maxLength={20}
        />
      </div>

      {!canSaveConciergeThread && !isUiPaywall ? (
        <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          <p>未ログインでも検索できます。保存にはログインが必要です。</p>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white"
              onClick={() => redirectToAuth("login")}
            >
              ログイン
            </button>
            <button
              type="button"
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700"
              onClick={() => redirectToAuth("register")}
            >
              新規登録
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-3 space-y-3">
        <div>
          <label htmlFor="concierge-entry-need" className="mb-1 block text-xs font-semibold text-slate-600">
            今、何に迷っていますか？
          </label>
          <textarea
            id="concierge-entry-need"
            value={needText}
            onChange={(e) => setNeedText(e.target.value)}
            placeholder="例：金運を整えたい、気持ちを切り替えたい、静かな場所で参拝したい"
            rows={4}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm leading-6 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-300 focus:ring-4 focus:ring-emerald-100"
          />
        </div>

        <div>
          <p className="text-xs font-semibold text-slate-500">迷ったら選んでください</p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {feelExamples.map((example) => {
              const isSelected = needText.trim() === example.text;
              return (
                <button
                  key={example.label}
                  type="button"
                  className={[
                    "rounded-full border px-3 py-1.5 text-sm font-semibold transition shadow-sm active:scale-[0.98]",
                    isSelected
                      ? "border-emerald-600 bg-emerald-600 text-white"
                      : "border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-800 active:bg-emerald-100",
                    "disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none",
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

        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            className="w-full rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-900/20 transition hover:-translate-y-0.5 hover:bg-emerald-700 active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
            disabled={isBusy || !needText.trim() || !canSend}
            onClick={onSubmit}
          >
            今の気持ちに合う神社を探す
          </button>

          <button
            type="button"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-500 transition hover:bg-slate-50 hover:text-slate-700 active:bg-slate-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
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
