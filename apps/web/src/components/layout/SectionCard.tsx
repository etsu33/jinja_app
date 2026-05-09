// apps/web/src/components/layout/SectionCard.tsx
import type { ReactNode } from "react";

type Props = {
  title?: string;
  description?: string;
  children: ReactNode;
};

export function SectionCard({ title, description, children }: Props) {
  return (
    <section className="space-y-6 px-2 py-8 sm:px-4 sm:py-10">
      {/* 繊細な区切り線 - 和の静けさ */}
      <div className="mx-auto h-px w-12 bg-gradient-to-r from-transparent via-border/50 to-transparent" />
      
      {(title || description) && (
        <header className="space-y-2 text-center">
          {title && (
            <h2 className="text-xs font-light uppercase tracking-[0.2em] text-muted-foreground/60">
              {title}
            </h2>
          )}
          {description && (
            <p className="text-sm font-light leading-relaxed tracking-wide text-foreground/50">
              {description}
            </p>
          )}
        </header>
      )}
      {children}
    </section>
  );
}
