"use client";

import Link from "next/link";
import type { Favorite } from "@/lib/api/favorites";
import { normalizeFavorite } from "@/lib/favorites/normalize";
import { LABELS } from "@/lib/ui/labels";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { buildShrineResolveHref } from "@/lib/nav/buildShrineResolveHref";

type Props = {
  favorite: Favorite;
  onUnsave?: () => void;
  onAddGoshuin?: () => void;

  disabled?: boolean;
  unsaveLoading?: boolean;
  addLoading?: boolean;

  canAddGoshuin?: boolean;
};

export function FavoriteShrineCard({
  favorite,
  onUnsave,
  onAddGoshuin,
  disabled,
  unsaveLoading,
  addLoading,
  canAddGoshuin,
}: Props) {
  const { shrineId, placeId } = normalizeFavorite(favorite);

  const href = shrineId ? buildShrineHref(shrineId) : placeId ? buildShrineResolveHref(placeId) : "/map";

  const title =
    (favorite.shrine?.name_jp && favorite.shrine.name_jp.trim()) ||
    (shrineId ? `神社 #${shrineId}` : placeId ? `place_id: ${placeId}` : `id: ${favorite.id}`);

  const sub = (favorite.shrine?.address && favorite.shrine.address.trim()) || null;

  const publicGoshuinCount = Number(favorite.public_goshuin_count ?? 0);
  const hasPublicGoshuins = publicGoshuinCount > 0;

  const goshuinHref = shrineId && hasPublicGoshuins ? buildShrineHref(shrineId, { subpath: "goshuins" }) : null;

  const allowAdd = canAddGoshuin ?? Boolean(shrineId || placeId);

  return (
    <div className="rounded-2xl border border-stone-200/20 bg-stone-50/20 p-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-stone-900">{title}</p>
          {sub && <p className="mt-0.5 truncate text-xs text-stone-500">{sub}</p>}

          {hasPublicGoshuins ? (
            <div className="mt-2">
              <span className="inline-flex items-center rounded-full border border-emerald-700/10 bg-emerald-50/50 px-2 py-0.5 text-[11px] font-medium text-emerald-800/80">
                御朱印 {publicGoshuinCount}件
              </span>
            </div>
          ) : null}

          <div className="mt-2 flex flex-wrap items-center gap-3">
            {href && (
              <Link href={href} className="text-xs text-stone-600 hover:text-stone-900 hover:underline">
                {LABELS.shrineDetail}
              </Link>
            )}

            {goshuinHref && (
              <Link href={goshuinHref} className="text-xs text-emerald-800/80 hover:text-emerald-900 hover:underline">
                御朱印を見る
              </Link>
            )}
          </div>
        </div>

        <div className="flex shrink-0 flex-row gap-2 sm:flex-col">
          {onAddGoshuin && (
            <button
              type="button"
              onClick={onAddGoshuin}
              disabled={disabled || addLoading || !allowAdd}
              className="rounded-full border border-stone-200/40 bg-stone-50/20 px-3 py-1 text-xs font-medium text-stone-700 transition hover:bg-stone-100/50 disabled:opacity-40"
            >
              {addLoading ? LABELS.moving : LABELS.addGoshuin}
            </button>
          )}

          {onUnsave && (
            <button
              type="button"
              onClick={onUnsave}
              disabled={disabled || unsaveLoading}
              className="rounded-full border border-stone-200/40 bg-stone-50/20 px-3 py-1 text-xs font-medium text-stone-600 transition hover:bg-stone-100/50 disabled:opacity-40"
            >
              {unsaveLoading ? LABELS.removing : LABELS.unsave}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
