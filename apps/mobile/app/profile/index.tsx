import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { appColors as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { useProfileStore } from "../../store/profileStore";
import { normalizeBirthday } from "../../lib/profile";
import { ProfilePickerModal } from "../../components/profile/ProfilePickerModal";
import { typography } from "../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 保存済みの印。グリフの ✓ は端末のフォント次第で字形が変わるため Ionicons を使う。
const SAVE_ICON_SIZE = 16;

// リストの送り記号。旧実装は "›" のグリフだった。
const CHEVRON_SIZE = 20;

const PREFECTURES = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"];
type PickerKind = "year" | "month" | "day" | "time" | "place" | null;

export default function ProfileScreen() {
  const { userProfile, derivedProfile, directionProfile, setBirthday, setBirthTime, setBirthPlace } =
    useProfileStore();
  const normalizedBirthday = normalizeBirthday(userProfile.birthday);
  const birthdayParts = normalizedBirthday?.split("-") ?? [];
  const [picker, setPicker] = React.useState<PickerKind>(null);
  const [draftYear, setDraftYear] = React.useState(birthdayParts[0] ?? "1990");
  const [draftMonth, setDraftMonth] = React.useState(birthdayParts[1] ?? "01");

  const years = Array.from({ length: new Date().getFullYear() - 1899 }, (_, index) => String(new Date().getFullYear() - index));
  const today = new Date();
  const monthCount = Number(draftYear) === today.getFullYear() ? today.getMonth() + 1 : 12;
  const months = Array.from({ length: monthCount }, (_, index) => String(index + 1).padStart(2, "0"));
  const calendarDays = new Date(Number(draftYear), Number(draftMonth), 0).getDate();
  const daysInMonth = Number(draftYear) === today.getFullYear() && Number(draftMonth) === today.getMonth() + 1
    ? today.getDate()
    : calendarDays;
  const days = Array.from({ length: daysInMonth }, (_, index) => String(index + 1).padStart(2, "0"));
  const times = Array.from({ length: 24 * 12 }, (_, index) => {
    const hour = Math.floor(index / 12);
    const minute = (index % 12) * 5;
    return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  });

  const fmtDerived = (v?: string) => v ?? "未計算";
  const openBirthdayPicker = () => {
    setDraftYear(birthdayParts[0] ?? "1990");
    setDraftMonth(birthdayParts[1] ?? "01");
    setPicker("year");
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.subtitle}>
          あなたの基本情報を入力すると、神社提案に活用されます。
        </Text>
        <View style={styles.saveNotice}>
          <Ionicons name="checkmark-circle-outline" size={SAVE_ICON_SIZE} color={theme.cedar} />
          <Text style={styles.saveNoticeText}>入力内容はこの端末に自動保存されます</Text>
        </View>
      </View>

      {/* UserProfile */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>基本情報</Text>

        <View style={styles.row}>
          <Text style={styles.label}>生年月日</Text>
          <Pressable style={styles.selectButton} onPress={openBirthdayPicker} accessibilityRole="button">
            <Text style={[styles.selectText, !normalizedBirthday && styles.placeholder]}>
              {normalizedBirthday ? `${birthdayParts[0]}年${Number(birthdayParts[1])}月${Number(birthdayParts[2])}日` : "選択してください"}
            </Text>
            <Ionicons name="chevron-forward" size={CHEVRON_SIZE} color={theme.accent} />
          </Pressable>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>出生時間</Text>
          <Pressable style={styles.selectButton} onPress={() => setPicker("time")} accessibilityRole="button">
            <Text style={[styles.selectText, !userProfile.birthTime && styles.placeholder]}>{userProfile.birthTime || "不明・未設定"}</Text>
            <Ionicons name="chevron-forward" size={CHEVRON_SIZE} color={theme.accent} />
          </Pressable>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>出生地</Text>
          <Pressable style={styles.selectButton} onPress={() => setPicker("place")} accessibilityRole="button">
            <Text style={[styles.selectText, !userProfile.birthPlace && styles.placeholder]}>{userProfile.birthPlace || "都道府県を選択"}</Text>
            <Ionicons name="chevron-forward" size={CHEVRON_SIZE} color={theme.accent} />
          </Pressable>
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
        <Text style={styles.sectionTitle}>{directionProfile.targetYear ? `${directionProfile.targetYear}年の方位プロフィール` : "方位プロフィール"}</Text>
        <View style={styles.row}>
          <Text style={styles.label}>吉方位</Text>
          <Text style={styles.value}>{directionProfile.luckyDirections?.length ? directionProfile.luckyDirections.join("・") : "該当なし"}</Text>
        </View>
        <Text style={styles.noticeText}>年盤をもとに凶方位を除外した補助情報です。参拝日単位の月盤・日盤は含みません。</Text>
      </View>

      {/* Concierge */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>コンシェルジュへの反映</Text>
        <Text style={styles.noticeText}>
          プロフィール情報は、神社提案の補助情報として利用されます。
        </Text>
      </View>

      <ProfilePickerModal visible={picker === "year"} title="生まれた年" options={years.map((value) => ({ value, label: `${value}年` }))} selectedValue={draftYear} onClose={() => setPicker(null)} onSelect={(value) => { setDraftYear(value); if (Number(value) === today.getFullYear() && Number(draftMonth) > today.getMonth() + 1) setDraftMonth(String(today.getMonth() + 1).padStart(2, "0")); setPicker("month"); }} />
      <ProfilePickerModal visible={picker === "month"} title="生まれた月" options={months.map((value) => ({ value, label: `${Number(value)}月` }))} selectedValue={draftMonth} onClose={() => setPicker(null)} onSelect={(value) => { setDraftMonth(value); setPicker("day"); }} />
      <ProfilePickerModal visible={picker === "day"} title="生まれた日" options={days.map((value) => ({ value, label: `${Number(value)}日` }))} selectedValue={birthdayParts[2]} onClose={() => setPicker(null)} onSelect={(value) => setBirthday(`${draftYear}-${draftMonth}-${value}`)} />
      <ProfilePickerModal visible={picker === "time"} title="出生時間（5分単位）" options={[{ value: "", label: "不明・未設定" }, ...times.map((value) => ({ value, label: value }))]} selectedValue={userProfile.birthTime ?? ""} onClose={() => setPicker(null)} onSelect={setBirthTime} />
      <ProfilePickerModal visible={picker === "place"} title="出生地" options={[{ value: "", label: "不明・未設定" }, ...PREFECTURES.map((value) => ({ value, label: value }))]} selectedValue={userProfile.birthPlace ?? ""} onClose={() => setPicker(null)} onSelect={setBirthPlace} />
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
  subtitle: {
    ...typography.body,
    color: theme.text,
  },
  // 印(Ionicons)と文字が横に並ぶ。
  saveNotice: { alignSelf: "flex-start", backgroundColor: theme.cedarSurface, borderRadius: radius.md, paddingHorizontal: 12, paddingVertical: 8, flexDirection: "row", alignItems: "center", gap: 6 },
  saveNoticeText: { ...typography.footnote, color: theme.cedar },
  sectionCard: {
    backgroundColor: theme.surface,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  sectionTitle: {
    ...typography.title,
    color: theme.accent,
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
  // HIGの最小タップ領域44pt。文字と余白だけでは37ptにしかならない。
  selectButton: { minHeight: 44, minWidth: 180, flexDirection: "row", alignItems: "center", justifyContent: "flex-end", gap: 8, paddingVertical: 8 },
  selectText: { ...typography.label, color: theme.text },
  placeholder: { color: theme.muted },
  label: {
    ...typography.label,
    color: theme.text,
    flex: 1,
  },
  value: {
    ...typography.body,
    color: theme.muted,
  },
  noticeText: {
    ...typography.subhead,
    color: theme.muted,
  },
});
