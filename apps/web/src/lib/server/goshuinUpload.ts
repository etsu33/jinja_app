// apps/web/src/lib/server/goshuinUpload.ts
//
// 御朱印アップロード（POST /api/my/goshuins）で、画像 decoder に渡す前の入力を絞る。
// 認証は呼び出し側（route.ts）で、body を読む前に行う。
import "server-only";

import sharp from "sharp";

// Backend の MAX_GOSHUIN_IMAGE_BYTES（10MB）と揃える。multipart の他フィールド分だけ余裕を持たせる。
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
export const MAX_REQUEST_BYTES = MAX_IMAGE_BYTES + 512 * 1024;
// 48MP 級のスマートフォン写真は通しつつ、decoder に渡す画素数の上限を固定する（sharp 既定値は約 268M）。
export const MAX_INPUT_PIXELS = 64_000_000;

// JPEG（MPO を含む）/ PNG / WebP / HEIF 系（AVIF・HEIC）だけを decoder へ渡す。
// SVG・GIF・TIFF・BMP などそれ以外の形式は decode する前に拒否する。
export type ImageKind = "jpeg" | "png" | "webp" | "heif";

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const HEIF_BRANDS = new Set(["heic", "heix", "hevc", "hevx", "heim", "heis", "mif1", "msf1", "avif", "avis"]);

export function sniffImageKind(buf: Buffer): ImageKind | null {
  if (buf.length >= 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return "jpeg";
  if (buf.length >= 8 && buf.subarray(0, 8).equals(PNG_SIGNATURE)) return "png";
  if (buf.length >= 12 && buf.toString("latin1", 0, 4) === "RIFF" && buf.toString("latin1", 8, 12) === "WEBP") {
    return "webp";
  }
  if (buf.length >= 12 && buf.toString("latin1", 4, 8) === "ftyp" && HEIF_BRANDS.has(buf.toString("latin1", 8, 12))) {
    return "heif";
  }
  return null;
}

/** 上限を超えた時点で読み取りを打ち切る。超えたら null。Content-Length が無い・偽りの場合も効く。 */
export async function readBodyWithLimit(
  body: ReadableStream<Uint8Array> | null,
  limit: number,
): Promise<Uint8Array<ArrayBuffer> | null> {
  if (!body) return new Uint8Array(0);

  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > limit) {
      await reader.cancel().catch(() => undefined);
      return null;
    }
    chunks.push(value);
  }

  const out = new Uint8Array(total);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.byteLength;
  }
  return out;
}

/**
 * 許可形式であることを確かめてから JPEG に変換する。許可外・破損・画素数超過は null。
 * シグネチャと sharp が検出した形式の両方が一致したものだけを decode する。
 */
export async function convertToJpeg(buf: Buffer): Promise<Buffer | null> {
  const kind = sniffImageKind(buf);
  if (kind === null) return null;

  try {
    const input = sharp(buf, { limitInputPixels: MAX_INPUT_PIXELS });
    const meta = await input.metadata();
    if (meta.format !== kind) return null;
    return await input.jpeg({ quality: 90 }).toBuffer();
  } catch {
    return null;
  }
}
