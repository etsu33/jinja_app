

import * as React from "react";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { getRecentViewed, RecentShrineItem } from "../../lib/shrineStorage";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";

export default function RecentlyViewedScreen() {
  const router = useRouter();
  const [items, setItems] = React.useState<RecentShrineItem[]>([]);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(() => {
    setLoading(true);
    getRecentViewed(20)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useFocusEffect(load);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Pressable
          onPress={() => router.replace("/records")}
          style={styles.backButton}
        >
          <Text style={styles.backText}>← 記録へ戻る</Text>
        </Pressable>
        <Text style={styles.title}>最近見た神社</Text>
        <Text style={styles.subtitle}>
          閲覧した神社をもう一度確認できます。
        </Text>
      </View>

      {loading ? (
        <Text style={styles.loadingText}>読み込み中…</Text>
      ) : items.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>⛩</Text>
          <Text style={styles.emptyTitle}>最近見た神社はまだありません</Text>
          <Text style={styles.emptyText}>神社詳細を見ると、ここに閲覧履歴として表示されます。</Text>
        </View>
      ) : (
        items.map((shrine) => (
          <RecentlyViewedCard
            key={String(shrine.id)}
            shrine={shrine}
            onPress={() => router.push(`/shrines/${shrine.id}`)}
          />
        ))
      )}
    </ScrollView>
  );
}

function RecentlyViewedCard({
  shrine,
  onPress,
}: {
  shrine: RecentShrineItem;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={styles.card}>
      {shrine.photo_url ? (
        <Image source={{ uri: shrine.photo_url }} style={styles.cardImage} />
      ) : (
        <View style={styles.cardPlaceholder}>
          <Text style={styles.cardPlaceholderText}>⛩</Text>
        </View>
      )}

      <View style={styles.cardBody}>
        <Text style={styles.cardTitle}>{shrine.name}</Text>
        {!!shrine.address && <Text style={styles.cardAddress}>{shrine.address}</Text>}
      </View>

      <Text accessibilityElementsHidden style={styles.chevron}>›</Text>
    </Pressable>
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
  loadingText: {
    color: theme.muted,
    textAlign: "center",
    marginTop: spacing.bottomSpace,
  },
  emptyCard: {
    alignItems: "center",
    backgroundColor: theme.surface,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    gap: spacing.mdGap,
    padding: cardSizes.cardPaddingLg,
    marginTop: spacing.sectionTop,
  },
  emptyIcon: {
    fontSize: 40,
  },
  emptyTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
  },
  emptyText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    textAlign: "center",
    fontWeight: "600",
  },
  card: {
    alignItems: "center",
    backgroundColor: theme.surface,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    flexDirection: "row",
    gap: cardSizes.cardPaddingMd,
    padding: cardSizes.cardPaddingMd,
  },
  cardImage: {
    width: cardSizes.imageSm,
    height: cardSizes.imageSm,
    borderRadius: radius.xs,
  },
  cardPlaceholder: {
    width: cardSizes.imageSm,
    height: cardSizes.imageSm,
    borderRadius: radius.xs,
    backgroundColor: theme.surfaceSoft,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    alignItems: "center",
    justifyContent: "center",
  },
  cardPlaceholderText: {
    fontSize: 28,
  },
  cardBody: {
    flex: 1,
    gap: spacing.tightGap,
  },
  cardTitle: {
    color: theme.text,
    fontSize: 16,
    fontWeight: "700",
  },
  cardAddress: {
    color: theme.muted,
    fontSize: 13,
  },
  chevron: {
    color: theme.muted,
    fontSize: 24,
    fontWeight: "600",
  },
});
