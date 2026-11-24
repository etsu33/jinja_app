import * as React from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import * as Linking from "expo-linking";

import { appColors as theme } from "../design/platformTheme";
import { spacing } from "../design/spacing";
import { getRefreshToken } from "../lib/authTokens";
import { createApplePurchaseFlow, type ApplePurchaseState } from "../lib/applePurchaseFlow";
import {
  APPLE_PRODUCTS,
  openAppleStoreKit,
  type ApplePrices,
  type ApplePurchaseFailureCode,
} from "../lib/appleStoreKit";
import { getAuthenticatedBillingStatus, registerAppleTransaction, type BillingStatus } from "../lib/billing";
import { LEGAL_LABELS, openLegalDocument, type LegalDocument } from "../lib/legalLinks";
import Button from "./ui/Button";
import { typography } from "../design/typography";

const errors: Record<ApplePurchaseFailureCode, string> = {
  "store-unavailable": "App Storeに接続できません。しばらくしてから再試行してください。",
  "product-unavailable": "この商品は現在購入できません。",
  verification: "購入を確認できませんでした。購入済みの場合は「購入を復元」をお試しください。",
  "backend-unavailable": "購入確認サービスに接続できません。時間をおいて「購入を復元」をお試しください。",
  ownership: "この購入は別のアカウントに登録されています。購入時のアカウントでログインしてください。",
  network: "通信に失敗しました。接続を確認して「購入を復元」をお試しください。",
  authentication: "購入の確認には購入時のアカウントでログインし直す必要があります。",
  finish: "購入を確認しました。App Storeでの処理を終えるには「購入を復元」をお試しください。",
  refresh: "最新の登録状況を取得できませんでした。「購入を復元」をお試しください。",
  purchase: "購入手続きを完了できませんでした。購入済みの場合は「購入を復元」をお試しください。",
};

const notices = {
  cancelled: "購入をキャンセルしました。",
  pending: "App Storeでの承認を待っています。承認後に「購入を復元」をお試しください。",
  updated: "購入情報を照合し、登録状況を更新しました。",
  "nothing-to-restore": "復元できる購入は見つかりませんでした。登録状況は更新済みです。",
} as const;

type ProductState = { kind: "loading" | "error" } | { kind: "ready"; prices: ApplePrices };

// App Store Review Guideline 3.1.2: 自動更新サブスクリプションを売る画面には、
// 更新の条件と、利用規約・プライバシーポリシーへの機能するリンクを置く。
const AUTO_RENEWAL_NOTICE =
  "月額Premiumは自動更新です。期間終了の24時間前までに解約しない限り、同じ料金で更新されます。" +
  "解約と次回更新日の確認は、iPhoneの「設定」>「Apple Account」>「サブスクリプション」から行えます。" +
  "Premium Passは自動更新されません。";

function LegalLink({ document }: { document: LegalDocument }) {
  return (
    <Pressable
      accessibilityRole="link"
      accessibilityLabel={`${LEGAL_LABELS[document]}を開く`}
      hitSlop={12}
      onPress={() => openLegalDocument(document, Linking.openURL)}
    >
      <Text style={styles.legalLinkText}>{LEGAL_LABELS[document]}</Text>
    </Pressable>
  );
}

type Props = { onBillingStatus: (status: BillingStatus) => void };

