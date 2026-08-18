"use client";

// Lightweight origin interaction (Phase 5 brief Section 8): inline current
// state + a narrowly-scoped bottom Sheet for changing it, reusing the
// existing OriginSelector as-is rather than turning the main screen into a
// filter form.
import { useState } from "react";
import OriginSelector from "@/features/concierge/components/OriginSelector";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { originSelectionAnnouncement } from "../../../../../../packages/shared/directionAccessibility";
import type { UserOrigin } from "../../../../../../packages/shared/userOrigin";

export type CompassOriginSummaryProps = {
  origin: UserOrigin | null;
  onChange: (origin: UserOrigin | null) => void;
  onUseDevice: () => void;
  deviceError?: string | null;
};

export default function CompassOriginSummary({
  origin,
  onChange,
  onUseDevice,
  deviceError = null,
}: CompassOriginSummaryProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex items-center justify-between gap-3 rounded-[var(--kt-radius-panel)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-4 py-3">
      <div className="min-w-0">
        <p className="text-xs font-medium text-[var(--kt-color-text-muted)]">出発地点</p>
        <p className="truncate text-sm text-[var(--kt-color-text-primary)]">
          {originSelectionAnnouncement(origin)}
        </p>
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="min-h-11 shrink-0 rounded-[var(--kt-radius-pill)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-3 py-1.5 text-sm font-semibold text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-background-subtle)]"
        >
          変更する
        </button>
        <SheetContent side="bottom" className="max-h-[85vh] overflow-y-auto rounded-t-[var(--kt-radius-modal)] p-4">
          <SheetHeader className="p-0">
            <SheetTitle>出発地点を選ぶ</SheetTitle>
          </SheetHeader>
          <div className="mt-4">
            <OriginSelector
              origin={origin}
              onChange={(next) => {
                onChange(next);
                if (next) setOpen(false);
              }}
              onUseDevice={onUseDevice}
              deviceError={deviceError}
            />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
