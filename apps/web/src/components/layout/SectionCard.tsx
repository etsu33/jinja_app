// apps/web/src/components/layout/SectionCard.tsx
import type { ReactNode } from "react";

type Props = {
  title?: string;
  description?: string;
  children: ReactNode;
};

export function SectionCard({ title, description, children }: Props) {
  return (
    <section className="px-2 py-10 sm:px-4 sm:py-12">
      {/* 繊細な区切り線 */}
      <div className="mx-auto mb-8 h-px w-16 bg-border/50 sm:mb-10" />
      
      {(title || description) && (
        <header className="mb-6 space-y-2 text-center sm:mb-8">
          {title && (
            <h2 className="text-xs font-medium uppercase tracking-[0.15em] text-foreground/70">
              {title}
            </h2>
          )}
          {description && (
            <p className="text-sm leading-relaxed text-muted-foreground">
              {description}
            </p>
          )}
        </header>
      )}
      {children}
    </section>
  );
}
