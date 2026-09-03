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

function mockGeolocationError(code: number) {
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: {
      getCurrentPosition: vi.fn(
        (_success: PositionCallback, error?: PositionErrorCallback) => {
          error?.({ code, message: "x" } as GeolocationPositionError);
        },
      ),
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

  it.each([[1], [2], [3]])(
    "geolocation error(code %i) では東京駅 fallback で検索を継続し、crash / loading 永久化しない (RH3-4b)",
    async (code) => {
      mockGeolocationError(code);

      render(<NearbyShrineCardListClient />);

      // fail-safe: fallback (東京駅) の告知が出る & 検索は継続する
      expect(await screen.findByText("現在地が取れないため仮の場所（東京駅）で検索中")).toBeInTheDocument();
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining("lat=35.681236"),
          expect.any(Object),
        );
      });
      expect(await screen.findByText("近くに候補が見つかりませんでした。")).toBeInTheDocument();
    },
  );

  it("geolocation 成功時は fallback 告知を出さず、取得座標で検索する (RH3-4b)", async () => {
    // beforeEach の mockGeolocationSuccess をそのまま使う
    render(<NearbyShrineCardListClient />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("lat=35.681236"), expect.any(Object));
    });
    expect(screen.queryByText("現在地が取れないため仮の場所（東京駅）で検索中")).not.toBeInTheDocument();
  });
});
