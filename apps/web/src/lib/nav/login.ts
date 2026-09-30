/**
 * Login 後に戻してよい内部パスの許可リスト。
 *
 * 追加するたびに「その画面が returnTo 経由の遷移で壊れないか」を確認すること。
 */
const SAFE_RETURN_TO_ROOTS = [
  "/shrines",
  "/mypage",
  "/concierge",
  "/billing",
  "/favorites",
  "/goshuin/new",
] as const;

/**
 * path 境界まで見て一致させる。
 *
 * `startsWith` だけだと `/favorites-xxx` や `/shrines-evil` のような
 * lookalike path まで許可してしまうため、次の境界のみを一致とみなす。
 *
 *   完全一致 / `/` の直後 / `?` の直後 / `#` の直後
 */
function isSafeInternalReturnTo(path: string): boolean {
  return SAFE_RETURN_TO_ROOTS.some(
    (root) =>
      path === root ||
      path.startsWith(`${root}/`) ||
      path.startsWith(`${root}?`) ||
      path.startsWith(`${root}#`),
  );
}

export function sanitizeNext(next: string | null | undefined): string | null {
  const t0 = (next ?? "").trim();
  if (!t0) return null;

  let t = t0;
  try {
    t = decodeURIComponent(t0);
  } catch {
    // ignore
  }

  if (!t.startsWith("/")) return null;
  if (t.startsWith("//")) return null;
  if (t.includes("://")) return null;

  if (t.startsWith("/auth/login")) return null;
  if (t.startsWith("/auth/register")) return null;
  if (t.startsWith("/login")) return null;
  if (t.startsWith("/signup")) return null;

  return isSafeInternalReturnTo(t) ? t : null;
}

export function normalizeReturnTo(input: string | null | undefined): string | null {
  const t0 = (input ?? "").trim();
  if (!t0) return null;

  let t = t0;
  try {
    t = decodeURIComponent(t0);
  } catch {
    // ignore
  }

  // 内部パス以外は reject
  if (!t.startsWith("/")) return null;
  if (t.startsWith("//")) return null;

  // URLスキームはすべて reject（内部相対パスのみ許可）
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(t)) return null;

  const [path, search = ""] = t.split("?", 2);
  if (!path.startsWith("/")) return null;
  if (path.startsWith("//")) return null;

  const params = new URLSearchParams(search);
  params.delete("returnTo");

  const nextSearch = params.toString();
  return nextSearch ? `${path}?${nextSearch}` : path;
}



export function sanitizeReturnTo(returnTo: string | null | undefined): string | null {
  return sanitizeNext(normalizeReturnTo(returnTo));
}

export function buildLoginHref(returnTo?: string | null): string {
  const safe = sanitizeReturnTo(returnTo);
  return safe ? `/auth/login?returnTo=${encodeURIComponent(safe)}` : "/auth/login";
}

export function buildRegisterHref(returnTo?: string | null): string {
  const safe = sanitizeReturnTo(returnTo);
  return safe ? `/auth/register?returnTo=${encodeURIComponent(safe)}` : "/auth/register";
}

export function buildLoginHrefFromCurrent(pathname: string, search: string): string {
  const current = `${pathname}${search || ""}`;
  return buildLoginHref(current);
}

export function buildRegisterHrefFromCurrent(pathname: string, search: string): string {
  const current = `${pathname}${search || ""}`;
  return buildRegisterHref(current);
}
