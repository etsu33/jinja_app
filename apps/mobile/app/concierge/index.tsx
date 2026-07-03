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
import { kamimusubiDark as theme } from "../theme";
import { shadows } from "../design/shadow";
import type { ConciergeContext } from "../../lib/conciergeContext";
import { buildDerivedProfile } from "../../lib/profile";
import { post } from "../../lib/http";
import { useProfileStore } from "../../store/profileStore";

// ────────────────────────────────────────────
// 型
// ────────────────────────────────────────────
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
};

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
  reasonFacts?: RecommendationReasonFacts | null;
  recommendationReasonQuality?: RecommendationReasonQuality | null;
  recommendationReasonDetail?: RecommendationReasonDetail | null;
  tags: string[];
  shrineId?: string;
  actionSuggestionV4Preview?: ActionSuggestionV4Preview | null;
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
  reason_facts?: RecommendationReasonFacts | null;
  reasonFacts?: RecommendationReasonFacts | null;
  recommendation_reason_quality?: RecommendationReasonQuality | null;
  recommendationReasonQuality?: RecommendationReasonQuality | null;
  recommendation_reason_detail?: RecommendationReasonDetail | null;
  recommendationReasonDetail?: RecommendationReasonDetail | null;
  reason_detail?: RecommendationReasonDetail | null;
  reasonDetail?: RecommendationReasonDetail | null;
  tags?: string[];
  shrineId?: string | number;
  shrine_id?: string | number;
  place_id?: string | number;
  action_suggestion_v4_preview?: unknown;
  actionSuggestionV4Preview?: unknown;
  _reason_facts?: RecommendationReasonFacts[] | RecommendationReasonFacts | null;
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
    extra_condition?: string;
    crowd?: string[];
    duration_max_min?: number;
    free_text?: string;
  };
  goriyaku_tag_ids?: number[];
  extra_condition?: string;
  profile_context?: ProfileContextPayload;
};


const VISIT_STYLE_OPTIONS = [
  "静かに整えたい",
  "人混みを避けたい",
  "近場を優先したい",
  "自然を感じたい",
] as const;

const GORIYAKU_OPTIONS = ["仕事運", "金運", "縁結び", "厄除け", "学業成就", "健康"] as const;

function buildExtraCondition({
  visitStyle,
  birthdate,
  goriyaku,
  supportText,
}: {
  visitStyle?: string;
  birthdate?: string;
  goriyaku?: string;
  supportText?: string;
}) {
  return [
    visitStyle ? `参拝スタイル: ${visitStyle}` : undefined,
    birthdate ? `誕生日: ${birthdate}` : undefined,
    goriyaku ? `ご利益: ${goriyaku}` : undefined,
    supportText?.trim() ? `補助条件: ${supportText.trim()}` : undefined,
  ]
    .filter(Boolean)
    .join(" / ");
}

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
  reasonFacts?: RecommendationReasonFacts | null;
  fallbackReason?: string | null;
}) {
  const v4Reason = asTrimmedString(recommendationReasonV4);
  if (v4Reason) return v4Reason;

  const factBasedReason =
    asTrimmedString(reasonFacts?.shrine_feature) ??
    asTrimmedString(reasonFacts?.shrine_benefit) ??
    asTrimmedString(reasonFacts?.visit_fit) ??
    asTrimmedString(reasonFacts?.fallback_reason);

  if (factBasedReason) return factBasedReason;

  const legacyReason = asTrimmedString(fallbackReason);
  if (legacyReason) return legacyReason;

  return "相談内容と神社情報をもとに選ばれた神社です。";
}

