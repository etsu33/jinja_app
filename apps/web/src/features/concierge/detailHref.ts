// apps/web/src/features/concierge/detailHref.ts
import { resolveShrineIdentity } from "@/lib/identity/resolveShrineId";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { buildShrineResolveHref } from "@/lib/nav/buildShrineResolveHref";

/**
 * Concierge recommendation → detail href (product spec)
 *
 * - 登録済み: shrine_id / shrineId / shrine.id を持つ → /shrines/:id
 * - 未登録: place_id / placeId（など）だけを持つ → /shrines/resolve?place_id=...
 * - IDなし: null（UIは詳細導線を表示しない）
 *
 * 注意:
 * recommendation の `id` は shrine_id ではない可能性があるため使わない。
 * 実在 shrine への導線は shrine_id / shrineId / shrine.id のみを採用する。
 * 詳細URLに載せる query はallowlist対象のみ。方位候補の表示位置は描画側で安全な分類値として追加する。
 *
 * F-4: Shrine identity の正規化・alias 優先順位・conflict 判定は共有 resolver
 * （@/lib/identity/resolveShrineId）へ集約した。ここに独自の正規化実装は持たない。
 *
 * F-3.1: この consumer は place_id fallback を持つため、`resolveShrineId()`
 * （number | null）ではなく `resolveShrineIdentity()`（status 付き）を使う。
 * identity が「無い」のか「壊れている／食い違っている」のかで挙動が逆になるため:
 *
 *   status=resolved -> /shrines/:id
 *   status=absent   -> place_id fallback を許可（従来どおり）
 *   status=invalid  -> null（place_id へ落とさない）
 *   status=conflict -> null（place_id へ落とさない）
 *
 * invalid / conflict で place_id へ落とすと、FAIL_CLOSED_ON_CONFLICT を破り、
 * F-6 の place_id shadow identity 経路へ入ってしまう
 * （docs/audit/shared-shrine-identity-resolver-design.md §13）。
 */

type AnyObj = Record<string, any>;

export function pickPlaceId(item: AnyObj): string | null {
  const v =
    item?.place_id ?? item?.placeId ?? item?.google?.place_id ?? item?.google?.placeId ?? item?.place?.id ?? null;
  return typeof v === "string" && v.trim() ? v.trim() : null;
}

export function detailHrefFromRecommendation(
  item: AnyObj,
  ctx?: {
    ctx?: string;
    tid?: string | number;
  },
): string | null {
  const identity = resolveShrineIdentity(item, "registered_compat");

  if (identity.status === "resolved") {
    return buildShrineHref(identity.shrineId, {
      ctx: ctx?.ctx,
      tid: ctx?.tid ?? undefined,
    });
  }

  // Shrine identity が主張されているのに使えない（invalid / conflict）場合は
  // fail closed。place_id は Shrine identity authority ではないので代替にしない。
  if (identity.status !== "absent") {
    return null;
  }

  const placeId = pickPlaceId(item);
  if (placeId) {
    return buildShrineResolveHref(placeId, {
      ctx: ctx?.ctx === "map" || ctx?.ctx === "concierge" ? ctx.ctx : "concierge",
      tid: ctx?.tid != null ? String(ctx.tid) : null,
    });
  }

  return null;
}
