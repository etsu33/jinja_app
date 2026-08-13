// apps/mobile/app/shrines/[id].tsx
import * as React from "react";
import { View, Text, Image, Pressable, StyleSheet, ScrollView, Linking, Platform, TextInput } from "react-native";
import { useLocalSearchParams, useRouter, useFocusEffect } from "expo-router";
import { SHRINES } from "../../data/shrines";
import { incVisits, isFavorite, toggleFavorite, pushRecent } from "../../lib/storage";
import { kamimusubiDark as theme } from "../../design/theme";
import { get, isUnauthenticatedError } from "../../lib/http";
import { isLoggedIn } from "../../lib/authTokens";
import { trackShrineDetailView, trackShrineRouteOpen } from "../../lib/shrineInteractions";
import { trackRouteOpen } from "../../lib/searchAnalytics";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { ctaSizes } from "../../design/ctaSizes";
import { createFavoriteByShrineId } from "../../lib/favorites";
import { createVisitByShrineId } from "../../lib/visits";
import { createShrineReflection } from "../../lib/reflections";
import {
  trackVisitDone,
  trackReflectionPromptView,
  trackReflectionSaved,
  trackReflectionToConsultationClick,
} from "../../lib/visitReflectionAnalytics";
import { AuthPrompt } from "../../components/common/AuthPrompt";
import Button from "../../components/ui/Button";
import { ShrineKnowledgeFactSection } from "../../components/shrine/ShrineKnowledgeFactSection";
import {
  buildReasonV4Sections,
  normalizeRecommendationReasonV4Detail,
  type RecommendationReasonV4Detail,
} from "../../lib/recommendationReasonV4";
import { buildShrineFactViewModel, type ShrineDeity, type ShrineHistory } from "../../lib/shrineKnowledgeFact";
import { track } from "../../lib/analytics";
import {
  buildReasonFactItems,
  findPrimaryReasonFact,
  normalizeRecommendationReasonFacts,
  type ConciergeReasonFacts,
} from "../../lib/recommendationReasonFacts";
import {
  recommendationAnalyticsProperties,
  recommendationAnalyticsProvenance,
} from "../../../../packages/shared/recommendationAnalyticsProvenance";



type RecommendationReasonDetail = {
  heroMeaningCopy?: string | null;
  consultationSummary?: string | null;
  shrineMeaning?: string | null;
  actionMeaning?: string | null;
};

type ActionSuggestionV4Action = {
  label?: string | null;
  description?: string | null;
};

type ActionSuggestionV4ReflectionPrompt = {
  question?: string | null;
};

type ActionSuggestionV4Preview = {
  preview?: boolean;
  primaryAction?: ActionSuggestionV4Action | null;
  primary_action?: ActionSuggestionV4Action | null;
  secondaryAction?: ActionSuggestionV4Action | null;
  secondary_action?: ActionSuggestionV4Action | null;
  reflectionPrompt?: ActionSuggestionV4ReflectionPrompt | null;
  reflection_prompt?: ActionSuggestionV4ReflectionPrompt | null;
  actionSource?: { source?: string | null } | null;
  action_source?: { source?: string | null } | null;
  sourceKeys?: string[];
  source_keys?: string[];
};

type RecommendationExplanation =
  | string
  | {
      summary?: string | null;
      reasons?: Array<{
        text?: string | null;
        label?: string | null;
      }> | null;
    }
  | null;

type Shrine = {
  id: string | number;
  name: string;
  prefecture?: string;
  description?: string;
  recommendationReason?: string;
  recommendationReasonV4?: string;
  reasonFacts?: ConciergeReasonFacts | null;
  explanation?: RecommendationExplanation;
  actionSuggestion?: string;
  actionSuggestionV4Preview?: ActionSuggestionV4Preview | null;
  imageUrl?: string;
  tags?: string[];
  latitude?: number;
  longitude?: number;
  // Knowledge Fact（PR-M1）。UIはまだこれらを描画しない。
  // Backendが既にhidden相当を除外して返したfull/disputed相当のFactのみが入る。
  deities?: ShrineDeity[];
  histories?: ShrineHistory[];
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
  reason_facts?: unknown;
  reasonFacts?: unknown;
  explanation?: RecommendationExplanation;
  action_suggestion?: string | null;
  actionSuggestion?: string | null;
  action_suggestion_v4_preview?: ActionSuggestionV4Preview | null;
  actionSuggestionV4Preview?: ActionSuggestionV4Preview | null;
  imageUrl?: string;
  image_url?: string;
  latitude?: number | null;
  longitude?: number | null;
  goriyaku?: string | null;
  goriyaku_tags?: Array<{ id: number; name: string; category?: string }>;
  // backend/temples/api/serializers/shrine.py ShrineDetailSerializer.get_deities/get_histories
  // に一致する（PR-M1。Evidence Gate判定はBackendが既に済ませたfull/disputed相当のみ返る）。
  deities?: ShrineDeity[];
  histories?: ShrineHistory[];
};

