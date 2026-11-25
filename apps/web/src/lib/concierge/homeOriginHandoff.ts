// apps/web/src/lib/concierge/homeOriginHandoff.ts
//
// トップページで選んだ出発地を、/concierge の自動送信（?theme=）へ渡す。
// - 位置は URL に載せない（履歴・ログに残さないため）。同じタブの sessionStorage で1回だけ渡す
// - /concierge は読んだらすぐ消す（読み直しや別の相談に持ち越さない）
// - 古い値（HANDOFF_TTL_MS より前）は使わない
import type { UserOrigin, UserOriginSource } from "../../../../../packages/shared/userOrigin";

export const HOME_ORIGIN_HANDOFF_KEY = "kamimusubi:home-origin-handoff";
const HANDOFF_TTL_MS = 10 * 60 * 1000;

const SOURCES: readonly UserOriginSource[] = ["device", "station", "address", "prefecture"];

type StoredHandoff = { origin: UserOrigin; savedAt: number };

function isUserOrigin(value: unknown): value is UserOrigin {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.latitude === "number" &&
    typeof v.longitude === "number" &&
    Number.isFinite(v.latitude) &&
    Number.isFinite(v.longitude) &&
    Math.abs(v.latitude) <= 90 &&
    Math.abs(v.longitude) <= 180 &&
    SOURCES.includes(v.source as UserOriginSource) &&
    (v.accuracy === "precise" || v.accuracy === "approximate") &&
    (v.displayName === undefined || typeof v.displayName === "string")
  );
}

/** トップページから /concierge へ移る直前に呼ぶ。origin が null なら前の値を消す。 */
export function saveHomeOriginHandoff(origin: UserOrigin | null, now: number = Date.now()): void {
  try {
    if (!origin) {
      window.sessionStorage.removeItem(HOME_ORIGIN_HANDOFF_KEY);
      return;
    }
    const payload: StoredHandoff = { origin, savedAt: now };
    window.sessionStorage.setItem(HOME_ORIGIN_HANDOFF_KEY, JSON.stringify(payload));
  } catch {
    // storage が使えない環境では渡さない（相談は位置なしで続けられる）
  }
}

/** /concierge で1回だけ読む。読んだら必ず消す。 */
export function consumeHomeOriginHandoff(now: number = Date.now()): UserOrigin | null {
  let raw: string | null;
  try {
    raw = window.sessionStorage.getItem(HOME_ORIGIN_HANDOFF_KEY);
    window.sessionStorage.removeItem(HOME_ORIGIN_HANDOFF_KEY);
  } catch {
    return null;
  }
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<StoredHandoff>;
    if (typeof parsed.savedAt !== "number" || now - parsed.savedAt > HANDOFF_TTL_MS || now < parsed.savedAt) {
      return null;
    }
    return isUserOrigin(parsed.origin) ? parsed.origin : null;
  } catch {
    return null;
  }
}
