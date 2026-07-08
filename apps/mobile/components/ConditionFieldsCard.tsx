import * as React from "react";
import { View, Text, TextInput, Pressable, StyleSheet } from "react-native";
import { kamimusubiDark as theme } from "../app/theme";
import { VISIT_STYLE_OPTIONS, GORIYAKU_OPTIONS } from "../lib/conditionPayload";

// Home画面・Concierge結果画面で共通の条件レイヤー入力（誕生日・参拝スタイル・ご利益・補助条件）
export type ConditionFieldsCardProps = {
  birthdate: string;
  onChangeBirthdate: (value: string) => void;
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
  selectedVisitStyle,
  onSelectVisitStyle,
  selectedGoriyaku,
  onSelectGoriyaku,
  supportText,
  onChangeSupportText,
  disabled,
}: ConditionFieldsCardProps) {
  return (
    <View style={styles.wrap}>
      <View style={styles.inputBlock}>
        <Text style={styles.label}>誕生日</Text>
        <TextInput
          value={birthdate}
          onChangeText={onChangeBirthdate}
          placeholder="例: 1984-05-15"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          editable={!disabled}
        />
      </View>

      <View style={styles.block}>
        <Text style={styles.label}>参拝スタイル</Text>
        <View style={styles.row}>
          {VISIT_STYLE_OPTIONS.map((option) => {
            const active = selectedVisitStyle === option;
            return (
              <Pressable
                key={option}
                onPress={() => onSelectVisitStyle(active ? undefined : option)}
                style={[styles.pill, active && styles.pillActive]}
              >
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{option}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.block}>
        <Text style={styles.label}>ご利益</Text>
        <View style={styles.row}>
          {GORIYAKU_OPTIONS.map((option) => {
            const active = selectedGoriyaku === option;
            return (
              <Pressable
                key={option}
                onPress={() => onSelectGoriyaku(active ? undefined : option)}
                style={[styles.pill, active && styles.pillActive]}
              >
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{option}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.inputBlock}>
        <Text style={styles.label}>相談補助条件</Text>
        <TextInput
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
    gap: 12,
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
  textarea: {
    minHeight: 76,
    textAlignVertical: "top",
  },
  block: {
    gap: 8,
  },
  label: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.7,
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  pill: {
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 999,
    paddingHorizontal: 11,
    paddingVertical: 7,
    backgroundColor: theme.surface,
  },
  pillActive: {
    borderColor: theme.borderGold,
    backgroundColor: theme.gold,
  },
  pillText: {
    color: theme.mutedSoft,
    fontSize: 12,
    fontWeight: "800",
  },
  pillTextActive: {
    color: theme.background,
  },
});
