import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";
import { useProfileStore } from "../../store/profileStore";

export default function ProfileScreen() {
  const router = useRouter();
  const { userProfile, derivedProfile, directionProfile, setBirthday, setBirthTime, setBirthPlace, setWorshipStyle } =
    useProfileStore();

  const fmt = (v?: string) => v ?? "未設定";
  const fmtDerived = (v?: string) => v ?? "未計算";

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Pressable onPress={() => router.replace("/mypage")} style={styles.backButton}>
          <Text style={styles.backText}>← マイページへ戻る</Text>
        </Pressable>
        <Text style={styles.eyebrow}>PROFILE</Text>
        <Text style={styles.title}>プロフィール</Text>
        <Text style={styles.subtitle}>
          あなたの基本情報を入力すると、神社提案に活用されます。
        </Text>
      </View>

      {/* UserProfile */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>基本情報</Text>

        <View style={styles.row}>
          <Text style={styles.label}>生年月日</Text>
          <TextInput
            style={styles.input}
            value={userProfile.birthday ?? ""}
            onChangeText={setBirthday}
            placeholder="例: 1990-04-01"
            placeholderTextColor={theme.muted}
            keyboardType="numbers-and-punctuation"
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>出生時間</Text>
          <TextInput
            style={styles.input}
            value={userProfile.birthTime ?? ""}
            onChangeText={setBirthTime}
            placeholder="例: 08:30"
            placeholderTextColor={theme.muted}
            keyboardType="numbers-and-punctuation"
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>出生地</Text>
          <TextInput
            style={styles.input}
            value={userProfile.birthPlace ?? ""}
            onChangeText={setBirthPlace}
            placeholder="例: 東京都"
            placeholderTextColor={theme.muted}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>参拝スタイル</Text>
          <TextInput
            style={styles.input}
            value={userProfile.worshipStyle ?? ""}
            onChangeText={setWorshipStyle}
            placeholder="例: 朝参り"
            placeholderTextColor={theme.muted}
          />
        </View>
      </View>

      {/* DerivedProfile */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>派生プロフィール</Text>

        <View style={styles.row}>
          <Text style={styles.label}>九星気学</Text>
          <Text style={styles.value}>{fmtDerived(derivedProfile.kyusei)}</Text>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>五行</Text>
          <Text style={styles.value}>{fmtDerived(derivedProfile.gogyo)}</Text>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>ライフパス</Text>
          <Text style={styles.value}>{fmtDerived(derivedProfile.lifePath)}</Text>
        </View>
      </View>

      {/* DirectionProfile */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>方位プロフィール</Text>
        <View style={styles.row}>
          <Text style={styles.label}>吉方位</Text>
          <Text style={styles.value}>{fmtDerived(directionProfile.luckyDirection)}</Text>
        </View>
      </View>

      {/* Concierge */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>コンシェルジュへの反映</Text>
        <Text style={styles.noticeText}>
          プロフィール情報は、神社提案の補助情報として利用されます。
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
    flex: 1,
  },
  value: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: "600",
  },
  input: {
    flex: 1,
    color: theme.text,
    fontSize: 14,
    fontWeight: "600",
    textAlign: "right",
  },
  noticeText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
