// apps/web/src/lib/api/auth.ts
import { markLoggedIn, markLoggedOut } from "@/lib/auth/loggedInMarker";

export type LoginInput = { username: string; password: string };

/**
 * Next.js API ルート経由の login（本体）
 *
 * 成功時は cookie の発行と合わせて client 側の logged-in マーカーも立てる。
 * これを login 成功の一部として扱わないと、この関数経由でログインした経路
 * （新規登録直後の自動ログイン）だけがマーカー無しの認証済み状態になり、
 * `/`・`/shrines/*`・`/concierge*` で Guest として描画されてしまう
 * （docs/audit/beta-core-flow-e2e-audit.md E2E-003）。
 *
 * 失敗時はマーカーを触らない（認証済みと誤認させない）。
 */
export async function login(body: LoginInput): Promise<void> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(msg || `login failed: ${res.status}`);
  }

  markLoggedIn();
}

/** 互換ラッパ */
export async function loginApi(username: string, password: string): Promise<void> {
  return login({ username, password });
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "same-origin",
  }).catch(() => {});

  // login と対になるよう、この経路でもマーカーを落とす。
  markLoggedOut();
}

export type SignupInput = { username: string; password: string; email: string };

/**
 * signup の失敗を「Backend が返した validation error」と
 * 「network / server failure」に切り分けられる形で表現するエラー。
 *
 * - `status`: HTTP status。fetch 自体が失敗した（= Backend に到達すらしていない）場合は null。
 * - `data`: Backend / BFF が返した body（JSON なら parse 済み、そうでなければ文字列）。
 */
export class SignupRequestError extends Error {
  readonly status: number | null;
  readonly data: unknown;

  constructor(message: string, options: { status: number | null; data?: unknown }) {
    super(message);
    this.name = "SignupRequestError";
    this.status = options.status;
    this.data = options.data ?? null;
  }
}

export async function signup(payload: SignupInput) {
  let res: Response;

  try {
    res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
  } catch (e) {
    throw new SignupRequestError(e instanceof Error ? e.message : "network error", {
      status: null,
    });
  }

  const text = await res.text().catch(() => "");

  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    throw new SignupRequestError(`signup failed: ${res.status}`, { status: res.status, data });
  }

  return (data ?? {}) as Record<string, unknown>;
}
