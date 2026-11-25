// apps/web/src/lib/shrine/__tests__/buildShrineFactSection.test.ts
import { describe, expect, it } from "vitest";

import { buildShrineFactSection, groupShrineHistoryFacts } from "../buildShrineFactSection";
import type { ShrineDeity, ShrineHistory, ShrineKnowledgeSource } from "@/lib/api/types";
import type { DetailFactHistoryItem } from "@/components/shrine/detail/types";

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

  // docs/audit/shrine-knowledge-grouping-implementation-readiness.md §9/§10 が指摘した gap:
  // 生APIには既に id/sources が存在するが、ViewModel（本関数）が落としていた。
  describe("Fact identity / provenance (PR-B)", () => {
    it("Historyのidが最終ViewModelまで到達する", () => {
      const section = buildShrineFactSection({
        histories: [makeHistory({ id: 42, title: "由緒A" })],
      });
      expect(section?.histories[0].id).toBe(42);
    });

    it("Historyのsourcesが最終ViewModelまで到達する", () => {
      const source = makeSource({ id: 7, title: "史料X", url: "https://example.com/x" });
      const section = buildShrineFactSection({
        histories: [makeHistory({ sources: [source] })],
      });
      expect(section?.histories[0].sources).toEqual([source]);
    });

    it("sourcesが無いHistoryは空配列になる（クラッシュしない）", () => {
      const section = buildShrineFactSection({
        histories: [makeHistory({ sources: [] })],
      });
      expect(section?.histories[0].sources).toEqual([]);
    });
  });
});

