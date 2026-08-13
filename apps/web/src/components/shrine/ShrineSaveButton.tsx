"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useFavorite } from "@/hooks/useFavorite";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { buildLoginHref } from "@/lib/nav/login";
import { useAuth } from "@/lib/auth/AuthProvider";
import { track } from "@/lib/analytics/track";
import {
  recommendationAnalyticsProperties,
  type RecommendationAnalyticsProvenance,
} from "../../../../../packages/shared/recommendationAnalyticsProvenance";

type Props = {
  shrineId: number;
  ctx?: "map" | "concierge" | null;
  tid?: string | null;
  nextPath?: string;
  guestMode?: boolean;
  variant?: "default" | "subtle";
  initial?: {
    fav: boolean;
    favorite_id: number | null;
  };
  onToggleSuccess?: (nextFav: boolean) => void;
  analyticsProvenance?: RecommendationAnalyticsProvenance;
};

export default function ShrineSaveButton({
  shrineId,
  ctx = null,
  tid = null,
  nextPath,
  guestMode,
  variant = "default",
  initial,
  onToggleSuccess,
  analyticsProvenance,
}: Props) {
  const router = useRouter();
  const { isLoggedIn, loading } = useAuth();
  const [err, setErr] = useState<string | null>(null);

  const effectiveGuestMode = typeof guestMode === "boolean" ? guestMode : !loading && !isLoggedIn;
  const accessLevel = effectiveGuestMode ? "anonymous" : "free";

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
        source: "shrine_detail",
        cardId: "saved_record",
        accessLevel,
        ...(analyticsProvenance ? recommendationAnalyticsProperties(analyticsProvenance) : {}),
      });

      if (nextFav) {
        track("shrine_decision", {
          shrineId,
          action: "save",
          ctx,
          tid,
          ...(analyticsProvenance ? recommendationAnalyticsProperties(analyticsProvenance) : {}),
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

  const buttonClass =
    variant === "subtle"
      ? `inline-flex w-full items-center justify-center rounded-[var(--kt-radius-panel)] border px-4 py-2.5 text-xs font-semibold transition
          ${
            fav
              ? /* border-emerald-200: subtle variant固有の値。default variantの
                   border-emerald-300とTokenが分裂しているため(MULTI_VARIANT_VALUE_SPLIT)、
                   --kt-color-saved-border(=emerald-300)を流用せずliteralのまま維持する。
                   docs/audit/design-token-stage4-mother-ship-decisions.md 参照 */
                "border-emerald-200 bg-[var(--kt-color-saved-background)] text-[var(--kt-color-saved-text)]"
              : "border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-muted)] hover:bg-[var(--kt-color-background-subtle)] hover:text-[var(--kt-color-text-secondary)]"
          }
          disabled:opacity-60`
      : `inline-flex w-full items-center justify-center rounded-[var(--kt-radius-panel)] border px-4 py-3 text-sm font-semibold transition
          ${
            fav
              ? "border-[var(--kt-color-saved-border)] bg-[var(--kt-color-saved-background)] text-[var(--kt-color-saved-text)]"
              : "border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)] hover:bg-[var(--kt-color-background-subtle)]"
          }
          disabled:opacity-60`;

  return (
    <div className="space-y-2">
      <button type="button" onClick={onClick} disabled={busy} className={buttonClass} aria-pressed={fav}>
        {busy
          ? "保存中…"
          : fav
            ? "保存しました"
            : effectiveGuestMode
              ? "ログインしてあとで見返す"
              : "あとで見返すために保存"}
      </button>

      {err ? <p className="text-xs text-[var(--kt-color-status-error)]">{err}</p> : null}
    </div>
  );
}
