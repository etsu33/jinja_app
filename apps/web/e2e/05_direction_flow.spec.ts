import { expect, test } from "@playwright/test";
import { createServer, type Server } from "node:http";
import {
  installDirectionScenario,
  matchedDirectionReference,
  mismatchedDirectionReference,
} from "./fixtures/directionScenario";
import directionAnalyticsForbiddenKeys from "../../../packages/shared/directionAnalyticsForbiddenKeys.json" with { type: "json" };

const consultation = "テスト用の相談です";
let fixedBackend: Server;

test.beforeAll(async () => {
  fixedBackend = createServer((request, response) => {
    response.setHeader("Content-Type", "application/json");
    if (/^\/api\/public\/shrines\/\d+\/$/.test(request.url ?? "")) {
      const id = Number(request.url?.match(/\d+/)?.[0] ?? 508);
      response.end(JSON.stringify({ id, name_jp: `固定詳細神社${id}`, latitude: 35.68, longitude: 139.76, address: "固定テスト所在地" }));
      return;
    }
    if ((request.url ?? "").includes("goshuin")) {
      response.end(JSON.stringify([]));
      return;
    }
    response.statusCode = 404;
    response.end(JSON.stringify({ detail: "fixed e2e response" }));
  });
  await new Promise<void>((resolve, reject) => {
    fixedBackend.once("error", reject);
    fixedBackend.listen(8000, "127.0.0.1", resolve);
  });
});

test.afterAll(async () => {
  await new Promise<void>((resolve, reject) => fixedBackend.close((error) => error ? reject(error) : resolve()));
});
const forbiddenAnalyticsKeys = new Set<string>(directionAnalyticsForbiddenKeys);

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

