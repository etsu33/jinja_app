"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { updateUser, type UserMe } from "@/lib/api/users";
import { useAuth as useAuthContext } from "@/lib/auth/AuthProvider";
import type { Favorite } from "@/lib/api/favorites";
import MyPageScreen from "@/features/mypage/components/MyPageScreen";
import FavoritesSection from "@/features/mypage/components/FavoritesSection";
import Link from "next/link";
import { buildLoginHref } from "@/lib/nav/login";

type Props = { initialFavorites: Favorite[] };
type MyPageTab = "profile" | "goshuin" | "favorites" | "submissions";
const GOSHUIN_TAB_ENABLED = false;

function normalizeTab(value: string | null): MyPageTab {
  if (GOSHUIN_TAB_ENABLED && value === "goshuin") return value;
  if (value === "favorites" || value === "submissions") return value;
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

export default function MyPageView({ initialFavorites }: Props) {
  const sp = useSearchParams();
  const tab = normalizeTab(sp.get("tab"));
  const { user: authUser, loading } = useAuthContext();

  const [user, setUser] = useState<UserMe | null>(null);
  const [form, setForm] = useState({ nickname: "", is_public: true });
  const [saving, setSaving] = useState(false);

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

  const dirty = useMemo(() => {
    if (!user) return false;
    const nick0 = (user.profile?.nickname ?? "").trim();
    const nick1 = (form.nickname ?? "").trim();
    return nick1 !== nick0 || Boolean(form.is_public) !== Boolean(user.profile?.is_public);
  }, [user, form.nickname, form.is_public]);

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
    const next = tab === "goshuin" || tab === "favorites" || tab === "submissions" ? `/mypage?tab=${tab}` : "/mypage?tab=profile";
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
      </div>

      {tab === "goshuin" ? (
        <MyPageScreen activeTab="goshuin" />
      ) : tab === "submissions" ? (
        <MyPageScreen activeTab="submissions" />
      ) : tab === "favorites" ? (
        <FavoritesSection initialFavorites={initialFavorites} />
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
