import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { track } from "../track";

const STORAGE_KEY = "app:track:dev-events";

describe("track", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    window.localStorage.clear();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("test環境ではイベントを送信しない", () => {
    vi.stubEnv("NODE_ENV", "test");
    const listener = vi.fn();

    window.addEventListener("app:track", listener);
    track("empty_state_view", { q: "存在しない神社" });
    window.removeEventListener("app:track", listener);

    expect(listener).not.toHaveBeenCalled();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it("development環境ではCustomEventを送信し、localStorageに保存する", () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.spyOn(console, "info").mockImplementation(() => undefined);
    const listener = vi.fn();

    window.addEventListener("app:track", listener);
    track("add_shrine_click", { q: "未登録神社", returnTo: "/shrines?q=%E6%9C%AA%E7%99%BB%E9%8C%B2" });
    window.removeEventListener("app:track", listener);

    expect(console.info).toHaveBeenCalledWith(
      "[track]",
      expect.objectContaining({
        eventName: "add_shrine_click",
        payload: expect.objectContaining({
          q: "未登録神社",
          returnTo: "/shrines?q=%E6%9C%AA%E7%99%BB%E9%8C%B2",
          analyticsSessionId: expect.any(String),
          sessionId: expect.any(String),
        }),
        timestamp: expect.any(String),
      }),
    );

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0]?.[0]).toBeInstanceOf(CustomEvent);
    expect(listener.mock.calls[0]?.[0].detail).toEqual(
      expect.objectContaining({
        eventName: "add_shrine_click",
        payload: expect.objectContaining({
          q: "未登録神社",
          returnTo: "/shrines?q=%E6%9C%AA%E7%99%BB%E9%8C%B2",
          analyticsSessionId: expect.any(String),
          sessionId: expect.any(String),
        }),
        timestamp: expect.any(String),
      }),
    );

    const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    expect(saved).toHaveLength(1);
    expect(saved[0]).toEqual(
      expect.objectContaining({
        eventName: "add_shrine_click",
        payload: expect.objectContaining({
          q: "未登録神社",
          returnTo: "/shrines?q=%E6%9C%AA%E7%99%BB%E9%8C%B2",
          analyticsSessionId: expect.any(String),
          sessionId: expect.any(String),
        }),
        timestamp: expect.any(String),
      }),
    );
  });

  it("development環境では保存済みイベントを最大100件に丸める", () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.spyOn(console, "info").mockImplementation(() => undefined);

    const existingEvents = Array.from({ length: 100 }, (_, index) => ({
      eventName: `event_${index}`,
      payload: { index },
      timestamp: "2026-01-01T00:00:00.000Z",
    }));
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(existingEvents));

    track("latest_event", { index: 100 });

    const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    expect(saved).toHaveLength(100);
    expect(saved[0].eventName).toBe("event_1");
    expect(saved[99]).toEqual(
      expect.objectContaining({
        eventName: "latest_event",
        payload: expect.objectContaining({
          index: 100,
          analyticsSessionId: expect.any(String),
          sessionId: expect.any(String),
        }),
        timestamp: expect.any(String),
      }),
    );
  });

  it("development環境でlocalStorage保存に失敗してもイベント送信は継続する", () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.spyOn(console, "info").mockImplementation(() => undefined);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("storage failed");
    });
    const listener = vi.fn();

    window.addEventListener("app:track", listener);
    expect(() => track("empty_state_view", { q: "保存失敗テスト" })).not.toThrow();
    window.removeEventListener("app:track", listener);

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0]?.[0].detail).toEqual(
      expect.objectContaining({
        eventName: "empty_state_view",
        payload: { q: "保存失敗テスト" },
        timestamp: expect.any(String),
      }),
    );
  });
});
