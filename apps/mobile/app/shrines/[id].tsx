// apps/mobile/app/shrines/[id].tsx
import * as React from "react";
import { View, Text, Image, Pressable, StyleSheet, ScrollView, Linking, Platform } from "react-native";
import { useLocalSearchParams, useRouter, useFocusEffect } from "expo-router";
import { SHRINES } from "../../data/shrines";
import { incVisits, isFavorite, toggleFavorite, pushRecent } from "../../lib/storage";
import { kamimusubiDark as theme } from "../theme";

type Shrine = {
  id: string | number;
  name: string;
  prefecture?: string;
  description?: string;
  imageUrl?: string;
  tags?: string[];
  latitude?: number;
  longitude?: number;
};

export default function ShrineDetail() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const shrineId = React.useMemo(() => {
    const raw = params.id;
    if (!raw) return undefined;
    return Array.isArray(raw) ? raw[0] : raw;
  }, [params.id]);

  const router = useRouter();
  const shrine: Shrine | undefined = React.useMemo(
    () => SHRINES.find((x: Shrine) => String(x.id) === String(shrineId)),
    [shrineId],
  );

  const [fav, setFav] = React.useState(false);
  const tags = shrine?.tags ?? [];

  const countedRef = React.useRef(false);
  useFocusEffect(
    React.useCallback(() => {
      if (!countedRef.current) {
        countedRef.current = true;
        incVisits(1).catch(() => {});
      }
      return () => {};
    }, [shrineId]),
  );

  React.useEffect(() => {
    if (!shrineId) return;
    isFavorite(String(shrineId)).then(setFav).catch(() => {});
    pushRecent(String(shrineId)).catch(() => {});
  }, [shrineId]);

  const onToggleFav = async () => {
    if (!shrineId) return;
    const now = await toggleFavorite(String(shrineId));
    setFav(now);
  };

  const openDirections = React.useCallback(() => {
    if (!shrine) return;
    const hasLatLng = typeof shrine.latitude === "number" && typeof shrine.longitude === "number";
    const destination = hasLatLng ? `${shrine.latitude},${shrine.longitude}` : encodeURIComponent(shrine.name);
    const googleMapsAppUrl = hasLatLng
      ? `comgooglemaps://?daddr=${destination}&directionsmode=walking`
      : `comgooglemaps://?daddr=${encodeURIComponent(shrine.name)}`;
    const googleMapsWebUrl = hasLatLng
      ? `https://www.google.com/maps/dir/?api=1&destination=${destination}`
      : `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(shrine.name)}`;

    if (Platform.OS === "ios") {
      Linking.openURL(googleMapsAppUrl).catch(() => { Linking.openURL(googleMapsWebUrl).catch(() => {}); });
      return;
    }
    if (Platform.OS === "android") {
      Linking.openURL(`google.navigation:q=${destination}`).catch(() => { Linking.openURL(googleMapsWebUrl).catch(() => {}); });
      return;
    }
    Linking.openURL(googleMapsWebUrl).catch(() => {});
  }, [shrine]);

  if (!shrineId) {
    return (
      <View style={styles.errorScreen}>
        <Text style={styles.errorText}>パラメータ `id` が不正です。</Text>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 戻る</Text>
        </Pressable>
      </View>
    );
  }

  if (!shrine) {
    return (
      <View style={styles.errorScreen}>
        <Text style={styles.errorText}>該当の神社が見つかりませんでした。</Text>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 戻る</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      {/* ヒーロー画像 */}
      {shrine.imageUrl ? (
        <Image source={{ uri: shrine.imageUrl }} style={styles.heroImage} />
      ) : (
        <View style={styles.heroPlaceholder}>
          <Text style={styles.heroPlaceholderText}>⛩</Text>
        </View>
      )}

      {/* ヘッダー（戻る + お気に入り） */}
      <View style={styles.headerBar}>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 戻る</Text>
        </Pressable>
        <Pressable
          onPress={onToggleFav}
          style={[styles.favBtn, fav && styles.favBtnActive]}
          accessibilityRole="button"
          accessibilityLabel="お気に入りの切り替え"
        >
          <Text style={[styles.favBtnText, fav && styles.favBtnTextActive]}>
            {fav ? "♡ 登録済み" : "♡ お気に入り"}
          </Text>
        </Pressable>
      </View>

      {/* 神社名・所在地 */}
      <View style={styles.titleBlock}>
        <Text style={styles.shrineName}>{shrine.name}</Text>
        {!!shrine.prefecture && <Text style={styles.shrineArea}>{shrine.prefecture}</Text>}
      </View>

      {/* ご利益タグ */}
      {tags.length > 0 ? (
        <View style={styles.tagRow}>
          {tags.map((t) => (
            <View key={t} style={styles.tagPill}>
              <Text style={styles.tagText}>{t}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {/* 説明文 */}
      <View style={styles.descCard}>
        <Text style={styles.descLabel}>神社について</Text>
        <Text style={styles.descText}>
          {shrine.description ?? "ご利益や混雑、アクセス、御朱印情報などをここに表示します。"}
        </Text>
      </View>

      {/* CTA */}
      <View style={styles.ctaBlock}>
        <Pressable onPress={openDirections} style={styles.ctaPrimary}>
          <Text style={styles.ctaPrimaryText}>経路案内を開く</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    paddingBottom: 48,
  },

  // エラー画面
  errorScreen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.background,
    gap: 16,
  },
  errorText: {
    color: theme.muted,
    fontSize: 15,
    fontWeight: "600",
  },

  // ヒーロー
  heroImage: {
    width: "100%",
    aspectRatio: 16 / 10,
  },
  heroPlaceholder: {
    width: "100%",
    aspectRatio: 16 / 10,
    backgroundColor: theme.surface,
    alignItems: "center",
    justifyContent: "center",
    borderBottomWidth: 1,
    borderBottomColor: theme.border,
  },
  heroPlaceholderText: {
    fontSize: 48,
  },

  // ヘッダーバー
  headerBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  backBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  backBtnText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  favBtn: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.border,
    backgroundColor: "transparent",
  },
  favBtnActive: {
    borderColor: theme.borderGold,
    backgroundColor: theme.borderGoldDark,
  },
  favBtnText: {
    color: theme.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  favBtnTextActive: {
    color: theme.gold,
  },

  // 神社名・所在地
  titleBlock: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 4,
    gap: 4,
  },
  shrineName: {
    color: theme.text,
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 0.5,
    lineHeight: 34,
  },
  shrineArea: {
    color: theme.muted,
    fontSize: 13,
    fontWeight: "600",
    letterSpacing: 0.3,
  },

  // タグ
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 7,
    paddingHorizontal: 20,
    paddingTop: 12,
  },
  tagPill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  tagText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.3,
  },

  // 説明文カード
  descCard: {
    marginHorizontal: 16,
    marginTop: 20,
    backgroundColor: theme.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: theme.border,
    padding: 18,
    gap: 8,
  },
  descLabel: {
    color: theme.mutedSoft,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 2,
  },
  descText: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 25,
    fontWeight: "500",
  },

  // CTA
  ctaBlock: {
    paddingHorizontal: 16,
    marginTop: 20,
    gap: 10,
  },
  ctaPrimary: {
    height: 52,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
    shadowColor: theme.gold,
    shadowOpacity: 0.25,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  ctaPrimaryText: {
    color: theme.background,
    fontSize: 16,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
});
