// @vitest-environment node
// apps/web/scripts/audit/__tests__/bff-backend-call-graph.test.ts
//
// WS-04 BFF Backend call-graph audit script の regression test。
// fixture はメモリ上の file map（disk に置かない）で、alias / wrapper / SSR / direct fetch / dynamic URL を再現する。
import path from "node:path";
import { fileURLToPath } from "node:url";
import { beforeAll, describe, expect, it } from "vitest";
import {
  analyzeProgram,
  createProgramFromFiles,
  reconcile,
  renderMarkdown,
  runAudit,
  toJson,
} from "../bff-backend-call-graph.mjs";

const ENV_D_TS = `declare const process: { env: Record<string, string | undefined> };\n`;

const AXIOS_D_TS = `
export interface AxiosResponse<T = any> { data: T }
export interface AxiosInstance {
  get<T = any>(url: string, config?: any): Promise<AxiosResponse<T>>;
  post<T = any>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>>;
}
export interface AxiosStatic extends AxiosInstance {
  create(config?: any): AxiosInstance;
  isAxiosError(e: unknown): boolean;
}
declare const axios: AxiosStatic;
export default axios;
`;

const FIXTURE: Record<string, string> = {
  "node_modules/axios/package.json": `{"name":"axios","types":"index.d.ts"}`,
  "node_modules/axios/index.d.ts": AXIOS_D_TS,
  "src/env.d.ts": ENV_D_TS,
  "src/lib/server/clientIdentity.ts": `
export function clientIdentityHeaders(
  req: { headers: { get(name: string): string | null } } | null | undefined,
  method: string,
  upstream: string,
): Record<string, string> {
  return req && method && upstream ? {} : {};
}
`,
  "src/lib/server/backend.ts": `
import { clientIdentityHeaders } from "./clientIdentity";

export function getDjangoOrigin() {
  return (process.env.DJANGO_ORIGIN || "http://127.0.0.1:8000").replace(/\\/$/, "");
}

type Init = RequestInit & { forwardAuth?: boolean; clientIdentityFrom?: Request };

export async function djFetch(reqOrPath: Request | string, pathOrInit?: string | Init, maybeInit?: Init) {
  let req: Request | null = null;
  let path: string;
  let init: Init;
  if (typeof reqOrPath === "string") {
    path = reqOrPath;
    init = (pathOrInit as Init) ?? {};
  } else {
    req = reqOrPath;
    path = pathOrInit as string;
    init = maybeInit ?? {};
  }
  const headers = new Headers(init.headers ?? {});
  if (req && (init.forwardAuth ?? true)) {
    const auth = req.headers.get("authorization");
    if (auth) headers.set("Authorization", auth);
  }
  const { forwardAuth: _forwardAuth, clientIdentityFrom, ...rest } = init;
  for (const [k, v] of Object.entries(clientIdentityHeaders(req ?? clientIdentityFrom, "GET", path))) headers.set(k, v);
  const url = new URL(path, getDjangoOrigin()).toString();
  return fetch(url, { ...rest, headers });
}
`,
  "src/lib/server/index.ts": `export { djFetch as backendFetch } from "./backend";\n`,
  "src/lib/server/unsigned.ts": `
import { getDjangoOrigin } from "./backend";
export function plainBackend(path: string) {
  return fetch(\`\${getDjangoOrigin()}\${path}\`);
}
`,
  "src/lib/server/signedGet.ts": `
import { djFetch } from "./backend";
export function signedGet(req: Request, path: string) {
  return djFetch(req, path, { method: "GET" });
}
`,
  "src/lib/server/base.ts": `
export function resolveServerBaseUrl() {
  return process.env.WEB_BASE_URL || "http://localhost:3000";
}
`,
  "src/app/api/signed/route.ts": `
import { getDjangoOrigin } from "@/lib/server/backend";
import { clientIdentityHeaders } from "@/lib/server/clientIdentity";
export async function POST(req: Request) {
  return fetch(\`\${getDjangoOrigin()}/api/x/\`, { method: "POST", headers: { ...clientIdentityHeaders(req, "POST", "/api/x/") } });
}
`,
  "src/app/api/alias/route.ts": `
export async function GET() {
  const f = fetch;
  return f(\`\${process.env.BACKEND_URL}/api/y/\`);
}
`,
  "src/app/api/global/route.ts": `
import { getDjangoOrigin } from "@/lib/server/backend";
export async function GET() {
  const bound = fetch.bind(globalThis);
  await bound(\`\${getDjangoOrigin()}/api/bound/\`);
  return globalThis.fetch(\`\${getDjangoOrigin()}/api/z/\`);
}
`,
  "src/app/api/reexport/route.ts": `
import { backendFetch } from "@/lib/server";
export async function GET(req: Request) {
  return backendFetch(req, "/api/re/");
}
`,
  "src/app/api/pathform/route.ts": `
import { backendFetch } from "@/lib/server";
export async function GET(req: Request) {
  await backendFetch("/api/p1/");
  await backendFetch("/api/p2/", { forwardAuth: false });
  return backendFetch("/api/p3/", { clientIdentityFrom: req });
}
`,
  "src/app/api/layered/route.ts": `
import { signedGet } from "@/lib/server/signedGet";
import { plainBackend } from "@/lib/server/unsigned";
export async function GET(req: Request) {
  await plainBackend("/api/plain/");
  return signedGet(req, "/api/layered/");
}
`,
  "src/app/api/internal-target/route.ts": `
import { djFetch } from "@/lib/server/backend";
export async function GET(req: Request) {
  return djFetch(req, "/api/target/", { forwardAuth: false });
}
`,
  "src/app/api/axios-direct/route.ts": `
import axios from "axios";
export async function GET() {
  return axios.get(\`\${process.env.BACKEND_URL}/api/direct-axios/\`);
}
`,
  "src/lib/client.ts": `
import axios from "axios";
const api = axios.create({ baseURL: "/api" });
export function getThings() {
  return api.get("things/");
}
`,
  "src/lib/dyn.ts": `
export function callWith(fetcher: (u: string) => Promise<Response>) {
  return fetcher("/api/dyn/");
}
export function anyUrl(u: string) {
  return fetch(u);
}
const clients: Record<string, (u: string) => Promise<Response>> = {};
export function byName(name: string) {
  return clients[name]("/api/by-name/");
}
export const holder = { f: fetch };
`,
  "src/components/Widget.tsx": `"use client";
import { getThings } from "@/lib/client";
import { anyUrl } from "@/lib/dyn";
export function Widget() {
  // fetch("/api/commented-out/") は text 検索にだけ現れる
  const label = "fetch(";
  void fetch("/api/signed/", { method: "POST" });
  void getThings();
  void anyUrl(String(Math.random()));
  return label;
}
`,
  "src/app/page.tsx": `
import { resolveServerBaseUrl } from "@/lib/server/base";
import { callWith, byName } from "@/lib/dyn";
import { Widget } from "@/components/Widget";
export default async function Page() {
  const base = resolveServerBaseUrl();
  await fetch(\`\${base}/api/internal-target/\`, { cache: "no-store" });
  await fetch(\`\${process.env.DJANGO_API_BASE_URL}/api/direct/\`);
  await callWith((u) => fetch(u));
  await byName("x");
  return Widget;
}
`,
  "src/lib/__tests__/ignored.test.ts": `
import { plainBackend } from "@/lib/server/unsigned";
export const t = () => plainBackend("/api/from-test/");
`,
};

