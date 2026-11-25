// apps/mobile/app/ranking/index.tsx
import * as React from "react";
import { Animated, ScrollView, View, Text, Pressable, StyleSheet } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { fetchPopularShrines, type PopularShrine } from "../../lib/popularShrines";
import { getFavorites, toggleFavorite } from "../../lib/storage";
import { StateCard } from "../../components/common/StateCard";
import Button from "../../components/ui/Button";
import { appColors as theme } from "../../design/platformTheme";
import { spacing } from "../../design/spacing";
import { typography } from "../../design/typography";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import Ionicons from "@expo/vector-icons/Ionicons";

// お気に入りの印。旧実装は "♡"/"♥" のグリフだった。
const HEART_ICON_SIZE = 18;

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
      <Animated.View style={{ transform: [{ scale }] }}>
        <Ionicons
          name={favored ? "heart" : "heart-outline"}
          size={HEART_ICON_SIZE}
          color={favored ? theme.background : theme.mutedSoft}
        />
      </Animated.View>
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
      style={{ flex: 1, backgroundColor: theme.background }}
      contentContainerStyle={{ padding: spacing.screenX, paddingBottom: spacing.bottomSpace }}
    >
      <Text style={{ ...typography.heading, color: theme.accent }}>人気神社ランキング</Text>
      <Text
        style={{
          ...typography.body,
          color: theme.text,
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
        <Text style={{ ...typography.footnote, marginLeft: spacing.smGap, color: theme.muted }}>
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
    backgroundColor: theme.surface,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    padding: cardSizes.cardPaddingSm,
    marginBottom: spacing.lgGap,
  },
  cardFav: {
    borderColor: theme.accent,
    backgroundColor: theme.surfaceSoft,
  },
  rank: {
    width: cardSizes.rankBadgeSize,
    height: cardSizes.rankBadgeSize,
    borderRadius: radius.pill,
    backgroundColor: theme.surfaceSoft,
    color: theme.accent,
    textAlign: "center",
    textAlignVertical: "center",
    fontWeight: "700",
    marginRight: spacing.mdGap,
  },
  name: {
    ...typography.title,
    color: theme.text,
  },
  sub: {
    ...typography.footnote,
    color: theme.muted,
    marginTop: 3,
  },
  savedHint: {
    ...typography.caption,
    color: theme.mutedSoft,
    marginTop: 6,
  },
  heartBtn: {
    paddingVertical: 6,
    paddingHorizontal: spacing.mdGap,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    backgroundColor: theme.surfaceSoft,
  },
  heartBtnFav: {
    borderColor: theme.accent,
    backgroundColor: theme.accent,
  },
});
