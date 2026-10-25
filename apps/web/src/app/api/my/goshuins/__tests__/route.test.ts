// @vitest-environment node
import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest, NextResponse } from "next/server";

vi.mock("server-only", () => ({}));

vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: vi.fn(),
}));

// 実物の sharp で変換しつつ、decoder に到達したかどうかを数える
const sharpCalls = vi.hoisted(() => ({ count: 0 }));
vi.mock("sharp", async (importOriginal) => {
  const actual = (await importOriginal()) as { default: (...args: unknown[]) => unknown };
  return {
    default: (...args: unknown[]) => {
      sharpCalls.count += 1;
      return actual.default(...args);
    },
  };
});

import sharp from "sharp";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";
import { MAX_IMAGE_BYTES, MAX_REQUEST_BYTES } from "@/lib/server/goshuinUpload";
import { POST } from "../route";

const bffMock = vi.mocked(bffFetchWithAuthFromReq);

const URL_ = "http://localhost/api/my/goshuins";

function multipartRequest(fields: Record<string, string | Blob>, init: { headers?: Record<string, string> } = {}) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) {
    if (typeof v === "string") fd.append(k, v);
    else fd.append(k, v, "photo");
  }
  return new NextRequest(URL_, { method: "POST", body: fd, headers: init.headers });
}

async function makeImage(format: "jpeg" | "png" | "webp", width = 16, height = 16): Promise<Blob> {
  const base = sharp({ create: { width, height, channels: 3, background: { r: 200, g: 30, b: 30 } } });
  const buf = await base[format]().toBuffer();
  return new Blob([new Uint8Array(buf)]);
}

function authorized() {
  bffMock.mockImplementation(async (_req, path, init) => {
    if (path === "/api/my/goshuins/count/") {
      return NextResponse.json({ count: 0, limit: 10, remaining: 10, can_add: true });
    }
    if (path === "/api/my/goshuins/" && init?.method === "POST") {
      return NextResponse.json({ id: 1 }, { status: 201 });
    }
    throw new Error(`unexpected upstream call: ${path}`);
  });
}

function postCalls() {
  return bffMock.mock.calls.filter(([, path, init]) => path === "/api/my/goshuins/" && init?.method === "POST");
}

beforeEach(() => {
  vi.clearAllMocks();
  sharpCalls.count = 0;
});

describe("POST /api/my/goshuins — authentication before decoding", () => {
  it("unauthenticated: returns the backend 401 and never reaches the decoder", async () => {
    bffMock.mockResolvedValue(NextResponse.json({ detail: "not authenticated" }, { status: 401 }));
    const img = await makeImage("jpeg");
    sharpCalls.count = 0;

    const res = await POST(multipartRequest({ image: img, title: "t" }));

    expect(res.status).toBe(401);
    expect(sharpCalls.count).toBe(0);
    expect(bffMock).toHaveBeenCalledTimes(1);
    expect(bffMock).toHaveBeenCalledWith(expect.anything(), "/api/my/goshuins/count/", { method: "GET" });
    expect(postCalls()).toHaveLength(0);
  });

  it("does not read the body when authentication fails", async () => {
    bffMock.mockResolvedValue(NextResponse.json({ detail: "not authenticated" }, { status: 401 }));
    const req = multipartRequest({ image: await makeImage("png") });

    await POST(req);

    expect(req.bodyUsed).toBe(false);
  });

  it("an upstream failure during the auth check is returned as is（fail closed）", async () => {
    bffMock.mockResolvedValue(NextResponse.json({ detail: "unavailable" }, { status: 503 }));
    const img = await makeImage("png");
    sharpCalls.count = 0;

    const res = await POST(multipartRequest({ image: img }));

    expect(res.status).toBe(503);
    expect(sharpCalls.count).toBe(0);
  });
});

