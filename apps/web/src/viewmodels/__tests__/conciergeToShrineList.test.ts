import { expect, it } from "vitest";
import { conciergeToShrineListItems } from "../conciergeToShrineList";

it("money × strong では三峯神社の短句を返す", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "三峯神社",
          shrine_id: 101,
          reason: "金運を上げたい",
          breakdown: {
            score_element: 0,
            score_need: 1,
            score_popular: 0,
            score_total: 1.0,
            weights: { element: 0, need: 1, popular: 0 },
            matched_need_tags: ["money"],
          },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.explanationPrimaryReason).toBe("金運や流れを動かす");
});

it("money × quiet では伊勢神宮（内宮）の短句を返す", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "伊勢神宮（内宮）",
          shrine_id: 102,
          reason: "金運を整えたい",
          breakdown: {
            score_element: 0,
            score_need: 1,
            score_popular: 0,
            score_total: 1.0,
            weights: { element: 0, need: 1, popular: 0 },
            matched_need_tags: ["money"],
          },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.explanationPrimaryReason).toBe("金運や巡りを整える");
});

it("study × tight では乃木神社の短句を返す", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "乃木神社",
          shrine_id: 103,
          reason: "集中したい",
          breakdown: {
            score_element: 0,
            score_need: 1,
            score_popular: 0,
            score_total: 1.0,
            weights: { element: 0, need: 1, popular: 0 },
            matched_need_tags: ["study"],
          },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.explanationPrimaryReason).toBe("集中や目標を定める");
});