type Row = {
  id: string;
  file: string;
  line: number;
  scope: string;
  kind: string;
  via: string;
  wrapper: string | null;
  method: string;
  destination: { category: string; staticPath: string; envNames: string[] };
  runtimeContext: string;
  provenance: string;
  identity: string;
  hmac: string;
  authentication: string;
  downstreamRoute: string | null;
  evidence: string[];
};

let result: any;
let rows: Row[];

/** fixture 内で `needle` を含む行番号（1 始まり）。 */
function lineOf(file: string, needle: string): number {
  const index = FIXTURE[file].split("\n").findIndex((l) => l.includes(needle));
  expect(index, `${needle} in ${file}`).toBeGreaterThanOrEqual(0);
  return index + 1;
}
const DJFETCH_SINK = () => `src/lib/server/backend.ts:${lineOf("src/lib/server/backend.ts", "return fetch(url")}`;

function row(file: string, predicate: (r: Row) => boolean = () => true): Row {
  const found = rows.filter((r) => r.file === file && predicate(r));
  expect(found, `row in ${file}`).toHaveLength(1);
  return found[0];
}

beforeAll(() => {
  const { program, srcDir } = createProgramFromFiles(FIXTURE);
  result = analyzeProgram(program, { srcDir });
  rows = result.rows;
});

describe("aliases and global references", () => {
  it("resolves a const alias of fetch and classifies the env-based Backend URL as unsigned", () => {
    const r = row("src/app/api/alias/route.ts");
    expect(r.kind).toBe("direct-sink");
    expect(r.via).toContain("alias of fetch via 'f'");
    expect(r.destination.category).toBe("backend");
    expect(r.destination.envNames).toEqual(["BACKEND_URL"]);
    expect(r.hmac).toBe("unsigned");
    expect(r.identity).toBe("absent");
  });

  it("resolves globalThis.fetch and fetch.bind(globalThis)", () => {
    const z = row("src/app/api/global/route.ts", (r) => r.destination.staticPath === "/api/z/");
    const bound = row("src/app/api/global/route.ts", (r) => r.destination.staticPath === "/api/bound/");
    for (const r of [z, bound]) {
      expect(r.destination.category).toBe("backend");
      expect(r.hmac).toBe("unsigned");
    }
  });

  it("follows a re-exported wrapper to its declaration", () => {
    const r = row("src/app/api/reexport/route.ts");
    expect(r.wrapper).toBe("djFetch");
    expect(r.evidence.join(" ")).toMatch(/re-export hop/);
    expect(r.hmac).toBe("conditionally signed");
    expect(r.identity).toBe("direct");
  });
});