const SHRINE_API_ID_BY_LOCAL_ID: Record<string, string> = {
  fushimi: "2",
};

function asTrimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function resolveExplanationText(
  explanation: RecommendationExplanation | undefined,
  fallback?: string,
): string | undefined {
  if (typeof explanation === "string") {
    const value = asTrimmedString(explanation);
    if (value) return value;
  }

  if (explanation && typeof explanation === "object") {
    const summary = asTrimmedString(explanation.summary);
    if (summary) return summary;

    const reasonText = explanation.reasons
      ?.map((reason) => asTrimmedString(reason?.text))
      .find((text): text is string => Boolean(text));

    if (reasonText) return reasonText;
  }

  return fallback;
}

function resolveRecommendationReason(shrine: Shrine) {
  const v4Reason = asTrimmedString(shrine.recommendationReasonV4);
  if (v4Reason) return v4Reason;

  const factBasedReason = asTrimmedString(findPrimaryReasonFact(shrine.reasonFacts)?.label);

  if (factBasedReason) return factBasedReason;

  const legacyReason = asTrimmedString(shrine.recommendationReason);
  if (legacyReason) return legacyReason;

  return "相談内容と神社情報をもとに選ばれた神社です。";
}

function toShrine(api: ShrineApiResponse): Shrine {
  return {
    id: api.id,
    name: api.name_jp ?? api.name ?? "名称未設定の神社",
    prefecture: api.prefecture ?? api.address,
    description: api.description ?? api.goriyaku ?? undefined,
    recommendationReason: api.recommendationReason ?? api.recommendation_reason ?? undefined,
    recommendationReasonV4: api.recommendationReasonV4 ?? api.recommendation_reason_v4 ?? undefined,
    reasonFacts: normalizeRecommendationReasonFacts(api.reasonFacts ?? api.reason_facts),
    explanation: api.explanation ?? undefined,
    actionSuggestion: api.actionSuggestion ?? api.action_suggestion ?? undefined,
    actionSuggestionV4Preview: api.actionSuggestionV4Preview ?? api.action_suggestion_v4_preview ?? null,
    imageUrl: api.imageUrl ?? api.image_url,
    tags: api.goriyaku_tags?.map((tag) => tag.name) ?? [],
    latitude: typeof api.latitude === "number" ? api.latitude : undefined,
    longitude: typeof api.longitude === "number" ? api.longitude : undefined,
    // Fact本文・confidence・sourcesは加工せずそのまま保持する（PR-M1）。
    deities: Array.isArray(api.deities) ? api.deities : [],
    histories: Array.isArray(api.histories) ? api.histories : [],
  };
}

