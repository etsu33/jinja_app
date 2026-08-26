// apps/web/src/components/shrine/detail/__tests__/ShrineFactSection.integration.test.tsx
//
// PR-D1: Shrine Detail APIレスポンス相当のfixture → buildShrineFactSection（ViewModel変換）
// → ShrineFactSection（UI描画）までを1本の統合テストとして固定する。
//
// 既存のunit/component testを置き換えるものではない。
// - buildShrineFactSection.test.ts: 変換ロジック単体の網羅（fail-safe/確認済みのfield等）
// - ShrineFactSection.test.tsx: UI単体（Design Token参照含む）
// これらの「間」、すなわちAPIレスポンス形状のfixtureからUI表示までが
// 実際に繋がっていることをこのファイルでのみ確認する。
//
// Recommendation / Evidence Gate / Backend Schema / Mobileはこのテストの対象外であり、変更しない。
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { buildShrineFactSection } from "@/lib/shrine/buildShrineFactSection";
import ShrineFactSection from "@/components/shrine/detail/ShrineFactSection";
import type { ShrineDeity, ShrineHistory, ShrineKnowledgeSource } from "@/lib/api/types";

// apps/web/src/lib/api/types.ts の型に合わせる（Backend Schemaを独自に再発明しない）。
function makeApiSource(overrides: Partial<ShrineKnowledgeSource> = {}): ShrineKnowledgeSource {
  return {
    id: 1,
    source_type: "shrine_official",
    title: "公式サイト",
    publisher: "",
    url: "",
    verification_status: "source_confirmed",
    confidence: "high",
    ...overrides,
  };
}

function makeApiDeity(overrides: Partial<ShrineDeity> = {}): ShrineDeity {
  return {
    id: 1,
    display_name: "確定祭神",
    canonical_name: "確定祭神",
    role: "enshrined",
    sort_order: 0,
    verification_status: "source_confirmed",
    confidence: "high",
    sources: [makeApiSource()],
    ...overrides,
  };
}

function makeApiHistory(overrides: Partial<ShrineHistory> = {}): ShrineHistory {
  return {
    id: 1,
    history_type: "official_origin",
    title: "由緒",
    content: "内容",
    period_text: "",
    event_date: null,
    sort_order: 0,
    verification_status: "source_confirmed",
    confidence: "high",
    sources: [makeApiSource()],
    ...overrides,
  };
}

