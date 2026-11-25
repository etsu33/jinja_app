// 相談履歴（?tid=）の認可失敗時・tid 切替時・アカウント切替時に、別 identity / 別 thread の
// 相談内容が fallback state（localStorage の eventsByThread / 前回の threadDetail / liveUnified）
// 経由で表示されないことの回帰テスト。
// docs/audit/concierge-thread-authorization-isolation-audit.md
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const nav = vi.hoisted(() => ({
  search: new URLSearchParams(),
  replace: vi.fn(),
  push: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: nav.replace, push: nav.push, prefetch: vi.fn(), back: vi.fn() }),
  useSearchParams: () => nav.search,
  usePathname: () => "/concierge",
}));

const auth = vi.hoisted(() => ({
  state: { user: null as null | { id: number }, isLoggedIn: false },
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => auth.state,
}));

vi.mock("@/features/billing/hooks/useBilling", () => ({
  useBilling: () => ({ status: null, loading: false, error: null }),
}));

const api = vi.hoisted(() => ({
  postConciergeChat: vi.fn(),
  getConciergeThread: vi.fn(),
}));

vi.mock("@/lib/api/concierge", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/concierge")>();
  return {
    ...actual,
    postConciergeChat: (...args: unknown[]) => api.postConciergeChat(...args),
    getConciergeThread: (...args: unknown[]) => api.getConciergeThread(...args),
    fetchThreadDetail: (...args: unknown[]) => api.getConciergeThread(...args),
    fetchThreads: vi.fn().mockResolvedValue([]),
  };
});

vi.mock("@/lib/api/tags", () => ({ getGoriyakuTags: vi.fn().mockResolvedValue([]) }));
vi.mock("@/lib/profile/useSharedBirthdayPersistence", () => ({
  useSharedBirthdayPersistence: () => ({ savedBirthday: null, isLoggedIn: false, persistBirthday: vi.fn() }),
}));
vi.mock("@/lib/analytics/track", () => ({ track: vi.fn() }));
vi.mock("@/lib/analytics/directionEvents", () => ({ trackWebDirection: vi.fn() }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: vi.fn() }));
vi.mock("@/lib/analytics/searchEvents", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/analytics/searchEvents")>();
  return Object.fromEntries(Object.entries(actual).map(([k, v]) => [k, typeof v === "function" ? vi.fn() : v]));
});

import ConciergeClientFull from "../ConciergeClientFull";

const STORAGE_KEY = "concierge:eventsByThread";

function rec(id: number, name: string) {
  return { shrine_id: id, id, name, display_name: name, address: "東京都千代田区1-1", reason: "検証用の推薦理由です。", rank: 1 };
}

// 別 identity が同じブラウザで tid=88 を相談したときに localStorage へ残った state。
function seedForeignEvents(tid: number, shrineName: string) {
  const unified = {
    ok: true,
    plan: "free",
    thread: { id: tid, title: "別の人の相談" },
    data: { recommendations: [rec(901, shrineName)] },
  };
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ [tid]: [{ type: "assistant_state", unified, at: "2026-10-22T00:00:00.000Z" }] }),
  );
}

function threadDetail(tid: number, shrineName: string) {
  return {
    id: tid,
    title: `相談${tid}`,
    messages: [],
    recommendations: [rec(tid * 10, shrineName)],
    recommendations_v2: [rec(tid * 10, shrineName)],
  };
}

function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

function setSearch(query: string) {
  nav.search = new URLSearchParams(query);
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
  auth.state = { user: null, isLoggedIn: false };
  api.getConciergeThread.mockResolvedValue(null);
});

afterEach(() => {
  setSearch("");
});

describe("API 401/403/404 のあとに fallback state を描画しない", () => {
  it("localStorage に別 identity の tid=88 が残っていても、API が拒否したら表示しない", async () => {
    seedForeignEvents(88, "別人の神社");
    setSearch("tid=88");
    render(<ConciergeClientFull />);

    await waitFor(() => expect(api.getConciergeThread).toHaveBeenCalledWith("88"));
    await act(async () => {});

    expect(screen.queryByText("別人の神社")).toBeNull();
  });

  it("拒否された tid の local cache は storage から取り除く", async () => {
    seedForeignEvents(88, "別人の神社");
    setSearch("tid=88");
    render(<ConciergeClientFull />);

    await waitFor(() => expect(api.getConciergeThread).toHaveBeenCalledWith("88"));
    await waitFor(() => {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
      expect(stored["88"]).toBeUndefined();
    });
  });

  it("logout 後に ?tid= を直接開いても、残った local cache を表示しない", async () => {
    // 認証中に保存された state が残ったまま Guest で開く
    seedForeignEvents(88, "ログアウト前の神社");
    auth.state = { user: null, isLoggedIn: false };
    setSearch("tid=88");
    render(<ConciergeClientFull />);

    await waitFor(() => expect(api.getConciergeThread).toHaveBeenCalledWith("88"));
    await act(async () => {});
    expect(screen.queryByText("ログアウト前の神社")).toBeNull();
  });
});

