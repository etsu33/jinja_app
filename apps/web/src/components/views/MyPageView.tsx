"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { updateUser, type UserMe } from "@/lib/api/users";
import { useAuth as useAuthContext } from "@/lib/auth/AuthProvider";
import type { Favorite } from "@/lib/api/favorites";
import { getVisits, type Visit } from "@/lib/api/visits";
import MyPageScreen from "@/features/mypage/components/MyPageScreen";
import FavoritesSection from "@/features/mypage/components/FavoritesSection";
import Link from "next/link";
import { buildLoginHref } from "@/lib/nav/login";

type Props = { initialFavorites: Favorite[] };
type MyPageTab = "profile" | "goshuin" | "favorites" | "submissions" | "visits";
const GOSHUIN_TAB_ENABLED = false;

function normalizeTab(value: string | null): MyPageTab {
  if (GOSHUIN_TAB_ENABLED && value === "goshuin") return value;
  if (value === "favorites" || value === "submissions" || value === "visits") return value;
  return "profile";
}

function TabLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className={`rounded-full px-3 py-1.5 text-sm transition ${
        active
          ? "border border-stone-300/50 bg-stone-200/50 text-stone-900"
          : "border border-stone-200/20 bg-stone-50/20 text-stone-500 hover:bg-stone-100/40 hover:text-stone-800"
      }`}
    >
      {children}
    </Link>
  );
}

function formatVisitedAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

type AggregatedVisit = {
  key: string;
  shrineId: number | string | null;
  shrineName: string;
  shrineAddress: string | null;
  latestVisitedAt: string;
  visitCount: number;
};

function getVisitTime(value: string) {
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? 0 : time;
}

function aggregateVisitsByShrine(visits: Visit[]): AggregatedVisit[] {
  const map = new Map<string, AggregatedVisit>();

  visits.forEach((visit) => {
    const shrine = visit.shrine as any;
    const shrineId = typeof shrine === "number" ? shrine : (shrine?.id ?? shrine?.shrine_id ?? null);
    const key = shrineId != null ? String(shrineId) : `visit-${visit.id}`;
    const shrineName =
      visit.shrine_name ??
      (typeof shrine === "number" ? null : (shrine?.name ?? shrine?.display_name ?? shrine?.title)) ??
      "神社名未設定";
    const shrineAddress =
      visit.shrine_address ??
      (typeof shrine === "number" ? null : (shrine?.address ?? shrine?.location ?? null));

    const current = map.get(key);
    if (!current) {
      map.set(key, {
        key,
        shrineId,
        shrineName,
        shrineAddress,
        latestVisitedAt: visit.visited_at,
        visitCount: 1,
      });
      return;
    }

    current.visitCount += 1;
    if (getVisitTime(visit.visited_at) > getVisitTime(current.latestVisitedAt)) {
      current.latestVisitedAt = visit.visited_at;
    }
    if (current.shrineName === "神社名未設定" && shrineName !== "神社名未設定") {
      current.shrineName = shrineName;
    }
    if (!current.shrineAddress && shrineAddress) {
      current.shrineAddress = shrineAddress;
    }
  });

  return Array.from(map.values()).sort(
    (a, b) => getVisitTime(b.latestVisitedAt) - getVisitTime(a.latestVisitedAt),
  );
}

