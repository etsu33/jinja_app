import * as React from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { listJourneyEvents, type JourneyEvent, type JourneyEventType } from "../../lib/journey";
import { isUnauthenticatedError } from "../../lib/http";
import { StateCard } from "../../components/common/StateCard";
import { AuthPrompt } from "../../components/common/AuthPrompt";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";

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
  items: JourneyEvent[];
};

function groupEventsByDate(events: JourneyEvent[]): JourneyGroup[] {
  const groups = new Map<string, JourneyEvent[]>();

  events.forEach((event) => {
    const label = formatDateGroupLabel(event.occurred_at);
    const current = groups.get(label) ?? [];
    current.push(event);
    groups.set(label, current);
  });

  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

function EventCard({ event }: { event: JourneyEvent }) {
  const typeView = resolveEventTypeView(event.event_type);
  const title = normalizeText(event.title, typeView.fallbackTitle);
  const description = normalizeText(event.description, "");
  const occurredAtTime = formatTime(event.occurred_at);
  const shrineName = event.shrine_name?.trim();

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
        <Text style={styles.descriptionText} numberOfLines={2}>
          {description}
        </Text>
      ) : null}
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

  const groupedEvents = React.useMemo(() => groupEventsByDate(events), [events]);

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
                {group.items.map((event) => (
                  <EventCard key={event.id} event={event} />
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
  list: {
    gap: spacing.mdGap,
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
