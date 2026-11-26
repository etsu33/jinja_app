// モバイルのコンシェルジュの送信。ログイン中ならログイン情報を付ける。
//
// 2026-11-26 えつこさん決定。これまでモバイルはログインしていても `post`（ログイン情報なし）で
// 送っていたため、Backend からはログインしていない人に見えていた:
// - Premium の人も、ログインしていない人と同じ回数の扱いになる（backend/temples/services/quota_policy.py）
// - 「今月の方角」（ログイン中で生年月日を登録した人だけ）が出ない
//
// Web と同じく、ログイン中は JWT を付けて送る。トークンが使えない（期限切れで更新もできない）ときは、
// モバイルのコンパス（lib/compass.ts）と同じく、付けずに送り直す。
import { getRefreshToken } from "./authTokens";
import { isUnauthenticatedError, post, postAuth } from "./http";

export const CONCIERGE_CHAT_PATH = "/concierge/chat/";

async function hasSession(): Promise<boolean> {
  try {
    return Boolean(await getRefreshToken());
  } catch {
    return false;
  }
}

export async function postConciergeChat<T>(body: unknown): Promise<T> {
  if (await hasSession()) {
    try {
      return await postAuth<T>(CONCIERGE_CHAT_PATH, body);
    } catch (error) {
      if (!isUnauthenticatedError(error)) throw error;
    }
  }
  return post<T>(CONCIERGE_CHAT_PATH, body);
}
