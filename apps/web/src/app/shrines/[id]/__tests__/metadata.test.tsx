// apps/web/src/app/shrines/[id]/__tests__/metadata.test.tsx
// generateMetadata（Shrine Detail Dynamic Metadata v1）の契約テスト。
// Page本体の表示・error behaviorは対象外（page.test.tsxが担保する）。
import { beforeEach, describe, expect, it, vi } from "vitest";

const getShrineDetailServerMock = vi.fn();
vi.mock("@/lib/api/shrines.server", () => ({
  getShrineDetailServer: (...args: unknown[]) => getShrineDetailServerMock(...args),
}));

vi.mock("@/lib/api/concierge.server", () => ({
  getConciergeThreadServer: vi.fn(),
  getConciergeThreadsServer: vi.fn(),
}));

vi.mock("@/lib/api/billing.server", () => ({
  getBillingStatusServer: vi.fn().mockResolvedValue({ plan: "free", is_active: false }),
}));

vi.mock("@/lib/api/publicGoshuins.server", () => ({
  fetchPublicGoshuinsForShrineServer: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/lib/server/favorites.server", () => ({
  getShrineFavoriteInitialState: vi.fn().mockResolvedValue({ fav: false, favorite_id: null, guestMode: true }),
}));

vi.mock("@/lib/api/shrineMeaning.server", () => ({
  fetchShrineMeaningPayloadV2Server: vi.fn().mockResolvedValue(null),
}));

async function callGenerateMetadata(id: string) {
  const { generateMetadata } = await import("../page");
  return generateMetadata({ params: Promise.resolve({ id }) });
}

describe("/shrines/[id] generateMetadata", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Shrine取得成功時、titleは {name_jp} | KAMI MUSUBI になる", async () => {
    getShrineDetailServerMock.mockResolvedValue({
      id: 42,
      name_jp: "愛宕神社",
      address: "東京都港区愛宕1-5-3",
      goriyaku_tags: [],
      histories: [],
    });

    const metadata = await callGenerateMetadata("42");

    expect(metadata.title).toBe("愛宕神社 | KAMI MUSUBI");
    expect(getShrineDetailServerMock).toHaveBeenCalledWith(42);
  });

  it("full な official_origin の History Fact を description に使う", async () => {
    getShrineDetailServerMock.mockResolvedValue({
      id: 42,
      name_jp: "愛宕神社",
      address: "東京都港区愛宕1-5-3",
      goriyaku_tags: [],
      histories: [
        {
          id: 1,
          history_type: "official_origin",
          title: "由緒",
          content: "由緒の内容",
          period_text: "",
          event_date: null,
          sort_order: 0,
          verification_status: "source_confirmed",
          confidence: "high",
          sources: [],
        },
      ],
    });

    const metadata = await callGenerateMetadata("42");

    expect(metadata.description).toBe("由緒の内容");
  });

  it("不正IDではAPI requestを発生させずgeneric metadataを返す", async () => {
    const metadata = await callGenerateMetadata("abc");

    expect(metadata).toMatchObject({
      title: "神社詳細 | KAMI MUSUBI",
      description: "KAMI MUSUBIで神社の基本情報を確認できます。",
    });
    expect(getShrineDetailServerMock).not.toHaveBeenCalled();
  });

  it("Shrine Detail API失敗時はgeneric metadataを返す", async () => {
    getShrineDetailServerMock.mockRejectedValue(new Error("getShrineDetailServer failed: 500"));

    const metadata = await callGenerateMetadata("42");

    expect(metadata).toMatchObject({
      title: "神社詳細 | KAMI MUSUBI",
      description: "KAMI MUSUBIで神社の基本情報を確認できます。",
    });
  });
});
