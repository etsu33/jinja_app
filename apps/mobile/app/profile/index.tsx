import * as React from "react";
import { View, Text, StyleSheet, ScrollView, RefreshControl, Pressable } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import PopularShrineCard from "../../components/PopularShrineCard";
import { CardSkeleton } from "../../components/Skeletons";
import { getRecents } from "../../lib/storage";
import { SHRINES } from "../../data/shrines";
import { kamimusubiDark as theme } from "../theme";

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
        <Pressable
          onPress={() => router.push("/")}
          style={({ pressed }) => [styles.homeLink, pressed && styles.homeLinkPressed]}
        >
          <Text style={styles.homeLinkText}>← ホーム</Text>
        </Pressable>
        <Text style={styles.h1}>マイページ</Text>
        <Text style={styles.subtitle}>プロフィール情報や最近見た神社を確認できます。</Text>
      </View>

      <View style={styles.profileCard}>
        <View style={styles.profileIcon}>
          <Text style={styles.profileIconText}>人</Text>
        </View>
        <View style={styles.profileBody}>
          <Text style={styles.profileTitle}>プロフィール</Text>
          <Text style={styles.profileDesc}>名前・設定・利用状況は今後ここにまとめます。</Text>
        </View>
      </View>

      <View style={styles.section}>
        <View style={styles.row}>
          <View style={styles.sectionTitleBlock}>
            <Text style={styles.h2}>最近見た神社</Text>
            <Text style={styles.sectionHint}>お気に入りではなく、閲覧履歴です</Text>
          </View>
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
            <Text style={styles.emptyText}>ホームや検索から神社を見ると、閲覧履歴として表示されます</Text>
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
  homeLink: {
    alignSelf: "flex-start",
    marginBottom: 8,
  },
  homeLinkPressed: {
    opacity: 0.5,
  },
  homeLinkText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
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
  profileCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 18,
    paddingHorizontal: 18,
    paddingVertical: 16,
    marginBottom: 28,
  },
  profileIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.borderGold,
    alignItems: "center",
    justifyContent: "center",
  },
  profileIconText: {
    color: theme.gold,
    fontSize: 18,
    fontWeight: "900",
  },
  profileBody: {
    flex: 1,
    gap: 3,
  },
  profileTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  profileDesc: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
    lineHeight: 18,
  },
  section: {
    gap: 12,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  sectionTitleBlock: {
    flex: 1,
    gap: 3,
  },
  h2: {
    color: theme.text,
    fontSize: 17,
    fontWeight: "800",
  },
  sectionHint: {
    color: theme.muted,
    fontSize: 12,
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
