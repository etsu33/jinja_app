import * as React from "react";
import { ActivityIndicator, Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import {
  InvalidCheckoutResponseError,
  createBillingCheckoutSession,
  getAuthenticatedBillingStatus,
  isPremiumStatus,
  type BillingStatus,
} from "../../lib/billing";
import { isUnauthenticatedError } from "../../lib/http";
import { StateCard } from "../../components/common/StateCard";
import { AuthPrompt } from "../../components/common/AuthPrompt";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";
import { ctaSizes } from "../design/ctaSizes";

// Stripe Checkout はhttp(s)のリダイレクト先を要求するため、Web版の /billing/success, /billing/cancel を再利用する。
// API サーバーのオリジンを流用した暫定値。Webアプリの配信ドメインが確定したら差し替える。
function resolveCheckoutOrigin(): string {
  const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
  try {
    return new URL(apiBaseUrl).origin;
  } catch {
    return "http://localhost:8000";
  }
}

const CHECKOUT_ORIGIN = resolveCheckoutOrigin();
const CHECKOUT_SUCCESS_URL = `${CHECKOUT_ORIGIN}/billing/success`;
const CHECKOUT_CANCEL_URL = `${CHECKOUT_ORIGIN}/billing/cancel`;

type StatusState =
  | { kind: "loading" }
  | { kind: "unauthenticated" }
  | { kind: "error" }
  | { kind: "ready"; status: BillingStatus };

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("ja-JP", { year: "numeric", month: "long", day: "numeric" });
}

function describeStatus(status: BillingStatus): { label: string; helper: string } {
  if (isPremiumStatus(status)) {
    const periodEnd = status.current_period_end ? formatDate(status.current_period_end) : "";
    return {
      label: "Premium登録済み",
      helper: periodEnd
        ? `次回更新日: ${periodEnd}${status.cancel_at_period_end ? "（更新停止予定）" : ""}`
        : "Premiumの機能をすべて利用できます。",
    };
  }

  return {
    label: "現在はFreeプラン",
    helper: "前回比較、深い振り返り、保存した相談の整理などのPremium機能を利用できます。",
  };
}

