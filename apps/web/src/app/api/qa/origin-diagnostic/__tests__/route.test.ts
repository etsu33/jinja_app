import { readFileSync } from "node:fs";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

const { djFetchMock, bffFetchWithAuthFromReqMock } = vi.hoisted(() => ({
  djFetchMock: vi.fn(),
  bffFetchWithAuthFromReqMock: vi.fn(),
}));

vi.mock("@/lib/server/backend", () => ({ djFetch: djFetchMock }));
vi.mock("@/lib/server/bffFetch", () => ({ bffFetchWithAuthFromReq: bffFetchWithAuthFromReqMock }));

import { DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT } from "../route";

const BRANCH_HOST = "jinja-app-web-git-qa-web-bff-pr-ejb0515-1459s-projects.vercel.app";
const DEPLOYMENT_HOST = "jinja-app-abc123xyz-ejb0515-1459s-projects.vercel.app";
const ALLOWED_BRANCH = "qa/web-bff-preview-origin-diagnostic";
const SENSITIVE = {
  cookie: "access_token=secret-access-value; concierge_anon_id=secret-anon-value",
  authorization: "Bearer secret-bearer-value",
  forwardedHost: "internal-forwarded.example",
};

function stubAuthorizedPreview(overrides: Record<string, string | undefined> = {}) {
  const env: Record<string, string | undefined> = {
    VERCEL: "1",
    VERCEL_ENV: "preview",
    VERCEL_GIT_COMMIT_REF: ALLOWED_BRANCH,
    VERCEL_URL: DEPLOYMENT_HOST,
    VERCEL_BRANCH_URL: BRANCH_HOST,
    ...overrides,
  };
  for (const [key, value] of Object.entries(env)) vi.stubEnv(key, value as string);
}

function makeRequest(
  url: string,
  { method = "GET", headers = {} }: { method?: string; headers?: Record<string, string> } = {},
) {
  return new NextRequest(url, { method, headers: new Headers(headers) });
}

function previewGet(host: string, extra: Record<string, string> = {}, url = `https://${host}/api/qa/origin-diagnostic`) {
  return makeRequest(url, {
    headers: {
      host,
      "sec-fetch-site": "same-origin",
      cookie: SENSITIVE.cookie,
      authorization: SENSITIVE.authorization,
      "x-forwarded-host": SENSITIVE.forwardedHost,
      ...extra,
    },
  });
}

async function readJson(res: Response) {
  return JSON.parse(await res.text()) as Record<string, unknown>;
}

function expectSafeHeaders(res: Response) {
  expect(res.headers.get("cache-control")).toBe("no-store");
  expect(res.headers.get("set-cookie")).toBeNull();
}

const fetchSpy = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.unstubAllEnvs();
  // 既存の Vercel system env を消し、各テストで明示する。
  for (const key of ["VERCEL", "VERCEL_ENV", "VERCEL_GIT_COMMIT_REF", "VERCEL_URL", "VERCEL_BRANCH_URL"]) {
    vi.stubEnv(key, undefined as unknown as string);
  }
  vi.stubGlobal("fetch", fetchSpy);
});

