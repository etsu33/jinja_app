import {
  directionReferenceMatchCopy,
  type DirectionReference,
} from "../../../../../../packages/shared/directionReference";
import { useEffect, useId, useRef } from "react";
import { trackWebDirection } from "@/lib/analytics/directionEvents";

export default function DirectionReferenceCard({ reference, recommendationKey = "unknown", rank }: { reference?: DirectionReference | null; recommendationKey?: string | number; rank?: number }) {
  const headingId = useId();
  const impressed = useRef(false);
  useEffect(() => { if (!reference || impressed.current) return; impressed.current = true; trackWebDirection("direction_match_impression", { matched: reference.matched, recommendation_rank: rank }); }, [reference, recommendationKey, rank]);
  if (!reference) return null;

  return (
    <aside aria-labelledby={headingId} className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-700">
      <h3 id={headingId} className="font-semibold text-stone-800">方位の参考情報</h3>
      <p className="mt-1">現在地から見た方角：{reference.actual_direction}</p>
      <p>予定日の参考方位：{reference.reference_directions.join("・")}</p>
      <p className="mt-1">{directionReferenceMatchCopy(reference)}</p>
      <p className="mt-1 text-stone-500">{reference.note}</p>
    </aside>
  );
}
