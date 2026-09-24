import { Suspense } from "react";
import ConciergeClientFull from "../ConciergeClientFull";

function Fallback() {
  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="rounded-2xl border bg-[var(--kt-color-surface-default)] p-4 text-sm text-[var(--kt-color-text-secondary)]">読み込み中…</div>
    </main>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<Fallback />}>
      <ConciergeClientFull />
    </Suspense>
  );
}
