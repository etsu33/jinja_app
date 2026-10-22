import { BASE_URL, launchChromium } from "./qa-env.mjs";
import { detail } from "./fixture.mjs";
const browser = await launchChromium();
const out = [];
for (const width of [375, 390, 393]) {
  const ctx = await browser.newContext({ viewport: { width, height: 852 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  await ctx.addInitScript(() => { try { localStorage.setItem("auth:logged_in", "1"); } catch {} });
  const page = await ctx.newPage();
  await page.route("**/api/**", async (route) => {
    const p = new URL(route.request().url()).pathname;
    const json = (s, b) => route.fulfill({ status: s, contentType: "application/json", body: JSON.stringify(b) });
    if (p.startsWith("/api/users/me")) return json(200, { id: 1, username: "qa-tester", profile: {} });
    if (p === "/api/concierge-threads/") return json(200, { results: [{ id: 500 }] });
    if (p === "/api/concierge-threads/500/") return json(200, detail);
    if (p.startsWith("/api/billing")) return json(200, { plan: "free", is_active: false });
    if (p.includes("tags")) return json(200, [{ id: 1, name: "仕事運" }]);
    return json(200, {});
  });
  await page.goto(`${BASE_URL}/concierge?tid=500`, { waitUntil: "networkidle", timeout: 180000 });
  await page.getByTestId("concierge-thread-save-feedback").waitFor({ state: "attached" });
  const m = () => page.evaluate(() => {
    const scrollers = [...document.querySelectorAll("*")].filter((e) => { const cs = getComputedStyle(e); return (cs.overflowX === "auto" || cs.overflowX === "scroll") && e.scrollWidth > e.clientWidth + 1; })
      .map((e) => ({ tag: e.tagName.toLowerCase(), cls: String(e.getAttribute("class") || "").slice(0, 60), sw: e.scrollWidth, cw: e.clientWidth }));
    const main = document.querySelector("main"); const before = main.scrollLeft; main.scrollLeft = 200; const moved = main.scrollLeft; main.scrollLeft = before;
    return { main: { sw: main.scrollWidth, cw: main.clientWidth, scrollLeftAfterAttempt: moved }, horizontalScrollers: scrollers };
  });
  const r = { width, initial: await m() };
  await page.locator("button[aria-controls]").filter({ hasText: /ほかの神社/ }).click(); await page.waitForTimeout(400); r.expanded = await m();
  await page.getByRole("button", { name: "もう少し詳しく添える" }).click(); await page.waitForTimeout(600); r.filterOpen = await m();
  out.push(r); await ctx.close();
}
console.log(JSON.stringify(out, null, 1)); await browser.close();
