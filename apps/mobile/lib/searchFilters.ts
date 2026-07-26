// apps/mobile/lib/searchFilters.ts
// Home→Search間で受け渡す`filters`クエリパラメータの構築・解析と、
// Search画面の神社一覧フィルタリングを担う純粋関数。
//
// Homeから渡してよい値は、Search側の既存フィルター処理(SHRINES.tags / prefecture)と
// 意味が一致する既存の固定ラベル(ご利益)のみに限定する。自由入力・個人情報はここでは扱わない
// (docs/product/mobile-user-flow.md 8節・10節、docs/audit/mobile-user-flow-inventory.md 12.8節)。
import type { Shrine } from "../data/shrines";

const MAX_FILTER_VALUES = 10;
const MAX_FILTER_VALUE_LENGTH = 50;

// Home側で選択された安全な固定値から、`filters`クエリパラメータの値を組み立てる。
// 未選択(undefined)・空文字は除外し、有効な値が1件もなければundefinedを返す
// (Search側は`filters`パラメータなしを「条件なし」として扱う)。
export function buildSearchFilters(values: Array<string | undefined>): string | undefined {
  const normalized = parseSearchFilters(values.filter((value): value is string => Boolean(value)).join(","));
  return normalized.length > 0 ? normalized.join(",") : undefined;
}

// Search画面が受け取る`filters`クエリパラメータ(カンマ区切り文字列)を解析する。
// Search画面はURLから直接開かれる可能性があるため、空値・重複値を除去し、
// 想定外に大きい入力(値の件数・値自体の長さ)を無視することで安全に扱う。
export function parseSearchFilters(filters?: string | null): string[] {
  if (!filters) return [];

  const seen = new Set<string>();
  const result: string[] = [];

  for (const raw of filters.split(",")) {
    const value = raw.trim();
    if (!value || value.length > MAX_FILTER_VALUE_LENGTH || seen.has(value)) continue;

    seen.add(value);
    result.push(value);
    if (result.length >= MAX_FILTER_VALUES) break;
  }

  return result;
}

export type ShrineListFilter = {
  query?: string;
  filters?: string;
};

// Search画面の神社一覧フィルタリング(既存ロジックをそのまま踏襲)。
// query: 神社名・タグ・都道府県への部分一致(大文字小文字を区別しない)。
// filters: 選択された値すべてが、タグまたは都道府県のいずれかに一致すること(AND)。
export function filterShrines(shrines: Shrine[], { query, filters }: ShrineListFilter): Shrine[] {
  const normalizedQuery = (query ?? "").toLowerCase();
  const selected = parseSearchFilters(filters);

  return shrines.filter((shrine) => {
    const textHit =
      !normalizedQuery ||
      shrine.name.toLowerCase().includes(normalizedQuery) ||
      shrine.tags.some((tag) => tag.toLowerCase().includes(normalizedQuery)) ||
      (shrine.prefecture ?? "").toLowerCase().includes(normalizedQuery);

    const tagsHit = selected.length === 0 || selected.every((sel) => shrine.tags.includes(sel) || shrine.prefecture === sel);

    return textHit && tagsHit;
  });
}
