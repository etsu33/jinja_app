export type DirectionReference = {
  visit_date: string;
  actual_direction: string;
  reference_directions: string[];
  matched: boolean;
  calculation_method: "annual_monthly_kyusei_v1";
  note: string;
};

export function directionReferenceMatchCopy(reference: DirectionReference): string {
  return reference.matched
    ? "現在地から見た方角が、予定日の参考方位と一致しています。"
    : "現在地から見た方角は、予定日の参考方位とは異なります。";
}
