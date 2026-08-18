"use client";

// Purpose = action intent, single-select (Phase 5 brief Section 7): reuses
// the existing need_tag taxonomy as-is via compassPurposes.ts, and never
// implies purpose changes the calculated direction -- this component only
// ever calls onChange(purpose); it has no access to direction state.
//
// Primary + More presentation (docs/audit/compass-purpose-first-view-polish.md):
// Phase 6 QA found all 15 equally-weighted chips dominate the 375px first
// viewport. Initially shows COMPASS_PRIMARY_PURPOSE_COUNT purposes (ordered
// by the existing backend NEED_PRIORITY ranking); the rest are one tap away
// via a toggle mirroring ConciergeEntryCard.tsx's existing expand/collapse
// chip pattern, never permanently hidden. If the current value lives in the
// "more" set, the list stays fully expanded and the toggle is not shown --
// collapsing would otherwise hide the user's own selection with no trace.
import { useState } from "react";
import { COMPASS_PRIMARY_PURPOSE_COUNT, COMPASS_PURPOSES_ORDERED, COMPASS_PURPOSE_LABELS_JA } from "../compassPurposes";
import type { CompassPurpose } from "../types";

export type CompassPurposeSelectorProps = {
  value: CompassPurpose | null;
  onChange: (purpose: CompassPurpose) => void;
};

export default function CompassPurposeSelector({ value, onChange }: CompassPurposeSelectorProps) {
  const [expanded, setExpanded] = useState(false);

  const primaryPurposes = COMPASS_PURPOSES_ORDERED.slice(0, COMPASS_PRIMARY_PURPOSE_COUNT);
  const morePurposes = COMPASS_PURPOSES_ORDERED.slice(COMPASS_PRIMARY_PURPOSE_COUNT);
  const selectionInMore = value !== null && morePurposes.includes(value);
  const showAll = expanded || selectionInMore;
  const visiblePurposes = showAll ? COMPASS_PURPOSES_ORDERED : primaryPurposes;

  return (
    <fieldset className="min-w-0">
      <legend className="mb-2 text-sm font-medium text-[var(--kt-color-text-secondary)]">目的</legend>
      <div role="radiogroup" aria-label="参拝の目的" className="flex flex-wrap gap-2">
        {visiblePurposes.map((purpose) => {
          const selected = value === purpose;
          return (
            <button
              key={purpose}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(purpose)}
              className={[
                "min-h-11 rounded-[var(--kt-radius-pill)] border px-3 py-1.5 text-sm font-semibold transition",
                selected
                  ? "border-[var(--kt-color-action-primary)] bg-[var(--kt-color-action-primary)] text-[var(--kt-color-action-primary-text)]"
                  : "border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-background-subtle)]",
              ].join(" ")}
            >
              {COMPASS_PURPOSE_LABELS_JA[purpose]}
            </button>
          );
        })}
      </div>

      {morePurposes.length > 0 && !selectionInMore ? (
        <button
          type="button"
          className="mt-2 text-xs font-medium text-[var(--kt-color-text-muted)] underline-offset-2 hover:text-[var(--kt-color-text-secondary)] hover:underline"
          onClick={() => setExpanded((prev) => !prev)}
          aria-expanded={expanded}
        >
          {expanded ? "目的を閉じる" : `その他の目的を見る（他${morePurposes.length}件）`}
        </button>
      ) : null}
    </fieldset>
  );
}
