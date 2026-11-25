/**
 * 最初の表示で PostHog が初期化され、$pageview が送られることを固定する。
 *
 * PostHog の初期化は遅延（最初の track() で行う）で、本番では ClientBootstrap の
 * health check がその最初の track() になっている。health check を外すなどして
 * 初期化されなくなると、最初の画面の $pageview が黙って抜け落ちるため、
 * posthog-js の実体を使って送信直前（before_send 適用後）のイベントまで確かめる。
 *
 * posthog-js の状態はモジュール単位の singleton なので、このファイルでは1回だけ描画する。
 */
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";
import posthog, { type CaptureResult } from "posthog-js";

import ClientBootstrap from "@/app/providers/ClientBootstrap";

describe("ClientBootstrap と最初の $pageview", () => {
  const captured: CaptureResult[] = [];
  const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));

  beforeAll(async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_KEY", "phc_test_key");
    // PostHog へ実際には送らない。
    vi.stubGlobal("fetch", fetchMock);

    window.history.replaceState(null, "", "/shrines?q=secret-keyword&utm_source=newsletter");

    // posthog.init の中で送られる最初の $pageview も取りこぼさないよう、描画より前に登録する。
    posthog.on("eventCaptured", (event: CaptureResult) => {
      captured.push(event);
    });

    render(<ClientBootstrap />);

    await waitFor(() => {
      expect(captured.some((event) => event.event === "$pageview")).toBe(true);
    });
  });

  afterAll(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  const pageviews = () => captured.filter((event) => event.event === "$pageview");

  it("マウントで PostHog が初期化され、最初の画面の $pageview が1件送られる", () => {
    expect(posthog.__loaded).toBe(true);
    expect(pageviews()).toHaveLength(1);
    expect(pageviews()[0].properties.$pathname).toBe("/shrines");
  });

  it("最初の $pageview の URL には utm_* 以外の query parameter が残らない", () => {
    const [first] = pageviews();

    expect(first.properties.$current_url).toBe("http://localhost/shrines?utm_source=newsletter");
    expect(first.properties.$session_entry_url).toBe("http://localhost/shrines?utm_source=newsletter");
    // どの property（SDK が自動で付けるものを含む）にも検索語が残らない。
    expect(JSON.stringify(first)).not.toContain("secret-keyword");
  });

  it("パスが変わる遷移で $pageview が1件増え、クエリだけの変化では増えない", async () => {
    window.history.pushState(null, "", "/shrines/1");
    await waitFor(() => expect(pageviews()).toHaveLength(2));
    expect(pageviews()[1].properties.$pathname).toBe("/shrines/1");

    window.history.replaceState(null, "", "/shrines/1?tab=map");
    // 同期で送られるので、ここで増えていなければ送られていない。
    expect(pageviews()).toHaveLength(2);
  });

  it("feature flag の問い合わせ（/flags）を送らない", () => {
    const requestedUrls = fetchMock.mock.calls.map((call) => String((call as unknown[])[0]));

    expect(requestedUrls.some((url) => url.includes("/flags"))).toBe(false);
  });
});