describe("ShrineFactSection integration (API response相当 -> ViewModel -> UI)", () => {
  // Shrine Detail APIレスポンス相当のfixture。
  // Backend契約(docs/knowledge/shrine-knowledge-contract.md, PR-C4B1):
  //   source_confirmed/reviewed + ready Source -> full
  //   disputed + ready Source                 -> disputed
  const apiResponseFixture = {
    deities: [
      makeApiDeity({
        id: 10,
        display_name: "確定祭神",
        verification_status: "source_confirmed",
        sort_order: 0,
      }),
    ],
    histories: [
      makeApiHistory({
        id: 20,
        history_type: "official_origin",
        title: "確定由緒",
        content: "公式由緒に基づく確定した由緒内容。",
        period_text: "大正9年（1920）",
        sort_order: 0,
        verification_status: "source_confirmed",
        confidence: "high",
      }),
      makeApiHistory({
        id: 21,
        history_type: "tradition",
        title: "説A",
        content: "説Aの内容そのもの。",
        period_text: "",
        sort_order: 1,
        verification_status: "disputed",
        confidence: "high",
        sources: [makeApiSource({ id: 2, title: "史料A" })],
      }),
      makeApiHistory({
        id: 22,
        history_type: "tradition",
        title: "説B",
        content: "説Bの内容そのもの。",
        period_text: "",
        sort_order: 2,
        verification_status: "disputed",
        confidence: "medium",
        sources: [makeApiSource({ id: 3, title: "史料B" })],
      }),
    ],
  };

  it("Phase3: ViewModel変換 - displayStateがverification_statusから正しく導出される", () => {
    const section = buildShrineFactSection(apiResponseFixture);

    expect(section).not.toBeNull();
    expect(section?.deities[0].displayState).toBe("full");

    const [confirmed, disputedA, disputedB] = section?.histories ?? [];
    expect(confirmed.displayState).toBe("full");
    expect(disputedA.displayState).toBe("disputed");
    expect(disputedB.displayState).toBe("disputed");
  });

  it("Phase3: Fact本文（display_name/title/content/period_text/history_type/sort_order）が変更されない", () => {
    const section = buildShrineFactSection(apiResponseFixture);
    const [confirmed, disputedA, disputedB] = section?.histories ?? [];

    expect(section?.deities[0].display_name).toBe("確定祭神");
    expect(section?.deities[0].sort_order).toBe(0);

    expect(confirmed.title).toBe("確定由緒");
    expect(confirmed.content).toBe("公式由緒に基づく確定した由緒内容。");
    expect(confirmed.period_text).toBe("大正9年（1920）");
    expect(confirmed.history_type).toBe("official_origin");
    expect(confirmed.sort_order).toBe(0);

    expect(disputedA.title).toBe("説A");
    expect(disputedA.content).toBe("説Aの内容そのもの。");
    expect(disputedA.sort_order).toBe(1);

    expect(disputedB.title).toBe("説B");
    expect(disputedB.content).toBe("説Bの内容そのもの。");
    expect(disputedB.sort_order).toBe(2);
  });

  it("Phase3: 複数disputed Factが別々のViewModel itemとして保持される（自動統合されない）", () => {
    const section = buildShrineFactSection(apiResponseFixture);
    const disputedItems = section?.histories.filter((h) => h.displayState === "disputed") ?? [];

    expect(disputedItems).toHaveLength(2);
    expect(disputedItems.map((h) => h.title)).toEqual(["説A", "説B"]);
  });

  it("Phase4: full Factは状態ラベルなしでそのまま表示される（回帰なし）", () => {
    const section = buildShrineFactSection(apiResponseFixture);
    render(<ShrineFactSection section={section!} />);

    expect(screen.getByText("確定祭神")).toBeInTheDocument();
    expect(screen.getByText("確定由緒")).toBeInTheDocument();
    expect(screen.getByText("公式由緒に基づく確定した由緒内容。")).toBeInTheDocument();
    expect(screen.getByText("大正9年（1920）")).toBeInTheDocument();
  });

  it("Phase4: disputed Factは状態ラベル付きでFact本文そのままに表示される", () => {
    const section = buildShrineFactSection(apiResponseFixture);
    render(<ShrineFactSection section={section!} />);

    expect(screen.getByText("説A")).toBeInTheDocument();
    expect(screen.getByText("説Aの内容そのもの。")).toBeInTheDocument();
    expect(screen.getByText("説B")).toBeInTheDocument();
    expect(screen.getByText("説Bの内容そのもの。")).toBeInTheDocument();

    // 状態ラベルはdisputed 2件分、独立して2つ存在する（1つへ統合されない）
    expect(screen.getAllByText("異なる見解を含む情報")).toHaveLength(2);
  });

  it("Phase4: 自動統合・自動要約・自動グルーピング・AIによる正誤判定文が存在しない", () => {
    const section = buildShrineFactSection(apiResponseFixture);
    render(<ShrineFactSection section={section!} />);

    expect(screen.queryByText(/複数の説/)).not.toBeInTheDocument();
    expect(screen.queryByText(/複数説/)).not.toBeInTheDocument();
    expect(screen.queryByText(/誤り/)).not.toBeInTheDocument();
    expect(screen.queryByText(/間違い/)).not.toBeInTheDocument();
    expect(screen.queryByText(/矛盾しています/)).not.toBeInTheDocument();
    expect(screen.queryByText(/正しい/)).not.toBeInTheDocument();
    expect(screen.queryByText(/有力/)).not.toBeInTheDocument();
  });

  // 実データ(backend/temples/data/knowledge_seeds/batch_10_seed.json、大國魂神社)で確認された
  // 重複パターン: 異なるhistory_typeを持つ2つのShrineHistoryが、同一ShrineKnowledgeSource行を
  // M2Mで共有している。PR: 神社詳細の出典表示と経路CTAをDark UI向けに整理。
  it("Phase6: 同一Sourceを共有する複数Factは、出典欄で1回だけ表示される（実データの重複パターン再現）", () => {
    const sharedOfficialSource = makeApiSource({
      id: 500,
      title: "大國魂神社 公式サイト",
      url: "https://www.ookunitamajinja.jp/",
    });
    const fixture = {
      deities: [],
      histories: [
        makeApiHistory({
          id: 30,
          history_type: "tradition",
          title: "創建の伝承",
          content: "伝承内容",
          sort_order: 0,
          sources: [sharedOfficialSource],
        }),
        makeApiHistory({
          id: 31,
          history_type: "historical_event",
          title: "歴史的出来事",
          content: "歴史内容",
          sort_order: 1,
          // Backend側でも同一のShrineKnowledgeSource行を指す(id/url完全一致)
          sources: [sharedOfficialSource],
        }),
      ],
    };

    const section = buildShrineFactSection(fixture);
    render(<ShrineFactSection section={section!} />);

    // 両Factの本文はそれぞれ表示される(集約はSource表示のみ、Fact自体は失われない)
    expect(screen.getByText("創建の伝承")).toBeInTheDocument();
    expect(screen.getByText("歴史的出来事")).toBeInTheDocument();

    // 同一Sourceは出典欄で1回だけ
    expect(screen.getAllByRole("link", { name: "大國魂神社 公式サイト" })).toHaveLength(1);
  });

  it("Phase5: Knowledge未登録（deities/historiesとも空）のAPIレスポンス相当fixtureはセクション自体を生成しない", () => {
    const section = buildShrineFactSection({ deities: [], histories: [] });
    expect(section).toBeNull();
  });

  it("Phase5: full Factのみの既存ケースはdisputedラベルを一切表示しない", () => {
    const fullOnlyFixture = {
      deities: [makeApiDeity({ verification_status: "reviewed" })],
      histories: [makeApiHistory({ verification_status: "reviewed" })],
    };
    const section = buildShrineFactSection(fullOnlyFixture);
    render(<ShrineFactSection section={section!} />);

    expect(screen.queryByText("異なる見解を含む情報")).not.toBeInTheDocument();
  });
});
