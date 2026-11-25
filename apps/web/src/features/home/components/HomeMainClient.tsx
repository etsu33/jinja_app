"use client";

import { HomeHero } from "./HomeHero";
import { HomeActionGrid } from "./HomeActionGrid";

export function HomeMainClient() {
  // 縦の構成順がそのまま階層を表す:
  //   ブランド → 見出し → 相談入力カード(主CTA) → 候補チップ/条件 → 補助導線グリッド
  // 旧実装のような横幅の異なるブロックの散在(ml-2 / ml-auto / max-w-[34rem] 等)は行わない。
  //
  // 連絡導線(HomeContactFooter)はここでは描画しない。
  // RootLayout の LegalFooter が全ページ共通で同じ mailto 契約の「お問い合わせ」を
  // 本文の直後に出すため、両方を描くと Home の末尾に同じリンクが二重に並ぶ。
  // 承認済み契約そのものは @/lib/contact が正本で、HomeContactFooter は
  // 契約の回帰テストとともに残してある。
  return (
    <div className="space-y-12">
      <HomeHero />
      <HomeActionGrid />
    </div>
  );
}
