// apps/web/src/app/signup/SignupForm.tsx
"use client";

import { useRef, useState } from "react";
import { signup, login as loginApi } from "@/lib/api/auth";

type Props = {
  returnTo?: string | null;
};

// Backend（DRF の EmailField）を validation の正本としたうえで、
// 明らかな入力ミスを送信前に弾くための最小限のパターン。
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const PASSWORD_MIN_LENGTH = 8;

const GENERIC_NETWORK_ERROR = "通信に失敗しました。";
const GENERIC_SERVER_ERROR = "サーバーエラーが発生しました。";

/**
 * signup の失敗から status / body を取り出す。
 * `SignupRequestError`（`@/lib/api/auth`）が持つ形を duck typing で読む。
 * status が取れない失敗（例: 後続の login が投げる素の Error）は undefined を返し、
 * generic な通信エラーとして扱う。
 */
function readSignupFailure(err: unknown): { status: number | null | undefined; data: unknown } {
  if (err && typeof err === "object" && "status" in err) {
    const status = (err as { status: unknown }).status;
    if (typeof status === "number" || status === null) {
      const data = "data" in err ? (err as { data: unknown }).data : null;
      return { status, data };
    }
  }
  return { status: undefined, data: null };
}

/** Backend の validation error body を画面表示用の文字列にする。 */
export function formatValidationErrors(data: unknown): string {
  if (!data) return "";
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.map((v) => formatValidationErrors(v)).filter(Boolean).join(" ");

  if (typeof data === "object") {
    return Object.values(data as Record<string, unknown>)
      .map((v) => formatValidationErrors(v))
      .filter(Boolean)
      .join(" ");
  }

  return String(data);
}

export default function SignupForm({ returnTo }: Props) {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [email, setE] = useState("");
  const [loading, setL] = useState(false);
  const [error, setErr] = useState<string | null>(null);
  const inFlight = useRef(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inFlight.current || loading) return;

    const trimmedUsername = username.trim();
    const trimmedEmail = email.trim();

    if (!trimmedUsername) {
      setErr("ユーザー名を入力してください");
      return;
    }
    if (!trimmedEmail) {
      setErr("メールアドレスを入力してください");
      return;
    }
    if (!EMAIL_PATTERN.test(trimmedEmail)) {
      setErr("メールアドレスの形式が正しくありません");
      return;
    }
    if (password.length < PASSWORD_MIN_LENGTH) {
      setErr(`パスワードは${PASSWORD_MIN_LENGTH}文字以上で入力してください`);
      return;
    }

    setErr(null);
    setL(true);
    inFlight.current = true;

    try {
      const signupResult = await signup({
        username: trimmedUsername,
        password,
        email: trimmedEmail,
      });

      const normalizedUsername =
        signupResult &&
        typeof signupResult.username === "string"
          ? signupResult.username
          : trimmedUsername;

      // 登録直後の自動ログインは通常ログインと同じ canonical な遷移を通す。
      // `login()` が cookie と合わせて logged-in マーカーも立てるため、
      // このあとの full reload 後に AuthProvider が認証済みとして復帰する
      // （`/`・`/shrines/*`・`/concierge*` は `/api/users/me/` を自動で
      // 叩かないので、マーカーが無いと Guest 扱いになる）。
      // login が失敗した場合は catch へ抜け、マーカーは立たない。
      await loginApi({
        username: normalizedUsername,
        password,
      });

      window.location.replace(returnTo || "/mypage");
    } catch (err) {
      const { status, data } = readSignupFailure(err);

      if (status === 400) {
        // Backend が返した validation error。generic な通信エラーに丸めない。
        setErr(formatValidationErrors(data) || "入力内容をご確認ください。");
      } else if (status === 409) {
        setErr("そのユーザー名は既に使われています。");
      } else if (status !== null && status !== undefined && status >= 500) {
        setErr(GENERIC_SERVER_ERROR);
      } else {
        setErr(GENERIC_NETWORK_ERROR);
      }
    } finally {
      setL(false);
      inFlight.current = false;
    }
  };

  return (
    <main className="p-4 max-w-sm mx-auto">
      <h1 className="text-xl font-bold mb-4">新規登録</h1>

      {error && <div className="mb-4 rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700">{error}</div>}

      {/*
        type="email" によるブラウザ標準の interactive validation は抑止し（noValidate）、
        エラー表示をこのフォーム自身のメッセージ欄に一本化する。
        type 自体はモバイルのキーボード最適化のために残す。
      */}
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label className="mb-1 block text-sm">ユーザー名</label>
          <input
            className="w-full rounded border p-2"
            value={username}
            onChange={(e) => setU(e.target.value)}
            disabled={loading}
            autoComplete="username"
            aria-required="true"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm">メールアドレス</label>
          <input
            type="email"
            className="w-full rounded border p-2"
            value={email}
            onChange={(e) => setE(e.target.value)}
            disabled={loading}
            autoComplete="email"
            aria-required="true"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm">パスワード</label>
          <input
            type="password"
            className="w-full rounded border p-2"
            value={password}
            onChange={(e) => setP(e.target.value)}
            disabled={loading}
            autoComplete="new-password"
            aria-required="true"
          />
          <p className="mt-1 text-xs text-[var(--kt-color-text-secondary)]">8文字以上</p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-[var(--kt-color-action-primary)] px-4 py-2 text-[var(--kt-color-action-primary-text)] hover:bg-[var(--kt-color-action-primary-hover)] disabled:opacity-50"
        >
          {loading ? "作成中..." : "アカウント作成"}
        </button>
      </form>
    </main>
  );
}
