import Link from "next/link";

export default function BillingCancelPage() {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="text-xl font-semibold text-slate-900">プレミアム登録を中断しました</h1>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        決済は完了していません。必要になったタイミングで、もう一度登録を開始できます。
      </p>

      <div className="mt-6 flex flex-col gap-2">
        <Link
          href="/billing/upgrade"
          className="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
        >
          プレミアム登録へ戻る
        </Link>
        <Link
          href="/concierge"
          className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
        >
          コンシェルジュへ戻る
        </Link>
      </div>
    </div>
  );
}
