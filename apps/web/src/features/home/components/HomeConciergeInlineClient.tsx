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
        /* Hero Section - 静かだが信頼感のある導線 */
        <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 py-12 sm:min-h-[45vh] sm:py-16">
          {/* ブランドマーク */}
          <p className="mb-8 text-[10px] font-medium uppercase tracking-[0.25em] text-muted-foreground/70 sm:mb-10">
            KAMI MUSUBI
          </p>
          
          {/* メインコピー */}
          <h1 className="text-balance text-center text-xl font-normal leading-relaxed tracking-wide text-foreground sm:text-2xl md:text-3xl">
            静かに、自分を整える場所へ
          </h1>
          
          {/* サブコピー */}
          <p className="mt-5 max-w-xs text-pretty text-center text-sm leading-relaxed text-muted-foreground sm:mt-6 sm:max-w-sm">
            心が少し疲れたとき、ふと立ち寄りたくなる場所がある。
            <br className="hidden sm:inline" />
            あなたの今の気持ちに寄り添う神社を見つけてみませんか。
          </p>

          {/* CTA - 明確な視認性 */}
          <button
            type="button"
            onClick={handleOpen}
            className="mt-10 rounded-full border border-primary/50 bg-primary/10 px-7 py-3 text-sm font-medium tracking-wide text-foreground/90 transition-all duration-300 hover:border-primary/60 hover:bg-primary/15 hover:text-foreground sm:mt-12 sm:px-8"
          >
            今の気持ちから探す
          </button>

          {/* ヒントテキスト */}
          <p className="mt-6 text-xs text-muted-foreground/70">
            または下へスクロールして近くの神社を探す
          </p>
        </div>
      ) : (
        <div className="relative px-1 py-6 sm:px-2 sm:py-8">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium tracking-wide text-foreground/80">今の気持ちから探す</p>
              <button 
                type="button" 
                onClick={onClose} 
                className="text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
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
