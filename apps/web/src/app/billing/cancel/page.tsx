import Link from "next/link";

export default function BillingCancelPage() {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="text-xl font-semibold text-[var(--kt-color-text-primary)]">プレミアム登録を中断しました</h1>
      <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
        決済は完了していません。必要になったタイミングで、もう一度登録を開始できます。
      </p>

      <div className="mt-6 flex flex-col gap-2">
        <Link
          href="/billing/upgrade"
          className="inline-flex items-center justify-center rounded-md bg-[var(--kt-color-surface-emphasis)] px-4 py-3 text-sm font-semibold text-[var(--kt-color-text-primary)]"
        >
          プレミアム登録へ戻る
        </Link>
        <Link
          href="/concierge"
          className="inline-flex items-center justify-center rounded-md border border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] px-4 py-3 text-sm font-semibold text-[var(--kt-color-text-primary)]"
        >
          コンシェルジュへ戻る
        </Link>
      </div>
    </div>
  );
}
