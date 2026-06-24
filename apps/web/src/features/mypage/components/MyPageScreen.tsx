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

type MyPageScreenProps = {
  activeTab: "goshuin" | "submissions";
};

export default function MyPageScreen({ activeTab }: MyPageScreenProps) {
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

  const approvedSubmissions = submissions.filter((submission) => submission.status === "approved");
  const pendingSubmissions = submissions.filter((submission) => submission.status === "pending");

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
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">マイページ</h1>
        <div className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-6">
          <p className="mb-3 text-sm text-stone-600">御朱印帳はログイン後に使えます。</p>
          <Link
            className="inline-block rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-2 text-sm text-white transition hover:bg-emerald-900"
            href={buildLoginHref(hasShrine ? `/mypage?tab=goshuin&shrine=${shrineId}` : `/mypage?tab=goshuin`)}
          >
            ログインへ
          </Link>
        </div>
      </main>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-stone-900">マイページ</h1>

        <button
          type="button"
          onClick={async () => {
            await logout();
            router.replace("/");
          }}
          className="rounded-full border border-stone-200/40 bg-stone-50/20 px-3 py-1.5 text-xs font-medium text-stone-500 transition hover:bg-stone-100/50 hover:text-stone-700"
        >
          ログアウト
        </button>
      </header>

      {showSubmissionPendingBanner && (
        <div
          className="whitespace-pre-line rounded-xl border border-emerald-700/10 bg-emerald-50/40 px-4 py-3 text-sm leading-6 text-emerald-900/80"
          role="status"
          aria-live="polite"
        >
          {submittedShrineName
            ? `「${submittedShrineName}」の投稿を受け付けました。\n公開までしばらくお待ちください。`
            : "投稿を受け付けました。\n公開までしばらくお待ちください。"}
        </div>
      )}

      <div className="space-y-4">
        {activeTab === "submissions" && (
          <SectionCard
            title="投稿状況"
            description="投稿した神社の状態を確認できます。"
          >
            {submissionsLoading ? (
              <p className="text-sm text-stone-500">読み込み中…</p>
            ) : submissionsError ? (
              <p className="text-sm text-rose-700">{submissionsError}</p>
            ) : submissions.length === 0 ? (
              <p className="text-sm text-stone-500">投稿した神社はまだありません。</p>
            ) : (
              <div className="space-y-5">
                <section className="space-y-3">
                  <h3 className="text-sm font-medium text-stone-700">公開済み</h3>

                  {approvedSubmissions.length === 0 ? (
                    <p className="rounded-xl border border-stone-200/20 bg-stone-50/30 p-4 text-sm text-stone-500">
                      まだ公開された神社はありません。
                    </p>
                  ) : (
                    approvedSubmissions.map((submission) => {
                      const searchHref = `/shrines?q=${encodeURIComponent(submission.name)}`;

                      return (
                        <div key={submission.id} className="rounded-xl border border-stone-200/20 bg-stone-50/30 p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-medium text-stone-900">{submission.name}</p>
                              <p className="mt-1 text-xs text-stone-500">{submission.address}</p>
                            </div>
                            <span className="rounded-full border border-emerald-700/10 bg-emerald-50/50 px-2 py-1 text-xs font-medium text-emerald-800/80">
                              公開済み
                            </span>
                          </div>

                          <p className="mt-3 text-xs leading-6 text-stone-500">検索から確認できます。</p>

                          <Link
                            className="mt-2 inline-flex w-fit items-center rounded-full border border-emerald-700/20 bg-emerald-800 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-900"
                            href={searchHref}
                          >
                            検索で見る
                          </Link>
                        </div>
                      );
                    })
                  )}
                </section>

                {pendingSubmissions.length > 0 && (
                  <section className="space-y-3">
                    <h3 className="text-sm font-medium text-stone-700">審査中</h3>

                    {pendingSubmissions.map((submission) => (
                      <div key={submission.id} className="rounded-xl border border-stone-200/20 bg-stone-50/30 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-stone-900">{submission.name}</p>
                            <p className="mt-1 text-xs text-stone-500">{submission.address}</p>
                          </div>
                          <span className="rounded-full border border-stone-300/30 bg-stone-100/50 px-2 py-1 text-xs font-medium text-stone-600">
                            審査中
                          </span>
                        </div>

                        <p className="mt-3 text-xs leading-6 text-stone-500">公開までしばらくお待ちください。</p>
                      </div>
                    ))}
                  </section>
                )}
              </div>
            )}
          </SectionCard>
        )}

        {activeTab === "goshuin" && (
          <section className="space-y-4" aria-labelledby="goshuin-section-title">
            <div className="space-y-1">
              <h2 id="goshuin-section-title" className="text-lg font-semibold text-stone-900">
                御朱印帳
              </h2>
              <p className="text-sm text-stone-500">御朱印を静かに残します。</p>
            </div>

            <div id="goshuin-upload">
              <SectionCard
                title="御朱印アップロード"
                description="画像を選んで登録します。"
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
          </section>
        )}
      </div>
    </div>
  );
}
