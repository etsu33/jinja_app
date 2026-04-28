"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { isSubmissionPendingParams } from "@/features/shrine-submission/lib/submissionReturnState";

import { ShrineCard } from "@/components/shrines/ShrineCard";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import { fetchShrines } from "@/lib/api/shrinesSearch";
import { getGoriyakuTags, type GoriyakuTag } from "@/lib/api/tags";
import { buildShrineListCardModel } from "@/lib/shrine/buildShrineListCardModel";

function ShrinesPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [q, setQ] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submittedName, setSubmittedName] = useState("");
  const [inputValue, setInputValue] = useState("");
  const showSubmissionPendingBanner = submitted;
  const shouldShowSearchResults = !showSubmissionPendingBanner;

  const [cards, setCards] = useState<ShrineCardAdapterProps[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [goriyakuTags, setGoriyakuTags] = useState<GoriyakuTag[]>([]);
  const [tagsLoading, setTagsLoading] = useState(false);
  const [tagsError, setTagsError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString());

    setQ((params.get("q") ?? "").trim());
    setSubmitted(isSubmissionPendingParams(params));
    setSubmittedName((params.get("name") ?? "").trim());
  }, [searchParams]);

  useEffect(() => {
    setInputValue(q);
  }, [q]);

  useEffect(() => {
    let alive = true;

    setTagsLoading(true);
    setTagsError(null);

    getGoriyakuTags()
      .then((tags) => {
        if (!alive) return;
        setGoriyakuTags(tags);
      })
      .catch(() => {
        if (!alive) return;
        setGoriyakuTags([]);
        setTagsError("ご利益タグを読み込めませんでした");
      })
      .finally(() => {
        if (!alive) return;
        setTagsLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    if (typeof window !== "undefined" && q === "" && window.location.search.includes("q=")) {
      return () => {
        alive = false;
      };
    }

    if (!shouldShowSearchResults || q.length === 0) {
      setCards([]);
      setCount(0);
      setError(null);
      setLoading(false);
      return () => {
        alive = false;
      };
    }

    setLoading(true);
    setError(null);

    fetchShrines({ q })
      .then((data) => {
        if (!alive) return;
        const nextCards = data.results.map((shrine) => buildShrineListCardModel(shrine));
        setCards(nextCards);
        setCount(data.count);
      })
      .catch(() => {
        if (!alive) return;
        setCards([]);
        setCount(0);
        setError("神社データの取得に失敗しました");
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [q, shouldShowSearchResults]);

  const hasSearched = q.length > 0;
  const isEmpty = shouldShowSearchResults && !loading && !error && hasSearched && count === 0;
  const submissionNoticeTitle = submittedName ? `「${submittedName}」の投稿を受け付けました` : "投稿を受け付けました";
  const activeGoriyakuTag = goriyakuTags.find((tag) => tag.name === q) ?? null;
  const submissionNoticeBody = showSubmissionPendingBanner
    ? "現在公開準備中です。確認が完了するまで公開検索には表示されません。"
    : null;

  const handleSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const nextQ = inputValue.trim();
    const next = new URLSearchParams();

    setSubmitted(false);
    setSubmittedName("");
    setQ(nextQ);

    if (nextQ) {
      next.set("q", nextQ);
    }

    router.push(`/shrines${next.toString() ? `?${next.toString()}` : ""}`);
  };

  const handleTagSearch = (tagName: string) => {
    const nextQ = tagName.trim();
    if (!nextQ) return;

    setSubmitted(false);
    setSubmittedName("");

    if (q === nextQ) {
      setQ("");
      setInputValue("");
      router.push("/shrines");
      return;
    }

    setQ(nextQ);
    setInputValue(nextQ);

    router.push(`/shrines?q=${encodeURIComponent(nextQ)}`);
  };

  const handleAddShrine = () => {
    const returnTo = `/shrines${q ? `?q=${encodeURIComponent(q)}` : ""}`;
    router.push(`/shrines/new?returnTo=${encodeURIComponent(returnTo)}`);
  };

  const handleReturnToSearch = () => {
    setSubmitted(false);
    setSubmittedName("");
    setQ("");
    setInputValue("");
    router.push("/shrines");
  };

  return (
    <main className="p-4">
      <h1 className="mb-4 text-xl font-bold">神社を探す</h1>

      {shouldShowSearchResults && (
        <div className="mb-6 space-y-3">
          <form onSubmit={handleSearch} className="flex flex-col gap-3 sm:flex-row">
            <input
              type="search"
              value={inputValue}
              onChange={(e) => setInputValue(e.currentTarget.value)}
              placeholder="神社名で検索"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
            />
            <button
              type="submit"
              className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white"
            >
              検索する
            </button>
          </form>

          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500">ご利益から探す</p>

            {tagsLoading ? (
              <p className="text-xs text-slate-400">ご利益タグを読み込み中…</p>
            ) : tagsError ? (
              <p className="text-xs text-rose-600">{tagsError}</p>
            ) : goriyakuTags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {goriyakuTags.slice(0, 8).map((tag) => {
                  const isActive = tag.name === q;

                  return (
                    <button
                      key={tag.id}
                      type="button"
                      aria-pressed={isActive}
                      onClick={() => handleTagSearch(tag.name)}
                      className={[
                        "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
                        isActive
                          ? "border-emerald-600 bg-emerald-600 text-white shadow-sm"
                          : "border-emerald-200 bg-white text-emerald-700 hover:bg-emerald-50",
                      ].join(" ")}
                    >
                      {tag.name}
                    </button>
                  );
                })}
                {activeGoriyakuTag ? (
                  <p className="text-xs text-emerald-700">{activeGoriyakuTag.name}で検索中です。もう一度押すと解除できます。</p>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      )}

      {submissionNoticeBody && (
        <div className="mb-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-900">
          <div className="mb-4 space-y-2">
            <p className="text-base font-semibold text-emerald-950">{submissionNoticeTitle}</p>
            <p className="leading-relaxed text-emerald-900">{submissionNoticeBody}</p>
            <p className="text-xs leading-relaxed text-emerald-800">
              ご利益タグなどの内容は確認時の参考情報として扱います。
            </p>
          </div>
          <button
            type="button"
            onClick={handleReturnToSearch}
            className="rounded-xl border border-emerald-200 bg-white px-4 py-2 text-sm font-medium text-emerald-700 shadow-sm transition hover:bg-emerald-100"
          >
            神社を探すへ戻る
          </button>
        </div>
      )}

      {error && <p className="text-red-500">{error}</p>}

      {shouldShowSearchResults && loading ? <p className="mb-4 text-sm text-slate-500">検索しています...</p> : null}

      {shouldShowSearchResults && hasSearched &&
        (isEmpty ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-700">
              {activeGoriyakuTag
                ? `${activeGoriyakuTag.name}に合う神社はまだ登録されていません。`
                : "お探しの神社が見つかりませんか？"}
            </p>
            <div className="mt-4">
              <button
                type="button"
                className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white"
                onClick={handleAddShrine}
              >
                神社を追加する
              </button>
            </div>
          </div>
        ) : (
          <>
            <ul className="grid gap-4">
              {cards.map((p) => (
                <li key={p.shrineId}>
                  <ShrineCard
                    name={p.title}
                    address={p.address ?? undefined}
                    recommendReason={p.description ?? undefined}
                    imageUrl={p.imageUrl ?? undefined}
                    tags={p.badges ?? []}
                    href={`/shrines/${p.shrineId}`}
                  />
                </li>
              ))}
            </ul>

            <section className="mt-6 rounded-2xl border border-emerald-100 bg-emerald-50/60 p-5 shadow-sm">
              <p className="text-sm font-semibold text-emerald-950">なんとなく選びきれない場合はこちら</p>
              <p className="mt-2 text-sm leading-6 text-emerald-900">
                今の気持ちや願いから、どの神社が合いそうかをコンシェルジュで整理できます。
              </p>
              <Link
                href="/concierge"
                className="mt-4 inline-flex rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-emerald-700"
              >
                あなたに合う理由を詳しく知る
              </Link>
            </section>
          </>
        ))}
    </main>
  );
}

export default function ShrinesPage() {
  return (
    <Suspense fallback={<p className="p-4">読み込み中...</p>}>
      <ShrinesPageContent />
    </Suspense>
  );
}