describe("groupShrineHistoryFacts", () => {
  function toItem(overrides: Partial<DetailFactHistoryItem> = {}): DetailFactHistoryItem {
    return {
      id: 1,
      history_type: "founding",
      history_type_label: "創始",
      title: "由緒A",
      content: "内容A",
      period_text: "",
      sort_order: 0,
      displayState: "full",
      sources: [],
      ...overrides,
    };
  }

  it("同一history_typeの非disputed Factは1つのgroupにまとまる（identityは個別のまま）", () => {
    const factA = toItem({ id: 10, history_type: "historical_event", history_type_label: "歴史", title: "説A" });
    const factB = toItem({ id: 11, history_type: "historical_event", history_type_label: "歴史", title: "説B" });

    const { groups } = groupShrineHistoryFacts([factA, factB]);

    expect(groups).toHaveLength(1);
    expect(groups[0].historyType).toBe("historical_event");
    expect(groups[0].label).toBe("歴史");
    expect(groups[0].items).toEqual([factA, factB]);
    // 2つのFactは別々のidを保持したまま（1つへ合成されない）
    expect(groups[0].items.map((f) => f.id)).toEqual([10, 11]);
  });

  it("グルーピング後も各Factは自身のsourcesを個別に保持する（groupレベルへ共有・曖昧化しない）", () => {
    const sourceA = { id: 100, source_type: "shrine_official", title: "史料A", publisher: "", url: "", verification_status: "source_confirmed", confidence: "high" };
    const sourceB = { id: 101, source_type: "local_history", title: "史料B", publisher: "", url: "", verification_status: "source_confirmed", confidence: "high" };
    const factA = toItem({ id: 10, history_type: "tradition", history_type_label: "伝承", title: "説A", sources: [sourceA] });
    const factB = toItem({ id: 11, history_type: "tradition", history_type_label: "伝承", title: "説B", sources: [sourceB] });

    const { groups } = groupShrineHistoryFacts([factA, factB]);

    expect(groups[0].items[0].sources).toEqual([sourceA]);
    expect(groups[0].items[1].sources).toEqual([sourceB]);
  });

  it("history_typeが異なるFactは別groupになる（History/Traditionは区別される）", () => {
    const historyFact = toItem({ history_type: "historical_event", history_type_label: "歴史", title: "史実" });
    const traditionFact = toItem({ history_type: "tradition", history_type_label: "伝承", title: "伝承" });

    const { groups } = groupShrineHistoryFacts([historyFact, traditionFact]);

    expect(groups.map((g) => g.historyType)).toEqual(["historical_event", "tradition"]);
    expect(groups[0].items).toHaveLength(1);
    expect(groups[1].items).toHaveLength(1);
  });

  it("コピーテキストの類似度ではなく、history_typeの完全一致のみでグルーピングする", () => {
    // タイトル・本文がほぼ同一でもhistory_typeが異なれば別group（テキストヒューリスティック不使用の確認）
    const a = toItem({ history_type: "founding", history_type_label: "創始", title: "同じ出来事について", content: "同じ内容の説明文" });
    const b = toItem({ history_type: "historical_event", history_type_label: "歴史", title: "同じ出来事について", content: "同じ内容の説明文" });

    const { groups } = groupShrineHistoryFacts([a, b]);

    expect(groups).toHaveLength(2);
  });

  it("Fact本文（title/content）はグルーピングによって書き換え・連結されない", () => {
    const a = toItem({ history_type: "tradition", title: "説A", content: "説Aの内容" });
    const b = toItem({ history_type: "tradition", title: "説B", content: "説Bの内容" });

    const { groups } = groupShrineHistoryFacts([a, b]);

    expect(groups[0].items[0].title).toBe("説A");
    expect(groups[0].items[0].content).toBe("説Aの内容");
    expect(groups[0].items[1].title).toBe("説B");
    expect(groups[0].items[1].content).toBe("説Bの内容");
  });

  it("group内の順序は入力配列の順序（=既存のsort_order順）を維持する", () => {
    const first = toItem({ id: 1, history_type: "tradition", title: "先", sort_order: 0 });
    const second = toItem({ id: 2, history_type: "tradition", title: "後", sort_order: 1 });

    const { groups } = groupShrineHistoryFacts([first, second]);

    expect(groups[0].items.map((f) => f.title)).toEqual(["先", "後"]);
  });

  it("group表示順はHISTORY_TYPE_LABELSのcanonical宣言順（テキスト内容から推測しない）", () => {
    // 入力順はtradition→founding だが、canonical順（founding→...→tradition）で出力される
    const traditionFact = toItem({ history_type: "tradition", history_type_label: "伝承", title: "伝承" });
    const foundingFact = toItem({ history_type: "founding", history_type_label: "創始", title: "創始" });

    const { groups } = groupShrineHistoryFacts([traditionFact, foundingFact]);

    expect(groups.map((g) => g.historyType)).toEqual(["founding", "tradition"]);
  });

  it("disputedなFactはグルーピングされず、disputed配列へ個別に残る", () => {
    const disputedA = toItem({ id: 20, history_type: "tradition", title: "説A", displayState: "disputed" });
    const disputedB = toItem({ id: 21, history_type: "tradition", title: "説B", displayState: "disputed" });
    const fullFact = toItem({ id: 22, history_type: "tradition", title: "確定説", displayState: "full" });

    const { groups, disputed } = groupShrineHistoryFacts([disputedA, disputedB, fullFact]);

    expect(disputed).toEqual([disputedA, disputedB]);
    expect(groups).toHaveLength(1);
    expect(groups[0].items).toEqual([fullFact]);
  });

  it("未知のhistory_typeでもFactは消えず、その値自体のgroupへ入る", () => {
    const unknown = toItem({ history_type: "future_unlisted_type", history_type_label: "future_unlisted_type", title: "未知区分" });

    const { groups } = groupShrineHistoryFacts([unknown]);

    expect(groups).toHaveLength(1);
    expect(groups[0].historyType).toBe("future_unlisted_type");
    expect(groups[0].items).toEqual([unknown]);
  });

  it("1件だけのcanonical typeも自然に1つのgroupとして返る", () => {
    const single = toItem({ history_type: "editorial_summary", history_type_label: "要約", title: "要約A" });

    const { groups } = groupShrineHistoryFacts([single]);

    expect(groups).toHaveLength(1);
    expect(groups[0].items).toHaveLength(1);
  });

  it("空配列を渡すとgroups/disputedとも空になる", () => {
    expect(groupShrineHistoryFacts([])).toEqual({ groups: [], disputed: [] });
  });
});
