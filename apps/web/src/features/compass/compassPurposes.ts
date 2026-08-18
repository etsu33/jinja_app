// Reuses the existing 15 need_tag slugs (backend/temples/domain/need_tags.py)
// as-is -- Compass purpose selection is presentation copy over that same
// taxonomy, not a new one (docs/product/compass-mvp-runtime-contract.md
// Section 4: "既存 need_tag/goriyaku taxonomy をそのまま再利用可能と判定する").
// Labels for love/career/mental/rest/money/courage/study/protection/focus/
// travel_safe match backend/temples/services/concierge_chat_ranking.py's
// NEED_TAG_LABELS_JA verbatim so the same tag reads identically in
// Concierge and Compass; the remaining 5 (relationship/marriage/
// communication/health/family) had no existing label anywhere and are
// added here in the same tone.
import type { CompassPurpose } from "./types";

export const COMPASS_PURPOSES: readonly CompassPurpose[] = [
  "love",
  "relationship",
  "marriage",
  "communication",
  "career",
  "money",
  "study",
  "health",
  "mental",
  "protection",
  "courage",
  "focus",
  "rest",
  "family",
  "travel_safe",
];

export const COMPASS_PURPOSE_LABELS_JA: Record<CompassPurpose, string> = {
  love: "恋愛",
  relationship: "人間関係",
  marriage: "縁結び・結婚",
  communication: "対話・発信",
  career: "転機・仕事",
  money: "金運",
  study: "学業・合格",
  health: "健康",
  mental: "不安・心",
  protection: "厄除け・守り",
  courage: "前進・後押し",
  focus: "集中・継続",
  rest: "休息",
  family: "子宝・家族",
  travel_safe: "移動・安全",
};

export function isCompassPurpose(value: unknown): value is CompassPurpose {
  return typeof value === "string" && (COMPASS_PURPOSES as readonly string[]).includes(value);
}
