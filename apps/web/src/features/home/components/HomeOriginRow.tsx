"use client";

// トップページの相談の欄の下に置く「出発地」の1行（2026-11-23）。
// - 1行だけを見せ、押したときに下から選択肢（既存の OriginSelector）を出す
// - 選ばなくても相談できる（任意）
// - 位置情報の許可は「現在地を使用」を押したときだけ聞く（開いた瞬間には聞かない）
import { useState } from "react";
import { MapPin } from "lucide-react";

import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import OriginSelector from "@/features/concierge/components/OriginSelector";
import { trackWebDirection } from "@/lib/analytics/directionEvents";
import type { UserOrigin } from "../../../../../../packages/shared/userOrigin";

type Props = {
  origin: UserOrigin | null;
  onChange: (origin: UserOrigin | null) => void;
};

export function homeOriginLabel(origin: UserOrigin | null): string {
  if (!origin) return "出発地を選ぶ（任意）";
  const name = origin.displayName?.trim() || "現在地";
  return `${name}から`;
}

export default function HomeOriginRow({ origin, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [deviceError, setDeviceError] = useState<string | null>(null);

  const useDevice = () => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setDeviceError("このブラウザでは現在地を取得できません。");
      return;
    }
    setDeviceError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        onChange({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          source: "device",
          displayName: "現在地",
          accuracy: "precise",
        });
        trackWebDirection("direction_origin_result", { origin_type: "device", result: "success" });
        setOpen(false);
      },
      (error) => {
        setDeviceError("現在地を取得できませんでした。位置情報の許可を確認してください。");
        trackWebDirection("direction_origin_result", {
          origin_type: "device",
          result: error.code === 1 ? "denied" : "failed",
        });
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 },
    );
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <button
        type="button"
        data-testid="home-origin-row"
        onClick={() => setOpen(true)}
        className="inline-flex min-h-11 items-center gap-1.5 px-1 text-xs font-medium text-[var(--home-text-secondary)] transition hover:text-[var(--kt-color-action-primary)]"
        aria-haspopup="dialog"
      >
        <MapPin
          className={origin ? "size-3.5 text-[var(--kt-color-action-primary)]" : "size-3.5"}
          aria-hidden
        />
        <span className={origin ? "text-[var(--home-text-primary)]" : undefined}>{homeOriginLabel(origin)}</span>
      </button>
      <SheetContent side="bottom" className="max-h-[85vh] overflow-y-auto rounded-t-[var(--kt-radius-modal)] p-4">
        <SheetHeader className="p-0">
          <SheetTitle>出発地を選ぶ</SheetTitle>
        </SheetHeader>
        <p className="mt-1 text-xs leading-5 text-[var(--kt-color-text-muted)]">
          選ぶと、近くの神社から提案します。選ばなくても相談できます。
        </p>
        <div className="mt-4">
          <OriginSelector
            origin={origin}
            onChange={(next) => {
              onChange(next);
              if (next) setOpen(false);
            }}
            onUseDevice={useDevice}
            deviceError={deviceError}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
