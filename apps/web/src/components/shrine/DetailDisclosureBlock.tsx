// apps/web/src/components/shrine/DetailDisclosureBlock.tsx
"use client";

import * as React from "react";


type SignalLevel = "strong" | "mid" | "soft";

type Props = {
  title: string;
  summary: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  level?: "strong" | "mid" | "soft";
  hint?: string | null;
  materials?: Array<{ label: string; value: string }>;
};

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function levelLabel(level?: SignalLevel) {
  if (level === "strong") return "高";
  if (level === "soft") return "低";
  if (level === "mid") return "中";
  return "中";
}

export default function DetailDisclosureBlock({
  title,
  summary,
  defaultOpen = false,
  children,
  level,
  hint,
  materials = [],
}: Props) {
  const [open, setOpen] = React.useState(defaultOpen);
  const lv = levelLabel(level);

  return (
    <div className="overflow-hidden rounded-[var(--kt-radius-card)] border bg-[var(--kt-color-surface-default)]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn("w-full px-4 py-3 text-left", "flex items-start justify-between gap-3", "hover:bg-[var(--kt-color-background-subtle)]")}
        aria-expanded={open}
      >
        {materials.length ? (
          <div className="shrink-0 rounded-[var(--kt-radius-panel)] border bg-[var(--kt-color-surface-default)] p-3">
            <div className="text-xs font-semibold text-[var(--kt-color-text-secondary)]">材料</div>
            <ul className="mt-2 space-y-1 text-xs text-[var(--kt-color-text-secondary)]">
              {materials.map((m) => (
                <li key={m.label}>
                  {m.label}：{m.value}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="truncate text-sm font-semibold text-[var(--kt-color-text-primary)]">{title}</div>
            {lv ? (
              <span className="shrink-0 rounded-[var(--kt-radius-pill)] bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-[var(--kt-color-text-secondary)]">
                {lv}
              </span>
            ) : null}
          </div>
          <div className="mt-1 line-clamp-2 text-xs text-slate-600">{summary}</div>
        </div>

        <span
          className={cn("size-4 transition-transform duration-200", open ? "rotate-0" : "rotate-180")}
          aria-hidden="true"
        >
          ▼
        </span>
      </button>

      {open ? (
        <div className="border-t bg-[var(--kt-color-surface-default)] px-4 pb-4 pt-3">
          {hint ? <div className="mb-3 text-xs text-[var(--kt-color-text-muted)]">{hint}</div> : null}
          {children}
        </div>
      ) : null}
    </div>
  );
}
