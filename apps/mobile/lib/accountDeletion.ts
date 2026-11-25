import { resetAnalyticsIdentity, track } from "./analytics";
import { clearTokens } from "./authTokens";
import { deleteAuth } from "./http";
import { clearLocalUserData } from "./localUserData";

export const ACCOUNT_DELETION_MESSAGES = {
  confirmTitle: "退会しますか？",
  confirmBody: "退会するとアカウントと記録は削除され、元に戻すことはできません。",
  finalConfirmTitle: "本当に退会しますか？",
  finalConfirmBody:
    "この操作は取り消せません。Premiumをご利用中の場合、Premiumの購読も停止されます。",
  done: "退会しました",
  failed: "退会できませんでした。時間をおいて再度お試しください",
} as const;

export type AccountDeletionResult = { ok: true } | { ok: false; message: string };

/**
 * DELETE /users/me/ を呼ぶ。
 * - 204: account_deleted を送り、解析用IDを作り直してから、トークンと端末内の利用者データを消去して ok を返す
 * - 503 / その他のエラー / ネットワークエラー: ログイン状態を維持したまま失敗を返す
 */
export async function deleteAccount(): Promise<AccountDeletionResult> {
  try {
    await deleteAuth("/users/me/");
  } catch {
    return { ok: false, message: ACCOUNT_DELETION_MESSAGES.failed };
  }

  // サーバー側の削除は確定しているため、端末側の消去に失敗しても退会完了として扱う。
  // 退会の印は、作り直す前の解析用IDのまま届くよう reset より先に送る。
  // payload にアカウントID・メールは入れない(退会前の利用履歴を匿名のまま残すため)。
  track("account_deleted", { platform: "mobile" });
  await resetAnalyticsIdentity();

  try {
    await clearTokens();
  } catch {
    // clearLocalUserData でもトークンのキーを消去する
  }
  try {
    await clearLocalUserData();
  } catch {
    // 端末側の消去失敗で退会完了の表示を妨げない
  }

  return { ok: true };
}
