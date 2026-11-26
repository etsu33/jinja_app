import * as React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { appColors as theme } from "../../design/platformTheme";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import { typography } from "../../design/typography";
import {
  MONTH_DIRECTION_COMPASS_LINK_LABEL,
  MONTH_DIRECTION_MARK_LABEL,
  monthDirectionSummary,
  type ConciergeMonthDirection,
} from "../../../../packages/shared/monthDirection";

// 結果の上に1回だけ出す「今月のあなたの方角」。
// 生年月日を登録したログイン中の人にだけ Backend が返す。並び順には使っていない。
// ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」（2026-11-26 決定）
export function MonthDirectionSummary({ monthDirection }: { monthDirection: ConciergeMonthDirection | null }) {
  const router = useRouter();
  if (!monthDirection) return null;
  return (
    <View style={styles.summary}>
      <Text style={styles.summaryText}>{monthDirectionSummary(monthDirection)}</Text>
      <Pressable
        onPress={() => router.push("/compass")}
        accessibilityRole="link"
        accessibilityLabel={MONTH_DIRECTION_COMPASS_LINK_LABEL}
        style={({ pressed }) => [styles.link, pressed && styles.pressed]}
      >
        <Text style={styles.linkText}>{MONTH_DIRECTION_COMPASS_LINK_LABEL}</Text>
      </Pressable>
    </View>
  );
}

// 今月の方角にある神社にだけ付ける印。合わない神社には何も出さない。
export function MonthDirectionMark({ inMonthDirection }: { inMonthDirection: boolean }) {
  if (!inMonthDirection) return null;
  return (
    <View style={styles.mark}>
      <Text style={styles.markText}>{MONTH_DIRECTION_MARK_LABEL}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  summary: {
    gap: spacing.tightGap,
    padding: cardSizes.cardPaddingLg,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    backgroundColor: theme.surfaceSoft,
  },
  summaryText: {
    ...typography.bodyStrong,
    color: theme.text,
  },
  link: {
    alignSelf: "flex-start",
    minHeight: 44,
    justifyContent: "center",
  },
  linkText: {
    ...typography.footnoteStrong,
    color: theme.accent,
  },
  pressed: {
    opacity: 0.8,
  },
  mark: {
    alignSelf: "flex-start",
    paddingHorizontal: spacing.smGap,
    paddingVertical: 2,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.accent,
  },
  markText: {
    ...typography.caption,
    color: theme.accent,
  },
});
