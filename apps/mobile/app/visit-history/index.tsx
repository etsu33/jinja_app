import * as React from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { listVisits, type VisitHistoryItem } from "../../lib/visits";
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

function normalizeText(value: string | null | undefined, fallback: string): string {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text || fallback;
}

type VisitGroup = {
  label: string;
  items: VisitHistoryItem[];
};

function groupVisitsByDate(visits: VisitHistoryItem[]): VisitGroup[] {
  const groups = new Map<string, VisitHistoryItem[]>();

  visits.forEach((visit) => {
    const label = formatDateGroupLabel(visit.visited_at);
    const current = groups.get(label) ?? [];
    current.push(visit);
    groups.set(label, current);
  });

  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

function VisitTimelineCard({ visit, isLast }: { visit: VisitHistoryItem; isLast: boolean }) {
  const shrineName = normalizeText(visit.shrine_name, "神社名未設定");
  const shrineAddress = normalizeText(visit.shrine_address, "所在地未設定");
  const visitedAt = formatDate(visit.visited_at);
  const note = normalizeText(visit.note, "メモはまだありません。");

  return (
    <View style={styles.timelineRow}>
      <View style={styles.timelineRail}>
        <View style={styles.timelineDot} />
        {!isLast ? <View style={styles.timelineLine} /> : null}
      </View>

      <View style={styles.visitCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.shrineName}>{shrineName}</Text>
          <Text style={styles.visitedAt}>{visitedAt}</Text>
        </View>

        <Text style={styles.addressText} numberOfLines={2}>
          {shrineAddress}
        </Text>

        {visit.note ? (
          <View style={styles.noteBlock}>
            <Text style={styles.noteLabel}>参拝メモ</Text>
            <Text style={styles.noteText}>{note}</Text>
          </View>
        ) : null}
      </View>
    </View>
  );
}

export default function VisitHistoryScreen() {
  const router = useRouter();
  const [visits, setVisits] = React.useState<VisitHistoryItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);

  const loadVisits = React.useCallback(async (options?: { showInitialLoading?: boolean; showRefreshing?: boolean }) => {
    if (options?.showInitialLoading) setLoading(true);
    if (options?.showRefreshing) setRefreshing(true);

    try {
      const items = await listVisits();
      setVisits(items);
      setError(false);
    } catch {
      setVisits([]);
      setError(true);
    } finally {
      if (options?.showInitialLoading) setLoading(false);
      if (options?.showRefreshing) setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    void loadVisits({ showInitialLoading: true });
  }, [loadVisits]);

  const groupedVisits = React.useMemo(() => groupVisitsByDate(visits), [visits]);

  const onRefresh = React.useCallback(() => {
    void loadVisits({ showRefreshing: true });
  }, [loadVisits]);

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
        <Text style={styles.title}>参拝履歴</Text>
        <Text style={styles.subtitle}>
          参拝済みにした神社を、新しい順に見返せます。行動の積み重ねを確認するための記録です。
        </Text>
      </View>

      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>参拝回数</Text>
        <Text style={styles.summaryValue}>{loading ? "..." : visits.length}</Text>
        <Text style={styles.summaryText}>神社詳細画面で「参拝したことを記録する」を押すと、ここに反映されます。</Text>
      </View>

      {loading ? (
        <StateCard
          title="参拝履歴を読み込み中"
          description="保存された参拝記録を確認しています。"
        />
      ) : null}

      {!loading && error ? (
        <StateCard
          title="参拝履歴を読み込めませんでした"
          description="通信状況を確認して、もう一度開き直してください。"
        />
      ) : null}

      {!loading && !error && visits.length === 0 ? (
        <StateCard
          title="参拝履歴はまだありません"
          description="神社詳細で参拝済みにすると、ここに履歴として表示されます。"
        />
      ) : null}

      {!loading && !error && groupedVisits.length > 0 ? (
        <View style={styles.timeline}>
          {groupedVisits.map((group) => (
            <View key={group.label} style={styles.timelineGroup}>
              <Text style={styles.groupLabel}>{group.label}</Text>
              <View style={styles.list}>
                {group.items.map((visit, index) => (
                  <VisitTimelineCard key={visit.id} visit={visit} isLast={index === group.items.length - 1} />
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
  summaryCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  summaryLabel: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  summaryValue: {
    color: theme.gold,
    fontSize: 44,
    fontWeight: "900",
  },
  summaryText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
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
    gap: 0,
  },
  timelineRow: {
    flexDirection: "row",
    gap: spacing.smGap,
    minHeight: 108,
  },
  timelineRail: {
    alignItems: "center",
    width: 18,
  },
  timelineDot: {
    backgroundColor: theme.gold,
    borderRadius: 7,
    height: 14,
    marginTop: 18,
    width: 14,
  },
  timelineLine: {
    backgroundColor: theme.borderGold,
    flex: 1,
    opacity: 0.45,
    width: 1,
  },
  visitCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    flex: 1,
    marginBottom: spacing.mdGap,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.smGap,
  },
  cardHeader: {
    gap: spacing.tightGap,
  },
  shrineName: {
    color: theme.gold,
    fontSize: 17,
    fontWeight: "900",
  },
  visitedAt: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  addressText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
  },
  noteBlock: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.tightGap,
  },
  noteLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.1,
  },
  noteText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
