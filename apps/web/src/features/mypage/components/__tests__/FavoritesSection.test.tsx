import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import FavoritesSection from "../FavoritesSection";

const useFavoritesMock = vi.fn();

vi.mock("../hooks/useFavorites", () => ({
  useFavorites: (args: unknown) => useFavoritesMock(args),
}));

vi.mock("../FavoriteShrineCard", () => ({
  FavoriteShrineCard: ({
    favorite,
    onUnsave,
  }: {
    favorite: { shrine?: { name_jp?: string | null } };
    onUnsave?: () => void;
  }) => (
    <div>
      <span>{favorite.shrine?.name_jp ?? "NO_NAME"}</span>
      <button type="button" onClick={onUnsave}>
        解除
      </button>
    </div>
  ),
}));

describe("FavoritesSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("解除後に対象 shrine が一覧から消える", () => {
    const target = {
      id: 101,
      created_at: "2026-04-18T08:00:00Z",
      public_goshuin_count: 0,
      shrine: {
        id: 17,
        name_jp: "乃木神社",
        address: "東京都港区赤坂",
      },
    };

    const other = {
      id: 102,
      created_at: "2026-04-17T08:00:00Z",
      public_goshuin_count: 0,
      shrine: {
        id: 18,
        name_jp: "伊勢山皇大神宮",
        address: "神奈川県横浜市",
      },
    };

    let items = [target, other];

    const unSaveMock = vi.fn((favorite: { id: number }) => {
      items = items.filter((x) => x.id !== favorite.id);
    });

    useFavoritesMock.mockImplementation(() => ({
      get items() {
        return items;
      },
      get count() {
        return items.length;
      },
      unSave: unSaveMock,
      error: null,
    }));

    const { rerender } = render(<FavoritesSection initialFavorites={[target, other] as any} />);

    expect(screen.getByText("乃木神社")).toBeInTheDocument();
    expect(screen.getByText("伊勢山皇大神宮")).toBeInTheDocument();
    expect(screen.getByText("2件")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "解除" })[0]);

    expect(unSaveMock).toHaveBeenCalledTimes(1);
    expect(unSaveMock).toHaveBeenCalledWith(target);

    rerender(<FavoritesSection initialFavorites={[target, other] as any} />);

    expect(screen.queryByText("乃木神社")).not.toBeInTheDocument();
    expect(screen.getByText("伊勢山皇大神宮")).toBeInTheDocument();
    expect(screen.getByText("1件")).toBeInTheDocument();
  });
});
