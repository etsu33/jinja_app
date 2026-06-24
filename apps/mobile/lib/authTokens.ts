import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY_ACCESS = "auth:access_token";
const KEY_REFRESH = "auth:refresh_token";

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

export function isExpiringSoon(token: string, skewSeconds = 60): boolean {
  const exp = readJwtExp(token);
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return exp - now <= skewSeconds;
}
