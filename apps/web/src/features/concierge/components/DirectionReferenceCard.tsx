import {
  directionReferenceMatchCopy,
  type DirectionReference,
} from "../../../../../../packages/shared/directionReference";

export default function DirectionReferenceCard({ reference }: { reference?: DirectionReference | null }) {
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
