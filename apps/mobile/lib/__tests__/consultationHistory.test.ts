// apps/mobile/lib/__tests__/consultationHistory.test.ts
import { describe, expect, it, vi, beforeEach } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

const getAuthMock = vi.fn();

vi.mock("../http", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../http")>();
  return {
    ...actual,
    getAuth: (...args: unknown[]) => getAuthMock(...args),
  };
});

import { listConciergeThreads } from "../consultationHistory";
import { UnauthenticatedError } from "../http";

describe("listConciergeThreads", () => {
  beforeEach(() => {
    getAuthMock.mockReset();
  });

  it("正常系: results配列をそのまま返す", async () => {
    getAuthMock.mockResolvedValueOnce({
      results: [
        { id: 1, title: "相談A", last_message: "本文", last_message_at: "2026-01-01T00:00:00Z", message_count: 2 },
      ],
    });

    const result = await listConciergeThreads();

    expect(result).toEqual([
      { id: 1, title: "相談A", last_message: "本文", last_message_at: "2026-01-01T00:00:00Z", message_count: 2 },
    ]);
  });

  it("正常系: 配列がそのまま返るレスポンス形状にも対応する", async () => {
    getAuthMock.mockResolvedValueOnce([
      { id: 2, title: "相談B", last_message: "本文2", last_message_at: null, message_count: 0 },
    ]);

    const result = await listConciergeThreads();

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(2);
  });

  // 回帰テスト: 401(未認証)時、現状の実装は空配列へfallbackする。
  // 「0件」と「未認証」を区別できない既知の制約であり、History画面はこの関数だけに
  // 頼らず認証状態を別途判定する必要がある(docs/product/history-recommendation-navigation-design.md参照)。
  // この挙動を変更する場合は、呼び出し側(History画面)の空状態判定ロジックも合わせて見直すこと。
  it("回帰テスト: 401(UnauthenticatedError)時は例外を投げず空配列を返す", async () => {
    getAuthMock.mockRejectedValueOnce(new UnauthenticatedError());

    const result = await listConciergeThreads();

    expect(result).toEqual([]);
  });

  it("回帰テスト: 403(HTTPエラー)時は例外を投げず空配列を返す", async () => {
    getAuthMock.mockRejectedValueOnce(new Error("HTTP 403: Forbidden"));

    const result = await listConciergeThreads();

    expect(result).toEqual([]);
  });

  it("回帰テスト: ネットワークエラー等の予期しない例外も空配列へfallbackする", async () => {
    getAuthMock.mockRejectedValueOnce(new TypeError("Network request failed"));

    const result = await listConciergeThreads();

    expect(result).toEqual([]);
  });
});
