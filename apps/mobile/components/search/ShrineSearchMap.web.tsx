// apps/mobile/components/search/ShrineSearchMap.web.tsx
import * as React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { kamimusubiDark as theme } from "../../design/theme";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import type { ShrineSearchMapProps } from "../../lib/shrineMap";

export function ShrineSearchMap({ points, selectedId, onSelect }: ShrineSearchMapProps) {
  return (
    <View style={styles.wrap} accessibilityRole="summary" accessibilityLabel="検索結果の神社を地図で見る">
      <Text style={styles.title}>地図表示はモバイルアプリで利用できます</Text>
      <Text style={styles.description}>この画面では、神社を一覧から選択できます。</Text>

      {points.length > 0 ? (
        <View style={styles.list}>
          {points.map((point) => {
            const selected = point.id === selectedId;
            return (
              <Pressable
                key={point.id}
                onPress={() => onSelect(point.id)}
                accessibilityRole="button"
                accessibilityLabel={selected ? `${point.name}を選択、選択中` : `${point.name}を選択`}
                accessibilityState={{ selected }}
                style={({ pressed }) => [styles.item, selected && styles.itemSelected, pressed && styles.itemPressed]}
              >
                <View style={styles.itemHeader}>
                  <Text style={styles.itemName} numberOfLines={1}>
                    {point.name}
                  </Text>
                  {selected ? <Text style={styles.itemSelectedBadge}>選択中</Text> : null}
                </View>
                {point.address ? (
                  <Text style={styles.itemAddress} numberOfLines={1}>
                    {point.address}
                  </Text>
                ) : null}
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderRadius: radius.lg,
    backgroundColor: theme.surfaceSoft,
    padding: spacing.mdGap,
    gap: spacing.tightGap,
  },
  title: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "800",
  },
  description: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
    marginBottom: spacing.tightGap,
  },
  list: {
    gap: spacing.tightGap,
  },
  item: {
    borderRadius: radius.xs,
    borderWidth: 1,
    borderColor: theme.border,
    backgroundColor: theme.surface,
    paddingHorizontal: spacing.mdGap,
    paddingVertical: spacing.tightGap,
  },
  itemSelected: {
    borderColor: theme.borderGold,
  },
  itemPressed: {
    opacity: 0.74,
  },
  itemHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.tightGap,
  },
  itemName: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "800",
  },
  itemSelectedBadge: {
    color: theme.gold,
    fontSize: 11,
    fontWeight: "800",
  },
  itemAddress: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
    marginTop: 2,
  },
});
