// ログインしているかどうかの判定。
//
// 以前は AsyncStorage に文字列が残っているかだけを見ていた。そのため、
// ログインが切れたあとも画面は「ログイン中」と出し続け、記録もPremiumも
// 開けないのに理由が分からない状態になっていた。
//
// サーバー側のリフレッシュトークンの寿命は1日(simplejwtの既定値)なので、
// これは一部の利用者の不運ではなく、全員が毎日踏む。
import { beforeEach, describe, expect, it, vi } from "vitest";

const getItemMock = vi.fn();

vi.mock("@react-native-async-storage/async-storage", () => ({
  default: {
    getItem: (...args: unknown[]) => getItemMock(...args),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
}));

import { KEY_ACCESS, KEY_REFRESH, isExpired, isLoggedIn } from "../authTokens";

/** exp だけを持つ JWT を組み立てる(署名は検証しないので不要)。 */
function tokenExpiringIn(seconds: number): string {
  const payload = { exp: Math.floor(Date.now() / 1000) + seconds };
  const body = globalThis.btoa(JSON.stringify(payload)).replace(/=+$/, "");
  return `header.${body}.signature`;
}

const LIVE = tokenExpiringIn(60 * 60);
const DEAD = tokenExpiringIn(-60 * 60);

function storage(values: { access?: string | null; refresh?: string | null }) {
  getItemMock.mockImplementation(async (key: string) => {
    if (key === KEY_ACCESS) return values.access ?? null;
    if (key === KEY_REFRESH) return values.refresh ?? null;
    return null;
  });
}

describe("isExpired", () => {
  it("期限を過ぎたトークンは切れている", () => {
    expect(isExpired(DEAD)).toBe(true);
  });

  it("期限内のトークンは切れていない", () => {
    expect(isExpired(LIVE)).toBe(false);
  });

  // 読めない形を「切れている」と決めつけると、こちらの都合で利用者を
  // ログアウトさせてしまう。
  it("期限を読めないトークンは、切れているとは見なさない", () => {
    expect(isExpired("not-a-jwt")).toBe(false);
    expect(isExpired("header.eyJzdWIiOiIxIn0.sig")).toBe(false);
  });
});

describe("isLoggedIn", () => {
  beforeEach(() => {
    getItemMock.mockReset();
  });

  it("両方とも期限内ならログイン中", async () => {
    storage({ access: LIVE, refresh: LIVE });
    await expect(isLoggedIn()).resolves.toBe(true);
  });

  // ここが本題。アクセスが切れていても、リフレッシュが生きていれば
  // http.ts が取り直せるので、ログインは続いている。
  it("アクセスだけ切れていて、リフレッシュが生きていればログイン中", async () => {
    storage({ access: DEAD, refresh: LIVE });
    await expect(isLoggedIn()).resolves.toBe(true);
  });

  // 以前はここが true だった。これが「ログイン中なのに何も開けない」の正体。
  it("両方とも切れていればログインしていない", async () => {
    storage({ access: DEAD, refresh: DEAD });
    await expect(isLoggedIn()).resolves.toBe(false);
  });

  it("何も保存されていなければログインしていない", async () => {
    storage({});
    await expect(isLoggedIn()).resolves.toBe(false);
  });

  it("リフレッシュだけ残っていて期限内ならログイン中", async () => {
    storage({ access: null, refresh: LIVE });
    await expect(isLoggedIn()).resolves.toBe(true);
  });
});
