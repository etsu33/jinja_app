import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import NearbyShrineCardListClient from "../NearbyShrineCardListClient";

const mockSearchParams = new Map<string, string>();

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({
    get: (key: string) => mockSearchParams.get(key) ?? null,
  }),
}));

function mockGeolocationSuccess() {
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: {
      getCurrentPosition: vi.fn((success: PositionCallback) => {
        success({
          coords: {
            latitude: 35.681236,
            longitude: 139.767125,
            accuracy: 10,
            altitude: null,
            altitudeAccuracy: null,
            heading: null,
            speed: null,
          },
          timestamp: Date.now(),
        } as GeolocationPosition);
      }),
    },
  });
}

describe("NearbyShrineCardListClient", () => {
  beforeEach(() => {
    mockSearchParams.clear();
    mockGeolocationSuccess();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ results: [] }),
      }),
    );
  });

  it("empty 状態で登録がない可能性の文言と神社追加リンクを表示する", async () => {
    render(<NearbyShrineCardListClient />);

    expect(await screen.findByText("近くに候補が見つかりませんでした。")).toBeInTheDocument();
    expect(screen.getByText("この場所にはまだ登録がない可能性があります。")).toBeInTheDocument();

    const addLink = screen.getByRole("link", { name: "神社を追加する" });
    expect(addLink).toHaveAttribute("href", "/shrines/new?returnTo=/map");
    expect(screen.getByRole("link", { name: "Googleマップで探す" })).toBeInTheDocument();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/places/nearby?"), expect.any(Object));
    });
  });

  it("submitted=1 かつ status=pending のとき submission 受付バナーを表示する", async () => {
    mockSearchParams.set("submitted", "1");
    mockSearchParams.set("status", "pending");
    mockSearchParams.set("name", "テスト神社");

    render(<NearbyShrineCardListClient />);

    expect(screen.getByRole("status")).toHaveTextContent(
      /「テスト神社」の投稿を受け付けました。\s*現在審査中のため、公開検索にはまだ表示されません。\s*審査完了後に公開されます。/,
    );
    expect(await screen.findByText("近くに候補が見つかりませんでした。")).toBeInTheDocument();
  });
});
