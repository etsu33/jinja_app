// apps/web/src/features/home/components/HomeMainClient.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { SectionCard } from "@/components/layout/SectionCard";
import { HomeConciergeInlineClient } from "./HomeConciergeInlineClient";
import { HomeNearbySection } from "./HomeNearbySection";
// TODO: バックエンド実装完了後に復活
// import HomeGoshuinFeedSection from "@/features/home/components/HomeGoshuinFeedSection";

export function HomeMainClient() {
  const [conciergeOpen, setConciergeOpen] = useState(false);
  const savedScrollYRef = useRef(0);

  const openConcierge = () => {
    savedScrollYRef.current = window.scrollY;
    setConciergeOpen(true);
  };

  const closeConcierge = () => {
    setConciergeOpen(false);
  };

  // ✅ ロゴ等から送られる close をホームで受ける
  useEffect(() => {
    const onClose = () => {
      closeConcierge();
    };
    window.addEventListener("jinja:close-concierge", onClose);
    return () => window.removeEventListener("jinja:close-concierge", onClose);
  }, []);

  // ✅ 戻る/復帰時も閉じる（Safari系の変挙動対策）
  useEffect(() => {
    const onPageShow = () => closeConcierge();
    window.addEventListener("pageshow", onPageShow);
    return () => window.removeEventListener("pageshow", onPageShow);
  }, []);

  // ✅ 閉じたら元のスクロールに戻す（“戻った感”を作る）
  useEffect(() => {
    if (conciergeOpen) return;
    window.scrollTo({ top: savedScrollYRef.current, behavior: "auto" });
  }, [conciergeOpen]);

  return (
    <>
      {/* Hero - カードで囲まず開放的な空間に */}
      <HomeConciergeInlineClient open={conciergeOpen} onOpen={openConcierge} onClose={closeConcierge} />

      {/* 
        TODO: 御朱印フィードは バックエンド実装完了後に復活予定
        優先導線: Hero → コンシェルジュ → 推薦結果 → 神社詳細 → 経路案内
        
        <SectionCard 
          title="みんなの御朱印" 
          description="最近記録された御朱印をご覧いただけます"
        >
          <HomeGoshuinFeedSection limit={12} />
        </SectionCard>
      */}

      {!conciergeOpen && (
        <SectionCard title="近くの神社">
          <HomeNearbySection />
        </SectionCard>
      )}
    </>
  );
}
