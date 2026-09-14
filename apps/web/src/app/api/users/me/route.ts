//apps/web/src/app/api/users/me/route.ts;

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

import type { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export async function GET(req: NextRequest) {
  return bffFetchWithAuthFromReq(req, "/api/users/me/", { method: "GET" });
}

export async function PATCH(req: NextRequest) {
  const bodyText = await req.text();
  return bffFetchWithAuthFromReq(req, "/api/users/me/", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: bodyText,
  });
}

export async function DELETE(req: NextRequest) {
  const response = await bffFetchWithAuthFromReq(req, "/api/users/me/", {
    method: "DELETE",
  });

  // Backend が削除完了を 204 で確定した場合だけ認証Cookieを破棄する。
  // 503 / 401 / その他の失敗時は Account が残っている可能性があるため、
  // Cookie を維持して再試行できる状態を残す。
  if (response.status !== 204) {
    return response;
  }

  response.cookies.set("access_token", "", {
    path: "/",
    maxAge: 0,
  });
  response.cookies.set("refresh_token", "", {
    path: "/",
    maxAge: 0,
  });

  return response;
}
