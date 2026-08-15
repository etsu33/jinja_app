import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ShrineDeepDivePrompt } from "../ShrineDeepDivePrompt";
import { askDeepDive, type DeepDiveAnswer, type DeepDiveAskError } from "@/lib/api/deepDive";

vi.mock("@/lib/api/deepDive", () => ({
  askDeepDive: vi.fn(),
}));

const mockedAskDeepDive = vi.mocked(askDeepDive);

function ask(text: string) {
  fireEvent.change(screen.getByPlaceholderText(/誰を祀っていますか/), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: /質問する/ }));
}

function makeError(status: number): DeepDiveAskError {
  const error = new Error("deep_dive_ask_failed") as DeepDiveAskError;
  error.status = status;
  return error;
}

describe("ShrineDeepDivePrompt", () => {
  beforeEach(() => {
    mockedAskDeepDive.mockReset();
  });

  // --- 1. 明治神宮 deity ---
  it("1. Full readiness(deity_who)でanswer/sourcesを表示する", async () => {
    const response: DeepDiveAnswer = {
      answer: "明治天皇と昭憲皇太后をお祀りしています。",
      readiness: "full",
      question_type: ["deity_who"],
      facts_used: [{ type: "deity", id: 1, label: "明治天皇" }],
      sources_used: [
        {
          id: 1,
          title: "公式サイト「明治神宮とは」",
          publisher: "明治神宮",
          source_type: "shrine_official",
          url: "https://example.com/about",
        },
      ],
      limitations: null,
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("誰を祀っていますか？");

    expect(await screen.findByText("明治天皇と昭憲皇太后をお祀りしています。")).toBeInTheDocument();
    expect(screen.getByText("公式サイト「明治神宮とは」")).toBeInTheDocument();
    expect(mockedAskDeepDive).toHaveBeenCalledWith(1, "誰を祀っていますか？");
  });

  // --- 2. Full history ---
  it("2. Full readiness(founding)でanswer/sourcesを表示する", async () => {
    const response: DeepDiveAnswer = {
      answer: "創建の経緯についてお答えします。",
      readiness: "full",
      question_type: ["founding"],
      facts_used: [{ type: "history", id: 2, label: "創建の経緯" }],
      sources_used: [
        { id: 2, title: "由緒書", publisher: "神社本庁", source_type: "official_record", url: "https://example.com/history" },
      ],
      limitations: null,
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={4} />);
    ask("なぜ創建されたのですか？");

    expect(await screen.findByText("創建の経緯についてお答えします。")).toBeInTheDocument();
    expect(screen.getByText("由緒書")).toBeInTheDocument();
  });

  // --- 3. Full tradition ---
  it("3. Full readiness(tradition)でanswer/sourcesを表示する", async () => {
    const response: DeepDiveAnswer = {
      answer: "こう伝わっています。",
      readiness: "full",
      question_type: ["tradition"],
      facts_used: [{ type: "history", id: 3, label: "言い伝え" }],
      sources_used: [
        { id: 3, title: "地域史料", publisher: "郷土資料館", source_type: "local_record", url: "https://example.com/tradition" },
      ],
      limitations: null,
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={7} />);
    ask("どんな伝承がありますか？");

    expect(await screen.findByText("こう伝わっています。")).toBeInTheDocument();
    expect(screen.getByText("地域史料")).toBeInTheDocument();
  });

  // --- 4. Limited ---
  it("4. Limited readinessはerror扱いにせず、answer + limitationsを表示する", async () => {
    const response: DeepDiveAnswer = {
      answer: "確認できる範囲でお答えします。",
      readiness: "limited",
      question_type: ["deity_who"],
      facts_used: [{ type: "deity", id: 5, label: "大国魂大神" }],
      sources_used: [{ id: 5, title: "公式", publisher: "神社", source_type: "shrine_official", url: "https://example.com" }],
      limitations: "この神社について確認できる資料は限られており、確認できる範囲でお答えしています。",
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={22} />);
    ask("誰を祀っていますか？");

    expect(await screen.findByText("確認できる範囲でお答えします。")).toBeInTheDocument();
    const limitationsNode = await screen.findByText(
      "この神社について確認できる資料は限られており、確認できる範囲でお答えしています。",
    );
    expect(limitationsNode.className).not.toContain("rose");
  });

  // --- 5. Not Ready ---
  it("5. Not Readyはerror alertにせず、静かなslate文言で理由を表示する", async () => {
    const response: DeepDiveAnswer = {
      answer: "",
      readiness: "not_ready",
      question_type: [],
      facts_used: [],
      sources_used: [],
      limitations: "この神社については、根拠付きで詳しくお答えできる情報がまだ十分ではありません。",
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={58} />);
    ask("誰を祀っていますか？");

    const message = await screen.findByText(
      "この神社については、根拠付きで詳しくお答えできる情報がまだ十分ではありません。",
    );
    expect(message.className).toContain("slate-400");
    expect(message.className).not.toContain("rose");
    expect(message.className).not.toContain("border");
  });

  // --- 6. Source複数 ---
  it("6. 複数Sourceを表示し、internal fieldは表示しない", async () => {
    const response: DeepDiveAnswer = {
      answer: "回答本文。",
      readiness: "full",
      question_type: ["deity_who"],
      facts_used: [],
      sources_used: [
        { id: 1, title: "Source A", publisher: "publisher A", source_type: "shrine_official", url: "https://a.example.com" },
        { id: 2, title: "Source B", publisher: "publisher B", source_type: "academic", url: "https://b.example.com" },
      ],
      limitations: null,
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("誰を祀っていますか？");

    expect(await screen.findByText("Source A")).toBeInTheDocument();
    expect(screen.getByText("Source B")).toBeInTheDocument();
    expect(screen.getByText("https://a.example.com")).toBeInTheDocument();
    expect(screen.getByText("https://b.example.com")).toBeInTheDocument();

    const container = screen.getByText("回答本文。").closest("div");
    expect(container?.textContent).not.toMatch(/verification_status|confidence|reason_strength/);
  });

  // --- 7. unanswered_aspects ---
  it("7. unanswered_aspectsがある場合はその内容を表示する", async () => {
    const response: DeepDiveAnswer = {
      answer: "創建の経緯についてお答えします。",
      readiness: "full",
      question_type: ["founding", "tradition"],
      facts_used: [{ type: "history", id: 1, label: "創建の経緯" }],
      sources_used: [],
      limitations: null,
      unanswered_aspects: ["tradition"],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("なぜ創建されたのですか？また、どんな伝承がありますか？");

    expect(await screen.findByText(/tradition/)).toBeInTheDocument();
  });

  // --- 8. LLM failure(200) ---
  it("8. LLM失敗時の固定文言(200)を通常のanswerとして表示する(独自fallbackを作らない)", async () => {
    const response: DeepDiveAnswer = {
      answer: "現在、回答の生成に失敗しました。時間をおいて再度お試しください。",
      readiness: "full",
      question_type: ["deity_who"],
      facts_used: [{ type: "deity", id: 1, label: "神" }],
      sources_used: [{ id: 1, title: "公式", publisher: "神社", source_type: "shrine_official", url: "https://example.com" }],
      limitations: null,
      unanswered_aspects: [],
    };
    mockedAskDeepDive.mockResolvedValueOnce(response);

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("誰を祀っていますか？");

    const message = await screen.findByText("現在、回答の生成に失敗しました。時間をおいて再度お試しください。");
    // Backendのdeterministic responseをそのまま表示するだけであり、
    // Frontend独自のerror styling(rose)を追加しない。
    expect(message.className).not.toContain("rose");
  });

  // --- 9. network failure ---
  it("9. network failureはsystem errorとしてrose表示する", async () => {
    mockedAskDeepDive.mockRejectedValueOnce(new Error("network down"));

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("誰を祀っていますか？");

    const message = await screen.findByText("通信に失敗しました。時間をおいて再度お試しください。");
    expect(message.className).toContain("rose");
  });

  it("400 validation errorは入力エラーとして表示する", async () => {
    mockedAskDeepDive.mockRejectedValueOnce(makeError(400));

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("誰を祀っていますか？");

    expect(await screen.findByText("質問の内容を確認してください。")).toBeInTheDocument();
  });

  it("404 shrine not foundはその旨を表示する", async () => {
    mockedAskDeepDive.mockRejectedValueOnce(makeError(404));

    render(<ShrineDeepDivePrompt shrineId={999999} />);
    ask("誰を祀っていますか？");

    expect(await screen.findByText("神社情報を取得できませんでした。")).toBeInTheDocument();
  });

  // --- 10. empty question ---
  it("10. 空質問(空白のみ含む)は送信ボタンを無効化し、APIを呼ばない", () => {
    render(<ShrineDeepDivePrompt shrineId={1} />);

    const button = screen.getByRole("button", { name: "質問する" });
    expect(button).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText(/誰を祀っていますか/), { target: { value: "   " } });
    expect(button).toBeDisabled();

    fireEvent.click(button);
    expect(mockedAskDeepDive).not.toHaveBeenCalled();
  });

  it("送信中はボタンを無効化しラベルを変える", async () => {
    let resolvePromise: (value: DeepDiveAnswer) => void = () => {};
    mockedAskDeepDive.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    render(<ShrineDeepDivePrompt shrineId={1} />);
    ask("誰を祀っていますか？");

    expect(screen.getByRole("button", { name: "回答を生成中..." })).toBeDisabled();

    resolvePromise({
      answer: "回答",
      readiness: "full",
      question_type: ["deity_who"],
      facts_used: [],
      sources_used: [],
      limitations: null,
      unanswered_aspects: [],
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "質問する" })).not.toBeDisabled();
    });
  });
});
