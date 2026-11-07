import { clearTokens } from "./authTokens";
import { getAuth } from "./http";

export const LOGOUT_MESSAGES = {
  confirmTitle: "ログアウトしますか？",
  confirmAction: "ログアウト",
  cancel: "キャンセル",
  /** ユーザー名が取れないときに、ログイン中の欄に出す文言。 */
  signedInFallbackName: "ログイン中",
} as const;

/**
 * ログアウト。端末に残したログインの印(アクセストークン・リフレッシュトークン)を消すだけ。
 *
 * - Web と同じく、バックエンドには何も送らない(印をブラックリストに入れることはしない)。
 * - PostHog の利用者の印は切り替えない(resetAnalyticsIdentity は呼ばない)。identify を
 *   使っていないため切り替えても守られるものがなく、同じ人の記録が分かれるだけなので。
 * - 端末内の利用者データ(clearLocalUserData)は消さない。御朱印・お気に入りなどが
 *   サーバーとつながっているか分からず、消すと元に戻せないおそれがあるため。
 * - 印の消去に失敗しても、ログアウトの表示は止めない(退会と同じ考え方)。
 */
export async function logout(): Promise<void> {
  try {
    await clearTokens();
  } catch {
    // 消去に失敗しても、ログアウトの表示を妨げない
  }
}

export type LogoutAlertButton = {
  text: string;
  style?: "default" | "cancel" | "destructive";
  onPress?: () => void;
};

export type LogoutAlert = (title: string, message: string | undefined, buttons: LogoutAlertButton[]) => void;

/**
 * 「ログアウトしますか？」の確認を出し、「ログアウト」を選んだときだけ onConfirm を呼ぶ。
 * 「キャンセル」やダイアログを閉じたときは何もしない。
 */
export function confirmLogout(alert: LogoutAlert, onConfirm: () => void): void {
  alert(LOGOUT_MESSAGES.confirmTitle, undefined, [
    { text: LOGOUT_MESSAGES.cancel, style: "cancel" },
    { text: LOGOUT_MESSAGES.confirmAction, style: "destructive", onPress: onConfirm },
  ]);
}

/** GET /users/me/ からユーザー名を取る。取れないときは null。 */
export async function fetchAccountUsername(): Promise<string | null> {
  try {
    const me = await getAuth<{ username?: unknown }>("/users/me/");
    const username = typeof me?.username === "string" ? me.username.trim() : "";
    return username || null;
  } catch {
    return null;
  }
}
