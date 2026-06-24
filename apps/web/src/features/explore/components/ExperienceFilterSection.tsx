

"use client";

export const VISIT_STYLE_TAGS = ["静か", "自然", "駅近", "ひとり", "落ち着く"] as const;
export const HISTORY_THEME_TAGS = ["縁結び", "武運", "商売", "学問", "稲荷", "八幡"] as const;

type ExperienceFilterSectionProps = {
  activeTag: string;
  onSelectTag: (tag: string) => void;
};

export function ExperienceFilterSection({ activeTag, onSelectTag }: ExperienceFilterSectionProps) {
  return (
    <section className="rounded-3xl border border-stone-200/25 bg-stone-50/30 p-4">
      <div className="space-y-1">
        <p className="text-[11px] font-medium tracking-[0.2em] text-stone-500">EXPERIENCE</p>
        <h2 className="text-sm font-medium text-stone-800">どんな時間を過ごしたいですか</h2>
      </div>

      <div className="mt-4 space-y-4">
        <FilterTagGroup title="過ごし方" tags={VISIT_STYLE_TAGS} activeTag={activeTag} onSelectTag={onSelectTag} />
        <FilterTagGroup title="歴史テーマ" tags={HISTORY_THEME_TAGS} activeTag={activeTag} onSelectTag={onSelectTag} />
      </div>
    </section>
  );
}

type FilterTagGroupProps = {
  title: string;
  tags: readonly string[];
  activeTag: string;
  onSelectTag: (tag: string) => void;
};

function FilterTagGroup({ title, tags, activeTag, onSelectTag }: FilterTagGroupProps) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-medium text-stone-500">{title}</p>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => {
          const isActive = tag === activeTag;

          return (
            <button
              key={tag}
              type="button"
              aria-pressed={isActive}
              onClick={() => onSelectTag(tag)}
              className={[
                "rounded-full border px-3 py-1.5 text-xs font-medium transition",
                isActive
                  ? "border-emerald-200/70 bg-emerald-50/80 text-emerald-700"
                  : "border-stone-200/40 bg-white/65 text-stone-600 hover:bg-stone-100/45",
              ].join(" ")}
            >
              {tag}
            </button>
          );
        })}
      </div>
    </div>
  );
}
