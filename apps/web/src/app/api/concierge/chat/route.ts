import { NextRequest, NextResponse } from "next/server";
import { djFetch } from "@/lib/server/backend";
import {
  isSecureRequest,
  setAccessTokenCookie,
  setAnonymousConciergeCookie,
  setRefreshTokenCookie,
} from "@/lib/server/authCookies";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

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

const ANON_COOKIE_BODY_FIELD = "_anon_cookie_value";

/**
 * Backend の chat body にある `_anon_cookie_value`（署名済みの匿名 credential）を取り出し、
 * browser へ返す body からは取り除く。値は HttpOnly cookie としてだけ browser へ渡す
 * （docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md F1）。
 * JSON object でない body、field を持たない body は 1 byte も変えない。
 */
function splitAnonCookieFromBody(body: string, phase: string): { body: string; anonCookieValue: string | null } {
  try {
    const json = JSON.parse(body);
    const hasField = json !== null && typeof json === "object" && !Array.isArray(json) && ANON_COOKIE_BODY_FIELD in json;
    const raw = hasField ? json[ANON_COOKIE_BODY_FIELD] : undefined;
    const anonCookieValue = typeof raw === "string" && raw ? raw : null;

    console.log("[BFF_ANON_COOKIE_FROM_BODY]", { phase, hasAnonCookieValue: Boolean(anonCookieValue) });

    if (!hasField) return { body, anonCookieValue: null };

    delete json[ANON_COOKIE_BODY_FIELD];
    return { body: JSON.stringify(json), anonCookieValue };
  } catch (error) {
    console.warn("[BFF_CHAT_PROXY] failed to parse anon cookie payload", {
      phase,
      error: error instanceof Error ? error.name : "unknown",
    });
    return { body, anonCookieValue: null };
  }
}

function buildChatResponse(upstream: Response, upstreamBody: string, phase: string, secure: boolean) {
  const { body, anonCookieValue } = splitAnonCookieFromBody(upstreamBody, phase);
  const res = buildProxyResponse(upstream, body);

  if (anonCookieValue) {
    setAnonymousConciergeCookie(res, anonCookieValue, { secure });
    console.log("[BFF_ANON_COOKIE_SET_RESULT]", { phase, attached: true });
  }

  return res;
}

function attachAuthCookies(res: NextResponse, refreshJson: RefreshResponse, secure: boolean) {
  if (refreshJson.access) {
    setAccessTokenCookie(res, refreshJson.access, { secure });
  }

  if (refreshJson.refresh) {
    setRefreshTokenCookie(res, refreshJson.refresh, { secure });
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
  const secureCookies = isSecureRequest(req);

  const doChat = (accessToken: string | null) => {
    const upstreamUrl = "/api/concierge/chat/";

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

        const res = buildChatResponse(upstream, await upstream.text(), "refresh-success", secureCookies);
        attachAuthCookies(res, refreshJson, secureCookies);

        console.log("[BFF_CHAT_RETURN] refresh-success");
        return res;
      }

      console.log("[BFF_CHAT_REFRESH] refresh ok but no access token");
    }

    const res = buildChatResponse(upstream, await upstream.text(), "refresh-fallback", secureCookies);
    res.cookies.delete("access_token");

    console.log("[BFF_CHAT_RETURN] refresh-fallback-delete-access");
    return res;
  }

  const res = buildChatResponse(upstream, await upstream.text(), "normal", secureCookies);

  console.log("[BFF_CHAT_RETURN] normal");
  return res;
}
