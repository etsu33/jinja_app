import { act, renderHook } from "@testing-library/react";
import { AxiosError, AxiosHeaders } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiMocks = vi.hoisted(() => ({
  fetchThreads: vi.fn(),
}));

vi.mock("@/lib/api/concierge", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/concierge")>();
  return {
    ConciergeThreadsResponseError: actual.ConciergeThreadsResponseError,
    fetchThreadsStrict: apiMocks.fetchThreads,
  };
});

import { ConciergeThreadsResponseError } from "@/lib/api/concierge";

import { useConciergeThreadSave } from "../useConciergeThreadSave";

function axiosWithStatus(status: number, data: unknown = {}, contentType = "application/json") {
  return new AxiosError(`status ${status}`, status >= 500 ? "ERR_BAD_RESPONSE" : "ERR_BAD_REQUEST", undefined, undefined, {
    status,
    statusText: String(status),
    data,
    headers: { "content-type": contentType },
    config: { headers: new AxiosHeaders() },
  });
}

function axios401() {
  return axiosWithStatus(401);
}

function setup(props: { threadId: number | null; canSave: boolean }) {
  const onAuthRequired = vi.fn();
  const hook = renderHook((p: { threadId: number | null; canSave: boolean }) =>
    useConciergeThreadSave({ ...p, onAuthRequired }),
    { initialProps: props },
  );
  return { ...hook, onAuthRequired };
}

describe("useConciergeThreadSave", () => {
  beforeEach(() => {
    apiMocks.fetchThreads.mockReset();
  });

  it("未ログイン: API を呼ばずログイン誘導する", async () => {
    const { result, onAuthRequired } = setup({ threadId: 10, canSave: false });

    await act(async () => {
      await result.current.save();
    });

    expect(onAuthRequired).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchThreads).not.toHaveBeenCalled();
    expect(result.current.state.status).toBe("idle");
  });

  it("ログイン済み: ユーザーの履歴一覧に thread があれば saved と履歴リンクを返す", async () => {
    apiMocks.fetchThreads.mockResolvedValue([{ id: 9 }, { id: 10 }]);
    const { result, onAuthRequired } = setup({ threadId: 10, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(onAuthRequired).not.toHaveBeenCalled();
    expect(result.current.state).toEqual({ status: "saved", error: null, historyHref: "/mypage/history/10" });
  });

  it("ログイン済み: 履歴一覧に thread が無ければ成功を報告しない(not_owned)", async () => {
    apiMocks.fetchThreads.mockResolvedValue([{ id: 9 }]);
    const { result } = setup({ threadId: 10, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.state).toEqual({ status: "error", error: "not_owned", historyHref: null });
  });

  it("確認 API の失敗は network エラーとして表示する", async () => {
    apiMocks.fetchThreads.mockRejectedValue(new Error("boom"));
    const { result } = setup({ threadId: 10, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.state).toEqual({ status: "error", error: "network", historyHref: null });
  });

  it("本番再現: upstream 502 (text/html) は server_unavailable として扱い、成功表示しない", async () => {
    apiMocks.fetchThreads.mockRejectedValue(axiosWithStatus(502, "<!DOCTYPE html>...", "text/html; charset=utf-8"));
    const { result } = setup({ threadId: 89, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.state).toEqual({ status: "error", error: "server_unavailable", historyHref: null });
  });

  it("server_unavailable の後は再クリックで再確認でき、成功すれば saved になる", async () => {
    apiMocks.fetchThreads
      .mockRejectedValueOnce(axiosWithStatus(502, "<html></html>", "text/html"))
      .mockResolvedValueOnce([{ id: 89 }]);
    const { result } = setup({ threadId: 89, canSave: true });

    await act(async () => {
      await result.current.save();
    });
    expect(result.current.state.error).toBe("server_unavailable");

    await act(async () => {
      await result.current.save();
    });
    expect(apiMocks.fetchThreads).toHaveBeenCalledTimes(2);
    expect(result.current.state).toEqual({ status: "saved", error: null, historyHref: "/mypage/history/89" });
  });

  it("2xx だが一覧形式で読めない応答は not_owned ではなく invalid_response", async () => {
    apiMocks.fetchThreads.mockRejectedValue(new ConciergeThreadsResponseError());
    const { result } = setup({ threadId: 89, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.state.error).toBe("invalid_response");
  });

  it("応答の無い axios エラー(transport 失敗)は network", async () => {
    apiMocks.fetchThreads.mockRejectedValue(new AxiosError("Network Error", "ERR_NETWORK"));
    const { result } = setup({ threadId: 89, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.state.error).toBe("network");
  });

  it("確認 API の 401 はセッション切れ(unauthenticated)として扱う", async () => {
    apiMocks.fetchThreads.mockRejectedValue(axios401());
    const { result } = setup({ threadId: 10, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.state.error).toBe("unauthenticated");
  });

  it("thread が無い(0)場合は API を呼ばず no_thread エラー", async () => {
    const { result } = setup({ threadId: 0, canSave: true });

    await act(async () => {
      await result.current.save();
    });

    expect(apiMocks.fetchThreads).not.toHaveBeenCalled();
    expect(result.current.state.error).toBe("no_thread");
  });

  it("確認中・確認済みの連打で重複リクエストしない", async () => {
    let resolve!: (v: unknown) => void;
    apiMocks.fetchThreads.mockReturnValue(new Promise((r) => (resolve = r)));
    const { result } = setup({ threadId: 10, canSave: true });

    let first!: Promise<void>;
    act(() => {
      first = result.current.save();
    });
    expect(result.current.state.status).toBe("saving");

    await act(async () => {
      await result.current.save();
    });
    expect(apiMocks.fetchThreads).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolve([{ id: 10 }]);
      await first;
    });
    expect(result.current.state.status).toBe("saved");

    await act(async () => {
      await result.current.save();
    });
    expect(apiMocks.fetchThreads).toHaveBeenCalledTimes(1);
  });

  it("別の thread に切り替わると保存状態をリセットする", async () => {
    apiMocks.fetchThreads.mockResolvedValue([{ id: 10 }]);
    const { result, rerender } = setup({ threadId: 10, canSave: true });

    await act(async () => {
      await result.current.save();
    });
    expect(result.current.state.status).toBe("saved");

    rerender({ threadId: 11, canSave: true });
    expect(result.current.state.status).toBe("idle");
  });
});
