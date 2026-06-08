"use client";

import Link from "next/link";

type Props = {
  user: any;
  onLogout?: () => Promise<void> | void;
};

export default function SettingsSection({ user, onLogout }: Props) {
  const profile = user?.profile ?? null;
  const username: string | null = user?.username ?? null;
  const isPublic: boolean = profile?.is_public ?? user?.is_public ?? false;

  const hasPublicPage = Boolean(username && isPublic);

  return (
    <section className="rounded-2xl border border-stone-200/20 bg-stone-50/30 px-6 py-5">
      <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-stone-800">
        <span className="inline-block h-5 w-1 rounded-full bg-stone-300" />
        設定
      </h2>

      <div className="space-y-4 text-sm text-stone-700">
        <p className="text-xs text-stone-500">公開設定や自己紹介を編集できます。</p>

        {/* 公開中だけ「公開プロフィールページ」へのリンクを出す */}
        {hasPublicPage && (
          <div className="border-t border-stone-200/20 pt-3">
            <div className="text-xs text-stone-400">公開プロフィールページ</div>
            <Link
              href={`/users/${username}`}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-flex break-all text-xs text-stone-600 underline hover:text-stone-900"
            >
              /users/{username}
            </Link>
          </div>
        )}

        {/* ✅ 最下部：ログアウト */}
        {onLogout && (
          <div className="border-t border-stone-200/20 pt-4">
            <button
              type="button"
              onClick={() => {
                // 誤タップ対策（必要なら）
                const ok = window.confirm("ログアウトしますか？");
                if (!ok) return;
                void onLogout();
              }}
              className="w-full rounded-full border border-rose-700/20 bg-stone-50/20 px-4 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-50/60"
            >
              ログアウト
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
