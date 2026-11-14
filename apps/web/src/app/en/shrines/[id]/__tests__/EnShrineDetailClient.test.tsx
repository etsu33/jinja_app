import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const apiGet = vi.fn();
vi.mock("@/lib/api/client", () => ({ default: { get: (url: string) => apiGet(url) } }));

import EnShrineDetailClient from "../EnShrineDetailClient";
import { metadata } from "../page";

function mockGeolocation(result: { lat: number; lng: number } | null) {
  const getCurrentPosition = vi.fn((ok: PositionCallback, fail: PositionErrorCallback) => {
    if (result) ok({ coords: { latitude: result.lat, longitude: result.lng } } as GeolocationPosition);
    else fail({ code: 1 } as GeolocationPositionError);
  });
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: { getCurrentPosition } });
}

const SHRINE = { name_jp: "赤坂氷川神社", name_romaji: "Akasaka Hikawa Jinja", address: "東京都港区赤坂6-10-12", latitude: 35.6702, longitude: 139.7357 };
const WORDS = {
  shrine_id: 60,
  items: [
    { word_id: "S_FOREST", label_en: "sacred forest", category: "Sight", slot: "scenery_experience", source_url: "https://example.jp/b", checked_on: "2026-11-01" },
    { word_id: "T_IMPERIAL", label_en: "imperial connection", category: "Story", slot: "history_culture", source_url: "https://example.jp/a", checked_on: "2026-11-01" },
  ],
};

function respond(words: unknown = WORDS) {
  apiGet.mockImplementation((url: string) => {
    if (url === "/shrines/60/data/") return Promise.resolve({ data: SHRINE });
    if (url === "/shrines/60/feature-words-en/") return Promise.resolve({ data: words });
    return Promise.reject({ response: { status: 404 } });
  });
}

describe("/en/shrines/[id]（英語の神社詳細・限定公開）", () => {
  beforeEach(() => {
    apiGet.mockReset();
    mockGeolocation({ lat: 35.6812, lng: 139.7671 });
  });
  afterEach(() => vi.restoreAllMocks());

  it("検索に出さない（限定公開）", () => {
    expect(metadata.robots).toEqual({ index: false, follow: false });
  });

  it("BFF（/api）経由で神社データと特徴語を読む", async () => {
    respond();
    render(<EnShrineDetailClient shrineId={60} />);
    await screen.findByRole("heading", { level: 1, name: "赤坂氷川神社" });
    expect(apiGet).toHaveBeenCalledWith("/shrines/60/data/");
    expect(apiGet).toHaveBeenCalledWith("/shrines/60/feature-words-en/");
  });

  it("枠が 2 → 4 → 5 → 6 の順に並び、本文は英語（lang=en）", async () => {
    respond();
    const { container } = render(<EnShrineDetailClient shrineId={60} />);
    await screen.findByRole("heading", { level: 1, name: "赤坂氷川神社" });
    await waitFor(() => expect(screen.getByText(/km away|m away/)).toBeInTheDocument());

    const order = Array.from(container.querySelectorAll("[data-section]")).map((el) => el.getAttribute("data-section"));
    expect(order).toEqual(["name_location", "history_culture", "scenery_experience", "visit"]);
    expect(container.querySelector("main")).toHaveAttribute("lang", "en");
    expect(screen.getByText("Akasaka Hikawa Jinja")).toBeInTheDocument();
    expect(screen.getByText("東京都港区赤坂6-10-12")).toBeInTheDocument();

    const history = screen.getByRole("region", { name: "History and culture" });
    expect(history).toHaveTextContent("imperial connection");
    const scenery = screen.getByRole("region", { name: "Scenery and experience" });
    expect(scenery).toHaveTextContent("sacred forest");
    const sources = screen.getAllByRole("link", { name: "Source (official site)" });
    expect(sources.map((a) => a.getAttribute("href"))).toEqual(["https://example.jp/a", "https://example.jp/b"]);

    const route = screen.getByRole("link", { name: "Open the route in Google Maps" });
    expect(route.getAttribute("href")).toContain("https://www.google.com/maps/dir/");
    expect(route.getAttribute("href")).not.toContain("origin=");
  });

  it("写真・訪れる価値の一言・ご利益や推薦理由・ご縁の文は出さない", async () => {
    respond();
    const { container } = render(<EnShrineDetailClient shrineId={60} />);
    await screen.findByRole("heading", { level: 1, name: "赤坂氷川神社" });
    expect(container.querySelector("img")).toBeNull();
    const text = container.textContent ?? "";
    for (const word of ["Matches your interests", "Known for", "goen", "fate", "destiny", "blessing", "ご利益", "ご縁"]) {
      expect(text).not.toContain(word);
    }
  });

  it("特徴語が無い神社は、その旨を短く出し、4・5 の枠は出さない", async () => {
    respond({ shrine_id: 60, items: [] });
    const { container } = render(<EnShrineDetailClient shrineId={60} />);
    await screen.findByText(/don.t have verified information about this shrine.s history or scenery yet/);
    expect(container.querySelector('[data-section="history_culture"]')).toBeNull();
    expect(container.querySelector('[data-section="scenery_experience"]')).toBeNull();
  });

  it("特徴語の読み込みに失敗しても、名前・所在地とルートは出す", async () => {
    apiGet.mockImplementation((url: string) =>
      url === "/shrines/60/data/" ? Promise.resolve({ data: SHRINE }) : Promise.reject(new Error("boom")),
    );
    render(<EnShrineDetailClient shrineId={60} />);
    await screen.findByRole("heading", { level: 1, name: "赤坂氷川神社" });
    expect(screen.getByRole("link", { name: "Open the route in Google Maps" })).toBeInTheDocument();
  });

  it("現在地が取れなければ距離は出さない", async () => {
    mockGeolocation(null);
    respond();
    render(<EnShrineDetailClient shrineId={60} />);
    await screen.findByRole("heading", { level: 1, name: "赤坂氷川神社" });
    expect(screen.queryByText(/km away|m away/)).not.toBeInTheDocument();
  });

  it("神社が無いときは、見つからない旨を出す", async () => {
    apiGet.mockRejectedValue({ response: { status: 404 } });
    render(<EnShrineDetailClient shrineId={999} />);
    expect(await screen.findByText("This shrine could not be found.")).toBeInTheDocument();
  });

  it("id が不正なら読み込まずに、見つからない旨を出す", () => {
    render(<EnShrineDetailClient shrineId={null} />);
    expect(screen.getByText("This shrine could not be found.")).toBeInTheDocument();
    expect(apiGet).not.toHaveBeenCalled();
  });
});
