// Home → /concierge?theme=... の自動送信ルートで、
// 空の本文・入力フォームの一瞬の表示を挟まず、待機表示 → 結果 の順になることの回帰テスト。
// plain /concierge（入口）と /concierge?tid=...（thread 復元）は従来どおりであることも確認する。
import { act, render, screen, waitFor } from "@testing-library/react";
import { renderToString } from "react-dom/server";
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

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => ({ user: null, isLoggedIn: false }),
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
  const stubbed = Object.fromEntries(
    Object.entries(actual).map(([k, v]) => [k, typeof v === "function" ? vi.fn() : v]),
  );
  return stubbed;
});

import ConciergeClientFull from "../ConciergeClientFull";
import ConciergeRouteFallback from "../ConciergeRouteFallback";
import { readAutoSubmitTheme } from "@/features/concierge/components/ConciergeAutoSubmitPending";

const THEME = "仕事の迷いを整理したい";

const recs = [1, 2, 3].map((id, i) => ({
  shrine_id: id,
  id,
  name: `検証神社${id}`,
  display_name: `検証神社${id}`,
  address: "東京都千代田区1-1",
  reason: "検証用の推薦理由です。",
  rank: i + 1,
}));

function chatPayload(recommendations: unknown[]) {
  return {
    ok: true,
    plan: "free",
    remaining: 2,
    limit: 3,
    limitReached: false,
    thread: { id: 10, title: "検証相談" },
    data: { recommendations },
  };
}

function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

// 入力フォーム（#concierge-input）が一度でも DOM に挿入されたかを記録する。
function watchEntryForm(container: HTMLElement) {
  const seen = { entryForm: false };
  const check = (node: Node) => {
    if (!(node instanceof Element)) return;
    if (node.id === "concierge-input" || node.querySelector("#concierge-input")) seen.entryForm = true;
  };
  const observer = new MutationObserver((records) => {
    for (const r of records) r.addedNodes.forEach(check);
  });
  observer.observe(container, { childList: true, subtree: true });
  check(container);
  return { seen, stop: () => observer.disconnect() };
}

function setSearch(query: string) {
  nav.search = new URLSearchParams(query);
}

function pendingPanel() {
  return screen.queryByTestId("concierge-auto-submit-pending");
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
  api.getConciergeThread.mockResolvedValue(null);
});

afterEach(() => {
  setSearch("");
});

describe("readAutoSubmitTheme", () => {
  it("theme があり tid が無い（または不正）ときだけ theme を返す", () => {
    expect(readAutoSubmitTheme(new URLSearchParams(`theme=${THEME}`))).toBe(THEME);
    expect(readAutoSubmitTheme(new URLSearchParams("theme=%20%20"))).toBe("");
    expect(readAutoSubmitTheme(new URLSearchParams(""))).toBe("");
    expect(readAutoSubmitTheme(new URLSearchParams(`theme=${THEME}&tid=10`))).toBe("");
    expect(readAutoSubmitTheme(new URLSearchParams(`theme=${THEME}&tid=abc`))).toBe(THEME);
  });
});

describe("route Suspense fallback", () => {
  it("?theme= では待機表示を出す", () => {
    setSearch(`theme=${THEME}`);
    render(<ConciergeRouteFallback />);
    expect(pendingPanel()).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("相談をもとに、神社を選んでいます…");
    expect(screen.getByText(THEME)).toBeInTheDocument();
  });

  it("plain /concierge と ?tid= では従来どおり何も出さない", () => {
    setSearch("");
    const { container, unmount } = render(<ConciergeRouteFallback />);
    expect(container).toBeEmptyDOMElement();
    unmount();

    setSearch(`tid=10&theme=${THEME}`);
    const second = render(<ConciergeRouteFallback />);
    expect(second.container).toBeEmptyDOMElement();
  });
});

