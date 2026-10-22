import { act, renderHook } from "@testing-library/react";
import { AxiosError, AxiosHeaders } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiMocks = vi.hoisted(() => ({
  fetchThreads: vi.fn(),
}));

vi.mock("@/lib/api/concierge", () => ({
  fetchThreads: apiMocks.fetchThreads,
}));

import { useConciergeThreadSave } from "../useConciergeThreadSave";

function axios401() {
  return new AxiosError("unauthorized", "ERR_BAD_REQUEST", undefined, undefined, {
    status: 401,
    statusText: "Unauthorized",
    data: {},
    headers: {},
    config: { headers: new AxiosHeaders() },
  });
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
