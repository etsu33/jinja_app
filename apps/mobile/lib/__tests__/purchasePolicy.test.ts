// iOS v1 で購入につながる要素を出さないことの検証。
// Mobileのテスト環境は node のため、画面はソースをテキストとして読んで構造を確認する
// (routerStructure.test.ts / mypageContactLink.test.ts と同じ方式)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { PREMIUM_COPY, canShowPurchaseUi } from "../purchasePolicy";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const premiumSource = readFileSync(resolve(mobileRoot, "app/premium/index.tsx"), "utf8");
const mypageSource = readFileSync(resolve(mobileRoot, "app/mypage/index.tsx"), "utf8");

describe("canShowPurchaseUi", () => {
  it("iOSでは購入要素を出さない", () => {
    expect(canShowPurchaseUi("ios")).toBe(false);
  });

  it("Android・Webでは従来どおり購入要素を出す", () => {
    expect(canShowPurchaseUi("android")).toBe(true);
    expect(canShowPurchaseUi("web")).toBe(true);
  });
});

describe("iOS向けの文言", () => {
  it("購入を促す表現・外部での登録を案内する表現を含まない", () => {
    for (const text of [PREMIUM_COPY.freeHelperWithoutPurchase, PREMIUM_COPY.mypageDescriptionWithoutPurchase]) {
      expect(text).not.toMatch(/登録する|購入|使えるようにします|Web|ウェブ|ブラウザ|円|価格/);
    }
  });
});

describe("Premium画面", () => {
  it("Platform.OS から購入要素の表示可否を決める", () => {
    expect(premiumSource).toContain("const PURCHASE_UI_ENABLED = canShowPurchaseUi(Platform.OS);");
  });

  it("購入ボタンは購入要素を出せる環境でのみ描画する", () => {
    const buttonIndex = premiumSource.indexOf('title="Premiumに登録する"');
    const gateIndex = premiumSource.indexOf("{!PURCHASE_UI_ENABLED || isPremiumStatus(state.status) ? null : (");
    expect(gateIndex).toBeGreaterThan(-1);
    expect(buttonIndex).toBeGreaterThan(gateIndex);
  });

  it("購入要素を出さない環境では外部決済ページを開く前に処理を止める", () => {
    const handlerStart = premiumSource.indexOf("const onStartCheckout");
    const guardIndex = premiumSource.indexOf("if (!PURCHASE_UI_ENABLED) return;", handlerStart);
    const createSessionIndex = premiumSource.indexOf("createBillingCheckoutSession({", handlerStart);
    const openUrlIndex = premiumSource.indexOf("Linking.openURL(session.checkout_url)", handlerStart);
    expect(guardIndex).toBeGreaterThan(handlerStart);
    expect(guardIndex).toBeLessThan(createSessionIndex);
    expect(guardIndex).toBeLessThan(openUrlIndex);
  });
});

describe("マイページのPremiumカード", () => {
  it("iOSでは購入を促さない説明文に切り替える", () => {
    expect(mypageSource).toContain("canShowPurchaseUi(Platform.OS)");
    expect(mypageSource).toContain("PREMIUM_COPY.mypageDescriptionWithoutPurchase");
  });
});
