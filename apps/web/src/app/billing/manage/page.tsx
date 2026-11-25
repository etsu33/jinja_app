// apps/web/src/app/billing/manage/page.tsx
//
// 月額の自動更新（Stripe Customer Portal での解約・支払い方法の変更）を廃止したため、
// 以前のリンクやブックマークから来た人はプラン状況のページへ送る。
import { redirect } from "next/navigation";

export default function BillingManagePage() {
  redirect("/billing");
}
