// @vitest-environment node
import { describe, it, expect, vi } from "vitest";

vi.mock("server-only", () => ({}));

import sharp from "sharp";
import {
  MAX_INPUT_PIXELS,
  convertToJpeg,
  readBodyWithLimit,
  sniffImageKind,
} from "@/lib/server/goshuinUpload";

function streamOf(chunks: Uint8Array[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(c);
      controller.close();
    },
  });
}

describe("sniffImageKind", () => {
  it("recognizes the allowed signatures", () => {
    expect(sniffImageKind(Buffer.from([0xff, 0xd8, 0xff, 0xe1]))).toBe("jpeg");
    expect(sniffImageKind(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))).toBe("png");
    expect(sniffImageKind(Buffer.from("RIFF\0\0\0\0WEBPVP8 ", "latin1"))).toBe("webp");
    expect(sniffImageKind(Buffer.from("\0\0\0\x18ftypheic\0\0\0\0", "latin1"))).toBe("heif");
    expect(sniffImageKind(Buffer.from("\0\0\0\x18ftypavif\0\0\0\0", "latin1"))).toBe("heif");
  });

  it("rejects everything else", () => {
    expect(sniffImageKind(Buffer.from("<svg xmlns='http://www.w3.org/2000/svg'/>"))).toBeNull();
    expect(sniffImageKind(Buffer.from("GIF89a\x01\0\x01\0", "latin1"))).toBeNull();
    expect(sniffImageKind(Buffer.from("BM\0\0\0\0\0\0\0\0", "latin1"))).toBeNull();
    expect(sniffImageKind(Buffer.from([0x49, 0x49, 0x2a, 0x00]))).toBeNull(); // TIFF
    expect(sniffImageKind(Buffer.from("\0\0\0\x18ftypisom\0\0\0\0", "latin1"))).toBeNull(); // MP4
    expect(sniffImageKind(Buffer.alloc(0))).toBeNull();
  });
});

describe("readBodyWithLimit", () => {
  it("returns the bytes when within the limit", async () => {
    const out = await readBodyWithLimit(streamOf([new Uint8Array([1, 2]), new Uint8Array([3])]), 3);
    expect(Array.from(out ?? [])).toEqual([1, 2, 3]);
  });

  it("returns null as soon as the limit is exceeded", async () => {
    const out = await readBodyWithLimit(streamOf([new Uint8Array(3), new Uint8Array(1)]), 3);
    expect(out).toBeNull();
  });

  it("treats a missing body as empty", async () => {
    expect((await readBodyWithLimit(null, 1))?.byteLength).toBe(0);
  });
});

describe("convertToJpeg", () => {
  it("rejects an image above the pixel limit", async () => {
    // 16001 x 4000 = 64,004,000 画素で MAX_INPUT_PIXELS を超える
    const wide = await sharp({
      create: { width: MAX_INPUT_PIXELS / 4000 + 1, height: 4000, channels: 3, background: "#fff" },
    })
      .png({ compressionLevel: 1 })
      .toBuffer();

    expect(await convertToJpeg(wide)).toBeNull();
  }, 30_000);
});
