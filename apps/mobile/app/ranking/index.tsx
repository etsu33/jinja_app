// apps/mobile/app/ranking/index.tsx
import * as React from "react";
import { Animated, ScrollView, View, Text, Pressable, StyleSheet } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { fetchPopularShrines, type PopularShrine } from "../../lib/popularShrines";
import { getFavorites, toggleFavorite } from "../../lib/storage";
import { StateCard } from "../../components/common/StateCard";
import Button from "../../components/ui/Button";
import { kamimusubiDark } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";

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

  const [items, setItems] = React.useState<PopularShrine[]>([]);
  const [status, setStatus] = React.useState<"loading" | "ready" | "error">("loading");

  // Backend(/populars/)が返す順序(popular_score降順)をそのまま維持し、Mobile側で再ソートしない。
  // 画面マウント時に1回だけ取得する(Search画面のloadPopularShrinesと同じ契約)。
  const loadItems = React.useCallback(async () => {
    setStatus("loading");
    try {
      const shrines = await fetchPopularShrines();
      setItems(shrines);
      setStatus("ready");
    } catch {
      setItems([]);
      setStatus("error");
    }
  }, []);

  React.useEffect(() => {
    void loadItems();
  }, [loadItems]);

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
        人気の神社を、参拝先選びの補助として見られます。
      </Text>

      <View style={{ flexDirection: "row", alignItems: "center", marginBottom: spacing.lgGap }}>
        <Button
          title={favOnly ? "保存済みだけ表示中" : "お気に入りだけ"}
          accessibilityLabel={favOnly ? "保存済みだけ表示中" : "お気に入りだけ"}
          variant={favOnly ? "primary" : "outline"}
          size="compact"
          onPress={() => setFavOnly((v) => !v)}
        />
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

      {status === "loading" ? <StateCard title="読み込み中" description="人気の神社を確認しています。" /> : null}

      {status === "error" ? (
        <View style={{ gap: spacing.mdGap, alignItems: "flex-start" }}>
          <StateCard title="読み込めませんでした" description="通信状況を確認して、もう一度お試しください。" />
          <Button
            title="もう一度試す"
            variant="outline"
            size="compact"
            onPress={() => void loadItems()}
            accessibilityLabel="人気の神社をもう一度読み込む"
          />
        </View>
      ) : null}

      {status === "ready" && list.length === 0 ? (
        <StateCard title="現在表示できる人気の神社がありません" description="条件を変えて、もう一度お試しください。" />
      ) : null}

      {status === "ready"
        ? list.map((s, idx) => {
            const favored = favSet.has(s.id);
            return (
              <Pressable
                key={s.id}
                onPress={() => router.push(`/shrines/${s.id}`)}
                style={[styles.card, favored && styles.cardFav]}
              >
                <Text style={styles.rank}>{idx + 1}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.name}>{s.name}</Text>
                  {s.address ? (
                    <Text style={styles.sub} numberOfLines={1}>
                      {s.address}
                    </Text>
                  ) : null}
                  {favored && <Text style={styles.savedHint}>記録タブで確認できます</Text>}
                </View>

                <FavoriteHeartButton favored={favored} onPress={() => onToggleFav(s.id)} />
              </Pressable>
            );
          })
        : null}
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
    borderRadius: radius.md,
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
    borderRadius: radius.pill,
    backgroundColor: kamimusubiDark.surfaceSoft,
    color: kamimusubiDark.gold,
    textAlign: "center",
    textAlignVertical: "center",
    fontWeight: "700",
    marginRight: spacing.mdGap,
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
  savedHint: {
    color: kamimusubiDark.mutedSoft,
    fontSize: 11,
    marginTop: 6,
  },
  heartBtn: {
    paddingVertical: 6,
    paddingHorizontal: spacing.mdGap,
    borderRadius: radius.pill,
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
