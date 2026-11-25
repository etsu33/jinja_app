// apps/web/src/lib/server/clientIdentity.ts
import "server-only";

import { createHmac } from "node:crypto";
import { isIP } from "node:net";

/**
 * WS-04（MD-2 = C）: BFF → Django に、Vercel が渡した client IP を HMAC 署名付きで添える。
 *
 * Backend（backend/shrine_project/throttling.py）は署名を検証できたときだけ、この IP を匿名 throttle の
 * 識別子に使う。署名できない条件（Vercel 外 / secret 未設定 / IP 不正）では何も付けず、Backend は
 * 従来どおり edge の peer identity を使う（fail-safe）。
 *
 * - secret は server-only の `KM_CLIENT_IDENTITY_SECRET`（ブラウザへ公開される env 名にしない）。
 * - secret・署名・IP はログに出さない。
 *
 * 署名方式（Backend と一致させる）:
 *   HMAC-SHA256(secret, ts + "\n" + METHOD + "\n" + path + "\n" + ip) を小文字 hex で。
 */

export const CLIENT_IP_HEADER = "X-KM-Client-IP";
export const CLIENT_TS_HEADER = "X-KM-Client-Ts";
export const CLIENT_SIG_HEADER = "X-KM-Client-Sig";

const MIN_SECRET_LENGTH = 32;
const IP_CHARS = /^[0-9A-Fa-f:.]{1,45}$/;

type HasHeaders = { headers: Pick<Headers, "get"> };

/**
 * Backend（Django）の origin として repo で使われている server-only の env 名。
 * 署名ヘッダはこれらの origin へのリクエストにだけ付ける（自アプリの BFF や他ホストへは送らない）。
 */
const BACKEND_ORIGIN_ENV_NAMES = [
  "DJANGO_ORIGIN",
  "BACKEND_ORIGIN",
  "DJANGO_API_BASE_URL",
  "BACKEND_BASE_URL",
  "BACKEND_URL",
] as const;

function identitySecret(): string | null {
  const secret = process.env.KM_CLIENT_IDENTITY_SECRET ?? "";
  return secret.length >= MIN_SECRET_LENGTH ? secret : null;
}

function originOf(value: string): string | null {
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
}

/** 署名できる実行環境か（Vercel 上で secret が設定されている）。request context を読む前の判定に使う。 */
export function clientIdentitySigningEnabled(): boolean {
  return process.env.VERCEL === "1" && identitySecret() !== null;
}

/** `url` が設定済みの Backend origin を指すか。 */
export function isBackendUrl(url: string): boolean {
  const target = originOf(url);
  if (!target) return false;
  return BACKEND_ORIGIN_ENV_NAMES.some((name) => {
    const value = process.env[name]?.trim();
    return Boolean(value) && originOf(value!) === target;
  });
}

/**
 * Vercel 上でのみ、Vercel が上書きする `x-forwarded-for` から client IP を読む。
 * 単一の IPv4 / IPv6 以外（リスト・空白・ポート付きなど）は使わない。
 */
export function trustedClientIp(req: HasHeaders): string | null {
  if (process.env.VERCEL !== "1") return null;
  const raw = req.headers.get("x-forwarded-for");
  if (!raw || !IP_CHARS.test(raw) || isIP(raw) === 0) return null;
  return raw;
}

export function signClientIdentity(secret: string, ts: string, method: string, path: string, ip: string): string {
  return createHmac("sha256", secret).update(`${ts}\n${method.toUpperCase()}\n${path}\n${ip}`, "utf8").digest("hex");
}

/**
 * Backend へのリクエストに付ける署名ヘッダ。署名できないときは空 object。
 * `upstream` は Backend の URL か絶対パス（query は署名対象外）。
 */
export function clientIdentityHeaders(
  req: HasHeaders | null | undefined,
  method: string,
  upstream: string,
): Record<string, string> {
  if (!req) return {};
  const secret = identitySecret();
  if (!secret) return {};
  const ip = trustedClientIp(req);
  if (!ip) return {};

  const path = new URL(upstream, "http://backend.invalid").pathname;
  const ts = String(Math.floor(Date.now() / 1000));
  return {
    [CLIENT_IP_HEADER]: ip,
    [CLIENT_TS_HEADER]: ts,
    [CLIENT_SIG_HEADER]: signClientIdentity(secret, ts, method, path, ip),
  };
}
