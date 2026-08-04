// apps/mobile/lib/__tests__/shrineKnowledgeFact.test.ts
import { describe, expect, it } from "vitest";

import {
  buildShrineFactViewModel,
  hasVisibleKnowledgeFact,
  isDisputedDisplayState,
  resolveFactDisplayState,
  type ShrineDeity,
  type ShrineHistory,
  type ShrineKnowledgeSource,
} from "../shrineKnowledgeFact";

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

describe("resolveFactDisplayState", () => {
  it.each(["source_confirmed", "reviewed"])("verification_status=%s はfullになる", (status) => {
    expect(resolveFactDisplayState(status)).toBe("full");
  });

  it("verification_status=disputed はdisputedになる", () => {
    expect(resolveFactDisplayState("disputed")).toBe("disputed");
  });

  it("未知のverification_statusはdisputedへ昇格せずfullとして扱う（fail-safe）", () => {
    expect(resolveFactDisplayState("unknown_future_status")).toBe("full");
  });
});

describe("buildShrineFactViewModel", () => {
  it("deitiesが保持される", () => {
    const vm = buildShrineFactViewModel({ deities: [makeDeity()], histories: [] });
    expect(vm.deities).toHaveLength(1);
  });

  it("historiesが保持される", () => {
    const vm = buildShrineFactViewModel({ deities: [], histories: [makeHistory()] });
    expect(vm.histories).toHaveLength(1);
  });

  it("deities/historiesが未指定でも空配列を返す", () => {
    const vm = buildShrineFactViewModel({});
    expect(vm.deities).toEqual([]);
    expect(vm.histories).toEqual([]);
  });

  it("sort_orderが保持され、昇順に並び替えられる", () => {
    const vm = buildShrineFactViewModel({
      deities: [
        makeDeity({ id: 2, display_name: "後の祭神", sort_order: 1 }),
        makeDeity({ id: 1, display_name: "先の祭神", sort_order: 0 }),
      ],
    });
    expect(vm.deities.map((d) => d.sortOrder)).toEqual([0, 1]);
    expect(vm.deities.map((d) => d.displayName)).toEqual(["先の祭神", "後の祭神"]);
  });

  it("Fact本文（display_name/title/content/period_text/history_type）が改変されない", () => {
    const vm = buildShrineFactViewModel({
      deities: [makeDeity({ display_name: "確定祭神" })],
      histories: [
        makeHistory({
          history_type: "official_origin",
          title: "確定由緒",
          content: "公式由緒に基づく内容そのもの。",
          period_text: "大正9年（1920）",
        }),
      ],
    });

    expect(vm.deities[0].displayName).toBe("確定祭神");
    expect(vm.histories[0].historyType).toBe("official_origin");
    expect(vm.histories[0].title).toBe("確定由緒");
    expect(vm.histories[0].content).toBe("公式由緒に基づく内容そのもの。");
    expect(vm.histories[0].periodText).toBe("大正9年（1920）");
  });

  it("confidenceが保持される", () => {
    const vm = buildShrineFactViewModel({
      deities: [makeDeity({ confidence: "medium" })],
      histories: [makeHistory({ confidence: "low" })],
    });
    expect(vm.deities[0].confidence).toBe("medium");
    expect(vm.histories[0].confidence).toBe("low");
  });

  it("sourcesが保持される（Source UIは今回作らないが内部型としては保持する）", () => {
    const source = makeSource({ id: 99, title: "史料X" });
    const vm = buildShrineFactViewModel({
      deities: [makeDeity({ sources: [source] })],
      histories: [makeHistory({ sources: [source] })],
    });
    expect(vm.deities[0].sources).toEqual([source]);
    expect(vm.histories[0].sources).toEqual([source]);
  });

  it("displayState変換: source_confirmed/reviewed -> full, disputed -> disputed", () => {
    const vm = buildShrineFactViewModel({
      deities: [
        makeDeity({ id: 1, verification_status: "source_confirmed" }),
        makeDeity({ id: 2, verification_status: "disputed", sort_order: 1 }),
      ],
      histories: [
        makeHistory({ id: 1, verification_status: "reviewed" }),
        makeHistory({ id: 2, verification_status: "disputed", sort_order: 1 }),
      ],
    });
    expect(vm.deities[0].displayState).toBe("full");
    expect(vm.deities[1].displayState).toBe("disputed");
    expect(vm.histories[0].displayState).toBe("full");
    expect(vm.histories[1].displayState).toBe("disputed");
  });

  it("複数disputed Factが別要素のまま保持される（自動統合されない）", () => {
    const vm = buildShrineFactViewModel({
      histories: [
        makeHistory({
          id: 1,
          title: "説A",
          content: "説Aの内容",
          verification_status: "disputed",
          sort_order: 0,
        }),
        makeHistory({
          id: 2,
          title: "説B",
          content: "説Bの内容",
          verification_status: "disputed",
          sort_order: 1,
        }),
      ],
    });

    expect(vm.histories).toHaveLength(2);
    expect(vm.histories[0].title).toBe("説A");
    expect(vm.histories[0].content).toBe("説Aの内容");
    expect(vm.histories[1].title).toBe("説B");
    expect(vm.histories[1].content).toBe("説Bの内容");
    // 1要素へ統合されていないこと（titleが連結・要約されていない）
    expect(vm.histories[0].title).not.toContain("説B");
    expect(vm.histories[1].title).not.toContain("説A");
  });
});

describe("isDisputedDisplayState", () => {
  it("full -> disputed labelを表示しない(false)", () => {
    expect(isDisputedDisplayState("full")).toBe(false);
  });

  it("disputed -> disputed labelを表示する(true)", () => {
    expect(isDisputedDisplayState("disputed")).toBe(true);
  });
});

describe("hasVisibleKnowledgeFact", () => {
  it("Knowledge Factあり(deitiesのみ) -> section visible(true)", () => {
    const vm = buildShrineFactViewModel({ deities: [makeDeity()], histories: [] });
    expect(hasVisibleKnowledgeFact(vm)).toBe(true);
  });

  it("Knowledge Factあり(historiesのみ) -> section visible(true)", () => {
    const vm = buildShrineFactViewModel({ deities: [], histories: [makeHistory()] });
    expect(hasVisibleKnowledgeFact(vm)).toBe(true);
  });

  it("Knowledge Factなし(両方空) -> section visible(false)", () => {
    const vm = buildShrineFactViewModel({ deities: [], histories: [] });
    expect(hasVisibleKnowledgeFact(vm)).toBe(false);
  });
});
