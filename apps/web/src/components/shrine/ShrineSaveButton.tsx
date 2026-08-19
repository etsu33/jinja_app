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
  ctx?: "map" | "concierge" | "compass" | null;
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
  recommendationInstanceId?: string | null;
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
  recommendationInstanceId = null,
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
      // PR-C (docs/analytics/compass-analytics-contract.md): source only
      // distinguishes "compass" from everything else. Concierge/map/direct
      // keep their existing "shrine_detail" value unchanged -- widening this
      // to a full ctx-derived value is out of PR-C's scope.
      const source = ctx === "compass" ? "compass" : "shrine_detail";
      track("favorite_click", {
        shrineId,
        ctx,
        tid,
        nextFav,
        source,
        cardId: "saved_record",
        accessLevel,
        recommendationInstanceId,
        ...(analyticsProvenance ? recommendationAnalyticsProperties(analyticsProvenance) : {}),
      });

      if (nextFav) {
        track("shrine_decision", {
          shrineId,
          action: "save",
          ctx,
          tid,
          source,
          recommendationInstanceId,
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

  // "subtle" variant: Recommendation Result Hero-only (docs/product/
  // recommendation-result-information-architecture.md §6/§11/§15 PR3). This must read
  // as clearly subordinate to the Hero's Primary CTA ("神社の詳細を見る", solid
  // bg-action-primary) -- a text-link, not a bordered/filled button, so it never
  // competes with it. Shrine Detail's own Save button uses the "default" variant below,
  // unaffected by this styling.
  const buttonClass =
    variant === "subtle"
      ? `inline-flex w-full items-center justify-center px-1 py-1.5 text-xs font-semibold underline underline-offset-2 transition
          ${
            fav
              ? "text-[var(--kt-color-saved-text)]"
              : "text-[var(--kt-color-text-muted)] hover:text-[var(--kt-color-text-secondary)]"
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