describe("/concierge?theme=... bootstrap（hydrate 前）", () => {
  it("hydrate 前の描画でも本文は空にならず、待機表示を出し、入力フォームは出さない", () => {
    setSearch(`theme=${THEME}`);
    const html = renderToString(<ConciergeClientFull />);
    expect(html).toContain('data-testid="concierge-auto-submit-pending"');
    expect(html).toContain(THEME);
    expect(html).not.toContain('id="concierge-input"');
  });

  it("plain /concierge の hydrate 前の描画は従来どおり（待機表示なし）", () => {
    setSearch("");
    const html = renderToString(<ConciergeClientFull />);
    expect(html).not.toContain('data-testid="concierge-auto-submit-pending"');
  });
});

describe("/concierge?theme=... 自動送信", () => {
  it("待機表示のまま送信し、入力フォームを一度も挟まずに結果へ進む", async () => {
    setSearch(`theme=${THEME}`);
    const chat = deferred<unknown>();
    api.postConciergeChat.mockReturnValue(chat.promise);

    const { container } = render(<div data-testid="root" />);
    const watcher = watchEntryForm(container);
    render(<ConciergeClientFull />, { container });

    await waitFor(() => expect(api.postConciergeChat).toHaveBeenCalledTimes(1));
    expect(api.postConciergeChat.mock.calls[0][0]).toMatchObject({ query: THEME });

    // 送信中: 待機表示のみ。入力フォーム・送信ボタン・旧 overlay は出さない
    expect(pendingPanel()).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByRole("button", { name: "この相談で神社を提案してもらう" })).toBeNull();
    expect(screen.queryByText("選定中です…")).toBeNull();

    await act(async () => {
      chat.resolve(chatPayload(recs));
    });

    await waitFor(() => expect(screen.getByRole("link", { name: "神社の詳細を見る" })).toBeInTheDocument());
    expect(pendingPanel()).toBeNull();
    expect(nav.replace).toHaveBeenCalledWith("/concierge?tid=10");
    expect(watcher.seen.entryForm).toBe(false);
    watcher.stop();
  });

  it("推薦0件でも ?tid= 確定まで待機表示を保ち、入力フォームを挟まない", async () => {
    setSearch(`theme=${THEME}`);
    api.postConciergeChat.mockResolvedValue(chatPayload([]));

    const { container, rerender } = render(<div />);
    const watcher = watchEntryForm(container);
    rerender(<ConciergeClientFull />);

    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/concierge?tid=10"));
    await act(async () => {});
    expect(pendingPanel()).toBeInTheDocument();

    // router.replace の確定（URL が ?tid=10 になる）
    setSearch("tid=10");
    rerender(<ConciergeClientFull />);
    await waitFor(() => expect(pendingPanel()).toBeNull());
    expect(watcher.seen.entryForm).toBe(false);
    watcher.stop();
  });

  it("API 失敗時は待機表示を解き、従来の入口表示（入力とエラー案内）へ戻る", async () => {
    setSearch(`theme=${THEME}`);
    api.postConciergeChat.mockRejectedValue(new Error("network"));

    render(<ConciergeClientFull />);

    await waitFor(() => expect(pendingPanel()).toBeNull());
    expect(screen.getByDisplayValue(THEME)).toBeInTheDocument();
    expect(screen.getByText("うまく取得できませんでした")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "この相談で神社を提案してもらう" })).toBeEnabled();
    expect(nav.replace).not.toHaveBeenCalledWith(expect.stringContaining("tid="));
  });
});

describe("既存ルートは変えない", () => {
  it("plain /concierge は入口表示のまま（待機表示なし・自動送信なし）", async () => {
    setSearch("");
    render(<ConciergeClientFull />);

    await waitFor(() => expect(document.querySelector("#concierge-input")).not.toBeNull());
    expect(pendingPanel()).toBeNull();
    expect(api.postConciergeChat).not.toHaveBeenCalled();
  });

  it("/concierge?tid=... は thread 復元のまま（待機表示なし・入口なし・自動送信なし）", async () => {
    setSearch("tid=10");
    render(<ConciergeClientFull />);

    await waitFor(() => expect(api.getConciergeThread).toHaveBeenCalledWith("10"));
    expect(pendingPanel()).toBeNull();
    expect(document.querySelector("#concierge-input")).toBeNull();
    expect(api.postConciergeChat).not.toHaveBeenCalled();
  });
});
