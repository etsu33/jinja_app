// apps/web/src/app/goshuin/new/page.tsx
import { Suspense } from "react";
import GoshuinNewClient from "./GoshuinNewClient";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-4 text-xs text-[var(--kt-color-text-muted)]">読み込み中…</div>}>
      <GoshuinNewClient />
    </Suspense>
  );
}
