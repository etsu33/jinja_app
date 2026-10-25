// apps/web/src/app/api/my/goshuins/route.ts
import { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";
import {
  MAX_IMAGE_BYTES,
  MAX_REQUEST_BYTES,
  convertToJpeg,
  readBodyWithLimit,
} from "@/lib/server/goshuinUpload";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

function imageError(message: string, status: number) {
  return Response.json({ image: [message] }, { status });
}

export async function GET(req: NextRequest) {
  return bffFetchWithAuthFromReq(req, "/api/my/goshuins/", {
    method: "GET",
  });
}

export async function POST(req: NextRequest) {
  // body を読む前に、宣言された形式と長さだけで弾けるものを弾く
  const contentType = req.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().startsWith("multipart/form-data")) {
    return imageError("multipart/form-data is required", 415);
  }
  const declaredLength = Number(req.headers.get("content-length") ?? "");
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
    return imageError("image is too large", 413);
  }

  // 認証の正本は Backend。body を読む・decode する前に、同じ認証情報で認可されるかを確かめる
  const auth = await bffFetchWithAuthFromReq(req, "/api/my/goshuins/count/", { method: "GET" });
  if (!auth.ok) return auth;

  const raw = await readBodyWithLimit(req.body, MAX_REQUEST_BYTES);
  if (raw === null) return imageError("image is too large", 413);

  let fd: FormData;
  try {
    fd = await new Response(raw, { headers: { "content-type": contentType } }).formData();
  } catch {
    return imageError("invalid multipart body", 400);
  }

  const img = fd.get("image");
  if (!(img instanceof File)) {
    return imageError("missing image", 400);
  }
  if (img.size > MAX_IMAGE_BYTES) {
    return imageError("image is too large", 413);
  }

  // 画像以外をコピー
  const out = new FormData();
  for (const [k, v] of fd.entries()) {
    if (k === "image") continue;
    out.append(k, typeof v === "string" ? v : String(v));
  }

  // 許可形式（JPEG/MPO・PNG・WebP・HEIF 系）だけを JPEG 化する。それ以外・破損は 400
  const jpegBuf = await convertToJpeg(Buffer.from(await img.arrayBuffer()));
  if (jpegBuf === null) {
    return imageError("invalid or unsupported image", 400);
  }

  out.append("image", new Blob([new Uint8Array(jpegBuf)], { type: "image/jpeg" }), "upload.jpg");

  return bffFetchWithAuthFromReq(req, "/api/my/goshuins/", {
    method: "POST",
    body: out,
  });
}
