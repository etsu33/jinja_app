"use client";

import React from "react";

type Props = {
  username: string;
  count: number;
  limit: number;
  offset: number;
};

export default function PublicGoshuinHeader({ username, count, limit, offset }: Props) {
  const from = count ? Math.min(offset + 1, count) : 0;
  const to = count ? Math.min(offset + limit, count) : 0;

  const shareUrl = typeof window !== "undefined" ? `${window.location.origin}/g/${encodeURIComponent(username)}` : "";

  const onCopy = async () => {
    try {
      if (!shareUrl) return;
      await navigator.clipboard.writeText(shareUrl);
      // alert は後で toast に置換でOK
      alert("URLをコピーしました");
    } catch {
      alert("コピーに失敗しました");
    }
  };

  return (
    <header className="flex items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-bold text-[var(--kt-color-text-primary)]">@{username} の御朱印帳</h1>
        <p className="mt-1 text-xs text-[var(--kt-color-text-muted)]">
          公開されている御朱印のみ表示します（{from}〜{to}/{count}）
        </p>
      </div>

      <button
        type="button"
        onClick={onCopy}
        className="rounded-md bg-[var(--kt-color-surface-elevated)] px-3 py-2 text-xs font-medium text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-surface-emphasis-hover)]"
      >
        URLをコピー
      </button>
    </header>
  );
}
