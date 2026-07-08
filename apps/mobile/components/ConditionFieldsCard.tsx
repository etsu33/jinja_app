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
          value={birthdate}
          onChangeText={onChangeBirthdate}
          placeholder="例: 1984-05-15"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          editable={!disabled}
        />
      </View>

      <View style={styles.divider} />

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
                onPress={() => onSelectVisitStyle(active ? undefined : option)}
                style={[styles.pill, active && styles.pillActive]}
              >
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{option}</Text>
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
                onPress={() => onSelectGoriyaku(active ? undefined : option)}
                style={[styles.pill, active && styles.pillActive]}
              >
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{option}</Text>
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
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderRadius: 999,
    paddingHorizontal: 11,
    paddingVertical: 6,
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