function buildReasonFactItems(reasonFacts?: RecommendationReasonFacts | null) {
  if (!reasonFacts) return [];

  return [
    reasonFacts.shrine_feature
      ? { label: "神社固有の文脈", value: reasonFacts.shrine_feature }
      : null,
    reasonFacts.shrine_benefit
      ? { label: "ご利益・意味", value: reasonFacts.shrine_benefit }
      : null,
    reasonFacts.visit_fit
      ? { label: "参拝との相性", value: reasonFacts.visit_fit }
      : null,
    reasonFacts.distance_label
      ? { label: "行きやすさ", value: reasonFacts.distance_label }
      : null,
    reasonFacts.popularity_label
      ? { label: "参考情報", value: reasonFacts.popularity_label }
      : null,
  ].filter((item): item is { label: string; value: string } => Boolean(item?.value?.trim()));
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
  const reasonFactsRaw = item.reason_facts ?? item.reasonFacts ?? item._reason_facts ?? null;
  const reasonFacts = Array.isArray(reasonFactsRaw) ? (reasonFactsRaw[0] ?? null) : reasonFactsRaw;
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
    tags: item.tags ?? [],
    shrineId: shrineId !== undefined && shrineId !== null ? String(shrineId) : undefined,
    actionSuggestionV4Preview,
  };
}

function normalizeRecommendations(items: RecommendationApiCard[]): RecommendationCard[] {
  return items.map(toRecommendationCard);
}

type ProfileContextPayload = {
  user_profile: Record<string, string | undefined>;
  derived_profile: Record<string, string | undefined>;
  direction_profile: Record<string, string | undefined>;
};

