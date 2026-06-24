// apps/mobile/app/shrines/[id].tsx
import * as React from "react";
import { View, Text, Image, Pressable, StyleSheet, ScrollView, Linking, Platform } from "react-native";
import { useLocalSearchParams, useRouter, useFocusEffect } from "expo-router";
import { SHRINES } from "../../data/shrines";
import { incVisits, isFavorite, toggleFavorite, pushRecent } from "../../lib/storage";
import { kamimusubiDark as theme } from "../theme";
import { get } from "../../lib/http";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";
import { ctaSizes } from "../design/ctaSizes";

type Shrine = {
  id: string | number;
  name: string;
  prefecture?: string;
  description?: string;
  recommendationReason?: string;
  explanation?: string;
  actionSuggestion?: string;
  imageUrl?: string;
  tags?: string[];
  latitude?: number;
  longitude?: number;
};

type ShrineApiResponse = {
  id: string | number;
  name?: string;
  name_jp?: string;
  address?: string;
  prefecture?: string;
  description?: string | null;
  recommendation_reason?: string | null;
  recommendationReason?: string | null;
  explanation?: string | null;
  action_suggestion?: string | null;
  actionSuggestion?: string | null;
  imageUrl?: string;
  image_url?: string;
  latitude?: number | null;
  longitude?: number | null;
  goriyaku?: string | null;
  goriyaku_tags?: Array<{ id: number; name: string; category?: string }>;
};

const SHRINE_API_ID_BY_LOCAL_ID: Record<string, string> = {
  fushimi: "2",
};

function toShrine(api: ShrineApiResponse): Shrine {
  return {
    id: api.id,
    name: api.name_jp ?? api.name ?? "名称未設定の神社",
    prefecture: api.prefecture ?? api.address,
    description: api.description ?? api.goriyaku ?? undefined,
    recommendationReason: api.recommendationReason ?? api.recommendation_reason ?? undefined,
    explanation: api.explanation ?? undefined,
    actionSuggestion: api.actionSuggestion ?? api.action_suggestion ?? undefined,
    imageUrl: api.imageUrl ?? api.image_url,
    tags: api.goriyaku_tags?.map((tag) => tag.name) ?? [],
    latitude: typeof api.latitude === "number" ? api.latitude : undefined,
    longitude: typeof api.longitude === "number" ? api.longitude : undefined,
  };
}