it("primary が取れないときは fallbackText を返す", () => {
  const resp = {
    ok: true,
    data: {
      _need: { tags: ["protection"] },
      recommendations: [
        {
          name: "神社Z",
          shrine_id: 104,
          reason: "厄除けを願う参拝に",
          breakdown: {
            score_element: 0,
            score_need: 0,
            score_popular: 0,
            score_total: 0.5,
            weights: { element: 0, need: 1, popular: 0 },
            matched_need_tags: [],
          },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.explanationPrimaryReason).toBe("厄除けを願う参拝に");
});

it("resp.ok=false のときは空配列を返す", () => {
  const items = conciergeToShrineListItems({ ok: false } as any);
  expect(items).toEqual([]);
});

it("top-level thread_id を tid に入れる", () => {
  const resp = {
    ok: true,
    thread_id: "thread-top",
    data: {
      recommendations: [
        {
          name: "神社A",
          shrine_id: 201,
          reason: "前に進みたい",
          breakdown: { matched_need_tags: ["courage"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].tid).toBe("thread-top");
});

it("data.thread_id を tid に入れる", () => {
  const resp = {
    ok: true,
    data: {
      thread_id: "thread-data",
      recommendations: [
        {
          name: "神社B",
          shrine_id: 202,
          reason: "休みたい",
          breakdown: { matched_need_tags: ["rest"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].tid).toBe("thread-data");
});

it("display_name を title に優先し、address を表示する", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "正式名",
          display_name: "表示名",
          shrine_id: 203,
          address: "東京都千代田区1-1",
          reason: "仕事を整えたい",
          breakdown: { matched_need_tags: ["career"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.title).toBe("表示名");
  expect(items[0].cardProps.address).toBe("東京都千代田区1-1");
});

it("address が無いときは location を使う", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "神社C",
          shrine_id: 204,
          location: "渋谷エリア",
          reason: "恋愛を進めたい",
          breakdown: { matched_need_tags: ["love"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.address).toBe("渋谷エリア");
});

it("primary_reason.label があるとそれを優先して短句を作る", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "三峯神社",
          shrine_id: 205,
          reason: "別の理由文",
          _explanation_payload: {
            primary_reason: { label: "courage" },
            original_reason: "元の理由文",
          },
          breakdown: { matched_need_tags: ["money"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.explanationPrimaryReason).toBe("止まった流れを動かす");
});

it("explanation.summary があれば explanationSummary と rawReason に使う", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "神社D",
          shrine_id: 206,
          explanation: {
            summary: "気持ちを整えたい時に向いています",
          },
          breakdown: { matched_need_tags: ["mental"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.explanationSummary).toBe("気持ちを整えたい時に向いています");
  expect(items[0].cardProps.explanationPrimaryReason).toBe("不安や気持ちを整える");
});

it("action_suggestion_v4_preview を actionSuggestionV4Preview より優先する", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "神社F",
          shrine_id: 208,
          reason: "行動を決めたい",
          breakdown: { matched_need_tags: ["courage"] },
          action_suggestion_v4_preview: {
            primary_action: {
              label: "snake_case側の行動",
              description: "snake_case側の説明",
              action_type: "detail_open",
              confidence: 0.82,
            },
            secondary_action: {
              label: "保存する",
              description: "あとで見返します。",
              action_type: "save",
              confidence: 0.74,
            },
            reflection_prompt: {
              question: "何を整理したいですか？",
              prompt_type: "before_visit",
              source_seed: "fallback",
            },
            action_source: {
              source: "fallback",
              reason: "安全な初期提案",
            },
            preview: true,
            version: "v4",
            source_keys: ["recommendation_reason_v4"],
          },
          actionSuggestionV4Preview: {
            primaryAction: {
              label: "camelCase側の行動",
              description: "camelCase側の説明",
              actionType: "save",
              confidence: 0.5,
            },
            secondaryAction: {
              label: "別の行動",
              description: "別の説明",
              actionType: "route_open",
              confidence: 0.4,
            },
            reflectionPrompt: {
              question: "別の問い",
              promptType: "after_visit",
              sourceSeed: "legacy",
            },
            actionSource: {
              source: "legacy",
              reason: "旧形式",
            },
            preview: true,
            version: "legacy",
            sourceKeys: ["legacy"],
          },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  const preview = items[0].actionSuggestionV4Preview;

  expect(preview?.preview).toBe(true);
  expect(preview?.version).toBe("v4");
  expect(preview?.primaryAction.label).toBe("snake_case側の行動");
  expect(preview?.primaryAction.description).toBe("snake_case側の説明");
  expect(preview?.primaryAction.actionType).toBe("detail_open");
  expect(preview?.sourceKeys).toEqual(["recommendation_reason_v4"]);
});

it("matched_need_tags が空でも badgesOverride は matched_need_tags のみを使い、_need.tags へフォールバックしない", () => {
  const resp = {
    ok: true,
    data: {
      _need: { tags: ["money", "rest"] },
      recommendations: [
        {
          name: "神社E",
          shrine_id: 207,
          reason: "整えたい",
          breakdown: { matched_need_tags: [] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  // 一致チップ(badgesOverride)は一致結果(matched_need_tags)のみを使う。空なら空のまま。
  expect(items[0].cardProps.badgesOverride).toEqual([]);
  // Hero・相談要約は入力側need_tagsを優先するため、matched_need_tagsが空でも生成できる。
  expect(items[0].deepReason?.shrineMeaning).toContain("金運や巡りを整えたい");
});

it("入力タグ優先: 入力側need_tagsとmatched_need_tagsが異なる場合、Hero・相談要約は入力側、一致チップ・一致理由はmatched側を使う", () => {
  const resp = {
    ok: true,
    data: {
      _need: { tags: ["career", "mental"] },
      recommendations: [
        {
          name: "神社X",
          shrine_id: 301,
          reason: "元の理由",
          breakdown: { matched_need_tags: ["money"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);

  // Hero・相談要約(deepReason.shrineMeaning)は入力側タグ(career)の文脈を使う
  expect(items[0].deepReason?.shrineMeaning).toContain("仕事や転機を見直したい");
  // 一致チップ(badgesOverride)はmatched_need_tags(money)のみを使う
  expect(items[0].cardProps.badgesOverride).toEqual(["金運"]);
  // 一致理由(explanationPrimaryReason)もmatched_need_tags(money)を使う
  expect(items[0].cardProps.explanationPrimaryReason).toBe("金運や流れを立て直す");
});

it("fallback: 入力側need_tagsが無い旧Payloadでは、matched_need_tagsでHero・相談要約を生成できる", () => {
  const resp = {
    ok: true,
    data: {
      _need: { tags: [] },
      recommendations: [
        {
          name: "神社Y",
          shrine_id: 302,
          reason: "元の理由",
          breakdown: { matched_need_tags: ["rest"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);

  expect(items[0].deepReason?.shrineMeaning).toContain("静かに休みたい");
  expect(items[0].cardProps.badgesOverride).toEqual(["休息"]);
});

it("非変更確認: breakdown.matched_need_tagsのキー・値はcardProps.breakdownにそのまま保持される", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "神社Z",
          shrine_id: 303,
          reason: "元の理由",
          breakdown: { matched_need_tags: ["career"], score_total: 0.8 },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items[0].cardProps.breakdown).toEqual({ matched_need_tags: ["career"], score_total: 0.8 });
});

it("shrine_id がない recommendation は除外される", () => {
  const resp = {
    ok: true,
    data: {
      recommendations: [
        {
          name: "place only shrine",
          place_id: "place_123",
          reason: "理由あり",
          breakdown: { matched_need_tags: ["money"] },
        },
      ],
    },
  };

  const items = conciergeToShrineListItems(resp as any);
  expect(items).toEqual([]);
});


