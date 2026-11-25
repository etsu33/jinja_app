// apps/web/src/features/concierge/components/ConciergeAutoSubmitPending.tsx
//
// Home → /concierge?theme=... の自動送信ルートで、結果が出るまで出し続ける待機表示。
// route の Suspense fallback（chunk 読み込み中）と、ConciergeClientFull の
// hydrate 前 / 自動送信前 / 送信中の全区間で同じ見た目を使い、
// 空の本文や入力フォームの一瞬の表示を挟まないためのもの。
//
// hooks を持たない表示専用 component。入力 UI（textarea / submit）は出さない。

type SearchParamsLike = { get(name: string): string | null };

// 自動送信の対象になる theme を返す。対象外なら ""。
// tid が正の整数なら thread 復元ルート（ConciergeClientFull の tidNum と同じ判定）なので対象外。
export function readAutoSubmitTheme(sp: SearchParamsLike): string {
  const theme = (sp.get("theme") ?? "").trim();
  if (!theme) return "";
  const rawTid = (sp.get("tid") ?? "").trim();
  const tid = Number(rawTid);
  if (rawTid && Number.isInteger(tid) && tid > 0) return "";
  return theme;
}

const CARD_CLASS =
  "rounded-3xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-6";

// ConciergeLayout（embedMode=false）の外枠と同じ class。
// route fallback は ConciergeLayout の外で描画されるため、ここで同じ枠を再現し
// fallback → client 描画の切り替えで位置がずれないようにする。
const LAYOUT_ROOT_CLASS = "mx-auto max-w-4xl w-full min-w-0 flex flex-col px-4 flex-1 min-h-0 overflow-hidden";
const LAYOUT_MAIN_CLASS = "flex flex-col flex-1 min-h-0 w-full h-full";

export function ConciergeAutoSubmitPendingPanel({ theme }: { theme: string }) {
  return (
    // min-h は ShrineDetailShell と同じ考え方。待機中に footer が本文直下へ上がってこないようにする。
    <div className="min-h-[calc(100dvh-64px)] px-4 pt-6" data-testid="concierge-auto-submit-pending">
      <div className={CARD_CLASS} role="status" aria-live="polite" aria-busy="true">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--kt-color-text-muted)]">KAMI MUSUBI GUIDE</p>
        <p className="mt-3 text-base font-semibold text-[var(--kt-color-text-primary)]">相談をもとに、神社を選んでいます…</p>
        {theme ? (
          <p className="mt-3 break-words rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] px-4 py-3 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            {theme}
          </p>
        ) : null}
        <div aria-hidden="true" className="mt-5 space-y-3 animate-pulse motion-reduce:animate-none">
          <div className="h-4 w-2/3 rounded-full bg-[var(--kt-color-surface-emphasis)]" />
          <div className="h-3 w-full rounded-full bg-[var(--kt-color-surface-emphasis)]" />
          <div className="h-3 w-5/6 rounded-full bg-[var(--kt-color-surface-emphasis)]" />
        </div>
      </div>
    </div>
  );
}

// route の Suspense fallback 用。ConciergeLayout と同じ外枠で包む。
export function ConciergeAutoSubmitPendingFrame({ theme }: { theme: string }) {
  return (
    <div className={LAYOUT_ROOT_CLASS}>
      <main className={LAYOUT_MAIN_CLASS}>
        <ConciergeAutoSubmitPendingPanel theme={theme} />
      </main>
    </div>
  );
}
