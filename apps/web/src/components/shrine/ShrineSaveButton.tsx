"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useFavorite } from "@/hooks/useFavorite";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { buildLoginHref } from "@/lib/nav/login";
import { useAuth } from "@/lib/auth/AuthProvider";
import { track } from "@/lib/analytics/track";

type Props = {
  shrineId: number;
  ctx?: "map" | "concierge" | null;
  tid?: string | null;
  nextPath?: string;
  guestMode?: boolean;
  initial?: {
    fav: boolean;
    favorite_id: number | null;
  };
  onToggleSuccess?: (nextFav: boolean) => void;
};

export default function ShrineSaveButton({
  shrineId,
  ctx = null,
  tid = null,
  nextPath,
  guestMode,
  initial,
  onToggleSuccess,
}: Props) {
  const router = useRouter();
  const { isLoggedIn, loading } = useAuth();
  const [err, setErr] = useState<string | null>(null);

  const effectiveGuestMode =
    typeof guestMode === "boolean" ? guestMode : !loading && !isLoggedIn;

  const { fav, busy, toggle } = useFavorite({
    shrineId,
    guestMode: effectiveGuestMode,
    initial,
  });

  const onClick = async () => {
    setErr(null);
    try {
      const prevFav = fav;
      const nextFav = !prevFav;
      await toggle();
      track("favorite_click", {
        shrineId,
        ctx,
        tid,
        nextFav,
      });

      if (nextFav) {
        track("shrine_decision", {
          shrineId,
          action: "save",
          ctx,
          tid,
        });
      }

      onToggleSuccess?.(nextFav);
    } catch (e: any) {
      const status = e?.response?.status ?? e?.status;
      if (status === 401) {
        const next = nextPath ?? buildShrineHref(shrineId);
        router.push(buildLoginHref(next));
        return;
      }
      setErr("保存の更新に失敗しました");
    }
  };

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className={`inline-flex w-full items-center justify-center rounded-xl border px-4 py-3 text-sm font-semibold transition
          ${
            fav
              ? "border-emerald-300 bg-emerald-50 text-emerald-800"
              : "border-slate-300 bg-white text-slate-900 hover:bg-slate-50"
          }
          disabled:opacity-60`}
        aria-pressed={fav}
      >
        {busy ? "保存中…" : fav ? "保存しました" : "保存する"}
      </button>

      {err ? <p className="text-xs text-red-600">{err}</p> : null}
    </div>
  );
}
