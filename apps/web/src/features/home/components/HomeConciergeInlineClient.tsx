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
        /* Hero Section - 静かだが導線が明確 */
        <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 py-12 sm:min-h-[45vh] sm:py-16">
          {/* ブランドマーク - 小さく控えめに */}
          <p className="mb-8 text-[10px] font-light uppercase tracking-[0.3em] text-muted-foreground/40 sm:mb-10">
            KAMI MUSUBI
          </p>
          
          {/* メインコピー - 読みやすさを上げつつ静けさを保つ */}
          <h1 className="text-balance text-center text-xl font-light leading-relaxed tracking-wider text-foreground/90 sm:text-2xl md:text-3xl">
            静かに、自分を整える場所へ
          </h1>
          
          {/* サブコピー - より具体的な導線を示唆 */}
          <p className="mt-5 max-w-xs text-pretty text-center text-sm font-normal leading-relaxed text-muted-foreground sm:mt-6 sm:max-w-sm">
            心が少し疲れたとき、ふと立ち寄りたくなる場所がある。
            <br className="hidden sm:inline" />
            あなたの今の気持ちに寄り添う神社を見つけてみませんか。
          </p>

          {/* CTA - 視認性を上げつつ静けさを保つ */}
          <button
            type="button"
            onClick={handleOpen}
            className="mt-10 rounded-full border border-primary/40 bg-primary/8 px-7 py-3 text-sm font-normal tracking-wide text-foreground/80 transition-all duration-300 hover:border-primary/50 hover:bg-primary/12 hover:text-foreground sm:mt-12 sm:px-8"
          >
            今の気持ちから探す
          </button>

          {/* ヒントテキスト - 次のアクションを示唆 */}
          <p className="mt-6 text-xs font-light text-muted-foreground/50">
            または下へスクロールして近くの神社を探す
          </p>
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
