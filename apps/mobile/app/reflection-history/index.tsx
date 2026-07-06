import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
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

function ReflectionCard({ reflection }: { reflection: ShrineReflectionResponse }) {
  const shrineName = reflection.shrine_name?.trim() || "神社名未設定";
  const historyTheme = reflection.history_theme?.trim() || "テーマ未設定";
  const answer = reflection.answer?.trim() || "振り返り本文はまだありません。";
  const createdAt = formatDate(reflection.created_at);

  return (
    <View style={styles.reflectionCard}>
      <View style={styles.cardHeader}>
        <Text style={styles.shrineName}>{shrineName}</Text>
        <Text style={styles.createdAt}>{createdAt}</Text>
      </View>

      <View style={styles.themePill}>
        <Text style={styles.themePillText}>{historyTheme}</Text>
      </View>

      <Text style={styles.answerText}>{answer}</Text>

      {reflection.state_change_summary ? (
        <View style={styles.summaryBlock}>
          <Text style={styles.summaryLabel}>変化のメモ</Text>
          <Text style={styles.summaryText}>{reflection.state_change_summary}</Text>
        </View>
      ) : null}
    </View>
  );
}

export default function ReflectionHistoryScreen() {
  const router = useRouter();
  const [reflections, setReflections] = React.useState<ShrineReflectionResponse[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);

  React.useEffect(() => {
    let mounted = true;

    listShrineReflections()
      .then((items) => {
        if (mounted) {
          setReflections(items);
          setError(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setReflections([]);
          setError(true);
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
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

      {!loading && !error && reflections.length > 0 ? (
        <View style={styles.list}>
          {reflections.map((reflection) => (
            <ReflectionCard key={reflection.id} reflection={reflection} />
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
});
