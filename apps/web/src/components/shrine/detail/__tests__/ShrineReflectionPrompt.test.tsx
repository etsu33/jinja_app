import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ShrineReflectionPrompt } from "../ShrineReflectionPrompt";
import { createShrineReflection } from "@/lib/api/reflections";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";

vi.mock("@/lib/api/reflections", () => ({
  createShrineReflection: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: vi.fn(),
}));

const mockedCreateShrineReflection = vi.mocked(createShrineReflection);
const mockedTrackSearchEvent = vi.mocked(trackSearchEvent);

describe("ShrineReflectionPrompt", () => {
  beforeEach(() => {
    mockedCreateShrineReflection.mockReset();
    mockedTrackSearchEvent.mockReset();
  });

  it("表示時に reflection_prompt_view を送信する", () => {
    render(
      <ShrineReflectionPrompt
        shrineId={17}
        historyTheme="静寂"
        threadId="tid-1"
        ctx="concierge"
        accessLevel="free"
      />,
    );

    expect(screen.getByText("参拝後の振り返り")).toBeInTheDocument();
    expect(mockedTrackSearchEvent).toHaveBeenCalledWith("reflection_prompt_view", {
      source: "shrine_detail",
      shrineId: 17,
      threadId: "tid-1",
      historyTheme: "静寂",
      reflectionFormType: "mood_delta",
      reflectionContext: "visit_done",
      mode: "need",
      accessLevel: "free",
    });
  });

  it("入力して保存するとAPIを呼び reflection_saved を送信する", async () => {
    const onSaved = vi.fn();
    mockedCreateShrineReflection.mockResolvedValueOnce({
      id: 1,
      user: 10,
      shrine: 17,
      history_theme: "静寂",
      prompt: "参拝して、今どんな変化がありましたか？",
      answer: "少し落ち着きました。",
      mood_before: "anxious",
      mood_after: "calm",
      created_at: "2026-06-03T00:00:00Z",
    });

    render(
      <ShrineReflectionPrompt
        shrineId={17}
        historyTheme="静寂"
        threadId="tid-1"
        ctx="concierge"
        accessLevel="free"
        onSaved={onSaved}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText(/少し落ち着いた/), {
      target: { value: "少し落ち着きました。" },
    });
    fireEvent.change(screen.getByPlaceholderText("参拝前の気分 任意"), {
      target: { value: "anxious" },
    });
    fireEvent.change(screen.getByPlaceholderText("参拝後の気分 任意"), {
      target: { value: "calm" },
    });

    fireEvent.click(screen.getByRole("button", { name: "振り返りを保存する" }));

    await waitFor(() => {
      expect(mockedCreateShrineReflection).toHaveBeenCalledWith(17, {
        history_theme: "静寂",
        prompt: "参拝して、今どんな変化がありましたか？",
        answer: "少し落ち着きました。",
        mood_before: "anxious",
        mood_after: "calm",
      });
    });

    expect(mockedTrackSearchEvent).toHaveBeenCalledWith("reflection_saved", {
      source: "shrine_detail",
      shrineId: 17,
      threadId: "tid-1",
      historyTheme: "静寂",
      reflectionFormType: "mood_delta",
      reflectionContext: "visit_done",
      answerLength: 10,
      moodBefore: "anxious",
      moodAfter: "calm",
      mode: "need",
      accessLevel: "free",
    });
    expect(onSaved).toHaveBeenCalled();
  });

  it("保存失敗時はエラー表示する", async () => {
    mockedCreateShrineReflection.mockRejectedValueOnce(new Error("failed"));

    render(<ShrineReflectionPrompt shrineId={17} />);

    fireEvent.change(screen.getByPlaceholderText(/少し落ち着いた/), {
      target: { value: "保存できないケース" },
    });
    fireEvent.click(screen.getByRole("button", { name: "振り返りを保存する" }));

    expect(await screen.findByText("振り返りの保存に失敗しました。")).toBeInTheDocument();
  });
});
