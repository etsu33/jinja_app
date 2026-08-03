// apps/web/src/lib/shrine/__tests__/buildShrineFactSection.test.ts
import { describe, expect, it } from "vitest";

import { buildShrineFactSection } from "../buildShrineFactSection";
import type { ShrineDeity, ShrineHistory, ShrineKnowledgeSource } from "@/lib/api/types";

function makeSource(overrides: Partial<ShrineKnowledgeSource> = {}): ShrineKnowledgeSource {
  return {
    id: 1,
    source_type: "shrine_official",
    title: "出典",
    publisher: "",
    url: "",
    verification_status: "source_confirmed",
    confidence: "high",
    ...overrides,
  };
}

function makeDeity(overrides: Partial<ShrineDeity> = {}): ShrineDeity {
  return {
    id: 1,
    display_name: "祭神A",
    canonical_name: "祭神A",
    role: "enshrined",
    sort_order: 0,
    verification_status: "source_confirmed",
    confidence: "high",
    sources: [makeSource()],
    ...overrides,
  };
}

function makeHistory(overrides: Partial<ShrineHistory> = {}): ShrineHistory {
  return {
    id: 1,
    history_type: "founding",
    title: "由緒A",
    content: "内容A",
    period_text: "",
    event_date: null,
    sort_order: 0,
    verification_status: "source_confirmed",
    confidence: "high",
    sources: [makeSource()],
    ...overrides,
  };
}

describe("buildShrineFactSection", () => {
  it("Knowledge未登録（deities/historiesとも空）はnullを返す", () => {
    expect(buildShrineFactSection({ deities: [], histories: [] })).toBeNull();
    expect(buildShrineFactSection({})).toBeNull();
  });

  describe("displayState変換", () => {
    it.each(["source_confirmed", "reviewed"])(
      "verification_status=%s のDeityはdisplayState=fullになる",
      (verificationStatus) => {
        const section = buildShrineFactSection({
          deities: [makeDeity({ verification_status: verificationStatus })],
        });
        expect(section?.deities[0].displayState).toBe("full");
      },
    );

    it("verification_status=disputed のDeityはdisplayState=disputedになる", () => {
      const section = buildShrineFactSection({
        deities: [makeDeity({ verification_status: "disputed" })],
      });
      expect(section?.deities[0].displayState).toBe("disputed");
    });

    it.each(["source_confirmed", "reviewed"])(
      "verification_status=%s のHistoryはdisplayState=fullになる",
      (verificationStatus) => {
        const section = buildShrineFactSection({
          histories: [makeHistory({ verification_status: verificationStatus })],
        });
        expect(section?.histories[0].displayState).toBe("full");
      },
    );

    it("verification_status=disputed のHistoryはdisplayState=disputedになる", () => {
      const section = buildShrineFactSection({
        histories: [makeHistory({ verification_status: "disputed" })],
      });
      expect(section?.histories[0].displayState).toBe("disputed");
    });

    it("想定外のverification_statusはdisputedへ昇格せずfullとして扱う（fail-safe）", () => {
      const section = buildShrineFactSection({
        deities: [makeDeity({ verification_status: "unknown_future_status" })],
        histories: [makeHistory({ verification_status: "unknown_future_status" })],
      });
      expect(section?.deities[0].displayState).toBe("full");
      expect(section?.histories[0].displayState).toBe("full");
    });

    it("confidenceの値に関わらずdisplayStateはverification_statusのみで決まる", () => {
      const section = buildShrineFactSection({
        deities: [
          makeDeity({ verification_status: "disputed", confidence: "high" }),
          makeDeity({
            id: 2,
            display_name: "祭神B",
            verification_status: "source_confirmed",
            confidence: "",
            sort_order: 1,
          }),
        ],
      });
      expect(section?.deities[0].displayState).toBe("disputed");
      expect(section?.deities[1].displayState).toBe("full");
    });

    it("history_typeの値に関わらずdisplayStateはverification_statusのみで決まる", () => {
      const section = buildShrineFactSection({
        histories: [
          makeHistory({ history_type: "tradition", verification_status: "disputed" }),
          makeHistory({
            id: 2,
            title: "由緒B",
            history_type: "official_origin",
            verification_status: "source_confirmed",
            sort_order: 1,
          }),
        ],
      });
      expect(section?.histories[0].displayState).toBe("disputed");
      expect(section?.histories[1].displayState).toBe("full");
    });
  });

  it("sort_orderを維持し、Fact本文（display_name/title/content等）を変更しない", () => {
    const section = buildShrineFactSection({
      deities: [
        makeDeity({ display_name: "後の祭神", sort_order: 1 }),
        makeDeity({ id: 2, display_name: "先の祭神", sort_order: 0 }),
      ],
      histories: [
        makeHistory({
          title: "後の由緒",
          content: "後の内容",
          period_text: "後の期間",
          sort_order: 1,
        }),
        makeHistory({
          id: 2,
          title: "先の由緒",
          content: "先の内容",
          period_text: "先の期間",
          sort_order: 0,
        }),
      ],
    });

    expect(section?.deities.map((d) => d.display_name)).toEqual(["先の祭神", "後の祭神"]);
    expect(section?.deities.map((d) => d.sort_order)).toEqual([0, 1]);
    expect(section?.histories.map((h) => h.title)).toEqual(["先の由緒", "後の由緒"]);
    expect(section?.histories[0].content).toBe("先の内容");
    expect(section?.histories[0].period_text).toBe("先の期間");
  });

  it("複数disputed Factを自動統合・自動グルーピングせず個別に保持する", () => {
    const section = buildShrineFactSection({
      histories: [
        makeHistory({ title: "説A", content: "説Aの内容", verification_status: "disputed", sort_order: 0 }),
        makeHistory({
          id: 2,
          title: "説B",
          content: "説Bの内容",
          verification_status: "disputed",
          sort_order: 1,
        }),
      ],
    });

    expect(section?.histories).toHaveLength(2);
    expect(section?.histories[0].title).toBe("説A");
    expect(section?.histories[0].content).toBe("説Aの内容");
    expect(section?.histories[1].title).toBe("説B");
    expect(section?.histories[1].content).toBe("説Bの内容");
  });
});
