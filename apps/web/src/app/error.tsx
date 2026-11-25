// apps/web/src/app/error.tsx
"use client";

import { useEffect } from "react";
import { clientLog } from "@/lib/client/logging";
import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    clientLog("error", "APP_ERROR_BOUNDARY", {
      message: error.message,
      digest: error.digest ?? null,
      // stack は環境で出たり出なかったりするけど、取れるなら便利
      stack: error.stack ?? null,
    });
  }, [error]);

  // Root の error boundary は Route Segment の layout より外側で描画されるため、
  // 世界観フレームをここで持つ（1画面1 backdrop）。
  return (
    <WorldviewFrame variant="standard">
      <main className="mx-auto max-w-md p-6 space-y-3">
        <h1 className="text-lg font-bold text-[var(--kt-color-text-primary)]">エラーが発生しました</h1>
        <pre className="text-xs whitespace-pre-wrap rounded-xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-3 text-[var(--kt-color-text-secondary)]">
          {error.message}
          {error.digest ? `\n\ndigest: ${error.digest}` : ""}
        </pre>
        <button
          className="rounded-md bg-[var(--kt-color-surface-emphasis)] px-3 py-2 text-xs text-[var(--kt-color-text-primary)] hover:bg-[var(--kt-color-surface-emphasis-hover)]"
          onClick={() => reset()}
        >
          再試行
        </button>
      </main>
    </WorldviewFrame>
  );
}
