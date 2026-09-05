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
      <main className="mx-auto max-w-3xl p-6 text-[var(--kt-color-text-primary)]">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <p className="text-sm text-[var(--kt-color-text-muted)]">読み込み中…</p>
      </main>
    );
  }

  if (!isLoggedIn) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-[var(--kt-color-text-primary)]">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-6">
          <p className="mb-3 text-sm text-[var(--kt-color-text-secondary)]">ログインすると、これまでの相談履歴を見返せます。</p>
          <Link
            href={buildLoginHref("/mypage/history")}
            className="inline-block rounded-full bg-[var(--kt-color-action-primary)] px-4 py-2 text-sm text-[var(--kt-color-action-primary-text)] transition hover:bg-[var(--kt-color-action-primary-hover)]"
          >
            ログインへ
          </Link>
        </div>
      </main>
    );
  }

  if (fetchFailed) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-[var(--kt-color-text-primary)]">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-6">
          <p className="mb-3 text-sm text-[var(--kt-color-status-error)]">相談履歴を読み込めませんでした。</p>
          <button
            type="button"
            onClick={() => router.refresh()}
            className="inline-block rounded-full border border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] px-4 py-2 text-sm text-[var(--kt-color-text-primary)] transition hover:bg-[var(--kt-color-background-subtle)]"
          >
            もう一度読み込む
          </button>
        </div>
      </main>
    );
  }

  if (initialThreads.length === 0) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-[var(--kt-color-text-primary)]">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-6">
          <p className="mb-3 text-sm text-[var(--kt-color-text-secondary)]">まだ相談履歴がありません。</p>
          <Link
            href="/concierge"
            className="inline-block rounded-full bg-[var(--kt-color-action-primary)] px-4 py-2 text-sm text-[var(--kt-color-action-primary-text)] transition hover:bg-[var(--kt-color-action-primary-hover)]"
          >
            コンシェルジュに相談する
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl p-6 text-[var(--kt-color-text-primary)]">
      <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
      <ul className="space-y-3">
        {initialThreads.map((thread, idx) => (
          <li key={thread.id}>
            <Link
              href={`/mypage/history/${thread.id}`}
              onClick={() =>
                trackConsultationHistoryDetailOpened({ threadId: thread.id, position: idx + 1 })
              }
              className="block rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-4 transition hover:bg-[var(--kt-color-surface-default)]"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold text-[var(--kt-color-text-primary)]">{thread.title?.trim() || "相談タイトル未設定"}</p>
                <p className="shrink-0 text-xs text-[var(--kt-color-text-muted)]">{formatDate(thread.last_message_at)}</p>
              </div>
              <p className="mt-1 line-clamp-2 text-sm text-[var(--kt-color-text-secondary)]">{normalizePreview(thread.last_message)}</p>
              <p className="mt-2 text-xs text-[var(--kt-color-text-muted)]">{thread.message_count}件のやりとり</p>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
