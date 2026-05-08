import { NextRequest, NextResponse } from "next/server";
import { djFetch } from "@/lib/server/backend";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

const ANON_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 90;
const ACCESS_COOKIE_MAX_AGE_SECONDS = 60 * 60;
const REFRESH_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

type RefreshResponse = { access?: string; refresh?: string };

function getResponseSetCookies(upstream: Response): string[] {
  const headers = upstream.headers as Headers & {
    getSetCookie?: () => string[];
    raw?: () => Record<string, string[]>;
  };

  if (typeof headers.getSetCookie === "function") {
    return headers.getSetCookie().filter(Boolean);
  }

  const raw = typeof headers.raw === "function" ? headers.raw()?.["set-cookie"] ?? [] : [];
  if (raw.length > 0) return raw.filter(Boolean);

  const single = upstream.headers.get("set-cookie");
  return single ? [single] : [];
}

function attachAnonCookieFromBody(res: NextResponse, body: string, phase: string) {
  try {
    const json = JSON.parse(body);
    const anonCookieValue = json?._anon_cookie_value;

    console.log("[BFF_ANON_COOKIE_FROM_BODY]", { phase, hasAnonCookieValue: Boolean(anonCookieValue) });

    if (!anonCookieValue) return;

    res.cookies.set("concierge_anon_id", anonCookieValue, {
      httpOnly: true,
      sameSite: "none",
      secure: true,
      path: "/",
      maxAge: ANON_COOKIE_MAX_AGE_SECONDS,
    });

    const serialized = res.cookies.get("concierge_anon_id");
    console.log("[BFF_ANON_COOKIE_SET_RESULT]", { phase, serialized });
  } catch (error) {
    console.warn("[BFF_CHAT_PROXY] failed to parse anon cookie payload", { phase, error });
  }
}

function attachAuthCookies(res: NextResponse, refreshJson: RefreshResponse) {
  if (refreshJson.access) {
    res.cookies.set("access_token", refreshJson.access, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: ACCESS_COOKIE_MAX_AGE_SECONDS,
    });
  }

  if (refreshJson.refresh) {
    res.cookies.set("refresh_token", refreshJson.refresh, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: REFRESH_COOKIE_MAX_AGE_SECONDS,
    });
  }
}


function buildProxyResponse(upstream: Response, body: string) {
  const ct = upstream.headers.get("content-type") || "application/json";
  const setCookies = getResponseSetCookies(upstream);

  console.log("[BFF_CHAT_PROXY]", {
    status: upstream.status,
    contentType: ct,
    hasSetCookie: setCookies.length > 0,
    setCookieCount: setCookies.length,
    setCookies,
  });

  const res = new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type": ct,
    },
  });

  for (const cookie of setCookies) {
    res.headers.append("set-cookie", cookie);
  }

  return res;
}

export async function POST(req: NextRequest) {
  const payload = await req.text();
  const contentType = req.headers.get("content-type") ?? "application/json";
  const refreshToken = req.cookies.get("refresh_token")?.value ?? null;

  const doChat = (accessToken: string | null) => {
    const upstreamUrl = "/api/concierge/chat/";

    console.log("🔥 BFF → backend 投げる直前 🔥");
    console.log("🔥 BFF → backend URL", upstreamUrl);

    return djFetch(req, upstreamUrl, {
      method: "POST",
      headers: {
        "content-type": contentType,
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: payload,
    });
  };

  const accessToken = req.cookies.get("access_token")?.value ?? null;
  let upstream = await doChat(accessToken);

  console.log("[BFF_CHAT_ENTRY]", {
    hit: true,
  });

  if (upstream.status === 401 && refreshToken) {
    console.log("[BFF_CHAT_REFRESH_FLOW] entered");

    const refreshUpstream = await djFetch(req, "/api/auth/jwt/refresh/", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    console.log("[BFF_CHAT_REFRESH]", {
      refreshStatus: refreshUpstream.status,
      refreshOk: refreshUpstream.ok,
    });

    if (refreshUpstream.ok) {
      const refreshJson = (await refreshUpstream.json()) as RefreshResponse;
      const nextAccess = refreshJson.access ?? null;

      console.log("[BFF_CHAT_REFRESH_JSON]", {
        hasNextAccess: Boolean(nextAccess),
        hasNextRefresh: Boolean(refreshJson.refresh),
      });

      if (nextAccess) {
        upstream = await doChat(nextAccess);

        const body = await upstream.text();
        const res = buildProxyResponse(upstream, body);
        attachAnonCookieFromBody(res, body, "refresh-success");
        attachAuthCookies(res, refreshJson);

        console.log("[BFF_CHAT_RETURN] refresh-success");
        return res;
      }

      console.log("[BFF_CHAT_REFRESH] refresh ok but no access token");
    }

    const body = await upstream.text();
    const res = buildProxyResponse(upstream, body);
    attachAnonCookieFromBody(res, body, "refresh-fallback");
    res.cookies.delete("access_token");

    console.log("[BFF_CHAT_RETURN] refresh-fallback-delete-access");
    return res;
  }

  const body = await upstream.text();
  const res = buildProxyResponse(upstream, body);

  attachAnonCookieFromBody(res, body, "normal");

  console.log("[BFF_CHAT_RETURN] normal");
  return res;
}
