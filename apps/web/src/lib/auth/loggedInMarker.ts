// apps/web/src/lib/auth/loggedInMarker.ts
//
// 「このブラウザは直近ログインに成功している」ことを表す client 側マーカー。
//
// AuthProvider はマウント時、`shouldAutoFetchMe()` が false を返す route
// （`/`・`/shrines/*`・`/concierge*`）では `/api/users/me/` を叩かない。
// そこで認証済みかどうかを判断する唯一の手掛かりがこのマーカーであり、
// 「ログイン経路を通ったのにマーカーが立っていない」状態になると、認証済み
// ユーザーがそれらの route で Guest として描画されてしまう
// （docs/audit/beta-core-flow-e2e-audit.md E2E-003）。
//
// そのためマーカーの読み書きは必ずこのモジュールに集約し、ログイン経路ごとに
// 実装を持たせない。
//
// 保存先は localStorage で、値そのものは真偽値のみ。認証情報・個人情報は
// 一切置かない（cookie 側が正本で、これはあくまで「/me を叩くべきか」の
// ヒントである）。private mode 等で localStorage が使えない環境でも例外を
// 投げずに縮退する。

const LOGGED_IN_MARKER_KEY = "auth:logged_in";

export function markLoggedIn(): void {
  try {
    localStorage.setItem(LOGGED_IN_MARKER_KEY, "1");
  } catch {
    // ignore
  }
}

export function markLoggedOut(): void {
  try {
    localStorage.removeItem(LOGGED_IN_MARKER_KEY);
  } catch {
    // ignore
  }
}

export function maybeLoggedIn(): boolean {
  try {
    return localStorage.getItem(LOGGED_IN_MARKER_KEY) === "1";
  } catch {
    return false;
  }
}
