import * as React from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { fetchConciergeThreadsRaw, type ConciergeThreadListItem } from "../../lib/consultationHistory";
import {
  classifyThreadsLoadError,
  formatThreadDate,
  groupThreadsByDate,
  normalizeThreadPreview,
} from "../../lib/consultationHistoryUi";
import {
  shouldTrackConsultationHistoryViewEvent,
  trackConsultationHistoryDetailOpened,
  trackConsultationHistoryListViewed,
} from "../../lib/consultationHistoryAnalytics";
import { StateCard } from "../../components/common/StateCard";
import { AuthPrompt } from "../../components/common/AuthPrompt";
import Button from "../../components/ui/Button";
import { kamimusubiDark as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";

function ConsultationCard({ thread, onPress }: { thread: ConciergeThreadListItem; onPress: () => void }) {
  const title = thread.title?.trim() || "相談タイトル未設定";
  const preview = normalizeThreadPreview(thread.last_message);
  const date = formatThreadDate(thread.last_message_at);
  const messageCount = Number.isFinite(thread.message_count) ? thread.message_count : 0;

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${title}の相談履歴を開く`}
      style={({ pressed }) => [styles.consultationCard, pressed && styles.consultationCardPressed]}
    >
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
    </Pressable>
  );
}

type ListState =
  | { kind: "loading" }
  | { kind: "unauthenticated" }
  | { kind: "error" }
  | { kind: "ready"; threads: ConciergeThreadListItem[] };

export default function ConsultationHistoryScreen() {
  const router = useRouter();
  const [state, setState] = React.useState<ListState>({ kind: "loading" });
  const [refreshing, setRefreshing] = React.useState(false);
  const [authPromptVisible, setAuthPromptVisible] = React.useState(false);

  const loadThreads = React.useCallback(async (options?: { showRefreshing?: boolean }) => {
    if (options?.showRefreshing) {
      setRefreshing(true);
    } else {
      setState({ kind: "loading" });
    }

    try {
      const threads = await fetchConciergeThreadsRaw();
      setState({ kind: "ready", threads });
    } catch (error) {
      const kind = classifyThreadsLoadError(error);
      if (kind === "error" && __DEV__) {
        console.warn("[ConsultationHistoryScreen] failed to load threads", error);
      }
      setState({ kind });
    } finally {
      if (options?.showRefreshing) setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    void loadThreads();
  }, [loadThreads]);

  const onRefresh = React.useCallback(() => {
    void loadThreads({ showRefreshing: true });
  }, [loadThreads]);

  const threads = state.kind === "ready" ? state.threads : [];
  const groupedThreads = React.useMemo(() => groupThreadsByDate(threads), [threads]);

  React.useEffect(() => {
    if (state.kind === "unauthenticated") setAuthPromptVisible(true);
  }, [state.kind]);

  // 認証済みかつ取得成功で一覧が表示可能になった時点で1回だけ発火する(0件でも発火する)。
  // Pull to Refresh・Retryによる再取得やその他の再レンダーでは再発火しない。
  const hasTrackedListViewRef = React.useRef(false);
  React.useEffect(() => {
    if (
      !shouldTrackConsultationHistoryViewEvent({
        isReady: state.kind === "ready",
        alreadyTracked: hasTrackedListViewRef.current,
      })
    ) {
      return;
    }

    hasTrackedListViewRef.current = true;
    trackConsultationHistoryListViewed({ historyCount: threads.length });
  }, [state.kind, threads.length]);

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

          <Text style={styles.title}>相談履歴</Text>
          <Text style={styles.subtitle}>
            これまでの相談を新しい順に見返せます。迷いや願いの変化を、次の相談につなげるための記録です。
          </Text>
        </View>

        {state.kind === "loading" ? (
          <StateCard title="相談履歴を読み込み中" description="保存された相談を確認しています。" />
        ) : null}

        {state.kind === "unauthenticated" ? (
          <StateCard
            title="ログインが必要です"
            description="相談履歴を見返すには、ログインしてください。"
          />
        ) : null}

        {state.kind === "error" ? (
          <View style={styles.errorBlock}>
            <StateCard
              title="相談履歴を読み込めませんでした"
              description="通信状況を確認して、もう一度お試しください。"
            />
            <Button
              title="もう一度読み込む"
              variant="outline"
              size="compact"
              onPress={() => void loadThreads()}
              accessibilityLabel="相談履歴をもう一度読み込む"
            />
          </View>
        ) : null}

        {state.kind === "ready" && threads.length === 0 ? (
          <StateCard
            title="相談履歴はまだありません"
            description="コンシェルジュで相談すると、ここに履歴として表示されます。"
          />
        ) : null}

        {state.kind === "ready" && groupedThreads.length > 0 ? (
          <View style={styles.timeline}>
            {groupedThreads.map((group) => (
              <View key={group.label} style={styles.timelineGroup}>
                <Text style={styles.groupLabel}>{group.label}</Text>
                <View style={styles.list}>
                  {group.items.map((thread) => (
                    <ConsultationCard
                      key={thread.id}
                      thread={thread}
                      onPress={() => {
                        // 日付グループごとの添字ではなく、一覧全体(threads)内での1始まりpositionを送る。
                        const position = threads.findIndex((t) => t.id === thread.id) + 1;
                        trackConsultationHistoryDetailOpened({ threadId: thread.id, position });
                        router.push({
                          pathname: "/consultation-history/[id]",
                          params: { id: String(thread.id) },
                        });
                      }}
                    />
                  ))}
                </View>
              </View>
            ))}
          </View>
        ) : null}
      </ScrollView>

      <AuthPrompt
        visible={authPromptVisible}
        onClose={() => setAuthPromptVisible(false)}
        description="相談履歴を見返すには、ログインが必要です。"
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
  errorBlock: {
    gap: spacing.smGap,
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
  consultationCardPressed: {
    opacity: 0.72,
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
