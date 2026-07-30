import { getAccessToken, getRefreshToken, isExpiringSoon, setAccessToken } from "./authTokens";
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

  constructor(status: number, message: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
  }
}

export function isHttpError(error: unknown): error is HttpError {
  return error instanceof HttpError;
}

type TokenRefreshResponse = {
  access: string;
};

async function refreshAccessToken(): Promise<string | null> {
  const refresh = await getRefreshToken();
  if (!refresh) return null;

  const res = await fetch(`${BASE_URL}/auth/jwt/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) return null;

  const data = (await res.json()) as TokenRefreshResponse;
  if (!data.access) return null;

  await setAccessToken(data.access);
  return data.access;
}

async function getValidAccessToken(): Promise<string> {
  const access = await getAccessToken();

  if (access && !isExpiringSoon(access)) {
    return access;
  }

  const refreshed = await refreshAccessToken();
  if (refreshed) return refreshed;

  if (access) return access;

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
    throw new HttpError(res.status, `HTTP ${res.status}: ${text || res.statusText}`);
  }

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
      throw new HttpError(first.status, `HTTP ${first.status}: ${text || first.statusText}`);
    }
    return (await first.json()) as T;
  }

  const refreshed = await refreshAccessToken();
  if (!refreshed) {
    throw new UnauthenticatedError("Authentication token expired");
  }

  const retryHeaders = mergeHeaders(
    {
      "Content-Type": "application/json",
      Authorization: `Bearer ${refreshed}`,
    },
    init.headers,
  );

  const retry = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: retryHeaders,
  });

  if (!retry.ok) {
    const text = await retry.text().catch(() => "");
    throw new HttpError(retry.status, `HTTP ${retry.status}: ${text || retry.statusText}`);
  }

  return (await retry.json()) as T;
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

// テストやデバッグ用
export const __internal = { BASE_URL, refreshAccessToken, getValidAccessToken };

