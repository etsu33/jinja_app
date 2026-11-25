import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { buildConciergeHref, HomeHeroConsultationInput } from "../HomeHeroConsultationInput";
import { HOME_ORIGIN_HANDOFF_KEY } from "@/lib/concierge/homeOriginHandoff";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock("@/lib/analytics/directionEvents", () => ({ trackWebDirection: vi.fn() }));

beforeEach(() => {
  pushMock.mockClear();
  sessionStorage.clear();
});

describe("buildConciergeHref", () => {
  it("returns concierge URL with encoded theme when theme exists", () => {
    expect(buildConciergeHref("仕事の迷いを整理したい")).toBe(
      "/concierge?theme=%E4%BB%95%E4%BA%8B%E3%81%AE%E8%BF%B7%E3%81%84%E3%82%92%E6%95%B4%E7%90%86%E3%81%97%E3%81%9F%E3%81%84",
    );
  });

  it("returns concierge URL with theme and openFilter when both exist", () => {
    expect(buildConciergeHref("少し休みたい", { openFilter: true })).toBe(
      "/concierge?theme=%E5%B0%91%E3%81%97%E4%BC%91%E3%81%BF%E3%81%9F%E3%81%84&openFilter=1",
    );
  });

  it("returns concierge URL with only openFilter when theme is empty", () => {
    expect(buildConciergeHref("", { openFilter: true })).toBe("/concierge?openFilter=1");
  });

  it("returns concierge URL without query when theme is empty and openFilter is false", () => {
    expect(buildConciergeHref("")).toBe("/concierge");
  });
});

describe("HomeHeroConsultationInput", () => {
  it("chip選択後に相談を開始できる", () => {
    render(<HomeHeroConsultationInput />);

    fireEvent.click(screen.getByRole("button", { name: "疲れを整えたい" }));
    fireEvent.click(screen.getByRole("button", { name: "この相談ではじめる" }));

    expect(pushMock).toHaveBeenCalledWith(
      "/concierge?theme=%E6%9C%80%E8%BF%91%E5%B0%91%E3%81%97%E7%96%B2%E3%82%8C%E3%81%A6%E3%81%84%E3%81%A6%E3%80%81%E6%B0%97%E6%8C%81%E3%81%A1%E3%82%92%E8%90%BD%E3%81%A1%E7%9D%80%E3%81%91%E3%82%8B%E5%8F%82%E6%8B%9D%E3%81%8C%E3%81%97%E3%81%9F%E3%81%84%E3%81%A7%E3%81%99",
    );
  });

  it("themeありで条件を追加するとthemeとopenFilterを付けて遷移する", () => {
    render(<HomeHeroConsultationInput />);

    fireEvent.change(screen.getByLabelText("今の気持ちを少しだけ書く"), {
      target: { value: "仕事の流れを整えたい" },
    });
    fireEvent.click(screen.getByRole("button", { name: "＋ 条件を追加する" }));

    expect(pushMock).toHaveBeenCalledWith(
      "/concierge?theme=%E4%BB%95%E4%BA%8B%E3%81%AE%E6%B5%81%E3%82%8C%E3%82%92%E6%95%B4%E3%81%88%E3%81%9F%E3%81%84&openFilter=1",
    );
  });

  it("themeなしで条件を追加するとopenFilterだけを付けて遷移する", () => {
    render(<HomeHeroConsultationInput />);

    fireEvent.click(screen.getByRole("button", { name: "＋ 条件を追加する" }));

    expect(pushMock).toHaveBeenCalledWith("/concierge?openFilter=1");
  });
});

describe("HomeHeroConsultationInput - 出発地の1行", () => {
  it("相談の欄の下に、選ばれていないときの1行を出す", () => {
    render(<HomeHeroConsultationInput />);
    expect(screen.getByTestId("home-origin-row")).toHaveTextContent("出発地を選ぶ（任意）");
  });

  it("押すと下から出発地の選択肢（4つ）を出す", () => {
    render(<HomeHeroConsultationInput />);
    fireEvent.click(screen.getByTestId("home-origin-row"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    for (const label of ["現在地を使用", "駅名・住所から指定", "都道府県から指定", "方位情報を使用しない"]) {
      expect(screen.getByRole("radio", { name: label })).toBeInTheDocument();
    }
  });

  it("都道府県を選ぶと1行の表示が変わり、相談を始めると出発地を渡す（URL には載せない）", () => {
    render(<HomeHeroConsultationInput />);
    fireEvent.click(screen.getByTestId("home-origin-row"));
    fireEvent.click(screen.getByRole("radio", { name: "都道府県から指定" }));
    fireEvent.change(screen.getByRole("combobox", { name: "都道府県" }), { target: { value: "東京都" } });

    expect(screen.getByTestId("home-origin-row")).toHaveTextContent("東京都から");

    fireEvent.click(screen.getByRole("button", { name: "疲れを整えたい" }));
    fireEvent.click(screen.getByRole("button", { name: "この相談ではじめる" }));

    const href = pushMock.mock.calls[0][0] as string;
    expect(href).not.toMatch(/lat|lng|35\.|139\./);
    const stored = JSON.parse(sessionStorage.getItem(HOME_ORIGIN_HANDOFF_KEY) ?? "null");
    expect(stored.origin).toMatchObject({ source: "prefecture", displayName: "東京都" });
  });

  it("出発地を選ばずに相談を始めると、前の出発地を残さない", () => {
    sessionStorage.setItem(HOME_ORIGIN_HANDOFF_KEY, JSON.stringify({ origin: {}, savedAt: 0 }));
    render(<HomeHeroConsultationInput />);
    fireEvent.click(screen.getByRole("button", { name: "疲れを整えたい" }));
    fireEvent.click(screen.getByRole("button", { name: "この相談ではじめる" }));
    expect(sessionStorage.getItem(HOME_ORIGIN_HANDOFF_KEY)).toBeNull();
  });
});
