import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";
import { buildDerivedProfile } from "../../lib/profile";
import type { UserProfile } from "../../types/profile";

export default function ProfileScreen() {
  const router = useRouter();
  const userProfile: UserProfile = {
    birthday: undefined,
    birthTime: undefined,
    birthPlace: undefined,
    worshipStyle: undefined,
  };
  const derivedProfile = buildDerivedProfile(userProfile);
  const formatValue = (value?: string) => value ?? "未設定";
  const formatDerivedValue = (value?: string) => value ?? "未計算";

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

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>基本情報</Text>
        <View style={styles.row}>
          <Text style={styles.label}>生年月日</Text>
          <Text style={styles.value}>{formatValue(userProfile.birthday)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>出生時間</Text>
          <Text style={styles.value}>{formatValue(userProfile.birthTime)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>出生地</Text>
          <Text style={styles.value}>{formatValue(userProfile.birthPlace)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>参拝スタイル</Text>
          <Text style={styles.value}>{formatValue(userProfile.worshipStyle)}</Text>
        </View>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>派生プロフィール</Text>
        <View style={styles.row}>
          <Text style={styles.label}>九星気学</Text>
          <Text style={styles.value}>{formatDerivedValue(derivedProfile.kyusei)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>五行</Text>
          <Text style={styles.value}>{formatDerivedValue(derivedProfile.gogyo)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>ライフパス</Text>
          <Text style={styles.value}>{formatDerivedValue(derivedProfile.lifePath)}</Text>
        </View>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>コンシェルジュへの反映</Text>
        <Text style={styles.noticeText}>
          プロフィール情報は、{"\n"}神社提案の補助情報として利用されます。
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
  sectionCard: {
    backgroundColor: theme.surface,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  sectionTitle: {
    color: theme.gold,
    fontSize: 15,
    fontWeight: "900",
    marginBottom: spacing.tightGap,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: spacing.tightGap,
    borderBottomWidth: cardSizes.borderWidth,
    borderBottomColor: theme.borderHeader,
  },
  label: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "700",
  },
  value: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: "600",
  },
  noticeText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
