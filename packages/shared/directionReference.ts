export type DirectionReference = {
  visit_date: string;
  actual_direction: string;
  reference_directions: string[];
  matched: boolean;
  calculation_method: "annual_monthly_kyusei_v1";
  note: string;
};

const DIRECTION_LABELS = new Set(["北", "北東", "東", "南東", "南", "南西", "西", "北西"]);

export function isValidDirectionReference(value: unknown): value is DirectionReference {
  if (!value || typeof value !== "object") return false;
  const reference = value as Partial<DirectionReference>;
  return (
    typeof reference.visit_date === "string" && reference.visit_date.trim().length > 0 &&
    typeof reference.actual_direction === "string" && DIRECTION_LABELS.has(reference.actual_direction) &&
    Array.isArray(reference.reference_directions) &&
    reference.reference_directions.length > 0 &&
    reference.reference_directions.every((direction) => typeof direction === "string" && DIRECTION_LABELS.has(direction)) &&
    typeof reference.matched === "boolean" &&
    reference.calculation_method === "annual_monthly_kyusei_v1" &&
    typeof reference.note === "string" && reference.note.trim().length > 0
  );
}

export function validDirectionReferenceOrNull(value: unknown): DirectionReference | null {
  return isValidDirectionReference(value) ? value : null;
}

export function directionReferenceMatchCopy(reference: DirectionReference): string {
  return reference.matched
    ? "現在地から見た方角が、予定日の参考方位と一致しています。"
    : "現在地から見た方角は、予定日の参考方位とは異なります。";
}
