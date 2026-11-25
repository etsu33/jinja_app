// apps/web/src/lib/api/__tests__/auth.signup.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { signup, SignupRequestError } from "@/lib/api/auth";

const VALID_PAYLOAD = {
  username: "tarou",
  email: "tarou@example.com",
  password: "password123",
};

describe("signup()", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("成功時は BFF の JSON を返す", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: 1, username: "tarou" }), {
        status: 201,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(signup(VALID_PAYLOAD)).resolves.toEqual({ id: 1, username: "tarou" });

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/auth/register",
      expect.objectContaining({ method: "POST", body: JSON.stringify(VALID_PAYLOAD) }),
    );
  });

  it("validation error（400）は status と body を保持して投げる", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ email: ["この項目は必須です。"] }), {
        status: 400,
        headers: { "content-type": "application/json" },
      }),
    );

    const err = await signup(VALID_PAYLOAD).catch((e) => e);

    expect(err).toBeInstanceOf(SignupRequestError);
    expect(err.status).toBe(400);
    expect(err.data).toEqual({ email: ["この項目は必須です。"] });
  });

  it("server error（502）は status を保持して投げる", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "バックエンドに接続できません", code: "backend_unreachable" }), {
        status: 502,
        headers: { "content-type": "application/json" },
      }),
    );

    const err = await signup(VALID_PAYLOAD).catch((e) => e);

    expect(err).toBeInstanceOf(SignupRequestError);
    expect(err.status).toBe(502);
  });

  it("network failure（fetch 自体の失敗）は status=null で投げる", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));

    const err = await signup(VALID_PAYLOAD).catch((e) => e);

    expect(err).toBeInstanceOf(SignupRequestError);
    expect(err.status).toBeNull();
  });

  it("JSON で無い error body も文字列として保持する", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("<html>500</html>", { status: 500, headers: { "content-type": "text/html" } }),
    );

    const err = await signup(VALID_PAYLOAD).catch((e) => e);

    expect(err.status).toBe(500);
    expect(err.data).toBe("<html>500</html>");
  });
});
