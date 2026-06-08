
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../client";
import { createShrineReflection, type ShrineReflectionPayload } from "../reflections";

vi.mock("../client", () => ({
  default: {
    post: vi.fn(),
  },
}));

const mockedPost = vi.mocked(api.post);

describe("createShrineReflection", () => {
  beforeEach(() => {
    mockedPost.mockReset();
  });

  it("神社IDとpayloadで振り返り保存APIを呼び出す", async () => {
    const payload: ShrineReflectionPayload = {
      history_theme: "静寂",
      prompt: "参拝して、今どんな変化がありましたか？",
      answer: "少し落ち着きました。",
      mood_before: "anxious",
      mood_after: "calm",
    };

    const response = {
      id: 1,
      user: 10,
      shrine: 17,
      shrine_name: "振り返り神社",
      history_theme: "静寂",
      prompt: payload.prompt ?? "",
      answer: payload.answer,
      mood_before: "anxious",
      mood_after: "calm",
      created_at: "2026-06-03T00:00:00Z",
    };

    mockedPost.mockResolvedValueOnce({ data: response });

    const result = await createShrineReflection(17, payload);

    expect(mockedPost).toHaveBeenCalledWith("/shrines/17/reflection", payload);
    expect(result).toEqual(response);
  });

  it("文字列の神社IDでも同じendpointへPOSTする", async () => {
    const payload: ShrineReflectionPayload = {
      answer: "次にやることを一つ決めました。",
    };

    const response = {
      id: 2,
      user: 10,
      shrine: 123,
      history_theme: "",
      prompt: "",
      answer: payload.answer,
      mood_before: "",
      mood_after: "",
      created_at: "2026-06-03T00:00:00Z",
    };

    mockedPost.mockResolvedValueOnce({ data: response });

    const result = await createShrineReflection("123", payload);

    expect(mockedPost).toHaveBeenCalledWith("/shrines/123/reflection", payload);
    expect(result).toEqual(response);
  });

  it("APIエラーは握りつぶさずrejectする", async () => {
    const error = new Error("reflection save failed");
    mockedPost.mockRejectedValueOnce(error);

    await expect(
      createShrineReflection(17, {
        answer: "保存に失敗するケース。",
      }),
    ).rejects.toThrow("reflection save failed");
  });
});
