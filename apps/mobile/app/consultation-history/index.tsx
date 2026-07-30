import * as React from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { listConciergeThreads, type ConciergeThreadListItem } from "../../lib/consultationHistory";
import { StateCard } from "../../components/common/StateCard";
import { kamimusubiDark as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";

function formatDate(value: string | null | undefined): string {
  if (!value) return "日付未記録";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日付未記録";

  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
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

function normalizePreview(value: string | null | undefined): string {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text || "相談内容はまだ記録されていません。";
}

type ConsultationGroup = {
  label: string;
  items: ConciergeThreadListItem[];
};

function groupThreadsByDate(threads: ConciergeThreadListItem[]): ConsultationGroup[] {
  const groups = new Map<string, ConciergeThreadListItem[]>();

  threads.forEach((thread) => {
    const label = formatDateGroupLabel(thread.last_message_at);
    const current = groups.get(label) ?? [];
    current.push(thread);
    groups.set(label, current);
  });

  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

function ConsultationCard({ thread }: { thread: ConciergeThreadListItem }) {
  const title = thread.title?.trim() || "相談タイトル未設定";
  const preview = normalizePreview(thread.last_message);
  const date = formatDate(thread.last_message_at);
  const messageCount = Number.isFinite(thread.message_count) ? thread.message_count : 0;

  return (
    <View style={styles.consultationCard}>
      <View style={styles.cardHeader}>
        <Text style={styles.threadTitle}>{title}</Text>
        <Text style={styles.createdAt}>{date}</Text>
      </View>

      <Text style={styles.previewText} numberOfLines={3}>
        {preview}
      </Text>

      <View style={styles.metaRow}>
        <View style={styles.messageCountPill}>
          <Text style={styles.messageCountText}>{messageCount}件のやりとり</Text>
        </View>
      </View>
    </View>
  );
}

export default function ConsultationHistoryScreen() {
  const router = useRouter();
  const [threads, setThreads] = React.useState<ConciergeThreadListItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);

  const loadThreads = React.useCallback(async (options?: { showInitialLoading?: boolean; showRefreshing?: boolean }) => {
    if (options?.showInitialLoading) setLoading(true);
    if (options?.showRefreshing) setRefreshing(true);

    try {
      const items = await listConciergeThreads();
      setThreads(items);
      setError(false);
    } catch {
      setThreads([]);
      setError(true);
    } finally {
      if (options?.showInitialLoading) setLoading(false);
      if (options?.showRefreshing) setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    void loadThreads({ showInitialLoading: true });
  }, [loadThreads]);

  const groupedThreads = React.useMemo(() => groupThreadsByDate(threads), [threads]);

  const onRefresh = React.useCallback(() => {
    void loadThreads({ showRefreshing: true });
  }, [loadThreads]);

  return (
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

        <Text style={styles.title}>相談履歴</Text>
        <Text style={styles.subtitle}>
          これまでの相談を新しい順に見返せます。迷いや願いの変化を、次の相談につなげるための記録です。
        </Text>
      </View>

      {loading ? (
        <StateCard
          title="相談履歴を読み込み中"
          description="保存された相談を確認しています。"
        />
      ) : null}

      {!loading && error ? (
        <StateCard
          title="相談履歴を読み込めませんでした"
          description="通信状況を確認して、もう一度開き直してください。"
        />
      ) : null}

      {!loading && !error && threads.length === 0 ? (
        <StateCard
          title="相談履歴はまだありません"
          description="コンシェルジュで相談すると、ここに履歴として表示されます。"
        />
      ) : null}

      {!loading && !error && groupedThreads.length > 0 ? (
        <View style={styles.timeline}>
          {groupedThreads.map((group) => (
            <View key={group.label} style={styles.timelineGroup}>
              <Text style={styles.groupLabel}>{group.label}</Text>
              <View style={styles.list}>
                {group.items.map((thread) => (
                  <ConsultationCard key={thread.id} thread={thread} />
                ))}
              </View>
            </View>
          ))}
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
  consultationCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  cardHeader: {
    gap: spacing.tightGap,
  },
  threadTitle: {
    color: theme.gold,
    fontSize: 17,
    fontWeight: "900",
  },
  createdAt: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  previewText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
  },
  metaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.tightGap,
  },
  messageCountPill: {
    alignSelf: "flex-start",
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: 999,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  messageCountText: {
    color: theme.text,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.6,
  },
});
