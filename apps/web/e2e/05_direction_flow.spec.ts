import { expect, test } from "@playwright/test";
import {
  installDirectionScenario,
  matchedDirectionReference,
  mismatchedDirectionReference,
} from "./fixtures/directionScenario";

const consultation = "テスト用の相談です";
const forbiddenAnalyticsKeys = new Set([
  "lat", "lng", "latitude", "longitude", "address", "birthdate", "birthday", "query", "free_text",
]);

async function fillAndSubmit(page: import("@playwright/test").Page) {
  await page.getByLabel("必要なら、今の状況を少しだけ書く").fill(consultation);
  await page.getByRole("button", { name: "この相談で神社を提案してもらう" }).click();
}

function expectPrivateDataAbsent(events: Array<{ payload: Record<string, unknown> }>) {
  for (const { payload } of events) {
    for (const key of Object.keys(payload)) expect(forbiddenAnalyticsKeys.has(key)).toBe(false);
    const serialized = JSON.stringify(payload);
    expect(serialized).not.toContain(consultation);
    expect(serialized).not.toContain("東京駅");
    expect(serialized).not.toContain("東京都");
    expect(serialized).not.toMatch(/35\.681236|139\.767125/);
  }
}

test.describe("方位条件のWeb E2E", () => {
  test("位置情報を許可し、予定日から方位参考情報を表示し、表示イベントを1回だけ送る", async ({ page, context }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 501, directionReference: matchedDirectionReference });
    await context.grantPermissions(["geolocation"]);
    await context.setGeolocation({ latitude: 35.681236, longitude: 139.767125 });
    await page.goto("/concierge");

    await page.getByRole("button", { name: "現在地を使用" }).click();
    await expect(page.getByText("設定中：現在地")).toBeVisible();
    await page.getByLabel("参拝予定日（任意）").fill("2026-09-15");
    await fillAndSubmit(page);

    await expect(page.getByText("方位の参考情報")).toBeVisible();
    await expect(page.getByText("現在地から見た方角が、予定日の参考方位と一致しています。")).toBeVisible();
    const displayOrder = await page.locator('[data-testid="recommendation-match-reason"], [data-testid="recommendation-standard-reason"], aside:has-text("方位の参考情報")').evaluateAll(
      (nodes) => nodes.map((node) => node.textContent),
    );
    expect(displayOrder[0]).toContain("相談内容・ご利益との一致");
    expect(displayOrder[1]).toContain("この神社を選んだ理由");
    expect(displayOrder[2]).toContain("方位の参考情報");
    expect(`${displayOrder[0]}${displayOrder[1]}`).not.toMatch(/方位|方角|吉方位/);
    await expect.poll(() => captured.analyticsEvents.filter((event) => event.eventName === "direction_match_impression").length).toBe(1);
    await page.waitForTimeout(250);
    expect(captured.analyticsEvents.filter((event) => event.eventName === "direction_match_impression")).toHaveLength(1);
    expect(captured.chatPayloads[0]).toMatchObject({ visit_date: "2026-09-15", location: { lat: 35.681236, lng: 139.767125 } });
    expectPrivateDataAbsent(captured.analyticsEvents);
  });

  test("位置情報拒否後、駅名候補を明示選択してBackendの不一致表示を出す", async ({ page, context }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 502, directionReference: mismatchedDirectionReference });
    await context.clearPermissions();
    await page.goto("/concierge");

    await page.getByRole("button", { name: "現在地を使用" }).click();
    await expect(page.getByText(/手動入力を選択できます/)).toBeVisible();
    await page.getByRole("button", { name: "駅名・住所から指定" }).click();
    await page.getByLabel("駅名または住所").fill("東京駅");
    await page.getByRole("button", { name: "東京駅", exact: true }).click();
    await expect(page.getByText("設定中：東京駅")).toBeVisible();
    await page.getByLabel("参拝予定日（任意）").fill("2026-09-15");
    await fillAndSubmit(page);

    await expect(page.getByText("現在地から見た方角は、予定日の参考方位とは異なります。")).toBeVisible();
    expect(captured.geocodeRequests).toHaveLength(1);
    expect(captured.chatPayloads[0]).toMatchObject({ location: { lat: 35.681236, lng: 139.767125 } });
    expect(captured.analyticsEvents.filter((event) => event.eventName === "direction_match_impression")).toHaveLength(0);
    expectPrivateDataAbsent(captured.analyticsEvents);
  });

  test("都道府県は概算地点として表示し、固定レスポンスの方位注記を維持する", async ({ page }) => {
    const reference = { ...matchedDirectionReference, note: "東京都のおおよその位置を基準にした参考情報です。日盤は使用していません。" };
    const captured = await installDirectionScenario(page, { recommendationId: 503, directionReference: reference });
    await page.goto("/concierge");

    await page.getByRole("button", { name: "都道府県から指定" }).click();
    await page.getByLabel("都道府県").selectOption({ label: "東京都" });
    await expect(page.getByText(/東京都のおおよその位置を出発地点として使用します/)).toBeVisible();
    await page.getByLabel("参拝予定日（任意）").fill("2026-09-15");
    await fillAndSubmit(page);

    await expect(page.getByText(/東京都のおおよその位置を基準にした参考情報/)).toBeVisible();
    expect(captured.chatPayloads[0]).toMatchObject({ location: { lat: 35.6762, lng: 139.6503 } });
    expectPrivateDataAbsent(captured.analyticsEvents);
  });

  test("方位情報を使用しなくても相談でき、location・方位カード・方位加点がない", async ({ page }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 504 });
    await page.goto("/concierge");

    await page.getByRole("button", { name: "方位情報を使用しない" }).click();
    await page.getByLabel("参拝予定日（任意）").fill("2026-09-15");
    await fillAndSubmit(page);

    await expect(page.getByText("固定レスポンス神社504")).toBeVisible();
    await expect(page.getByText("方位の参考情報")).toHaveCount(0);
    expect(captured.chatPayloads[0]).not.toHaveProperty("location");
    expect(captured.analyticsEvents.filter((event) => event.eventName === "direction_match_impression")).toHaveLength(0);
    expectPrivateDataAbsent(captured.analyticsEvents);
  });

  test("根拠不足のBackendレスポンスではdirection_referenceを表示しない", async ({ page }) => {
    await installDirectionScenario(page, { recommendationId: 505 });
    await page.goto("/concierge");
    await fillAndSubmit(page);
    await expect(page.getByText("固定レスポンス神社505")).toBeVisible();
    await expect(page.getByText("方位の参考情報")).toHaveCount(0);
  });
});
