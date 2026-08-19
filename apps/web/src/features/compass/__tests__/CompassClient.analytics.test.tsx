import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Compass lifecycle analytics (PR-A,
// docs/audit/compass-analytics-contract-readiness.md §6-10): Home discovery
// -> Compass entry -> Compass activation/result. Recommendation exposure,
// Shrine Detail, Favorite/Visit/Reflection attribution are explicitly out
// of scope for this PR and are not touched here.
//
// Mocked at the dispatch-helper boundary (trackSearchEvent), not PostHog
// itself -- matches ConciergeSectionsRenderer.recommendationInstanceId.test.tsx.
const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

// Local override of vitest.setup.ts's blanket `useSearchParams: () => new
// URLSearchParams()` -- reads window.location.search dynamically so each
// test can set `?ref=home` via history.pushState, same pattern as
// src/app/shrines/__tests__/page.test.tsx.
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

import CompassClient from "../CompassClient";

function setOriginViaPrefecture() {
  fireEvent.click(screen.getByRole("button", { name: "変更する" }));
  fireEvent.click(screen.getByRole("radio", { name: "都道府県から指定" }));
  fireEvent.change(screen.getByLabelText("都道府県"), { target: { value: "東京都" } });
}

function fillMinimumValidInput() {
  fireEvent.click(screen.getByRole("radio", { name: "転機・仕事" }));
  setOriginViaPrefecture();
  fireEvent.change(screen.getByLabelText("生年月日（方位計算に使用）"), {
    target: { value: "1990-01-01" },
  });
}

function submit() {
  return act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
  });
}

