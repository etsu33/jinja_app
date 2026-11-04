import { isHttpError, post } from "./http";
import { setTokens } from "./authTokens";

// サインアップの順序とエラーの扱いは apps/web/src/app/signup/SignupForm.tsx に揃える。
// 1. POST /users/signup/
// 2. 成功したら続けて POST /auth/jwt/create/（自動ログイン）
// 3. setTokens
// 400 は Backend の validation error として扱い、generic な通信エラーに丸めない。

export const PASSWORD_MIN_LENGTH = 8;

// Backend（DRF の EmailField）を validation の正本としたうえで、
// 明らかな入力ミスを送信前に弾くための最小限のパターン（web と同一）。
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const SIGNUP_MESSAGES = {
  usernameRequired: "ユーザー名を入力してください",
  emailRequired: "メールアドレスを入力してください",
  emailInvalid: "メールアドレスの形式が正しくありません",
  passwordTooShort: `パスワードは${PASSWORD_MIN_LENGTH}文字以上で入力してください`,
  validationFallback: "入力内容をご確認ください。",
  conflict: "そのユーザー名は既に使われています。",
  server: "サーバーエラーが発生しました。",
  network: "通信に失敗しました。",
  autoLoginFailed: "アカウントは作成されましたが、ログインできませんでした。ログイン画面からログインしてください。",
} as const;

export type SignupInput = {
  username: string;
  email: string;
  password: string;
};

export type SignupField = "username" | "email" | "password";

export type SignupFieldErrors = Partial<Record<SignupField, string>> & {
  // 特定の入力項目に紐づかないエラー（non_field_errors / detail など）
  form?: string;
};

export type SignupResult =
  | { ok: true; kind: "success" }
  | { ok: false; kind: "validation"; errors: SignupFieldErrors }
  | { ok: false; kind: "conflict" | "server" | "network" | "autoLoginFailed"; message: string };

type JwtCreateResponse = {
  access: string;
  refresh: string;
};

const FIELD_KEYS: readonly SignupField[] = ["username", "email", "password"];

function flattenMessages(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(flattenMessages).filter(Boolean).join(" ");
  if (typeof value === "object") {
    return Object.values(value as Record<string, unknown>)
      .map(flattenMessages)
      .filter(Boolean)
      .join(" ");
  }
  return String(value);
}

/** 送信前の入力チェック。web の SignupForm と同じ条件・文言。 */
export function validateSignupInput(input: SignupInput): SignupFieldErrors {
  const errors: SignupFieldErrors = {};
  const username = input.username.trim();
  const email = input.email.trim();

  if (!username) errors.username = SIGNUP_MESSAGES.usernameRequired;
  if (!email) errors.email = SIGNUP_MESSAGES.emailRequired;
  else if (!EMAIL_PATTERN.test(email)) errors.email = SIGNUP_MESSAGES.emailInvalid;
  if (input.password.length < PASSWORD_MIN_LENGTH) errors.password = SIGNUP_MESSAGES.passwordTooShort;

  return errors;
}

export function hasSignupErrors(errors: SignupFieldErrors): boolean {
  return Object.values(errors).some(Boolean);
}

/**
 * 400 の本文を項目ごとのエラーに振り分ける。
 * username / email / password 以外のキーはフォーム全体のエラーにまとめる。
 * JSON でない本文はそのままフォーム全体のエラーとして扱う。
 */
export function parseSignupFieldErrors(body: string): SignupFieldErrors {
  if (!body) return { form: SIGNUP_MESSAGES.validationFallback };

  let data: unknown;
  try {
    data = JSON.parse(body);
  } catch {
    return { form: body };
  }

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return { form: flattenMessages(data) || SIGNUP_MESSAGES.validationFallback };
  }

  const errors: SignupFieldErrors = {};
  const rest: string[] = [];

  for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
    const message = flattenMessages(value);
    if (!message) continue;
    if ((FIELD_KEYS as readonly string[]).includes(key)) {
      errors[key as SignupField] = message;
    } else {
      rest.push(message);
    }
  }

  if (rest.length > 0) errors.form = rest.join(" ");
  if (!hasSignupErrors(errors)) errors.form = SIGNUP_MESSAGES.validationFallback;

  return errors;
}

/**
 * サインアップ → 自動ログイン → トークン保存までを行う。
 * 画面遷移は呼び出し側（app/signup.tsx）が ok: true を受けて行う。
 */
export async function signupAndLogin(input: SignupInput): Promise<SignupResult> {
  const username = input.username.trim();
  const email = input.email.trim();

  let signupResponse: unknown;
  try {
    signupResponse = await post<unknown>("/users/signup/", {
      username,
      email,
      password: input.password,
    });
  } catch (error) {
    if (isHttpError(error)) {
      if (error.status === 400) {
        return { ok: false, kind: "validation", errors: parseSignupFieldErrors(error.body) };
      }
      if (error.status === 409) {
        return { ok: false, kind: "conflict", message: SIGNUP_MESSAGES.conflict };
      }
      if (error.status >= 500) {
        return { ok: false, kind: "server", message: SIGNUP_MESSAGES.server };
      }
    }
    return { ok: false, kind: "network", message: SIGNUP_MESSAGES.network };
  }

  // Backend が正規化した username を返した場合はそれでログインする（web と同じ）。
  const normalizedUsername =
    signupResponse &&
    typeof signupResponse === "object" &&
    typeof (signupResponse as { username?: unknown }).username === "string"
      ? (signupResponse as { username: string }).username
      : username;

  try {
    const tokens = await post<JwtCreateResponse>("/auth/jwt/create/", {
      username: normalizedUsername,
      password: input.password,
    });
    await setTokens(tokens.access, tokens.refresh);
  } catch {
    // アカウントは作成済みのため、再度サインアップさせずログイン画面へ誘導する。
    return { ok: false, kind: "autoLoginFailed", message: SIGNUP_MESSAGES.autoLoginFailed };
  }

  return { ok: true, kind: "success" };
}
