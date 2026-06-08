import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const loginFormMock = vi.fn(({ next }: { next?: string | null }) => {
  return <div data-testid="login-form-props">{next ?? "__NULL__"}</div>;
});

vi.mock("../../../login/LoginForm", () => ({
  default: (props: { next?: string | null }) => loginFormMock(props),
}));

describe("/auth/login page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returnTo を sanitize して LoginForm に渡す", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: "/shrines/1?ctx=concierge&tid=123",
      },
    });

    render(ui);

    expect(loginFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        next: "/shrines/1?ctx=concierge&tid=123",
      }),
    );
    expect(screen.getByTestId("login-form-props")).toHaveTextContent(
      "/shrines/1?ctx=concierge&tid=123",
    );
  });

  it("_rsc を除去して LoginForm に渡す", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: "/shrines/1?ctx=concierge&_rsc=abc123&tid=999",
      },
    });

    render(ui);

    expect(loginFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        next: "/shrines/1?ctx=concierge&tid=999",
      }),
    );
    expect(screen.getByTestId("login-form-props")).toHaveTextContent(
      "/shrines/1?ctx=concierge&tid=999",
    );
  });

  it("外部 URL は null に落とす", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: "https://evil.example.com/phish",
      },
    });

    render(ui);

    expect(loginFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        next: null,
      }),
    );
    expect(screen.getByTestId("login-form-props")).toHaveTextContent("__NULL__");
  });

  it("配列の returnTo は先頭要素を使う", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: ["/shrines/1?ctx=concierge", "/mypage?tab=favorites"],
      },
    });

    render(ui);

    expect(loginFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        next: "/shrines/1?ctx=concierge",
      }),
    );
    expect(screen.getByTestId("login-form-props")).toHaveTextContent(
      "/shrines/1?ctx=concierge",
    );
  });
});
