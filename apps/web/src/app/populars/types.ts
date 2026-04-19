/**
 * GET /api/populars/（BFF→Backend）で返る神社行の最小形。
 * Backend: ShrineListSerializer（一覧で使うフィールド）
 */
export type PopularShrineRow = {
  id: number;
  name_jp: string;
  kind?: string;
  address?: string;
  latitude?: number | null;
  longitude?: number | null;
};

/** DRF ページネーション付き一覧（populars で一般的） */
export type PopularShrinesPaginatedBody = {
  count: number;
  next: string | null;
  previous: string | null;
  results: PopularShrineRow[];
};

/** OpenAPI の PopularsResponse や配列直下など、実装上ありうる形 */
export type PopularShrinesResponseBody =
  | PopularShrinesPaginatedBody
  | PopularShrineRow[]
  | { results?: PopularShrineRow[]; items?: PopularShrineRow[] };
