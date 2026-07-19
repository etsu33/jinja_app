import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineCardCompact from "../ShrineCardCompact";

describe("ShrineCardCompact", () => {
  it("shows address when address is present", () => {
    render(
      <ShrineCardCompact
        name="検証神社"
        href="/shrines/1?ctx=concierge"
        address="東京都千代田区1-1-1"
        distanceM={500}
      />,
    );

    expect(screen.getByText("東京都千代田区1-1-1")).toBeInTheDocument();
    expect(screen.queryByText("500m")).not.toBeInTheDocument();
  });

  it("falls back to distance when address is missing", () => {
    render(<ShrineCardCompact name="検証神社" href="/shrines/1?ctx=concierge" address={null} distanceM={500} />);

    expect(screen.getByText("500m")).toBeInTheDocument();
  });

  it("shows no supplementary line when both address and distance are missing", () => {
    render(<ShrineCardCompact name="検証神社" address={null} distanceM={null} />);

    expect(screen.queryByText(/m$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/km$/)).not.toBeInTheDocument();
  });

  it("renders primaryReason as the single reason block, but not summary or tags", () => {
    render(
      <ShrineCardCompact
        name="検証神社"
        href="/shrines/1?ctx=concierge"
        summary="長いMeaning文のサマリー"
        primaryReason="短い理由"
        tags={["mental", "rest"]}
      />,
    );

    expect(screen.getByText("短い理由")).toBeInTheDocument();
    expect(screen.queryByText("長いMeaning文のサマリー")).not.toBeInTheDocument();
    expect(screen.queryByText("mental")).not.toBeInTheDocument();
  });

  it("does not render primaryReason when it is null", () => {
    const { container } = render(
      <ShrineCardCompact name="検証神社" href="/shrines/1?ctx=concierge" primaryReason={null} />,
    );

    expect(container.querySelectorAll("p")).toHaveLength(0);
  });
});
