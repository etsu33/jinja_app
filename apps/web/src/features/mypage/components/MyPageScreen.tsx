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
      <main className="mx-auto max-w-3xl p-6 text-[var(--kt-color-text-primary)]">
        <h1 className="mb-4 text-xl font-semibold">マイページ</h1>
        <div className="rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-6">
          <p className="mb-3 text-sm text-[var(--kt-color-text-secondary)]">御朱印帳はログイン後に使えます。</p>
          <Link
            className="inline-block rounded-full border border-[var(--kt-color-action-primary)] bg-[var(--kt-color-action-primary)] px-4 py-2 text-sm text-[var(--kt-color-action-primary-text)] transition hover:bg-[var(--kt-color-action-primary-hover)]"
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
        <h1 className="text-xl font-semibold text-[var(--kt-color-text-primary)]">マイページ</h1>

        <button
          type="button"
          onClick={async () => {
            await logout();
            router.replace("/");
          }}
          className="rounded-full border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-3 py-1.5 text-xs font-medium text-[var(--kt-color-text-muted)] transition hover:bg-[var(--kt-color-background-subtle)] hover:text-[var(--kt-color-text-secondary)]"
        >
          ログアウト
        </button>
      </header>

      {showSubmissionPendingBanner && (
        <div
          className="whitespace-pre-line rounded-xl border border-[var(--kt-color-action-primary)] bg-[var(--kt-color-background-subtle)] px-4 py-3 text-sm leading-6 text-[var(--kt-color-action-primary)]"
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
              <p className="text-sm text-[var(--kt-color-text-secondary)]">読み込み中…</p>
            ) : submissionsError ? (
              <p className="text-sm text-[var(--kt-color-status-error)]">{submissionsError}</p>
            ) : submissions.length === 0 ? (
              <p className="text-sm text-[var(--kt-color-text-secondary)]">投稿した神社はまだありません。</p>
            ) : (
              <div className="space-y-5">
                <section className="space-y-3">
                  <h3 className="text-sm font-medium text-[var(--kt-color-text-secondary)]">公開済み</h3>

                  {approvedSubmissions.length === 0 ? (
                    <p className="rounded-xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4 text-sm text-[var(--kt-color-text-secondary)]">
                      まだ公開された神社はありません。
                    </p>
                  ) : (
                    approvedSubmissions.map((submission) => {
                      const searchHref = `/shrines?q=${encodeURIComponent(submission.name)}`;

                      return (
                        <div key={submission.id} className="rounded-xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-medium text-[var(--kt-color-text-primary)]">{submission.name}</p>
                              <p className="mt-1 text-xs text-[var(--kt-color-text-muted)]">{submission.address}</p>
                            </div>
                            <span className="rounded-full border border-[var(--kt-color-status-success-border)] bg-[var(--kt-color-status-success-surface)] px-2 py-1 text-xs font-medium text-[var(--kt-color-status-success-text)]">
                              公開済み
                            </span>
                          </div>

                          <p className="mt-3 text-xs leading-6 text-[var(--kt-color-text-muted)]">検索から確認できます。</p>

                          <Link
                            className="mt-2 inline-flex w-fit items-center rounded-full border border-[var(--kt-color-action-primary)] bg-[var(--kt-color-action-primary)] px-3 py-1.5 text-xs font-medium text-[var(--kt-color-action-primary-text)] transition hover:bg-[var(--kt-color-action-primary-hover)]"
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
                    <h3 className="text-sm font-medium text-[var(--kt-color-text-secondary)]">審査中</h3>

                    {pendingSubmissions.map((submission) => (
                      <div key={submission.id} className="rounded-xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-[var(--kt-color-text-primary)]">{submission.name}</p>
                            <p className="mt-1 text-xs text-[var(--kt-color-text-muted)]">{submission.address}</p>
                          </div>
                          <span className="rounded-full border border-[var(--kt-color-status-warning)] bg-[var(--kt-color-background-subtle)] px-2 py-1 text-xs font-medium text-[var(--kt-color-status-warning)]">
                            審査中
                          </span>
                        </div>

                        <p className="mt-3 text-xs leading-6 text-[var(--kt-color-text-muted)]">公開までしばらくお待ちください。</p>
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
