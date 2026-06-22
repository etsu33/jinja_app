// apps/mobile/components/home/RankingCarousel.tsx
import * as React from "react";
import { Image, ScrollView, Text, View, StyleSheet, Pressable } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { getFavorites, toggleFavorite } from "../../lib/storage";
import { spacing } from "../../app/design/spacing";
import { cardSizes } from "../../app/design/cardSizes";
import { shadows } from "../../app/design/shadow";
import { kamimusubiDark as theme } from "../../app/theme";

type Shrine = {
  id: string;
  name: string;
  imageUrl: string;
  tags: string[];
  rating?: number;
  favorites?: number;
};

export default function RankingCarousel({ items }: { items: Shrine[] }) {
  const router = useRouter();

  // お気に入り集合（ハイライト判定用）
  const [favSet, setFavSet] = React.useState<Set<string>>(new Set());

  const refreshFavs = React.useCallback(async () => {
    const favs = await getFavorites();
    setFavSet(new Set(favs));
  }, []);

  // Home画面に戻ってきた時などに再読込
  useFocusEffect(
    React.useCallback(() => {
      refreshFavs();
    }, [refreshFavs])
  );

  const onToggleFav = async (id: string) => {
    await toggleFavorite(id);
    refreshFavs();
  };

  return (
    <View style={{ marginTop: spacing.smGap, paddingHorizontal: spacing.screenX }}>
      {/* ヘッダー */}
      <View style={styles.headerRow}>
        <Text style={styles.title}>人気神社ランキング</Text>
        <View style={styles.headerActionRow}>
          <Pressable onPress={() => router.push("/ranking")} style={styles.moreLink}>
            <Text style={styles.moreLinkText}>もっと見る</Text>
          </Pressable>
          <View style={styles.badge}><Text style={styles.badgeText}>今週</Text></View>
        </View>
      </View>

      {/* 横スクロール */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.listContent}>
        {items.map((s, i) => {
          const favored = favSet.has(s.id);
          return (
            <Pressable
              key={s.id}
              onPress={() => router.push(`/shrines/${s.id}`)}
              style={[styles.card, { marginRight: i === items.length - 1 ? 0 : spacing.lgGap }, favored && styles.cardFav]}
            >
              {/* ハートの小ボタン（カード右上・タップでトグル／ナビは発火させない） */}
              <Pressable
                onPress={(e) => {
                  e.stopPropagation();
                  onToggleFav(s.id);
                }}
                style={[styles.heartFab, favored && styles.heartFabFav]}
                hitSlop={spacing.smGap}
              >
                <Text style={[styles.heartFabText, favored && styles.heartFabTextFav]}>{favored ? "♡" : "♡"}</Text>
              </Pressable>

              <Image source={{ uri: s.imageUrl }} style={styles.img} />
              <View style={styles.cardContent}>
                <Text numberOfLines={1} style={styles.name}>
                  {s.name}
                </Text>
                <View style={styles.tagRow}>
                  {s.tags.slice(0, 3).map((t) => (
                    <React.Fragment key={t}>
                      <View style={styles.tag}>
                        <Text style={styles.tagText}>{t}</Text>
                      </View>
                    </React.Fragment>
                  ))}
                </View>
                <View style={styles.rowSpace}>
                  <Text style={styles.meta}>★ {(s.rating ?? 4.6).toFixed(1)}</Text>
                  <Text style={styles.meta}>♡ {s.favorites ?? 0}</Text>
                </View>
              </View>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

const rankingCarouselColors = {
  badgeBackground: theme.gold,
  badgeText: theme.background,
  cardBackground: theme.text,
  cardBorder: theme.border,
  favoriteBorder: theme.gold,
  favoriteBackground: theme.borderGoldDark,
  tagBackground: theme.outside,
  metaText: theme.mutedDark,
  heartBackground: theme.text,
  heartText: theme.background,
  heartTextFav: theme.gold,
} as const;

const styles = StyleSheet.create({
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.smGap,
  },
  headerActionRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  moreLink: {
    marginRight: spacing.smGap,
  },
  moreLinkText: {
    fontSize: 12,
    textDecorationLine: "underline",
  },
  listContent: {
    paddingRight: spacing.screenX,
  },
  title: { fontSize: 18, fontWeight: "600" },
  badge: {
    backgroundColor: rankingCarouselColors.badgeBackground,
    paddingHorizontal: spacing.smGap,
    paddingVertical: spacing.tightGap,
    borderRadius: cardSizes.radiusSm / 2,
  },
  badgeText: { fontSize: 12, fontWeight: "500", color: rankingCarouselColors.badgeText },

  card: {
    width: cardSizes.carouselWidthLg,
    borderRadius: cardSizes.radiusMd,
    backgroundColor: rankingCarouselColors.cardBackground,
    borderWidth: cardSizes.borderWidth,
    borderColor: rankingCarouselColors.cardBorder,
    overflow: "hidden",
    position: "relative",
    ...shadows.lightCard,
  },
  cardFav: {
    borderColor: rankingCarouselColors.favoriteBorder,
    backgroundColor: rankingCarouselColors.favoriteBackground,
  },
  img: {
    width: "100%",
    aspectRatio: 16 / 9,
    borderTopLeftRadius: cardSizes.radiusMd,
    borderTopRightRadius: cardSizes.radiusMd,
  },
  cardContent: {
    padding: cardSizes.cardPaddingSm,
  },
  name: { fontWeight: "600" },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.inlineGap - 1,
  },
  tag: {
    borderRadius: cardSizes.pillRadius,
    backgroundColor: rankingCarouselColors.tagBackground,
    paddingHorizontal: spacing.smGap,
    paddingVertical: 2,
    marginRight: spacing.inlineGap - 1,
    marginBottom: spacing.inlineGap - 1,
  },
  tagText: { fontSize: 11 },
  rowSpace: { flexDirection: "row", justifyContent: "space-between" },
  meta: { color: rankingCarouselColors.metaText, fontSize: 12 },

  heartFab: {
    position: "absolute",
    top: spacing.smGap,
    right: spacing.smGap,
    zIndex: 2,
    paddingVertical: spacing.tightGap,
    paddingHorizontal: spacing.smGap,
    borderRadius: cardSizes.pillRadius,
    backgroundColor: rankingCarouselColors.heartBackground,
    borderWidth: cardSizes.borderWidth,
    borderColor: rankingCarouselColors.cardBorder,
  },
  heartFabFav: {
    borderColor: rankingCarouselColors.favoriteBorder,
    backgroundColor: rankingCarouselColors.heartBackground,
  },
  heartFabText: { fontSize: 14, color: rankingCarouselColors.heartText },
  heartFabTextFav: { color: rankingCarouselColors.heartTextFav },
});
