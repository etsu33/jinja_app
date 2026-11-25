// apps/web/src/components/layout/SectionCard.tsx
import type { ReactNode } from "react";

type Props = {
  title?: string;
  description?: string;
  variant?: "default" | "subtle";
  children: ReactNode;
};

export function SectionCard({ title, description, variant = "default", children }: Props) {
  const sectionClassName =
    variant === "subtle"
      ? "space-y-4 rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-5 shadow-none sm:p-6"
      : "space-y-4 rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-6 shadow-none";

  return (
    <section className={sectionClassName}>
      {(title || description) && (
        <header>
          {title && <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{title}</h2>}
          {description && <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-muted)]">{description}</p>}
        </header>
      )}
      {children}
    </section>
  );
}
