"use client";

export type ExploreViewMode = "list" | "map";

type ViewModeTabsProps = {
  value: ExploreViewMode;
  onChange: (value: ExploreViewMode) => void;
};

const VIEW_MODE_OPTIONS: readonly { value: ExploreViewMode; label: string }[] = [
  { value: "list", label: "一覧" },
  { value: "map", label: "地図" },
];

export function ViewModeTabs({ value, onChange }: ViewModeTabsProps) {
  return (
    <div className="inline-flex rounded-full border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-1">
      {VIEW_MODE_OPTIONS.map((option) => {
        const isActive = option.value === value;

        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(option.value)}
            className={[
              "rounded-full px-4 py-1.5 text-xs font-medium transition",
              // Segmented control: the selected chip sits one step lighter than the
              // track (--kt-color-background-subtle) so selection reads from the
              // surface step, not from a colour fill. Avoids introducing another
              // instance of the action-primary/white pairing on a 12px label.
              isActive
                ? "bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)]"
                : "text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-surface-default)]",
            ].join(" ")}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
