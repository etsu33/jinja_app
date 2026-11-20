import * as React from "react";
import {
  AccessibilityInfo,
  KeyboardAvoidingView,
  Platform,
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  StyleSheet,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { appColors as theme } from "../../../design/theme";
import Button from "../../../components/ui/Button";
import {
  buildConditionFilters,
  buildConditionProfileContext,
  resolveGoriyakuTagIds,
  type ConditionFilters,
  type ConditionState,
  type ProfileContextPayload,
} from "../../../lib/conditionPayload";
import { post } from "../../../lib/http";
import { trackActionEvent, type ActionEventActionType } from "../../../lib/actionEvents";
import { useProfileStore } from "../../../store/profileStore";
import {
  directionReferenceMatchCopy,
  validDirectionReferenceOrNull,
  type DirectionReference,
} from "../../../../../packages/shared/directionReference";
import { toOriginPayload, type UserOrigin } from "../../../../../packages/shared/userOrigin";
import { buildRecommendationReasonDisplay } from "../../../../../packages/shared/recommendationReasonDisplay";
import { getOriginSession } from "../../../lib/originSession";
import { trackMobileDirection } from "../../../lib/directionEvents";
import { track } from "../../../lib/analytics";
import { typography } from "../../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 送信ボタンの矢印。旧実装は "↑" のグリフだった。
const SEND_ICON_SIZE = 22;

// 相談文が空で条件だけが入っているときに送る既定文。従来と同じ文字列。
const CONSULTATION_FALLBACK = "条件から合う神社を知りたい";
import {
  buildRecommendationImpressionDedupKey,
  buildRecommendationResultSetId,
  normalizeRecommendationInstanceId,
  recommendationAnalyticsProperties,
  recommendationAnalyticsProvenance,
  type RecommendationAnalyticsProvenance,
} from "../../../../../packages/shared/recommendationAnalyticsProvenance";
import {
  buildReasonV4Sections,
  normalizeRecommendationReasonV4Detail,
  serializeReasonV4Detail,
  type RecommendationReasonV4Detail,
} from "../../../lib/recommendationReasonV4";
import {
  buildReasonFactItems,
  findPrimaryReasonFact,
  normalizeRecommendationReasonFacts,
  resolveActionEventHistoryTheme,
  type ConciergeReasonFacts,
} from "../../../lib/recommendationReasonFacts";
import { goriyakuColor } from "../../../design/goriyakuColors";

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
  // docs/audit/recommendation-instance-identity-propagation.md: Backend-issued rid,
  // reused as-is. Never generated/derived on Mobile.
  recommendationInstanceId: string | null;
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
  recommendation_instance_id?: string | null;
  recommendationInstanceId?: string | null;
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

// 1回の送信に効かせる条件。state とレンダーのタイミングをずらさずに submit へ渡すため、
// 値の組として扱う。項目は従来の payload と同じで、増減させていない。
type ConditionInputs = {
  birthdate: string;
  plannedVisitDate: string;
  visitStyle?: string;
  goriyaku?: string;
  supportText: string;
  origin: UserOrigin | null;
};

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
  const recommendationInstanceId = normalizeRecommendationInstanceId(
    item.recommendation_instance_id ?? item.recommendationInstanceId,
  );
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
    recommendationInstanceId,
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
      {/* 順位。塗りの丸バッジと「ご縁1」で同じ数字を2回出していたため、見出しだけにする。 */}
      <View style={styles.rankRow}>
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
          <Text style={styles.reasonFactsLabel}>相談と重なったもの</Text>
          {reasonFactItems.slice(0, 3).map((item) => (
            <View key={item.key} style={styles.reasonFactItem}>
              <Text style={styles.reasonFactLabel}>{item.label}</Text>
              {item.value ? <Text style={styles.reasonFactText}>{item.value}</Text> : null}
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
          {card.tags.slice(0, 2).map((tag) => {
            const tone = goriyakuColor(tag);
            return (
              <View key={tag} style={[styles.tagPill, { backgroundColor: tone.surface }]}>
                <Text style={[styles.tagText, { color: tone.text }]}>{tag}</Text>
              </View>
            );
          })}
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
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const { userProfile: globalUserProfile } = useProfileStore();

  const initialQuery = [params.q, params.theme].filter(Boolean).join(" ").trim();
  // 相談画面の条件だけが入力されている場合、相談文が空でも初回送信できるようにする
  const initialHasCondition = Boolean(params.birthdate || params.plannedVisitDate || params.visitStyle || params.goriyaku || params.support);

  const [input, setInput] = React.useState(initialQuery);
  const [consultationText, setConsultationText] = React.useState(initialQuery);
  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [results, setResults] = React.useState<RecommendationCard[]>([]);
  const trackedImpressionKeysRef = React.useRef<Set<string>>(new Set());
  const [selectedVisitStyle, setSelectedVisitStyle] = React.useState<string | undefined>(params.visitStyle || undefined);
  const [birthdate, setBirthdate] = React.useState(params.birthdate ?? "");
  const [plannedVisitDate, setPlannedVisitDate] = React.useState(params.plannedVisitDate ?? "");
  const initialOrigin: UserOrigin | null = getOriginSession() ?? (params.originLat && params.originLng ? { latitude: Number(params.originLat), longitude: Number(params.originLng), source: "device", displayName: "現在地", accuracy: "precise" } : null);
  const [origin, setOrigin] = React.useState<UserOrigin | null>(initialOrigin);
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

    results.forEach((card, index) => {
      // Recommendation Impression Instance Dedup Contract (docs/audit/
      // recommendation-strict-funnel-readiness.md §6, §14-2): dedup boundary must be the
      // Backend-issued recommendationInstanceId, not a single batch-level resultSetId ref
      // -- the previous single-ref guard suppressed the entire Impression batch for any
      // new generation sharing the same (always-"unknown"-prefixed on Mobile) shrine
      // signature, orphaning that generation's Click. Uses the same shared helper as Web
      // so both platforms dedup with the identical algorithm.
      const impressionKey = buildRecommendationImpressionDedupKey({
        recommendationInstanceId: card.recommendationInstanceId,
        resultSetId,
        shrineId: card.shrineId ?? card.id,
        rank: index + 1,
      });
      if (trackedImpressionKeysRef.current.has(impressionKey)) return;
      trackedImpressionKeysRef.current.add(impressionKey);

      track("concierge_result_impression", {
        source: "concierge_result",
        platform: "mobile",
        resultSetId,
        shrineId: card.shrineId ?? card.id,
        recommendationRank: index + 1,
        recommendationInstanceId: card.recommendationInstanceId,
        ...recommendationAnalyticsProperties(card.analyticsProvenance),
      });
    });
  }, [results]);
  const lastInitialQueryRef = React.useRef<string | null>(null);

  // 相談画面から戻ってきたかどうかの判定キー。
  // 相談文だけでなく条件も含める。この画面はタブなので、相談画面が replace で戻ると
  // 同じインスタンスが生き残る。相談文が同じで条件だけ変わった場合に再送信されない
  // (= 条件の変更が結果に反映されない)のを防ぐ。
  const paramsKey = [
    params.q,
    params.theme,
    params.birthdate,
    params.plannedVisitDate,
    params.visitStyle,
    params.goriyaku,
    params.support,
  ]
    .map((value) => value ?? "")
    .join("\u0001");

  // 相談画面で確定した相談内容・条件を受け取ったら自動送信する
  React.useEffect(() => {
    if (!initialQuery && !initialHasCondition) return;
    if (lastInitialQueryRef.current === paramsKey) return;

    lastInitialQueryRef.current = paramsKey;

    // 同じインスタンスが生き残るため、params から state を揃え直す。
    // state の反映はこのレンダー内では見えないので、送信には同じ値を直接渡す。
    const incoming: ConditionInputs = {
      birthdate: params.birthdate ?? "",
      plannedVisitDate: params.plannedVisitDate ?? "",
      visitStyle: params.visitStyle || undefined,
      goriyaku: params.goriyaku || undefined,
      supportText: params.support ?? "",
      origin: getOriginSession() ?? initialOrigin,
    };
    setBirthdate(incoming.birthdate);
    setPlannedVisitDate(incoming.plannedVisitDate);
    setSelectedVisitStyle(incoming.visitStyle);
    setSelectedGoriyaku(incoming.goriyaku);
    setSupportText(incoming.supportText);
    setOrigin(incoming.origin);

    setInput(initialQuery);
    void submit(initialQuery, incoming);
    // submitはこの画面内の状態更新関数だけを使うため、受け取った値の変化だけを監視する
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  const submit = async (text: string, override?: ConditionInputs) => {
    const applied: ConditionInputs = override ?? {
      birthdate,
      plannedVisitDate,
      visitStyle: selectedVisitStyle,
      goriyaku: selectedGoriyaku,
      supportText,
      origin,
    };
    const appliedHasCondition = Boolean(
      applied.visitStyle ||
        applied.goriyaku ||
        applied.birthdate.trim() ||
        applied.plannedVisitDate.trim() ||
        applied.supportText.trim(),
    );
    const trimmed = text.trim();
    if (!trimmed && !appliedHasCondition) return;
    const queryText = trimmed || CONSULTATION_FALLBACK;
    trackMobileDirection("direction_condition_submitted", { has_visit_date: !!applied.plannedVisitDate, has_origin: !!applied.origin });

    setConsultationText(queryText);
    setInput("");
    setLoading(true);
    setSubmitted(false);
    setErrorMessage(null);

    try {
      const goriyakuTagIds = await resolveGoriyakuTagIds(applied.goriyaku);
      const condition: ConditionState = {
        birthdate: applied.birthdate,
        plannedVisitDate: applied.plannedVisitDate,
        visitStyleLabel: applied.visitStyle,
        goriyakuLabel: applied.goriyaku,
        goriyakuTagIds,
        supportText: applied.supportText,
      };
      const conditionFilters = buildConditionFilters(condition);
      const profileContext = buildConditionProfileContext({ condition, globalUserProfile });
      const recommendations = await fetchConciergeRecommendations({
        consultation: queryText,
        conditionFilters,
        profileContext,
        plannedVisitDate: applied.plannedVisitDate.trim() || undefined,
        location: toOriginPayload(applied.origin),
      });
      setResults(recommendations);
      AccessibilityInfo.announceForAccessibility(
        `神社の提案結果を更新しました。${recommendations.length}件です。`,
      );
    } catch {
      setErrorMessage("通信に失敗しました。前回の結果を表示したまま、もう一度相談できます。");
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  const handleSend = () => void submit(input);

  // 条件の編集は相談画面(/consultation)が持つ。ここからは今の値を渡して送り出すだけ。
  const openConsultation = () => {
    const query = new URLSearchParams();
    const topic = consultationText === CONSULTATION_FALLBACK ? "" : consultationText.trim();
    if (topic) query.set("q", topic);
    if (birthdate.trim()) query.set("birthdate", birthdate.trim());
    if (plannedVisitDate.trim()) query.set("plannedVisitDate", plannedVisitDate.trim());
    if (selectedVisitStyle) query.set("visitStyle", selectedVisitStyle);
    if (selectedGoriyaku) query.set("goriyaku", selectedGoriyaku);
    if (supportText.trim()) query.set("support", supportText.trim());
    const search = query.toString();
    router.push(search ? `/consultation?${search}` : "/consultation");
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
        recommendation_instance_id: card.recommendationInstanceId,
      },
    });
  };

  // 効いている条件の読み上げ用。入力ではないので、値が無い項目は行ごと出さない。
  const hasConsultation = Boolean(consultationText);
  const appliedConditions = [
    { label: "参拝スタイル", value: selectedVisitStyle ?? "" },
    { label: "願うご縁", value: selectedGoriyaku ?? "" },
    { label: "参拝予定日", value: plannedVisitDate.trim() },
    { label: "誕生日", value: birthdate.trim() },
    { label: "出発地点", value: origin?.displayName ?? "" },
    { label: "その他", value: supportText.trim() },
  ].filter((item) => item.value.length > 0);

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
      recommendationInstanceId: card.recommendationInstanceId,
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
        recommendationInstanceId: card.recommendationInstanceId ?? "",
      },
    });
  };

  return (
    <KeyboardAvoidingView
      style={[styles.screen, { paddingTop: insets.top }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* ヘッダー。タブ画面なので戻るは持たない(ホームはタブバーから戻る)。 */}
        <View style={styles.header}>
          <Text accessibilityRole="header" style={styles.headerTitle}>ご縁の神社</Text>
        </View>

        {/* 相談内容 */}
        <View style={styles.consultationArea}>
          <View style={styles.consultationCard}>
            <Text style={styles.consultationLabel}>相談内容</Text>
            <Text style={styles.consultationText}>
              {consultationText || "まだ相談がありません。4つの質問に答えると、ご縁のある神社を提案します。"}
            </Text>
          </View>

          {/* docs/design/ios-ui-spec-v2.md 08節: 1画面1テーマ。
              旧実装はここに ConditionFieldsCard を丸ごと置いており、相談画面の
              STEP 2〜4 と同じ入力が2箇所にあった。この画面は結果を読む場所なので、
              効いている条件は読むだけにし、編集は相談画面へ返す。 */}
          <View style={styles.conditionCard}>
            <View style={styles.conditionHeaderRow}>
              <View style={styles.conditionTitleBlock}>
                <Text style={styles.conditionLabel}>
                  {hasConsultation ? "この提案に効いている条件" : "相談の条件"}
                </Text>
              </View>
              <Button
                title={hasConsultation ? "条件を変える" : "相談を始める"}
                variant={hasConsultation ? "outline" : "primary"}
                size="compact"
                onPress={openConsultation}
                accessibilityLabel={hasConsultation ? "相談条件を変更する" : "相談を始める"}
              />
            </View>

            {appliedConditions.length > 0 ? (
              <View style={styles.conditionList}>
                {appliedConditions.map((item) => (
                  <View key={item.label} style={styles.conditionSummaryRow}>
                    <Text style={styles.conditionSummaryLabel}>{item.label}</Text>
                    <Text style={styles.conditionSummaryText} numberOfLines={2}>
                      {item.value}
                    </Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={styles.conditionEmptyText}>
                {hasConsultation
                  ? "条件は加えていません。相談内容だけで提案しています。"
                  : "まだ条件はありません。"}
              </Text>
            )}
          </View>

          {loading ? (
            <View style={styles.loadingRow}>
              <Text style={styles.loadingText}>新しい相談内容から、ご縁を結び直しています…</Text>
            </View>
          ) : null}

          {errorMessage ? (
            <View style={styles.errorNotice}>
              <Text accessibilityRole="alert" style={styles.errorNoticeText}>{errorMessage}</Text>
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
          <Ionicons name="arrow-up" size={SEND_ICON_SIZE} color={theme.background} />
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
  headerTitle: {
    ...typography.title,
    color: theme.text,
  },

  consultationArea: {
    paddingHorizontal: 18,
    paddingTop: 16,
    gap: 8,
  },
  consultationCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderAccent,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 6,
  },
  consultationLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  consultationText: {
    ...typography.body,
    color: theme.text,
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
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  conditionList: {
    gap: 10,
  },
  conditionEmptyText: {
    ...typography.subhead,
    color: theme.muted,
  },
  conditionSummaryRow: {
    borderLeftWidth: 2,
    borderLeftColor: theme.borderAccent,
    paddingLeft: 10,
    gap: 3,
  },
  conditionSummaryLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  conditionSummaryText: {
    ...typography.subhead,
    color: theme.mutedSoft,
  },
  loadingRow: {
    paddingVertical: 8,
  },
  loadingText: {
    ...typography.body,
    color: theme.muted,
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
    ...typography.footnote,
    color: theme.muted,
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
    ...typography.label,
    color: theme.accentSoft,
  },
  resultsLead: {
    ...typography.footnote,
    color: theme.muted,
  },

  // カード
  card: {
    backgroundColor: theme.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: theme.borderAccent,
    paddingHorizontal: 18,
    paddingTop: 16,
    paddingBottom: 18,
    gap: 12,
  },

  // ランク
  rankRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  rankLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
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
    ...typography.subheading,
    color: theme.text,
  },
  cardArea: {
    ...typography.footnote,
    color: theme.muted,
  },

  connectionBlock: {
    borderLeftWidth: 2,
    borderLeftColor: theme.borderAccent,
    paddingLeft: 10,
    gap: 4,
  },
  connectionLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  connectionText: {
    ...typography.body,
    color: theme.text,
  },

  // 推薦理由
  // 27/28節: 読み物にする。カードの中に箱を積まない。
  // 旧実装は card > 塗りの箱 > 塗りの箱 の3段で、1件の結果に箱が5つ以上並んでいた。
  // 節の区切りは細い罫と余白で作り、塗りと枠は使わない。
  reasonBlock: {
    borderTopWidth: 1,
    borderTopColor: theme.borderSoft,
    paddingTop: 12,
    gap: 5,
  },
  reasonLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  cardReason: {
    ...typography.subhead,
    color: theme.mutedSoft,
  },
  reasonFactsCard: {
    borderTopWidth: 1,
    borderTopColor: theme.borderSoft,
    paddingTop: 12,
    gap: 9,
  },
  reasonFactsLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  reasonFactItem: {
    gap: 3,
  },
  reasonFactLabel: {
    ...typography.eyebrow,
    color: theme.muted,
  },
  reasonFactText: {
    ...typography.footnote,
    color: theme.mutedSoft,
  },
  directionReferenceCard: {
    borderTopWidth: 1,
    borderTopColor: theme.borderSoft,
    paddingTop: 12,
    gap: 4,
  },
  directionReferenceLabel: {
    ...typography.label,
    color: theme.accentSoft,
  },
  directionReferenceText: {
    ...typography.body,
    color: theme.mutedSoft,
  },
  directionReferenceNote: {
    ...typography.body,
    color: theme.muted,
  },

  actionV4Card: {
    borderTopWidth: 1,
    borderTopColor: theme.borderSoft,
    paddingTop: 12,
    gap: 10,
  },
  actionV4Header: {
    gap: 3,
  },
  actionV4Label: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  actionV4SubLabel: {
    ...typography.eyebrow,
    color: theme.muted,
  },
  actionV4Item: {
    // 押せる項目なので、左罫で並びであることを示す(条件サマリと同じ文法)。
    borderLeftWidth: 2,
    borderLeftColor: theme.borderAccent,
    paddingLeft: 10,
    paddingVertical: 6,
    gap: 4,
  },
  actionV4ItemPressed: {
    opacity: 0.78,
  },
  actionV4ItemLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  actionV4Title: {
    ...typography.title,
    color: theme.text,
  },
  actionV4Description: {
    ...typography.footnote,
    color: theme.mutedSoft,
  },

  // タグ
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  // 面と文字の色は goriyakuColor が渡す。枠線は置かない。
  tagPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
  },
  tagText: {
    ...typography.caption,
    color: theme.accentSoft,
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
    ...typography.bodyStrong,
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
  },
  sendBtn: {
    width: 50,
    height: 50,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 25,
    backgroundColor: theme.accent,
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
});
