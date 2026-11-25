// @vitest-environment node
/**
 * FU-2-P7 F1（Web JSON exposure）: the signed anonymous credential reaches the browser only as the HttpOnly
 * `concierge_anon_id` cookie, never in the chat JSON body, on every response path.
 * docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

const djFetchMock = vi.fn();

vi.mock("server-only", () => ({}));
vi.mock("@/lib/server/backend", () => ({
  djFetch: (...args: unknown[]) => djFetchMock(...args),
}));

import { POST } from "../route";

const CREDENTIAL = "signed-anon-credential-value";
const BACKEND_BODY = {
  ok: true,
  intent: "recommend",
  thread_id: "42",
  data: { recommendations: [{ name: "神社A" }], thread_id: "42" },
  plan: "anonymous",
  reply: "候補: 神社A",
  consultation_meaning: { needs: [] },
  remaining: 2,
  limit: 3,
  limitReached: false,
  thread: { id: 42 },
  _anon_cookie_value: CREDENTIAL,
};
const { _anon_cookie_value: _omit, ...EXPECTED_BODY } = BACKEND_BODY;

function json(body: unknown, status = 200, extraHeaders: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...extraHeaders },
  });
}

function req(cookie = "") {
  return new NextRequest("http://localhost/api/concierge/chat", {
    method: "POST",
    headers: { "content-type": "application/json", ...(cookie ? { cookie } : {}) },
    body: JSON.stringify({ query: "仕事運" }),
  });
}

function setCookies(res: Response): string[] {
  return (res.headers as Headers & { getSetCookie: () => string[] }).getSetCookie();
}

function anonCookies(res: Response): string[] {
  return setCookies(res).filter((c) => c.startsWith("concierge_anon_id="));
}

let logs: unknown[][];

beforeEach(() => {
  vi.clearAllMocks();
  logs = [];
  for (const level of ["log", "warn", "error", "info"] as const) {
    vi.spyOn(console, level).mockImplementation((...args: unknown[]) => {
      logs.push(args);
    });
  }
});

afterEach(() => {
  vi.restoreAllMocks();
});

function expectNoCredentialInBodyOrLogs(text: string) {
  expect(text).not.toContain(CREDENTIAL);
  expect(text).not.toContain("_anon_cookie_value");
  expect(JSON.stringify(logs)).not.toContain(CREDENTIAL);
}

async function expectStrippedWithCookie(res: Response, status = 200, body: unknown = EXPECTED_BODY) {
  const text = await res.text();
  expect(res.status).toBe(status);
  expect(JSON.parse(text)).toEqual(body);
  expectNoCredentialInBodyOrLogs(text);
  const anon = anonCookies(res);
  expect(anon).toHaveLength(1);
  expect(anon[0]).toContain(`concierge_anon_id=${CREDENTIAL}`);
  expect(anon[0]).toMatch(/HttpOnly/i);
  expect(anon[0]).toMatch(/SameSite=lax/i);
}

describe("browser-facing chat body carries no anonymous credential", () => {
  it("normal path: strips the field, keeps every other field and the status, sets the cookie", async () => {
    djFetchMock.mockResolvedValue(json(BACKEND_BODY));

    await expectStrippedWithCookie(await POST(req()));
  });

  it("normal path: keeps the field order of the remaining body", async () => {
    djFetchMock.mockResolvedValue(json(BACKEND_BODY));

    const text = await (await POST(req())).text();

    expect(Object.keys(JSON.parse(text))).toEqual(Object.keys(EXPECTED_BODY));
  });

  it("normal path: also strips it from a non-200 JSON body（e.g. limit reached）", async () => {
    djFetchMock.mockResolvedValue(json({ ...BACKEND_BODY, limitReached: true, remaining: 0 }, 429));

    await expectStrippedWithCookie(await POST(req()), 429, { ...EXPECTED_BODY, limitReached: true, remaining: 0 });
  });

  it("refresh-success path: strips the field and still sets auth + anonymous cookies", async () => {
    djFetchMock
      .mockResolvedValueOnce(json({ detail: "token expired" }, 401))
      .mockResolvedValueOnce(json({ access: "NEXT_ACCESS", refresh: "NEXT_REFRESH" }))
      .mockResolvedValueOnce(json(BACKEND_BODY));

    const res = await POST(req("access_token=OLD; refresh_token=OLD_REFRESH"));

    await expectStrippedWithCookie(res);
    const all = setCookies(res).join("\n");
    expect(all).toContain("access_token=NEXT_ACCESS");
    expect(all).toContain("refresh_token=NEXT_REFRESH");
  });

  it("refresh-fallback path: strips the field from the returned 401 body and keeps deleting access_token", async () => {
    djFetchMock
      .mockResolvedValueOnce(json({ detail: "token expired", _anon_cookie_value: CREDENTIAL }, 401))
      .mockResolvedValueOnce(json({ detail: "invalid" }, 401));

    const res = await POST(req("access_token=OLD; refresh_token=BAD"));

    await expectStrippedWithCookie(res, 401, { detail: "token expired" });
    expect(setCookies(res).join("\n")).toMatch(/access_token=;/);
  });

  it("refresh ok without access token falls back the same way", async () => {
    djFetchMock
      .mockResolvedValueOnce(json({ detail: "token expired", _anon_cookie_value: CREDENTIAL }, 401))
      .mockResolvedValueOnce(json({ refresh: "ONLY_REFRESH" }));

    await expectStrippedWithCookie(await POST(req("access_token=OLD; refresh_token=R")), 401, {
      detail: "token expired",
    });
  });

  it("does not duplicate the cookie when Django also sends Set-Cookie", async () => {
    djFetchMock.mockResolvedValue(
      json(BACKEND_BODY, 200, {
        "set-cookie": `concierge_anon_id=${CREDENTIAL}; HttpOnly; Max-Age=7776000; Path=/; SameSite=None; Secure`,
      }),
    );

    await expectStrippedWithCookie(await POST(req()));
  });

  it.each([
    ["null", null],
    ["an empty string", ""],
    ["a non-string", 123],
  ])("strips a field holding %s and sets no anonymous cookie", async (_label, value) => {
    djFetchMock.mockResolvedValue(json({ ok: true, _anon_cookie_value: value }));

    const res = await POST(req());
    const text = await res.text();

    expect(JSON.parse(text)).toEqual({ ok: true });
    expect(text).not.toContain("_anon_cookie_value");
    expect(anonCookies(res)).toHaveLength(0);
  });
});

describe("bodies without the field are passed through byte for byte", () => {
  it.each([
    ["an authenticated JSON body", JSON.stringify({ ok: true, plan: "free", thread: { id: 1 } }), "application/json", 200],
    ["a JSON array", JSON.stringify([{ _anon_cookie_value: "nested" }]), "application/json", 200],
    ["a nested field only", JSON.stringify({ data: { _anon_cookie_value: "nested" } }), "application/json", 200],
    ["a non-JSON body", "upstream error", "text/plain", 500],
    ["an empty body", "", "application/json", 502],
  ])("%s", async (_label, body, contentType, status) => {
    djFetchMock.mockResolvedValue(new Response(body, { status, headers: { "content-type": contentType } }));

    const res = await POST(req());

    expect(res.status).toBe(status);
    expect(res.headers.get("content-type")).toBe(contentType);
    await expect(res.text()).resolves.toBe(body);
    expect(anonCookies(res)).toHaveLength(0);
  });
});

describe("logging", () => {
  it("never logs the credential or the body, even when the body is not JSON", async () => {
    djFetchMock.mockResolvedValue(new Response(`not json ${CREDENTIAL}`, { status: 500 }));

    await POST(req());

    expect(JSON.stringify(logs)).not.toContain(CREDENTIAL);
  });
});
