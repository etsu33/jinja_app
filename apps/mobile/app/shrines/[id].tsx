// apps/mobile/app/shrines/[id].tsx
import * as React from "react";
import { View, Text, Image, Pressable, StyleSheet, ScrollView, Linking, Platform } from "react-native";
import { useLocalSearchParams, useRouter, useFocusEffect } from "expo-router";
import { SHRINES } from "../../data/shrines";
import { incVisits, isFavorite, toggleFavorite, pushRecent } from "../../lib/storage";
import { kamimusubiDark as theme } from "../theme";
import { get } from "../../lib/http";
import { trackShrineDetailView, trackShrineRouteOpen } from "../../lib/shrineInteractions";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";
import { ctaSizes } from "../design/ctaSizes";


type RecommendationReasonFactAxis =
  | "need"
  | "benefit"
  | "feature"
  | "element"
  | "distance"
  | "popularity"
  | "fallback";

type RecommendationReasonFacts = {
  version?: 1;
  primary_axis?: RecommendationReasonFactAxis | null;
  secondary_axis?: RecommendationReasonFactAxis | null;
  matched_need_tags?: string[];
  matched_benefits?: string[];
  shrine_feature?: string | null;
  shrine_benefit?: string | null;
  visit_fit?: string | null;
  matched_element?: string | null;
  matched_sign?: string | null;
  distance_label?: string | null;
  popularity_label?: string | null;
  fallback_reason?: string | null;
  confidence?: "high" | "mid" | "low" | null;
  type?: string | null;
  label?: string | null;
  label_ja?: string | null;
  evidence?: Array<string | { label?: string | null; value?: string | null; text?: string | null }>;
};

type RecommendationReasonDetail = {
  heroMeaningCopy?: string | null;
  consultationSummary?: string | null;
  shrineMeaning?: string | null;
  actionMeaning?: string | null;
};

