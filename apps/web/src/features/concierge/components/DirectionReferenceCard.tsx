import {
  directionReferenceMatchCopy,
  type DirectionReference,
} from "../../../../../../packages/shared/directionReference";
import { useEffect } from "react";
import { trackWebDirection } from "@/lib/analytics/directionEvents";
const impressed = new Set<string>();

export default function DirectionReferenceCard({ reference, recommendationKey = "unknown", rank }: { reference?: DirectionReference | null; recommendationKey?: string | number; rank?: number }) {
  useEffect(() => { if (!reference?.matched) return; const key = String(recommendationKey); if (impressed.has(key)) return; impressed.add(key); trackWebDirection("direction_match_impression", { matched: true, recommendation_rank: rank }); }, [reference, recommendationKey, rank]);
  if (!reference) return null;

  return (
    <aside className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-xs text-stone-600">
      <p className="font-semibold text-stone-700">方位の参考情報</p>
      <p className="mt-1">現在地から見た方角：{reference.actual_direction}</p>
      <p>予定日の参考方位：{reference.reference_directions.join("・")}</p>
      <p className="mt-1">{directionReferenceMatchCopy(reference)}</p>
      <p className="mt-1 text-stone-500">{reference.note}</p>
    </aside>
  );
}
