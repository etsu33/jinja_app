import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const postConciergeChat = vi.fn();
vi.mock("@/lib/api/conciergeChat", () => ({ postConciergeChat: (p: unknown) => postConciergeChat(p) }));

import TravelConciergeClient from "../TravelConciergeClient";
import { metadata } from "../page";

function mockGeolocation(result: { lat: number; lng: number } | null) {
  const getCurrentPosition = vi.fn((ok: PositionCallback, fail: PositionErrorCallback) => {
    if (result) ok({ coords: { latitude: result.lat, longitude: result.lng } } as GeolocationPosition);
    else fail({ code: 1 } as GeolocationPositionError);
  });
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: { getCurrentPosition } });
}

describe("/en/concierge (preview)", () => {
  beforeEach(() => {
    postConciergeChat.mockReset();
    postConciergeChat.mockResolvedValue({
      data: { recommendations: [{ name: "赤坂氷川神社", shrine_id: 60, reason: "静かな杜", distance_m: 900 }] },
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it("is not indexed by search engines", () => {
    expect(metadata.robots).toEqual({ index: false, follow: false });
  });

  it("sends travel mode in English with the current location and shows the results", async () => {
    mockGeolocation({ lat: 35.67, lng: 139.73 });
    render(<TravelConciergeClient />);

    fireEvent.change(screen.getByLabelText("What are you looking for?"), { target: { value: "Somewhere quiet with old trees" } });
    fireEvent.click(screen.getByRole("button", { name: "Find shrines" }));

    await waitFor(() => expect(postConciergeChat).toHaveBeenCalledTimes(1));
    expect(postConciergeChat).toHaveBeenCalledWith({
      query: "Somewhere quiet with old trees",
      mode: "travel",
      language: "en",
      lat: 35.67,
      lng: 139.73,
    });
    expect(await screen.findByText("赤坂氷川神社")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /赤坂氷川神社|詳細/ })).toHaveAttribute("href", "/en/shrines/60");
  });

  it("still sends without a location and says so", async () => {
    mockGeolocation(null);
    render(<TravelConciergeClient />);

    fireEvent.change(screen.getByLabelText("What are you looking for?"), { target: { value: "quiet forest" } });
    fireEvent.click(screen.getByRole("button", { name: "Find shrines" }));

    await waitFor(() => expect(postConciergeChat).toHaveBeenCalledWith({ query: "quiet forest", mode: "travel", language: "en" }));
    expect(screen.getByRole("status")).toHaveTextContent("could not get your location");
  });

  it("does not send an empty consultation", () => {
    render(<TravelConciergeClient />);
    expect(screen.getByRole("button", { name: "Find shrines" })).toBeDisabled();
  });

  it("shows an error when the request fails", async () => {
    mockGeolocation(null);
    postConciergeChat.mockRejectedValueOnce(new Error("chat failed: 500"));
    render(<TravelConciergeClient />);

    fireEvent.change(screen.getByLabelText("What are you looking for?"), { target: { value: "quiet" } });
    fireEvent.click(screen.getByRole("button", { name: "Find shrines" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong");
  });
});