type Shrine = {
  id: string | number;
  name: string;
  prefecture?: string;
  description?: string;
  recommendationReason?: string;
  recommendationReasonV4?: string;
  reasonFacts?: RecommendationReasonFacts | null;
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
  recommendation_reason_v4?: string | null;
  recommendationReasonV4?: string | null;
  reason_facts?: RecommendationReasonFacts | null;
  reasonFacts?: RecommendationReasonFacts | null;
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

function asTrimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function resolveRecommendationReason(shrine: Shrine) {
  const v4Reason = asTrimmedString(shrine.recommendationReasonV4);
  if (v4Reason) return v4Reason;

  const factBasedReason =
    asTrimmedString(shrine.reasonFacts?.shrine_feature) ??
    asTrimmedString(shrine.reasonFacts?.shrine_benefit) ??
    asTrimmedString(shrine.reasonFacts?.visit_fit) ??
    asTrimmedString(shrine.reasonFacts?.fallback_reason);

  if (factBasedReason) return factBasedReason;

  const legacyReason = asTrimmedString(shrine.recommendationReason);
  if (legacyReason) return legacyReason;

  return "相談内容と神社情報をもとに選ばれた候補です。";
}

function buildReasonFactItems(reasonFacts?: RecommendationReasonFacts | RecommendationReasonFacts[] | null) {
  if (!reasonFacts) return [];

  const facts = Array.isArray(reasonFacts) ? reasonFacts : [reasonFacts];
  const technicalValues = new Set(["history_theme", "matched_need_tags", "fallback"]);

  return facts
    .flatMap((fact) => {
      const structuredItems = [
        fact.shrine_feature ? { label: "神社固有の文脈", value: fact.shrine_feature } : null,
        fact.shrine_benefit ? { label: "ご利益・意味", value: fact.shrine_benefit } : null,
        fact.visit_fit ? { label: "参拝との相性", value: fact.visit_fit } : null,
        fact.distance_label ? { label: "行きやすさ", value: fact.distance_label } : null,
        fact.popularity_label ? { label: "参考情報", value: fact.popularity_label } : null,
      ];

      const labelValue = asTrimmedString(fact.label_ja ?? fact.label);
      const labelItem = labelValue ? { label: "推薦の文脈", value: labelValue } : null;

      const evidenceItems = Array.isArray(fact.evidence)
        ? fact.evidence.map((evidence) => {
            const rawValue =
              typeof evidence === "string"
                ? evidence
                : evidence.value ?? evidence.text ?? null;
            const value = asTrimmedString(rawValue);
            if (!value || technicalValues.has(value) || value === labelValue) return null;

            return { label: "判断材料", value };
          })
        : [];

      return [labelItem, ...structuredItems, ...evidenceItems];
    })
    .filter((item): item is { label: string; value: string } => Boolean(item?.value?.trim()));
}

function toShrine(api: ShrineApiResponse): Shrine {
  return {
    id: api.id,
    name: api.name_jp ?? api.name ?? "名称未設定の神社",
    prefecture: api.prefecture ?? api.address,
    description: api.description ?? api.goriyaku ?? undefined,
    recommendationReason: api.recommendationReason ?? api.recommendation_reason ?? undefined,
    recommendationReasonV4: api.recommendationReasonV4 ?? api.recommendation_reason_v4 ?? undefined,
    reasonFacts: api.reasonFacts ?? api.reason_facts ?? null,
    explanation: api.explanation ?? undefined,
    actionSuggestion: api.actionSuggestion ?? api.action_suggestion ?? undefined,
    imageUrl: api.imageUrl ?? api.image_url,
    tags: api.goriyaku_tags?.map((tag) => tag.name) ?? [],
    latitude: typeof api.latitude === "number" ? api.latitude : undefined,
    longitude: typeof api.longitude === "number" ? api.longitude : undefined,
  };
}

export default function ShrineDetail() {
  const params = useLocalSearchParams<{
    id?: string | string[];
    recommendationReasonV4?: string | string[];
    reasonFacts?: string | string[];
    recommendationReasonDetail?: string | string[];
  }>();
  const shrineId = React.useMemo(() => {
    const raw = params.id;
    if (!raw) return undefined;
    return Array.isArray(raw) ? raw[0] : raw;
  }, [params.id]);

  const contextRecommendationReasonV4 = React.useMemo(() => {
    const raw = params.recommendationReasonV4;
    const value = Array.isArray(raw) ? raw[0] : raw;
    return asTrimmedString(value) ?? undefined;
  }, [params.recommendationReasonV4]);

  const contextReasonFacts = React.useMemo<RecommendationReasonFacts | null>(() => {
    const raw = params.reasonFacts;
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (!value) return null;

    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed)
        ? (parsed as RecommendationReasonFacts)
        : null;
    } catch {
      return null;
    }
  }, [params.reasonFacts]);

  const contextRecommendationReasonDetail = React.useMemo<RecommendationReasonDetail | null>(() => {
    const raw = params.recommendationReasonDetail;
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (!value) return null;

    try {
      const parsed = JSON.parse(value);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;

      const detail: RecommendationReasonDetail = {
        heroMeaningCopy: asTrimmedString((parsed as any).heroMeaningCopy ?? (parsed as any).hero_meaning_copy),
        consultationSummary: asTrimmedString((parsed as any).consultationSummary ?? (parsed as any).consultation_summary),
        shrineMeaning: asTrimmedString((parsed as any).shrineMeaning ?? (parsed as any).shrine_meaning),
        actionMeaning: asTrimmedString((parsed as any).actionMeaning ?? (parsed as any).action_meaning),
      };

      return detail.heroMeaningCopy || detail.consultationSummary || detail.shrineMeaning || detail.actionMeaning ? detail : null;
    } catch {
      return null;
    }
  }, [params.recommendationReasonDetail]);

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

  const reasonFactItems = buildReasonFactItems(contextReasonFacts ?? shrine?.reasonFacts).slice(0, 3);

  const hasConsultationSummary = Boolean(contextRecommendationReasonDetail?.consultationSummary);
  const hasMeaningConnection = Boolean(
    contextRecommendationReasonDetail?.shrineMeaning || contextRecommendationReasonDetail?.actionMeaning,
  );

  const recommendationReason = React.useMemo(() => {
    if (!shrine) return undefined;
    return resolveRecommendationReason({
      ...shrine,
      recommendationReasonV4: contextRecommendationReasonV4 ?? shrine.recommendationReasonV4,
      reasonFacts: contextReasonFacts ?? shrine.reasonFacts,
    });
  }, [contextReasonFacts, contextRecommendationReasonV4, shrine]);

  const explanation = React.useMemo(() => {
    if (!shrine) return undefined;
    return shrine.explanation ?? shrine.description ?? `${shrine.name}の由緒やご利益を確認しながら、今の自分に必要な意味を探しやすい神社です。`;
  }, [shrine]);

  const actionSuggestion = React.useMemo(() => {
    if (!shrine) return undefined;
    return shrine.actionSuggestion ?? "参拝前に、今考えていることを一つだけ言葉にしてから向かうと、帰ってきたあとに変化を振り返りやすくなります。";
  }, [shrine]);

  const countedRef = React.useRef(false);
  const detailTrackedRef = React.useRef<string | null>(null);

  useFocusEffect(
    React.useCallback(() => {
      if (!countedRef.current) {
        countedRef.current = true;
        incVisits(1).catch(() => {});
      }

      const shrineIdNumber = apiShrineId != null ? Number(apiShrineId) : null;
      const detailTrackKey = shrineIdNumber != null && Number.isFinite(shrineIdNumber) && shrineIdNumber > 0
        ? String(shrineIdNumber)
        : null;

      if (shrineIdNumber != null && detailTrackKey && detailTrackedRef.current !== detailTrackKey) {
        detailTrackedRef.current = detailTrackKey;
        void trackShrineDetailView({
          shrineId: shrineIdNumber,
          source: "mobile_shrine_detail",
          metadata: {
            ctx: "mobile_shrine_detail",
          },
        });
      }

      return () => {};
    }, [apiShrineId]),
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
    const shrineIdNumber = apiShrineId != null ? Number(apiShrineId) : null;
    if (shrineIdNumber != null && Number.isFinite(shrineIdNumber) && shrineIdNumber > 0) {
      void trackShrineRouteOpen({
        shrineId: shrineIdNumber,
        source: "mobile_shrine_detail",
        metadata: {
          ctx: "mobile_shrine_detail",
        },
      });
    }
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
  }, [apiShrineId, shrine]);

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
        <Pressable onPress={() => (router.canGoBack() ? router.back() : router.replace("/"))} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 戻る</Text>
        </Pressable>
        <Pressable
          onPress={onToggleFav}
          style={[styles.favBtn, fav && styles.favBtnActive]}
          accessibilityRole="button"
          accessibilityLabel="お気に入りの切り替え"
        >
          <Text style={[styles.favBtnText, fav && styles.favBtnTextActive]}>{fav ? "♡ 登録済み" : "♡ お気に入り"}</Text>
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
        <Text style={styles.cardTitle}>この神社が候補に入った理由</Text>
        <Text style={styles.cardBody}>{recommendationReason}</Text>
      </View>

      {reasonFactItems.length > 0 ? (
        <View style={styles.reasonFactsCard}>
          <Text style={styles.reasonFactsLabel}>選定のポイント</Text>
          {reasonFactItems.map((item) => (
            <View key={`${item.label}-${item.value}`} style={styles.reasonFactItem}>
              <Text style={styles.reasonFactLabel}>{item.label}</Text>
              <Text style={styles.reasonFactText}>{item.value}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {hasConsultationSummary ? (
        <View style={styles.contextCard}>
          <Text style={styles.cardTitle}>今回の相談の整理</Text>
          {contextRecommendationReasonDetail?.consultationSummary ? (
            <Text style={styles.cardBody}>{contextRecommendationReasonDetail.consultationSummary}</Text>
          ) : null}
        </View>
      ) : null}

      {hasMeaningConnection ? (
        <View style={styles.meaningCard}>
          <Text style={styles.cardTitle}>神社との意味の接続</Text>
          {contextRecommendationReasonDetail?.shrineMeaning ? (
            <Text style={styles.cardBody}>{contextRecommendationReasonDetail.shrineMeaning}</Text>
          ) : null}
          {contextRecommendationReasonDetail?.actionMeaning ? (
            <View style={styles.meaningActionBlock}>
              <Text style={styles.meaningActionLabel}>参拝前の問い</Text>
              <Text style={styles.cardBody}>{contextRecommendationReasonDetail.actionMeaning}</Text>
            </View>
          ) : null}
        </View>
      ) : null}

      {/* explanation */}
      <View style={styles.explanationCard}>
        <Text style={styles.cardTitle}>神社の意味を知る</Text>
        <Text style={styles.cardBody}>{explanation}</Text>
      </View>

      {/* action suggestion */}
      <View style={styles.actionCard}>
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
          <Text style={styles.cardTitle}>参拝後の振り返り</Text>
          <Text style={styles.cardBody}>
            参拝して感じたことを残しておくと、次の相談や再訪時に自分の変化を見返しやすくなります。
          </Text>
          <Pressable style={styles.reflectionButton} onPress={() => router.push("/records")}>
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
  contextCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surfaceSoft,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  meaningCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  meaningActionBlock: {
    marginTop: spacing.smGap,
    gap: spacing.tightGap,
  },
  meaningActionLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.1,
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
  reasonFactsCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.mdGap,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.mdGap,
  },
  reasonFactsLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1.1,
  },
  reasonFactItem: {
    gap: spacing.tightGap,
  },
  reasonFactLabel: {
    color: theme.muted,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.4,
  },
  reasonFactText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
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