describe("認可された thread は従来どおり表示する", () => {
  it("API が 200 を返した自分の thread の推薦を表示する", async () => {
    api.getConciergeThread.mockResolvedValue(threadDetail(10, "自分の神社"));
    setSearch("tid=10");
    render(<ConciergeClientFull />);

    expect(await screen.findByText("自分の神社")).toBeTruthy();
  });

  it("認可確認後は同じ tid の local cache を補助的に使える", async () => {
    // backend の thread に推薦が無い場合、同じ tid の local state（自分の直前の結果）で補う
    seedForeignEvents(10, "直前の結果の神社");
    api.getConciergeThread.mockResolvedValue({ id: 10, title: "相談10", messages: [], recommendations: [], recommendations_v2: [] });
    setSearch("tid=10");
    render(<ConciergeClientFull />);

    expect(await screen.findByText("直前の結果の神社")).toBeTruthy();
  });
});

describe("thread 切替中は前の thread を表示しない", () => {
  it("tid=10 → tid=20 の取得待ちの間、tid=10 の推薦を出さない", async () => {
    api.getConciergeThread.mockResolvedValueOnce(threadDetail(10, "十番の神社"));
    setSearch("tid=10");
    const view = render(<ConciergeClientFull />);
    expect(await screen.findByText("十番の神社")).toBeTruthy();

    const pending = deferred<unknown>();
    api.getConciergeThread.mockReturnValueOnce(pending.promise);
    setSearch("tid=20");
    view.rerender(<ConciergeClientFull />);

    await waitFor(() => expect(api.getConciergeThread).toHaveBeenCalledWith("20"));
    expect(screen.queryByText("十番の神社")).toBeNull();

    await act(async () => {
      pending.resolve(threadDetail(20, "二十番の神社"));
    });
    expect(await screen.findByText("二十番の神社")).toBeTruthy();
    expect(screen.queryByText("十番の神社")).toBeNull();
  });

  it("遅れて返った前の tid の応答で、今の tid を上書きしない", async () => {
    const slow = deferred<unknown>();
    api.getConciergeThread.mockReturnValueOnce(slow.promise);
    setSearch("tid=10");
    const view = render(<ConciergeClientFull />);
    await waitFor(() => expect(api.getConciergeThread).toHaveBeenCalledWith("10"));

    api.getConciergeThread.mockResolvedValueOnce(threadDetail(20, "二十番の神社"));
    setSearch("tid=20");
    view.rerender(<ConciergeClientFull />);
    expect(await screen.findByText("二十番の神社")).toBeTruthy();

    await act(async () => {
      slow.resolve(threadDetail(10, "十番の神社"));
    });
    expect(screen.queryByText("十番の神社")).toBeNull();
    expect(screen.getByText("二十番の神社")).toBeTruthy();
  });
});

describe("アカウント切替", () => {
  it("identity が変わったら、同じ tid でも新しい identity で認可を確認し直す", async () => {
    auth.state = { user: { id: 1 }, isLoggedIn: true };
    api.getConciergeThread.mockResolvedValue(threadDetail(10, "Aさんの神社"));
    setSearch("tid=10");
    const view = render(<ConciergeClientFull />);
    expect(await screen.findByText("Aさんの神社")).toBeTruthy();
    const callsBefore = api.getConciergeThread.mock.calls.length;

    api.getConciergeThread.mockResolvedValue(null);
    auth.state = { user: { id: 2 }, isLoggedIn: true };
    view.rerender(<ConciergeClientFull />);

    await waitFor(() => expect(api.getConciergeThread.mock.calls.length).toBeGreaterThan(callsBefore));
    await act(async () => {});
    expect(screen.queryByText("Aさんの神社")).toBeNull();
  });

  it("同じ画面で identity が変わったら、前の identity の表示と local cache を捨てる", async () => {
    auth.state = { user: { id: 1 }, isLoggedIn: true };
    api.getConciergeThread.mockResolvedValue(threadDetail(10, "Aさんの神社"));
    setSearch("tid=10");
    const view = render(<ConciergeClientFull />);
    expect(await screen.findByText("Aさんの神社")).toBeTruthy();

    // B としてログインし直す（同じタブ・リロードなし）。B は tid=10 を読めない。
    api.getConciergeThread.mockResolvedValue(null);
    auth.state = { user: { id: 2 }, isLoggedIn: true };
    view.rerender(<ConciergeClientFull />);

    await waitFor(() => expect(screen.queryByText("Aさんの神社")).toBeNull());
    await waitFor(() => {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
      expect(Object.keys(stored)).toEqual([]);
    });
  });
});
