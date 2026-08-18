"use client";

// Purpose = action intent, single-select (Phase 5 brief Section 7): reuses
// the existing need_tag taxonomy as-is via compassPurposes.ts, and never
// implies purpose changes the calculated direction -- this component only
// ever calls onChange(purpose); it has no access to direction state.
import { COMPASS_PURPOSES, COMPASS_PURPOSE_LABELS_JA } from "../compassPurposes";
import type { CompassPurpose } from "../types";

export type CompassPurposeSelectorProps = {
  value: CompassPurpose | null;
  onChange: (purpose: CompassPurpose) => void;
};

export default function CompassPurposeSelector({ value, onChange }: CompassPurposeSelectorProps) {
  return (
    <fieldset className="min-w-0">
      <legend className="mb-2 text-sm font-medium text-[var(--kt-color-text-secondary)]">目的</legend>
      <div role="radiogroup" aria-label="参拝の目的" className="flex flex-wrap gap-2">
        {COMPASS_PURPOSES.map((purpose) => {
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
    </fieldset>
  );
}
