// apps/mobile/src/app/favorites/page.tsx
import * as React from "react";
import { View, Text, Pressable, ScrollView, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { getFavorites, toggleFavorite } from "../../../lib/storage";
import { SHRINES, Shrine } from "../../../data/shrines";
import { kamimusubiDark as theme } from "../../../app/theme";

function resolveShrines(ids: string[]): Shrine[] {
  return ids
    .map((id) => SHRINES.find((s) => s.id === id))
    .filter((s): s is Shrine => s !== undefined);
}

export default function FavoritesPage() {
  const router = useRouter();
  const [shrines, setShrines] = React.useState<Shrine[]>([]);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(() => {
    getFavorites()
      .then((ids) => setShrines(resolveShrines(ids)))
      .catch(() => setShrines([]))
      .finally(() => setLoading(false));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const onRemove = async (id: string) => {
    await toggleFavorite(id);
    setShrines((prev) => prev.filter((s) => s.id !== id));
  };

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.title}>お気に入り</Text>
        <Text style={styles.subtitle}>保存した神社を確認できます。</Text>
      </View>

      {loading ? (
        <Text style={styles.stateText}>読み込み中…</Text>
      ) : shrines.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>♡</Text>
          <Text style={styles.emptyTitle}>お気に入りの神社はまだありません</Text>
          <Text style={styles.emptyDesc}>
            神社詳細ページから「♡ お気に入り」を押すと保存されます
          </Text>
        </View>
      ) : (
        shrines.map((shrine) => (
          <Pressable
            key={shrine.id}
            style={styles.card}
            onPress={() => router.push(`/shrines/${shrine.id}`)}
            accessibilityRole="button"
            accessibilityLabel={shrine.name}
          >
            <View style={styles.cardIcon}>
              <Text style={styles.cardIconText}>⛩</Text>
            </View>

            <View style={styles.cardBody}>
              <Text style={styles.cardName}>{shrine.name}</Text>
              {shrine.prefecture != null && (
                <Text style={styles.cardPref}>{shrine.prefecture}</Text>
              )}
              {shrine.tags.length > 0 && (
                <Text style={styles.cardTags}>{shrine.tags.join(" · ")}</Text>
              )}
            </View>

            <Pressable
              onPress={(e) => {
                e.stopPropagation();
                onRemove(shrine.id);
              }}
              hitSlop={8}
              style={styles.removeBtn}
              accessibilityRole="button"
              accessibilityLabel={`${shrine.name}をお気に入りから解除`}
            >
              <Text style={styles.removeBtnText}>解除</Text>
            </Pressable>
          </Pressable>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    padding: 24,
    paddingBottom: 48,
    gap: 12,
  },
  header: {
    marginBottom: 12,
  },
  title: {
    color: theme.gold,
    fontSize: 26,
    fontWeight: "700",
  },
  subtitle: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 23,
    marginTop: 10,
  },
  stateText: {
    color: theme.muted,
    textAlign: "center",
    marginTop: 40,
    fontSize: 15,
  },
  emptyState: {
    alignItems: "center",
    marginTop: 60,
    gap: 12,
  },
  emptyIcon: {
    fontSize: 40,
  },
  emptyTitle: {
    color: theme.muted,
    fontSize: 15,
  },
  emptyDesc: {
    color: theme.mutedDark,
    fontSize: 13,
    textAlign: "center",
    paddingHorizontal: 24,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: theme.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: theme.borderHeader,
    padding: 14,
  },
  cardIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.border,
    alignItems: "center",
    justifyContent: "center",
  },
  cardIconText: {
    fontSize: 24,
  },
  cardBody: {
    flex: 1,
    gap: 3,
  },
  cardName: {
    color: theme.text,
    fontSize: 16,
    fontWeight: "700",
  },
  cardPref: {
    color: theme.muted,
    fontSize: 13,
  },
  cardTags: {
    color: theme.goldSoft,
    fontSize: 12,
  },
  removeBtn: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.borderGold,
  },
  removeBtnText: {
    color: theme.gold,
    fontSize: 12,
    fontWeight: "700",
  },
});
