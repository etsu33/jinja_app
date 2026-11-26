import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  isInMonthDirection,
  monthDirectionSummary,
  normalizeMonthDirection,
} from "../../../../../../packages/shared/monthDirection";
import { buildPayloadFromUnified } from "../buildPayloadFromUnified";
import { normalizeConciergeResponse } from "../hooks";
import { MonthDirectionMark, MonthDirectionSummary } from "../components/MonthDirection";

// ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」（2026-11-26 決定）:
// 結果の上に1回だけ「今月のあなたの方角」、方角に当たる神社にだけ印。合わない神社には何も書かない。

const monthDirection = {
  reference_directions: ["北東", "南"],
  calculation_method: "annual_monthly_kyusei_v1",
  target_date: "2026-11-26",
  note: "年盤と月盤による参考情報です。日盤は使用していません。",
};

const baseFilterState: any = {
  isOpen: false,
  birthdate: "",
  element4: null,
  goriyakuTags: [],
  suggestedTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
};

describe("packages/shared/monthDirection", () => {
  it("Backend の形だけを受け取り、知らない方位は落とす", () => {
    expect(normalizeMonthDirection(monthDirection)).toEqual(monthDirection);
    expect(
      normalizeMonthDirection({ ...monthDirection, reference_directions: ["北東", "上"] })?.reference_directions,
    ).toEqual(["北東"]);
    expect(normalizeMonthDirection({ ...monthDirection, reference_directions: [] })).toBeNull();
    expect(normalizeMonthDirection({ ...monthDirection, calculation_method: "daily" })).toBeNull();
    expect(normalizeMonthDirection(null)).toBeNull();
  });

  it("in_month_direction が true のときだけ印を付ける", () => {
    expect(isInMonthDirection({ in_month_direction: true })).toBe(true);
    expect(isInMonthDirection({ in_month_direction: false })).toBe(false);
    expect(isInMonthDirection({ in_month_direction: "true" })).toBe(false);
    expect(isInMonthDirection({})).toBe(false);
  });

  it("方角を一行にまとめる", () => {
    expect(monthDirectionSummary(monthDirection as any)).toBe("今月のあなたの方角：北東・南");
  });
});

describe("応答から画面の形へ", () => {
  it("normalizeConciergeResponse が month_direction を残す", () => {
    expect(normalizeConciergeResponse({ month_direction: monthDirection, data: {} }, []).month_direction).toEqual(
      monthDirection,
    );
    expect(normalizeConciergeResponse({ data: {} }, []).month_direction).toBeNull();
  });

  it("buildPayloadFromUnified が meta と各候補へ渡す", () => {
    const payload = buildPayloadFromUnified(
      {
        month_direction: monthDirection,
        data: {
          recommendations: [
            { shrine_id: 1, display_name: "北東の神社", reason: "R1", in_month_direction: true },
            { shrine_id: 2, display_name: "西の神社", reason: "R2" },
          ],
        },
        thread: { id: 1 },
      } as any,
      baseFilterState,
    );
    expect(payload?.meta?.monthDirection).toEqual(monthDirection);
    const items = (payload?.sections.find((s: any) => s.type === "recommendations") as any)?.items;
    expect(items.map((item: any) => item.inMonthDirection)).toEqual([true, false]);
  });

  it("month_direction が無ければ meta にも出さない", () => {
    const payload = buildPayloadFromUnified(
      { data: { recommendations: [{ shrine_id: 1, display_name: "S1", reason: "R1" }] }, thread: { id: 1 } } as any,
      baseFilterState,
    );
    expect(payload?.meta?.monthDirection).toBeNull();
  });
});

describe("表示", () => {
  it("結果の上に今月の方角とコンパスへの導線を出す", () => {
    render(<MonthDirectionSummary monthDirection={monthDirection as any} />);
    expect(screen.getByText("今月のあなたの方角：北東・南")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "方角で選びたいときはコンパスへ" })).toHaveAttribute("href", "/compass");
  });

  it("month_direction が無いときは何も出さない", () => {
    const { container } = render(<MonthDirectionSummary monthDirection={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("印は合う神社にだけ出し、合わない神社には何も書かない", () => {
    const { rerender, container } = render(<MonthDirectionMark inMonthDirection />);
    expect(screen.getByText("今月の方角")).toBeInTheDocument();

    rerender(<MonthDirectionMark inMonthDirection={false} />);
    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByText(/異なります|違います|凶/)).not.toBeInTheDocument();
  });
});