describe("CompassClient lifecycle analytics", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    analyticsMocks.trackSearchEvent.mockClear();
    window.history.pushState({}, "", "/compass");
  });

  describe("Compass Entry", () => {
    it("直接遷移ではcompass_entryをreferrer_source=directで一度だけ送る", () => {
      render(<CompassClient />);

      const entryCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_entry");
      expect(entryCalls).toHaveLength(1);
      expect(entryCalls[0][1]).toEqual({ referrer_source: "direct" });
    });

    it("?ref=homeで遷移した場合はcompass_entryをreferrer_source=homeで送る（HomeのCTAクリックとは別イベント）", () => {
      window.history.pushState({}, "", "/compass?ref=home");
      render(<CompassClient />);

      const entryCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_entry");
      expect(entryCalls).toHaveLength(1);
      expect(entryCalls[0][1]).toEqual({ referrer_source: "home" });
    });

    it("再レンダーではcompass_entryを重複送信しない", () => {
      const { rerender } = render(<CompassClient />);
      fireEvent.click(screen.getByRole("radio", { name: "転機・仕事" }));
      rerender(<CompassClient />);

      const entryCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_entry");
      expect(entryCalls).toHaveLength(1);
    });
  });

  describe("Compass Activation / Result", () => {
    it("必須項目が未入力のまま送信するとcompass_resultを送らない（バリデーション失敗はActivationとして扱わない）", () => {
      vi.stubGlobal("fetch", vi.fn());
      render(<CompassClient />);

      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));

      expect(analyticsMocks.trackSearchEvent).not.toHaveBeenCalledWith("compass_result", expect.anything());
      expect(fetch).not.toHaveBeenCalled();
    });

    it("recommendation_successでresult_state・recommendation_count・purpose・origin_modeを送り、PIIを含まない", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
          ok: true,
          status: 200,
          json: async () => ({
            state: "recommendation_success",
            purpose: "career",
            direction_context: {
              targetDate: "2026-09-15",
              targetYear: 2026,
              solarMonthIndex: 8,
              referenceDirections: ["北西"],
              calculationMethod: "annual_monthly_kyusei_v1",
              note: "note",
            },
            recommendation_instance_id: "compass01",
            recommendations: [
              { shrine_id: 1, name: "北西神社", reason: "仕事運との一致" },
              { shrine_id: 2, name: "北西二の宮", reason: "縁結び" },
            ],
          }),
        }),
      );

      render(<CompassClient />);
      fillMinimumValidInput();
      await submit();

      const resultCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_result");
      expect(resultCalls).toHaveLength(1);
      const [, payload] = resultCalls[0];

      expect(payload).toEqual({
        result_state: "recommendation_success",
        purpose: "career",
        origin_mode: "prefecture",
        has_birthdate: true,
        recommendation_count: 2,
        recommendationInstanceId: "compass01",
      });

      // PII / data-minimization contract (task §10, §24 of the readiness audit):
      const serialized = JSON.stringify(payload);
      expect(payload).not.toHaveProperty("birthdate");
      expect(payload).not.toHaveProperty("latitude");
      expect(payload).not.toHaveProperty("longitude");
      expect(serialized).not.toContain("1990-01-01");
      expect(serialized).not.toMatch(/東京都/);
      expect(serialized).not.toContain("35.6762");
      expect(serialized).not.toContain("139.6503");
    });

    it("direction_zero_candidatesとdirection_filter_unavailableをresult_stateとして区別する（collapse禁止）", async () => {
      const fetchMock = vi.fn();
      vi.stubGlobal("fetch", fetchMock);
      render(<CompassClient />);
      fillMinimumValidInput();

      fetchMock.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          state: "direction_zero_candidates",
          purpose: "career",
          direction_context: null,
          recommendations: [],
        }),
      });
      await submit();

      fetchMock.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          state: "direction_filter_unavailable",
          purpose: "career",
          direction_context: null,
          recommendations: [],
        }),
      });
      await submit();

      const resultStates = analyticsMocks.trackSearchEvent.mock.calls
        .filter(([name]) => name === "compass_result")
        .map(([, payload]) => (payload as { result_state: string }).result_state);

      expect(resultStates).toEqual(["direction_zero_candidates", "direction_filter_unavailable"]);
      // recommendation_count must not be fabricated for non-success states.
      const zeroCandidatesPayload = analyticsMocks.trackSearchEvent.mock.calls.find(
        ([name, payload]) => name === "compass_result" && (payload as { result_state: string }).result_state === "direction_zero_candidates",
      )?.[1] as { recommendation_count: unknown };
      expect(zeroCandidatesPayload.recommendation_count).toBeNull();
    });

    it("invalid_purpose（HTTP 400）をresult_stateとして正しく表す", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
          ok: false,
          status: 400,
          json: async () => ({
            state: "invalid_purpose",
            purpose: null,
            direction_context: null,
            recommendations: [],
          }),
        }),
      );

      render(<CompassClient />);
      fillMinimumValidInput();
      await submit();

      const resultCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_result");
      expect(resultCalls).toHaveLength(1);
      expect(resultCalls[0][1]).toMatchObject({ result_state: "invalid_purpose" });
    });

    it("バックエンドエラー(HTTP 500)をresult_state=backend_errorとして表す", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));

      render(<CompassClient />);
      fillMinimumValidInput();
      await submit();

      const resultCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_result");
      expect(resultCalls).toHaveLength(1);
      expect(resultCalls[0][1]).toMatchObject({ result_state: "backend_error", recommendation_count: null });
    });

    it("ネットワーク例外もresult_state=backend_errorとして表す", async () => {
      vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

      render(<CompassClient />);
      fillMinimumValidInput();
      await submit();

      const resultCalls = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "compass_result");
      expect(resultCalls).toHaveLength(1);
      expect(resultCalls[0][1]).toMatchObject({ result_state: "backend_error" });
    });
  });

  describe("匿名利用", () => {
    it("未ログイン状態でもcompass_entry/compass_resultの計測が例外を投げない", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
          ok: true,
          status: 200,
          json: async () => ({
            state: "recommendation_success",
            purpose: "career",
            direction_context: null,
            recommendations: [],
          }),
        }),
      );

      expect(() => render(<CompassClient />)).not.toThrow();
      fillMinimumValidInput();
      await expect(submit()).resolves.not.toThrow();
    });
  });
});
