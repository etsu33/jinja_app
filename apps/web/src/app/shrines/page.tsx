"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  clearSubmissionPendingParams,
  isSubmissionPendingParams,
} from "@/features/shrine-submission/lib/submissionReturnState";

import { ShrineCard } from "@/components/shrines/ShrineCard";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import { fetchShrines } from "@/lib/api/shrinesSearch";
import { buildShrineListCardModel } from "@/lib/shrine/buildShrineListCardModel";

export default function ShrinesPage() {
  const router = useRouter();
  const pathname = usePathname();

  const [q, setQ] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submittedName, setSubmittedName] = useState("");
  const [inputValue, setInputValue] = useState("");
  const showSubmissionPendingBanner = submitted;

  const [cards, setCards] = useState<ShrineCardAdapterProps[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);

    setQ((params.get("q") ?? "").trim());
    setSubmitted(isSubmissionPendingParams(params));
    setSubmittedName((params.get("name") ?? "").trim());
  }, []);

  useEffect(() => {
    if (!showSubmissionPendingBanner) return;
    if (typeof window === "undefined") return;

    const next = new URLSearchParams(window.location.search);
    clearSubmissionPendingParams(next);

    const qs = next.toString();
    const url = qs ? `${pathname}?${qs}` : pathname;

    const timer = window.setTimeout(() => {
      router.replace(url);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [showSubmissionPendingBanner, pathname, router]);

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
  }, [q]);

  const hasSearched = q.length > 0;
  const isEmpty = !loading && !error && hasSearched && count === 0;
  const submissionNotice = useMemo(() => {
    if (!showSubmissionPendingBanner) return null;
    return submittedName
      ? `「${submittedName}」の投稿を受け付けました。\n現在審査中のため、公開検索にはまだ表示されません。\n審査完了後に公開されます。`
      : "投稿を受け付けました。\n現在審査中のため、公開検索にはまだ表示されません。\n審査完了後に公開されます。";
  }, [showSubmissionPendingBanner, submittedName]);

  const handleSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const nextQ = inputValue.trim();
    const next = new URLSearchParams();
    if (nextQ) next.set("q", nextQ);
    router.push(`/shrines${next.toString() ? `?${next.toString()}` : ""}`);
  };

  const handleAddShrine = () => {
    const returnTo = `/shrines${q ? `?q=${encodeURIComponent(q)}` : ""}`;
    router.push(`/shrines/new?returnTo=${encodeURIComponent(returnTo)}`);
  };

  if (loading) return <p className="p-4">読み込み中...</p>;

  return (
    <main className="p-4">
      <h1 className="mb-4 text-xl font-bold">神社を探す</h1>

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

      {submissionNotice && (
        <div className="mb-6 whitespace-pre-line rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {submissionNotice}
        </div>
      )}

      {error && <p className="text-red-500">{error}</p>}

      {isEmpty ? (
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
      )}
    </main>
  );
}
