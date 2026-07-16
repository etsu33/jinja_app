import { describe, it, expect } from "vitest";
import { buildPayloadFromUnified } from "../buildPayloadFromUnified";

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

describe("buildPayloadFromUnified (payload/meta/astro)", () => {
  it("recs無しでも reply があれば payload を返す（filter/actions + meta）", () => {
    const u: any = {
      reply: "候補が見つかりませんでした",
      data: { recommendations: [] },
      thread: { id: 123 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    expect(p).not.toBeNull();
    expect(p?.sections?.some((s: any) => s.type === "filter")).toBe(true);
    expect(p?.sections?.some((s: any) => s.type === "actions")).toBe(true);
    expect(p?.meta?.reply).toBe("候補が見つかりませんでした");
    expect(p?.meta?.tid).toBe("123");
  });

  it("recs無しでも limitReached=true なら limit として payload を返す", () => {
    const u: any = {
      limitReached: true,
      remaining: 0,
      data: { recommendations: [] },
      thread_id: 9,
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    expect(p).not.toBeNull();
    expect(p?.meta?.limitReached).toBe(true);
    expect(p?.meta?.remaining).toBe(0);
    expect(p?.meta?.tid).toBe("9");
  });

  it("recsありなら recommendations セクションを返す（meta も揃う）", () => {
    const u: any = {
      meta: { reply: "どうぞ" },
      data: {
        recommendations: [
          { shrine_id: 10, place_id: "P10", display_name: "S1", reason: "R1" },
          { place_id: "P11", display_name: "S2", reason: "R2" },
        ],
      },
      thread: { id: 1 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    expect(p).not.toBeNull();

    const recSec = p?.sections?.find((s: any) => s.type === "recommendations");
    expect(recSec).toBeTruthy();
    expect(Array.isArray((recSec as any).items)).toBe(true);

    expect(p?.meta?.reply).toBe("どうぞ");
    expect(p?.meta?.tid).toBe("1");
  });

  it("astro があれば astro セクションを recommendations の前に挿入する", () => {
    const u: any = {
      data: {
        _signals: {
          astro: { label_ja: "火", sun_sign: "牡羊座", reason: "テスト" },
          mode: "B",
        },
        recommendations: [{ place_id: "P1", name: "A", reason: "R" }],
      },
      thread: { id: 77 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    expect(p).not.toBeNull();

    const types = (p?.sections ?? []).map((s: any) => s.type);
    const astroIdx = types.indexOf("astro");
    const recIdx = types.indexOf("recommendations");
    expect(astroIdx).toBeGreaterThanOrEqual(0);
    expect(recIdx).toBeGreaterThanOrEqual(0);
    expect(astroIdx).toBeLessThan(recIdx);

    expect(p?.meta?.mode).toBe("B");
  });

  it("meta の揺れ: reply / remaining / limitReached を u 側からも拾える", () => {
    const u: any = {
      remaining: 0,
      limitReached: true,
      reply: "上限です",
      data: { recommendations: [] },
      thread_id: 555,
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    expect(p).not.toBeNull();
    expect(p?.meta?.remaining).toBe(0);
    expect(p?.meta?.limitReached).toBe(true);
    expect(p?.meta?.reply).toBe("上限です");
    expect(p?.meta?.tid).toBe("555");
  });
});

it("reason_facts を recommendation item に通す", () => {
  const u: any = {
    data: {
      recommendations: [
        {
          shrine_id: 10,
          display_name: "S1",
          reason: "R1",
          reason_facts: {
            version: 1,
            primary_axis: "need",
            matched_need_tags: ["厄除け"],
            shrine_feature: "静かに歩ける",
          },
        },
      ],
    },
    thread: { id: 1 },
  };

  const p = buildPayloadFromUnified(u, baseFilterState);
  const recSec = p?.sections.find((s: any) => s.type === "recommendations") as any;
  expect(recSec.items[0].reasonFacts).toEqual(
    expect.objectContaining({
      primary_axis: "need",
      matched_need_tags: ["厄除け"],
    }),
  );
});

it("consultation_axis を meta と recommendation item に通す", () => {
  const u: any = {
    data: {
      consultation_axis: "money_growth",
      _need: { consultation_axis: "career_change" },
      _signals: {
        consultation_axis: "restart_mindset",
        result_state: { consultation_axis: "rest_healing" },
      },
      recommendations: [
        {
          shrine_id: 10,
          display_name: "S1",
          reason: "R1",
          consultation_axis: "independence",
        },
        {
          place_id: "P2",
          display_name: "S2",
          reason: "R2",
          consultationAxis: "nature_reset",
        },
      ],
    },
    thread: { id: 1 },
  };

  const p = buildPayloadFromUnified(u, baseFilterState);
  const recSec = p?.sections.find((s: any) => s.type === "recommendations") as any;

  expect(p?.meta?.consultationAxis).toBe("money_growth");
  expect(recSec.items[0].consultationAxis).toBe("independence");
  expect(recSec.items[1].consultationAxis).toBe("nature_reset");
});

it("consultation_axis を consultationAxis より優先する", () => {
  const u: any = {
    data: {
      consultation_axis: "snake_meta",
      consultationAxis: "camel_meta",
      recommendations: [
        {
          shrine_id: 10,
          display_name: "S1",
          reason: "R1",
          consultation_axis: "snake_item",
          consultationAxis: "camel_item",
        },
      ],
    },
    thread: { id: 1 },
  };

  const p = buildPayloadFromUnified(u, baseFilterState);
  const recSec = p?.sections.find((s: any) => s.type === "recommendations") as any;

  expect(p?.meta?.consultationAxis).toBe("snake_meta");
  expect(recSec.items[0].consultationAxis).toBe("snake_item");
});

it("place候補の詳細情報とresult_stateをpayloadへ通す", () => {
  const u: any = {
    data: {
      _signals: {
        mode: { mode: "need", flow: "A" },
        result_state: {
          matched_count: 0,
          fallback_mode: "nearby_unfiltered",
          fallback_reason_ja: "条件に一致する神社が見つかりませんでした（0件）",
          ui_disclaimer_ja: "代わりに近い神社を表示しています",
          requested_extra_condition: "静かな場所",
          consultation_axis: "rest_healing",
        },
      },
      recommendations: [
        {
          placeId: " P-PLACE-1 ",
          display_name: "未登録神社",
          display_address: "東京都",
          reason: "静かに整える候補です。",
          photo_url: "https://example.com/photo.jpg",
          breakdown: { score_total: 1 },
          breakdownDetail: { features: { visit_style: "quiet" } },
          reasonFacts: { primary_axis: "feature" },
          trustMetadata: { rank_class: "local" },
          historyTheme: "静寂",
          historyContext: "静けさの文脈",
        },
      ],
    },
    thread: { id: 88 },
  };

  const p = buildPayloadFromUnified(u, {
    ...baseFilterState,
    birthdate: "1984-05-15",
  });

  expect(p).not.toBeNull();
  expect(p?.meta?.resultState).toEqual(
    expect.objectContaining({
      matched_count: 0,
      fallback_mode: "nearby_unfiltered",
      requested_extra_condition: "静かな場所",
    }),
  );
  expect(p?.meta?.consultationAxis).toBe("rest_healing");

  const recSec = p?.sections.find((s: any) => s.type === "recommendations") as any;
  expect(recSec.items[0]).toEqual(
    expect.objectContaining({
      kind: "place",
      placeId: "P-PLACE-1",
      title: "未登録神社",
      address: "東京都",
      imageUrl: "https://example.com/photo.jpg",
      historyTheme: "静寂",
      historyContext: "静けさの文脈",
      consultationAxis: "rest_healing",
      detailLabel: "神社の詳細を見る",
    }),
  );
});


it("data._need.tags を meta.needTags へ通す（入力側need_tagsの経路）", () => {
  const u: any = {
    data: {
      _need: { tags: ["career", "mental", ""] },
      recommendations: [
        {
          shrine_id: 10,
          display_name: "S1",
          reason: "R1",
          breakdown: { matched_need_tags: ["money"] },
        },
      ],
    },
    thread: { id: 1 },
  };

  const p = buildPayloadFromUnified(u, baseFilterState);
  expect(p?.meta?.needTags).toEqual(["career", "mental"]);
});

it("data._need.tags が無ければ meta.needTags は空配列になる", () => {
  const u: any = {
    data: {
      recommendations: [
        {
          shrine_id: 10,
          display_name: "S1",
          reason: "R1",
          breakdown: { matched_need_tags: ["rest"] },
        },
      ],
    },
    thread: { id: 1 },
  };

  const p = buildPayloadFromUnified(u, baseFilterState);
  expect(p?.meta?.needTags).toEqual([]);
});

it("reason_facts を reasonFacts より優先する", () => {
  const u: any = {
    data: {
      recommendations: [
        {
          shrine_id: 10,
          display_name: "S1",
          reason: "R1",
          reason_facts: {
            primary_axis: "need",
            shrine_feature: "snake_case側",
          },
          reasonFacts: {
            primary_axis: "feature",
            shrine_feature: "camelCase側",
          },
        },
      ],
    },
    thread: { id: 1 },
  };

  const p = buildPayloadFromUnified(u, baseFilterState);
  const recSec = p?.sections.find((s: any) => s.type === "recommendations") as any;

  expect(recSec.items[0].reasonFacts).toEqual(
    expect.objectContaining({
      primary_axis: "need",
      shrine_feature: "snake_case側",
    }),
  );
});