export function ApplePurchaseSection({ onBillingStatus }: Props) {
  const [productState, setProductState] = React.useState<ProductState>({ kind: "loading" });
  const [purchaseState, setPurchaseState] = React.useState<ApplePurchaseState>({ kind: "idle" });
  const [loadAttempt, setLoadAttempt] = React.useState(0);
  const [flow, setFlow] = React.useState<ReturnType<typeof createApplePurchaseFlow> | null>(null);

  React.useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const store = await openAppleStoreKit(Platform.OS);
        if (!active || !store) return;
        setFlow(
          createApplePurchaseFlow({
            store,
            getSession: getRefreshToken,
            register: registerAppleTransaction,
            refresh: getAuthenticatedBillingStatus,
            publishStatus: (status) => {
              if (active) onBillingStatus(status);
            },
            publishPurchaseState: (state) => {
              if (active) setPurchaseState(state);
            },
          }),
        );
        const prices = await store.loadPrices();
        if (active) setProductState({ kind: "ready", prices });
      } catch {
        if (active) setProductState({ kind: "error" });
      }
    })();
    return () => {
      active = false;
    };
  }, [loadAttempt, onBillingStatus]);

  const busy = purchaseState.kind === "purchasing" || purchaseState.kind === "restoring";
  const hasPrices = productState.kind === "ready" && Object.keys(productState.prices).length > 0;
  const unavailable = productState.kind === "ready" && !hasPrices;
  const message = purchaseState.kind in notices ? notices[purchaseState.kind as keyof typeof notices] : null;

  return (
    <View style={styles.section}>
      {productState.kind === "loading" ? (
        <Text accessibilityLiveRegion="polite" style={styles.helper}>
          App Storeの商品を読み込んでいます。
        </Text>
      ) : null}
      {productState.kind === "error" ? (
        <Text accessibilityRole="alert" style={styles.message}>
          App Storeの商品を取得できませんでした。
        </Text>
      ) : null}
      {unavailable ? (
        <Text accessibilityLiveRegion="polite" style={styles.helper}>
          現在購入できる商品がありません。
        </Text>
      ) : null}
      {productState.kind === "ready" && hasPrices
        ? APPLE_PRODUCTS.map((product) => {
            const price = productState.prices[product.id];
            if (!price)
              return (
                <Text key={product.id} style={styles.helper}>
                  {product.label}は現在購入できません。
                </Text>
              );
            const title = `${product.label} ${price}${product.typeIOS === "auto-renewable-subscription" ? " / 月" : ""}`;
            return (
              <Button
                key={product.id}
                title={title}
                variant={product.typeIOS === "auto-renewable-subscription" ? "primary" : "outline"}
                onPress={() => void flow?.purchase(product)}
                disabled={busy || !flow}
                accessibilityLabel={title}
              />
            );
          })
        : null}
      {productState.kind === "error" || unavailable ? (
        <Button
          title="商品を再読み込み"
          variant="outline"
          disabled={busy}
          onPress={() => {
            setFlow(null);
            setProductState({ kind: "loading" });
            setLoadAttempt((attempt) => attempt + 1);
          }}
        />
      ) : null}
      {purchaseState.kind === "purchasing" ? (
        <Text accessibilityLiveRegion="polite" style={styles.helper}>
          購入を確認しています。
        </Text>
      ) : null}
      <Button
        title={purchaseState.kind === "restoring" ? "復元しています…" : "購入を復元"}
        variant="outline"
        disabled={!flow || busy}
        loading={purchaseState.kind === "restoring"}
        onPress={() => void flow?.restore()}
      />
      {message ? (
        <Text accessibilityLiveRegion="polite" style={styles.helper}>
          {message}
        </Text>
      ) : null}
      {purchaseState.kind === "error" ? (
        <Text accessibilityRole="alert" style={styles.message}>
          {errors[purchaseState.reason]}
        </Text>
      ) : null}

      <Text style={styles.notice}>{AUTO_RENEWAL_NOTICE}</Text>
      <View style={styles.legalRow}>
        <LegalLink document="terms" />
        <Text style={styles.legalSeparator}>・</Text>
        <LegalLink document="privacy" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  section: { marginTop: spacing.smGap, gap: spacing.smGap },
  notice: { ...typography.footnote, color: theme.mutedDark, marginTop: spacing.smGap },
  legalRow: { flexDirection: "row", alignItems: "center", gap: spacing.tightGap },
  legalLinkText: { ...typography.footnoteStrong, color: theme.accent },
  legalSeparator: { ...typography.footnote, color: theme.mutedDark },
  helper: { ...typography.subhead, color: theme.mutedSoft },
  message: { ...typography.footnote, color: theme.accent },
});