describe("wrappers", () => {
  it("models djFetch: URL params, identity sources, auth gate and final sink", () => {
    const w = result.wrappers.find((x: any) => x.name === "djFetch");
    expect(w.known).toBe(true);
    expect(w.urlParamIndices).toEqual([0, 1]);
    expect(w.base).toBe("backend");
    expect(w.signingHelperOnPath).toBe(true);
    expect(w.identitySources).toEqual(
      expect.arrayContaining(["param#0(reqOrPath)", "param#1.clientIdentityFrom", "param#2.clientIdentityFrom"]),
    );
    expect(w.authGates).toEqual(["forwardAuth"]);
    expect(w.finalSinks).toEqual([DJFETCH_SINK()]);
  });

  it("treats the presence of the helper as conditional: path form without a request is unsigned", () => {
    const p1 = row("src/app/api/pathform/route.ts", (r) => r.destination.staticPath === "/api/p1/");
    const p2 = row("src/app/api/pathform/route.ts", (r) => r.destination.staticPath === "/api/p2/");
    const p3 = row("src/app/api/pathform/route.ts", (r) => r.destination.staticPath === "/api/p3/");
    expect(p1.hmac).toBe("unsigned");
    expect(p2.hmac).toBe("unsigned");
    expect(p3.hmac).toBe("conditionally signed");
    expect(p3.identity).toBe("direct");
    expect(p1.authentication).toMatch(/^none forwarded/);
  });

  it("reports forwardAuth: false as an anonymous Backend call", () => {
    const r = row("src/app/api/internal-target/route.ts");
    expect(r.authentication).toMatch(/^anonymous/);
    expect(r.hmac).toBe("conditionally signed");
  });

  it("detects a wrapper of a wrapper and maps its request parameter", () => {
    const w = result.wrappers.find((x: any) => x.name === "signedGet");
    expect(w.identitySources).toEqual(["param#0(req)"]);
    expect(w.finalSinks).toEqual([DJFETCH_SINK()]);
    const r = row("src/app/api/layered/route.ts", (x) => x.wrapper === "signedGet");
    expect(r.destination.category).toBe("backend");
    expect(r.destination.staticPath).toBe("/api/layered/");
    expect(r.hmac).toBe("conditionally signed");
  });

  it("classifies a wrapper without the helper as unsigned at every call site", () => {
    const w = result.wrappers.find((x: any) => x.name === "plainBackend");
    expect(w.signingHelperOnPath).toBe(false);
    const r = row("src/app/api/layered/route.ts", (x) => x.wrapper === "plainBackend");
    expect(r.hmac).toBe("unsigned");
    expect(r.identity).toBe("absent");
  });

  it("keeps the wrapper's final sink as a wrapper-internal row", () => {
    const r = row("src/lib/server/backend.ts");
    expect(r.kind).toBe("wrapper-internal");
    expect(r.destination.category).toBe("parameter");
  });
});

describe("direct and SSR fetches", () => {
  it("classifies a direct Route Handler fetch with the helper in the init as conditionally signed", () => {
    const r = row("src/app/api/signed/route.ts");
    expect(r.method).toBe("POST");
    expect(r.runtimeContext).toBe("route-handler");
    expect(r.hmac).toBe("conditionally signed");
    expect(r.identity).toBe("direct");
    expect(r.evidence.join(" ")).toMatch(/incoming Route Handler request 'req' of POST/);
  });

  it("marks an SSR fetch to the app's own BFF as an internal hop without client identity", () => {
    const r = row("src/app/page.tsx", (x) => x.destination.staticPath === "/api/internal-target/");
    expect(r.runtimeContext).toBe("ssr");
    expect(r.destination.category).toBe("internal-bff");
    expect(r.identity).toBe("absent");
    expect(r.downstreamRoute).toBe("/api/internal-target");
    const target = result.routes.find((x: any) => x.path === "/api/internal-target");
    expect(target.internalServerCallers).toEqual([`${r.file}:${r.line}`]);
    expect(row("src/app/api/internal-target/route.ts").provenance).toMatch(/^original or internal/);
  });

  it("classifies a direct SSR Backend fetch without the helper as unsigned", () => {
    const r = row("src/app/page.tsx", (x) => x.destination.staticPath === "/api/direct/");
    expect(r.destination.category).toBe("backend");
    expect(r.hmac).toBe("unsigned");
  });

  it("classifies a client component fetch as browser → BFF", () => {
    const r = row("src/components/Widget.tsx", (x) => x.via === "fetch");
    expect(r.runtimeContext).toBe("client");
    expect(r.destination.category).toBe("relative");
    expect(r.hmac).toBe("not applicable (non-Backend hop)");
    expect(r.downstreamRoute).toBe("/api/signed");
  });

  it("resolves axios instances with a relative baseURL and direct axios Backend calls", () => {
    const things = row("src/lib/client.ts");
    expect(things.via).toBe("axios.get");
    expect(things.destination.staticPath).toBe("/api/things/");
    expect(things.runtimeContext).toBe("client");
    const direct = row("src/app/api/axios-direct/route.ts");
    expect(direct.destination.category).toBe("backend");
    expect(direct.hmac).toBe("unsigned");
  });

  it("keeps test files out of the production inventory", () => {
    const r = row("src/lib/__tests__/ignored.test.ts");
    expect(r.scope).toBe("test");
  });
});

