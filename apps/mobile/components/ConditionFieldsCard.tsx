import * as React from "react";
import { View, Text, TextInput, Pressable, StyleSheet } from "react-native";
import { appColors as theme, inputAppearance } from "../design/platformTheme";
import { VISIT_STYLE_OPTIONS, GORIYAKU_OPTIONS } from "../lib/conditionPayload";
import { ProfilePickerModal } from "./profile/ProfilePickerModal";
import { MobileOriginSelector } from "./MobileOriginSelector";
import type { UserOrigin } from "../../../packages/shared/userOrigin";
import { typography } from "../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 選択中の印。グリフの ✓ は端末のフォント次第で字形が変わるため Ionicons を使う。
const CHECK_ICON_SIZE = 15;

// リストの送り記号。旧実装は "›" のグリフだった。
const CHEVRON_SIZE = 20;

// Home画面・Concierge結果画面で共通の条件レイヤー入力（誕生日・参拝スタイル・ご利益・補助条件）
export type ConditionFieldsCardProps = {
  birthdate: string;
  onChangeBirthdate: (value: string) => void;
  plannedVisitDate: string;
  onChangePlannedVisitDate: (value: string) => void;
  locationStatus?: "idle" | "loading" | "ready" | "error";
  onUseCurrentLocation?: () => void;
  origin?: UserOrigin | null;
  onChangeOrigin?: (value: UserOrigin | null) => void;
  selectedVisitStyle?: string;
  onSelectVisitStyle: (value: string | undefined) => void;
  selectedGoriyaku?: string;
  onSelectGoriyaku: (value: string | undefined) => void;
  supportText: string;
  onChangeSupportText: (value: string) => void;
  disabled?: boolean;
};

