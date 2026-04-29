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
      ? "space-y-4 rounded-2xl border border-slate-100 bg-white/70 p-5 shadow-none sm:p-6"
      : "space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm";

  return (
    <section className={sectionClassName}>
      {(title || description) && (
        <header>
          {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
          {description && <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>}
        </header>
      )}
      {children}
    </section>
  );
}
