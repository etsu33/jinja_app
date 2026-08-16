import { describe, expect, it } from "vitest";
import { normalizeActionSuggestionV4Preview } from "@/viewmodels/actionSuggestionV4Preview";

function validSnakeCasePreview() {
  return {
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
  };
}

function validCamelCasePreview() {
  return {
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
  };
}

describe("normalizeActionSuggestionV4Preview", () => {
  it("normalizes a valid snake_case (Backend) payload into the camelCase ViewModel", () => {
    const result = normalizeActionSuggestionV4Preview(validSnakeCasePreview());

    expect(result).not.toBeNull();
    expect(result?.primaryAction).toEqual({
      label: "まず詳細を見る",
      description: "候補神社の詳細を見て判断材料を増やします。",
      actionType: "detail_open",
      confidence: 0.82,
    });
    expect(result?.secondaryAction.actionType).toBe("save");
    expect(result?.reflectionPrompt).toEqual({
      question: "何を整理したいですか？",
      promptType: "before_visit",
      sourceSeed: "fallback",
    });
    expect(result?.actionSource).toEqual({ source: "fallback", reason: "安全な初期提案" });
    expect(result?.sourceKeys).toEqual(["recommendation_reason_v4"]);
    expect(result?.preview).toBe(true);
    expect(result?.version).toBe("v4");
  });

  it("normalizes a valid camelCase (legacy) payload into the camelCase ViewModel", () => {
    const result = normalizeActionSuggestionV4Preview(validCamelCasePreview());

    expect(result).not.toBeNull();
    expect(result?.primaryAction.label).toBe("まず詳細を見る");
    expect(result?.secondaryAction.actionType).toBe("save");
    expect(result?.reflectionPrompt.promptType).toBe("before_visit");
    expect(result?.actionSource.source).toBe("fallback");
    expect(result?.sourceKeys).toEqual(["recommendation_reason_v4"]);
  });

  it("returns null when primary_action is missing", () => {
    const raw = validSnakeCasePreview();
    delete (raw as any).primary_action;

    expect(normalizeActionSuggestionV4Preview(raw)).toBeNull();
  });

  it("returns null when secondary_action is missing", () => {
    const raw = validSnakeCasePreview();
    delete (raw as any).secondary_action;

    expect(normalizeActionSuggestionV4Preview(raw)).toBeNull();
  });

  it("returns null when reflection_prompt is missing", () => {
    const raw = validSnakeCasePreview();
    delete (raw as any).reflection_prompt;

    expect(normalizeActionSuggestionV4Preview(raw)).toBeNull();
  });

  it("returns null when action_source is missing", () => {
    const raw = validSnakeCasePreview();
    delete (raw as any).action_source;

    expect(normalizeActionSuggestionV4Preview(raw)).toBeNull();
  });

  it("accepts an empty description (Backend allows description: \"\", only label is required non-empty)", () => {
    const raw = validSnakeCasePreview();
    (raw as any).primary_action.description = "";

    const result = normalizeActionSuggestionV4Preview(raw);

    expect(result).not.toBeNull();
    expect(result?.primaryAction.description).toBe("");
    expect(result?.primaryAction.label).toBe("まず詳細を見る");
  });

  it("returns null for null/undefined/non-object input without throwing", () => {
    expect(normalizeActionSuggestionV4Preview(null)).toBeNull();
    expect(normalizeActionSuggestionV4Preview(undefined)).toBeNull();
    expect(normalizeActionSuggestionV4Preview("not-an-object")).toBeNull();
    expect(normalizeActionSuggestionV4Preview(42)).toBeNull();
  });
});