afterEach(() => {
  // backend にも外部にも出ていないこと（全テスト共通）。
  expect(fetchSpy).not.toHaveBeenCalled();
  expect(djFetchMock).not.toHaveBeenCalled();
  expect(bffFetchWithAuthFromReqMock).not.toHaveBeenCalled();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("GET /api/qa/origin-diagnostic — authorized Preview", () => {
  it("branch URL: nextUrl.origin が基準と一致すれば match", async () => {
    stubAuthorizedPreview();

    const res = await GET(previewGet(BRANCH_HOST));
    const body = await readJson(res);

    expect(res.status).toBe(200);
    expectSafeHeaders(res);
    expect(body).toEqual({
      diagnostic: "web-bff-origin",
      version: 1,
      environment: "vercel-preview",
      result: "match",
      reason: null,
      referenceKind: "branch_url",
      nextUrlOriginKind: "branch_url",
      secFetchSite: "same-origin",
      secFetchSiteIsSameOrigin: true,
      originHeader: "absent",
    });
  });

  it("deployment URL でも基準を選べる（Host は大文字小文字を区別しない）", async () => {
    stubAuthorizedPreview();

    const res = await GET(previewGet(DEPLOYMENT_HOST.toUpperCase(), {}, `https://${DEPLOYMENT_HOST}/api/qa/origin-diagnostic`));
    const body = await readJson(res);

    expect(body.result).toBe("match");
    expect(body.referenceKind).toBe("deployment_url");
  });

  it("nextUrl が bind address（localhost）なら mismatch", async () => {
    stubAuthorizedPreview();

    const res = await GET(previewGet(BRANCH_HOST, {}, "http://localhost:3000/api/qa/origin-diagnostic"));
    const body = await readJson(res);

    expect(body.result).toBe("mismatch");
    expect(body.nextUrlOriginKind).toBe("loopback_or_bind_address");
  });

  it("nextUrl が placeholder（http://n）なら mismatch", async () => {
    stubAuthorizedPreview();

    const res = await GET(previewGet(BRANCH_HOST, {}, "http://n/api/qa/origin-diagnostic"));
    const body = await readJson(res);

    expect(body.result).toBe("mismatch");
    expect(body.nextUrlOriginKind).toBe("placeholder");
  });

  it("host は同じで scheme が違えば mismatch（区別して報告）", async () => {
    stubAuthorizedPreview();

    const res = await GET(previewGet(BRANCH_HOST, {}, `http://${BRANCH_HOST}/api/qa/origin-diagnostic`));
    const body = await readJson(res);

    expect(body.result).toBe("mismatch");
    expect(body.nextUrlOriginKind).toBe("platform_host_scheme_or_port_differs");
  });

  it("Sec-Fetch-Site と Origin header を分類だけして返す", async () => {
    stubAuthorizedPreview();

    const cases: Array<[Record<string, string>, unknown, unknown]> = [
      [{ "sec-fetch-site": "cross-site", origin: "https://evil.example" }, "cross-site", "differs_from_reference"],
      [{ "sec-fetch-site": "none" }, "none", "absent"],
      [{ "sec-fetch-site": "weird" }, "other", "absent"],
      [{ origin: `https://${BRANCH_HOST}` }, "same-origin", "matches_reference"],
      [{ origin: "null" }, "same-origin", "null"],
      [{ origin: "not a url" }, "same-origin", "malformed"],
    ];
    for (const [headers, expectedSfs, expectedOrigin] of cases) {
      const body = await readJson(await GET(previewGet(BRANCH_HOST, headers)));
      expect(body.secFetchSite).toBe(expectedSfs);
      expect(body.originHeader).toBe(expectedOrigin);
    }

    const absent = makeRequest(`https://${BRANCH_HOST}/api/qa/origin-diagnostic`, { headers: { host: BRANCH_HOST } });
    const absentBody = await readJson(await GET(absent));
    expect(absentBody.secFetchSite).toBe("absent");
    expect(absentBody.secFetchSiteIsSameOrigin).toBe(false);
  });
});

describe("GET — inconclusive when the reference cannot be trusted", () => {
  it("Host header が無い → inconclusive", async () => {
    stubAuthorizedPreview();

    const req = makeRequest(`https://${BRANCH_HOST}/api/qa/origin-diagnostic`);
    const body = await readJson(await GET(req));

    expect(body.result).toBe("inconclusive");
    expect(body.reason).toBe("request_host_not_a_platform_url");
    expect(body.referenceKind).toBeNull();
  });

  it("Host が platform URL でない（偽装）→ X-Forwarded-Host が platform URL でも inconclusive", async () => {
    stubAuthorizedPreview();

    const req = previewGet("evil.example", { "x-forwarded-host": BRANCH_HOST }, `https://${BRANCH_HOST}/api/qa/origin-diagnostic`);
    const body = await readJson(await GET(req));

    expect(body.result).toBe("inconclusive");
    expect(body.reason).toBe("request_host_not_a_platform_url");
  });

  it("VERCEL_URL / VERCEL_BRANCH_URL が無い → inconclusive", async () => {
    stubAuthorizedPreview({ VERCEL_URL: undefined, VERCEL_BRANCH_URL: undefined });

    const body = await readJson(await GET(previewGet(BRANCH_HOST)));

    expect(body.result).toBe("inconclusive");
    expect(body.reason).toBe("platform_reference_unavailable");
  });

  it("VERCEL_URL が不正な形式（scheme 付き・path 付き）なら基準に使わない", async () => {
    stubAuthorizedPreview({
      VERCEL_URL: `https://${DEPLOYMENT_HOST}`,
      VERCEL_BRANCH_URL: `${BRANCH_HOST}/path`,
    });

    const body = await readJson(await GET(previewGet(BRANCH_HOST)));

    expect(body.result).toBe("inconclusive");
    expect(body.reason).toBe("platform_reference_unavailable");
  });
});

describe("GET — rejected outside the authorized Preview", () => {
  const rejectedEnvs: Array<[string, Record<string, string | undefined>]> = [
    ["Production", { VERCEL_ENV: "production" }],
    ["Vercel development", { VERCEL_ENV: "development" }],
    ["Preview of another branch", { VERCEL_GIT_COMMIT_REF: "feature/other" }],
    ["Preview of the production branch", { VERCEL_GIT_COMMIT_REF: "develop" }],
    ["not on Vercel（VERCEL unset）", { VERCEL: undefined }],
    ["VERCEL_ENV unset", { VERCEL_ENV: undefined }],
  ];

  for (const [label, overrides] of rejectedEnvs) {
    it(`${label} → 404, 診断結果なし`, async () => {
      stubAuthorizedPreview(overrides);

      const res = await GET(previewGet(BRANCH_HOST));

      expect(res.status).toBe(404);
      expectSafeHeaders(res);
      expect(await readJson(res)).toEqual({ detail: "not found" });
    });
  }

  it("NODE_ENV=development だけでは許可しない", async () => {
    vi.stubEnv("NODE_ENV", "development");

    const res = await GET(previewGet(BRANCH_HOST));

    expect(res.status).toBe(404);
    expect(await readJson(res)).toEqual({ detail: "not found" });
  });

  it("NODE_ENV=production だけ（Vercel 外）でも 404", async () => {
    vi.stubEnv("NODE_ENV", "production");

    const res = await GET(previewGet(BRANCH_HOST));

    expect(res.status).toBe(404);
  });
});

describe("non-GET methods", () => {
  const handlers = { HEAD, POST, PUT, PATCH, DELETE, OPTIONS };

  for (const [name, handler] of Object.entries(handlers)) {
    it(`${name}: 許可 Preview では 405（Allow: GET）`, async () => {
      stubAuthorizedPreview();

      const res = await handler();

      expect(res.status).toBe(405);
      expect(res.headers.get("allow")).toBe("GET");
      expectSafeHeaders(res);
    });

    it(`${name}: Production では 404（存在を示さない）`, async () => {
      stubAuthorizedPreview({ VERCEL_ENV: "production" });

      const res = await handler();

      expect(res.status).toBe(404);
      expect(res.headers.get("allow")).toBeNull();
      expectSafeHeaders(res);
    });
  }
});

describe("no sensitive information", () => {
  it("response は固定キーだけで、header 値・env 値・cookie・token を含まない", async () => {
    stubAuthorizedPreview();

    const res = await GET(
      previewGet(BRANCH_HOST, { origin: "https://evil.example", "x-forwarded-proto": "https", "x-real-ip": "203.0.113.9" }),
    );
    const text = await res.text();
    const body = JSON.parse(text) as Record<string, unknown>;

    expect(Object.keys(body).sort()).toEqual(
      [
        "diagnostic",
        "environment",
        "nextUrlOriginKind",
        "originHeader",
        "reason",
        "referenceKind",
        "result",
        "secFetchSite",
        "secFetchSiteIsSameOrigin",
        "version",
      ].sort(),
    );
    for (const secret of [
      BRANCH_HOST,
      DEPLOYMENT_HOST,
      ALLOWED_BRANCH,
      "secret-access-value",
      "secret-anon-value",
      "secret-bearer-value",
      SENSITIVE.forwardedHost,
      "evil.example",
      "203.0.113.9",
    ]) {
      expect(text).not.toContain(secret);
    }
  });

  it("console に何も書かない", async () => {
    stubAuthorizedPreview();
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((m) => vi.spyOn(console, m));

    await GET(previewGet(BRANCH_HOST));
    stubAuthorizedPreview({ VERCEL_ENV: "production" });
    await GET(previewGet(BRANCH_HOST));

    for (const spy of spies) expect(spy).not.toHaveBeenCalled();
    for (const spy of spies) spy.mockRestore();
  });
});

describe("no backend, database or cookie dependencies", () => {
  it("route module は next/server の型以外を import しない", () => {
    const source = readFileSync(path.join(__dirname, "..", "route.ts"), "utf8");
    const imports = [...source.matchAll(/^\s*import\s[^;]*?from\s+["']([^"']+)["']/gm)].map((m) => m[1]);

    expect(imports).toEqual(["next/server"]);
    expect(source).toMatch(/^import type \{ NextRequest \} from "next\/server";$/m);
    const code = source.replace(/^\s*\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "");
    expect(code).not.toMatch(/cookies\(|\.cookies\b|set-cookie|djFetch|bffFetch|\bfetch\(|console\./i);
  });
});
