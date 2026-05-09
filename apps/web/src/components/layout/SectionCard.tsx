// apps/web/src/components/layout/SectionCard.tsx
import type { ReactNode } from "react";

type Props = {
  title?: string;
  description?: string;
  children: ReactNode;
};

export function SectionCard({ title, description, children }: Props) {
  return (
    <section className="space-y-5 rounded-xl border border-border/60 bg-card px-5 py-6 sm:px-8 sm:py-8">
      {(title || description) && (
        <header className="space-y-1">
          {title && <h2 className="text-sm font-medium text-foreground/70">{title}</h2>}
          {description && <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>}
        </header>
      )}
      {children}
    </section>
  );
}