async function fetchConciergeRecommendations({
  consultation,
  extraCondition,
  birthdate,
  profileContext,
}: {
  consultation: string;
  extraCondition?: string;
  birthdate?: string;
  profileContext?: ProfileContextPayload;
}): Promise<RecommendationCard[]> {
  const normalizedBirthdate = birthdate?.trim() || undefined;
  const normalizedExtraCondition = extraCondition?.trim() || undefined;
  const payload: ConciergeChatRequestPayload = {
    version: 1,
    mode: "need",
    query: consultation,
    birthdate: normalizedBirthdate,
    filters: {
      birthdate: normalizedBirthdate,
      goriyaku_tag_ids: undefined,
      extra_condition: normalizedExtraCondition,
      crowd: undefined,
      duration_max_min: undefined,
      free_text: normalizedExtraCondition,
    },
    goriyaku_tag_ids: undefined,
    extra_condition: normalizedExtraCondition,
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
}: {
  card: RecommendationCard;
  rank: number;
  onDetail: () => void;
}) {
  const reasonFactItems = buildReasonFactItems(card.reasonFacts);
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

      {/* 今の相談とのつながり */}
      <View style={styles.connectionBlock}>
        <Text style={styles.connectionLabel}>今の相談とのつながり</Text>
        <Text style={styles.connectionText}>{card.connection}</Text>
      </View>

      {/* 推薦理由 */}
      <View style={styles.reasonBlock}>
        <Text style={styles.reasonLabel}>この神社を選んだ理由</Text>
        <Text style={styles.cardReason} numberOfLines={3}>{card.reason}</Text>
      </View>

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

      {card.actionSuggestionV4Preview?.preview ? (
        <View style={styles.actionV4Card}>
          <View style={styles.actionV4Header}>
            <Text style={styles.actionV4Label}>次に取りやすい行動</Text>
            <Text style={styles.actionV4SubLabel}>この神社を見たあとに、無理なく進めるための整理です。</Text>
          </View>

          <View style={styles.actionV4Item}>
            <Text style={styles.actionV4ItemLabel}>まずやること</Text>
            <Text style={styles.actionV4Title}>{card.actionSuggestionV4Preview.primaryAction.label}</Text>
            <Text style={styles.actionV4Description}>{card.actionSuggestionV4Preview.primaryAction.description}</Text>
          </View>

          <View style={styles.actionV4Item}>
            <Text style={styles.actionV4ItemLabel}>次にできること</Text>
            <Text style={styles.actionV4Title}>{card.actionSuggestionV4Preview.secondaryAction.label}</Text>
            <Text style={styles.actionV4Description}>{card.actionSuggestionV4Preview.secondaryAction.description}</Text>
          </View>

          <View style={styles.actionV4Item}>
            <Text style={styles.actionV4ItemLabel}>参拝前の問い</Text>
            <Text style={styles.actionV4Title}>{card.actionSuggestionV4Preview.reflectionPrompt.question}</Text>
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
      <View style={styles.ctaRow}>
        <Pressable onPress={onDetail} style={styles.ctaPrimary}>
          <Text style={styles.ctaPrimaryText}>この神社を詳しく見る</Text>
        </Pressable>
      </View>
    </View>
  );
}

// ────────────────────────────────────────────
// メイン画面
// ────────────────────────────────────────────
export default function ConciergeScreen() {
  const params = useLocalSearchParams<{ q?: string; theme?: string }>();
  const router = useRouter();
  const { userProfile, derivedProfile, directionProfile } = useProfileStore();

  const initialQuery = [params.q, params.theme].filter(Boolean).join(" ").trim();

  const [input, setInput] = React.useState(initialQuery);
  const [consultationText, setConsultationText] = React.useState(initialQuery);
  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [results, setResults] = React.useState<RecommendationCard[]>([]);
  const [selectedVisitStyle, setSelectedVisitStyle] = React.useState<string | undefined>();
  const [birthdate, setBirthdate] = React.useState("");
  const [selectedGoriyaku, setSelectedGoriyaku] = React.useState<string | undefined>();
  const [supportText, setSupportText] = React.useState("");
  const hasAnyCondition = Boolean(selectedVisitStyle || birthdate.trim() || selectedGoriyaku || supportText.trim());
  const lastInitialQueryRef = React.useRef<string | null>(null);
  const conciergeContext = React.useMemo<ConciergeContext>(() => {
    const userProfile = {
      birthday: birthdate.trim() || undefined,
      birthTime: undefined,
      birthPlace: undefined,
      worshipStyle: selectedVisitStyle,
    };

    return {
      userProfile,
      derivedProfile: buildDerivedProfile(userProfile),
    };
  }, [birthdate, selectedVisitStyle]);

  // URLの相談内容が変わったら自動送信する
  React.useEffect(() => {
    if (!initialQuery || lastInitialQueryRef.current === initialQuery) return;

    lastInitialQueryRef.current = initialQuery;
    setInput(initialQuery);
    void submit(initialQuery);
    // submitはこの画面内の状態更新関数だけを使うため、initialQueryの変更だけを監視する
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const submit = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed && !hasAnyCondition) return;
    const queryText = trimmed || "条件から合う神社を知りたい";

    setConsultationText(queryText);
    setInput("");
    setLoading(true);
    setSubmitted(false);
    setErrorMessage(null);

    try {
      const extraCondition = buildExtraCondition({
        visitStyle: selectedVisitStyle,
        birthdate,
        goriyaku: selectedGoriyaku,
        supportText,
      });
      const profileContext: ProfileContextPayload = {
        user_profile: {
          birthday: userProfile.birthday,
          birthTime: userProfile.birthTime,
          birthPlace: userProfile.birthPlace,
          worshipStyle: userProfile.worshipStyle,
        },
        derived_profile: {
          kyusei: derivedProfile.kyusei,
          gogyo: derivedProfile.gogyo,
          lifePath: derivedProfile.lifePath,
        },
        direction_profile: {
          luckyDirection: directionProfile.luckyDirection,
          source: directionProfile.source,
        },
      };
      const recommendations = await fetchConciergeRecommendations({
        consultation: queryText,
        extraCondition: extraCondition || undefined,
        birthdate,
        profileContext,
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

  const handleChangeConditions = () => {
    setInput(consultationText);
  };

  const handleResuggest = () => {
    void submit(consultationText);
  };

  const handleDetail = (card: RecommendationCard) => {
    if (!card.shrineId) return;
    router.push({
      pathname: "/shrines/[id]",
      params: {
        id: card.shrineId,
        recommendationReasonV4: card.recommendationReasonV4 ?? "",
        reasonFacts: card.reasonFacts ? JSON.stringify(card.reasonFacts) : "",
        recommendationReasonDetail: card.recommendationReasonDetail ? JSON.stringify(card.recommendationReasonDetail) : "",
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
          <Pressable onPress={() => router.back()} style={styles.backBtn}>
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
              <Pressable onPress={handleChangeConditions} style={styles.conditionEditButton}>
                <Text style={styles.conditionEditText}>条件を変える</Text>
              </Pressable>
            </View>

            <View style={styles.conditionSummaryRow}>
              <Text style={styles.conditionSummaryLabel}>相談テーマ</Text>
              <Text style={styles.conditionSummaryText} numberOfLines={2}>
                {consultationText || "未入力"}
              </Text>
            </View>

            <View style={styles.conditionInputBlock}>
              <Text style={styles.visitStyleLabel}>誕生日</Text>
              <TextInput
                value={birthdate}
                onChangeText={setBirthdate}
                placeholder="例: 1984-05-15"
                placeholderTextColor={theme.mutedDark}
                style={styles.conditionInput}
                editable={!loading}
              />
            </View>

            <View style={styles.visitStyleBlock}>
              <Text style={styles.visitStyleLabel}>参拝スタイル</Text>
              <View style={styles.visitStyleRow}>
                {VISIT_STYLE_OPTIONS.map((option) => {
                  const active = selectedVisitStyle === option;
                  return (
                    <Pressable
                      key={option}
                      onPress={() => setSelectedVisitStyle(active ? undefined : option)}
                      style={[styles.visitStylePill, active && styles.visitStylePillActive]}
                    >
                      <Text style={[styles.visitStyleText, active && styles.visitStyleTextActive]}>{option}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            <View style={styles.visitStyleBlock}>
              <Text style={styles.visitStyleLabel}>ご利益</Text>
              <View style={styles.visitStyleRow}>
                {GORIYAKU_OPTIONS.map((option) => {
                  const active = selectedGoriyaku === option;
                  return (
                    <Pressable
                      key={option}
                      onPress={() => setSelectedGoriyaku(active ? undefined : option)}
                      style={[styles.visitStylePill, active && styles.visitStylePillActive]}
                    >
                      <Text style={[styles.visitStyleText, active && styles.visitStyleTextActive]}>{option}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            <View style={styles.conditionInputBlock}>
              <Text style={styles.visitStyleLabel}>相談補助条件</Text>
              <TextInput
                value={supportText}
                onChangeText={setSupportText}
                placeholder="例: 駅から近い場所、静かな場所、短時間で行ける場所"
                placeholderTextColor={theme.mutedDark}
                style={[styles.conditionInput, styles.conditionTextarea]}
                multiline
                editable={!loading}
              />
            </View>

            <Pressable
              onPress={handleResuggest}
              style={[styles.resuggestButton, (loading || (!consultationText && !hasAnyCondition)) && styles.resuggestButtonDisabled]}
              disabled={loading || (!consultationText && !hasAnyCondition)}
            >
              <Text style={styles.resuggestButtonText}>この条件で再提案する</Text>
            </Pressable>
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
                onDetail={() => handleDetail(card)}
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
          onPress={handleSend}
          style={[styles.sendBtn, (loading || (!input.trim() && !hasAnyCondition)) && styles.sendBtnDisabled]}
          disabled={loading || (!input.trim() && !hasAnyCondition)}
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
  conditionEditButton: {
    borderWidth: 1,
    borderColor: theme.borderGold,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  conditionEditText: {
    color: theme.gold,
    fontSize: 11,
    fontWeight: "800",
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
  conditionInputBlock: {
    gap: 8,
  },
  conditionInput: {
    minHeight: 44,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: theme.text,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "700",
  },
  conditionTextarea: {
    minHeight: 76,
    textAlignVertical: "top",
  },
  visitStyleBlock: {
    gap: 8,
  },
  visitStyleLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.7,
  },
  visitStyleRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  visitStylePill: {
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 999,
    paddingHorizontal: 11,
    paddingVertical: 7,
    backgroundColor: theme.surface,
  },
  visitStylePillActive: {
    borderColor: theme.borderGold,
    backgroundColor: theme.gold,
  },
  visitStyleText: {
    color: theme.mutedSoft,
    fontSize: 12,
    fontWeight: "800",
  },
  visitStyleTextActive: {
    color: theme.background,
  },
  resuggestButton: {
    height: 46,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
  },
  resuggestButtonDisabled: {
    opacity: 0.45,
  },
  resuggestButtonText: {
    color: theme.background,
    fontSize: 14,
    fontWeight: "900",
    letterSpacing: 0.3,
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

  // CTA
  ctaRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 4,
  },
  ctaPrimary: {
    flex: 1,
    height: 50,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
    shadowColor: theme.gold,
    ...shadows.goldCta,
  },
  ctaPrimaryText: {
    color: theme.background,
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: 0.3,
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
