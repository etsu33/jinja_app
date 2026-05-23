// apps/web/src/features/concierge/components/ThreadList.tsx
import Link from "next/link";
import type { ConciergeThread } from "@/lib/api/concierge";
import ThreadListItem from "./ThreadListItem";
import { trackRetentionEvent } from "@/lib/analytics/retentionEvents";

type Props = {
  threads: ConciergeThread[] | null | undefined;
  selectedId: string | null;
  loading: boolean;
  requiresLogin?: boolean;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
};

export function ThreadList({ threads, selectedId, loading, requiresLogin, onSelect, onCreateNew }: Props) {
  if (requiresLogin) {
    return (
      <div className="text-xs text-gray-500 px-3 py-2 space-y-2">
        <p>ログインすると、前回の相談や今の変化をあとから見返せます。</p>
        {/* ログイン導線を付けるならここでボタン or Link */}
      </div>
    );
  }
  const safeThreads = Array.isArray(threads)
    ? threads.filter((t): t is ConciergeThread => !!t && typeof (t as any).id === "number")
    : [];

  const handleSelectThread = (id: string) => {
    if (id === selectedId) return;

    trackRetentionEvent("thread_resume", {
      source: "thread_list",
      threadId: id,
    });

    onSelect(id);
  };

  // 未ログイン：履歴エリアは「ログイン特典」として説明だけ出す
  if (requiresLogin) {
    return (
      <div className="flex flex-col h-full px-3 py-2 text-xs text-gray-500">
        <p className="mb-2">ログインすると、前回の相談や今の変化をあとから見返せます。</p>
        <button
          type="button"
          onClick={onCreateNew}
          className="self-start mt-1 rounded-full border px-3 py-1 text-[11px]"
          disabled={loading}
        >
          ログインせずに新しい相談をはじめる
        </button>
      </div>
    );
  }

  // ログイン済み：通常の履歴リスト
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2">
        <p className="text-xs text-gray-600">相談履歴</p>
        <button
          type="button"
          onClick={onCreateNew}
          className="text-[11px] text-blue-600 underline disabled:text-gray-400"
          disabled={loading}
        >
          新しい相談
        </button>
      </div>

      <div className="mx-3 mb-2 rounded-2xl border border-amber-200 bg-amber-50/80 p-3 text-xs">
        <p className="font-semibold text-amber-950">前回からの変化をPremiumで見返せます。</p>
        <p className="mt-1 leading-5 text-slate-600">過去の相談と比べて、今の状態や選び方の変化を確認できます。</p>
        <Link
          href="/billing/upgrade"
          className="mt-2 inline-flex rounded-xl bg-amber-700 px-3 py-2 font-semibold text-white"
          onClick={() =>
            trackRetentionEvent("premium_history_click", {
              source: "thread_list",
              funnelStep: "history_comparison",
            })
          }
        >
          変化を見返す
        </Link>
      </div>

      {loading && <p className="px-3 pb-2 text-[11px] text-gray-400">読み込み中です…</p>}

      {!loading && safeThreads.length === 0 && (
        <p className="px-3 pb-2 text-[11px] text-gray-400">まだ相談履歴がありません。</p>
      )}

      <ul className="flex-1 space-y-1 overflow-y-auto px-1 pb-2">
        {safeThreads.map((t) => {
          const idStr = String((t as any).id);
          return (
            <ThreadListItem
              key={idStr}
              thread={t}
              selected={idStr === selectedId}
              onClick={() => handleSelectThread(idStr)}
            />
          );
        })}
      </ul>
    </div>
  );
}
