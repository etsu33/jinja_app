// apps/mobile/app/ranking/index.tsx
import * as React from "react";
import { Animated, ScrollView, View, Text, Image, Pressable, StyleSheet } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { SHRINES } from "../../data/shrines";
import { getFavorites, toggleFavorite } from "../../lib/storage";
import { kamimusubiDark } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";

type FavoriteHeartButtonProps = {
  favored: boolean;
  onPress: () => void;
};

function FavoriteHeartButton({ favored, onPress }: FavoriteHeartButtonProps) {
  const scale = React.useRef(new Animated.Value(1)).current;

  const handlePress = () => {
    Animated.sequence([
      Animated.timing(scale, {
        toValue: 1.16,
        duration: 90,
        useNativeDriver: true,
      }),
      Animated.timing(scale, {
        toValue: 1,
        duration: 90,
        useNativeDriver: true,
      }),
    ]).start();

    onPress();
  };

  return (
    <Pressable
      onPress={(event) => {
        event.stopPropagation();
        handlePress();
      }}
      style={[styles.heartBtn, favored && styles.heartBtnFav]}
      hitSlop={spacing.smGap}
    >
      <Animated.Text style={[styles.heartText, favored && styles.heartTextFav, { transform: [{ scale }] }]}>
        {favored ? "♥" : "♡"}
      </Animated.Text>
    </Pressable>
  );
}

export default function RankingPage() {
  const router = useRouter();

  // お気に入り数の多い順で表示
  const items = React.useMemo(() => [...SHRINES].sort((a, b) => (b.favorites ?? 0) - (a.favorites ?? 0)), []);

  // お気に入り集合（ハイライト判定用）
  const [favSet, setFavSet] = React.useState<Set<string>>(new Set());
  const [favOnly, setFavOnly] = React.useState(false); // ← 追加

  const refreshFavs = React.useCallback(async () => {
    const favs = await getFavorites();
    setFavSet(new Set(favs));
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      refreshFavs();
    }, [refreshFavs]),
  );

  const onToggleFav = async (id: string) => {
    await toggleFavorite(id);
    refreshFavs();
  };

  const list = React.useMemo(
    () => items.filter((s) => !favOnly || favSet.has(s.id)), // ← 絞り込み
    [items, favOnly, favSet],
  );

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: kamimusubiDark.background }}
      contentContainerStyle={{ padding: spacing.screenX, paddingBottom: spacing.bottomSpace }}
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
          marginTop: spacing.smGap,
          marginBottom: spacing.xlGap,
        }}
      >
        保存数の多い神社を、参拝先選びの補助として見られます。
      </Text>

      <View style={{ flexDirection: "row", alignItems: "center", marginBottom: spacing.lgGap }}>
        <Pressable
          onPress={() => setFavOnly((v) => !v)}
          style={{
            paddingHorizontal: spacing.mdGap,
            paddingVertical: spacing.inlineGap - 1,
            borderRadius: cardSizes.pillRadius,
            borderWidth: cardSizes.borderWidth,
            borderColor: favOnly ? kamimusubiDark.gold : kamimusubiDark.borderHeader,
            backgroundColor: favOnly ? kamimusubiDark.gold : kamimusubiDark.surface,
          }}
        >
          <Text
            style={{
              color: favOnly ? kamimusubiDark.background : kamimusubiDark.text,
              fontSize: 12,
            }}
          >
            {favOnly ? "保存済みだけ表示中" : "お気に入りだけ"}
          </Text>
        </Pressable>
        <Text
          style={{
            marginLeft: spacing.smGap,
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
              <Text style={styles.meta}>
                ★ {(s.rating ?? 4.6).toFixed(1)}　♡ {s.favorites ?? 0}
              </Text>
              {favored && <Text style={styles.savedHint}>記録タブで確認できます</Text>}
            </View>

            <FavoriteHeartButton favored={favored} onPress={() => onToggleFav(s.id)} />
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
    borderWidth: cardSizes.borderWidth,
    borderColor: kamimusubiDark.borderHeader,
    borderRadius: cardSizes.radiusMd,
    padding: cardSizes.cardPaddingSm,
    marginBottom: spacing.lgGap,
  },
  cardFav: {
    borderColor: kamimusubiDark.gold,
    backgroundColor: kamimusubiDark.surfaceSoft,
  },
  rank: {
    width: cardSizes.rankBadgeSize,
    height: cardSizes.rankBadgeSize,
    borderRadius: cardSizes.pillRadius,
    backgroundColor: kamimusubiDark.surfaceSoft,
    color: kamimusubiDark.gold,
    textAlign: "center",
    textAlignVertical: "center",
    fontWeight: "700",
    marginRight: spacing.mdGap,
  },
  thumb: {
    width: 68,
    height: 52,
    borderRadius: cardSizes.imageRadius,
    marginRight: spacing.lgGap,
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
    paddingHorizontal: spacing.mdGap,
    borderRadius: cardSizes.pillRadius,
    borderWidth: cardSizes.borderWidth,
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
