import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LegalFooter } from "../LegalFooter";
import { CONTACT_MAILTO_HREF } from "@/lib/contact";

// HomeContactFooter と同じ、Mother Ship承認済みの契約値。
// LegalFooter が別のアドレスを持ち始めていないことをここでも固定する。
const APPROVED_HREF =
  "mailto:j33db05@gmail.com?subject=KAMI%20MUSUBI%20%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B";

describe("LegalFooter", () => {
  it("利用規約とプライバシーポリシーへのリンクを持つ", () => {
    render(<LegalFooter />);

    expect(screen.getByRole("link", { name: "利用規約" })).toHaveAttribute("href", "/terms");
    expect(screen.getByRole("link", { name: "プライバシーポリシー" })).toHaveAttribute(
      "href",
      "/privacy",
    );
  });

  it("お問い合わせの承認済みmailto契約を共有する", () => {
    render(<LegalFooter />);

    const href = screen.getByRole("link", { name: "お問い合わせ" }).getAttribute("href");
    expect(href).toBe(APPROVED_HREF);
    expect(CONTACT_MAILTO_HREF).toBe(APPROVED_HREF);
  });

  it("スティッキーにせず、CTAより弱い表示に留める", () => {
    const { container } = render(<LegalFooter />);
    const footer = container.querySelector("footer");

    expect(footer).not.toBeNull();
    expect(footer?.className ?? "").not.toContain("sticky");
    expect(footer?.className ?? "").not.toContain("fixed");
    // 面を持たせない（背景色を敷かない）
    expect(footer?.className ?? "").not.toContain("bg-");
  });

  it("375px幅でも横スクロールを生む固定幅を持たない", () => {
    const { container } = render(<LegalFooter />);

    // jsdom はレイアウトを計算しないため実測はできない。
    // 代わりに「横あふれの原因になる指定が無いこと」を静的に固定する。
    for (const el of Array.from(container.querySelectorAll("*"))) {
      const className = el.getAttribute("class") ?? "";
      expect(className).not.toMatch(/(^|\s)w-\[\d{3,}px\]/);
      expect(className).not.toMatch(/(^|\s)min-w-\[\d{3,}px\]/);
      expect(el.getAttribute("style") ?? "").not.toContain("width");
    }
    // 折り返して縦に積めること
    expect(container.querySelector("nav")?.className ?? "").toContain("flex-wrap");
  });
});
