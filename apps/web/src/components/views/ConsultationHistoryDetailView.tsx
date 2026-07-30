"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildLoginHref } from "@/lib/nav/login";
import { pickReasonV4FactText } from "@/features/concierge/reasonV4FactPriority";
import type { ConciergeThreadDetail, ConciergeRecommendation } from "@/lib/api/concierge/types";

type Props = {
  tid: string;
  thread: ConciergeThreadDetail | null;
  fetchFailed: boolean;
};

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "日時未記録";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日時未記録";
  return date.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const ACTION_STATE_LABEL: Record<string, string> = {
  saved: "気になる登録済み",
  visited: "参拝済み",
  reflected: "振り返り済み",
};

function extractShrineId(rec: ConciergeRecommendation): number | null {
  const raw = rec.shrine_id ?? rec.id;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

function RecommendationCard({ rec, tid }: { rec: ConciergeRecommendation; tid: string }) {
  const shrineId = extractShrineId(rec);
  const factText = pickReasonV4FactText(rec.recommendation_reason_v4_detail?.fact);
  const actionLabel = rec.action_state ? ACTION_STATE_LABEL[rec.action_state] : null;

  return (
    <li className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="font-semibold text-stone-900">{rec.name}</p>
        {actionLabel ? (
          <span className="shrink-0 rounded-full border border-emerald-700/20 bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800">
            {actionLabel}
          </span>
        ) : null}
      </div>
      {rec.address ? <p className="mt-1 text-xs text-stone-500">{rec.address}</p> : null}
      {factText ? <p className="mt-2 text-sm text-stone-700">{factText}</p> : null}
      {shrineId != null ? (
        <Link
          href={`/shrines/${shrineId}?ctx=concierge&tid=${encodeURIComponent(tid)}`}
          className="mt-3 inline-block text-xs font-semibold text-emerald-800 underline"
        >
          神社の詳細を見る
        </Link>
      ) : null}
    </li>
  );
}

export default function ConsultationHistoryDetailView({ tid, thread, fetchFailed }: Props) {
  const { loading, isLoggedIn } = useAuth();
  const router = useRouter();

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <p className="text-sm text-stone-500">読み込み中…</p>
      </main>
    );
  }

  if (!isLoggedIn) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">相談履歴</h1>
        <div className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-6">
          <p className="mb-3 text-sm text-stone-600">ログインすると、この相談履歴を見返せます。</p>
          <Link
            href={buildLoginHref(`/mypage/history/${tid}`)}
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

  if (!thread) {
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <div className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-6">
          <p className="text-sm text-stone-600">この相談は見つかりませんでした。</p>
          <Link href="/mypage/history" className="mt-3 inline-block text-sm text-emerald-800 underline">
            相談履歴の一覧へ戻る
          </Link>
        </div>
      </main>
    );
  }

  const recommendations = thread.recommendations_v2 ?? thread.recommendations ?? [];

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-6 text-stone-800">
      <div>
        <Link href="/mypage/history" className="text-xs text-stone-500 underline">
          ← 相談履歴の一覧へ
        </Link>
        <h1 className="mt-2 text-xl font-semibold">{thread.title?.trim() || "相談タイトル未設定"}</h1>
        <p className="mt-1 text-xs text-stone-500">{formatDateTime(thread.last_message_at)}</p>
      </div>

      {recommendations.length > 0 ? (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-stone-700">当時推薦された神社</h2>
          <ul className="space-y-3">
            {recommendations.map((rec, idx) => (
              <RecommendationCard key={`${extractShrineId(rec) ?? rec.name}-${idx}`} rec={rec} tid={tid} />
            ))}
          </ul>
        </section>
      ) : null}

      <section>
        <h2 className="mb-2 text-sm font-semibold text-stone-700">相談内容</h2>
        <ul className="space-y-2">
          {thread.messages.map((message) => (
            <li
              key={message.id}
              className={
                message.role === "user"
                  ? "rounded-2xl bg-emerald-50 p-3 text-sm text-stone-800"
                  : "rounded-2xl bg-stone-100 p-3 text-sm text-stone-800"
              }
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p className="mt-1 text-xs text-stone-400">{formatDateTime(message.created_at)}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
