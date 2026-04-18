import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const signupFormMock = vi.fn(({ returnTo }: { returnTo?: string | null }) => {
  return <div data-testid="signup-form-props">{returnTo ?? "__NULL__"}</div>;
});

vi.mock("../../../signup/SignupForm", () => ({
  default: (props: { returnTo?: string | null }) => signupFormMock(props),
}));

describe("/auth/register page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returnTo を sanitize して SignupForm に渡す", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: "/shrines/1?ctx=concierge&tid=123",
      },
    });

    render(ui);

    expect(signupFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        returnTo: "/shrines/1?ctx=concierge&tid=123",
      }),
    );
    expect(screen.getByTestId("signup-form-props")).toHaveTextContent(
      "/shrines/1?ctx=concierge&tid=123",
    );
  });

  it("_rsc を除去して SignupForm に渡す", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: "/shrines/1?ctx=concierge&_rsc=abc123&tid=999",
      },
    });

    render(ui);

    expect(signupFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        returnTo: "/shrines/1?ctx=concierge&tid=999",
      }),
    );
    expect(screen.getByTestId("signup-form-props")).toHaveTextContent(
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

    expect(signupFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        returnTo: null,
      }),
    );
    expect(screen.getByTestId("signup-form-props")).toHaveTextContent("__NULL__");
  });

  it("配列の returnTo は先頭要素を使う", async () => {
    const { default: Page } = await import("../page");

    const ui = await Page({
      searchParams: {
        returnTo: ["/shrines/1?ctx=concierge", "/mypage?tab=favorites"],
      },
    });

    render(ui);

    expect(signupFormMock).toHaveBeenCalledWith(
      expect.objectContaining({
        returnTo: "/shrines/1?ctx=concierge",
      }),
    );
    expect(screen.getByTestId("signup-form-props")).toHaveTextContent(
      "/shrines/1?ctx=concierge",
    );
  });
});
