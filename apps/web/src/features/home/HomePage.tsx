// apps/web/src/features/home/HomePage.tsx


import { Suspense } from "react";
import { HomeToastClient } from "@/features/home/components/HomeToastClient";
import { HomeMainClient } from "@/features/home/components/HomeMainClient";

export default function HomePage() {
  return (
    <div className="min-h-0 bg-background">
      <HomeToastClient />

      <div className="mx-auto flex w-full max-w-3xl flex-col gap-12 px-5 py-12 sm:px-6 sm:py-16">
        <Suspense fallback={null}>
          <HomeMainClient />
        </Suspense>
      </div>
    </div>
  );
}
// HomePage (Server Component)
// - データ取得や状態管理はしない
// - HomeMainClient 等の Client を並べるだけ
