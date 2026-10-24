// apps/web/src/app/api/qa/origin-diagnostic/route.ts
//
// S-13: Preview 専用の一時的な origin 診断（読み取りのみ）。
// docs/audit/web-bff-csrf-hardening-contract-2026-10-23.md §4.4 /
// docs/audit/web-bff-origin-preview-verification-2026-10-23.md §10。
//
// 目的は「Vercel Preview の route handler で req.nextUrl.origin が、ブラウザが
// 開いた origin と一致するか」を、生の header や設定値を返さずに確かめること。
//
// 契約:
// - 許可された Vercel Preview（VERCEL=1, VERCEL_ENV=preview, 許可ブランチ）だけで
//   診断結果を返す。それ以外（Production / Development / ローカル）は 404。
//   NODE_ENV では判定しない。
// - 比較の基準は Vercel が設定する VERCEL_URL / VERCEL_BRANCH_URL（request から
//   制御できない値）だけ。Host header は「どちらの基準か」を選ぶためにだけ使い、
//   基準そのものにはしない。基準を決められなければ inconclusive を返す。
// - 生の Host / X-Forwarded-* / Cookie / Authorization / origin 値は返さず、
//   ログにも書かない。backend も DB も呼ばない。Set-Cookie も出さない。
// - GET だけ。Cache-Control: no-store。
//
// 検証が終わったら、このディレクトリと __tests__ を削除する（PR 本文の削除手順）。
import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// 診断を返してよい Preview のブランチ。develop（Production branch）や他の
// feature branch の Preview では返さない。
const ALLOWED_PREVIEW_BRANCHES: ReadonlySet<string> = new Set([
  "qa/web-bff-preview-origin-diagnostic",
]);

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
  "Content-Type": "application/json",
} as const;

type ReferenceKind = "deployment_url" | "branch_url";
type OriginKind =
  | ReferenceKind
  | "platform_host_scheme_or_port_differs"
  | "placeholder"
  | "loopback_or_bind_address"
  | "other"
  | "unparseable";
type SecFetchSiteKind = "same-origin" | "same-site" | "cross-site" | "none" | "absent" | "other";
type OriginHeaderKind = "absent" | "matches_reference" | "differs_from_reference" | "null" | "malformed";

function json(body: unknown, status: number, extraHeaders?: Record<string, string>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...NO_STORE_HEADERS, ...(extraHeaders ?? {}) },
  });
}

function notFound(): Response {
  return json({ detail: "not found" }, 404);
}

/** 診断を返してよい環境か。process.env はリクエスト時に読む。 */
function isAuthorizedPreview(): boolean {
  const env = process.env;
  return (
    env.VERCEL === "1" &&
    env.VERCEL_ENV === "preview" &&
    typeof env.VERCEL_GIT_COMMIT_REF === "string" &&
    ALLOWED_PREVIEW_BRANCHES.has(env.VERCEL_GIT_COMMIT_REF)
  );
}

/** Vercel の system env（host 名のみ、scheme なし）を https origin にする。不正なら null。 */
function platformOrigin(host: string | undefined): string | null {
  if (!host || !/^[a-z0-9.-]+$/i.test(host)) return null;
  try {
    const url = new URL(`https://${host}`);
    return url.host === host.toLowerCase() ? url.origin : null;
  } catch {
    return null;
  }
}

function platformReferences(): Map<ReferenceKind, string> {
  const refs = new Map<ReferenceKind, string>();
  const deployment = platformOrigin(process.env.VERCEL_URL);
  const branch = platformOrigin(process.env.VERCEL_BRANCH_URL);
  if (deployment) refs.set("deployment_url", deployment);
  if (branch) refs.set("branch_url", branch);
  return refs;
}

