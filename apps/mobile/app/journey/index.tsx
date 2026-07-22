import * as React from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import {
  buildJourneyTimeline,
  listJourneyEvents,
  parseRecommendationMetadata,
  type JourneyActionSuggestionMeta,
  type JourneyEvent,
  type JourneyEventType,
  type JourneyRecommendationMetadata,
  type JourneyTimelineItem,
} from "../../lib/journey";
import { isUnauthenticatedError } from "../../lib/http";
import { StateCard } from "../../components/common/StateCard";
import { AuthPrompt } from "../../components/common/AuthPrompt";
import { kamimusubiDark as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";

function formatTime(value: string | null | undefined): string {
  if (!value) return "";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
}

function formatDateGroupLabel(value: string | null | undefined): string {
  if (!value) return "日付未記録";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日付未記録";

  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  });
}

function normalizeText(value: string | null | undefined, fallback: string): string {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text || fallback;
}

type EventTypeView = {
  label: string;
  fallbackTitle: string;
};

const EVENT_TYPE_VIEW: Record<JourneyEventType, EventTypeView> = {
  consultation_created: { label: "相談", fallbackTitle: "相談しました" },
  recommendation_shown: { label: "ご提案", fallbackTitle: "神社をご提案しました" },
  visit_completed: { label: "参拝", fallbackTitle: "参拝しました" },
  reflection_created: { label: "振り返り", fallbackTitle: "振り返りを書きました" },
};

function resolveEventTypeView(eventType: JourneyEventType): EventTypeView {
  return EVENT_TYPE_VIEW[eventType] ?? { label: "できごと", fallbackTitle: "できごとがありました" };
}

type JourneyGroup = {
  label: string;
  items: JourneyTimelineItem[];
};

