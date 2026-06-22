import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { getCounts } from "../../lib/storage";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";

export default function VisitHistoryScreen() {
  const router = useRouter();
  const [visitCount, setVisitCount] = React.useState<number | null>(null);

  React.useEffect(() => {
    let mounted = true;

    getCounts()
      .then(({ visits }) => {
        if (mounted) setVisitCount(visits);
      })
      .catch(() => {
        if (mounted) setVisitCount(0);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Pressable
          onPress={() => router.canGoBack() ? router.back() : router.replace("/records")}
          style={styles.backButton}
        >
          <Text style={styles.backText}>← 記録へ戻る</Text>
        </Pressable>
        <Text style={styles.title}>参拝履歴</Text>
        <Text style={styles.subtitle}>
          参拝済みにした回数をここで確認できます。詳細な履歴一覧は次フェーズで追加します。
        </Text>
      </View>

      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>参拝回数</Text>
        <Text style={styles.summaryValue}>{visitCount === null ? "..." : visitCount}</Text>
        <Text style={styles.summaryText}>神社詳細画面で「参拝したことを記録する」を押すと加算されます。</Text>
      </View>

      <View style={styles.noticeCard}>
        <Text style={styles.noticeTitle}>次に追加するもの</Text>
        <Text style={styles.noticeText}>
          参拝した神社名、日付、振り返りメモを一覧で見られるようにします。
        </Text>
      </View>
    </ScrollView>
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
  summaryCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  summaryLabel: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  summaryValue: {
    color: theme.gold,
    fontSize: 44,
    fontWeight: "900",
  },
  summaryText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
  noticeCard: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.smGap,
  },
  noticeTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
  },
  noticeText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