test.describe.configure({ mode: "serial" });
test.describe("方位条件のWeb E2E", () => {
  test("位置情報を許可し、予定日から方位参考情報を表示し、表示イベントを1回だけ送る", async ({ page, context }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 501, directionReference: matchedDirectionReference });
    await context.grantPermissions(["geolocation"]);
    await context.setGeolocation({ latitude: 35.681236, longitude: 139.767125 });
    await page.goto("/concierge");

    await page.getByRole("radio", { name: "現在地を使用" }).click();
    await expect(
      page.getByText("現在の出発地点は現在地、確定した位置です。"),
    ).toBeVisible();
    await page.getByLabel("参拝予定日（任意）").fill("2026-09-15");
    await fillAndSubmit(page);

    await expect(page.getByText("方位の参考情報")).toBeVisible();
    await expect(page.getByText("現在地から見た方角が、予定日の参考方位と一致しています。")).toBeVisible();
    const displayOrder = await page.locator(
      '[data-testid="recommendation-reason-v4-fact"], [data-testid="recommendation-reason-v4-interpretation"], [data-testid="recommendation-reason-v4-action"], aside:has-text("方位の参考情報")',
    ).evaluateAll((nodes) => nodes.map((node) => node.textContent));
    expect(displayOrder[0]).toContain("この神社について");
    expect(displayOrder[1]).toContain("今の相談とのつながり");
    expect(displayOrder[2]).toContain("参拝前にできること");
    expect(displayOrder[3]).toContain("方位の参考情報");
    expect(`${displayOrder[0]}${displayOrder[1]}${displayOrder[2]}`).not.toMatch(/方位|方角|吉方位/);
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

    await page.getByRole("radio", { name: "現在地を使用" }).click();
    await expect(
      page.getByRole("button", { name: "駅名・住所から指定する" }),
    ).toBeVisible();
    await page.getByRole("radio", { name: "駅名・住所から指定" }).click();
    await page.getByLabel("駅名または住所").fill("東京駅");
    await page.getByRole("option", { name: "東京駅", exact: true }).click();
    await expect(
      page.getByText("現在の出発地点は東京駅、確定した位置です。"),
    ).toBeVisible();
    await page.getByLabel("参拝予定日（任意）").fill("2026-09-15");
    await fillAndSubmit(page);

    await expect(page.getByText("現在地から見た方角は、予定日の参考方位とは異なります。")).toBeVisible();
    expect(captured.geocodeRequests).toHaveLength(1);
    expect(captured.chatPayloads[0]).toMatchObject({ location: { lat: 35.681236, lng: 139.767125 } });
    expect(captured.analyticsEvents.filter((event) => event.eventName === "direction_match_impression")).toEqual([
      expect.objectContaining({ payload: expect.objectContaining({ matched: false }) }),
    ]);
    expectPrivateDataAbsent(captured.analyticsEvents);
  });

  test("都道府県は概算地点として表示し、固定レスポンスの方位注記を維持する", async ({ page }) => {
    const reference = { ...matchedDirectionReference, note: "東京都のおおよその位置を基準にした参考情報です。日盤は使用していません。" };
    const captured = await installDirectionScenario(page, { recommendationId: 503, directionReference: reference });
    await page.goto("/concierge");

    await page.getByRole("radio", { name: "都道府県から指定" }).click();
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

    await page.getByRole("radio", { name: "方位情報を使用しない" }).click();
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

  test("ジオコード500でも方位を無効化して通常相談を継続できる", async ({ page }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 510, geocodeFailure: "500" });
    await page.goto("/concierge");
    await page.getByRole("radio", { name: "駅名・住所から指定" }).click();
    await page.getByLabel("駅名または住所").fill("失敗地点");
    await expect(page.getByText("候補を検索できませんでした。相談はそのまま続けられます。")).toBeVisible();
    await page.getByRole("radio", { name: "方位情報を使用しない" }).click();
    await fillAndSubmit(page);
    await expect(page.getByText("固定レスポンス神社510")).toBeVisible();
    expect(captured.chatPayloads[0]).not.toHaveProperty("location");
  });

  test("未知のcalculation_methodは通常候補を維持して方位だけ省略する", async ({ page }) => {
    await installDirectionScenario(page, {
      recommendationId: 511,
      directionReference: { ...matchedDirectionReference, calculation_method: "future_unknown_v2" },
    });
    await page.goto("/concierge");
    await fillAndSubmit(page);
    await expect(page.getByText("固定レスポンス神社511")).toBeVisible();
    await expect(page.getByTestId("recommendation-reason-v4-fact")).toBeVisible();
    await expect(page.getByText("方位の参考情報")).toHaveCount(0);
  });

  test("キーボードだけで手動候補を選択して相談を送信できる", async ({ page }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 506, directionReference: mismatchedDirectionReference });
    await page.goto("/concierge");

    const manualMode = page.getByRole("radio", { name: "駅名・住所から指定" });
    await manualMode.focus();
    await expect(manualMode).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(manualMode).toHaveAttribute("aria-checked", "true");

    const input = page.getByRole("combobox", { name: "駅名または住所" });
    await input.focus();
    await page.keyboard.type("東京駅");
    const option = page.getByRole("option", { name: "東京駅" });
    await option.focus();
    await expect(option).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByText("現在の出発地点は東京駅、確定した位置です。")).toBeVisible();

    await page.getByLabel("必要なら、今の状況を少しだけ書く").fill(consultation);
    const submit = page.getByRole("button", { name: "この相談で神社を提案してもらう" });
    await submit.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByText("固定レスポンス神社506")).toBeVisible();
    expect(captured.chatPayloads).toHaveLength(1);
  });

  test("320px相当かつ文字拡大時も横方向へ崩れない", async ({ page }) => {
    await installDirectionScenario(page, { recommendationId: 507 });
    await page.setViewportSize({ width: 320, height: 700 });
    await page.goto("/concierge");
    await page.addStyleTag({ content: "html { font-size: 20px !important; }" });
    await page.getByRole("radio", { name: "駅名・住所から指定" }).click();

    const sizes = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
    expect(sizes.scrollWidth).toBeLessThanOrEqual(sizes.clientWidth);
    for (const radio of await page.getByRole("radio").all()) {
      expect((await radio.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(44);
    }
  });

  test("方位参考情報付きHero候補からキーボードで経路を開き、1回だけ送信する", async ({ page, context }) => {
    const captured = await installDirectionScenario(page, {
      recommendationId: 508,
      directionReference: matchedDirectionReference,
    });
    await context.route("https://www.google.com/maps/**", (route) => route.fulfill({ status: 200, body: "fixed map" }));
    await page.goto("/concierge");
    await fillAndSubmit(page);

    const heroLink = page.getByRole("link", { name: "神社の詳細を見る" });
    await expect(heroLink).toHaveAttribute("href", /direction_matched=1/);
    await expect(heroLink).toHaveAttribute("href", /direction_position=hero/);
    await heroLink.focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/shrines\/508.*direction_position=hero/);

    const routeLink = page.getByRole("link", { name: "Googleマップで経路案内" });
    await expect(routeLink).toHaveAttribute("href", /^https:\/\/www\.google\.com\/maps\/dir\//);
    await routeLink.focus();
    const popupPromise = page.waitForEvent("popup");
    await page.keyboard.press("Enter");
    const popup = await popupPromise;
    await popup.close();

    const events = captured.analyticsEvents.filter((event) => event.eventName === "direction_match_route_clicked");
    expect(events).toEqual([expect.objectContaining({ payload: expect.objectContaining({ matched: true, candidate_position: "hero" }) })]);
    expectPrivateDataAbsent(events);
    expect(JSON.stringify(events)).not.toMatch(/固定詳細神社|固定テスト所在地|google\.com\/maps/);
  });

  test("方位参考情報付きその他候補の経路操作をotherとして1回送信する", async ({ page, context }) => {
    const captured = await installDirectionScenario(page, {
      recommendationId: 508,
      directionReference: matchedDirectionReference,
      additionalRecommendation: { id: 509, directionReference: matchedDirectionReference },
    });
    await context.route("https://www.google.com/maps/**", (route) => route.fulfill({ status: 200, body: "fixed map" }));
    await page.goto("/concierge");
    await fillAndSubmit(page);

    await page.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }).click();
    const otherLink = page.getByRole("link", { name: "詳細だけ見る" });
    await expect(otherLink).toHaveAttribute("href", /direction_matched=1/);
    await expect(otherLink).toHaveAttribute("href", /direction_position=other/);
    expect(await otherLink.getAttribute("href")).not.toMatch(/固定レスポンス神社|テスト用所在地|google\.com|35\.681|139\.767/);
    await otherLink.click();
    await expect(page).toHaveURL(/\/shrines\/509.*direction_position=other/);

    const popupPromise = page.waitForEvent("popup");
    await page.getByRole("link", { name: "Googleマップで経路案内" }).click();
    const popup = await popupPromise;
    await popup.close();
    expect(captured.analyticsEvents.filter((event) => event.eventName === "direction_match_route_clicked")).toEqual([
      expect.objectContaining({ payload: expect.objectContaining({ matched: true, candidate_position: "other" }) }),
    ]);
  });

  test("方位参考情報のない候補の経路操作では方位イベントを送らない", async ({ page, context }) => {
    const captured = await installDirectionScenario(page, { recommendationId: 510 });
    await context.route("https://www.google.com/maps/**", (route) => route.fulfill({ status: 200, body: "fixed map" }));
    await page.goto("/concierge");
    await fillAndSubmit(page);

    const detailLink = page.getByRole("link", { name: "神社の詳細を見る" });
    const href = await detailLink.getAttribute("href");
    expect(href).not.toContain("direction_matched");
    expect(href).not.toContain("direction_position");
    await detailLink.click();
    const popupPromise = page.waitForEvent("popup");
    await page.getByRole("link", { name: "Googleマップで経路案内" }).click();
    const popup = await popupPromise;
    await popup.close();
    expect(captured.analyticsEvents.filter((event) => event.eventName === "direction_match_route_clicked")).toHaveLength(0);
  });
});