function groupTimelineByDate(items: JourneyTimelineItem[]): JourneyGroup[] {
  const groups = new Map<string, JourneyTimelineItem[]>();

  items.forEach((item) => {
    const label = formatDateGroupLabel(item.occurredAt);
    const current = groups.get(label) ?? [];
    current.push(item);
    groups.set(label, current);
  });

  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

function RecommendationActionSuggestionBlock({ actionSuggestion }: { actionSuggestion: JourneyActionSuggestionMeta }) {
  const { primary_action, secondary_action, reflection_prompt } = actionSuggestion;

  if (!primary_action && !secondary_action && !reflection_prompt) return null;

  return (
    <View style={styles.actionSuggestionBlock}>
      {primary_action ? (
        <View style={styles.actionItem}>
          <Text style={styles.actionItemLabel}>{primary_action.label}</Text>
          {primary_action.description ? (
            <Text style={styles.actionItemDescription}>{primary_action.description}</Text>
          ) : null}
        </View>
      ) : null}

      {secondary_action ? (
        <View style={styles.actionItemSecondary}>
          <Text style={styles.actionItemSecondaryLabel}>{secondary_action.label}</Text>
          {secondary_action.description ? (
            <Text style={styles.actionItemSecondaryDescription}>{secondary_action.description}</Text>
          ) : null}
        </View>
      ) : null}

      {reflection_prompt ? (
        <View style={styles.reflectionPromptBlock}>
          <Text style={styles.reflectionPromptLabel}>参拝前の問い</Text>
          <Text style={styles.reflectionPromptText}>{reflection_prompt.question}</Text>
        </View>
      ) : null}
    </View>
  );
}

function RecommendationContextBlock({ metadata }: { metadata: JourneyRecommendationMetadata }) {
  const { history_theme, reason, matched_benefits, action_suggestion } = metadata;
  const hasContext = Boolean(history_theme) || Boolean(reason) || matched_benefits.length > 0 || Boolean(action_suggestion);

  if (!hasContext) return null;

  return (
    <View style={styles.reasonBlock}>
      {history_theme ? (
        <View style={styles.typePillMuted}>
          <Text style={styles.typePillText}>{history_theme}</Text>
        </View>
      ) : null}

      {reason ? (
        <View style={styles.contextSection}>
          <Text style={styles.sectionHeading}>提案された理由</Text>
          <Text style={styles.descriptionText}>{reason}</Text>
        </View>
      ) : null}

      {matched_benefits.length > 0 ? (
        <View style={styles.contextSection}>
          <Text style={styles.sectionHeading}>ご利益</Text>
          <View style={styles.benefitRow}>
            {matched_benefits.map((benefit) => (
              <View key={benefit} style={styles.benefitChip}>
                <Text style={styles.benefitChipText}>{benefit}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {action_suggestion ? (
        <View style={styles.contextSection}>
          <Text style={styles.sectionHeading}>参拝前にできること</Text>
          <RecommendationActionSuggestionBlock actionSuggestion={action_suggestion} />
        </View>
      ) : null}
    </View>
  );
}

function EventCard({ event }: { event: JourneyEvent }) {
  const typeView = resolveEventTypeView(event.event_type);
  const title = normalizeText(event.title, typeView.fallbackTitle);
  const description = normalizeText(event.description, "");
  const occurredAtTime = formatTime(event.occurred_at);
  const shrineName = event.shrine_name?.trim();
  const recommendationMetadata =
    event.event_type === "recommendation_shown" ? parseRecommendationMetadata(event.metadata) : null;
  const descriptionMaxLines = event.event_type === "consultation_created" ? 4 : 2;

  return (
    <View style={styles.eventCard}>
      <View style={styles.cardHeader}>
        <View style={styles.typePill}>
          <Text style={styles.typePillText}>{typeView.label}</Text>
        </View>
        {occurredAtTime ? <Text style={styles.occurredAt}>{occurredAtTime}</Text> : null}
      </View>

      <Text style={styles.eventTitle}>{title}</Text>

      {shrineName ? <Text style={styles.shrineName}>{shrineName}</Text> : null}

      {description ? (
        <Text style={styles.descriptionText} numberOfLines={descriptionMaxLines}>
          {description}
        </Text>
      ) : null}

      {recommendationMetadata ? <RecommendationContextBlock metadata={recommendationMetadata} /> : null}
    </View>
  );
}

function VisitExperienceCard({ visit, reflection }: { visit: JourneyEvent; reflection: JourneyEvent | null }) {
  const shrineName = visit.shrine_name?.trim();
  const occurredAtTime = formatTime(visit.occurred_at);
  const visitNote = normalizeText(String(visit.metadata?.note ?? ""), "");

  const reflectionBody = reflection ? normalizeText(reflection.description, "") : "";
  const historyTheme = reflection ? normalizeText(String(reflection.metadata?.history_theme ?? ""), "") : "";
  const moodBefore = reflection ? normalizeText(String(reflection.metadata?.mood_before ?? ""), "") : "";
  const moodAfter = reflection ? normalizeText(String(reflection.metadata?.mood_after ?? ""), "") : "";
  const hasMood = Boolean(moodBefore) || Boolean(moodAfter);

  return (
    <View style={styles.eventCard}>
      <View style={styles.cardHeader}>
        <View style={styles.typePill}>
          <Text style={styles.typePillText}>参拝</Text>
        </View>
        {occurredAtTime ? <Text style={styles.occurredAt}>{occurredAtTime}</Text> : null}
      </View>

      <Text style={styles.eventTitle}>参拝しました</Text>

      {shrineName ? <Text style={styles.shrineName}>{shrineName}</Text> : null}

      {visitNote ? (
        <Text style={styles.descriptionText} numberOfLines={2}>
          {visitNote}
        </Text>
      ) : null}

      {reflection ? (
        <View style={styles.reflectionBlock}>
          <View style={styles.cardHeader}>
            <View style={styles.typePillMuted}>
              <Text style={styles.typePillText}>振り返り</Text>
            </View>
            {historyTheme ? <Text style={styles.occurredAt}>{historyTheme}</Text> : null}
          </View>

          {reflectionBody ? (
            <View style={styles.contextSection}>
              <Text style={styles.sectionHeading}>参拝後の振り返り</Text>
              <Text style={styles.descriptionText}>{reflectionBody}</Text>
            </View>
          ) : null}

          {hasMood ? (
            <View style={styles.contextSection}>
              <Text style={styles.sectionHeading}>気分の変化</Text>
              <Text style={styles.moodText}>
                {moodBefore || "―"} → {moodAfter || "―"}
              </Text>
            </View>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

function TimelineItemCard({ item }: { item: JourneyTimelineItem }) {
  if (item.kind === "visit_experience") {
    return <VisitExperienceCard visit={item.visit} reflection={item.reflection} />;
  }

  return <EventCard event={item.event} />;
}

function TimelineRow({ isLast, children }: { isLast: boolean; children: React.ReactNode }) {
  return (
    <View style={styles.timelineRow}>
      <View style={styles.timelineRail}>
        <View style={styles.timelineNode} />
        {!isLast ? <View style={styles.timelineConnector} /> : null}
      </View>
      <View style={styles.timelineRowContent}>{children}</View>
    </View>
  );
}

export default function JourneyScreen() {
  const router = useRouter();
  const [events, setEvents] = React.useState<JourneyEvent[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [unauthenticated, setUnauthenticated] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);

  const loadEvents = React.useCallback(
    async (options?: { showInitialLoading?: boolean; showRefreshing?: boolean }) => {
      if (options?.showInitialLoading) setLoading(true);
      if (options?.showRefreshing) setRefreshing(true);

      try {
        const items = await listJourneyEvents();
        setEvents(items);
        setError(false);
        setUnauthenticated(false);
      } catch (err) {
        if (isUnauthenticatedError(err)) {
          setEvents([]);
          setError(false);
          setUnauthenticated(true);
        } else {
          if (__DEV__) {
            console.warn("[JourneyScreen] failed to load timeline", err);
          }
          setEvents([]);
          setError(true);
        }
      } finally {
        if (options?.showInitialLoading) setLoading(false);
        if (options?.showRefreshing) setRefreshing(false);
      }
    },
    [],
  );

  React.useEffect(() => {
    void loadEvents({ showInitialLoading: true });
  }, [loadEvents]);

  const groupedEvents = React.useMemo(() => groupTimelineByDate(buildJourneyTimeline(events)), [events]);

  const onRefresh = React.useCallback(() => {
    void loadEvents({ showRefreshing: true });
  }, [loadEvents]);

  return (
    <>
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.gold} />}
    >
      <View style={styles.header}>
        <Pressable onPress={() => router.replace("/records")} style={styles.backButton}>
          <Text style={styles.backText}>← 記録へ戻る</Text>
        </Pressable>
        <Text style={styles.title}>ご縁の歩み</Text>
        <Text style={styles.subtitle}>
          相談から提案、参拝、振り返りまでの出来事を時系列で見返せます。
        </Text>
      </View>

      {loading ? (
        <StateCard title="ご縁の歩みを読み込み中" description="これまでの出来事を確認しています。" />
      ) : null}

      {!loading && error ? (
        <StateCard
          title="ご縁の歩みを読み込めませんでした"
          description="通信状況を確認して、もう一度開き直してください。"
        />
      ) : null}

      {!loading && unauthenticated ? (
        <StateCard
          title="ログインが必要です"
          description="ご縁の歩みを見るには、ログインしてください。"
        />
      ) : null}

      {!loading && !error && !unauthenticated && events.length === 0 ? (
        <StateCard
          title="ご縁の歩みはまだありません"
          description="相談や参拝、振り返りを記録すると、ここに時系列で表示されます。"
        />
      ) : null}

      {!loading && !error && !unauthenticated && groupedEvents.length > 0 ? (
        <View style={styles.timeline}>
          {groupedEvents.map((group) => (
            <View key={group.label} style={styles.timelineGroup}>
              <Text style={styles.groupLabel}>{group.label}</Text>
              <View style={styles.list}>
                {group.items.map((item, index) => (
                  <TimelineRow
                    key={item.kind === "visit_experience" ? item.visit.id : item.event.id}
                    isLast={index === group.items.length - 1}
                  >
                    <TimelineItemCard item={item} />
                  </TimelineRow>
                ))}
              </View>
            </View>
          ))}
        </View>
      ) : null}
    </ScrollView>

    <AuthPrompt
      visible={unauthenticated}
      onClose={() => router.replace("/records")}
      description="ご縁の歩みを見るには、ログインが必要です。"
    />
    </>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    padding: spacing.screenXWide,
    paddingBottom: spacing.bottomSpace,
    gap: spacing.lgGap,
  },
  header: {
    gap: spacing.mdGap,
  },
  backButton: {
    alignSelf: "flex-start",
    marginBottom: spacing.smGap,
  },
  backText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  title: {
    color: theme.gold,
    fontSize: 26,
    fontWeight: "900",
  },
  subtitle: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 23,
    fontWeight: "600",
  },
  timeline: {
    gap: spacing.lgGap,
  },
  timelineGroup: {
    gap: spacing.smGap,
  },
  groupLabel: {
    color: theme.goldSoft,
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0.8,
  },
  list: {},
  timelineRow: {
    flexDirection: "row",
  },
  timelineRail: {
    width: 20,
    alignItems: "center",
  },
  timelineNode: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginTop: 10,
    backgroundColor: theme.gold,
  },
  timelineConnector: {
    flex: 1,
    width: 2,
    marginTop: 4,
    backgroundColor: theme.borderHeader,
  },
  timelineRowContent: {
    flex: 1,
    marginLeft: spacing.smGap,
    paddingBottom: spacing.mdGap,
  },
  eventCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.tightGap,
  },
  typePill: {
    alignSelf: "flex-start",
    borderColor: theme.borderGold,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  typePillText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  typePillMuted: {
    alignSelf: "flex-start",
    borderColor: theme.borderHeader,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  reflectionBlock: {
    borderTopColor: theme.borderHeader,
    borderTopWidth: cardSizes.borderWidth,
    paddingTop: spacing.smGap,
    marginTop: spacing.smGap,
    gap: spacing.smGap,
  },
  moodText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "700",
  },
  reasonBlock: {
    borderTopColor: theme.borderHeader,
    borderTopWidth: cardSizes.borderWidth,
    paddingTop: spacing.smGap,
    marginTop: spacing.smGap,
    gap: spacing.smGap,
  },
  benefitRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.tightGap,
  },
  benefitChip: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  benefitChipText: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "700",
  },
  contextSection: {
    gap: spacing.tightGap,
  },
  sectionHeading: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.4,
  },
  actionSuggestionBlock: {
    gap: spacing.tightGap,
  },
  actionItem: {
    gap: 2,
  },
  actionItemLabel: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  actionItemDescription: {
    color: theme.mutedSoft,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },
  actionItemSecondary: {
    gap: 2,
  },
  actionItemSecondaryLabel: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  actionItemSecondaryDescription: {
    color: theme.mutedSoft,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: "600",
  },
  reflectionPromptBlock: {
    gap: 2,
  },
  reflectionPromptLabel: {
    color: theme.muted,
    fontSize: 11,
    fontWeight: "700",
  },
  reflectionPromptText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontStyle: "italic",
    fontWeight: "700",
  },
  occurredAt: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  eventTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
  },
  shrineName: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  descriptionText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
