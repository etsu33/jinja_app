import { describe, expect, it } from "vitest";
import type { CaptureResult } from "posthog-js";

import {
  isAllowedQueryParam,
  sanitizeCaptureResult,
  stripDisallowedQueryParams,
} from "@/lib/analytics/urlSanitizer";

describe("isAllowedQueryParam", () => {
  it.each(["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_custom"])(
    "%s は許可する",
    (name) => {
      expect(isAllowedQueryParam(name)).toBe(true);
    },
  );

  it.each(["q", "query", "lat", "lng", "email", "gclid", "fbclid", "UTM_SOURCE", "xutm_source", ""])(
    "%j は許可しない",
    (name) => {
      expect(isAllowedQueryParam(name)).toBe(false);
    },
  );
});

describe("stripDisallowedQueryParams", () => {
  it("検索語などの query parameter を除く", () => {
    expect(stripDisallowedQueryParams("https://example.com/shrines?q=%E7%A5%9E%E7%A4%BE")).toBe(
      "https://example.com/shrines",
    );
  });

  it("utm_* だけを残す", () => {
    expect(
      stripDisallowedQueryParams(
        "https://example.com/shrines?q=secret&utm_source=x&page=2&utm_campaign=autumn",
      ),
    ).toBe("https://example.com/shrines?utm_source=x&utm_campaign=autumn");
  });

  it("フラグメントは残す", () => {
    expect(stripDisallowedQueryParams("https://example.com/a?q=secret&utm_medium=sns#top")).toBe(
      "https://example.com/a?utm_medium=sns#top",
    );
  });

  it("フラグメント内の ? は query として扱わない", () => {
    expect(stripDisallowedQueryParams("https://example.com/a#x?q=1")).toBe("https://example.com/a#x?q=1");
  });

  it("query の無い URL・$direct・相対パスもそのまま、または同じ規則で扱う", () => {
    expect(stripDisallowedQueryParams("https://example.com/a")).toBe("https://example.com/a");
    expect(stripDisallowedQueryParams("$direct")).toBe("$direct");
    expect(stripDisallowedQueryParams("/shrines?q=secret&utm_term=t")).toBe("/shrines?utm_term=t");
  });
});

describe("sanitizeCaptureResult（before_send）", () => {
  function buildCaptureResult(overrides: Partial<CaptureResult> = {}): CaptureResult {
    return {
      uuid: "uuid-1",
      event: "$pageview",
      properties: {
        $current_url: "https://example.com/shrines?q=secret&utm_source=x",
        $referrer: "https://example.com/plan?q=secret2",
        $pathname: "/shrines",
        other: "keep?q=not-a-target",
      },
      ...overrides,
    };
  }

  it("null はそのまま返す", () => {
    expect(sanitizeCaptureResult(null)).toBeNull();
  });

  it("properties の $current_url / $referrer から utm_* 以外を除き、ほかの property は変えない", () => {
    const result = sanitizeCaptureResult(buildCaptureResult());

    expect(result?.properties.$current_url).toBe("https://example.com/shrines?utm_source=x");
    expect(result?.properties.$referrer).toBe("https://example.com/plan");
    expect(result?.properties.$pathname).toBe("/shrines");
    expect(result?.properties.other).toBe("keep?q=not-a-target");
    expect(result?.event).toBe("$pageview");
    expect(result?.uuid).toBe("uuid-1");
  });

  it("$set_once 内の $initial_current_url / $current_url / $referrer も絞る", () => {
    const result = sanitizeCaptureResult(
      buildCaptureResult({
        event: "$identify",
        $set_once: {
          $initial_current_url: "https://example.com/shrines?q=first&utm_campaign=c",
          $current_url: "https://example.com/shrines?q=entry",
          $referrer: "https://example.com/?q=ref",
          $initial_utm_source: "x",
        },
      }),
    );

    expect(result?.$set_once).toEqual({
      $initial_current_url: "https://example.com/shrines?utm_campaign=c",
      $current_url: "https://example.com/shrines",
      $referrer: "https://example.com/",
      $initial_utm_source: "x",
    });
  });

  it("$set と properties 内の $set / $set_once も絞る", () => {
    const result = sanitizeCaptureResult(
      buildCaptureResult({
        $set: { $current_url: "https://example.com/a?q=1" },
        properties: {
          $current_url: "https://example.com/b?q=2",
          $set: { $current_url: "https://example.com/c?q=3" },
          $set_once: { $initial_current_url: "https://example.com/d?q=4&utm_term=t" },
        },
      }),
    );

    expect(result?.$set).toEqual({ $current_url: "https://example.com/a" });
    expect(result?.properties.$current_url).toBe("https://example.com/b");
    expect(result?.properties.$set).toEqual({ $current_url: "https://example.com/c" });
    expect(result?.properties.$set_once).toEqual({ $initial_current_url: "https://example.com/d?utm_term=t" });
  });

  it("元の CaptureResult は書き換えない", () => {
    const original = buildCaptureResult({ $set_once: { $initial_current_url: "https://example.com/?q=1" } });
    const snapshot = structuredClone(original);

    sanitizeCaptureResult(original);

    expect(original).toEqual(snapshot);
  });
});
