import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PrivacyPolicyPage from "../privacy/page";
import TermsOfServicePage from "../terms/page";
import { LegalFooter } from "@/components/layout/LegalFooter";

/**
 * Legal導線の到達保証。
 *
 * /privacy ↔ /terms の相互到達は、ページごとに重複したリンクブロックを置くのではなく
 * RootLayout に一度だけ置く LegalFooter を正本とする。
 * ここでは「各ページ + 共通Footer」の組み合わせで両方へ到達できることを固定する。
 */
function renderWithLegalFooter(page: React.ReactNode) {
  return render(
    <>
      {page}
      <LegalFooter />
    </>,
  );
}

function hrefs(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll("a")).map((a) => a.getAttribute("href") ?? "");
}

describe("Legal navigation", () => {
  it("/privacy から /terms へ到達できる", () => {
    const { container } = renderWithLegalFooter(<PrivacyPolicyPage />);
    expect(hrefs(container)).toContain("/terms");
  });

  it("/terms から /privacy へ到達できる", () => {
    const { container } = renderWithLegalFooter(<TermsOfServicePage />);
    expect(hrefs(container)).toContain("/privacy");
  });

  it("Legalページ自身は巨大なリンクブロックを重複して持たない", () => {
    const privacy = render(<PrivacyPolicyPage />);
    const terms = render(<TermsOfServicePage />);

    // 本文中に /terms /privacy を再掲しない（正本は共通Footer）
    expect(hrefs(privacy.container)).toHaveLength(0);
    expect(hrefs(terms.container)).toHaveLength(0);
  });

  it("375px幅で横スクロールを生む固定幅をLegalページが持たない", () => {
    for (const page of [<PrivacyPolicyPage key="p" />, <TermsOfServicePage key="t" />]) {
      const { container } = render(page);
      for (const el of Array.from(container.querySelectorAll("*"))) {
        const className = el.getAttribute("class") ?? "";
        expect(className).not.toMatch(/(^|\s)w-\[\d{3,}px\]/);
        expect(className).not.toMatch(/(^|\s)min-w-\[\d{3,}px\]/);
        expect(el.getAttribute("style") ?? "").not.toContain("width");
      }
      // 横幅は max-w + 左右paddingで抑える
      expect(container.querySelector("article")?.className ?? "").toContain("max-w-2xl");
      expect(container.querySelector("article")?.className ?? "").toContain("px-4");
    }
  });
});
