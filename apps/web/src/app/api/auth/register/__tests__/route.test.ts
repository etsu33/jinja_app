// apps/web/src/app/api/auth/register/__tests__/route.test.ts
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { NextRequest } from "next/server";

import { POST } from "../route";

vi.mock("server-only", () => ({}));

const BACKEND_ORIGIN_ENV_NAMES = [
  "DJANGO_ORIGIN",
  "BACKEND_ORIGIN",
  "DJANGO_API_BASE_URL",
  "BACKEND_BASE_URL",
] as const;

const server = setupServer();

const OLD_ENV = process.env;

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

beforeEach(() => {
  process.env = { ...OLD_ENV };
  for (const name of BACKEND_ORIGIN_ENV_NAMES) delete process.env[name];
});

afterEach(() => {
  process.env = OLD_ENV;
  server.resetHandlers();
  vi.restoreAllMocks();
});

afterAll(() => server.close());

function makeReq(body: unknown) {
  return new NextRequest("http://localhost/api/auth/register", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

const VALID_PAYLOAD = {
  username: "tarou",
  email: "tarou@example.com",
  password: "password123",
};

describe("/api/auth/register BFF", () => {
  it("DJANGO_ORIGIN（他 BFF と同じ名称）から upstream を解決して透過する", async () => {
    const origin = "https://backend.example.com";
    process.env.DJANGO_ORIGIN = origin;

    let receivedBody: unknown = null;
    server.use(
      http.post(`${origin}/api/users/signup/`, async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ id: 1, username: "tarou" }, { status: 201 });
      }),
    );

    const res = await POST(makeReq(VALID_PAYLOAD));

    expect(res.status).toBe(201);
    expect(await res.json()).toEqual({ id: 1, username: "tarou" });
    expect(receivedBody).toEqual(VALID_PAYLOAD);
  });

  it.each(["BACKEND_ORIGIN", "DJANGO_API_BASE_URL", "BACKEND_BASE_URL"] as const)(
    "%s しか設定されていなくても upstream を解決できる",
    async (envName) => {
      const origin = "https://backend.example.com";
      process.env[envName] = `${origin}/`; // 末尾スラッシュも許容する

      server.use(
        http.post(`${origin}/api/users/signup/`, () =>
          HttpResponse.json({ id: 2, username: "tarou" }, { status: 201 }),
        ),
      );

      const res = await POST(makeReq(VALID_PAYLOAD));

      expect(res.status).toBe(201);
    },
  );

  it("Backend の validation error（400）は status と body をそのまま返す", async () => {
    const origin = "https://backend.example.com";
    process.env.DJANGO_ORIGIN = origin;

    server.use(
      http.post(`${origin}/api/users/signup/`, () =>
        HttpResponse.json({ email: ["この項目は必須です。"] }, { status: 400 }),
      ),
    );

    const res = await POST(makeReq({ username: "tarou", password: "password123" }));

    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ email: ["この項目は必須です。"] });
  });

  it("Backend へ到達できない場合は 502 + backend_unreachable を返す（validation error と混ざらない）", async () => {
    process.env.DJANGO_ORIGIN = "https://backend.example.com";

    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("ECONNREFUSED"));

    const res = await POST(makeReq(VALID_PAYLOAD));

    expect(res.status).toBe(502);
    expect(await res.json()).toEqual({
      detail: "バックエンドに接続できません",
      code: "backend_unreachable",
    });
  });
});
