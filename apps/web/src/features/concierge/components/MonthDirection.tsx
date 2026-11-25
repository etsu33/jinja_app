import Link from "next/link";

import {
  MONTH_DIRECTION_COMPASS_LINK_LABEL,
  MONTH_DIRECTION_MARK_LABEL,
  monthDirectionSummary,
  type ConciergeMonthDirection,
} from "../../../../../../packages/shared/monthDirection";

// 結果の上に1回だけ出す「今月のあなたの方角」。
// 生年月日を登録したログイン中の人にだけ Backend が返す。並び順には使っていない。
export function MonthDirectionSummary({ monthDirection }: { monthDirection: ConciergeMonthDirection | null | undefined }) {
  if (!monthDirection) return null;
  return (
    <div
      data-testid="month-direction-summary"
      className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 rounded-[var(--kt-radius-panel)] border border-[var(--kt-color-border-default)] px-3 py-2 text-sm leading-6"
    >
      <span className="font-semibold text-[var(--kt-color-text-primary)]">{monthDirectionSummary(monthDirection)}</span>
      <Link
        href="/compass"
        className="text-xs font-semibold text-[var(--kt-color-text-secondary)] underline underline-offset-2"
      >
        {MONTH_DIRECTION_COMPASS_LINK_LABEL}
      </Link>
    </div>
  );
}

// 今月の方角にある神社にだけ付ける印。合わない神社には何も出さない。
export function MonthDirectionMark({ inMonthDirection }: { inMonthDirection: boolean | undefined }) {
  if (inMonthDirection !== true) return null;
  return (
    <span
      data-testid="month-direction-mark"
      className="inline-flex w-fit items-center rounded-full border border-[var(--kt-color-border-default)] px-2 py-0.5 text-xs font-semibold text-[var(--kt-color-text-secondary)]"
    >
      {MONTH_DIRECTION_MARK_LABEL}
    </span>
  );
}