function classifyOrigin(origin: string, refs: Map<ReferenceKind, string>): OriginKind {
  for (const [kind, ref] of refs) {
    if (origin === ref) return kind;
  }
  let url: URL;
  try {
    url = new URL(origin);
  } catch {
    return "unparseable";
  }
  for (const ref of refs.values()) {
    if (new URL(ref).hostname === url.hostname) return "platform_host_scheme_or_port_differs";
  }
  // next-request.js は initURL が絶対 URL でないとき "http://n" を base にする。
  if (url.hostname === "n") return "placeholder";
  if (["localhost", "127.0.0.1", "0.0.0.0", "[::1]", "[::]"].includes(url.hostname)) {
    return "loopback_or_bind_address";
  }
  return "other";
}

function classifySecFetchSite(value: string | null): SecFetchSiteKind {
  if (value === null) return "absent";
  if (value === "same-origin" || value === "same-site" || value === "cross-site" || value === "none") {
    return value;
  }
  return "other";
}

function classifyOriginHeader(value: string | null, reference: string | null): OriginHeaderKind {
  if (value === null) return "absent";
  if (value === "null") return "null";
  try {
    const parsed = new URL(value).origin;
    if (reference !== null && parsed === reference) return "matches_reference";
    return "differs_from_reference";
  } catch {
    return "malformed";
  }
}

/**
 * Host header で「どちらの platform 基準か」を選ぶ。Host は基準そのものにはしない:
 * 既知の platform host と完全一致したときだけ、その platform 値を基準にする。
 */
function selectReference(
  hostHeader: string | null,
  refs: Map<ReferenceKind, string>,
): { kind: ReferenceKind; origin: string } | null {
  if (!hostHeader) return null;
  const host = hostHeader.trim().toLowerCase();
  for (const [kind, ref] of refs) {
    if (new URL(ref).host === host) return { kind, origin: ref };
  }
  return null;
}

function readNextUrlOrigin(req: NextRequest): string | null {
  try {
    return req.nextUrl.origin;
  } catch {
    return null;
  }
}

export async function GET(req: NextRequest): Promise<Response> {
  if (!isAuthorizedPreview()) return notFound();

  const refs = platformReferences();
  const reference = selectReference(req.headers.get("host"), refs);

  const nextUrlOrigin = readNextUrlOrigin(req);

  const nextUrlKind: OriginKind = nextUrlOrigin === null ? "unparseable" : classifyOrigin(nextUrlOrigin, refs);
  const secFetchSite = classifySecFetchSite(req.headers.get("sec-fetch-site"));
  const originHeader = classifyOriginHeader(req.headers.get("origin"), reference?.origin ?? null);

  let result: "match" | "mismatch" | "inconclusive";
  let reason: string | null = null;
  if (refs.size === 0) {
    result = "inconclusive";
    reason = "platform_reference_unavailable";
  } else if (reference === null) {
    result = "inconclusive";
    reason = "request_host_not_a_platform_url";
  } else if (nextUrlOrigin === null || nextUrlKind === "unparseable") {
    result = "inconclusive";
    reason = "next_url_origin_unparseable";
  } else {
    result = nextUrlOrigin === reference.origin ? "match" : "mismatch";
  }

  return json(
    {
      diagnostic: "web-bff-origin",
      version: 1,
      environment: "vercel-preview",
      result,
      reason,
      referenceKind: reference?.kind ?? null,
      nextUrlOriginKind: nextUrlKind,
      secFetchSite,
      secFetchSiteIsSameOrigin: secFetchSite === "same-origin",
      originHeader,
    },
    200,
  );
}

// GET 以外は、許可 Preview では 405、それ以外では GET と同じ 404（存在を示さない）。
function rejectMethod(): Response {
  if (!isAuthorizedPreview()) return notFound();
  return json({ detail: "method not allowed" }, 405, { Allow: "GET" });
}

export async function HEAD(): Promise<Response> {
  return rejectMethod();
}
export async function POST(): Promise<Response> {
  return rejectMethod();
}
export async function PUT(): Promise<Response> {
  return rejectMethod();
}
export async function PATCH(): Promise<Response> {
  return rejectMethod();
}
export async function DELETE(): Promise<Response> {
  return rejectMethod();
}
export async function OPTIONS(): Promise<Response> {
  return rejectMethod();
}
