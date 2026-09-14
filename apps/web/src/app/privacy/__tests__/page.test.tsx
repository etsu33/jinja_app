import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PrivacyPolicyPage from "../page";

const REQUIRED_SECTIONS = [
  "1. 取得する情報",
  "2. 利用目的",
  "3. 相談内容について",
  "4. 位置情報について",
  "5. Cookie / localStorageについて",
  "6. Analyticsについて",
  "7. 決済サービスについて",
  "8. 外部AIサービスについて",
  "9. 外部サービスについて",
  "10. 保存期間",
  "11. 開示・訂正・削除等",
  "12. お問い合わせ",
];

describe("PrivacyPolicyPage", () => {
  it("主要見出しを表示する", () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByRole("heading", { level: 1, name: "プライバシーポリシー" })).toBeInTheDocument();
    for (const section of REQUIRED_SECTIONS) {
      expect(screen.getByRole("heading", { level: 2, name: section })).toBeInTheDocument();
    }
  });

  it("外部生成AIへ相談内容を送信していない旨を明記する", () => {
    render(<PrivacyPolicyPage />);

    expect(
      screen.getByText(
        "現在、KAMI MUSUBIでは、利用者の相談内容を外部の生成AIサービスへ送信していません。",
      ),
    ).toBeInTheDocument();
  });

  it("将来外部AIを導入する場合はポリシーを更新する旨を明記する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    expect(text).toContain("将来、外部AIサービスを利用する機能を導入する場合");
    expect(text).toContain("本プライバシーポリシーを更新します");
  });

  it("OpenAI等の外部生成AIを現在利用していると誤認させる文言がない", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    for (const banned of ["OpenAI", "ChatGPT", "GPT", "Anthropic", "Claude", "Gemini"]) {
      expect(text).not.toContain(banned);
    }
  });

  it("現行UIで変更できるプロフィール項目と変更できない項目を正しく区別する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    expect(text).not.toContain("いずれも利用者が任意で入力・変更できます");

    expect(text).toContain("現在の設定画面から利用者が変更できるのは、表示名、公開設定および生年月日です");

    expect(text).toContain("生年月日は、設定画面のほか、コンシェルジュやコンパスで入力した場合にも保存され");

    expect(text).toContain(
      "自己紹介、アイコン画像、出生時刻、出生地については、現時点では設定画面から入力・変更する導線を提供していません",
    );
  });

  it("相談内容の非公開と、公開投稿の説明を別の文に分ける", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    // 「相談内容は非公開。ただし公開設定は別」という続き方をすると、
    // 相談内容が公開されうると読めてしまう。
    expect(text).toContain("本サービスには、相談内容を他の利用者へ公開する機能はありません。");
    expect(text).not.toContain("ただし、利用者が公開設定を有効にした投稿");

    const consultIndex = text.indexOf("相談内容を他の利用者へ公開する機能はありません");
    const publicIndex = text.indexOf("公開設定を有効にした場合に他の利用者から閲覧可能になるのは");
    expect(consultIndex).toBeGreaterThan(-1);
    expect(publicIndex).toBeGreaterThan(consultIndex);
    expect(text).toContain("相談内容はこれに含まれません");
  });

  it("匿名データの90日Retentionと自動削除ではない境界を正しく記載する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    expect(text).toContain("90日を超えたデータを削除対象とします");

    expect(text).toContain("認証済みアカウントに紐づく情報には、この90日の匿名データ保持ルールを適用しません");

    expect(text).not.toContain("90日後に自動削除");
    expect(text).not.toContain("90日経過時に自動削除");
    expect(text).not.toContain("完全に削除します");
  });

  it("現行実装で確認できる取得情報と外部サービスを記載する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    for (const fact of [
      "access_token",
      "refresh_token",
      "concierge_anon_id",
      "Stripe",
      "PostHog",
      "Google Maps Platform",
      "OpenStreetMap",
    ]) {
      expect(text).toContain(fact);
    }
    expect(text).toContain("クレジットカード番号などの支払手段そのものは本サービスのサーバーに保存しません");
  });
});

  it("アカウント削除とPremium課金停止の現在仕様を明記する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    expect(text).toContain("利用者は設定画面から、自身のアカウントを削除できます");

    expect(text).toContain("将来の請求停止を確認したうえでPremiumを終了し、アカウント削除を進めます");

    expect(text).toContain("アカウントとの紐付けを解除したうえで保持される場合があります");
  });
