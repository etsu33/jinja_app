import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { NextRequest } from "next/server";

import { POST } from "../route";

vi.mock("server-only", () => ({}));

const DJANGO_ORIGIN = "http://127.0.0.1:8000";
const UPSTREAM_CHECKOUT = `${DJANGO_ORIGIN}/api/billings/checkout/`;

const server = setupServer();

beforeAll(() => {
  process.env.DJANGO_ORIGIN = DJANGO_ORIGIN;
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  delete process.env.DJANGO_ORIGIN;
  server.close();
});

function makeReq(body: unknown = { pass_type: "7d" }) {
  return new NextRequest("http://localhost:3000/api/billings/checkout", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: body === null ? undefined : JSON.stringify(body),
  });
}

describe("/api/billings/checkout BFF", () => {
  it("backendへパスの種類とsuccess/cancel URLを渡してcheckout sessionを返す", async () => {
    server.use(
      http.post(UPSTREAM_CHECKOUT, async ({ request }) => {
        const body = (await request.json()) as Record<string, string>;
        expect(body).toEqual({
          pass_type: "7d",
          success_url: "http://localhost:3000/billing/success",
          cancel_url: "http://localhost:3000/billing/cancel",
        });
        return HttpResponse.json({
          session_id: "cs_test_123",
          checkout_url: "https://checkout.stripe.com/c/pay/cs_test_123",
        });
      }),
    );

    const res = await POST(makeReq());

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({
      session_id: "cs_test_123",
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_123",
    });
  });

  it("backendの未認証レスポンスをそのまま返す", async () => {
    server.use(
      http.post(UPSTREAM_CHECKOUT, async () => {
        return HttpResponse.json({ detail: "Authentication credentials were not provided." }, { status: 401 });
      }),
    );

    const res = await POST(makeReq());

    expect(res.status).toBe(401);
    expect(await res.json()).toHaveProperty("detail");
  });

  it.each([
    ["パスの種類が無い", {}],
    ["知らないパスの種類", { pass_type: "30d" }],
    ["本文が無い", null],
  ])("%s ときは backend を呼ばずに 400 を返す", async (_label, body) => {
    // backend を呼ぶと onUnhandledRequest: "error" で失敗する
    const res = await POST(makeReq(body));

    expect(res.status).toBe(400);
  });
});