describe("POST /api/my/goshuins — size limits", () => {
  it("rejects a declared Content-Length above the limit before any upstream call", async () => {
    const req = new NextRequest(URL_, {
      method: "POST",
      body: "x",
      headers: {
        "content-type": "multipart/form-data; boundary=x",
        "content-length": String(MAX_REQUEST_BYTES + 1),
      },
    });

    const res = await POST(req);

    expect(res.status).toBe(413);
    expect(bffMock).not.toHaveBeenCalled();
    expect(sharpCalls.count).toBe(0);
  });

  it("stops reading a body that exceeds the limit without a Content-Length", async () => {
    authorized();
    const big = new Blob([new Uint8Array(MAX_REQUEST_BYTES + 1)]);

    const res = await POST(multipartRequest({ image: big }));

    expect(res.status).toBe(413);
    expect(await res.json()).toEqual({ image: ["image is too large"] });
    expect(sharpCalls.count).toBe(0);
    expect(postCalls()).toHaveLength(0);
  });

  it("rejects an image file above the image limit", async () => {
    authorized();
    const tooBig = new Blob([new Uint8Array(MAX_IMAGE_BYTES + 1)]);

    const res = await POST(multipartRequest({ image: tooBig }));

    expect(res.status).toBe(413);
    expect(sharpCalls.count).toBe(0);
    expect(postCalls()).toHaveLength(0);
  });
});

describe("POST /api/my/goshuins — allowed formats and malformed input", () => {
  it("rejects a non-multipart request before any upstream call", async () => {
    const req = new NextRequest(URL_, {
      method: "POST",
      body: JSON.stringify({ image: "x" }),
      headers: { "content-type": "application/json" },
    });

    const res = await POST(req);

    expect(res.status).toBe(415);
    expect(bffMock).not.toHaveBeenCalled();
  });

  it("rejects SVG without decoding it", async () => {
    authorized();
    const svg = new Blob(['<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>']);

    const res = await POST(multipartRequest({ image: svg }));

    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ image: ["invalid or unsupported image"] });
    expect(sharpCalls.count).toBe(0);
    expect(postCalls()).toHaveLength(0);
  });

  it("rejects GIF（not in the allow-list）without decoding it", async () => {
    authorized();
    const gif = new Blob([new Uint8Array([0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 1, 0, 1, 0, 0, 0, 0])]);

    const res = await POST(multipartRequest({ image: gif }));

    expect(res.status).toBe(400);
    expect(sharpCalls.count).toBe(0);
  });

  it("rejects a truncated JPEG safely", async () => {
    authorized();
    const broken = new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46])]);

    const res = await POST(multipartRequest({ image: broken }));

    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ image: ["invalid or unsupported image"] });
    expect(postCalls()).toHaveLength(0);
  });

  it("rejects a file whose signature and decoded format disagree", async () => {
    authorized();
    const png = Buffer.from(await (await makeImage("png")).arrayBuffer());
    // RIFF....WEBP の見出しを付けた PNG 本体
    const spoofed = Buffer.concat([Buffer.from("RIFF\0\0\0\0WEBP", "latin1"), png]);

    const res = await POST(multipartRequest({ image: new Blob([new Uint8Array(spoofed)]) }));

    expect(res.status).toBe(400);
    expect(postCalls()).toHaveLength(0);
  });

  it("keeps the existing missing-image response for authenticated requests", async () => {
    authorized();

    const res = await POST(multipartRequest({ title: "t" }));

    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ image: ["missing image"] });
  });
});

describe("POST /api/my/goshuins — valid uploads keep the backend contract", () => {
  it.each(["jpeg", "png", "webp"] as const)("%s is converted to JPEG and forwarded with the other fields", async (format) => {
    authorized();
    const img = await makeImage(format);

    const res = await POST(multipartRequest({ image: img, title: "御朱印", is_public: "true", shrine: "12" }));

    expect(res.status).toBe(201);
    const calls = postCalls();
    expect(calls).toHaveLength(1);
    const body = calls[0][2]?.body as FormData;
    expect(body.get("title")).toBe("御朱印");
    expect(body.get("is_public")).toBe("true");
    expect(body.get("shrine")).toBe("12");
    const forwarded = body.get("image") as File;
    expect(forwarded.name).toBe("upload.jpg");
    expect(forwarded.type).toBe("image/jpeg");
    const meta = await sharp(Buffer.from(await forwarded.arrayBuffer())).metadata();
    expect(meta.format).toBe("jpeg");
  });
});
