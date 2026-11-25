// apps/web/src/lib/concierge/conciergeLocalState.ts
//
// Concierge の browser storage（相談 state の local cache）の key と、identity 境界での消去。
// どの key も identity を含まないため、ログイン / ログアウト / アカウント切替の境界で消す。
// docs/audit/concierge-thread-authorization-isolation-audit.md

/** localStorage: thread id ごとの local event（assistant_state / 送受信メッセージ）。 */
export const CONCIERGE_EVENTS_STORAGE_KEY = "concierge:eventsByThread";

/** sessionStorage: thread 未保存の匿名相談結果の snapshot（入口 route の復元用）。 */
export const CONCIERGE_ANON_SNAPSHOT_STORAGE_KEY = "concierge:anonymousSnapshot:v1";

/** thread id ごとの local event cache を消す。 */
export function clearConciergeThreadCache(): void {
  try {
    localStorage.removeItem(CONCIERGE_EVENTS_STORAGE_KEY);
  } catch {
    // ignore（storage 不可の環境）
  }
}

/** 匿名相談 snapshot を消す。 */
export function clearConciergeAnonymousSnapshot(): void {
  try {
    sessionStorage.removeItem(CONCIERGE_ANON_SNAPSHOT_STORAGE_KEY);
  } catch {
    // ignore
  }
}
