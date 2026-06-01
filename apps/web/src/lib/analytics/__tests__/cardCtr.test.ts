import { describe, expect, it } from "vitest";

import { aggregateCardCtr } from "@/lib/analytics/cardCtr";

describe("aggregateCardCtr", () => {
  it("source / cardId / visibility / accessLevel ごとにCTRを集計する", () => {
    const rows = aggregateCardCtr([
      {
        event: "card_view",
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "visible",
        accessLevel: "premium",
      },
      {
        event: "card_view",
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "visible",
        accessLevel: "premium",
      },
      {
        event: "shrine_detail_premium_preview_click",
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "visible",
        accessLevel: "premium",
      },
    ]);

    expect(rows).toEqual([
      {
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "visible",
        accessLevel: "premium",
        historyTheme: null,
        cardVisibilityCount: 2,
        premiumClickCount: 1,
        ctr: 0.5,
      },
    ]);
  });

  it("card_partial_view と card_teaser_view を分母として集計する", () => {
    const rows = aggregateCardCtr([
      {
        event: "card_partial_view",
        source: "shrine_detail",
        cardId: "context_reason",
        accessLevel: "free",
      },
      {
        event: "shrine_detail_premium_preview_click",
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "partial",
        accessLevel: "free",
      },
      {
        event: "card_teaser_view",
        source: "concierge_result",
        cardId: "premium_preview",
        accessLevel: "anonymous",
      },
      {
        event: "premium_preview_click",
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "anonymous",
      },
    ]);

    expect(rows).toEqual([
      {
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "partial",
        accessLevel: "free",
        historyTheme: null,
        cardVisibilityCount: 1,
        premiumClickCount: 1,
        ctr: 1,
      },
      {
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "anonymous",
        historyTheme: null,
        cardVisibilityCount: 1,
        premiumClickCount: 1,
        ctr: 1,
      },
    ]);
  });

  it("必須payloadが欠けているeventは除外する", () => {
    const rows = aggregateCardCtr([
      {
        event: "card_view",
        source: "shrine_detail",
        cardId: "context_reason",
        visibility: "visible",
      },
      {
        event: "card_view",
        cardId: "context_reason",
        visibility: "visible",
        accessLevel: "premium",
      },
      {
        event: "card_view",
        source: "shrine_detail",
        visibility: "visible",
        accessLevel: "premium",
      },
    ]);

    expect(rows).toEqual([]);
  });

  it("分母が0のclickだけの行はCTRを0にする", () => {
    const rows = aggregateCardCtr([
      {
        event: "premium_preview_click",
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
      },
    ]);

    expect(rows).toEqual([
      {
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
        historyTheme: null,
        cardVisibilityCount: 0,
        premiumClickCount: 1,
        ctr: 0,
      },
    ]);
  });

  it("historyTheme ごとにCTRを分けて集計する", () => {
    const rows = aggregateCardCtr([
      {
        event: "card_view",
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
        historyTheme: "再出発",
      },
      {
        event: "premium_preview_click",
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
        historyTheme: "再出発",
      },
      {
        event: "card_view",
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
        historyTheme: "静寂",
      },
    ]);

    expect(rows).toEqual([
      {
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
        historyTheme: "再出発",
        cardVisibilityCount: 1,
        premiumClickCount: 1,
        ctr: 1,
      },
      {
        source: "concierge_result",
        cardId: "premium_preview",
        visibility: "teaser",
        accessLevel: "free",
        historyTheme: "静寂",
        cardVisibilityCount: 1,
        premiumClickCount: 0,
        ctr: 0,
      },
    ]);
  });
});
