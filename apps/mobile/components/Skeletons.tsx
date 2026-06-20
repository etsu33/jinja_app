import { View, StyleSheet } from "react-native";
import { kamimusubiDark as theme } from "../app/theme";

export function CardSkeleton() {
  return (
    <View style={styles.card}>
      <View style={[styles.shimmer, { width: "60%", height: 14 }]} />
      <View style={[styles.shimmer, { width: "85%", height: 12, marginTop: 8 }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 160,
    backgroundColor: theme.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.border,
    padding: 14,
    gap: 6,
    elevation: 2,
  },
  shimmer: { backgroundColor: theme.borderSoft, borderRadius: 8 },
});
