import type { Metadata } from "next";

import EnShrineDetailClient from "./EnShrineDetailClient";

// 英語の神社詳細（限定公開）。ナビにリンクは置かず、検索にも出さない（/en/concierge と同じ）。
// ログインなしで見られる。
export const metadata: Metadata = {
  title: "Shrine (preview) | KAMI MUSUBI",
  robots: { index: false, follow: false },
};

type Props = {
  params: Promise<{ id: string }>;
};

export default async function EnShrineDetailPage({ params }: Props) {
  const { id } = await params;
  const shrineId = Number(id);
  return <EnShrineDetailClient shrineId={Number.isInteger(shrineId) && shrineId > 0 ? shrineId : null} />;
}
