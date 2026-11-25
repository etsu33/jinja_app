import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { djFetch } from "@/lib/server/backend";
import { UnregisteredPlaceView } from "./UnregisteredPlaceView";

type SP = {
  place_id?: string;
  locationbias?: string;
  ctx?: string;
  tid?: string;
};

export default async function ResolvePage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;

  const placeId = sp.place_id?.trim();
  if (!placeId) redirect("/?toast=resolve_missing_place");

  // Django を直接呼び、利用者リクエストの x-forwarded-for で WS-04 client identity を署名する。
  // 以前の自己 fetch（`${baseUrl}/api/places/resolve/`）では BFF が見る送信元が Next.js サーバー自身になり、
  // `places-resolve` throttle（POST 10/min）の bucket を全利用者で共有しうるため。
  // Django 側の resolve は認証を使わない（authentication_classes = []）ので、cookie / 認証は転送しない。
  const h = await headers();
  const forwardedFor = h.get("x-forwarded-for");
  const identitySource = new Request("http://web.invalid/shrines/resolve", {
    headers: forwardedFor ? { "x-forwarded-for": forwardedFor } : {},
  });

  const res = await djFetch("/api/places/resolve/", {
    method: "POST",
    cache: "no-store",
    clientIdentityFrom: identitySource,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ place_id: placeId }),
  });

  if (res.status === 401) redirect("/?toast=login_required");
  if (!res.ok) redirect("/?toast=resolve_failed");

  const data = (await res.json()) as {
    shrine_id?: number | string | null;
    id?: number | string | null;
    registered?: boolean;
    place_id?: string;
    name_jp?: string | null;
    address?: string | null;
  };

  // Shrine マスタ未登録: backend は Shrine を作らない（作成は staff 限定）ので、Place 情報だけを表示する。
  if (data.registered === false) {
    return (
      <UnregisteredPlaceView
        place={{ place_id: data.place_id ?? placeId, name_jp: data.name_jp, address: data.address }}
      />
    );
  }

  const shrineId = data.shrine_id ?? data.id;
  if (!shrineId) redirect("/?toast=resolve_no_shrine");

  const q = new URLSearchParams();
  const ctx = sp.ctx?.trim();
  if (ctx) q.set("ctx", ctx);
  const tid = sp.tid?.trim();
  if (tid) q.set("tid", tid);

  const query = Object.fromEntries(q.entries());
  redirect(buildShrineHref(shrineId, { query: Object.keys(query).length ? query : undefined }));
}
