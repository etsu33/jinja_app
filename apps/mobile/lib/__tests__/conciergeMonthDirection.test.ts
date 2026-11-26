import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

// コンシェルジュの結果に添える「今月の方角」（ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」2026-11-26）。
const concierge = readFileSync(resolve(mobileRoot, "app/(tabs)/concierge/index.tsx"), "utf8");
const component = readFileSync(resolve(mobileRoot, "components/concierge/MonthDirection.tsx"), "utf8");

describe("コンシェルジュの今月の方角", () => {
  it("応答の month_direction を結果の上に1回だけ出す", () => {
    expect(concierge).toContain("monthDirection: normalizeMonthDirection(body.month_direction)");
    expect(concierge.match(/<MonthDirectionSummary /g)).toHaveLength(1);
  });

  it("印は in_month_direction が true の神社だけ。合わないときの文は持たない", () => {
    expect(concierge).toContain("inMonthDirection: isInMonthDirection(item)");
    expect(concierge).toContain("<MonthDirectionMark inMonthDirection={card.inMonthDirection} />");
    expect(component).toContain("if (!inMonthDirection) return null;");
    expect(component).not.toMatch(/異なります|違います|凶/);
  });

  it("結果の上の1行からコンパスへ進める", () => {
    expect(component).toContain('router.push("/compass")');
  });
});