export default function ShrineDetail() {
  const params = useLocalSearchParams<{
    id?: string | string[];
    recommendationReasonV4?: string | string[];
    reasonFacts?: string | string[];
    recommendationReasonDetail?: string | string[];
    actionSuggestionV4Preview?: string | string[];
    recommendationReasonV4Detail?: string | string[];
    recommendationRank?: string | string[];
    resultSetId?: string | string[];
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

  const contextReasonFacts = React.useMemo<ConciergeReasonFacts>(() => {
    const raw = params.reasonFacts;
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (!value) return [];

    try {
      const parsed = JSON.parse(value);
      return normalizeRecommendationReasonFacts(parsed);
    } catch {
      return [];
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

  const contextActionSuggestionV4Preview = React.useMemo<ActionSuggestionV4Preview | null>(() => {
    const raw = params.actionSuggestionV4Preview;
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (!value) return null;

    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed)
        ? (parsed as ActionSuggestionV4Preview)
        : null;
    } catch {
      return null;
    }
  }, [params.actionSuggestionV4Preview]);

  const contextReasonV4Detail = React.useMemo<RecommendationReasonV4Detail | null>(() => {
    const raw = params.recommendationReasonV4Detail;
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (!value) return null;

    try {
      const parsed = JSON.parse(value);
      return normalizeRecommendationReasonV4Detail(parsed);
    } catch {
      return null;
    }
  }, [params.recommendationReasonV4Detail]);

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
  const [visitSaving, setVisitSaving] = React.useState(false);
  const [reflectionAnswer, setReflectionAnswer] = React.useState("");
  const [reflectionSaved, setReflectionSaved] = React.useState(false);
  const [reflectionSaving, setReflectionSaving] = React.useState(false);
  const [authPromptVisible, setAuthPromptVisible] = React.useState(false);
  const shrine = apiShrine ?? localShrine;
  const tags = shrine?.tags ?? [];

  // Knowledge Fact ViewModel（PR-M1のbuildShrineFactViewModel()をそのまま利用）。
  // Evidence利用可否の再判定はここでは行わない。Backendが既にhidden相当を除外して
  // 返したfull/disputed相当のFactを、表示用の形へ変換するだけ。
  const factViewModel = React.useMemo(
    () => buildShrineFactViewModel(shrine ?? {}),
    [shrine],
  );

  const effectiveReasonFacts = contextReasonFacts.length > 0 ? contextReasonFacts : shrine?.reasonFacts;
  const reasonFactItems = buildReasonFactItems(effectiveReasonFacts).slice(0, 3);

  const hasConsultationSummary = Boolean(contextRecommendationReasonDetail?.consultationSummary);
  const hasShrineMeaning = Boolean(contextRecommendationReasonDetail?.shrineMeaning);
  const hasActionMeaning = Boolean(contextRecommendationReasonDetail?.actionMeaning);

  const recommendationReason = React.useMemo(() => {
    if (!shrine) return undefined;
    return resolveRecommendationReason({
      ...shrine,
      recommendationReasonV4: contextRecommendationReasonV4 ?? shrine.recommendationReasonV4,
      reasonFacts: effectiveReasonFacts,
    });
  }, [contextRecommendationReasonV4, effectiveReasonFacts, shrine]);

  // Concierge以外の遷移ではcontextReasonV4Detailがnullのため常にhasStructured=falseとなり、
  // 神社APIの値から相談文脈を推測することはない(v4 detailはroute params専用でShrine型に持たせていない)
  const reasonV4Sections = buildReasonV4Sections({
    detail: contextReasonV4Detail,
    fallbackReason: recommendationReason ?? null,
  });
  const hasStructuredReasonV4 = reasonV4Sections.hasStructured;
  const hideReasonFactsCard = Boolean(reasonV4Sections.factText);

  const explanation = React.useMemo(() => {
    if (!shrine) return undefined;
    return resolveExplanationText(
      shrine.explanation,
      shrine.description ?? `${shrine.name}の由緒やご利益を確認しながら、今の自分に必要な意味を探しやすい神社です。`,
    );
  }, [shrine]);

  const actionSuggestion = React.useMemo(() => {
    if (!shrine) return undefined;
    return shrine.actionSuggestion ?? "参拝前に、今考えていることを一つだけ言葉にしてから向かうと、帰ってきたあとに変化を振り返りやすくなります。";
  }, [shrine]);

  const actionSuggestionV4Preview = contextActionSuggestionV4Preview ?? shrine?.actionSuggestionV4Preview ?? null;
  const analyticsProvenance = recommendationAnalyticsProvenance({
    reasonFacts: contextReasonFacts.length > 0 ? contextReasonFacts : shrine?.reasonFacts,
    actionSuggestionPreview: actionSuggestionV4Preview,
  });
  const analyticsProperties = recommendationAnalyticsProperties(analyticsProvenance);
  const primaryHistoryTheme = (() => {
    const primary = findPrimaryReasonFact(contextReasonFacts.length > 0 ? contextReasonFacts : shrine?.reasonFacts);
    return primary?.type === "history_theme" ? primary.label : "";
  })();
  const primaryAction = actionSuggestionV4Preview?.primaryAction ?? actionSuggestionV4Preview?.primary_action ?? null;
  const secondaryAction = actionSuggestionV4Preview?.secondaryAction ?? actionSuggestionV4Preview?.secondary_action ?? null;
  const reflectionPrompt = actionSuggestionV4Preview?.reflectionPrompt ?? actionSuggestionV4Preview?.reflection_prompt ?? null;
  const shouldShowActionSuggestionV4 = actionSuggestionV4Preview?.preview === true && Boolean(
    asTrimmedString(primaryAction?.label) ||
    asTrimmedString(primaryAction?.description) ||
    asTrimmedString(secondaryAction?.label) ||
    asTrimmedString(secondaryAction?.description) ||
    asTrimmedString(reflectionPrompt?.question),
  );

  const countedRef = React.useRef(false);
  const detailTrackedRef = React.useRef<string | null>(null);
  const visitInFlightRef = React.useRef(false);

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
            recommendation_rank: Number(Array.isArray(params.recommendationRank) ? params.recommendationRank[0] : params.recommendationRank) || null,
            result_set_id: Array.isArray(params.resultSetId) ? params.resultSetId[0] : params.resultSetId,
            ...analyticsProperties,
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

    if (!(await isLoggedIn())) {
      setAuthPromptVisible(true);
      return;
    }

    const now = await toggleFavorite(String(shrineId));
    setFav(now);
    track("favorite_click", {
      source: "shrine_detail",
      platform: "mobile",
      shrineId: apiShrineId ?? shrineId,
      nextFav: now,
      ...analyticsProperties,
    });

    if (now) {
      try {
        await createFavoriteByShrineId(apiShrineId ?? shrineId);
      } catch (error) {
        if (isUnauthenticatedError(error)) {
          setAuthPromptVisible(true);
        }
      }
    }
  };

  const onVisitDone = React.useCallback(async () => {
    const targetShrineId = apiShrineId ?? shrineId;
    if (!targetShrineId || visited || visitInFlightRef.current) return;

    visitInFlightRef.current = true;
    setVisitSaving(true);
    try {
      if (!(await isLoggedIn())) {
        setAuthPromptVisible(true);
        return;
      }

      const result = await createVisitByShrineId(targetShrineId);
      if (!result) return;

      setVisited(true);
      trackVisitDone({
        shrineId: targetShrineId,
        historyTheme: primaryHistoryTheme,
        provenance: analyticsProvenance,
      });
    } catch (error) {
      if (isUnauthenticatedError(error)) {
        setAuthPromptVisible(true);
      }
    } finally {
      visitInFlightRef.current = false;
      setVisitSaving(false);
    }
  }, [apiShrineId, contextReasonFacts, shrine, shrineId, visited]);

  React.useEffect(() => {
    const targetShrineId = apiShrineId ?? shrineId;
    if (!visited || !targetShrineId) return;

    trackReflectionPromptView({
      shrineId: targetShrineId,
      historyTheme: primaryHistoryTheme,
      reflectionFormType: "one_line",
      reflectionContext: "visit_done",
      provenance: analyticsProvenance,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visited]);

  const onSaveReflection = React.useCallback(async () => {
    const targetShrineId = apiShrineId ?? shrineId;
    const answer = reflectionAnswer.trim();
    if (!targetShrineId || !answer || reflectionSaving) return;

    setReflectionSaving(true);
    try {
      const saved = await createShrineReflection({
        shrineId: targetShrineId,
        answer,
        prompt: asTrimmedString(reflectionPrompt?.question) ?? "参拝後に何を感じましたか？",
        historyTheme: primaryHistoryTheme,
        moodBefore: "",
        moodAfter: "",
      });

      if (saved) {
        setReflectionSaved(true);
        trackReflectionSaved({
          shrineId: targetShrineId,
          historyTheme: primaryHistoryTheme,
          reflectionFormType: "one_line",
          reflectionContext: "visit_done",
          answerLength: answer.length,
          provenance: analyticsProvenance,
        });
      }
    } catch (error) {
      if (isUnauthenticatedError(error)) {
        setAuthPromptVisible(true);
      }
    } finally {
      setReflectionSaving(false);
    }
  }, [apiShrineId, contextReasonFacts, reflectionAnswer, reflectionPrompt, reflectionSaving, shrine, shrineId]);

  // 保存成功直後のCTAからのみ呼ばれる(reflectionSaved===trueの間だけボタンが描画される)。
  // 自動遷移は行わず、ユーザーがCTAを押した場合のみConciergeへ進む。
  const consultationNavigatingRef = React.useRef(false);
  const onGoToConsultation = React.useCallback(() => {
    if (consultationNavigatingRef.current) return;
    consultationNavigatingRef.current = true;
    // 連打時の重複遷移・重複Analyticsのみを防ぐための短時間ガード。
    // 画面へ戻ってきた後は再びCTAを押せるよう、一定時間で解除する。
    setTimeout(() => {
      consultationNavigatingRef.current = false;
    }, 1000);

    const targetShrineId = apiShrineId ?? shrineId;
    trackReflectionToConsultationClick({
      shrineId: targetShrineId ?? "",
      historyTheme: primaryHistoryTheme,
      provenance: analyticsProvenance,
    });

    // Reflection本文・相談文等の自由入力は一切引き継がず、Conciergeを通常状態で開く
    // (安全に本文を引き継げる既存契約が無いため。docs/product/visit-reflection-flow.md「次回相談との接続」参照)。
    router.push("/concierge");
  }, [apiShrineId, contextReasonFacts, router, shrine, shrineId]);

  const openDirections = React.useCallback(() => {
    if (!shrine) return;
    const shrineIdNumber = apiShrineId != null ? Number(apiShrineId) : null;
    if (shrineIdNumber != null && Number.isFinite(shrineIdNumber) && shrineIdNumber > 0) {
      void trackShrineRouteOpen({
        shrineId: shrineIdNumber,
        source: "mobile_shrine_detail",
        metadata: {
          ctx: "mobile_shrine_detail",
          recommendation_rank: Number(Array.isArray(params.recommendationRank) ? params.recommendationRank[0] : params.recommendationRank) || null,
          result_set_id: Array.isArray(params.resultSetId) ? params.resultSetId[0] : params.resultSetId,
          ...analyticsProperties,
        },
      });
      // Backend保存用(trackShrineRouteOpen)とは別に、PostHog等で可視化するための
      // track()イベントをWeb版のroute_openと同じ名前・意味で送る。
      trackRouteOpen({ shrineId: shrineIdNumber, provenance: analyticsProvenance });
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
    <>
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

        {hasConsultationSummary ? (
          <View style={styles.contextCard}>
            <Text style={styles.cardTitle}>① 今回の相談の整理</Text>
            {contextRecommendationReasonDetail?.consultationSummary ? (
              <Text style={styles.cardBody}>{contextRecommendationReasonDetail.consultationSummary}</Text>
            ) : null}
          </View>
        ) : null}

        {/* 推薦理由(構造化Reason V4がある場合はfactを、無ければ旧recommendationReasonを表示) */}
        {hasStructuredReasonV4 ? (
          reasonV4Sections.factText ? (
            <View style={styles.recommendationCard}>
              <Text style={styles.cardTitle}>② 選ばれた背景</Text>
              <Text style={styles.cardBody}>{reasonV4Sections.factText}</Text>
            </View>
          ) : null
        ) : (
          <View style={styles.recommendationCard}>
            <Text style={styles.cardTitle}>② 選ばれた理由</Text>
            <Text style={styles.cardBody}>{recommendationReason}</Text>
          </View>
        )}

        {!hideReasonFactsCard && reasonFactItems.length > 0 ? (
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

        {hasStructuredReasonV4 ? (
          reasonV4Sections.interpretationText ? (
            <View style={styles.meaningCard}>
              <Text style={styles.cardTitle}>③ 今回の相談との意味</Text>
              <Text style={styles.cardBody}>{reasonV4Sections.interpretationText}</Text>
            </View>
          ) : null
        ) : hasShrineMeaning ? (
          <View style={styles.meaningCard}>
            <Text style={styles.cardTitle}>③ この神社で受け取る意味</Text>
            <Text style={styles.cardBody}>{contextRecommendationReasonDetail?.shrineMeaning}</Text>
          </View>
        ) : null}

        {hasStructuredReasonV4 ? (
          reasonV4Sections.actionText ? (
            <View style={styles.actionCard}>
              <Text style={styles.cardTitle}>④ 参拝するときの視点</Text>
              <Text style={styles.cardBody}>{reasonV4Sections.actionText}</Text>
            </View>
          ) : null
        ) : hasActionMeaning ? (
          <View style={styles.actionCard}>
            <Text style={styles.cardTitle}>④ 参拝するときの視点</Text>
            <Text style={styles.cardBody}>{contextRecommendationReasonDetail?.actionMeaning}</Text>
          </View>
        ) : null}

        {/* explanation */}
        <View style={styles.explanationCard}>
          <Text style={styles.cardTitle}>神社の意味を知る</Text>
          <Text style={styles.cardBody}>{explanation}</Text>
        </View>

        {/* action suggestion */}
        {shouldShowActionSuggestionV4 ? (
          <View style={styles.actionCard}>
            <Text style={styles.cardEyebrow}>NEXT ACTION</Text>
            <Text style={styles.cardTitle}>参拝前にできること</Text>
            {asTrimmedString(primaryAction?.label) ? (
              <Text style={styles.actionV4Title}>{primaryAction?.label}</Text>
            ) : null}
            {asTrimmedString(primaryAction?.description) ? (
              <Text style={styles.cardBody}>{primaryAction?.description}</Text>
            ) : null}
            {asTrimmedString(secondaryAction?.label) || asTrimmedString(secondaryAction?.description) ? (
              <View style={styles.actionV4SecondaryBlock}>
                {asTrimmedString(secondaryAction?.label) ? (
                  <Text style={styles.actionV4SubTitle}>{secondaryAction?.label}</Text>
                ) : null}
                {asTrimmedString(secondaryAction?.description) ? (
                  <Text style={styles.cardBody}>{secondaryAction?.description}</Text>
                ) : null}
              </View>
            ) : null}
            {asTrimmedString(reflectionPrompt?.question) ? (
              <View style={styles.actionV4SecondaryBlock}>
                <Text style={styles.meaningActionLabel}>参拝前の問い</Text>
                <Text style={styles.cardBody}>{reflectionPrompt?.question}</Text>
              </View>
            ) : null}
          </View>
        ) : (
          <View style={styles.actionCard}>
            <Text style={styles.cardTitle}>参拝前にできること</Text>
            <Text style={styles.cardBody}>{actionSuggestion}</Text>
          </View>
        )}

        {/* 祭神・由緒（Knowledge Fact）。Legacy「神社について」とは独立した表示責務。
            Knowledge未登録（deities/historiesとも空）時の非表示判定はcomponent内部で行う。
            Legacy Fieldの表示・非表示には一切影響しない。 */}
        <ShrineKnowledgeFactSection factViewModel={factViewModel} />

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
          <Button
            title="地図で経路を確認する"
            variant="outline"
            onPress={openDirections}
            accessibilityLabel="地図で経路を確認する"
          />
          <Button
            title={visited ? "参拝済みとして記録しました" : "参拝したことを記録する"}
            variant={visited ? "success" : "primary"}
            onPress={onVisitDone}
            disabled={visitSaving || visited}
            loading={visitSaving}
            accessibilityLabel={visited ? "参拝済みとして記録しました" : "参拝したことを記録する"}
          />
        </View>

        {visited ? (
          <View style={styles.reflectionCard}>
            <Text style={styles.cardTitle}>参拝後の振り返り</Text>
            <Text style={styles.cardBody}>
              参拝して感じたことを残しておくと、次の相談や再訪時に自分の変化を見返しやすくなります。
            </Text>
            <TextInput
              value={reflectionAnswer}
              onChangeText={(text) => {
                setReflectionAnswer(text);
                if (reflectionSaved) setReflectionSaved(false);
              }}
              placeholder="参拝して感じたことを一言で残す"
              placeholderTextColor={theme.muted}
              multiline
              style={styles.reflectionInput}
              textAlignVertical="top"
            />
            <Button
              title={reflectionSaved ? "振り返りを保存しました" : "振り返りを保存する"}
              variant={reflectionSaved ? "success" : "outline"}
              onPress={onSaveReflection}
              disabled={!reflectionAnswer.trim()}
              loading={reflectionSaving}
              accessibilityLabel={reflectionSaved ? "振り返りを保存しました" : "振り返りを保存する"}
            />

            {reflectionSaved ? (
              <View style={styles.nextConsultationWrap}>
                <Button
                  title="この体験をもとに、もう一度相談する"
                  variant="outline"
                  onPress={onGoToConsultation}
                  accessibilityLabel="この体験をもとに、もう一度相談する"
                />
              </View>
            ) : null}
          </View>
        ) : null}
      </ScrollView>
      <AuthPrompt visible={authPromptVisible} onClose={() => setAuthPromptVisible(false)} />
    </>
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
  actionV4Title: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "900",
  },
  actionV4SubTitle: {
    color: theme.goldSoft,
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "900",
  },
  actionV4SecondaryBlock: {
    marginTop: spacing.smGap,
    gap: spacing.tightGap,
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
  nextConsultationWrap: {
    marginTop: spacing.smGap,
  },
  reflectionInput: {
    minHeight: 96,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    backgroundColor: theme.surfaceSoft,
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
    paddingHorizontal: cardSizes.cardPaddingMd,
    paddingVertical: spacing.mdGap,
  },
});
