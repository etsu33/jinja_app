"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { SectionCard } from "@/components/layout/SectionCard";
import GoshuinUploadForm from "./GoshuinUploadForm";
import MyGoshuinList from "./MyGoshuinList";
import { useMyGoshuin } from "@/features/mypage/hooks";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { useRouter } from "next/navigation";

import { buildLoginHref } from "@/lib/nav/login";
import { getMyShrineSubmissions } from "@/lib/api/shrineSubmissions";
import type { ShrineSubmissionStatus } from "@/features/shrine-submission/types";

const submissionStatusLabel: Record<ShrineSubmissionStatus, string> = {
  pending: "審査中",
  approved: "公開済み",
  rejected: "見送り",
};

const submissionStatusClass: Record<ShrineSubmissionStatus, string> = {
  pending: "border-amber-200 bg-amber-50 text-amber-800",
  approved: "border-emerald-200 bg-emerald-50 text-emerald-800",
  rejected: "border-rose-200 bg-rose-50 text-rose-800",
};

export default function MyPageScreen() {
  const router = useRouter();
  const { user, isLoggedIn, loading, logout } = useAuth();

  const goshuinEnabled = !loading && isLoggedIn && !!user;

  const [submissions, setSubmissions] = useState<Awaited<ReturnType<typeof getMyShrineSubmissions>>>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [submissionsError, setSubmissionsError] = useState<string | null>(null);

  const sp = useSearchParams();

  const shrineId = Number(sp.get("shrine") ?? "");
  const hasShrine = Number.isFinite(shrineId) && shrineId > 0;
  const submitted = sp.get("submitted");
  const submissionStatus = sp.get("status");
  const submittedShrineName = sp.get("name")?.trim() ?? "";
  const showSubmissionPendingBanner = submitted === "1" && submissionStatus === "pending";

  const {
    items,
    loading: goshuinLoading,
    error: goshuinError,
    addItem,
    removeItem,
    toggleVisibility,
  } = useMyGoshuin({ enabled: goshuinEnabled });

  useEffect(() => {
    if (loading || !isLoggedIn || !user) {
      setSubmissions([]);
      setSubmissionsError(null);
      setSubmissionsLoading(false);
      return;
    }

    let active = true;
    setSubmissionsLoading(true);
    setSubmissionsError(null);

    getMyShrineSubmissions()
      .then((items) => {
        if (!active) return;
        setSubmissions(items);
      })
      .catch(() => {
        if (!active) return;
        setSubmissionsError("投稿した神社を読み込めませんでした。");
      })
      .finally(() => {
        if (!active) return;
        setSubmissionsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [loading, isLoggedIn, user]);

  if (loading) {
    return (
      <div role="status" aria-live="polite" className="py-6">
        読み込み中…
      </div>
    );
  }

  if (!isLoggedIn || !user) {
    return (
      <main className="mx-auto max-w-3xl p-6">
        <h1 className="mb-4 text-xl font-bold">御朱印帳</h1>
        <div className="rounded-lg border bg-white p-6">
          <p className="mb-3">御朱印帳を利用するにはログインしてください。</p>
          <Link
            className="inline-block rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            href={buildLoginHref(hasShrine ? `/mypage?tab=goshuin&shrine=${shrineId}` : `/mypage?tab=goshuin`)}
          >
            ログインへ
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold">御朱印帳</h1>

        <button
          type="button"
          onClick={async () => {
            await logout();
            router.replace("/");
          }}
          className="rounded-full border bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          ログアウト
        </button>
      </header>

      {showSubmissionPendingBanner && (
        <div
          className="whitespace-pre-line rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          role="status"
          aria-live="polite"
        >
          {submittedShrineName
            ? `「${submittedShrineName}」の投稿を受け付けました。\n現在審査中のため、公開検索にはまだ表示されません。\n審査完了後に公開されます。`
            : "投稿を受け付けました。\n現在審査中のため、公開検索にはまだ表示されません。\n審査完了後に公開されます。"}
        </div>
      )}

      <div className="space-y-4">
        <SectionCard
          title="投稿した神社"
          description="追加申請した神社の審査状態を確認できます。公開済みになると検索から確認できます。"
        >
          {submissionsLoading ? (
            <p className="text-sm text-slate-500">投稿履歴を読み込み中…</p>
          ) : submissionsError ? (
            <p className="text-sm text-rose-700">{submissionsError}</p>
          ) : submissions.length === 0 ? (
            <p className="text-sm text-slate-500">投稿した神社はまだありません。</p>
          ) : (
            <div className="space-y-3">
              {submissions.map((submission) => {
                const searchHref = `/shrines?q=${encodeURIComponent(submission.name)}`;

                return (
                  <article key={submission.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <h3 className="text-sm font-semibold text-slate-900">{submission.name}</h3>
                        <p className="text-xs leading-6 text-slate-500">{submission.address}</p>
                      </div>
                      <span
                        className={`w-fit rounded-full border px-2 py-0.5 text-xs font-medium ${submissionStatusClass[submission.status]}`}
                      >
                        {submissionStatusLabel[submission.status]}
                      </span>
                    </div>

                    {submission.status === "pending" && (
                      <p className="mt-3 text-xs leading-6 text-slate-600">
                        現在審査中です。公開検索にはまだ表示されません。
                      </p>
                    )}

                    {submission.status === "approved" && (
                      <div className="mt-3">
                        <Link className="text-xs font-medium text-emerald-700 hover:underline" href={searchHref}>
                          公開検索で確認する
                        </Link>
                      </div>
                    )}

                    {submission.status === "rejected" && submission.review_comment && (
                      <p className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-xs leading-6 text-rose-800">
                        {submission.review_comment}
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </SectionCard>

        <div id="goshuin-upload">
          <SectionCard
            title="御朱印アップロード"
            description="御朱印画像（推奨サイズ：5MB 以下）をアップロードできます。画像とタイトルを選んで登録してください。"
          >
            <GoshuinUploadForm
              onUploaded={(created) => {
                addItem(created);
                const href = hasShrine
                  ? buildShrineHref(shrineId, { query: { toast: "goshuin_saved" }, hash: "goshuins" })
                  : `/mypage?tab=goshuin&toast=goshuin_saved#goshuin-upload`;

                router.push(href);
              }}
            />
          </SectionCard>
        </div>

        <SectionCard title="登録済みの御朱印">
          <MyGoshuinList
            items={items}
            loading={goshuinLoading}
            error={goshuinError}
            onDelete={removeItem}
            onToggleVisibility={toggleVisibility}
            navigateOnCardClick
          />
        </SectionCard>
      </div>
    </main>
  );
}
