import * as React from "react";
import { View, Text, StyleSheet, ScrollView, RefreshControl, Pressable } from "react-native";
import { Link, useFocusEffect, useRouter } from "expo-router";
import PopularShrineCard from "../../../components/PopularShrineCard";
import { CardSkeleton } from "../../../components/Skeletons";
import { getRecents } from "../../../lib/storage";
import { SHRINES } from "../../../data/shrines";
import { kamimusubiDark as theme } from "../../../app/theme";

type RecentItem = {
  id: string;
  name: string;
  address?: string;
  rating?: number;
  photo_url?: string;
  popularity?: number;
};

function resolveRecents(ids: string[]): RecentItem[] {
  return ids.flatMap((id) => {
    const s = SHRINES.find((x) => String(x.id) === id);
    if (!s) return [];
    return [{
      id: String(s.id),
      name: s.name,
      address: s.prefecture,
      rating: s.rating,
      photo_url: s.imageUrl,
    }];
  });
}

export default function MyPage() {
  const router = useRouter();
  const [items, setItems] = React.useState<RecentItem[] | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      const ids = await getRecents();
      setItems(resolveRecents(ids));
    } catch {
      setItems([]);
    }
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      void load();
      return () => {};
    }, [load]),
  );

  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={theme.gold}
        />
      }
    >
      {/* ヘッダー */}
      <View style={styles.header}>
        <Text style={styles.h1}>マイページ</Text>
        <Text style={styles.subtitle}>参拝の記録、最近見た神社、ご縁の履歴をここから確認できます。</Text>
      </View>

      {/* 導線カード */}
      <View style={styles.navCards}>
        <Pressable
          onPress={() => router.push("/goshuin")}
          style={({ pressed }) => [styles.navCard, pressed && styles.navCardPressed]}
        >
          <Text style={styles.navCardIcon}>⛩</Text>
          <View style={styles.navCardBody}>
            <Text style={styles.navCardTitle}>御朱印・参拝の記録</Text>
            <Text style={styles.navCardDesc}>結んだご縁を残す</Text>
          </View>
          <Text style={styles.navCardChevron}>›</Text>
        </Pressable>

        <Pressable
          onPress={() => router.push("/search")}
          style={({ pressed }) => [styles.navCard, pressed && styles.navCardPressed]}
        >
          <Text style={styles.navCardIcon}>🔍</Text>
          <View style={styles.navCardBody}>
            <Text style={styles.navCardTitle}>神社を探す</Text>
            <Text style={styles.navCardDesc}>今の気持ちに合う神社を探す</Text>
          </View>
          <Text style={styles.navCardChevron}>›</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.h2}>最近見た神社</Text>
          <Link href="/search" asChild>
            <Text style={styles.link}>神社を探す</Text>
          </Link>
        </View>

        {items === null ? (
          <View style={styles.skeletonRow}>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </View>
        ) : null}

        {items?.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>まだ閲覧履歴がありません</Text>
            <Text style={styles.emptyText}>ホームや検索から神社を見てみましょう</Text>
          </View>
        ) : null}

        {items && items.length > 0 ? (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.horizontalList}
          >
            {items.map((s) => (
              <PopularShrineCard
                key={s.id}
                id={s.id}
                name={s.name}
                address={s.address}
                rating={s.rating}
                photo_url={s.photo_url}
                popularity={s.popularity}
              />
            ))}
          </ScrollView>
        ) : null}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  container: {
    padding: 20,
    paddingBottom: 48,
  },
  header: {
    marginBottom: 24,
    gap: 6,
  },
  h1: {
    color: theme.text,
    fontSize: 24,
    fontWeight: "900",
    letterSpacing: 0.4,
  },
  subtitle: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "500",
  },
  navCards: {
    gap: 12,
    marginBottom: 28,
  },
  navCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 18,
    paddingHorizontal: 18,
    paddingVertical: 16,
  },
  navCardPressed: {
    opacity: 0.75,
  },
  navCardIcon: {
    fontSize: 22,
  },
  navCardBody: {
    flex: 1,
    gap: 3,
  },
  navCardTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  navCardDesc: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
  },
  navCardChevron: {
    color: theme.gold,
    fontSize: 22,
    fontWeight: "700",
    lineHeight: 26,
  },
  section: {
    gap: 12,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  h2: {
    color: theme.text,
    fontSize: 17,
    fontWeight: "800",
  },
  link: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  skeletonRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 4,
  },
  empty: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    padding: 18,
    borderRadius: 16,
    gap: 6,
  },
  emptyTitle: {
    color: theme.text,
    fontWeight: "800",
    fontSize: 15,
  },
  emptyText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
  },
  horizontalList: {
    paddingVertical: 4,
    paddingRight: 4,
    gap: 12,
  },
});
