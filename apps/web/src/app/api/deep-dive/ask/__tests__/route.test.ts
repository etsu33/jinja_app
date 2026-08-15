import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

const djFetchMock = vi.fn();

vi.mock("@/lib/server/backend", () => ({
  djFetch: (...args: unknown[]) => djFetchMock(...args),
}));

import { POST } from "../route";

function makeReq(body: unknown) {
  return new NextRequest("http://localhost/api/deep-dive/ask/", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("/api/deep-dive/ask BFF contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("upstream 200(Full)をそのまま透過する", async () => {
    const upstreamBody = {
      answer: "回答本文。",
      readiness: "full",
      question_type: ["deity_who"],
      facts_used: [],
      sources_used: [],
      limitations: null,
      unanswered_aspects: [],
    };
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify(upstreamBody), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ shrine_id: 1, question: "誰を祀っていますか？" }));

    expect(djFetchMock).toHaveBeenCalledTimes(1);
    const [, path, init] = djFetchMock.mock.calls[0];
    expect(path).toBe("/api/deep-dive/ask/");
    expect(init).toMatchObject({ method: "POST", forwardAuth: false });

    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual(upstreamBody);
  });

  it("upstream 200(not_ready)もそのまま200として透過する(errorに変換しない)", async () => {
    const upstreamBody = {
      answer: "",
      readiness: "not_ready",
      question_type: [],
      facts_used: [],
      sources_used: [],
      limitations: "この神社については、根拠付きで詳しくお答えできる情報がまだ十分ではありません。",
      unanswered_aspects: [],
    };
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify(upstreamBody), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ shrine_id: 58, question: "誰を祀っていますか？" }));

    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual(upstreamBody);
  });

  it("upstream 400はstatusをそのまま透過する", async () => {
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify({ question: ["This field is required."] }), {
        status: 400,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ shrine_id: 1 }));

    expect(res.status).toBe(400);
  });

  it("upstream 404はstatusをそのまま透過する", async () => {
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "shrine not found" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ shrine_id: 999999, question: "質問" }));

    expect(res.status).toBe(404);
  });

  it("upstream 500はstatusをそのまま透過する", async () => {
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "internal error" }), {
        status: 500,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ shrine_id: 1, question: "質問" }));

    expect(res.status).toBe(500);
  });

  it("djFetch自体が例外を投げた場合(network失敗)は502を返す", async () => {
    djFetchMock.mockRejectedValue(new Error("ECONNREFUSED"));

    const res = await POST(makeReq({ shrine_id: 1, question: "質問" }));

    expect(res.status).toBe(502);
  });
});
