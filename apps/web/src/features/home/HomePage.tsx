// apps/web/src/features/home/HomePage.tsx


import { Suspense } from "react";
import { HomeToastClient } from "@/features/home/components/HomeToastClient";
import { HomeMainClient } from "@/features/home/components/HomeMainClient";

export default function HomePage() {
  return (
    <div className="min-h-0 bg-background">
      <HomeToastClient />

      <div className="mx-auto flex w-full max-w-3xl flex-col gap-0 px-5 pb-20 sm:px-6 sm:pb-28">
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
