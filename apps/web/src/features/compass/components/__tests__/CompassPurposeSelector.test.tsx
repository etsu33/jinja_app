import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import CompassPurposeSelector from "../CompassPurposeSelector";
import { COMPASS_PURPOSES, COMPASS_PURPOSES_ORDERED, COMPASS_PURPOSE_LABELS_JA } from "../../compassPurposes";

describe("CompassPurposeSelector", () => {
  it("目的を1つ選択するとonChangeへ渡す（値はslugのまま、表示順の影響を受けない）", () => {
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

  it("初期状態では上位6件のみ表示し、15件すべてを一度には出さない（375px初回ビューポート対策）", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);
    expect(screen.getAllByRole("radio")).toHaveLength(6);
    expect(screen.getByRole("button", { name: "その他の目的を見る（他9件）" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("「その他の目的を見る」で残り9件を含む15件すべてが選択可能になる", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "その他の目的を見る（他9件）" }));

    expect(screen.getAllByRole("radio")).toHaveLength(15);
    expect(screen.getByRole("button", { name: "目的を閉じる" })).toHaveAttribute("aria-expanded", "true");
    for (const purpose of COMPASS_PURPOSES) {
      expect(screen.getByRole("radio", { name: COMPASS_PURPOSE_LABELS_JA[purpose] })).toBeInTheDocument();
    }
  });

  it("展開後に折りたたむと再び6件表示に戻る", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "その他の目的を見る（他9件）" }));
    fireEvent.click(screen.getByRole("button", { name: "目的を閉じる" }));

    expect(screen.getAllByRole("radio")).toHaveLength(6);
  });

  it("「その他」側の目的を選んでもonChangeへ正しいslugが渡る", () => {
    const onChange = vi.fn();
    render(<CompassPurposeSelector value={null} onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "その他の目的を見る（他9件）" }));
    fireEvent.click(screen.getByRole("radio", { name: "移動・安全" }));

    expect(onChange).toHaveBeenCalledWith("travel_safe");
  });

  it("選択中の目的が「その他」側にある場合、展開状態を維持しトグルは表示しない（選択が隠れるのを防ぐ）", () => {
    render(<CompassPurposeSelector value="travel_safe" onChange={() => undefined} />);

    expect(screen.getAllByRole("radio")).toHaveLength(15);
    expect(screen.getByRole("radio", { name: "移動・安全" })).toHaveAttribute("aria-checked", "true");
    expect(screen.queryByRole("button", { name: /その他の目的を見る|目的を閉じる/ })).not.toBeInTheDocument();
  });

  it("表示順序が変わっても15個の既存need_tag全てが最終的に選択肢として存在する", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);
    fireEvent.click(screen.getByRole("button", { name: /その他の目的を見る/ }));
    expect(screen.getAllByRole("radio")).toHaveLength(COMPASS_PURPOSES_ORDERED.length);
  });

  it("操作要素は44px相当の最小タップ領域を持つ", () => {
    render(<CompassPurposeSelector value={null} onChange={() => undefined} />);
    for (const radio of screen.getAllByRole("radio")) {
      expect(radio.className).toContain("min-h-11");
    }
  });
});
