import { describe, expect, it } from "vitest";

import {
  buildLoginHref,
  buildRegisterHref,
  sanitizeReturnTo,
} from "@/lib/nav/login";

describe("sanitizeReturnTo", () => {
  it("内部パスは通す", () => {
    expect(sanitizeReturnTo("/mypage")).toBe("/mypage");
  });

  it("/concierge は復帰先として通す", () => {
    expect(sanitizeReturnTo("/concierge")).toBe("/concierge");
  });

  it("/billing/upgrade は復帰先として通す", () => {
    expect(sanitizeReturnTo("/billing/upgrade")).toBe("/billing/upgrade");
  });

  it("/favorites は復帰先として通す", () => {
    expect(sanitizeReturnTo("/favorites")).toBe("/favorites");
  });

  it("/favorites のクエリ付きパスは復帰先として通す", () => {
    expect(sanitizeReturnTo("/favorites?source=detail")).toBe("/favorites?source=detail");
  });

  it("/goshuin/new のクエリ付きパスは復帰先として通す", () => {
    expect(sanitizeReturnTo("/goshuin/new?shrine=123")).toBe("/goshuin/new?shrine=123");
  });

  it("許可routeに似ただけのパスは拒否する", () => {
    expect(sanitizeReturnTo("/favorites-old")).toBeNull();
    expect(sanitizeReturnTo("/goshuin/new-old")).toBeNull();
  });

  it("クエリ付き内部パスは通す", () => {
    expect(sanitizeReturnTo("/shrines/1?ctx=concierge&tid=123")).toBe(
      "/shrines/1?ctx=concierge&tid=123",
    );
  });

  it("外部URLは拒否する", () => {
    expect(sanitizeReturnTo("https://evil.example.com/phish")).toBeNull();
  });

  it("// で始まるパスは拒否する", () => {
    expect(sanitizeReturnTo("//evil.example.com/phish")).toBeNull();
  });

  it("/auth/login は拒否する", () => {
    expect(sanitizeReturnTo("/auth/login?returnTo=%2Fshrines%2F1")).toBeNull();
  });

  it("/auth/register は拒否する", () => {
    expect(sanitizeReturnTo("/auth/register?returnTo=%2Fshrines%2F1")).toBeNull();
  });

  it("/login は拒否する", () => {
    expect(sanitizeReturnTo("/login?next=%2Fshrines%2F1")).toBeNull();
  });

  it("/signup は拒否する", () => {
    expect(sanitizeReturnTo("/signup?next=%2Fshrines%2F1")).toBeNull();
  });
});

describe("buildLoginHref", () => {
  it("safe な returnTo を付ける", () => {
    expect(buildLoginHref("/shrines/1?ctx=concierge")).toBe(
      "/auth/login?returnTo=%2Fshrines%2F1%3Fctx%3Dconcierge",
    );
  });

  it("/billing/upgrade を returnTo に付ける", () => {
    expect(buildLoginHref("/billing/upgrade")).toBe("/auth/login?returnTo=%2Fbilling%2Fupgrade");
  });

  it("/favorites を returnTo に付ける", () => {
    expect(buildLoginHref("/favorites")).toBe("/auth/login?returnTo=%2Ffavorites");
  });

  it("/goshuin/new のqueryを保持して returnTo に付ける", () => {
    expect(buildLoginHref("/goshuin/new?shrine=123")).toBe("/auth/login?returnTo=%2Fgoshuin%2Fnew%3Fshrine%3D123");
  });

  it("unsafe な returnTo のとき /auth/login に落とす", () => {
    expect(buildLoginHref("https://evil.example.com/phish")).toBe("/auth/login");
  });
});

describe("buildRegisterHref", () => {
  it("safe な returnTo を付ける", () => {
    expect(buildRegisterHref("/mypage?tab=favorites")).toBe(
      "/auth/register?returnTo=%2Fmypage%3Ftab%3Dfavorites",
    );
  });

  it("/concierge を returnTo に付ける", () => {
    expect(buildRegisterHref("/concierge")).toBe("/auth/register?returnTo=%2Fconcierge");
  });

  it("unsafe な returnTo のとき /auth/register に落とす", () => {
    expect(buildRegisterHref("https://evil.example.com/phish")).toBe("/auth/register");
  });
});
