import { clearTokens, getAccessToken, getRefreshToken, isExpiringSoon, setAccessToken } from "./authTokens";
const BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export class UnauthenticatedError extends Error {
  constructor(message = "Authentication token is missing") {
    super(message);
    this.name = "UnauthenticatedError";
  }
}

export function isUnauthenticatedError(error: unknown): error is UnauthenticatedError {
  return error instanceof UnauthenticatedError;
}

// HTTPステータスを保持するエラー。401(UnauthenticatedError)以外の異常応答(403/404/500等)を
// 呼び出し側がstatusで区別できるようにする(メッセージ文字列のparseに頼らない)。
export class HttpError extends Error {
  status: number;
  // 異常応答の本文(未加工の文字列)。400のフィールドエラー等を呼び出し側で解釈するために保持する。
  body: string;

  constructor(status: number, message: string, body = "") {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.body = body;
  }
}

export function isHttpError(error: unknown): error is HttpError {
  return error instanceof HttpError;
}

type TokenRefreshResponse = {
  access: string;
};

// リフレッシュの結果は3通りあり、区別しないと利用者を不当にログアウトさせる。
//
//   "refreshed" … 新しいアクセストークンが取れた
//   "rejected"  … サーバーがこのリフレッシュトークンを明確に拒んだ(401/400)。
//                 期限切れか失効。もう使えないので捨ててよい。
//   "unreachable" … 届かなかった(5xx など)。トークンの正否は分からない。
//                 Render の無料枠は一定時間で眠るため、これは普通に起きる。
//                 ここで捨てると、サーバーが眠っていただけでログアウトになる。
type RefreshOutcome =
  | { kind: "refreshed"; access: string }
  | { kind: "rejected" }
  | { kind: "unreachable" };

async function refreshAccessToken(): Promise<RefreshOutcome> {
  const refresh = await getRefreshToken();
  if (!refresh) return { kind: "rejected" };

  const res = await fetch(`${BASE_URL}/auth/jwt/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    return res.status === 401 || res.status === 400 ? { kind: "rejected" } : { kind: "unreachable" };
  }

  const data = (await res.json()) as TokenRefreshResponse;
  if (!data.access) return { kind: "unreachable" };

  await setAccessToken(data.access);
  return { kind: "refreshed", access: data.access };
}

async function getValidAccessToken(): Promise<string> {
  const access = await getAccessToken();

  if (access && !isExpiringSoon(access)) {
    return access;
  }

  const outcome = await refreshAccessToken();
  if (outcome.kind === "refreshed") return outcome.access;

  // 届かなかっただけなら、手元のトークンで投げてみる価値がある。
  if (access) return access;

  if (outcome.kind === "rejected") await clearTokens();

  throw new UnauthenticatedError();
}

function mergeHeaders(base: HeadersInit, extra?: HeadersInit): HeadersInit {
  return {
    ...base,
    ...(extra ?? {}),
  };
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new HttpError(res.status, `HTTP ${res.status}: ${text || res.statusText}`, text);
  }

  return (await res.json()) as T;
}

// 204 No Content は本文が無いため res.json() を呼ばずに undefined を返す。
async function readAuthBody<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function requestAuth<T>(path: string, init: RequestInit): Promise<T> {
  const access = await getValidAccessToken();
  const headers = mergeHeaders(
    {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access}`,
    },
    init.headers,
  );

  const first = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (first.status !== 401) {
    if (!first.ok) {
      const text = await first.text().catch(() => "");
      throw new HttpError(first.status, `HTTP ${first.status}: ${text || first.statusText}`, text);
    }
    return readAuthBody<T>(first);
  }

  // ここに来た時点で、サーバーはアクセストークンを401で拒んでいる。
  const outcome = await refreshAccessToken();
  if (outcome.kind !== "refreshed") {
    // 拒まれたのなら、この組み合わせはもう使えない。残しておくと
    // isLoggedIn() が「ログイン中」と言い続け、利用者は自分でログアウトを
    // 探す以外に復帰できなくなる。届かなかっただけのときは残す。
    if (outcome.kind === "rejected") await clearTokens();

    throw new UnauthenticatedError("Authentication token expired");
  }

  const retryHeaders = mergeHeaders(
    {
      "Content-Type": "application/json",
      Authorization: `Bearer ${outcome.access}`,
    },
    init.headers,
  );

  const retry = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: retryHeaders,
  });

  if (!retry.ok) {
    const text = await retry.text().catch(() => "");
    throw new HttpError(retry.status, `HTTP ${retry.status}: ${text || retry.statusText}`, text);
  }

  return readAuthBody<T>(retry);
}

export async function get<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...init,
    headers: mergeHeaders({ "Content-Type": "application/json" }, init?.headers),
  });
}

export async function post<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...init,
    method: "POST",
    headers: mergeHeaders({ "Content-Type": "application/json" }, init?.headers),
    body: JSON.stringify(body),
  });
}

export async function getAuth<T>(path: string, init?: RequestInit): Promise<T> {
  return requestAuth<T>(path, {
    ...init,
    method: "GET",
  });
}

export async function postAuth<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  return requestAuth<T>(path, {
    ...init,
    method: "POST",
    body: JSON.stringify(body),
  });
}

// 204(本文なし)の場合は undefined を返す。
export async function deleteAuth<T = void>(path: string, init?: RequestInit): Promise<T> {
  return requestAuth<T>(path, {
    ...init,
    method: "DELETE",
  });
}

// テストやデバッグ用
export const __internal = { BASE_URL, refreshAccessToken, getValidAccessToken };

