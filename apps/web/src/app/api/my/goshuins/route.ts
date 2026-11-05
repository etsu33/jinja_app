// apps/web/src/app/api/my/goshuins/route.ts
import { NextRequest } from "next/server";
import sharp from "sharp";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// Enforce the raw request limit before multipart parsing, not just after File extraction.
const MAX_REQUEST_BYTES = 8 * 1024 * 1024;
const MAX_IMAGE_BYTES = 7 * 1024 * 1024;
const MAX_INPUT_PIXELS = 20_000_000;
const MAX_OUTPUT_DIMENSION = 2048;
const ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]);

function tooLarge() {
  return Response.json({ image: ["image too large"] }, { status: 413 });
}

async function readBoundedBody(req: NextRequest): Promise<Uint8Array | null> {
  if (!req.body) return new Uint8Array();
  const reader = req.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_REQUEST_BYTES) {
        await reader.cancel().catch(() => undefined);
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return result;
}

export async function GET(req: NextRequest) {
  return bffFetchWithAuthFromReq(req, "/api/my/goshuins/", {
    method: "GET",
  });
}

export async function POST(req: NextRequest) {
  // Validate the session with the authenticated upstream before reading the body or invoking sharp.
  // Cookie/header presence is NOT authentication.
  const authCheck = await bffFetchWithAuthFromReq(req, "/api/my/goshuins/", { method: "GET" });
  if (authCheck.status !== 200) {
    return Response.json({ detail: "authentication required" }, { status: 401 });
  }

  const declaredLength = req.headers.get("content-length");
  if (declaredLength !== null) {
    const length = Number(declaredLength);
    if (!Number.isSafeInteger(length) || length < 0) {
      return Response.json({ detail: "invalid request length" }, { status: 400 });
    }
    if (length > MAX_REQUEST_BYTES) return tooLarge();
  }

  const contentType = req.headers.get("content-type") ?? "";
  if (!/^multipart\/form-data(?:;|$)/i.test(contentType)) {
    return Response.json({ detail: "multipart form required" }, { status: 415 });
  }

  let fd: FormData;
  try {
    const bytes = await readBoundedBody(req);
    if (bytes === null) return tooLarge();
    const boundedRequest = new Request("http://localhost/upload", {
      method: "POST",
      headers: { "content-type": contentType },
      body: bytes,
    });
    fd = await boundedRequest.formData();
  } catch {
    return Response.json({ image: ["invalid form data"] }, { status: 400 });
  }

  const img = fd.get("image");
  if (!(img instanceof File)) {
    return Response.json({ image: ["missing image"] }, { status: 400 });
  }
  if (img.size > MAX_IMAGE_BYTES) return tooLarge();
  if (!ALLOWED_TYPES.has(img.type.toLowerCase())) {
    return Response.json({ image: ["unsupported image type"] }, { status: 415 });
  }

  const out = new FormData();
  for (const [k, v] of fd.entries()) {
    if (k === "image") continue;
    if (typeof v !== "string") {
      return Response.json({ detail: "unexpected file field" }, { status: 400 });
    }
    out.append(k, v);
  }

  let jpegBuf: Buffer;
  try {
    const input = Buffer.from(await img.arrayBuffer());
    jpegBuf = await sharp(input, { limitInputPixels: MAX_INPUT_PIXELS })
      .rotate()
      .resize(MAX_OUTPUT_DIMENSION, MAX_OUTPUT_DIMENSION, { fit: "inside", withoutEnlargement: true })
      .jpeg({ quality: 85 })
      .toBuffer();
  } catch {
    // Never log attacker-supplied names, contents, or decoder exceptions.
    return Response.json({ image: ["invalid or unsupported image"] }, { status: 400 });
  }

  out.append("image", new Blob([new Uint8Array(jpegBuf)], { type: "image/jpeg" }), "upload.jpg");
  return bffFetchWithAuthFromReq(req, "/api/my/goshuins/", {
    method: "POST",
    body: out,
  });
}