export default function ShrineDetail() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const shrineId = React.useMemo(() => {
    const raw = params.id;
    if (!raw) return undefined;
    return Array.isArray(raw) ? raw[0] : raw;
  }, [params.id]);

  const apiShrineId = React.useMemo(() => {
    if (!shrineId) return undefined;
    return SHRINE_API_ID_BY_LOCAL_ID[shrineId] ?? shrineId;
  }, [shrineId]);

  const router = useRouter();
  const localShrine: Shrine | undefined = React.useMemo(
    () => SHRINES.find((x: Shrine) => String(x.id) === String(shrineId)),
    [shrineId],
  );

  const [apiShrine, setApiShrine] = React.useState<Shrine | undefined>();
  const [loading, setLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [fav, setFav] = React.useState(false);
  const [visited, setVisited] = React.useState(false);
  const shrine = apiShrine ?? localShrine;
  const tags = shrine?.tags ?? [];

  const recommendationReason = React.useMemo(() => {
    if (!shrine) return undefined;
    return shrine.recommendationReason ?? `${shrine.name}は、今の相談や願いを一度落ち着いて整理する場所として受け取りやすい候補です。`;
  }, [shrine]);

  const explanation = React.useMemo(() => {
    if (!shrine) return undefined;
    return shrine.explanation ?? shrine.description ?? `${shrine.name}の由緒やご利益を確認しながら、今の自分に必要な意味を探しやすい神社です。`;
  }, [shrine]);

  const actionSuggestion = React.useMemo(() => {
    if (!shrine) return undefined;
    return shrine.actionSuggestion ?? "参拝前に、今考えていることを一つだけ言葉にしてから向かうと、帰ってきたあとに変化を振り返りやすくなります。";
  }, [shrine]);

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
    if (!apiShrineId) return;

    let active = true;
    setLoading(true);
    setErrorMessage(null);

    get<ShrineApiResponse>(`/shrines/${apiShrineId}/`)
      .then((data) => {
        if (!active) return;
        setApiShrine(toShrine(data));
      })
      .catch(() => {
        if (!active) return;
        setApiShrine(undefined);
        setErrorMessage(localShrine ? null : "神社情報を取得できませんでした。");
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [apiShrineId, localShrine]);

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

  const onVisitDone = React.useCallback(() => {
    setVisited(true);
  }, []);

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

  if (loading && !shrine) {
    return (
      <View style={styles.errorScreen}>
        <Text style={styles.errorText}>神社情報を読み込んでいます…</Text>
      </View>
    );
  }

  if (!shrine) {
    return (
      <View style={styles.errorScreen}>
        <Text style={styles.errorText}>該当の神社が見つかりませんでした。</Text>
        <Pressable onPress={() => router.canGoBack() ? router.back() : router.replace("/")} style={styles.backBtn}>
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
        <Pressable onPress={() => router.canGoBack() ? router.back() : router.replace("/")} style={styles.backBtn}>
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

      {/* 推薦理由 */}
      <View style={styles.recommendationCard}>
        <Text style={styles.cardEyebrow}>RECOMMENDATION</Text>
        <Text style={styles.cardTitle}>この神社が候補に入った理由</Text>
        <Text style={styles.cardBody}>{recommendationReason}</Text>
      </View>

      {/* explanation */}
      <View style={styles.explanationCard}>
        <Text style={styles.cardEyebrow}>EXPLANATION</Text>
        <Text style={styles.cardTitle}>神社の意味を知る</Text>
        <Text style={styles.cardBody}>{explanation}</Text>
      </View>

      {/* action suggestion */}
      <View style={styles.actionCard}>
        <Text style={styles.cardEyebrow}>NEXT ACTION</Text>
        <Text style={styles.cardTitle}>参拝前にできること</Text>
        <Text style={styles.cardBody}>{actionSuggestion}</Text>
      </View>

      {/* 説明文 */}
      <View style={styles.descCard}>
        <Text style={styles.descLabel}>神社について</Text>
        <Text style={styles.descText}>
          {shrine.description ?? "ご利益や混雑、アクセス、御朱印情報などをここに表示します。"}
        </Text>
      </View>

      {errorMessage ? (
        <View style={styles.noticeCard}>
          <Text style={styles.noticeText}>{errorMessage}</Text>
        </View>
      ) : null}

      {/* CTA */}
      <View style={styles.ctaBlock}>
        <Text style={styles.ctaCaption}>参拝に行くと決めたら、地図で経路を確認できます。</Text>
        <Pressable onPress={openDirections} style={styles.ctaSecondary}>
          <Text style={styles.ctaSecondaryText}>地図で経路を確認する</Text>
        </Pressable>
        <Pressable onPress={onVisitDone} style={[styles.ctaPrimary, visited && styles.ctaPrimaryDone]}>
          <Text style={styles.ctaPrimaryText}>{visited ? "参拝済みとして記録しました" : "参拝したことを記録する"}</Text>
        </Pressable>
      </View>

      {visited ? (
        <View style={styles.reflectionCard}>
          <Text style={styles.cardEyebrow}>REFLECTION</Text>
          <Text style={styles.cardTitle}>参拝後の振り返り</Text>
          <Text style={styles.cardBody}>参拝して感じたことを残しておくと、次の相談や再訪時に自分の変化を見返しやすくなります。</Text>
          <Pressable style={styles.reflectionButton} onPress={() => router.push("/records") }>
            <Text style={styles.reflectionButtonText}>振り返りを残す</Text>
          </Pressable>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    paddingBottom: spacing.bottomSpaceLg,
  },

  // エラー画面
  errorScreen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.background,
    gap: spacing.xlGap,
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
    borderBottomWidth: cardSizes.borderWidth,
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
    paddingHorizontal: spacing.screenX,
    paddingTop: spacing.xlGap,
    paddingBottom: spacing.smGap,
  },
  backBtn: {
    paddingVertical: ctaSizes.pillPaddingY,
    paddingHorizontal: ctaSizes.pillPaddingX,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  backBtnText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  favBtn: {
    paddingVertical: ctaSizes.pillPaddingY,
    paddingHorizontal: cardSizes.cardPaddingMd,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
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
    paddingHorizontal: spacing.contentX,
    paddingTop: spacing.lgGap,
    paddingBottom: spacing.tightGap,
    gap: spacing.tightGap,
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
    gap: spacing.inlineGap,
    paddingHorizontal: spacing.contentX,
    paddingTop: spacing.lgGap,
  },
  tagPill: {
    paddingHorizontal: ctaSizes.pillPaddingX,
    paddingVertical: 5,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  tagText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.3,
  },

  // v2カード共通
  recommendationCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surfaceSoft,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  explanationCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  actionCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surfaceSoft,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  cardEyebrow: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.4,
  },
  cardTitle: {
    color: theme.text,
    fontSize: 16,
    lineHeight: 22,
    fontWeight: "900",
  },
  cardBody: {
    color: theme.mutedSoft,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
  },

  // 説明文カード
  descCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
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

  noticeCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.xlGap,
    backgroundColor: theme.surface,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    paddingHorizontal: cardSizes.cardPaddingMd,
    paddingVertical: spacing.lgGap,
  },
  noticeText: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },

  // CTA
  ctaBlock: {
    paddingHorizontal: spacing.screenX,
    marginTop: spacing.xlGap,
    gap: spacing.mdGap,
  },
  ctaCaption: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
    textAlign: "center",
  },
  ctaSecondary: {
    height: ctaSizes.mediumHeight,
    borderRadius: ctaSizes.mediumRadius,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "transparent",
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
  },
  ctaSecondaryText: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
  ctaPrimary: {
    height: ctaSizes.mediumHeight,
    borderRadius: ctaSizes.mediumRadius,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
  },
  ctaPrimaryDone: {
    backgroundColor: theme.borderGoldDark,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
  },
  ctaPrimaryText: {
    color: theme.background,
    fontSize: 14,
    fontWeight: "900",
    letterSpacing: 0.3,
  },
  reflectionCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.mdGap,
  },
  reflectionButton: {
    height: ctaSizes.mediumHeight,
    borderRadius: ctaSizes.mediumRadius,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "transparent",
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
  },
  reflectionButtonText: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
});