describe("dynamic calls are reported, not assumed safe", () => {
  it("lists callee parameters, index-signature calls, escaped fetch references and parameter URLs", () => {
    const prod = result.unresolved.filter((u: any) => u.scope === "production");
    const reasons = prod.map((u: any) => `${u.file}:${u.callee}:${u.reason}`).join("\n");
    expect(reasons).toMatch(/src\/lib\/dyn\.ts:fetcher:callee 'fetcher' is a Parameter/);
    expect(reasons).toMatch(/src\/lib\/dyn\.ts:clients\[name\]/);
    expect(reasons).toMatch(/global fetch referenced as a value/);
    expect(reasons).toMatch(/src\/components\/Widget\.tsx:anyUrl/);
    const anyUrlRow = row("src/components/Widget.tsx", (x) => x.wrapper === "anyUrl");
    expect(anyUrlRow.hmac).toBe("unresolved");
  });
});

describe("reconciliation and output", () => {
  it("reconciles text hits against the AST, including comments and string literals", () => {
    const rec = reconcile(result);
    expect(rec.status).toBe("RECONCILED");
    const fetchPattern = rec.patterns.find((p: any) => p.pattern === "fetch");
    expect(fetchPattern.byClass.comment).toBe(1);
    expect(fetchPattern.byClass["string/regex literal"]).toBe(1);
    // const alias（f(...)）と bind（bound(...)）は text の fetch( に現れない
    expect(rec.astOnlyRequestSites.join("\n")).toMatch(/alias\/route\.ts/);
    expect(rec.orphanSigningCalls).toEqual([]);
  });

  it("fails reconciliation when a text hit cannot be explained", () => {
    const fake = { ...result, sources: new Map(result.sources), callAnchors: new Map() };
    const rec = reconcile(fake);
    expect(rec.status).toBe("NOT RECONCILED");
    expect(rec.unexplainedTotal).toBeGreaterThan(0);
  });

  it("never emits environment values, only names", () => {
    const secret = "fixture-secret-value-that-must-not-appear-0123456789";
    const previous = process.env.KM_CLIENT_IDENTITY_SECRET;
    process.env.KM_CLIENT_IDENTITY_SECRET = secret;
    process.env.DJANGO_ORIGIN = "https://backend.example.invalid";
    try {
      const { program, srcDir } = createProgramFromFiles(FIXTURE);
      const r = analyzeProgram(program, { srcDir });
      const out = JSON.stringify(toJson(r, reconcile(r))) + renderMarkdown(r, reconcile(r));
      expect(out).not.toContain(secret);
      expect(out).not.toContain("backend.example.invalid");
      expect(out).toContain("DJANGO_ORIGIN");
    } finally {
      if (previous === undefined) delete process.env.KM_CLIENT_IDENTITY_SECRET;
      else process.env.KM_CLIENT_IDENTITY_SECRET = previous;
      delete process.env.DJANGO_ORIGIN;
    }
  });
});

describe("repository smoke test", () => {
  it("analyzes apps/web/src, reconciles every text hit and traces the known wrappers to their sinks", () => {
    const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
    const { result: real, reconciliation } = runAudit(webRoot);
    expect(reconciliation.status).toBe("RECONCILED");
    for (const name of ["djFetch", "bffFetchWithAuthFromReq", "bffPostJsonWithAuthFromReq"]) {
      const w = real.wrappers.find((x: any) => x.name === name);
      expect(w, name).toBeDefined();
      expect(w.signingHelperOnPath).toBe(true);
      expect(w.finalSinks.length).toBeGreaterThan(0);
    }
  }, 180_000);
});
