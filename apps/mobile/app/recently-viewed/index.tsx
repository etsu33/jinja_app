

import * as React from "react";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { getRecentViewed, RecentShrineItem } from "../../lib/shrineStorage";
import { appColors as theme } from "../../design/platformTheme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { typography } from "../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 空状態の印の大きさ。
const EMPTY_ICON_SIZE = 32;

// リストの送り記号。旧実装は "›" のグリフだった。
const CHEVRON_SIZE = 20;

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
        <Text style={styles.subtitle}>
          閲覧した神社をもう一度確認できます。
        </Text>
      </View>

      {loading ? (
        <Text style={styles.loadingText}>読み込み中…</Text>
      ) : items.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="time-outline" size={EMPTY_ICON_SIZE} color={theme.muted} />
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
      ) : null}

      <View style={styles.cardBody}>
        <Text style={styles.cardTitle}>{shrine.name}</Text>
        {!!shrine.address && <Text style={styles.cardAddress}>{shrine.address}</Text>}
      </View>

      <Ionicons accessibilityElementsHidden name="chevron-forward" size={CHEVRON_SIZE} color={theme.accent} />
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
  subtitle: {
    ...typography.body,
    color: theme.text,
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
  emptyTitle: {
    ...typography.title,
    color: theme.text,
  },
  emptyText: {
    ...typography.subhead,
    color: theme.muted,
    textAlign: "center",
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
  cardBody: {
    flex: 1,
    gap: spacing.tightGap,
  },
  cardTitle: {
    ...typography.title,
    color: theme.text,
  },
  cardAddress: {
    ...typography.subhead,
    color: theme.muted,
  },
});
