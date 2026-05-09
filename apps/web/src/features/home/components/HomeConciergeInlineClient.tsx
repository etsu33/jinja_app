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
        /* Hero Section - 静かなエディトリアル空間 */
        <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-16 sm:min-h-[55vh] sm:py-20">
          {/* 装飾的な縦線 - 神社の鳥居をイメージ */}
          <div className="mb-12 h-12 w-px bg-gradient-to-b from-transparent via-primary/30 to-primary/50 sm:mb-16 sm:h-16" />
          
          {/* メインコピー - 大きく静かに */}
          <h1 className="text-balance text-center text-2xl font-extralight leading-loose tracking-widest text-foreground/85 sm:text-3xl md:text-4xl">
            静かに、自分を整える場所へ
          </h1>
          
          {/* サブコピー - 余白を大きく */}
          <p className="mt-8 max-w-sm text-pretty text-center text-sm font-light leading-loose tracking-wide text-muted-foreground/80 sm:mt-10 sm:max-w-md sm:text-base">
            心が少し疲れたとき、
            <br />
            ふと立ち寄りたくなる場所がある
          </p>

          {/* CTA - 控えめだが存在感 */}
          <button
            type="button"
            onClick={handleOpen}
            className="mt-14 rounded-full border border-primary/25 bg-transparent px-7 py-3 text-sm font-light tracking-wider text-foreground/70 transition-all duration-500 hover:border-primary/40 hover:bg-primary/5 hover:text-foreground/90 sm:mt-16 sm:px-8"
          >
            今の気持ちから探す
          </button>

          {/* 下部の装飾線 */}
          <div className="mt-14 h-8 w-px bg-gradient-to-b from-primary/40 to-transparent sm:mt-16 sm:h-10" />
        </div>
      ) : (
        <div className="relative px-1 py-4 sm:px-2 sm:py-6">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <p className="text-sm font-light tracking-wide text-foreground/60">今の気持ちから探す</p>
              <button 
                type="button" 
                onClick={onClose} 
                className="text-xs font-light text-muted-foreground/70 transition-colors hover:text-foreground"
              >
                戻る
              </button>
            </div>

            <ConciergeClient embedMode />
          </div>
        </div>
      )}
    </div>
  );
}
