// マイページの生年月日を、ログイン中ならサーバーにも保存する。
//
// 2026-11-26 えつこさん決定。コンシェルジュの結果に添える「今月の方角」は、
// サーバーのプロフィール（users.UserProfile.birthday）に生年月日がある、ログイン中の人にだけ出る
// （backend/temples/services/concierge_month_direction.py）。モバイルの生年月日は端末に
// だけ保存していたため、ログイン中はサーバーにも同じ値を送る。
//
// - ログインしていない人の生年月日は、今までどおり端末にだけ保存する（サーバーには送らない）
// - サーバーへの保存に失敗しても、端末の保存はそのまま（画面の操作は止めない）
// - 退会すると、サーバーのプロフィールごと生年月日も消える（users/services/account_deletion.py の user.delete()）
// - 生年月日の値はログに出さない
import { getRefreshToken } from "./authTokens";
import { getAuth, isUnauthenticatedError, patchAuth } from "./http";
import { normalizeBirthday } from "./profile";

const ME_PATH = "/users/me/";

type MeResponse = {
  profile?: { birthday?: unknown } | null;
};

export type BirthdayPushResult = "saved" | "skipped" | "failed";

async function hasSession(): Promise<boolean> {
  try {
    return Boolean(await getRefreshToken());
  } catch {
    return false;
  }
}

// 端末で決まった生年月日をサーバーへ送る。ログインしていなければ何もしない。
export async function pushBirthdayToServer(birthday: string | null | undefined): Promise<BirthdayPushResult> {
  const normalized = normalizeBirthday(birthday ?? undefined);
  if (!normalized) return "skipped";
  if (!(await hasSession())) return "skipped";
  try {
    await patchAuth<unknown>(ME_PATH, { birthday: normalized });
    return "saved";
  } catch (error) {
    return isUnauthenticatedError(error) ? "skipped" : "failed";
  }
}

// サーバーに保存されている生年月日（YYYY-MM-DD）。ログインしていない・無い・取れないときは null。
export async function pullBirthdayFromServer(): Promise<string | null> {
  if (!(await hasSession())) return null;
  try {
    const me = await getAuth<MeResponse>(ME_PATH);
    const raw = me?.profile?.birthday;
    return typeof raw === "string" ? (normalizeBirthday(raw) ?? null) : null;
  } catch {
    return null;
  }
}

// マイページを開いたときに揃える。
// - サーバーに値があり、端末と違えば、サーバーの値を端末に入れる（アカウントの値を正とする）
// - サーバーに値が無く、端末に値があれば、端末の値をサーバーへ送る
export async function syncBirthdayWithServer({
  localBirthday,
  setLocalBirthday,
}: {
  localBirthday: string | null | undefined;
  setLocalBirthday: (value: string) => void;
}): Promise<"pulled" | "pushed" | "unchanged"> {
  if (!(await hasSession())) return "unchanged";
  const local = normalizeBirthday(localBirthday ?? undefined) ?? null;
  const server = await pullBirthdayFromServer();
  if (server && server !== local) {
    setLocalBirthday(server);
    return "pulled";
  }
  if (!server && local) {
    return (await pushBirthdayToServer(local)) === "saved" ? "pushed" : "unchanged";
  }
  return "unchanged";
}
