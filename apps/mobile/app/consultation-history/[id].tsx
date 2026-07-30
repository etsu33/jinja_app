import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import {
  getConciergeThread,
  type ConciergeRecommendation,
  type ConciergeThreadDetail,
} from "../../lib/consultationHistory";
import {
  ACTION_STATE_LABEL,
  classifyThreadDetailLoadError,
  extractRecommendationShrineId,
  formatThreadDateTime,
} from "../../lib/consultationHistoryUi";
import {
  buildReasonV4Sections,
  normalizeRecommendationReasonV4Detail,
  serializeReasonV4Detail,
} from "../../lib/recommendationReasonV4";
import { StateCard } from "../../components/common/StateCard";
import { AuthPrompt } from "../../components/common/AuthPrompt";
import Button from "../../components/ui/Button";
import { kamimusubiDark as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";

function RecommendationCard({
  rec,
  onOpenShrineDetail,
}: {
  rec: ConciergeRecommendation;
  onOpenShrineDetail: (shrineId: string) => void;
}) {
  const shrineId = extractRecommendationShrineId(rec);
  const name = rec.display_name?.trim() || rec.name?.trim() || "名称未設定の神社";
  const address = rec.address ?? rec.location ?? rec.formatted_address ?? null;
  const reasonV4Detail = normalizeRecommendationReasonV4Detail(rec.recommendation_reason_v4_detail);
  const sections = buildReasonV4Sections({ detail: reasonV4Detail, fallbackReason: null });
  const factText = sections.factText ?? sections.fallbackText;
  const actionLabel = rec.action_state ? ACTION_STATE_LABEL[rec.action_state] : undefined;

  return (
    <View style={styles.recommendationCard}>
      <View style={styles.recommendationHeader}>
        <Text style={styles.recommendationName}>{name}</Text>
        {actionLabel ? (
          <View style={styles.actionBadge}>
            <Text style={styles.actionBadgeText}>{actionLabel}</Text>
          </View>
        ) : null}
      </View>
      {address ? <Text style={styles.recommendationAddress}>{address}</Text> : null}
      {factText ? <Text style={styles.recommendationFact}>{factText}</Text> : null}
      {shrineId ? (
        <Pressable
          onPress={() => onOpenShrineDetail(shrineId)}
          accessibilityRole="button"
          accessibilityLabel={`${name}の詳細を見る`}
          style={styles.detailLink}
        >
          <Text style={styles.detailLinkText}>神社の詳細を見る</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

type DetailState =
  | { kind: "loading" }
  | { kind: "unauthenticated" }
  | { kind: "not_found" }
  | { kind: "error" }
  | { kind: "ready"; thread: ConciergeThreadDetail };

export default function ConsultationHistoryDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const tid = React.useMemo(() => {
    const raw = params.id;
    return Array.isArray(raw) ? raw[0] : raw;
  }, [params.id]);

  const [state, setState] = React.useState<DetailState>({ kind: "loading" });
  const [authPromptVisible, setAuthPromptVisible] = React.useState(false);

  const load = React.useCallback(async () => {
    if (!tid) {
      setState({ kind: "not_found" });
      return;
    }

    setState({ kind: "loading" });

    try {
      const thread = await getConciergeThread(tid);
      setState({ kind: "ready", thread });
    } catch (error) {
      const kind = classifyThreadDetailLoadError(error);
      if (kind === "error" && __DEV__) {
        console.warn("[ConsultationHistoryDetailScreen] failed to load thread", error);
      }
      setState({ kind });
    }
  }, [tid]);

  React.useEffect(() => {
    void load();
  }, [load]);

  React.useEffect(() => {
    if (state.kind === "unauthenticated") setAuthPromptVisible(true);
  }, [state.kind]);

  const handleOpenShrineDetail = React.useCallback(
    (shrineId: string, rec: ConciergeRecommendation) => {
      const reasonV4Detail = normalizeRecommendationReasonV4Detail(rec.recommendation_reason_v4_detail);
      router.push({
        pathname: "/shrines/[id]",
        params: {
          id: shrineId,
          recommendationReasonV4: rec.recommendation_reason_v4 ?? "",
          reasonFacts: rec.reason_facts ? JSON.stringify(rec.reason_facts) : "",
          recommendationReasonDetail: rec.recommendation_reason_detail
            ? JSON.stringify(rec.recommendation_reason_detail)
            : "",
          actionSuggestionV4Preview: rec.action_suggestion_v4_preview
            ? JSON.stringify(rec.action_suggestion_v4_preview)
            : "",
          recommendationReasonV4Detail: serializeReasonV4Detail(reasonV4Detail),
        },
      });
    },
    [router],
  );

  const recommendations =
    state.kind === "ready" ? (state.thread.recommendations_v2 ?? state.thread.recommendations ?? []) : [];

  return (
    <>
      <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backButton}>
            <Text style={styles.backText}>← 相談履歴へ戻る</Text>
          </Pressable>
          <Text style={styles.title}>
            {state.kind === "ready" ? state.thread.title?.trim() || "相談タイトル未設定" : "相談履歴"}
          </Text>
          {state.kind === "ready" ? (
            <Text style={styles.subtitle}>{formatThreadDateTime(state.thread.last_message_at)}</Text>
          ) : null}
        </View>

        {state.kind === "loading" ? (
          <StateCard title="相談履歴を読み込み中" description="保存された相談を確認しています。" />
        ) : null}

        {state.kind === "unauthenticated" ? (
          <StateCard title="ログインが必要です" description="この相談履歴を見返すには、ログインしてください。" />
        ) : null}

        {state.kind === "not_found" ? (
          <View style={styles.errorBlock}>
            <StateCard
              title="この相談は見つかりませんでした"
              description="削除されたか、アクセスできない相談です。"
            />
            <Button
              title="相談履歴の一覧へ戻る"
              variant="outline"
              size="compact"
              onPress={() => router.replace("/consultation-history")}
              accessibilityLabel="相談履歴の一覧へ戻る"
            />
          </View>
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
              onPress={() => void load()}
              accessibilityLabel="相談履歴をもう一度読み込む"
            />
          </View>
        ) : null}

        {state.kind === "ready" ? (
          <>
            {recommendations.length > 0 ? (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>当時推薦された神社</Text>
                <View style={styles.list}>
                  {recommendations.map((rec, idx) => (
                    <RecommendationCard
                      key={`${extractRecommendationShrineId(rec) ?? rec.name ?? "rec"}-${idx}`}
                      rec={rec}
                      onOpenShrineDetail={(shrineId) => handleOpenShrineDetail(shrineId, rec)}
                    />
                  ))}
                </View>
              </View>
            ) : null}

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>相談内容</Text>
              <View style={styles.list}>
                {state.thread.messages.map((message) => (
                  <View
                    key={message.id}
                    style={[
                      styles.messageBubble,
                      message.role === "user" ? styles.messageBubbleUser : styles.messageBubbleAssistant,
                    ]}
                  >
                    <Text style={styles.messageText}>{message.content}</Text>
                    <Text style={styles.messageDate}>{formatThreadDateTime(message.created_at)}</Text>
                  </View>
                ))}
              </View>
            </View>
          </>
        ) : null}
      </ScrollView>

      <AuthPrompt
        visible={authPromptVisible}
        onClose={() => setAuthPromptVisible(false)}
        description="この相談履歴を見返すには、ログインが必要です。"
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
    fontSize: 22,
    fontWeight: "900",
  },
  subtitle: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  errorBlock: {
    gap: spacing.smGap,
  },
  section: {
    gap: spacing.smGap,
  },
  sectionTitle: {
    color: theme.goldSoft,
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0.6,
  },
  list: {
    gap: spacing.mdGap,
  },
  recommendationCard: {
    backgroundColor: theme.surface,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.tightGap,
  },
  recommendationHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.smGap,
  },
  recommendationName: {
    flex: 1,
    color: theme.gold,
    fontSize: 16,
    fontWeight: "900",
  },
  actionBadge: {
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  actionBadgeText: {
    color: theme.gold,
    fontSize: 11,
    fontWeight: "800",
  },
  recommendationAddress: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
  },
  recommendationFact: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "600",
  },
  detailLink: {
    marginTop: spacing.tightGap,
    alignSelf: "flex-start",
  },
  detailLinkText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
    textDecorationLine: "underline",
  },
  messageBubble: {
    borderRadius: radius.lg,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.tightGap,
  },
  messageBubbleUser: {
    backgroundColor: theme.surfaceSoft,
  },
  messageBubbleAssistant: {
    backgroundColor: theme.surface,
  },
  messageText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
  },
  messageDate: {
    color: theme.muted,
    fontSize: 11,
    fontWeight: "600",
  },
});
