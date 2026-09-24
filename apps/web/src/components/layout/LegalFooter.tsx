// apps/web/src/components/layout/LegalFooter.tsx
//
// 全ページ共通のLegal導線。RootLayoutに一度だけ置く。
//
// 責務の分離:
//   - Home専用の HomeContactFooter とは別物。あちらは Home本文の締めくくり、
//     こちらはサイト全体の規約・ポリシーへの到達保証。
//   - 各ページが個別に巨大なLegalリンクブロックを持たないための正本。
//
// 従属性の担保:
//   - スティッキーにしない（main の内容の後ろに一度だけ現れる）
//   - 文字サイズと彩度を落とし、面も持たせない。CTAより必ず弱く見せる
// 色は既存の Semantic Token のみを使い、新規Tokenは追加しない
// （中立色は KAMI MUSUBI Worldview Token を経由して解決される）。

import Link from "next/link";

import { CONTACT_MAILTO_HREF } from "@/lib/contact";

const LINK_CLASS =
  "text-[var(--kt-color-text-secondary)] underline-offset-4 transition hover:text-[var(--kt-color-text-primary)] hover:underline";

export function LegalFooter() {
  return (
    <footer
      aria-label="規約とポリシー"
      className="mt-12 border-t border-[var(--kt-color-border-default)] px-4 py-6"
    >
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 text-xs">
        <Link href="/terms" className={LINK_CLASS}>
          利用規約
        </Link>
        <Link href="/privacy" className={LINK_CLASS}>
          プライバシーポリシー
        </Link>
        <a href={CONTACT_MAILTO_HREF} className={LINK_CLASS}>
          お問い合わせ
        </a>
      </nav>
    </footer>
  );
}

export default LegalFooter;
