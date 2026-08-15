import { beforeEach, describe, expect, it, vi } from "vitest";

import { askDeepDive } from "../deepDive";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

describe("deepDive api", () => {
  it("askDeepDive は成功時にresponseをそのまま返す(値の再解釈をしない)", async () => {
    const body = {
      answer: "明治天皇と昭憲皇太后をお祀りしています。",
      readiness: "full",
      question_type: ["deity_who"],
      facts_used: [{ type: "deity", id: 1, label: "明治天皇" }],
      sources_used: [
        { id: 1, title: "公式サイト", publisher: "明治神宮", source_type: "shrine_official", url: "https://example.com" },
      ],
      limitations: null,
      unanswered_aspects: [],
    };

    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(askDeepDive(1, "誰を祀っていますか？")).resolves.toEqual(body);

    expect(fetchMock).toHaveBeenCalledWith("/api/deep-dive/ask/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ shrine_id: 1, question: "誰を祀っていますか？" }),
    });
  });

  it("shrine_idを常に数値へ変換して送信する", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({}),
    });

    await askDeepDive("42", "質問");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/deep-dive/ask/",
      expect.objectContaining({ body: JSON.stringify({ shrine_id: 42, question: "質問" }) }),
    );
  });

  it("400 validation errorはstatus/bodyを持つerrorとしてrejectする", async () => {
    const body = { shrine_id: ["A valid integer is required."] };
    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(askDeepDive(1, "")).rejects.toMatchObject({
      message: "deep_dive_ask_failed",
      status: 400,
      body,
    });
  });

  it("404 shrine not foundはstatus 404のerrorとしてrejectする", async () => {
    const body = { detail: "shrine not found" };
    fetchMock.mockResolvedValue({
      ok: false,
      status: 404,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(askDeepDive(999999, "誰を祀っていますか？")).rejects.toMatchObject({
      status: 404,
      body,
    });
  });

  it("500はstatus 500のerrorとしてrejectする", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "internal error" }),
    });

    await expect(askDeepDive(1, "質問")).rejects.toMatchObject({ status: 500 });
  });

  it("APIエラーは握りつぶさずrejectする(networkエラー)", async () => {
    fetchMock.mockRejectedValue(new Error("network down"));

    await expect(askDeepDive(1, "質問")).rejects.toThrow("network down");
  });
});
