// apps/web/src/components/shrine/DetailSection.tsx
"use client";

import * as React from "react";

export default function DetailSection({
  title,
  right,
  children,
  className = "",
}: {
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`space-y-4 py-6 ${className}`}>
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-xs font-medium uppercase tracking-[0.12em] text-foreground/50">{title}</h2>
        {right ? <div className="text-xs text-muted-foreground">{right}</div> : null}
      </div>
      {children}
    </section>
  );
}
