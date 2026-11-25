// apps/web/src/app/shrines/[id]/loading.tsx
//
// /shrines/[id] の Route loading boundary。
// Page は server fetch を完了するまで本文を返さないため、その間に
// ShrineDetailShell と同じ骨格（閉じる / タイトル / 操作 / 本文）を先に出す
// （docs/audit/shrine-detail-transition-flash.md）。
//
// - 世界観フレームは app/shrines/layout.tsx が持つ。ここでは重ねない
// - 外枠は ShrineDetailShell の <main> と同じ class にし、本文到着時の高さの差を抑える
// - 実データ風の文言（神社名・ご利益・推薦理由など）は出さない
// - 読み上げは status の1文だけにし、骨格の図形は aria-hidden にする
// - この boundary は /shrines/[id]/goshuins にも適用される（同じ Shell を使う画面）

const BAR = "rounded-full bg-[var(--kt-color-surface-emphasis)]";
const CARD =
  "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-5 shadow-[var(--kt-shadow-medium)]";

export default function ShrineDetailLoading() {
  return (
    <main
      className="mx-auto min-h-[calc(100vh-64px)] max-w-md space-y-4 p-4 lg:max-w-2xl"
      data-testid="shrine-detail-loading"
    >
      <p role="status" aria-live="polite" className="sr-only">
        神社の情報を読み込み中です
      </p>

      <div aria-hidden="true" className="space-y-4 animate-pulse motion-reduce:animate-none">
        {/* header: 閉じる / タイトル / 右側の固定幅 */}
        <div data-skeleton-region="header" className="flex items-center justify-between">
          <div className={`h-4 w-14 shrink-0 ${BAR}`} />
          <div className="flex min-w-0 flex-1 justify-center px-2">
            <div className={`h-4 w-32 ${BAR}`} />
          </div>
          <div className="w-[64px]" />
        </div>

        {/* 操作: 経路案内 CTA */}
        <div data-skeleton-region="actions" className={CARD}>
          <div className={`mb-3 h-3.5 w-12 ${BAR}`} />
          <div className="min-h-[44px] w-full rounded-[var(--kt-radius-panel)] bg-[var(--kt-color-surface-emphasis)]" />
        </div>

        {/* 神社名と補足情報 */}
        <div data-skeleton-region="title" className={`${CARD} space-y-3`}>
          <div className={`h-7 w-2/3 ${BAR}`} />
          <div className={`h-3 w-24 ${BAR}`} />
          <div className={`h-4 w-full ${BAR}`} />
          <div className={`h-3 w-40 ${BAR}`} />
        </div>

        {/* 本文セクション */}
        {[0, 1].map((i) => (
          <div key={i} data-skeleton-region="section" className={`${CARD} space-y-3`}>
            <div className={`h-4 w-28 ${BAR}`} />
            <div className={`h-3 w-full ${BAR}`} />
            <div className={`h-3 w-11/12 ${BAR}`} />
            <div className={`h-3 w-3/4 ${BAR}`} />
          </div>
        ))}
      </div>
    </main>
  );
}
