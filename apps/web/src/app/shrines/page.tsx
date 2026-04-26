"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { isSubmissionPendingParams } from "@/features/shrine-submission/lib/submissionReturnState";

import { ShrineCard } from "@/components/shrines/ShrineCard";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import { fetchShrines } from "@/lib/api/shrinesSearch";
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
  const submissionNoticeBody = useMemo(() => {
    if (!showSubmissionPendingBanner) return null;
    return "現在公開準備中です。確認が完了するまで公開検索には表示されません。";
  }, [showSubmissionPendingBanner]);

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

  if (loading) return <p className="p-4">読み込み中...</p>;

  return (
    <main className="p-4">
      <h1 className="mb-4 text-xl font-bold">神社を探す</h1>

      {shouldShowSearchResults && (
        <form onSubmit={handleSearch} className="mb-6 flex flex-col gap-3 sm:flex-row">
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

      {shouldShowSearchResults && hasSearched &&
        (isEmpty ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-700">お探しの神社が見つかりませんか？</p>
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
