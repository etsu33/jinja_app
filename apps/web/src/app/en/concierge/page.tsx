import type { Metadata } from "next";

import TravelConciergeClient from "./TravelConciergeClient";

// 英語の相談ページ（限定公開）。リンクは置かず、検索にも出さない。
// 並び順はまだ日本語版（need）と同じで、結果のカードも日本語のまま（英語表示は次の段）。
export const metadata: Metadata = {
  title: "Find a shrine (preview) | KAMI MUSUBI",
  robots: { index: false, follow: false },
};

export default function EnConciergePage() {
  return <TravelConciergeClient />;
}
