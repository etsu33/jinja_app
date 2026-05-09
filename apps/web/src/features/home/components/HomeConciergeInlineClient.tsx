// apps/web/src/features/home/components/HomeConciergeInlineClient.tsx
"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef } from "react";

const ConciergeClient = dynamic(() => import("@/app/concierge/ConciergeClient"), {
  ssr: false,
  loading: () => <div className="rounded-xl bg-card p-4 text-sm text-muted-foreground">読み込み中…</div>,
});

type Props = {
  className?: string;
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
};

export function HomeConciergeInlineClient({ className, open, onOpen, onClose }: Props) {
  const topRef = useRef<HTMLDivElement | null>(null);

  // closeイベント受けたら確実に閉じる（親へ委譲）
  useEffect(() => {
    const onCloseEvt = () => {
   
      onClose();
    };
    window.addEventListener("jinja:close-concierge", onCloseEvt);
    return () => window.removeEventListener("jinja:close-concierge", onCloseEvt);
  }, [onClose]);

  const handleOpen = () => {
    onOpen();

    requestAnimationFrame(() => {
      topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      window.dispatchEvent(new Event("concierge:focus-input"));
    });
  };

  return (
    <div className={className}>
      <div ref={topRef} />

      {!open ? (
        /* Hero Section - 静かで感情的なデザイン */
        <div className="flex flex-col items-center text-center">
          {/* メインコピー */}
          <h1 className="text-balance text-2xl font-light leading-relaxed tracking-wide text-foreground/90 sm:text-3xl">
            静かに、自分を整える場所へ
          </h1>
          
          <p className="mt-4 max-w-md text-pretty text-sm leading-relaxed text-muted-foreground">
            心が少し疲れたとき、ふと立ち寄りたくなる場所がある。
            <br className="hidden sm:inline" />
            あなたの今の気持ちに寄り添う神社を、見つけてみませんか。
          </p>

          {/* 単一の主役CTA - soft sage green */}
          <button
            type="button"
            onClick={handleOpen}
            className="mt-10 rounded-full border border-accent/40 bg-accent/30 px-8 py-3.5 text-sm font-medium text-accent-foreground transition-all duration-300 hover:border-accent/60 hover:bg-accent/50"
          >
            今の気持ちから探す
          </button>

          {/* サブテキスト */}
          <p className="mt-4 text-xs text-muted-foreground/70">
            位置情報から、近くの神社もお探しできます
          </p>
        </div>
      ) : (
        <div className="relative">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground/70">今の気持ちから探す</p>
              <button 
                type="button" 
                onClick={onClose} 
                className="text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                閉じる
              </button>
            </div>

            <ConciergeClient embedMode />
          </div>
        </div>
      )}
    </div>
  );
}
