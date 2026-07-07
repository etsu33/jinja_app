import * as React from "react";
import { Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { listShrineReflections, type ShrineReflectionResponse } from "../../lib/reflections";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";

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

function resolveDirectionView(direction: string | null | undefined): { icon: string; label: string } {
  switch (direction) {
    case "improved":
      return { icon: "↗", label: "前進" };
    case "unchanged":
      return { icon: "→", label: "維持" };
    case "worsened":
      return { icon: "↘", label: "要調整" };
    default:
      return { icon: "•", label: "未判定" };
  }
}

function normalizeHints(values: string[] | null | undefined): string[] {
  return [...new Set((values ?? []).map((value) => value.trim()).filter(Boolean))].slice(0, 3);
}

type ReflectionGroup = {
  label: string;
  items: ShrineReflectionResponse[];
};

function groupReflectionsByDate(reflections: ShrineReflectionResponse[]): ReflectionGroup[] {
  const groups = new Map<string, ShrineReflectionResponse[]>();

  reflections.forEach((reflection) => {
    const label = formatDateGroupLabel(reflection.created_at);
    const current = groups.get(label) ?? [];
    current.push(reflection);
    groups.set(label, current);
  });

  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

function ReflectionCard({
  reflection,
  onPress,
}: {
  reflection: ShrineReflectionResponse;
  onPress: (reflection: ShrineReflectionResponse) => void;
}) {
  const shrineName = reflection.shrine_name?.trim() || "神社名未設定";
  const historyTheme = reflection.history_theme?.trim() || "テーマ未設定";
  const answer = reflection.answer?.trim() || "振り返り本文はまだありません。";
  const createdAt = formatDate(reflection.created_at);
  const direction = resolveDirectionView(reflection.state_change_direction);
  const nextNeedHints = normalizeHints(reflection.next_need_hint);

  return (
    <Pressable
      style={({ pressed }) => [styles.reflectionCard, pressed ? styles.reflectionCardPressed : null]}
      onPress={() => onPress(reflection)}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.shrineName}>{shrineName}</Text>
        <Text style={styles.createdAt}>{createdAt}</Text>
      </View>

      <View style={styles.metaRow}>
        <View style={styles.themePill}>
          <Text style={styles.themePillText}>{historyTheme}</Text>
        </View>
        <View style={styles.directionPill}>
          <Text style={styles.directionPillText}>{direction.icon} {direction.label}</Text>
        </View>
      </View>

      <Text style={styles.answerText}>{answer}</Text>

      {reflection.state_change_summary ? (
        <View style={styles.summaryBlock}>
          <Text style={styles.summaryLabel}>変化のメモ</Text>
          <Text style={styles.summaryText}>{reflection.state_change_summary}</Text>
        </View>
      ) : null}

      {nextNeedHints.length > 0 ? (
        <View style={styles.hintBlock}>
          <Text style={styles.summaryLabel}>次に出やすいテーマ</Text>
          <View style={styles.hintRow}>
            {nextNeedHints.map((hint) => (
              <View key={hint} style={styles.hintPill}>
                <Text style={styles.hintPillText}>{hint}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}
    </Pressable>
  );
}

function ReflectionDetailModal({
  reflection,
  onClose,
}: {
  reflection: ShrineReflectionResponse | null;
  onClose: () => void;
}) {
  return (
    <Modal
      visible={reflection !== null}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalCard}>
          <ScrollView showsVerticalScrollIndicator={false} style={styles.modalScroll}>
            <Text style={styles.modalLabel}>問いかけ</Text>
            <Text style={styles.modalText}>{reflection?.prompt?.trim() || "問いかけは記録されていません。"}</Text>

            <Text style={styles.modalLabel}>振り返り</Text>
            <Text style={styles.modalText}>{reflection?.answer?.trim() || "振り返り本文はまだありません。"}</Text>

            <Text style={styles.modalLabel}>参拝前の気持ち</Text>
            <Text style={styles.modalText}>{reflection?.mood_before?.trim() || "記録されていません。"}</Text>

            <Text style={styles.modalLabel}>参拝後の気持ち</Text>
            <Text style={styles.modalText}>{reflection?.mood_after?.trim() || "記録されていません。"}</Text>

            {reflection?.state_change_summary ? (
              <>
                <Text style={styles.modalLabel}>変化のメモ</Text>
                <Text style={styles.modalText}>{reflection.state_change_summary}</Text>
              </>
            ) : null}
          </ScrollView>

          <Pressable style={styles.modalCloseButton} onPress={onClose}>
            <Text style={styles.modalCloseText}>閉じる</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

export default function ReflectionHistoryScreen() {
  const router = useRouter();
  const [reflections, setReflections] = React.useState<ShrineReflectionResponse[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const [selectedReflection, setSelectedReflection] = React.useState<ShrineReflectionResponse | null>(null);

  const loadReflections = React.useCallback(async (options?: { showInitialLoading?: boolean; showRefreshing?: boolean }) => {
    if (options?.showInitialLoading) setLoading(true);
    if (options?.showRefreshing) setRefreshing(true);

    try {
      const items = await listShrineReflections();
      setReflections(items);
      setError(false);
    } catch {
      setReflections([]);
      setError(true);
    } finally {
      if (options?.showInitialLoading) setLoading(false);
      if (options?.showRefreshing) setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    void loadReflections({ showInitialLoading: true });
  }, [loadReflections]);

  const groupedReflections = React.useMemo(() => groupReflectionsByDate(reflections), [reflections]);

  const onRefresh = React.useCallback(() => {
    void loadReflections({ showRefreshing: true });
  }, [loadReflections]);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.gold} />}
    >
      <View style={styles.header}>
        <Pressable onPress={() => (router.canGoBack() ? router.back() : router.replace("/records"))} style={styles.backButton}>
          <Text style={styles.backText}>← 記録へ戻る</Text>
        </Pressable>

        <Text style={styles.title}>振り返り履歴</Text>
        <Text style={styles.subtitle}>
          参拝後に残した振り返りを、新しい順に見返せます。次の相談につなげるための記録です。
        </Text>
      </View>

      {loading ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>振り返りを読み込み中</Text>
          <Text style={styles.stateText}>保存した振り返りを確認しています。</Text>
        </View>
      ) : null}

      {!loading && error ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>振り返り履歴を読み込めませんでした</Text>
          <Text style={styles.stateText}>通信状況を確認して、もう一度開き直してください。</Text>
        </View>
      ) : null}

      {!loading && !error && reflections.length === 0 ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>振り返りはまだありません</Text>
          <Text style={styles.stateText}>
            神社詳細で参拝記録をしたあと、感じたことを保存するとここに表示されます。
          </Text>
        </View>
      ) : null}

      {!loading && !error && groupedReflections.length > 0 ? (
        <View style={styles.timeline}>
          {groupedReflections.map((group) => (
            <View key={group.label} style={styles.timelineGroup}>
              <Text style={styles.groupLabel}>{group.label}</Text>
              <View style={styles.list}>
                {group.items.map((reflection) => (
                  <ReflectionCard key={reflection.id} reflection={reflection} onPress={setSelectedReflection} />
                ))}
              </View>
            </View>
          ))}
        </View>
      ) : null}

      <ReflectionDetailModal reflection={selectedReflection} onClose={() => setSelectedReflection(null)} />
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
  reflectionCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  reflectionCardPressed: {
    opacity: 0.7,
  },
  cardHeader: {
    gap: spacing.tightGap,
  },
  shrineName: {
    color: theme.gold,
    fontSize: 17,
    fontWeight: "900",
  },
  createdAt: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  metaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.tightGap,
  },
  themePill: {
    alignSelf: "flex-start",
    borderColor: theme.borderGold,
    borderRadius: 999,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  themePillText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  directionPill: {
    alignSelf: "flex-start",
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: 999,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  directionPillText: {
    color: theme.text,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.6,
  },
  answerText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
  },
  summaryBlock: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.tightGap,
  },
  summaryLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.1,
  },
  summaryText: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
  hintBlock: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.tightGap,
  },
  hintRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.tightGap,
  },
  hintPill: {
    borderColor: theme.borderGold,
    borderRadius: 999,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: 9,
    paddingVertical: 3,
  },
  hintPillText: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
  },
  stateCard: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  stateTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
  },
  stateText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(7, 16, 31, 0.82)",
    justifyContent: "center",
    padding: spacing.screenXWide,
  },
  modalCard: {
    maxHeight: "80%",
    backgroundColor: theme.surface,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.mdGap,
  },
  modalScroll: {
    flexGrow: 0,
  },
  modalLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.1,
    marginTop: spacing.mdGap,
  },
  modalText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
    marginTop: spacing.tightGap,
  },
  modalCloseButton: {
    alignSelf: "center",
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderGold,
    borderRadius: 999,
    borderWidth: cardSizes.borderWidth,
    paddingHorizontal: spacing.lgGap,
    paddingVertical: spacing.smGap,
  },
  modalCloseText: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "800",
  },
});
