import * as React from "react";
import { View, Text, TextInput, Pressable, StyleSheet } from "react-native";
import { kamimusubiDark as theme } from "../design/theme";
import { VISIT_STYLE_OPTIONS, GORIYAKU_OPTIONS } from "../lib/conditionPayload";
import { ProfilePickerModal } from "./profile/ProfilePickerModal";
import { MobileOriginSelector } from "./MobileOriginSelector";
import type { UserOrigin } from "../../../packages/shared/userOrigin";

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
          <Text style={styles.selectChevron}>›</Text>
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
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{active ? `✓ ${option}` : option}</Text>
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
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{active ? `✓ ${option}` : option}</Text>
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
    color: theme.goldSoft,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5,
    borderWidth: 1,
    borderColor: theme.borderGoldDark,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
    overflow: "hidden",
  },
  introText: {
    flex: 1,
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "500",
  },
  divider: {
    height: 1,
    backgroundColor: theme.borderSoft,
  },
  inputBlock: {
    gap: 8,
  },
  input: {
    minHeight: 44,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: theme.text,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "700",
  },
  selectInput: { minHeight: 44, backgroundColor: theme.surface, borderWidth: 1, borderColor: theme.borderSoft, borderRadius: 14, paddingHorizontal: 12, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  selectInputText: { color: theme.text, fontSize: 14, fontWeight: "700" },
  selectPlaceholder: { color: theme.mutedDark, fontSize: 14 },
  selectChevron: { color: theme.gold, fontSize: 22 },
  clearText: { color: theme.muted, fontSize: 12, fontWeight: "700", alignSelf: "flex-end" },
  clearButton: { minHeight: 44, alignSelf: "flex-end", justifyContent: "center", paddingHorizontal: 8 },
  locationButton: { minHeight: 44, borderWidth: 1, borderColor: theme.borderSoft, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: theme.surface },
  locationButtonReady: { borderColor: theme.borderGold, backgroundColor: theme.gold },
  locationButtonText: { color: theme.text, fontSize: 13, fontWeight: "800" },
  locationButtonTextReady: { color: theme.background },
  locationError: { color: "#ef8f8f", fontSize: 11, lineHeight: 16 },
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
    color: theme.mutedSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.6,
  },
  caption: {
    color: theme.mutedDark,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: "500",
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
    justifyContent: "center",
    backgroundColor: "transparent",
  },
  pillActive: {
    borderColor: theme.borderGold,
    backgroundColor: theme.gold,
  },
  pillText: {
    color: theme.mutedSoft,
    fontSize: 12,
    fontWeight: "700",
  },
  pillTextActive: {
    color: theme.background,
  },
});