export default function PremiumScreen() {
  const router = useRouter();
  const [state, setState] = React.useState<StatusState>({ kind: "loading" });
  const [checkoutLoading, setCheckoutLoading] = React.useState(false);
  const [checkoutError, setCheckoutError] = React.useState<string | null>(null);
  const checkoutInFlightRef = React.useRef(false);

  const loadStatus = React.useCallback(async () => {
    setState({ kind: "loading" });
    setCheckoutError(null);

    try {
      const status = await getAuthenticatedBillingStatus();
      setState(status ? { kind: "ready", status } : { kind: "error" });
    } catch (error) {
      if (isUnauthenticatedError(error)) {
        setState({ kind: "unauthenticated" });
      } else {
        if (__DEV__) {
          console.warn("[PremiumScreen] failed to load billing status", error);
        }
        setState({ kind: "error" });
      }
    }
  }, []);

  React.useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const onStartCheckout = React.useCallback(async () => {
    // Checkout開始中の二重送信防止: refで即時ガードし、setState反映前の連打も弾く
    if (checkoutInFlightRef.current) return;
    checkoutInFlightRef.current = true;
    setCheckoutLoading(true);
    setCheckoutError(null);

    try {
      const session = await createBillingCheckoutSession({
        successUrl: CHECKOUT_SUCCESS_URL,
        cancelUrl: CHECKOUT_CANCEL_URL,
      });
      await Linking.openURL(session.checkout_url);
    } catch (error) {
      if (isUnauthenticatedError(error)) {
        setState({ kind: "unauthenticated" });
      } else if (error instanceof InvalidCheckoutResponseError) {
        setCheckoutError("お支払いページの準備に失敗しました。しばらくしてからもう一度お試しください。");
      } else {
        setCheckoutError("お支払いページを開けませんでした。通信状況を確認してもう一度お試しください。");
      }
      if (__DEV__) {
        console.warn("[PremiumScreen] checkout failed", error);
      }
    } finally {
      checkoutInFlightRef.current = false;
      setCheckoutLoading(false);
    }
  }, []);

  return (
    <>
      <ScrollView
        style={styles.screen}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Pressable onPress={() => router.replace("/mypage")} style={styles.backButton}>
            <Text style={styles.backText}>← マイページへ戻る</Text>
          </Pressable>
          <Text style={styles.title}>Premium</Text>
          <Text style={styles.subtitle}>
            前回比較、深い振り返り、保存した相談の整理などをPremiumで利用できます。
          </Text>
        </View>

        {state.kind === "loading" ? (
          <StateCard title="読み込み中" description="Premiumの登録状況を確認しています。" />
        ) : null}

        {state.kind === "error" ? (
          <View style={styles.errorBlock}>
            <StateCard
              title="登録状況を確認できませんでした"
              description="通信状況を確認して、もう一度お試しください。"
            />
            <Pressable onPress={() => void loadStatus()} style={styles.retryButton} accessibilityRole="button">
              <Text style={styles.retryButtonText}>再試行</Text>
            </Pressable>
          </View>
        ) : null}

        {state.kind === "unauthenticated" ? (
          <StateCard
            title="ログインが必要です"
            description="Premiumの登録状況を見るには、ログインしてください。"
          />
        ) : null}

        {state.kind === "ready" ? (
          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>{describeStatus(state.status).label}</Text>
            <Text style={styles.statusHelper}>{describeStatus(state.status).helper}</Text>

            {isPremiumStatus(state.status) ? null : (
              <View style={styles.checkoutSection}>
                <Pressable
                  onPress={() => void onStartCheckout()}
                  disabled={checkoutLoading}
                  style={({ pressed }) => [
                    styles.checkoutButton,
                    checkoutLoading && styles.checkoutButtonDisabled,
                    pressed && !checkoutLoading && styles.checkoutButtonPressed,
                  ]}
                  accessibilityRole="button"
                >
                  {checkoutLoading ? (
                    <ActivityIndicator color={theme.background} />
                  ) : (
                    <Text style={styles.checkoutButtonText}>Premiumに登録する</Text>
                  )}
                </Pressable>

                {checkoutError ? <Text style={styles.checkoutErrorText}>{checkoutError}</Text> : null}
              </View>
            )}
          </View>
        ) : null}
      </ScrollView>

      <AuthPrompt
        visible={state.kind === "unauthenticated"}
        onClose={() => router.replace("/mypage")}
        description="Premiumの登録状況を見るには、ログインが必要です。"
      />
    </>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    padding: spacing.screenXWide,
    paddingBottom: spacing.bottomSpace,
    gap: spacing.lgGap,
  },
  header: {
    gap: spacing.mdGap,
  },
  backButton: {
    alignSelf: "flex-start",
    marginBottom: spacing.smGap,
  },
  backText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  title: {
    color: theme.gold,
    fontSize: 26,
    fontWeight: "900",
  },
  subtitle: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 23,
    fontWeight: "600",
  },
  errorBlock: {
    gap: spacing.smGap,
  },
  retryButton: {
    alignSelf: "flex-start",
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    borderRadius: radius.pill,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  retryButtonText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  statusCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  statusLabel: {
    color: theme.gold,
    fontSize: 18,
    fontWeight: "900",
  },
  statusHelper: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
  checkoutSection: {
    marginTop: spacing.smGap,
    gap: spacing.smGap,
  },
  checkoutButton: {
    minHeight: ctaSizes.mediumHeight,
    borderRadius: radius.md,
    backgroundColor: theme.gold,
    alignItems: "center",
    justifyContent: "center",
  },
  checkoutButtonDisabled: {
    opacity: 0.6,
  },
  checkoutButtonPressed: {
    opacity: 0.85,
  },
  checkoutButtonText: {
    color: theme.background,
    fontSize: 15,
    fontWeight: "800",
  },
  checkoutErrorText: {
    color: theme.gold,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "700",
  },
});
