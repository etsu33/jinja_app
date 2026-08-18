import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import CompassPurposeSelector from "../CompassPurposeSelector";

describe("CompassPurposeSelector", () => {
  it("目的を1つ選択するとonChangeへ渡す", () => {
    const onChange = vi.fn();
    render(<CompassPurposeSelector value={null} onChange={onChange} />);

    fireEvent.click(screen.getByRole("radio", { name: "転機・仕事" }));
    expect(onChange).toHaveBeenCalledWith("career");
  });

  it("選択中の目的はaria-checkedで示される", () => {
    render(<CompassPurposeSelector value="career" onChange={() => undefined} />);

    expect(screen.getByRole("radio", { name: "転機・仕事" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "恋愛" })).toHaveAttribute("aria-checked", "false");
  });

  it("15個の既存need_tagすべてが選択肢として表示される", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);
    expect(screen.getAllByRole("radio")).toHaveLength(15);
  });

  it("操作要素は44px相当の最小タップ領域を持つ", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);
    for (const radio of screen.getAllByRole("radio")) {
      expect(radio.className).toContain("min-h-11");
    }
  });
});
