import { describe, expect, it } from "vitest";

import { buildShrineFactSection } from "@/lib/shrine/buildShrineFactSection";
import { SHRINE_HISTORY_TYPE_LABELS } from "@/lib/shrine/shrineHistoryTypeLabels";
import type { ShrineHistory } from "@/lib/api/types";
import { prefectureOrigin, type UserOrigin } from "../../../../../../packages/shared/userOrigin";
import {
  resolveCompassCandidateMeaning,
  resolveCompassCandidateShrineFacts,
  resolveCompassRouteOrigin,
} from "../resolveCompassCandidatePresentation";

describe("resolveCompassCandidateMeaning", () => {
  it("fallbackだけがprimaryの場合はnull（Meaningを生成しない）", () => {
    expect(
      resolveCompassCandidateMeaning({
        shrine_id: 1,
        reason: "legacy",
        reason_facts: [{ type: "fallback", label: "fallback", label_ja: "近い候補", is_primary: true }],
      }),
    ).toBeNull();
  });
});

describe("resolveCompassRouteOrigin", () => {
  const precise = (source: UserOrigin["source"]): UserOrigin => ({
    latitude: 35.6812,
    longitude: 139.7671,
    source,
    accuracy: "precise",
  });

  it.each(["device", "station", "address"] as const)("precise な %s origin は座標を返す", (source) => {
    expect(resolveCompassRouteOrigin(precise(source))).toEqual({ lat: 35.6812, lng: 139.7671 });
  });

  it("都道府県の代表座標（approximate）は返さない", () => {
    const tokyo = prefectureOrigin("東京都");
    expect(tokyo?.accuracy).toBe("approximate");
    expect(resolveCompassRouteOrigin(tokyo)).toBeNull();
  });

  it("origin が無い / 座標が不正なら null", () => {
    expect(resolveCompassRouteOrigin(null)).toBeNull();
    expect(resolveCompassRouteOrigin(undefined)).toBeNull();
    expect(resolveCompassRouteOrigin({ ...precise("device"), latitude: Number.NaN })).toBeNull();
  });
});

describe("history_type label は Shrine Detail と共有の canonical 対応表", () => {
  function detailLabel(historyType: string): string {
    const history: ShrineHistory = {
      id: 1,
      history_type: historyType,
      title: "",
      content: "内容。",
      period_text: "",
      sort_order: 0,
      verification_status: "verified",
      sources: [],
    } as unknown as ShrineHistory;
    return buildShrineFactSection({ histories: [history] })?.histories[0].history_type_label ?? "";
  }

  function compassLabel(historyType: string): string | null {
    return (
      resolveCompassCandidateShrineFacts({
        shrine_id: 1,
        shrine_facts: { history: { history_type: historyType, content: "内容。" } },
      })?.history?.typeLabel ?? null
    );
  }

  it.each(Object.entries(SHRINE_HISTORY_TYPE_LABELS))("%s は Detail / Compass とも「%s」", (historyType, label) => {
    expect(detailLabel(historyType)).toBe(label);
    expect(compassLabel(historyType)).toBe(label);
  });

  it("未知の値: Detail は従来どおり値そのもの、Compass は内部type文字列を出さずラベルなし", () => {
    expect(detailLabel("future_type")).toBe("future_type");
    expect(compassLabel("future_type")).toBeNull();
  });
});
