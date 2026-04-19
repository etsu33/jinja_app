"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { ShrineCard } from "@/components/shrines/ShrineCard";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import { fetchShrines } from "@/lib/api/shrinesSearch";
import { buildShrineListCardModel } from "@/lib/shrine/buildShrineListCardModel";

export default function ShrinesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const q = (searchParams.get("q") ?? "").trim();
  const submitted = searchParams.get("submitted") === "1";
  const status = searchParams.get("status");
  const submittedName = (searchParams.get("name") ?? "").trim();

  const [inputValue, setInputValue] = useState(q);
  const [cards, setCards] = useState<ShrineCardAdapterProps[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setInputValue(q);
  }, [q]);

  useEffect(() => {
    let alive = true;
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
    if (!submitted) return null;
    if (status === "pending") {
      return submittedName
        ? `「${submittedName}」の投稿を受け付けました。現在審査中です。`
        : "神社登録の投稿を受け付けました。現在審査中です。";
    }
    return submittedName
      ? `「${submittedName}」の投稿を受け付けました。`
      : "神社登録の投稿を受け付けました。";
  }, [status, submitted, submittedName]);

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
        <div className="mb-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
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
