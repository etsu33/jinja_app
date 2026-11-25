// apps/web/src/app/tokushoho/page.tsx
//
// 特定商取引法に基づく表記。
//
// 記載方針:
//   - 販売事業者名は lib/legal/seller.ts の SELLER_NAME だけを読む（本名は事業者本人が入れる）。
//   - 所在地・電話番号は記載しない（請求があれば遅滞なく開示する）。推測して記載しない。
//   - 価格・有効期限は旅行パス（lib/billing/passes.ts、利用規約5章）と一致させる。
//   - 消費税の扱いは記載しない（税率の登録・Stripe Tax は使っていない＝税の上乗せは無い）。
// 色は既存の Semantic Token のみを使い、新規Tokenは追加しない。

import type { Metadata } from "next";

import { CONTACT_EMAIL, CONTACT_MAILTO_HREF } from "@/lib/contact";
import { SELLER_NAME } from "@/lib/legal/seller";

export const metadata: Metadata = {
  title: "特定商取引法に基づく表記 | KAMI MUSUBI",
  description: "KAMI MUSUBIの旅行パス（Premium）の販売事業者、価格、支払い、提供時期、返品・キャンセルについて記載します。",
};

const UNDISCLOSED = "請求があれば遅滞なく開示します";

type Row = { label: string; content: React.ReactNode };

const ROWS: Row[] = [
  { label: "販売事業者", content: SELLER_NAME },
  { label: "所在地", content: UNDISCLOSED },
  { label: "電話番号", content: UNDISCLOSED },
  {
    label: "連絡先",
    content: (
      <>
        メール：
        <a href={CONTACT_MAILTO_HREF} className="underline underline-offset-2">
          {CONTACT_EMAIL}
        </a>
      </>
    ),
  },
  {
    label: "販売価格",
    content: "1日パス 2.99米ドル／7日パス 7.99米ドル／14日パス 11.99米ドル（表示価格がお支払いの総額です）",
  },
  {
    label: "価格以外の費用",
    content: (
      <ul className="list-disc space-y-1 pl-5">
        <li>インターネットの通信料はお客様のご負担となります。</li>
        <li>カード会社の為替レート・手数料により、円でのご請求額は変わることがあります。</li>
      </ul>
    ),
  },
  { label: "支払い方法", content: "クレジットカード" },
  { label: "支払いの時期", content: "購入の手続きの完了時" },
  { label: "提供の時期", content: "お支払いの完了後、すぐにご利用いただけます。" },
  {
    label: "有効期限",
    content: (
      <ul className="list-disc space-y-1 pl-5">
        <li>購入した時点から、1日パスは24時間、7日パスは7日間、14日パスは14日間です。</li>
        <li>自動更新はありません。</li>
        <li>有効期限が残っているうちに追加で購入した場合は、残りの有効期限にそのパスの日数を足します。</li>
      </ul>
    ),
  },
  {
    label: "返品・キャンセル",
    content: (
      <ul className="list-disc space-y-1 pl-5">
        <li>デジタルのサービスの性質上、購入後の返品・返金は、原則としてお受けしません。</li>
        <li>
          ただし、決済が重複した場合、および本サービスの不具合によりパスを利用できなかった場合は、お問い合わせのうえ返金します。
        </li>
        <li>返金した場合は、そのパスの日数分、有効期限を短くします。</li>
      </ul>
    ),
  },
  {
    label: "動作環境",
    content:
      "最新版の Google Chrome、Microsoft Edge、Mozilla Firefox、Safari（iPhone・iPad を含む）。目安として Chrome／Edge／Firefox 111 以降、Safari 16.4 以降。",
  },
];

export default function TokushohoPage() {
  return (
    <article className="mx-auto w-full max-w-2xl px-4 py-8">
      <h1 className="text-xl font-semibold text-[var(--kt-color-text-primary)]">特定商取引法に基づく表記</h1>
      <dl className="mt-6 divide-y divide-[var(--kt-color-border-default)] border-y border-[var(--kt-color-border-default)] text-sm leading-6">
        {ROWS.map((row) => (
          <div key={row.label} className="py-3 sm:grid sm:grid-cols-[10rem_1fr] sm:gap-4">
            <dt className="font-semibold text-[var(--kt-color-text-primary)]">{row.label}</dt>
            <dd className="mt-1 text-[var(--kt-color-text-secondary)] sm:mt-0">{row.content}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
