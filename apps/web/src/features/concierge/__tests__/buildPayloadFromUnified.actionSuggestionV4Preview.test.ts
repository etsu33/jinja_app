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

function findFirstRecommendationItem(p: ReturnType<typeof buildPayloadFromUnified>): any {
  const recSec = p?.sections?.find((s: any) => s.type === "recommendations") as any;
  return recSec?.items?.[0] ?? null;
}

describe("buildPayloadFromUnified action_suggestion_v4_preview normalization", () => {
  it("normalizes a raw Backend snake_case action_suggestion_v4_preview into the camelCase ViewModel (regression for Hero crash on preview.primaryAction.label)", () => {
    const u: any = {
      data: {
        recommendations: [
          {
            shrine_id: 10,
            display_name: "S1",
            reason: "R1",
            action_suggestion_v4_preview: {
              primary_action: {
                label: "まず詳細を見る",
                description: "候補神社の詳細を見て判断材料を増やします。",
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
          },
        ],
      },
      thread: { id: 1 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    const item = findFirstRecommendationItem(p);

    expect(item).not.toBeNull();
    // The field the Hero component reads directly (preview.primaryAction.label) must exist
    // in camelCase form -- this is exactly what crashed when the raw snake_case payload was
    // passed through unnormalized.
    expect(item.actionSuggestionV4Preview.primaryAction.label).toBe("まず詳細を見る");
    expect(item.actionSuggestionV4Preview.secondaryAction.actionType).toBe("save");
    expect(item.actionSuggestionV4Preview.reflectionPrompt.promptType).toBe("before_visit");
    expect(item.actionSuggestionV4Preview.actionSource.source).toBe("fallback");
    expect(item.actionSuggestionV4Preview.sourceKeys).toEqual(["recommendation_reason_v4"]);
  });

  it("normalizes a camelCase action_suggestion_v4_preview payload", () => {
    const u: any = {
      data: {
        recommendations: [
          {
            shrine_id: 11,
            display_name: "S2",
            reason: "R2",
            actionSuggestionV4Preview: {
              primaryAction: {
                label: "まず詳細を見る",
                description: "候補神社の詳細を見て判断材料を増やします。",
                actionType: "detail_open",
                confidence: 0.82,
              },
              secondaryAction: {
                label: "保存する",
                description: "あとで見返します。",
                actionType: "save",
                confidence: 0.74,
              },
              reflectionPrompt: {
                question: "何を整理したいですか？",
                promptType: "before_visit",
                sourceSeed: "fallback",
              },
              actionSource: {
                source: "fallback",
                reason: "安全な初期提案",
              },
              preview: true,
              version: "v4",
              sourceKeys: ["recommendation_reason_v4"],
            },
          },
        ],
      },
      thread: { id: 2 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    const item = findFirstRecommendationItem(p);

    expect(item.actionSuggestionV4Preview.primaryAction.label).toBe("まず詳細を見る");
  });

  it("normalizes an incomplete preview (missing secondary_action) to null instead of passing the raw object through", () => {
    const u: any = {
      data: {
        recommendations: [
          {
            shrine_id: 12,
            display_name: "S3",
            reason: "R3",
            action_suggestion_v4_preview: {
              primary_action: {
                label: "まず詳細を見る",
                description: "説明",
                action_type: "detail_open",
                confidence: 0.5,
              },
              reflection_prompt: {
                question: "問い",
                prompt_type: "before_visit",
                source_seed: "fallback",
              },
              action_source: { source: "fallback", reason: "理由" },
              preview: true,
              version: "v4",
            },
          },
        ],
      },
      thread: { id: 3 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    const item = findFirstRecommendationItem(p);

    expect(item).not.toBeNull();
    expect(item.actionSuggestionV4Preview).toBeNull();
  });

  it("does not throw and yields null actionSuggestionV4Preview when the field is entirely absent", () => {
    const u: any = {
      data: {
        recommendations: [{ shrine_id: 13, display_name: "S4", reason: "R4" }],
      },
      thread: { id: 4 },
    };

    expect(() => buildPayloadFromUnified(u, baseFilterState)).not.toThrow();
    const item = findFirstRecommendationItem(buildPayloadFromUnified(u, baseFilterState));
    expect(item.actionSuggestionV4Preview).toBeNull();
  });
});
