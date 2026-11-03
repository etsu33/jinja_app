import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

const authFetch = vi.fn();
const convert = vi.fn();
vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: (...args: unknown[]) => authFetch(...args),
}));
vi.mock("sharp", () => ({
  default: (...args: unknown[]) => {
    convert(...args);
    return {
      rotate: () => ({
        resize: () => ({
          jpeg: () => ({
            toBuffer: async () => Buffer.from("jpeg"),
          }),
        }),
      }),
    };
  },
}));

import { POST } from "./route";

function uploadRequest(body: FormData, headers?: Record<string, string>) {
  return new NextRequest("http://localhost/api/my/goshuins", {
    method: "POST",
    body,
    headers,
  });
}

describe("goshuin upload authorization and bounds", () => {
  beforeEach(() => {
    authFetch.mockReset();
    convert.mockReset();
  });

  it("rejects unauthenticated uploads before reading or decoding", async () => {
    authFetch.mockResolvedValueOnce(new Response(null, { status: 401 }));
    const fd = new FormData();
    fd.set("image", new File(["attacker"], "a.png", { type: "image/png" }));
    const res = await POST(uploadRequest(fd));
    expect(res.status).toBe(401);
    expect(authFetch).toHaveBeenCalledTimes(1);
    expect(convert).not.toHaveBeenCalled();
  });

  it("rejects an oversized declared body before parsing", async () => {
    authFetch.mockResolvedValueOnce(new Response(null, { status: 200 }));
    const fd = new FormData();
    fd.set("image", new File(["a"], "a.png", { type: "image/png" }));
    const res = await POST(uploadRequest(fd, { "content-length": String(9 * 1024 * 1024) }));
    expect(res.status).toBe(413);
    expect(convert).not.toHaveBeenCalled();
  });

  it("rejects a streamed oversized body without relying on content-length", async () => {
    authFetch.mockResolvedValueOnce(new Response(null, { status: 200 }));
    const body = new Uint8Array(8 * 1024 * 1024 + 1);
    const req = new NextRequest("http://localhost/api/my/goshuins", {
      method: "POST",
      headers: { "content-type": "multipart/form-data; boundary=abc" },
      body,
    });
    const res = await POST(req);
    expect(res.status).toBe(413);
    expect(convert).not.toHaveBeenCalled();
  });

  it("converts a bounded authenticated upload and forwards it", async () => {
    authFetch.mockResolvedValueOnce(new Response(null, { status: 200 }));
    authFetch.mockResolvedValueOnce(new Response(null, { status: 201 }));
    const fd = new FormData();
    fd.set("image", new File(["small"], "a.png", { type: "image/png" }));
    const res = await POST(uploadRequest(fd));
    expect(res.status).toBe(201);
    expect(convert).toHaveBeenCalledTimes(1);
    expect(authFetch).toHaveBeenCalledTimes(2);
    expect(authFetch.mock.calls[1][1]).toBe("/api/my/goshuins/");
    expect(authFetch.mock.calls[1][2].method).toBe("POST");
  });
});
