import * as React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appColors as theme } from "../../design/platformTheme";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import { typography } from "../../design/typography";
import { describeReferenceDirections } from "../../lib/compass";

// 8方位を3×3のマスで見せる。Web は SVG の輪だが、Mobile には react-native-svg が
// 入っていないため、部品を足さずに View だけで描く。
// 色だけに頼らない: 強調する方位は塗りに加えて太字にし、同じ内容を下に文でも出す。
const GRID: ReadonlyArray<ReadonlyArray<string | null>> = [
  ["北西", "北", "北東"],
  ["西", null, "東"],
  ["南西", "南", "南東"],
];

const CELL_SIZE = 64;

export function CompassDirectionGrid({ referenceDirections }: { referenceDirections: string[] }) {
  const highlighted = new Set(referenceDirections);
  const summary = describeReferenceDirections(referenceDirections);

  return (
    <View style={styles.wrap}>
      <View accessible accessibilityRole="image" accessibilityLabel={summary} style={styles.grid}>
        {GRID.map((row, rowIndex) => (
          <View key={rowIndex} style={styles.row} importantForAccessibility="no-hide-descendants">
            {row.map((label, columnIndex) => {
              if (!label) {
                return (
                  <View key={`center-${columnIndex}`} style={[styles.cell, styles.center]}>
                    <View style={styles.centerDot} />
                  </View>
                );
              }
              const active = highlighted.has(label);
              return (
                <View key={label} style={[styles.cell, active ? styles.cellActive : styles.cellIdle]}>
                  <Text style={[styles.label, active ? styles.labelActive : styles.labelIdle]}>{label}</Text>
                </View>
              );
            })}
          </View>
        ))}
      </View>
      <Text style={styles.summary}>{summary}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: "center",
    gap: spacing.lgGap,
  },
  grid: {
    gap: spacing.tightGap,
  },
  row: {
    flexDirection: "row",
    gap: spacing.tightGap,
  },
  cell: {
    width: CELL_SIZE,
    height: CELL_SIZE,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  cellIdle: {
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderHeader,
  },
  cellActive: {
    backgroundColor: theme.accent,
    borderWidth: 1,
    borderColor: theme.accent,
  },
  center: {
    backgroundColor: "transparent",
  },
  centerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.mutedDark,
  },
  label: {
    ...typography.label,
  },
  labelIdle: {
    color: theme.muted,
  },
  labelActive: {
    color: theme.background,
    fontWeight: "700",
  },
  summary: {
    ...typography.subhead,
    color: theme.mutedSoft,
    textAlign: "center",
  },
});
