import { describe, expect, it, vi } from "vitest";

import { LEGAL_LABELS, LEGAL_URLS, openLegalDocument } from "../legalLinks";

describe("規約類のリンク", () => {
  it("Web版の /terms と /privacy をhttpsで指す", () => {
    expect(LEGAL_URLS.terms).toBe("https://jinja-app-web.vercel.app/terms");
    expect(LEGAL_URLS.privacy).toBe("https://jinja-app-web.vercel.app/privacy");
  });

  it("2つの文書に表示名を持つ", () => {
    expect(LEGAL_LABELS).toEqual({ terms: "利用規約", privacy: "プライバシーポリシー" });
  });

  it.each(["terms", "privacy"] as const)("%s を openURL に渡す", (document) => {
    const openUrl = vi.fn().mockResolvedValue(true);

    openLegalDocument(document, openUrl);

    expect(openUrl).toHaveBeenCalledWith(LEGAL_URLS[document]);
  });

  it("ブラウザを開けない端末でも例外を外に出さない", async () => {
    const openUrl = vi.fn().mockRejectedValue(new Error("no browser"));

    expect(() => openLegalDocument("terms", openUrl)).not.toThrow();
    await Promise.resolve();
  });
});
