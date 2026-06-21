import { useCallback, useState } from "react";
import { Image, Pressable, ScrollView, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { getFavoriteShrines, RecentShrineItem } from "../shrines/storage";
import { toggleFavorite } from "../../lib/storage";
import { kamimusubiDark as theme } from "../theme";

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
      contentContainerStyle={{ padding: 24, paddingBottom: 40, gap: 12 }}
    >
      <View style={{ marginBottom: 12 }}>
        <Pressable
          onPress={() => router.canGoBack() ? router.back() : router.replace("/")}
          style={{ marginBottom: 16 }}
        >
          <Text style={{ color: theme.gold, fontSize: 13, fontWeight: "700" }}>
            ← 戻る
          </Text>
        </Pressable>
        <Text style={{ color: theme.gold, fontSize: 26, fontWeight: "700" }}>
          お気に入り
        </Text>
        <Text style={{ color: theme.text, fontSize: 15, lineHeight: 23, marginTop: 10 }}>
          保存した神社を確認できます。
        </Text>
      </View>

      {loading ? (
        <Text style={{ color: theme.muted, textAlign: "center", marginTop: 40 }}>
          読み込み中…
        </Text>
      ) : items.length === 0 ? (
        <View style={{ alignItems: "center", marginTop: 60, gap: 12 }}>
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
        borderRadius: 16,
        borderWidth: 1,
        flexDirection: "row",
        gap: 14,
        padding: 14,
        alignItems: "center",
      }}
    >
      {shrine.photo_url ? (
        <Image
          source={{ uri: shrine.photo_url }}
          style={{ width: 64, height: 64, borderRadius: 12 }}
        />
      ) : (
        <View
          style={{
            width: 64,
            height: 64,
            borderRadius: 12,
            backgroundColor: theme.surfaceSoft,
            borderWidth: 1,
            borderColor: theme.border,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text style={{ fontSize: 28 }}>⛩</Text>
        </View>
      )}

      <View style={{ flex: 1, gap: 4 }}>
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
          borderRadius: 999,
          borderWidth: 1,
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
