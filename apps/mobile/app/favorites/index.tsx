import { useCallback, useState } from "react";
import { Image, Pressable, ScrollView, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { getFavoriteShrines, RecentShrineItem } from "../shrines/storage";
import { toggleFavorite } from "../../lib/storage";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";

export default function FavoritesScreen() {
  const router = useRouter();
  const [items, setItems] = useState<RecentShrineItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    getFavoriteShrines()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useFocusEffect(load);

  const onRemove = async (id: number | string) => {
    await toggleFavorite(String(id));
    setItems((prev) => prev.filter((x) => String(x.id) !== String(id)));
  };

  return (
    <ScrollView
      style={{ backgroundColor: theme.background, flex: 1 }}
      contentContainerStyle={{ padding: spacing.screenXWide, paddingBottom: spacing.bottomSpace, gap: spacing.lgGap }}
    >
      <View style={{ marginBottom: spacing.lgGap }}>
        <Pressable
          onPress={() => router.canGoBack() ? router.back() : router.replace("/")}
          style={{ marginBottom: spacing.xlGap }}
        >
          <Text style={{ color: theme.gold, fontSize: 13, fontWeight: "700" }}>
            ← 戻る
          </Text>
        </Pressable>
        <Text style={{ color: theme.gold, fontSize: 26, fontWeight: "700" }}>
          お気に入り
        </Text>
        <Text style={{ color: theme.text, fontSize: 15, lineHeight: 23, marginTop: spacing.mdGap }}>
          保存した神社を確認できます。
        </Text>
      </View>

      {loading ? (
        <Text style={{ color: theme.muted, textAlign: "center", marginTop: spacing.bottomSpace }}>
          読み込み中…
        </Text>
      ) : items.length === 0 ? (
        <View style={{ alignItems: "center", marginTop: spacing.bottomSpace + spacing.sectionTop, gap: spacing.lgGap }}>
          <Text style={{ fontSize: 40 }}>♡</Text>
          <Text style={{ color: theme.muted, fontSize: 15 }}>
            お気に入りの神社はまだありません
          </Text>
          <Text style={{ color: theme.mutedDark, fontSize: 13, textAlign: "center" }}>
            神社詳細ページから「♡ お気に入り」を押すと保存されます
          </Text>
        </View>
      ) : (
        items.map((shrine) => (
          <FavoriteCard
            key={String(shrine.id)}
            shrine={shrine}
            onPress={() => router.push(`/shrines/${shrine.id}`)}
            onRemove={() => onRemove(shrine.id)}
          />
        ))
      )}
    </ScrollView>
  );
}

function FavoriteCard({
  shrine,
  onPress,
  onRemove,
}: {
  shrine: RecentShrineItem;
  onPress: () => void;
  onRemove: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={{
        backgroundColor: theme.surface,
        borderColor: theme.borderHeader,
        borderRadius: cardSizes.radiusMd,
        borderWidth: cardSizes.borderWidth,
        flexDirection: "row",
        gap: cardSizes.cardPaddingMd,
        padding: cardSizes.cardPaddingMd,
        alignItems: "center",
      }}
    >
      {shrine.photo_url ? (
        <Image
          source={{ uri: shrine.photo_url }}
          style={{ width: cardSizes.imageSm, height: cardSizes.imageSm, borderRadius: cardSizes.imageRadius }}
        />
      ) : (
        <View
          style={{
            width: cardSizes.imageSm,
            height: cardSizes.imageSm,
            borderRadius: cardSizes.imageRadius,
            backgroundColor: theme.surfaceSoft,
            borderWidth: cardSizes.borderWidth,
            borderColor: theme.border,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text style={{ fontSize: 28 }}>⛩</Text>
        </View>
      )}

      <View style={{ flex: 1, gap: spacing.tightGap }}>
        <Text style={{ color: theme.text, fontSize: 16, fontWeight: "700" }}>
          {shrine.name}
        </Text>
        {!!shrine.address && (
          <Text style={{ color: theme.muted, fontSize: 13 }}>
            {shrine.address}
          </Text>
        )}
      </View>

      <Pressable
        onPress={(e) => { e.stopPropagation(); onRemove(); }}
        hitSlop={8}
        accessibilityLabel="お気に入りを解除"
        style={{
          paddingVertical: 6,
          paddingHorizontal: 10,
          borderRadius: cardSizes.pillRadius,
          borderWidth: cardSizes.borderWidth,
          borderColor: theme.borderGold,
        }}
      >
        <Text style={{ color: theme.gold, fontSize: 12, fontWeight: "700" }}>
          解除
        </Text>
      </Pressable>
    </Pressable>
  );
}
