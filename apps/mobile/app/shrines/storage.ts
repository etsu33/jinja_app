// apps/mobile/app/shrines/storage.ts
import { getRecents } from "../../lib/storage";
import { SHRINES } from "../../data/shrines";

type ShrineSourceItem = {
  id: number | string;
  name: string;
  prefecture?: string;
  address?: string;
  rating?: number;
  imageUrl?: string;
  photo_url?: string;
  popularity?: number;
};

export type RecentShrineItem = {
  id: number | string;
  name: string;
  address: string;
  rating?: number;
  photo_url?: string;
  popularity?: number;
};

function findShrineById(id: number | string): ShrineSourceItem | undefined {
  return (SHRINES as ShrineSourceItem[]).find(
    (shrine) => String(shrine.id) === String(id),
  );
}

function toRecentShrineItem(shrine: ShrineSourceItem): RecentShrineItem {
  return {
    id: shrine.id,
    name: shrine.name,
    address: shrine.prefecture ?? shrine.address ?? "",
    rating: shrine.rating,
    photo_url: shrine.imageUrl ?? shrine.photo_url,
    popularity: shrine.popularity,
  };
}

export async function getFavoriteShrines(): Promise<RecentShrineItem[]> {
  const { getFavorites } = await import("../../lib/storage");
  const ids = await getFavorites();

  return ids
    .map(findShrineById)
    .filter((shrine): shrine is ShrineSourceItem => shrine !== undefined)
    .map(toRecentShrineItem);
}

export async function getRecentViewed(
  limit = 10,
): Promise<RecentShrineItem[]> {
  const ids = await getRecents();

  return ids
    .map(findShrineById)
    .filter((shrine): shrine is ShrineSourceItem => shrine !== undefined)
    .slice(0, limit)
    .map(toRecentShrineItem);
}
