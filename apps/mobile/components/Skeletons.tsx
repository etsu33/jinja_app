import { View, StyleSheet } from "react-native";
import { kamimusubiDark as theme } from "../app/theme";
import { spacing } from "../app/design/spacing";
import { cardSizes } from "../app/design/cardSizes";

export function CardSkeleton() {
  return (
    <View style={styles.card}>
      <View style={[styles.shimmer, { width: "60%", height: 14 }]} />
      <View style={[styles.shimmer, { width: "85%", height: 12, marginTop: spacing.smGap }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: cardSizes.skeletonWidth,
    backgroundColor: theme.surface,
    borderRadius: cardSizes.skeletonRadius,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.inlineGap - 1,
    elevation: 2,
  },
  shimmer: { backgroundColor: theme.borderSoft, borderRadius: cardSizes.shimmerRadius },
});
