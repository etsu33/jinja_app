import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";

export default function ProfileScreen() {
  const router = useRouter();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Pressable onPress={() => router.replace("/mypage")} style={styles.backButton}>
          <Text style={styles.backText}>← マイページへ戻る</Text>
        </Pressable>
        <Text style={styles.eyebrow}>PROFILE</Text>
        <Text style={styles.title}>プロフィール</Text>
        <Text style={styles.subtitle}>
          表示名やプロフィール情報を確認する場所です。最近見た神社や参拝記録は、記録タブにまとめます。
        </Text>
      </View>

      <View style={styles.card}>
        <View style={styles.iconBox}>
          <Text style={styles.iconText}>人</Text>
        </View>
        <View style={styles.cardBody}>
          <Text style={styles.cardTitle}>プロフィールカード</Text>
          <Text style={styles.cardDescription}>名前・表示名・アカウント情報は今後ここにまとめます。</Text>
          <Text style={styles.cardMeta}>現在はプロフィール設定の準備中です。</Text>
        </View>
      </View>

      <View style={styles.noticeCard}>
        <Text style={styles.noticeTitle}>この画面に置くもの</Text>
        <Text style={styles.noticeText}>
          表示名、プロフィール画像、アカウント状態など、ユーザー自身の情報だけを扱います。
        </Text>
      </View>
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
  eyebrow: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 2,
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
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: theme.surface,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    padding: cardSizes.cardPaddingLg,
  },
  iconBox: {
    width: 48,
    height: 48,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    alignItems: "center",
    justifyContent: "center",
  },
  iconText: {
    color: theme.gold,
    fontSize: 20,
    fontWeight: "900",
  },
  cardBody: {
    flex: 1,
    gap: spacing.tightGap,
  },
  cardTitle: {
    color: theme.text,
    fontSize: 16,
    fontWeight: "900",
  },
  cardDescription: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "700",
  },
  cardMeta: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },
  noticeCard: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.smGap,
  },
  noticeTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "900",
  },
  noticeText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
