import { act, fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import CompassClient from "../CompassClient";

function setOriginViaPrefecture() {
  fireEvent.click(screen.getByRole("button", { name: "変更する" }));
  fireEvent.click(screen.getByRole("radio", { name: "都道府県から指定" }));
  fireEvent.change(screen.getByLabelText("都道府県"), { target: { value: "東京都" } });
}

function fillMinimumValidInput() {
  fireEvent.click(screen.getByRole("radio", { name: "転機・仕事" }));
  setOriginViaPrefecture();
  fireEvent.change(screen.getByLabelText("生年月日（方位計算に使用）"), {
    target: { value: "1990-01-01" },
  });
}

describe("CompassClient", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("初期状態では月見出しとProduct Promiseのみを表示し、結果セクションは出さない", () => {
    render(<CompassClient />);
    expect(screen.getByRole("heading", { level: 1, name: "今月の参拝コンパス" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "今月の参拝コンパス" })).toBeInTheDocument();
    expect(screen.getByText("今月の流れと目的から、向かう方向と参拝候補を見つけます。")).toBeInTheDocument();
    expect(screen.queryByText("この方向の参拝候補")).not.toBeInTheDocument();
  });

  it("目的・出発地点・生年月日が未入力のまま送信すると、それぞれ個別のエラーを出しAPIを呼ばない", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<CompassClient />);

    fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));

    expect(screen.getByText("出発地点を選択してください。")).toBeInTheDocument();
    expect(screen.getByText("生年月日を入力してください。")).toBeInTheDocument();
    expect(screen.getByText("目的を選択してください。")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("入力が揃うとAPIへpurpose/origin/birthdateを送信し、成功時に方向と推薦を表示する", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        state: "recommendation_success",
        purpose: "career",
        direction_context: {
          targetDate: "2026-09-15",
          targetYear: 2026,
          solarMonthIndex: 8,
          referenceDirections: ["北西"],
          calculationMethod: "annual_monthly_kyusei_v1",
          note: "年盤と月盤による参考情報です。日盤は使用していません。",
        },
        recommendations: [{ shrine_id: 1, name: "北西神社", reason: "仕事運との一致" }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<CompassClient />);
    fillMinimumValidInput();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
    });

    const [, init] = fetchMock.mock.calls[0];
    const sentBody = JSON.parse(init.body);
    expect(sentBody.purpose).toBe("career");
    expect(sentBody.birthdate).toBe("1990-01-01");
    expect(sentBody.origin).toEqual({ lat: 35.6762, lng: 139.6503 });

    expect(await screen.findByText("今月意識したい方向: 北西")).toBeInTheDocument();
    expect(screen.getByText("この方向の参拝候補")).toBeInTheDocument();
    expect(screen.getByText("北西神社")).toBeInTheDocument();
  });

  it("「その他の目的」から選んでも送信payloadは折りたたみ表示に影響されず正しいslugになる（Purpose UI Polish回帰確認）", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        state: "recommendation_success",
        purpose: "travel_safe",
        direction_context: {
          targetDate: "2026-09-15",
          targetYear: 2026,
          solarMonthIndex: 8,
          referenceDirections: ["北西"],
          calculationMethod: "annual_monthly_kyusei_v1",
          note: "note",
        },
        recommendations: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<CompassClient />);
    fireEvent.click(screen.getByRole("button", { name: /その他の目的を見る/ }));
    fireEvent.click(screen.getByRole("radio", { name: "移動・安全" }));
    setOriginViaPrefecture();
    fireEvent.change(screen.getByLabelText("生年月日（方位計算に使用）"), {
      target: { value: "1990-01-01" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body).purpose).toBe("travel_safe");
  });

  it("direction_zero_candidatesとdirection_filter_unavailableを区別して表示する", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        state: "direction_zero_candidates",
        purpose: "career",
        direction_context: {
          targetDate: "2026-09-15",
          targetYear: 2026,
          solarMonthIndex: 8,
          referenceDirections: ["北西"],
          calculationMethod: "annual_monthly_kyusei_v1",
          note: "note",
        },
        recommendations: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<CompassClient />);
    fillMinimumValidInput();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
    });

    expect(await screen.findByText("この方向の参拝候補が見つかりませんでした")).toBeInTheDocument();
    expect(screen.queryByText("方向の参考情報を計算できませんでした")).not.toBeInTheDocument();
    expect(screen.queryByText("この方向の参拝候補")).not.toBeInTheDocument();
  });

  it("no_common_directionは正当な結果として表示し、direction_filter_unavailableの誤解を招く案内文は出さない", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        state: "no_common_direction",
        purpose: "career",
        direction_context: null,
        recommendations: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<CompassClient />);
    fillMinimumValidInput();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
    });

    expect(await screen.findByText("今月は年盤と月盤で重なる方位がありません")).toBeInTheDocument();
    // Must not imply the failure is a calculation error or an input mistake.
    expect(
      screen.queryByText("生年月日または出発地点をご確認のうえ、もう一度お試しください。"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("方向の参考情報を計算できませんでした")).not.toBeInTheDocument();
    // No direction visual, no recommendation cards -- there is nothing to show.
    expect(screen.queryByText("今月意識したい方向:", { exact: false })).not.toBeInTheDocument();
    expect(screen.queryByText("この方向の参拝候補")).not.toBeInTheDocument();
  });

  it("direction_filter_unavailableは引き続き既存のfail-safe文言を表示する", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        state: "direction_filter_unavailable",
        purpose: "career",
        direction_context: null,
        recommendations: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<CompassClient />);
    fillMinimumValidInput();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
    });

    expect(await screen.findByText("方向の参考情報を計算できませんでした")).toBeInTheDocument();
    expect(
      screen.getByText("生年月日または出発地点をご確認のうえ、もう一度お試しください。"),
    ).toBeInTheDocument();
    expect(screen.queryByText("今月は年盤と月盤で重なる方位がありません")).not.toBeInTheDocument();
  });

  it("バックエンドエラー時は落ち着いた文言のエラー状態を表示する", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));

    render(<CompassClient />);
    fillMinimumValidInput();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));
    });

    expect(await screen.findByText("只今、確認できませんでした")).toBeInTheDocument();
  });

  it("送信中はボタンが無効化され、ラベルが変わる", async () => {
    let resolveFetch: (value: unknown) => void = () => undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
      ),
    );

    render(<CompassClient />);
    fillMinimumValidInput();
    fireEvent.click(screen.getByRole("button", { name: "今月の方向を確認する" }));

    expect(await screen.findByRole("button", { name: "確認しています…" })).toBeDisabled();

    await act(async () => {
      resolveFetch({ ok: true, status: 200, json: async () => ({ state: "direction_zero_candidates", purpose: "career", direction_context: null, recommendations: [] }) });
    });
  });
});
