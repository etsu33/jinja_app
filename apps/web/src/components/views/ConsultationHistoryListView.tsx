"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildLoginHref } from "@/lib/nav/login";
import {
  trackConsultationHistoryDetailOpened,
  trackConsultationHistoryListViewed,
} from "@/lib/analytics/consultationHistoryEvents";
import type { ConciergeThread } from "@/lib/api/concierge/types";

type Props = {
  initialThreads: ConciergeThread[];
  fetchFailed: boolean;
};

function formatDate(value: string | null | undefined): string {
  if (!value) return "日付未記録";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日付未記録";
  return date.toLocaleDateString("ja-JP", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function normalizePreview(value: string | null | undefined): string {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text || "相談内容はまだ記録されていません。";
}

export default function ConsultationHistoryListView({ initialThreads, fetchFailed }: Props) {
  const { loading, isLoggedIn } = useAuth();
  const router = useRouter();

  // 認証済みかつ取得成功で一覧が表示可能になった時点で1回だけ発火する(0件でも発火する)。
  // 再レンダーでの重複防止はhasTrackedListViewRefで行う。
  const hasTrackedListViewRef = useRef(false);
  useEffect(() => {
    if (loading || !isLoggedIn || fetchFailed) return;
    if (hasTrackedListViewRef.current) return;
    hasTrackedListViewRef.current = true;
    trackConsultationHistoryListViewed({ historyCount: initialThreads.length });
  }, [loading, isLoggedIn, fetchFailed, initialThreads.length]);

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <p className="text-sm text-stone-500">読み込み中…</p>
      </main>
    );
  }

  if (!isLoggedIn) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-6">
          <p className="mb-3 text-sm text-stone-600">ログインすると、これまでの相談履歴を見返せます。</p>
          <Link
            href={buildLoginHref("/mypage/history")}
            className="inline-block rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-2 text-sm text-white transition hover:bg-emerald-900"
          >
            ログインへ
          </Link>
        </div>
      </main>
    );
  }

  if (fetchFailed) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-rose-200/40 bg-rose-50/40 p-6">
          <p className="mb-3 text-sm text-rose-700">相談履歴を読み込めませんでした。</p>
          <button
            type="button"
            onClick={() => router.refresh()}
            className="inline-block rounded-full border border-stone-300 bg-white px-4 py-2 text-sm text-stone-700 transition hover:bg-stone-50"
          >
            もう一度読み込む
          </button>
        </div>
      </main>
    );
  }

  if (initialThreads.length === 0) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-6">
          <p className="mb-3 text-sm text-stone-600">まだ相談履歴がありません。</p>
          <Link
            href="/concierge"
            className="inline-block rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-2 text-sm text-white transition hover:bg-emerald-900"
          >
            コンシェルジュに相談する
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl p-6 text-stone-800">
      <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
      <ul className="space-y-3">
        {initialThreads.map((thread, idx) => (
          <li key={thread.id}>
            <Link
              href={`/mypage/history/${thread.id}`}
              onClick={() =>
                trackConsultationHistoryDetailOpened({ threadId: thread.id, position: idx + 1 })
              }
              className="block rounded-2xl border border-stone-200/20 bg-stone-50/30 p-4 transition hover:bg-stone-50/60"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold text-stone-900">{thread.title?.trim() || "相談タイトル未設定"}</p>
                <p className="shrink-0 text-xs text-stone-500">{formatDate(thread.last_message_at)}</p>
              </div>
              <p className="mt-1 line-clamp-2 text-sm text-stone-600">{normalizePreview(thread.last_message)}</p>
              <p className="mt-2 text-xs text-stone-400">{thread.message_count}件のやりとり</p>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
