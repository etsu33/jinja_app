// apps/mobile/lib/shrineStorage.ts
import { SHRINES } from "../data/shrines";
import { get } from "./http";
import { getFavorites, getRecents } from "./storage";

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

type ShrineApiResponse = {
  id: number | string;
  name?: string;
  name_jp?: string;
  address?: string;
  prefecture?: string;
  imageUrl?: string;
  image_url?: string;
  rating?: number;
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

function toRecentShrineItemFromApi(shrine: ShrineApiResponse): RecentShrineItem {
  return {
    id: shrine.id,
    name: shrine.name_jp ?? shrine.name ?? "名称未設定の神社",
    address: shrine.prefecture ?? shrine.address ?? "",
    rating: shrine.rating,
    photo_url: shrine.imageUrl ?? shrine.image_url,
    popularity: shrine.popularity,
  };
}

async function resolveShrineById(id: number | string): Promise<RecentShrineItem | undefined> {
  const localShrine = findShrineById(id);
  if (localShrine) return toRecentShrineItem(localShrine);

  try {
    const apiShrine = await get<ShrineApiResponse>(`/shrines/${id}/`);
    return toRecentShrineItemFromApi(apiShrine);
  } catch {
    return undefined;
  }
}

export async function getFavoriteShrines(): Promise<RecentShrineItem[]> {
  const ids = await getFavorites();
  const items = await Promise.all(ids.map(resolveShrineById));

  return items.filter((shrine): shrine is RecentShrineItem => shrine !== undefined);
}

export async function getRecentViewed(limit = 10): Promise<RecentShrineItem[]> {
  const ids = await getRecents();
  const items = await Promise.all(ids.slice(0, limit).map(resolveShrineById));

  return items.filter((shrine): shrine is RecentShrineItem => shrine !== undefined);
}
