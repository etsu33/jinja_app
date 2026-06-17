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
    <div className="inline-flex rounded-full border border-stone-200/40 bg-white/65 p-1">
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
              isActive ? "bg-emerald-50 text-emerald-700" : "text-stone-500 hover:bg-stone-50",
            ].join(" ")}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