export function ConditionFieldsCard({
  birthdate,
  onChangeBirthdate,
  plannedVisitDate,
  onChangePlannedVisitDate,
  locationStatus = "idle",
  onUseCurrentLocation,
  origin = null,
  onChangeOrigin = () => undefined,
  selectedVisitStyle,
  onSelectVisitStyle,
  selectedGoriyaku,
  onSelectGoriyaku,
  supportText,
  onChangeSupportText,
  disabled,
}: ConditionFieldsCardProps) {
  const today = new Date();
  const currentParts = plannedVisitDate.split("-");
  const [datePicker, setDatePicker] = React.useState<"year" | "month" | "day" | null>(null);
  const [draftYear, setDraftYear] = React.useState(currentParts[0] || String(today.getFullYear()));
  const [draftMonth, setDraftMonth] = React.useState(currentParts[1] || String(today.getMonth() + 1).padStart(2, "0"));
  const years = [String(today.getFullYear()), String(today.getFullYear() + 1)];
  const firstMonth = Number(draftYear) === today.getFullYear() ? today.getMonth() + 1 : 1;
  const months = Array.from({ length: 13 - firstMonth }, (_, index) => String(firstMonth + index).padStart(2, "0"));
  const calendarDays = new Date(Number(draftYear), Number(draftMonth), 0).getDate();
  const firstDay = Number(draftYear) === today.getFullYear() && Number(draftMonth) === today.getMonth() + 1 ? today.getDate() : 1;
  const days = Array.from({ length: calendarDays - firstDay + 1 }, (_, index) => String(firstDay + index).padStart(2, "0"));
  const openDatePicker = () => {
    setDraftYear(currentParts[0] || String(today.getFullYear()));
    setDraftMonth(currentParts[1] || String(today.getMonth() + 1).padStart(2, "0"));
    setDatePicker("year");
  };

  return (
    <View style={styles.wrap}>
      <View style={styles.intro}>
        <Text style={styles.introBadge}>任意</Text>
        <Text style={styles.introText}>
          すべて任意の補助条件です。必要な項目だけ選ぶと、次の相談画面でその条件を反映したご縁を確認できます。
        </Text>
      </View>

      <View style={styles.divider} />

      <View style={styles.inputBlock}>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>誕生日</Text>
          <Text style={styles.caption}>命式や吉方位の参考にします</Text>
        </View>
        <TextInput
          {...inputAppearance}
          accessibilityLabel="誕生日"
          value={birthdate}
          onChangeText={onChangeBirthdate}
          placeholder="例: 1984-05-15"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          editable={!disabled}
        />
      </View>

      <View style={styles.divider} />

      <View style={styles.inputBlock}>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>参拝予定日</Text>
          <Text style={styles.caption}>予定日の年盤・月盤から吉方位を計算します</Text>
        </View>
        <Pressable onPress={openDatePicker} disabled={disabled} style={styles.selectInput} accessibilityRole="button" accessibilityLabel="参拝予定日を選択" accessibilityValue={{ text: plannedVisitDate || "未選択" }} accessibilityState={{ disabled: !!disabled }}>
          <Text style={plannedVisitDate ? styles.selectInputText : styles.selectPlaceholder}>{plannedVisitDate || "日付を選択"}</Text>
          <Ionicons name="chevron-forward" size={CHEVRON_SIZE} color={theme.accent} />
        </Pressable>
        {plannedVisitDate ? <Pressable onPress={() => onChangePlannedVisitDate("")} style={styles.clearButton} accessibilityRole="button" accessibilityLabel="予定日を解除"><Text style={styles.clearText}>予定日を解除</Text></Pressable> : null}
      </View>

      <View style={styles.divider} />

      <View style={styles.inputBlock}>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>出発地点</Text>
          <Text style={styles.caption}>現在地から神社への方角を計算します</Text>
        </View>
        <MobileOriginSelector origin={origin} onChange={onChangeOrigin} onUseDevice={onUseCurrentLocation ?? (()=>undefined)} locationStatus={locationStatus} disabled={disabled} />
      </View>

      <ProfilePickerModal visible={datePicker === "year"} title="参拝する年" options={years.map((value) => ({ value, label: `${value}年` }))} selectedValue={draftYear} onClose={() => setDatePicker(null)} onSelect={(value) => { setDraftYear(value); if (Number(value) === today.getFullYear() && Number(draftMonth) < today.getMonth() + 1) setDraftMonth(String(today.getMonth() + 1).padStart(2, "0")); setDatePicker("month"); }} />
      <ProfilePickerModal visible={datePicker === "month"} title="参拝する月" options={months.map((value) => ({ value, label: `${Number(value)}月` }))} selectedValue={draftMonth} onClose={() => setDatePicker(null)} onSelect={(value) => { setDraftMonth(value); setDatePicker("day"); }} />
      <ProfilePickerModal visible={datePicker === "day"} title="参拝する日" options={days.map((value) => ({ value, label: `${Number(value)}日` }))} selectedValue={currentParts[2]} onClose={() => setDatePicker(null)} onSelect={(value) => onChangePlannedVisitDate(`${draftYear}-${draftMonth}-${value}`)} />

      <View style={styles.block}>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>参拝スタイル</Text>
          <Text style={styles.caption}>今の気分に近いものを一つ選べます</Text>
        </View>
        <View style={styles.row}>
          {VISIT_STYLE_OPTIONS.map((option) => {
            const active = selectedVisitStyle === option;
            return (
              <Pressable
                key={option}
                disabled={disabled}
                onPress={() => onSelectVisitStyle(active ? undefined : option)}
                style={[styles.pill, active && styles.pillActive]}
                accessibilityRole="radio"
                accessibilityState={{ checked: active, disabled: !!disabled }}
                accessibilityLabel={option}
              >
                <>
                  {active ? (
                    <Ionicons name="checkmark" size={CHECK_ICON_SIZE} color={theme.accent} />
                  ) : null}
                  <Text style={[styles.pillText, active && styles.pillTextActive]}>{option}</Text>
                </>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.divider} />

      <View style={styles.block}>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>ご利益</Text>
          <Text style={styles.caption}>気になるものを一つ選べます</Text>
        </View>
        <View style={styles.row}>
          {GORIYAKU_OPTIONS.map((option) => {
            const active = selectedGoriyaku === option;
            return (
              <Pressable
                key={option}
                disabled={disabled}
                onPress={() => onSelectGoriyaku(active ? undefined : option)}
                style={[styles.pill, active && styles.pillActive]}
                accessibilityRole="radio"
                accessibilityState={{ checked: active, disabled: !!disabled }}
                accessibilityLabel={option}
              >
                <>
                  {active ? (
                    <Ionicons name="checkmark" size={CHECK_ICON_SIZE} color={theme.accent} />
                  ) : null}
                  <Text style={[styles.pillText, active && styles.pillTextActive]}>{option}</Text>
                </>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.divider} />

      <View style={styles.inputBlock}>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>相談補助条件</Text>
          <Text style={styles.caption}>場所や時間の希望があれば自由にどうぞ</Text>
        </View>
        <TextInput
          {...inputAppearance}
          accessibilityLabel="相談補助条件"
          value={supportText}
          onChangeText={onChangeSupportText}
          placeholder="例: 駅から近い場所、静かな場所、短時間で行ける場所"
          placeholderTextColor={theme.mutedDark}
          style={[styles.input, styles.textarea]}
          multiline
          editable={!disabled}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 16,
  },
  intro: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
  },
  introBadge: {
    color: theme.accentSoft,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5,
    borderWidth: 1,
    borderColor: theme.borderAccentDark,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
    overflow: "hidden",
  },
  introText: {
    ...typography.footnote,
    flex: 1,
    color: theme.muted,
  },
  divider: {
    height: 1,
    backgroundColor: theme.borderSoft,
  },
  inputBlock: {
    gap: 8,
  },
  input: {
    ...typography.bodyStrong,
    minHeight: 44,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: theme.text,
  },
  selectInput: { minHeight: 44, backgroundColor: theme.surface, borderWidth: 1, borderColor: theme.borderSoft, borderRadius: 14, paddingHorizontal: 12, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  selectInputText: { ...typography.bodyStrong, color: theme.text },
  selectPlaceholder: { ...typography.label, color: theme.mutedDark },
  clearText: { ...typography.label, color: theme.muted, alignSelf: "flex-end" },
  clearButton: { minHeight: 44, alignSelf: "flex-end", justifyContent: "center", paddingHorizontal: 8 },
  locationButton: { minHeight: 44, borderWidth: 1, borderColor: theme.borderSoft, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: theme.surface },
  locationButtonReady: { borderColor: theme.borderAccent, backgroundColor: theme.accent },
  locationButtonText: { ...typography.label, color: theme.text },
  locationButtonTextReady: { color: theme.background },
  locationError: { ...typography.footnote, color: theme.error },
  textarea: {
    minHeight: 76,
    textAlignVertical: "top",
  },
  block: {
    gap: 8,
  },
  sectionHeader: {
    gap: 2,
  },
  label: {
    ...typography.eyebrow,
    color: theme.mutedSoft,
  },
  caption: {
    ...typography.caption,
    color: theme.mutedDark,
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  pill: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 999,
    paddingHorizontal: 11,
    paddingVertical: 10,
    // 選択中は印(Ionicons)と文字が横に並ぶ。
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    justifyContent: "center",
    backgroundColor: "transparent",
  },
  pillActive: {
    borderColor: theme.borderAccent,
    backgroundColor: theme.accent,
  },
  pillText: {
    ...typography.footnoteStrong,
    color: theme.mutedSoft,
  },
  pillTextActive: {
    color: theme.background,
  },
});
