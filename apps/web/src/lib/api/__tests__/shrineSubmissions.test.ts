import { beforeEach, describe, expect, it, vi } from "vitest";

import { createShrineSubmission, getMyShrineSubmissions } from "../shrineSubmissions";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

describe("shrineSubmissions api", () => {
  it("createShrineSubmission は submission を作成して返す", async () => {
    const body = {
      id: 1,
      name: "投稿神社",
      address: "東京都千代田区1-1-1",
      lat: null,
      lng: null,
      goriyaku_tags: ["開運"],
      note: "補足",
      status: "pending",
      created_at: "2026-04-01T00:00:00Z",
    };

    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(
      createShrineSubmission({
        name: "投稿神社",
        address: "東京都千代田区1-1-1",
        goriyaku_tags: ["開運"],
        note: "補足",
      }),
    ).resolves.toEqual(body);

    expect(fetchMock).toHaveBeenCalledWith("/api/shrine-submissions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        name: "投稿神社",
        address: "東京都千代田区1-1-1",
        goriyaku_tags: ["開運"],
        note: "補足",
      }),
    });
  });

  it("getMyShrineSubmissions は配列レスポンスをそのまま返す", async () => {
    const body = [
      {
        id: 1,
        name: "投稿神社",
        address: "東京都千代田区1-1-1",
        lat: null,
        lng: null,
        goriyaku_tags: [],
        note: "",
        status: "approved",
        created_at: "2026-04-01T00:00:00Z",
        reviewed_at: "2026-04-02T00:00:00Z",
        review_comment: null,
      },
    ];

    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(getMyShrineSubmissions()).resolves.toEqual(body);

    expect(fetchMock).toHaveBeenCalledWith("/api/shrine-submissions/", {
      method: "GET",
      credentials: "include",
    });
  });

  it("getMyShrineSubmissions は results 形式を配列に正規化する", async () => {
    const results = [
      {
        id: 2,
        name: "ページング投稿神社",
        address: "東京都港区2-2-2",
        lat: null,
        lng: null,
        goriyaku_tags: [],
        note: "",
        status: "pending",
        created_at: "2026-04-03T00:00:00Z",
        reviewed_at: null,
        review_comment: null,
      },
    ];
    const body = {
      count: 1,
      next: null,
      previous: null,
      results,
    };

    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(getMyShrineSubmissions()).resolves.toEqual(results);

    expect(fetchMock).toHaveBeenCalledWith("/api/shrine-submissions/", {
      method: "GET",
      credentials: "include",
    });
  });

  it("getMyShrineSubmissions は失敗時に status と body を持つ error を投げる", async () => {
    const body = { detail: "unauthorized" };

    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });

    await expect(getMyShrineSubmissions()).rejects.toMatchObject({
      message: "submission_list_failed",
      status: 401,
      body,
    });
  });
});
