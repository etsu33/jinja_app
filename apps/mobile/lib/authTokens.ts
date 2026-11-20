import AsyncStorage from "@react-native-async-storage/async-storage";

export const KEY_ACCESS = "auth:access_token";
export const KEY_REFRESH = "auth:refresh_token";

// ---- storage ----

export async function getAccessToken(): Promise<string | null> {
  return AsyncStorage.getItem(KEY_ACCESS);
}

export async function getRefreshToken(): Promise<string | null> {
  return AsyncStorage.getItem(KEY_REFRESH);
}

export async function setTokens(access: string, refresh: string): Promise<void> {
  await Promise.all([
    AsyncStorage.setItem(KEY_ACCESS, access),
    AsyncStorage.setItem(KEY_REFRESH, refresh),
  ]);
}

export async function setAccessToken(access: string): Promise<void> {
  await AsyncStorage.setItem(KEY_ACCESS, access);
}

export async function clearTokens(): Promise<void> {
  await Promise.all([
    AsyncStorage.removeItem(KEY_ACCESS),
    AsyncStorage.removeItem(KEY_REFRESH),
  ]);
}

// 文字列が残っているかではなく、まだ使えるかで判定する。
//
// 期限切れを見ていなかったため、ログインが切れたあとも画面は「ログイン中」と
// 出し続け、記録もPremiumも開けないのに理由が分からない状態になっていた。
// サーバー側のリフレッシュトークンの寿命は1日(simplejwtの既定値)なので、
// これは放っておくと全利用者が毎日踏む。
//
// アクセスが切れていても、リフレッシュが生きていれば続けられる(http.ts が
// 取り直す)。両方切れて初めて、ログインが切れたことになる。
export async function isLoggedIn(): Promise<boolean> {
  const [access, refresh] = await Promise.all([getAccessToken(), getRefreshToken()]);

  if (access && !isExpired(access)) return true;
  if (refresh && !isExpired(refresh)) return true;

  return false;
}

// ---- JWT helpers ----

type JwtPayload = { exp?: number };

function decodeBase64Url(input: string): string {
  const base64 = input.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");

  return globalThis.atob(padded);
}

export function readJwtExp(token: string): number | null {
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const decoded = decodeBase64Url(payload);
    const json = JSON.parse(decoded) as JwtPayload;
    return typeof json.exp === "number" ? json.exp : null;
  } catch {
    return null;
  }
}

// 期限を読んだうえで、すでに過ぎているか。
// 読めない形のトークンを「切れている」と決めつけると、こちらの都合で利用者を
// ログアウトさせてしまうため、読めないときは切れていないものとして扱う。
export function isExpired(token: string): boolean {
  const exp = readJwtExp(token);
  if (exp === null) return false;

  return exp <= Math.floor(Date.now() / 1000);
}

export function isExpiringSoon(token: string, skewSeconds = 60): boolean {
  const exp = readJwtExp(token);
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return exp - now <= skewSeconds;
}
