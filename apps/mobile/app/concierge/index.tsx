import * as React from "react";
import {
  KeyboardAvoidingView,
  Platform,
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  StyleSheet,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Location from "expo-location";
import { kamimusubiDark as theme } from "../../design/theme";
import { shadows } from "../../design/shadow";
import { ConditionFieldsCard } from "../../components/ConditionFieldsCard";
import Button from "../../components/ui/Button";
import {
  buildConditionFilters,
  buildConditionProfileContext,
  resolveGoriyakuTagIds,
  type ConditionFilters,
  type ConditionState,
  type ProfileContextPayload,
} from "../../lib/conditionPayload";
import { post } from "../../lib/http";
import { trackActionEvent, type ActionEventActionType } from "../../lib/actionEvents";
import { useProfileStore } from "../../store/profileStore";
import {
  directionReferenceMatchCopy,
  validDirectionReferenceOrNull,
  type DirectionReference,
} from "../../../../packages/shared/directionReference";
import { toOriginPayload, type UserOrigin } from "../../../../packages/shared/userOrigin";
import { buildRecommendationReasonDisplay } from "../../../../packages/shared/recommendationReasonDisplay";
import { getOriginSession } from "../../lib/originSession";
import { trackMobileDirection } from "../../lib/directionEvents";
import { track } from "../../lib/analytics";
import {
  buildRecommendationResultSetId,
  recommendationAnalyticsProperties,
  recommendationAnalyticsProvenance,
  type RecommendationAnalyticsProvenance,
} from "../../../../packages/shared/recommendationAnalyticsProvenance";
import {
  buildReasonV4Sections,
  normalizeRecommendationReasonV4Detail,
  serializeReasonV4Detail,
  type RecommendationReasonV4Detail,
} from "../../lib/recommendationReasonV4";
import {
  buildReasonFactItems,
  findPrimaryReasonFact,
  normalizeRecommendationReasonFacts,
  resolveActionEventHistoryTheme,
  type ConciergeReasonFacts,
} from "../../lib/recommendationReasonFacts";

// ────────────────────────────────────────────
// 型
// ────────────────────────────────────────────
type RecommendationReasonQuality = {
  shrine_data_rate?: number | null;
  consultation_reflection_rate?: number | null;
  fallback_reason_rate?: number | null;
  evidence_rate?: number | null;
  action_grounding_rate?: number | null;
  is_ai_inference_only?: boolean | null;
  fallback_source?: string | null;
};

type RecommendationReasonDetail = {
  heroMeaningCopy?: string | null;
  consultationSummary?: string | null;
  shrineMeaning?: string | null;
  actionMeaning?: string | null;
};
type RecommendationCard = {
  id: string;
  name: string;
  area: string;
  connection: string;
  reason: string;
  recommendationReasonV4?: string | null;
  reasonFacts: ConciergeReasonFacts;
  recommendationReasonQuality?: RecommendationReasonQuality | null;
  recommendationReasonDetail?: RecommendationReasonDetail | null;
  reasonV4Detail?: RecommendationReasonV4Detail | null;
  tags: string[];
  shrineId?: string;
  actionSuggestionV4Preview?: ActionSuggestionV4Preview | null;
  directionReference?: DirectionReference | null;
  analyticsProvenance: RecommendationAnalyticsProvenance;
};

type ActionSuggestionV4Action = {
  label: string;
  description: string;
  actionType: "detail_open" | "route_open" | "save" | "visit" | "reflect" | "pause";
  confidence: number;
};

type ActionSuggestionV4ReflectionPrompt = {
  question: string;
  promptType: "before_visit" | "after_visit" | "decision" | "emotion" | "constraint";
  sourceSeed: string;
};

type ActionSuggestionV4Source = {
  source:
    | "decision_context"
    | "constraint_profile"
    | "outcome_hint"
    | "action_context"
    | "reflection_question_seed"
    | "fallback";
  reason: string;
};

type ActionSuggestionV4Preview = {
  primaryAction: ActionSuggestionV4Action;
  secondaryAction: ActionSuggestionV4Action;
  reflectionPrompt: ActionSuggestionV4ReflectionPrompt;
  actionSource: ActionSuggestionV4Source;
  preview: boolean;
  version: "v4";
  sourceKeys: string[];
};

type RecommendationApiCard = {
  id?: string | number;
  name?: string;
  display_name?: string;
  area?: string;
  location?: string;
  address?: string;
  formatted_address?: string;
  connection?: string;
  reason?: string;
  recommendation_reason_v4?: string | null;
  recommendationReasonV4?: string | null;
  reason_facts?: unknown;
  reasonFacts?: unknown;
  recommendation_reason_quality?: RecommendationReasonQuality | null;
  recommendationReasonQuality?: RecommendationReasonQuality | null;
  recommendation_reason_detail?: RecommendationReasonDetail | null;
  recommendationReasonDetail?: RecommendationReasonDetail | null;
  reason_detail?: RecommendationReasonDetail | null;
  reasonDetail?: RecommendationReasonDetail | null;
  recommendation_reason_v4_detail?: unknown;
  recommendationReasonV4Detail?: unknown;
  tags?: string[];
  shrineId?: string | number;
  shrine_id?: string | number;
  place_id?: string | number;
  action_suggestion_v4_preview?: unknown;
  actionSuggestionV4Preview?: unknown;
  direction_reference?: DirectionReference | null;
  primary_reason_source?: string | null;
  _primary_reason_source?: string | null;
};
function normalizeRecommendationReasonDetail(raw: unknown): RecommendationReasonDetail | null {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;

  const value = raw as any;
  const detail: RecommendationReasonDetail = {
    heroMeaningCopy: asTrimmedString(value.heroMeaningCopy ?? value.hero_meaning_copy),
    consultationSummary: asTrimmedString(value.consultationSummary ?? value.consultation_summary),
    shrineMeaning: asTrimmedString(value.shrineMeaning ?? value.shrine_meaning),
    actionMeaning: asTrimmedString(value.actionMeaning ?? value.action_meaning),
  };

  return detail.heroMeaningCopy || detail.consultationSummary || detail.shrineMeaning || detail.actionMeaning ? detail : null;
}

type ConciergeChatResponse = {
  data?: {
    recommendations?: RecommendationApiCard[];
  };
};

type ConciergeChatRequestPayload = {
  version: 1;
  mode: "need";
  query: string;
  birthdate?: string;
  filters: {
    birthdate?: string;
    goriyaku_tag_ids?: number[];
    visit_style_tags?: string[];
    extra_condition?: string;
    crowd?: string[];
    duration_max_min?: number;
    free_text?: string;
  };
  goriyaku_tag_ids?: number[];
  extra_condition?: string;
  visit_date?: string;
  location?: { lat: number; lng: number };
  profile_context?: ProfileContextPayload;
};


const ACTION_SUGGESTION_V4_ACTION_TYPES = ["detail_open", "route_open", "save", "visit", "reflect", "pause"] as const;
const ACTION_SUGGESTION_V4_PROMPT_TYPES = ["before_visit", "after_visit", "decision", "emotion", "constraint"] as const;
const ACTION_SUGGESTION_V4_SOURCES = [
  "decision_context",
  "constraint_profile",
  "outcome_hint",
  "action_context",
  "reflection_question_seed",
  "fallback",
] as const;

function asTrimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function isActionSuggestionV4ActionType(value: unknown): value is ActionSuggestionV4Action["actionType"] {
  return typeof value === "string" && ACTION_SUGGESTION_V4_ACTION_TYPES.includes(value as any);
}

function isActionSuggestionV4PromptType(value: unknown): value is ActionSuggestionV4ReflectionPrompt["promptType"] {
  return typeof value === "string" && ACTION_SUGGESTION_V4_PROMPT_TYPES.includes(value as any);
}

function isActionSuggestionV4Source(value: unknown): value is ActionSuggestionV4Source["source"] {
  return typeof value === "string" && ACTION_SUGGESTION_V4_SOURCES.includes(value as any);
}

function normalizeActionSuggestionV4Action(raw: any): ActionSuggestionV4Action | null {
  if (!raw || typeof raw !== "object") return null;

  const label = asTrimmedString(raw.label);
  const description = asTrimmedString(raw.description);
  const actionTypeRaw = raw.action_type ?? raw.actionType;
  const confidenceRaw = typeof raw.confidence === "number" ? raw.confidence : Number(raw.confidence);

  if (!label || !description || !isActionSuggestionV4ActionType(actionTypeRaw) || !Number.isFinite(confidenceRaw)) {
    return null;
  }

  return {
    label,
    description,
    actionType: actionTypeRaw,
    confidence: Math.max(0, Math.min(1, confidenceRaw)),
  };
}

function normalizeActionSuggestionV4ReflectionPrompt(raw: any): ActionSuggestionV4ReflectionPrompt | null {
  if (!raw || typeof raw !== "object") return null;

  const question = asTrimmedString(raw.question);
  const promptTypeRaw = raw.prompt_type ?? raw.promptType;
  const sourceSeed = asTrimmedString(raw.source_seed ?? raw.sourceSeed);

  if (!question || !isActionSuggestionV4PromptType(promptTypeRaw) || !sourceSeed) {
    return null;
  }

  return {
    question,
    promptType: promptTypeRaw,
    sourceSeed,
  };
}

function normalizeActionSuggestionV4Source(raw: any): ActionSuggestionV4Source | null {
  if (!raw || typeof raw !== "object") return null;

  const sourceRaw = raw.source;
  const reason = asTrimmedString(raw.reason);

  if (!isActionSuggestionV4Source(sourceRaw) || !reason) {
    return null;
  }

  return {
    source: sourceRaw,
    reason,
  };
}

function normalizeActionSuggestionV4Preview(raw: unknown): ActionSuggestionV4Preview | null {
  if (!raw || typeof raw !== "object") return null;

  const value = raw as any;
  const primaryAction = normalizeActionSuggestionV4Action(value.primary_action ?? value.primaryAction);
  const secondaryAction = normalizeActionSuggestionV4Action(value.secondary_action ?? value.secondaryAction);
  const reflectionPrompt = normalizeActionSuggestionV4ReflectionPrompt(value.reflection_prompt ?? value.reflectionPrompt);
  const actionSource = normalizeActionSuggestionV4Source(value.action_source ?? value.actionSource);
  const sourceKeysRaw = value.source_keys ?? value.sourceKeys;
  const sourceKeys = Array.isArray(sourceKeysRaw)
    ? sourceKeysRaw
        .map((item) => asTrimmedString(item))
        .filter((item): item is string => Boolean(item))
    : [];

  if (!primaryAction || !secondaryAction || !reflectionPrompt || !actionSource) {
    return null;
  }

  return {
    primaryAction,
    secondaryAction,
    reflectionPrompt,
    actionSource,
    preview: value.preview === true,
    version: "v4",
    sourceKeys,
  };
}

function resolveRecommendationReason({
  recommendationReasonV4,
  reasonFacts,
  fallbackReason,
}: {
  recommendationReasonV4?: string | null;
  reasonFacts?: ConciergeReasonFacts | null;
  fallbackReason?: string | null;
}) {
  const v4Reason = asTrimmedString(recommendationReasonV4);
  if (v4Reason) return v4Reason;

  const factBasedReason = asTrimmedString(findPrimaryReasonFact(reasonFacts)?.label);

  if (factBasedReason) return factBasedReason;

  const legacyReason = asTrimmedString(fallbackReason);
  if (legacyReason) return legacyReason;

  return "相談内容と神社情報をもとに選ばれた神社です。";
}

function toRecommendationCard(item: RecommendationApiCard, index: number): RecommendationCard {
  const id = item.id ?? item.shrine_id ?? item.place_id ?? `recommendation-${index + 1}`;
  const shrineId = item.shrineId ?? item.shrine_id ?? item.id ?? item.place_id;
  const actionSuggestionV4Preview = normalizeActionSuggestionV4Preview(
    item.action_suggestion_v4_preview ?? item.actionSuggestionV4Preview,
  );
  const recommendationReasonV4 = item.recommendation_reason_v4 ?? item.recommendationReasonV4 ?? null;
  const recommendationReasonQuality = item.recommendation_reason_quality ?? item.recommendationReasonQuality ?? null;
  const recommendationReasonDetail = normalizeRecommendationReasonDetail(
    item.recommendation_reason_detail ?? item.recommendationReasonDetail ?? item.reason_detail ?? item.reasonDetail,
  );
  const reasonV4Detail = normalizeRecommendationReasonV4Detail(
    item.recommendation_reason_v4_detail ?? item.recommendationReasonV4Detail,
  );
  const reasonFacts = normalizeRecommendationReasonFacts(item.reason_facts ?? item.reasonFacts);
  const analyticsProvenance = recommendationAnalyticsProvenance({
    primaryReasonSource: item.primary_reason_source ?? item._primary_reason_source,
    reasonFacts,
    actionSuggestionPreview: item.action_suggestion_v4_preview ?? item.actionSuggestionV4Preview,
  });
  const reason = resolveRecommendationReason({
    recommendationReasonV4,
    reasonFacts,
    fallbackReason: item.reason,
  });

  return {
    id: String(id),
    name: item.display_name ?? item.name ?? "名称未設定の神社",
    area: item.area ?? item.location ?? item.address ?? item.formatted_address ?? "所在地未設定",
    connection: item.connection ?? "今の相談内容と近い意味を持つご縁",
    reason,
    recommendationReasonV4,
    reasonFacts,
    recommendationReasonQuality,
    recommendationReasonDetail,
    reasonV4Detail,
    tags: item.tags ?? [],
    shrineId: shrineId !== undefined && shrineId !== null ? String(shrineId) : undefined,
    actionSuggestionV4Preview,
    directionReference: validDirectionReferenceOrNull(item.direction_reference),
    analyticsProvenance,
  };
}

function normalizeRecommendations(items: RecommendationApiCard[]): RecommendationCard[] {
  return items.map(toRecommendationCard);
}

function buildActionSuggestionId({
  card,
  action,
  slot,
  rank,
}: {
  card: RecommendationCard;
  action: ActionSuggestionV4Action;
  slot: "primary" | "secondary";
  rank: number;
}) {
  return [card.shrineId ?? card.id, rank, slot, action.actionType].filter(Boolean).join(":");
}

async function fetchConciergeRecommendations({
  consultation,
  conditionFilters,
  profileContext,
  plannedVisitDate,
  location,
}: {
  consultation: string;
  conditionFilters: ConditionFilters;
  profileContext?: ProfileContextPayload;
  plannedVisitDate?: string;
  location?: { lat: number; lng: number };
}): Promise<RecommendationCard[]> {
  const payload: ConciergeChatRequestPayload = {
    version: 1,
    mode: "need",
    query: consultation,
    birthdate: conditionFilters.birthdate,
    filters: {
      birthdate: conditionFilters.birthdate,
      goriyaku_tag_ids: conditionFilters.goriyaku_tag_ids,
      visit_style_tags: conditionFilters.visit_style_tags,
      extra_condition: conditionFilters.extra_condition,
      crowd: undefined,
      duration_max_min: undefined,
      free_text: conditionFilters.extra_condition,
    },
    goriyaku_tag_ids: conditionFilters.goriyaku_tag_ids,
    extra_condition: conditionFilters.extra_condition,
    visit_date: plannedVisitDate || undefined,
    location,
    ...(profileContext ? { profile_context: profileContext } : {}),
  };

  const body = await post<ConciergeChatResponse>("/concierge/chat/", payload);
  return normalizeRecommendations(body.data?.recommendations ?? []);
}


// ────────────────────────────────────────────
// 推薦結果カード
// ────────────────────────────────────────────
function ResultCard({
  card,
  rank,
  onDetail,
  onActionEvent,
}: {
  card: RecommendationCard;
  rank: number;
  onDetail: () => void;
  onActionEvent: (params: {
    actionType: ActionEventActionType;
    action: ActionSuggestionV4Action;
    slot: "primary" | "secondary";
  }) => void;
}) {
  const directionImpressed = React.useRef(false);
  const reasonFactItems = buildReasonFactItems(card.reasonFacts);
  const actionSuggestionV4Preview = card.actionSuggestionV4Preview;
  const reasonDisplay = buildRecommendationReasonDisplay({
    matchReason: card.connection,
    reason: card.reason,
    directionReference: card.directionReference,
  });
  const reasonV4Sections = buildReasonV4Sections({
    detail: card.reasonV4Detail,
    fallbackReason: card.reason,
  });
  React.useEffect(() => { if (!card.directionReference || directionImpressed.current) return; directionImpressed.current = true; trackMobileDirection("direction_match_impression", { matched: card.directionReference.matched, recommendation_rank: rank }); }, [card.directionReference, rank]);
  return (
    <View style={styles.card}>
      {/* ランクバッジ */}
      <View style={styles.rankRow}>
        <View style={styles.rankBadge}>
          <Text style={styles.rankBadgeText}>{rank}</Text>
        </View>
        <Text style={styles.rankLabel}>ご縁{rank}</Text>
        <View style={styles.rankLine} />
      </View>

      {/* 神社名 + エリア */}
      <View style={styles.cardTitleBlock}>
        <Text style={styles.cardName}>{card.name}</Text>
        <Text style={styles.cardArea}>{card.area}</Text>
      </View>

      {reasonV4Sections.hasStructured ? (
        <>
          {/* この神社について */}
          {reasonV4Sections.factText ? (
            <View style={styles.reasonBlock}>
              <Text style={styles.reasonLabel}>この神社について</Text>
              <Text style={styles.cardReason} numberOfLines={3}>{reasonV4Sections.factText}</Text>
            </View>
          ) : null}

          {/* 今の相談とのつながり */}
          {reasonV4Sections.interpretationText ? (
            <View style={styles.reasonBlock}>
              <Text style={styles.reasonLabel}>今の相談とのつながり</Text>
              <Text style={styles.cardReason} numberOfLines={3}>{reasonV4Sections.interpretationText}</Text>
            </View>
          ) : null}

          {/* 参拝前にできること */}
          {reasonV4Sections.actionText ? (
            <View style={styles.reasonBlock}>
              <Text style={styles.reasonLabel}>参拝前にできること</Text>
              <Text style={styles.cardReason} numberOfLines={3}>{reasonV4Sections.actionText}</Text>
            </View>
          ) : null}
        </>
      ) : (
        <>
          {/* 相談内容・ご利益との一致 */}
          {reasonDisplay.matchReason ? (
            <View style={styles.connectionBlock}>
              <Text style={styles.connectionLabel}>相談内容・ご利益との一致</Text>
              <Text style={styles.connectionText}>{reasonDisplay.matchReason}</Text>
            </View>
          ) : null}

          {/* 推薦理由 */}
          {reasonV4Sections.fallbackText ? (
            <View style={styles.reasonBlock}>
              <Text style={styles.reasonLabel}>この神社を選んだ理由</Text>
              <Text style={styles.cardReason} numberOfLines={3}>{reasonV4Sections.fallbackText}</Text>
            </View>
          ) : null}
        </>
      )}

      {reasonFactItems.length > 0 ? (
        <View style={styles.reasonFactsCard}>
          <Text style={styles.reasonFactsLabel}>根拠として見ている情報</Text>
          {reasonFactItems.slice(0, 3).map((item) => (
            <View key={`${item.label}-${item.value}`} style={styles.reasonFactItem}>
              <Text style={styles.reasonFactLabel}>{item.label}</Text>
              <Text style={styles.reasonFactText}>{item.value}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {reasonDisplay.directionReference ? (
        <View style={styles.directionReferenceCard}>
          <Text accessibilityRole="header" style={styles.directionReferenceLabel}>方位の参考情報</Text>
          <Text style={styles.directionReferenceText}>現在地から見た方角：{reasonDisplay.directionReference.actual_direction}</Text>
          <Text style={styles.directionReferenceText}>予定日の参考方位：{reasonDisplay.directionReference.reference_directions.join("・")}</Text>
          <Text style={styles.directionReferenceText}>{directionReferenceMatchCopy(reasonDisplay.directionReference)}</Text>
          <Text style={styles.directionReferenceNote}>{reasonDisplay.directionReference.note}</Text>
        </View>
      ) : null}

      {actionSuggestionV4Preview?.preview ? (
        <View style={styles.actionV4Card}>
          <View style={styles.actionV4Header}>
            <Text style={styles.actionV4Label}>次に取りやすい行動</Text>
            <Text style={styles.actionV4SubLabel}>この神社を見たあとに、無理なく進めるための整理です。</Text>
          </View>

          {actionSuggestionV4Preview?.primaryAction ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`まずやること。${actionSuggestionV4Preview.primaryAction.label}。${actionSuggestionV4Preview.primaryAction.description}`}
              onPress={() =>
                onActionEvent({
                  actionType: "action_started",
                  action: actionSuggestionV4Preview.primaryAction,
                  slot: "primary",
                })
              }
              style={({ pressed }) => [
                styles.actionV4Item,
                pressed ? styles.actionV4ItemPressed : null,
              ]}
            >
              <Text style={styles.actionV4ItemLabel}>まずやること</Text>
              <Text style={styles.actionV4Title}>{actionSuggestionV4Preview.primaryAction.label}</Text>
              <Text style={styles.actionV4Description}>{actionSuggestionV4Preview.primaryAction.description}</Text>
            </Pressable>
          ) : null}

          {actionSuggestionV4Preview?.secondaryAction ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`次にできること。${actionSuggestionV4Preview.secondaryAction.label}。${actionSuggestionV4Preview.secondaryAction.description}`}
              onPress={() =>
                onActionEvent({
                  actionType: "action_completed",
                  action: actionSuggestionV4Preview.secondaryAction,
                  slot: "secondary",
                })
              }
              style={({ pressed }) => [
                styles.actionV4Item,
                pressed ? styles.actionV4ItemPressed : null,
              ]}
            >
              <Text style={styles.actionV4ItemLabel}>次にできること</Text>
              <Text style={styles.actionV4Title}>{actionSuggestionV4Preview.secondaryAction.label}</Text>
              <Text style={styles.actionV4Description}>{actionSuggestionV4Preview.secondaryAction.description}</Text>
            </Pressable>
          ) : null}

          <View style={styles.actionV4Item}>
            <Text style={styles.actionV4ItemLabel}>参拝前の問い</Text>
            <Text style={styles.actionV4Title}>{actionSuggestionV4Preview.reflectionPrompt.question}</Text>
          </View>
        </View>
      ) : null}

      {/* タグ */}
      {card.tags.length > 0 ? (
        <View style={styles.tagRow}>
          {card.tags.slice(0, 2).map((tag) => (
            <View key={tag} style={styles.tagPill}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {/* CTA */}
      <Button
        title="この神社を詳しく見る"
        variant="primary"
        onPress={onDetail}
        accessibilityLabel="この神社を詳しく見る"
      />
    </View>
  );
}

// ────────────────────────────────────────────
// メイン画面
// ────────────────────────────────────────────
export default function ConciergeScreen() {
  const params = useLocalSearchParams<{
    q?: string;
    theme?: string;
    birthdate?: string;
    visitStyle?: string;
    goriyaku?: string;
    support?: string;
    plannedVisitDate?: string;
    originLat?: string;
    originLng?: string;
  }>();
  const router = useRouter();
  const { userProfile: globalUserProfile } = useProfileStore();

  const initialQuery = [params.q, params.theme].filter(Boolean).join(" ").trim();
  // Homeの条件レイヤーで入力済みの場合、相談文が空でも初回送信できるようにする
  const initialHasCondition = Boolean(params.birthdate || params.plannedVisitDate || params.visitStyle || params.goriyaku || params.support);

  const [input, setInput] = React.useState(initialQuery);
  const [consultationText, setConsultationText] = React.useState(initialQuery);
  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [results, setResults] = React.useState<RecommendationCard[]>([]);
  const trackedResultSetRef = React.useRef<string | null>(null);
  const [selectedVisitStyle, setSelectedVisitStyle] = React.useState<string | undefined>(params.visitStyle || undefined);
  const [birthdate, setBirthdate] = React.useState(params.birthdate ?? "");
  const [plannedVisitDate, setPlannedVisitDate] = React.useState(params.plannedVisitDate ?? "");
  const initialOrigin: UserOrigin | null = getOriginSession() ?? (params.originLat && params.originLng ? { latitude: Number(params.originLat), longitude: Number(params.originLng), source: "device", displayName: "現在地", accuracy: "precise" } : null);
  const [origin, setOrigin] = React.useState<UserOrigin | null>(initialOrigin);
  const [locationStatus, setLocationStatus] = React.useState<"idle" | "loading" | "ready" | "error">(initialOrigin ? "ready" : "idle");
  const [selectedGoriyaku, setSelectedGoriyaku] = React.useState<string | undefined>(params.goriyaku || undefined);
  const [supportText, setSupportText] = React.useState(params.support ?? "");
  const hasAnyCondition = Boolean(selectedVisitStyle || birthdate.trim() || plannedVisitDate.trim() || selectedGoriyaku || supportText.trim());
  const isSendDisabled = loading || (!input.trim() && !hasAnyCondition);

  React.useEffect(() => {
    if (results.length === 0) return;
    const resultSetId = buildRecommendationResultSetId(
      null,
      results.map((card) => ({ shrineId: card.shrineId ?? card.id })),
    );
    if (trackedResultSetRef.current === resultSetId) return;
    trackedResultSetRef.current = resultSetId;

    results.forEach((card, index) => {
      track("concierge_result_impression", {
        source: "concierge_result",
        platform: "mobile",
        resultSetId,
        shrineId: card.shrineId ?? card.id,
        recommendationRank: index + 1,
        ...recommendationAnalyticsProperties(card.analyticsProvenance),
      });
    });
  }, [results]);
  const lastInitialQueryRef = React.useRef<string | null>(null);

  // Homeからの相談内容・条件が変わったら自動送信する
  React.useEffect(() => {
    const autoSubmitKey = initialQuery || (initialHasCondition ? "__condition_only__" : "");
    if (!autoSubmitKey || lastInitialQueryRef.current === autoSubmitKey) return;

    lastInitialQueryRef.current = autoSubmitKey;
    setInput(initialQuery);
    void submit(initialQuery);
    // submitはこの画面内の状態更新関数だけを使うため、initialQuery / initialHasConditionの変更だけを監視する
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery, initialHasCondition]);

  const submit = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed && !hasAnyCondition) return;
    const queryText = trimmed || "条件から合う神社を知りたい";
    trackMobileDirection("direction_condition_submitted", { has_visit_date: !!plannedVisitDate, has_origin: !!origin });

    setConsultationText(queryText);
    setInput("");
    setLoading(true);
    setSubmitted(false);
    setErrorMessage(null);

    try {
      const goriyakuTagIds = await resolveGoriyakuTagIds(selectedGoriyaku);
      const condition: ConditionState = {
        birthdate,
        plannedVisitDate,
        visitStyleLabel: selectedVisitStyle,
        goriyakuLabel: selectedGoriyaku,
        goriyakuTagIds,
        supportText,
      };
      const conditionFilters = buildConditionFilters(condition);
      const profileContext = buildConditionProfileContext({ condition, globalUserProfile });
      const recommendations = await fetchConciergeRecommendations({
        consultation: queryText,
        conditionFilters,
        profileContext,
        plannedVisitDate: plannedVisitDate.trim() || undefined,
        location: toOriginPayload(origin),
      });
      setResults(recommendations);
    } catch {
      setErrorMessage("通信に失敗しました。前回の結果を表示したまま、もう一度相談できます。");
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  const handleSend = () => void submit(input);

  const useCurrentLocation = async () => {
    setLocationStatus("loading");
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") { setLocationStatus("error"); trackMobileDirection("direction_origin_result", { origin_type: "device", result: "denied" }); return; }
    try {
      const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setOrigin({ latitude: current.coords.latitude, longitude: current.coords.longitude, source: "device", displayName: "現在地", accuracy: "precise" }); trackMobileDirection("direction_origin_result", { origin_type: "device", result: "success" });
      setLocationStatus("ready");
    } catch { setLocationStatus("error"); trackMobileDirection("direction_origin_result", { origin_type: "device", result: "failed" }); }
  };

  const handleChangeConditions = () => {
    setInput(consultationText);
  };

  const handleResuggest = () => {
    void submit(consultationText);
  };

  const handleActionEvent = ({
    card,
    rank,
    actionType,
    action,
    slot,
  }: {
    card: RecommendationCard;
    rank: number;
    actionType: ActionEventActionType;
    action: ActionSuggestionV4Action;
    slot: "primary" | "secondary";
  }) => {
    if (action.actionType === "route_open" && card.directionReference?.matched) {
      trackMobileDirection("direction_match_route_clicked", { matched: true, recommendation_rank: rank });
    }
    const actionSuggestionId = buildActionSuggestionId({ card, action, slot, rank });
    const hasPreview = Boolean(card.actionSuggestionV4Preview?.preview);

    if (__DEV__) {
      console.info("[ConciergeScreen] action event requested", {
        actionType,
        actionSuggestionId,
        hasPreview,
        cardId: card.id,
        shrineId: card.shrineId ?? null,
        rank,
        slot,
        actionTypeFromSuggestion: action.actionType,
      });
    }

    void trackActionEvent({
      actionType,
      actionSuggestionId,
      source: "mobile_concierge_result",
      shrineId: card.shrineId ?? null,
      threadId: null,
      historyTheme: resolveActionEventHistoryTheme({
        facts: card.reasonFacts,
        actionSourceKeys: card.actionSuggestionV4Preview?.sourceKeys,
      }),
      actionCategory: action.actionType,
      metadata: {
        platform: "mobile",
        rank,
        slot,
        has_preview: hasPreview,
        action_label: action.label,
        action_description: action.description,
        action_source: card.actionSuggestionV4Preview?.actionSource.source ?? null,
        source_keys: card.actionSuggestionV4Preview?.sourceKeys ?? [],
        primary_reason_source: card.analyticsProvenance.primaryReasonSource,
        is_fallback_recommendation: card.analyticsProvenance.isFallbackRecommendation,
      },
    });
  };

  const handleDetail = (card: RecommendationCard, rank: number) => {
    if (card.directionReference?.matched) trackMobileDirection("direction_match_detail_opened", { matched: true, recommendation_rank: rank });
    if (!card.shrineId) return;
    const resultSetId = buildRecommendationResultSetId(
      null,
      results.map((result) => ({ shrineId: result.shrineId ?? result.id })),
    );
    track("shrine_detail_transition", {
      source: "concierge_result",
      platform: "mobile",
      resultSetId,
      shrineId: card.shrineId,
      recommendationRank: rank,
      ...recommendationAnalyticsProperties(card.analyticsProvenance),
    });
    router.push({
      pathname: "/shrines/[id]",
      params: {
        id: card.shrineId,
        recommendationReasonV4: card.recommendationReasonV4 ?? "",
        reasonFacts: card.reasonFacts ? JSON.stringify(card.reasonFacts) : "",
        recommendationReasonDetail: card.recommendationReasonDetail
          ? JSON.stringify(card.recommendationReasonDetail)
          : "",
        actionSuggestionV4Preview: card.actionSuggestionV4Preview ? JSON.stringify(card.actionSuggestionV4Preview) : "",
        recommendationReasonV4Detail: serializeReasonV4Detail(card.reasonV4Detail),
        recommendationRank: String(rank),
        resultSetId,
      },
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* ヘッダー */}
        <View style={styles.header}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="前の画面に戻る"
            onPress={() => router.back()}
            style={styles.backBtn}
          >
            <Text style={styles.backText}>← 戻る</Text>
          </Pressable>
          <Text style={styles.headerTitle}>ご縁の神社</Text>
        </View>

        {/* 相談内容 */}
        <View style={styles.consultationArea}>
          <View style={styles.consultationCard}>
            <Text style={styles.consultationLabel}>相談内容</Text>
            <Text style={styles.consultationText}>
              {consultationText || "ホームで選んだ相談内容をもとに、おすすめの神社を表示します。"}
            </Text>
          </View>

          <View style={styles.conditionCard}>
            <View style={styles.conditionHeaderRow}>
              <View style={styles.conditionTitleBlock}>
                <Text style={styles.conditionLabel}>条件レイヤー</Text>
                <Text style={styles.conditionTitle}>今回の相談に反映する条件</Text>
              </View>
              <Button
                title="条件を変える"
                variant="outline"
                size="compact"
                onPress={handleChangeConditions}
                accessibilityLabel="相談条件を変更する"
              />
            </View>

            <View style={styles.conditionSummaryRow}>
              <Text style={styles.conditionSummaryLabel}>相談テーマ</Text>
              <Text style={styles.conditionSummaryText} numberOfLines={2}>
                {consultationText || "未入力"}
              </Text>
            </View>

            <ConditionFieldsCard
              birthdate={birthdate}
              onChangeBirthdate={setBirthdate}
              plannedVisitDate={plannedVisitDate}
              onChangePlannedVisitDate={(value)=>{setPlannedVisitDate(value);if(value)trackMobileDirection("direction_visit_date_set");}}
              locationStatus={locationStatus}
              onUseCurrentLocation={() => void useCurrentLocation()}
              origin={origin}
              onChangeOrigin={(value)=>{setOrigin(value);if(value)trackMobileDirection("direction_origin_result",{origin_type:value.source,result:"selected"});}}
              selectedVisitStyle={selectedVisitStyle}
              onSelectVisitStyle={setSelectedVisitStyle}
              selectedGoriyaku={selectedGoriyaku}
              onSelectGoriyaku={setSelectedGoriyaku}
              supportText={supportText}
              onChangeSupportText={setSupportText}
              disabled={loading}
            />

            <Button
              title="この条件で再提案する"
              variant="primary"
              onPress={handleResuggest}
              loading={loading}
              disabled={!consultationText && !hasAnyCondition}
              accessibilityLabel="この条件で再提案する"
            />
          </View>

          {loading ? (
            <View style={styles.loadingRow}>
              <Text style={styles.loadingText}>新しい相談内容から、ご縁を結び直しています…</Text>
            </View>
          ) : null}

          {errorMessage ? (
            <View style={styles.errorNotice}>
              <Text style={styles.errorNoticeText}>{errorMessage}</Text>
            </View>
          ) : null}
        </View>

        {/* 結果カード */}
        {submitted && results.length > 0 ? (
          <View style={styles.resultsArea}>
            <View style={styles.resultsIntro}>
              <Text style={styles.resultsLabel}>今の相談から結ばれた神社</Text>
              <Text style={styles.resultsLead}>必要な時だけ、下の入力欄から条件を変えて再相談できます。</Text>
            </View>
            {results.map((card, i) => (
              <ResultCard
                key={card.id}
                card={card}
                rank={i + 1}
                onDetail={() => handleDetail(card, i + 1)}
                onActionEvent={({ actionType, action, slot }) =>
                  handleActionEvent({
                    card,
                    rank: i + 1,
                    actionType,
                    action,
                    slot,
                  })
                }
              />
            ))}
          </View>
        ) : null}
      </ScrollView>

      {/* 入力バー */}
      <View style={styles.inputBar}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="条件を変える時だけ、追加で相談する"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          multiline
          editable={!loading}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="相談内容を送信する"
          accessibilityState={{
            disabled: isSendDisabled,
            busy: loading,
          }}
          onPress={handleSend}
          style={[styles.sendBtn, isSendDisabled && styles.sendBtnDisabled]}
          disabled={isSendDisabled}
        >
          <Text style={styles.sendText}>↑</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

// ────────────────────────────────────────────
// スタイル
// ────────────────────────────────────────────
const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  scrollContent: {
    paddingBottom: 104,
  },

  // ヘッダー
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 18,
    paddingTop: 18,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: theme.borderHeader,
  },
  backBtn: {
    paddingVertical: 4,
    paddingRight: 8,
  },
  backText: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "700",
  },
  headerTitle: {
    color: theme.text,
    fontSize: 17,
    fontWeight: "800",
    letterSpacing: 0.5,
  },

  consultationArea: {
    paddingHorizontal: 18,
    paddingTop: 16,
    gap: 8,
  },
  consultationCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderGold,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 6,
  },
  consultationLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  consultationText: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "800",
  },

  conditionCard: {
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 12,
  },
  conditionHeaderRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 10,
  },
  conditionTitleBlock: {
    flex: 1,
    gap: 4,
  },
  conditionLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  conditionTitle: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 21,
    fontWeight: "900",
  },
  conditionSummaryRow: {
    borderLeftWidth: 2,
    borderLeftColor: theme.borderGold,
    paddingLeft: 10,
    gap: 3,
  },
  conditionSummaryLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.7,
  },
  conditionSummaryText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "700",
  },
  loadingRow: {
    paddingVertical: 8,
  },
  loadingText: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: "600",
  },
  errorNotice: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  errorNoticeText: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },

  resultsArea: {
    paddingHorizontal: 16,
    paddingTop: 18,
    gap: 14,
  },
  resultsIntro: {
    gap: 4,
    marginBottom: 2,
  },
  resultsLabel: {
    color: theme.goldSoft,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  resultsLead: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },

  // カード
  card: {
    backgroundColor: theme.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingHorizontal: 18,
    paddingTop: 16,
    paddingBottom: 18,
    gap: 12,
    ...shadows.card,
  },

  // ランク
  rankRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  rankBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: theme.gold,
    alignItems: "center",
    justifyContent: "center",
  },
  rankBadgeText: {
    color: theme.background,
    fontSize: 12,
    fontWeight: "900",
    lineHeight: 14,
  },
  rankLabel: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0.8,
  },
  rankLine: {
    flex: 1,
    height: 1,
    backgroundColor: theme.borderSoft,
  },

  // 神社名・エリア
  cardTitleBlock: {
    gap: 3,
  },
  cardName: {
    color: theme.text,
    fontSize: 19,
    fontWeight: "900",
    letterSpacing: 0.3,
  },
  cardArea: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 0.2,
  },

  connectionBlock: {
    borderLeftWidth: 2,
    borderLeftColor: theme.borderGold,
    paddingLeft: 10,
    gap: 4,
  },
  connectionLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.7,
  },
  connectionText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "800",
  },

  // 推薦理由
  reasonBlock: {
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 5,
  },
  reasonLabel: {
    color: theme.goldSoft,
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.7,
  },
  cardReason: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 22,
    fontWeight: "700",
  },
  reasonFactsCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 9,
  },
  reasonFactsLabel: {
    color: theme.goldSoft,
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.7,
  },
  reasonFactItem: {
    gap: 3,
  },
  reasonFactLabel: {
    color: theme.muted,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
  reasonFactText: {
    color: theme.mutedSoft,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },
  directionReferenceCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 4,
  },
  directionReferenceLabel: {
    color: theme.goldSoft,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "900",
    letterSpacing: 0.7,
  },
  directionReferenceText: {
    color: theme.mutedSoft,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "600",
  },
  directionReferenceNote: {
    color: theme.muted,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "600",
  },

  actionV4Card: {
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 10,
  },
  actionV4Header: {
    gap: 3,
  },
  actionV4Label: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 0.8,
  },
  actionV4SubLabel: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },
  actionV4Item: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 4,
  },
  actionV4ItemPressed: {
    opacity: 0.78,
  },
  actionV4ItemLabel: {
    color: theme.goldSoft,
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.7,
  },
  actionV4Title: {
    color: theme.text,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "900",
  },
  actionV4Description: {
    color: theme.mutedSoft,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },

  // タグ
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  tagPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    backgroundColor: theme.surfaceSoft,
  },
  tagText: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.2,
  },

  // 入力バー
  inputBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 18,
    backgroundColor: theme.background,
    borderTopWidth: 1,
    borderTopColor: theme.borderHeader,
  },
  input: {
    flex: 1,
    minHeight: 46,
    maxHeight: 120,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 16,
    paddingHorizontal: 13,
    paddingVertical: 10,
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
  },
  sendBtn: {
    width: 50,
    height: 50,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 25,
    backgroundColor: theme.gold,
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
  sendText: {
    color: theme.background,
    fontSize: 22,
    fontWeight: "900",
  },
});
