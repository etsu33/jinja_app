import type { Page, Request } from "@playwright/test";

export type CapturedDirectionScenario = {
  chatPayloads: Array<Record<string, unknown>>;
  analyticsEvents: Array<{ eventName: string; payload: Record<string, unknown> }>;
  geocodeRequests: string[];
};

type DirectionReference = {
  visit_date: string;
  actual_direction: string;
  reference_directions: string[];
  matched: boolean;
  calculation_method: string;
  note: string;
};

export async function installDirectionScenario(
  page: Page,
  options: {
    recommendationId: number;
    directionReference?: DirectionReference | Record<string, unknown>;
    geocodeFailure?: "500";
    additionalRecommendation?: {
      id: number;
      directionReference?: DirectionReference;
    };
  },
): Promise<CapturedDirectionScenario> {
  const captured: CapturedDirectionScenario = {
    chatPayloads: [],
    analyticsEvents: [],
    geocodeRequests: [],
  };

  await page.exposeFunction("captureDirectionAnalytics", (event: unknown) => {
    captured.analyticsEvents.push(event as CapturedDirectionScenario["analyticsEvents"][number]);
  });
  await page.addInitScript(() => {
    window.addEventListener("app:track", (event) => {
      const detail = (event as CustomEvent).detail;
      if (detail?.eventName?.startsWith("direction_")) {
        void (window as typeof window & { captureDirectionAnalytics: (value: unknown) => Promise<void> })
          .captureDirectionAnalytics({ eventName: detail.eventName, payload: detail.payload });
      }
    });
  });

  // 後続の個別routeに該当しない初期化APIも外へ出さない。
  await page.route("**/api/**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) }),
  );

  // 画面初期化に必要なBFFもブラウザ側で完結させ、Backendへ接続させない。
  await page.route("**/api/users/me/**", (route) =>
    route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "anonymous test user" }) }),
  );
  await page.route("**/api/billings/status/**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ plan: "free", is_active: false }) }),
  );
  await page.route("**/api/goriyaku-tags/**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) }),
  );

  await page.route("**/api/geocodes/search/**", async (route) => {
    captured.geocodeRequests.push(route.request().url());
    if (options.geocodeFailure === "500") {
      await route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: "fixed failure" }) });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          { place_id: "station-tokyo", name: "東京駅", lat: 35.681236, lng: 139.767125, type: "station" },
          { place_id: "address-test", name: "テスト住所候補", lat: 35.68, lng: 139.76, type: "address" },
        ],
      }),
    });
  });

  await page.route("**/api/concierge/chat/**", async (route) => {
    const request: Request = route.request();
    captured.chatPayloads.push(request.postDataJSON() as Record<string, unknown>);
    const recommendation = {
      shrine_id: options.recommendationId,
      display_name: `固定レスポンス神社${options.recommendationId}`,
      display_address: "テスト用所在地",
      reason: "固定レスポンスによる推薦です。",
      breakdown: { matched_need_tags: ["career"] },
      reason_facts: { primary_axis: "benefit", shrine_benefit: "仕事運を整えるご利益" },
      ...(options.directionReference ? { direction_reference: options.directionReference } : {}),
    };
    const recommendations = [recommendation];
    if (options.additionalRecommendation) {
      recommendations.push({
        shrine_id: options.additionalRecommendation.id,
        display_name: `固定レスポンス神社${options.additionalRecommendation.id}`,
        display_address: "テスト用所在地",
        reason: "固定レスポンスによる推薦です。",
        breakdown: { matched_need_tags: ["career"] },
        reason_facts: { primary_axis: "benefit", shrine_benefit: "仕事運を整えるご利益" },
        ...(options.additionalRecommendation.directionReference
          ? { direction_reference: options.additionalRecommendation.directionReference }
          : {}),
      });
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: { recommendations, recommendations_v2: recommendations },
        thread: { id: options.recommendationId },
        remaining: 9,
      }),
    });
  });

  return captured;
}

export const matchedDirectionReference: DirectionReference = {
  visit_date: "2026-09-15",
  actual_direction: "東",
  reference_directions: ["東", "北西"],
  matched: true,
  calculation_method: "annual_monthly_kyusei_v1",
  note: "年盤と月盤による参考情報です。日盤は使用していません。",
};

export const mismatchedDirectionReference: DirectionReference = {
  ...matchedDirectionReference,
  actual_direction: "南",
  matched: false,
};
