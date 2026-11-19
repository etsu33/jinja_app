import { useCallback, useState } from "react";
import { Image, Pressable, ScrollView, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { getFavoriteShrines, RecentShrineItem } from "../../lib/shrineStorage";
import { toggleFavorite } from "../../lib/storage";
import { appColors as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { typography } from "../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 空状態の印。旧実装は "♡" のグリフだった。
const EMPTY_ICON_SIZE = 40;

export default function FavoritesScreen() {
  const router = useRouter();
  const [items, setItems] = useState<RecentShrineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    let alive = true;

    setLoading(true);
    setError(false);

    void getFavoriteShrines()
      .then((nextItems) => {
        if (!alive) return;

        setItems(nextItems);
        setError(false);
      })
      .catch(() => {
        if (!alive) return;

        setItems([]);
        setError(true);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
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
        <Text style={{ ...typography.subhead, color: theme.text, marginTop: spacing.mdGap }}>
          保存した神社を確認できます。
        </Text>
      </View>

      {loading ? (
        <Text style={{ color: theme.muted, textAlign: "center", marginTop: spacing.bottomSpace }}>
          読み込み中…
        </Text>
      ) : error ? (
        <View style={{ alignItems: "center", marginTop: spacing.bottomSpace + spacing.sectionTop, gap: spacing.lgGap }}>
          <Text style={{ ...typography.body, color: theme.muted }}>お気に入りを読み込めませんでした</Text>
          <Text style={{ ...typography.footnote, color: theme.mutedDark, textAlign: "center" }}>
            通信状況を確認して、もう一度画面を開き直してください。
          </Text>
        </View>
      ) : items.length === 0 ? (
        <View style={{ alignItems: "center", marginTop: spacing.bottomSpace + spacing.sectionTop, gap: spacing.lgGap }}>
          <Ionicons name="heart-outline" size={EMPTY_ICON_SIZE} color={theme.mutedDark} />
          <Text style={{ ...typography.body, color: theme.muted }}>お気に入りの神社はまだありません</Text>
          <Text style={{ ...typography.footnote, color: theme.mutedDark, textAlign: "center" }}>
            神社詳細ページの「お気に入り」を押すと保存されます
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
        borderRadius: radius.md,
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
          style={{ width: cardSizes.imageSm, height: cardSizes.imageSm, borderRadius: radius.xs }}
        />
      ) : (
        <View
          style={{
            width: cardSizes.imageSm,
            height: cardSizes.imageSm,
            borderRadius: radius.xs,
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
        <Text style={{ ...typography.title, color: theme.text }}>
          {shrine.name}
        </Text>
        {!!shrine.address && (
          <Text style={{ ...typography.footnote, color: theme.muted }}>
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
          borderRadius: radius.pill,
          borderWidth: cardSizes.borderWidth,
          borderColor: theme.borderAccent,
        }}
      >
        <Text style={{ ...typography.footnoteStrong, color: theme.accent }}>
          解除
        </Text>
      </Pressable>
    </Pressable>
  );
}
