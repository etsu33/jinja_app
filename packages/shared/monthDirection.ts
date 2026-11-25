// コンシェルジュの結果に添える「今月の方角」（Web・モバイル共通）。
//
// ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」（2026-11-26 決定）:
// - 生年月日を登録したログイン中の人の、日本語の相談のときだけ Backend が返す
// - 結果の上に1回だけ month_direction を出し、コンパスへの導線を置く
// - in_month_direction: true の神社にだけ「今月の方角」の印を付ける
// - 合わない神社には何も書かない（「方角が違う」とは表示しない）。凶方位は扱わない
// - 並び順・推薦理由には使わない
//
// Backend: backend/temples/services/concierge_month_direction.py

export type ConciergeMonthDirection = {
  reference_directions: string[];
  calculation_method: "annual_monthly_kyusei_v1" | "monthly_kyusei_v1";
  target_date: string;
  note: string;
};

const DIRECTION_LABELS = new Set(["北", "北東", "東", "南東", "南", "南西", "西", "北西"]);
const CALCULATION_METHODS = new Set(["annual_monthly_kyusei_v1", "monthly_kyusei_v1"]);

export function normalizeMonthDirection(value: unknown): ConciergeMonthDirection | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Partial<ConciergeMonthDirection>;
  if (!Array.isArray(raw.reference_directions)) return null;
  const directions = raw.reference_directions.filter(
    (direction): direction is string => typeof direction === "string" && DIRECTION_LABELS.has(direction),
  );
  if (directions.length === 0) return null;
  if (typeof raw.calculation_method !== "string" || !CALCULATION_METHODS.has(raw.calculation_method)) return null;
  return {
    reference_directions: directions,
    calculation_method: raw.calculation_method,
    target_date: typeof raw.target_date === "string" ? raw.target_date : "",
    note: typeof raw.note === "string" ? raw.note : "",
  };
}

// true のときだけ印を付ける。false・未設定・文字列などはすべて「印なし」。
export function isInMonthDirection(recommendation: unknown): boolean {
  return Boolean(
    recommendation &&
      typeof recommendation === "object" &&
      (recommendation as { in_month_direction?: unknown }).in_month_direction === true,
  );
}

export const MONTH_DIRECTION_MARK_LABEL = "今月の方角";

export function monthDirectionSummary(monthDirection: ConciergeMonthDirection): string {
  return `今月のあなたの方角：${monthDirection.reference_directions.join("・")}`;
}

export const MONTH_DIRECTION_COMPASS_LINK_LABEL = "方角で選びたいときはコンパスへ";
