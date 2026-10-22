import { chromium } from "/home/user/jinja_app/node_modules/.pnpm/node_modules/playwright/index.mjs";
import { detail } from "./fixture.mjs";
const OUT = process.argv[2];
const widths = (process.argv[3] || "375,390,393").split(",").map(Number);
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const results = [];
for (const width of widths) {
  const ctx = await browser.newContext({ viewport: { width, height: 852 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
    userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" });
  await ctx.addInitScript(() => { try { localStorage.setItem("auth:logged_in", "1"); } catch {} });
  const page = await ctx.newPage();
  const net = []; const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200)); });
  page.on("pageerror", (e) => consoleErrors.push("pageerror: " + String(e).slice(0, 200)));
  await page.route("**/api/**", async (route) => {
    const u = new URL(route.request().url()); const p = u.pathname; const m = route.request().method();
    const json = (s, b) => route.fulfill({ status: s, contentType: "application/json", body: JSON.stringify(b) });
    if (p.startsWith("/_next")) return route.continue();
    net.push(`${m} ${p}`);
    if (p.startsWith("/api/users/me")) return json(200, { id: 1, username: "qa-tester", profile: { nickname: "QAテスター" } });
    if (p === "/api/concierge-threads/") return json(200, { results: [{ id: 500, title: "QA用テスト相談", message_count: 2 }] });
    if (p === "/api/concierge-threads/500/") return json(200, detail);
    if (p.startsWith("/api/favorites")) return m === "POST" ? json(201, { id: 77, shrine: 9001, shrine_id: 9001 }) : json(200, []);
    if (p.startsWith("/api/billing")) return json(200, { plan: "free", is_active: false });
    if (p.startsWith("/api/goriyaku-tags") || p.includes("tags")) return json(200, [{ id: 1, name: "仕事運" }, { id: 2, name: "縁結び" }]);
    return json(200, {});
  });
  await page.goto("http://localhost:3100/concierge?tid=500", { waitUntil: "networkidle", timeout: 180000 });
  await page.getByTestId("concierge-thread-save-feedback").waitFor({ state: "attached", timeout: 60000 });
  await page.waitForTimeout(800);

  const measure = () => page.evaluate(() => {
    const vw = window.innerWidth;
    const vis = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none"; };
    const path = (el) => { const parts = []; let e = el; for (let k = 0; e && k < 4; k++, e = e.parentElement) { parts.unshift(e.tagName.toLowerCase() + (e.dataset?.testid ? `[${e.dataset.testid}]` : "")); } return parts.join(">"); };
    const overflowing = []; const clipped = []; const fixed = [];
    for (const el of document.querySelectorAll("body *")) {
      if (!vis(el)) continue;
      const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
      if (r.right > vw + 0.5 || r.left < -0.5) overflowing.push({ el: path(el), left: Math.round(r.left), right: Math.round(r.right), text: (el.textContent || "").trim().slice(0, 40) });
      if ((cs.overflowX === "hidden" || cs.overflow === "hidden" || cs.textOverflow === "ellipsis") && el.scrollWidth > el.clientWidth + 1 && el.children.length === 0)
        clipped.push({ el: path(el), sw: el.scrollWidth, cw: el.clientWidth, text: (el.textContent || "").trim().slice(0, 40) });
      if (cs.position === "fixed" || cs.position === "sticky") fixed.push({ el: path(el), pos: cs.position, top: Math.round(r.top), h: Math.round(r.height), w: Math.round(r.width) });
    }
    const targets = [...document.querySelectorAll("a[href], button, [role=button], input, select, textarea")].filter(vis).map((el) => {
      const r = el.getBoundingClientRect();
      return { tag: el.tagName.toLowerCase(), text: (el.textContent || el.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").slice(0, 36), href: el.getAttribute("href"), w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.top + window.scrollY), disabled: el.disabled === true };
    });
    const headings = [...document.querySelectorAll("h1,h2,h3")].filter(vis).map((h) => `${h.tagName}:${h.textContent.trim().slice(0, 50)}`);
    const testids = [...new Set([...document.querySelectorAll("[data-testid]")].map((e) => e.dataset.testid))];
    const htmlOverflowX = getComputedStyle(document.documentElement).overflowX, bodyOverflowX = getComputedStyle(document.body).overflowX;
    return { innerWidth: vw, docScrollWidth: document.documentElement.scrollWidth, bodyScrollWidth: document.body.scrollWidth, pageHeight: document.documentElement.scrollHeight,
      htmlOverflowX, bodyOverflowX, overflowing: overflowing.slice(0, 30), overflowingCount: overflowing.length, clipped, fixed, targets, headings, testids };
  });
  const metrics = await measure();

  // screenshots: top / middle / bottom + full
  const H = metrics.pageHeight;
  for (const [label, y] of [["top", 0], ["middle", Math.max(0, H / 2 - 426)], ["bottom", H]]) {
    await page.evaluate((yy) => window.scrollTo(0, yy), y); await page.waitForTimeout(250);
    await page.screenshot({ path: `${OUT}/w${width}-${label}.png` });
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${OUT}/w${width}-full.png`, fullPage: true });

  // CTA actions
  const actions = {};
  const tryStep = async (name, fn) => { try { actions[name] = await fn(); } catch (e) { actions[name] = "ERROR: " + String(e).split("\n")[0].slice(0, 160); } };
  await tryStep("other_recs_toggle", async () => {
    const b = page.locator("button[aria-controls]").filter({ hasText: /ほかの神社/ });
    if (!(await b.count())) return "NOT_PRESENT";
    const label0 = (await b.textContent()).trim();
    const before = await page.locator("a[href*='/shrines/']").count();
    await b.click(); await page.waitForTimeout(500);
    const after = await page.locator("a[href*='/shrines/']").count();
    const expanded = await measure();
    await b.scrollIntoViewIfNeeded(); await page.screenshot({ path: `${OUT}/w${width}-expanded.png` });
    await page.screenshot({ path: `${OUT}/w${width}-expanded-full.png`, fullPage: true });
    const res = { label0, labelOpen: (await b.textContent()).trim(), ariaExpanded: await b.getAttribute("aria-expanded"), shrineLinksBefore: before, shrineLinksAfter: after,
      expandedScroll: { inner: expanded.innerWidth, doc: expanded.docScrollWidth, body: expanded.bodyScrollWidth, overflowingCount: expanded.overflowingCount, overflowing: expanded.overflowing.slice(0,8), clipped: expanded.clipped, smallTargets: expanded.targets.filter(t => t.h < 44 || t.w < 44) } };
    await b.click(); await page.waitForTimeout(300); res.labelClosed = (await b.textContent()).trim();
    return res;
  });
  await tryStep("links", async () => (await page.$$eval("a[href]", (as) => as.map((a) => ({ text: a.textContent.trim().replace(/\s+/g, " ").slice(0, 30), href: a.getAttribute("href") })))));
  await tryStep("add_condition", async () => {
    const b = page.getByRole("button", { name: "もう少し詳しく添える" });
    await b.click(); await page.waitForTimeout(700);
    const m = await measure();
    await page.screenshot({ path: `${OUT}/w${width}-filter-open.png` });
    const closeBtn = page.getByRole("button", { name: /閉じる/ }).first();
    const r = { doc: m.docScrollWidth, body: m.bodyScrollWidth, inner: m.innerWidth, overflowingCount: m.overflowingCount, overflowing: m.overflowing.slice(0,8), headingsAfter: m.headings, smallTargets: m.targets.filter(t => t.h < 44 || t.w < 44).slice(0, 30) };
    if (await closeBtn.count()) { await closeBtn.click(); await page.waitForTimeout(400); r.closed = true; }
    return r;
  });
  await tryStep("favorite", async () => {
    const f = page.locator("button[aria-pressed]").first(); const before = (await f.textContent()).trim();
    await f.click(); await page.waitForTimeout(800);
    return { before, after: (await f.textContent()).trim(), favPosts: net.filter((n) => n === "POST /api/favorites/").length };
  });
  await tryStep("consultation_save", async () => {
    const fb = page.getByTestId("concierge-thread-save-feedback"); const s = fb.locator("xpath=preceding-sibling::button[1]");
    const before = (await s.textContent()).trim(); const listBefore = net.filter((n) => n === "GET /api/concierge-threads/").length;
    await s.click(); await page.waitForTimeout(800);
    return { before, after: (await s.textContent()).trim(), feedback: (await fb.textContent()).trim(), historyHref: await fb.locator("a").getAttribute("href").catch(() => null),
      listCallsForSave: net.filter((n) => n === "GET /api/concierge-threads/").length - listBefore };
  });
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/w${width}-bottom-saved.png` });
  const afterInteraction = await page.evaluate(() => ({ docScrollWidth: document.documentElement.scrollWidth, bodyScrollWidth: document.body.scrollWidth, innerWidth: window.innerWidth }));
  await tryStep("history_link_nav", async () => {
    const a = page.getByTestId("concierge-thread-save-feedback").locator("a");
    if (!(await a.count())) return "NOT_PRESENT";
    await a.click(); await page.waitForURL(/\/mypage\/history\/500/, { timeout: 20000 }).catch(() => {});
    const url = page.url(); await page.goBack({ waitUntil: "networkidle" }).catch(() => {}); return url;
  });
  results.push({ width, metrics, afterInteraction, actions, consoleErrors: consoleErrors.slice(0, 15), net: [...new Set(net)] });
  await ctx.close();
}
console.log(JSON.stringify(results, null, 1));
await browser.close();