export default function MyPageView({ initialFavorites }: Props) {
  const sp = useSearchParams();
  const tab = normalizeTab(sp.get("tab"));
  const { user: authUser, loading } = useAuthContext();

  const [user, setUser] = useState<UserMe | null>(null);
  const [form, setForm] = useState({ nickname: "", is_public: true });
  const [saving, setSaving] = useState(false);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [visitsLoading, setVisitsLoading] = useState(false);
  const [visitsError, setVisitsError] = useState<string | null>(null);

  useEffect(() => {
    if (!authUser) {
      setUser(null);
      return;
    }

    const me = authUser as UserMe;
    setUser(me);
    setForm({
      nickname: (me.profile?.nickname ?? "").trim(),
      is_public: !!me.profile?.is_public,
    });
  }, [authUser]);

  useEffect(() => {
    if (tab !== "goshuin") return;
    const hash = window.location.hash;
    if (hash !== "#goshuin-upload") return;
    requestAnimationFrame(() => {
      document.querySelector(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [tab]);

  useEffect(() => {
    if (!user || tab !== "visits") return;

    let cancelled = false;

    (async () => {
      try {
        setVisitsLoading(true);
        setVisitsError(null);
        const data = await getVisits();
        if (cancelled) return;
        setVisits(Array.isArray(data) ? data : []);
      } catch {
        if (cancelled) return;
        setVisits([]);
        setVisitsError("参拝履歴を読み込めませんでした。");
      } finally {
        if (!cancelled) setVisitsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [tab, user]);

  const dirty = useMemo(() => {
    if (!user) return false;
    const nick0 = (user.profile?.nickname ?? "").trim();
    const nick1 = (form.nickname ?? "").trim();
    return nick1 !== nick0 || Boolean(form.is_public) !== Boolean(user.profile?.is_public);
  }, [user, form.nickname, form.is_public]);

  const aggregatedVisits = useMemo(() => aggregateVisitsByShrine(visits), [visits]);

  const handleSave = async () => {
    if (!user || !dirty || saving) return;
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {};
      const nick0 = (user.profile?.nickname ?? "").trim();
      const nick1 = (form.nickname ?? "").trim();
      if (nick1 !== nick0) payload.nickname = nick1;
      if (Boolean(form.is_public) !== Boolean(user.profile?.is_public)) payload.is_public = form.is_public;

      const updated = await updateUser(payload);
      setUser(updated);
      setForm({
        nickname: (updated.profile?.nickname ?? "").trim(),
        is_public: !!updated.profile?.is_public,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (!user) return;
    setForm({ nickname: user.profile?.nickname ?? "", is_public: !!user.profile?.is_public });
  };

  if (loading) {
    return (
      <div className="p-4 text-sm text-stone-500" role="status" aria-busy="true">
        読み込み中...
      </div>
    );
  }

  if (!user) {
    const next = tab === "goshuin" || tab === "favorites" || tab === "submissions" || tab === "visits" ? `/mypage?tab=${tab}` : "/mypage?tab=profile";
    return (
      <main className="mx-auto max-w-3xl p-6 text-stone-800">
        <h1 className="mb-4 text-xl font-semibold">マイページ</h1>
        <div className="rounded-2xl border border-stone-200/20 bg-stone-50/30 p-6">
          <p className="mb-3 text-sm text-stone-600">ログインしてご利用ください。</p>
          <Link
            href={buildLoginHref(next)}
            className="inline-block rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-2 text-sm text-white transition hover:bg-emerald-900"
          >
            ログインへ
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-6 text-stone-800 sm:px-6">
      <div className="flex flex-wrap gap-2 border-b border-stone-200/20 pb-3">
        <TabLink href="/mypage?tab=profile" active={tab === "profile"}>
          プロフィール
        </TabLink>

        <TabLink href="/mypage?tab=submissions" active={tab === "submissions"}>
          投稿した神社
        </TabLink>

        {GOSHUIN_TAB_ENABLED && (
          <TabLink href="/mypage?tab=goshuin" active={tab === "goshuin"}>
            御朱印
          </TabLink>
        )}

        <TabLink href="/mypage?tab=favorites" active={tab === "favorites"}>
          保存した神社
        </TabLink>

        <TabLink href="/mypage?tab=visits" active={tab === "visits"}>
          参拝履歴
        </TabLink>
      </div>

      {tab === "goshuin" ? (
        <MyPageScreen activeTab="goshuin" />
      ) : tab === "submissions" ? (
        <MyPageScreen activeTab="submissions" />
      ) : tab === "favorites" ? (
        <FavoritesSection initialFavorites={initialFavorites} />
      ) : tab === "visits" ? (
        <section className="space-y-4 rounded-2xl border border-stone-200/20 bg-stone-50/30 p-5 sm:p-6">
          <div>
            <h2 className="text-lg font-semibold text-stone-900">参拝履歴</h2>
            <p className="mt-1 text-sm text-stone-500">参拝済みにした神社を見返せます。</p>
          </div>

          {visitsLoading ? (
            <p className="text-sm text-stone-500" role="status" aria-busy="true">
              参拝履歴を読み込み中...
            </p>
          ) : visitsError ? (
            <div className="rounded-xl border border-rose-200 bg-white p-4">
              <p className="text-sm font-medium text-rose-700">{visitsError}</p>
            </div>
          ) : aggregatedVisits.length === 0 ? (
            <div className="rounded-xl border border-stone-200/40 bg-white p-4">
              <p className="text-sm font-medium text-stone-700">参拝履歴はまだありません。</p>
              <p className="mt-1 text-xs text-stone-500">神社詳細から「参拝済みにする」を押すとここに表示されます。</p>
            </div>
          ) : (
            <div className="space-y-3">
              {aggregatedVisits.map((visit) => {
                return (
                  <article key={visit.key} className="rounded-xl border border-stone-200/40 bg-white p-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h3 className="text-base font-semibold text-stone-900">{visit.shrineName}</h3>
                        {visit.shrineAddress ? <p className="mt-1 text-xs text-stone-500">{visit.shrineAddress}</p> : null}
                        <p className="mt-2 text-xs text-stone-500">最新参拝：{formatVisitedAt(visit.latestVisitedAt)}</p>
                        <p className="mt-1 text-xs font-medium text-emerald-700">参拝回数：{visit.visitCount}回</p>
                      </div>

                      {visit.shrineId ? (
                        <Link
                          href={`/shrines/${visit.shrineId}`}
                          className="inline-flex shrink-0 items-center justify-center rounded-full border border-emerald-700/20 bg-emerald-800 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-900"
                        >
                          詳細を見る
                        </Link>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      ) : (
        <section className="space-y-5 rounded-2xl border border-stone-200/20 bg-stone-50/30 p-5 sm:p-6">
          <div>
            <label className="mb-1 block text-sm font-medium text-stone-700">ニックネーム</label>
            <input
              type="text"
              value={form.nickname}
              onChange={(e) => setForm((f) => ({ ...f, nickname: e.target.value }))}
              disabled={saving}
              className="w-full rounded-xl border border-stone-200/30 bg-stone-50/30 px-3 py-2 text-sm text-stone-800 outline-none transition placeholder:text-stone-300 focus:border-stone-300/70 focus:ring-2 focus:ring-stone-200/30 disabled:opacity-60"
            />
          </div>

          <label className="inline-flex items-center gap-2 text-sm text-stone-700">
            <input
              type="checkbox"
              checked={form.is_public}
              onChange={(e) => setForm((f) => ({ ...f, is_public: e.target.checked }))}
              disabled={saving}
              className="h-4 w-4 rounded border-stone-300 text-emerald-800 focus:ring-stone-200"
            />
            <span>プロフィールを公開</span>
          </label>

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!dirty || saving}
              className="rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-2 text-sm text-white transition hover:bg-emerald-900 disabled:opacity-40"
            >
              {saving ? "保存中..." : "保存"}
            </button>
            <button
              type="button"
              onClick={handleReset}
              disabled={!dirty || saving}
              className="rounded-full border border-stone-200/40 bg-stone-50/20 px-4 py-2 text-sm text-stone-600 transition hover:bg-stone-100/50 disabled:opacity-40"
            >
              変更を破棄
            </button>
          </div>
        </section>
      )}
    </main>
  );
}
