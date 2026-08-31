"use client";

import * as React from "react";

// `primary` / `secondary` / `tertiary` are surface tiers (border + bg + shadow).
// `plain` is a borderless editorial section: no surface at all, just an <h2> and
// content, meant to sit in a whitespace-separated reading flow. It carries the
// same strong heading weight as `primary` but draws no container -- separation is
// the parent's spacing responsibility (e.g. `space-y-6`), not a box.
// Additive only: existing callers and the default (`secondary`) are unchanged.
export type DetailSectionVariant = "primary" | "secondary" | "tertiary" | "plain";

const SECTION_CLASS: Record<DetailSectionVariant, string> = {
  primary: "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] p-6 shadow-[var(--kt-shadow-high)]",
  secondary: "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-5 shadow-[var(--kt-shadow-medium)]",
  tertiary: "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-4",
  plain: "",
};

const TITLE_CLASS: Record<DetailSectionVariant, string> = {
  primary: "text-base font-semibold text-[var(--kt-color-text-primary)]",
  secondary: "text-sm font-semibold text-[var(--kt-color-text-primary)]",
  tertiary: "text-xs font-semibold text-[var(--kt-color-text-muted)]",
  plain: "text-base font-semibold text-[var(--kt-color-text-primary)]",
};

const RIGHT_CLASS: Record<DetailSectionVariant, string> = {
  primary: "text-xs text-[var(--kt-color-text-muted)]",
  secondary: "text-xs text-[var(--kt-color-text-muted)]",
  tertiary: "text-[11px] text-slate-400",
  plain: "text-xs text-[var(--kt-color-text-muted)]",
};

export default function DetailSection({
  title,
  right,
  children,
  className = "",
  variant = "secondary",
}: {
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  variant?: DetailSectionVariant;
}) {
  return (
    <section className={`${SECTION_CLASS[variant]} ${className}`.trim()}>
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className={TITLE_CLASS[variant]}>{title}</h2>
        {right ? <div className={RIGHT_CLASS[variant]}>{right}</div> : null}
      </div>
      {children}
    </section>
  );
}
