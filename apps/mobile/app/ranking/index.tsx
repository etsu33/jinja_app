// apps/mobile/app/ranking/index.tsx
import * as React from "react";
import { ScrollView, View, Text, Image, Pressable, StyleSheet } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { SHRINES } from "../../data/shrines";
import { getFavorites, toggleFavorite } from "../../lib/storage";
import { kamimusubiDark } from "../theme";

export default function RankingPage() {
  const router = useRouter();

  // お気に入り数の多い順で表示
  const items = React.useMemo(
    () => [...SHRINES].sort((a, b) => (b.favorites ?? 0) - (a.favorites ?? 0)),
    []
  );

  // お気に入り集合（ハイライト判定用）
  const [favSet, setFavSet] = React.useState<Set<string>>(new Set());
  const [favOnly, setFavOnly] = React.useState(false); // ← 追加

  const refreshFavs = React.useCallback(async () => {
    const favs = await getFavorites();
    setFavSet(new Set(favs));
  }, []);

  useFocusEffect(React.useCallback(() => { refreshFavs(); }, [refreshFavs]));

  const onToggleFav = async (id: string) => {
    await toggleFavorite(id);
    refreshFavs();
  };

  const list = React.useMemo(
    () => items.filter(s => !favOnly || favSet.has(s.id)), // ← 絞り込み
    [items, favOnly, favSet]
  );

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: kamimusubiDark.background }}
      contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
    >
      <Text
        style={{
          color: kamimusubiDark.gold,
          fontSize: 24,
          fontWeight: "700",
        }}
      >
        人気神社ランキング
      </Text>
      <Text
        style={{
          color: kamimusubiDark.text,
          fontSize: 14,
          lineHeight: 21,
          marginTop: 8,
          marginBottom: 16,
        }}
      >
        保存数の多い神社を、参拝先選びの補助として見られます。
      </Text>

      <View
        style={{ flexDirection: "row", alignItems: "center", marginBottom: 12 }}
      >
        <Pressable
          onPress={() => setFavOnly(v => !v)}
          style={{
            paddingHorizontal: 10,
            paddingVertical: 6,
            borderRadius: 999,
            borderWidth: 1,
            borderColor: favOnly
              ? kamimusubiDark.gold
              : kamimusubiDark.borderHeader,
            backgroundColor: favOnly
              ? kamimusubiDark.gold
              : kamimusubiDark.surface,
          }}
        >
          <Text
            style={{
              color: favOnly
                ? kamimusubiDark.background
                : kamimusubiDark.text,
              fontSize: 12,
            }}
          >
            {favOnly ? "保存済みだけ表示中" : "お気に入りだけ"}
          </Text>
        </Pressable>
        <Text
          style={{
            marginLeft: 8,
            fontSize: 12,
            color: kamimusubiDark.muted,
          }}
        >
          保存 {favSet.size}
        </Text>
      </View>

      {list.map((s, idx) => {
        const favored = favSet.has(s.id);
        return (
          <Pressable
            key={s.id}
            onPress={() => router.push(`/shrines/${s.id}`)}
            style={[styles.card, favored && styles.cardFav]}
          >
            <Text style={styles.rank}>{idx + 1}</Text>
            <Image source={{ uri: s.imageUrl }} style={styles.thumb} />
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{s.name}</Text>
              <Text style={styles.sub}>{s.prefecture}</Text>
              <Text style={styles.meta}>★ {(s.rating ?? 4.6).toFixed(1)}　♡ {s.favorites ?? 0}</Text>
              {favored && (
                <Text style={styles.savedHint}>記録タブで確認できます</Text>
              )}
            </View>

            <Pressable
              onPress={(event) => {
                event.stopPropagation();
                onToggleFav(s.id);
              }}
              style={[styles.heartBtn, favored && styles.heartBtnFav]}
              hitSlop={8}
            >
              <Text style={[styles.heartText, favored && styles.heartTextFav]}>
                {favored ? "♥" : "♡"}
              </Text>
            </Pressable>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: kamimusubiDark.surface,
    borderWidth: 1,
    borderColor: kamimusubiDark.borderHeader,
    borderRadius: 16,
    padding: 12,
    marginBottom: 12,
  },
  cardFav: {
    borderColor: kamimusubiDark.gold,
    backgroundColor: kamimusubiDark.surfaceSoft,
  },
  rank: {
    width: 32,
    height: 32,
    borderRadius: 999,
    backgroundColor: kamimusubiDark.surfaceSoft,
    color: kamimusubiDark.gold,
    textAlign: "center",
    textAlignVertical: "center",
    fontWeight: "700",
    marginRight: 10,
  },
  thumb: {
    width: 68,
    height: 52,
    borderRadius: 12,
    marginRight: 12,
    backgroundColor: kamimusubiDark.surfaceSoft,
  },
  name: {
    color: kamimusubiDark.text,
    fontWeight: "700",
    fontSize: 15,
  },
  sub: {
    color: kamimusubiDark.muted,
    fontSize: 12,
    marginTop: 3,
  },
  meta: {
    color: kamimusubiDark.goldSoft,
    fontSize: 12,
    marginTop: 5,
  },
  savedHint: {
    color: kamimusubiDark.mutedSoft,
    fontSize: 11,
    marginTop: 6,
  },
  heartBtn: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: kamimusubiDark.borderHeader,
    backgroundColor: kamimusubiDark.surfaceSoft,
  },
  heartBtnFav: {
    borderColor: kamimusubiDark.gold,
    backgroundColor: kamimusubiDark.gold,
  },
  heartText: {
    fontSize: 16,
    color: kamimusubiDark.mutedSoft,
  },
  heartTextFav: {
    color: kamimusubiDark.background,
  },
});
