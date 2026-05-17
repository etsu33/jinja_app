import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  parseBillingFunnelSource,
  parseBillingFunnelStep,
  serializeBillingAnalyticsPayload,
  trackBillingEvent,
} from "../billing";
import { track } from "../track";

vi.mock("../track", () => ({
  track: vi.fn(),
}));

const trackMock = vi.mocked(track);

describe("billing analytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("parseBillingFunnelSource", () => {
    it("想定外値をnullにfallbackする", () => {
      expect(parseBillingFunnelSource("state_delta_card")).toBe("state_delta_card");
      expect(parseBillingFunnelSource("unexpected_source")).toBeNull();
      expect(parseBillingFunnelSource(null)).toBeNull();
    });
  });

  describe("parseBillingFunnelStep", () => {
    it("想定外値をnullにfallbackする", () => {
      expect(parseBillingFunnelStep("comparison_preview")).toBe("comparison_preview");
      expect(parseBillingFunnelStep("unexpected_step")).toBeNull();
      expect(parseBillingFunnelStep(null)).toBeNull();
    });
  });

  describe("serializeBillingAnalyticsPayload", () => {
    it("null / undefinedだけ除去し、false / 0 / 空文字は残す", () => {
      expect(
        serializeBillingAnalyticsPayload({
          source: null,
          funnelStep: undefined,
          disabled: false,
          count: 0,
          label: "",
        }),
      ).toEqual({
        disabled: false,
        count: 0,
        label: "",
      });
    });

    it("session_id / sessionIdをpayloadから除去する", () => {
      expect(
        serializeBillingAnalyticsPayload({
          checkoutSessionId: "cs_test_123",
          session_id: "raw_session_id",
          sessionId: "rawSessionId",
        }),
      ).toEqual({
        checkoutSessionId: "cs_test_123",
      });
    });
  });

  describe("trackBillingEvent", () => {
    it("analyticsの例外を外に投げない", () => {
      trackMock.mockImplementationOnce(() => {
        throw new Error("analytics failed");
      });

      expect(() => {
        trackBillingEvent("checkout_started", {
          checkoutSessionId: "cs_test_123",
        });
      }).not.toThrow();
    });

    it("session_id / sessionIdをtrack payloadに残さない", () => {
      trackBillingEvent("checkout_started", {
        checkoutSessionId: "cs_test_123",
        session_id: "raw_session_id",
        sessionId: "rawSessionId",
      });

      expect(trackMock).toHaveBeenCalledWith("checkout_started", {
        area: "billing",
        checkoutSessionId: "cs_test_123",
      });
    });
  });
});
