// apps/web/src/app/map/loading.tsx
export default function MapLoading() {
  return (
    <main className="p-4 max-w-5xl mx-auto space-y-4">
      <div className="h-4 w-24 rounded bg-[var(--kt-color-surface-emphasis)]" />
      <div className="grid gap-3 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-24 rounded-2xl border bg-[var(--kt-color-surface-default)] shadow-sm p-3 flex flex-col justify-between animate-pulse"
          >
            <div className="h-3 w-20 rounded bg-[var(--kt-color-surface-emphasis)]" />
            <div className="h-2 w-32 rounded bg-[var(--kt-color-surface-elevated)]" />
          </div>
        ))}
      </div>

      <div className="w-full h-[60vh] rounded-xl overflow-hidden bg-[var(--kt-color-surface-elevated)] flex items-center justify-center text-sm text-[var(--kt-color-text-muted)]">
        地図を読み込み中…
      </div>

      <div className="max-h-64 overflow-y-auto rounded-lg border bg-[var(--kt-color-surface-default)] p-3 text-xs text-[var(--kt-color-text-muted)]">
        神社リストを読み込み中…
      </div>
    </main>
  );
}
