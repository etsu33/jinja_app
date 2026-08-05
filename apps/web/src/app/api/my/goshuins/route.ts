// apps/web/src/app/api/my/goshuins/route.ts
import { NextRequest } from "next/server";
import sharp from "sharp";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(req: NextRequest) {
  return bffFetchWithAuthFromReq(req, "/api/my/goshuins/", {
    method: "GET",
  });
}

export async function POST(req: NextRequest) {
  const fd = await req.formData();
  const img = fd.get("image");

  console.log("[BFF] inbound image:", img instanceof File, (img as any)?.type, (img as any)?.name, (img as any)?.size);

  if (!(img instanceof File)) {
    return Response.json({ image: ["missing image"] }, { status: 400 });
  }

  // 画像以外をコピー
  const out = new FormData();
  for (const [k, v] of fd.entries()) {
    if (k === "image") continue;
    out.append(k, typeof v === "string" ? v : String(v));
  }

  // MPO/HEIC混入でもJPEG化。失敗したら400にする
  let jpegBuf: Buffer;
  try {
    const buf = Buffer.from(await img.arrayBuffer());
    jpegBuf = await sharp(buf).jpeg({ quality: 90 }).toBuffer();
  } catch (e) {
    console.log("[BFF] sharp convert failed:", String(e));
    return Response.json({ image: ["invalid or unsupported image"] }, { status: 400 });
  }

  out.append("image", new Blob([new Uint8Array(jpegBuf)], { type: "image/jpeg" }), "upload.jpg");

  return bffFetchWithAuthFromReq(req, "/api/my/goshuins/", {
    method: "POST",
    body: out,
  });
}
