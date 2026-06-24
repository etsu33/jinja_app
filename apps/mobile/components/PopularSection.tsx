import { View, Text, Pressable, StyleSheet, ScrollView } from "react-native";
import PopularShrineCard from "./PopularShrineCard";
import { CardSkeleton } from "./Skeletons";
import { usePopularShrines } from "../hooks/usePopularShrines";
import { useRouter } from "expo-router";
import { spacing } from "../app/design/spacing";
import { cardSizes } from "../app/design/cardSizes";
import { radius } from "../app/design/radius";
import { colors } from "../app/theme";

export default function PopularSection() {
  const router = useRouter();
  const { state, reload } = usePopularShrines(10);

  const goMap = () =>
    // map 画面がある前提のまま残しています。未実装ならここは後続PRで対応。
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    router.push({ pathname: "/map", params: { filter: "popular", radius_km: "10" } });

  return (
    <View style={styles.box}>
      <View style={styles.header}>
        <Text style={styles.title}>{state.status === "ready" && state.nearby ? "近場の人気" : "人気の神社"}</Text>
        <Pressable onPress={goMap}>
          <Text style={styles.link}>地図で見る</Text>
        </Pressable>
      </View>

      {state.status === "loading" && (
        <View style={styles.skeletonList}>
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </View>
      )}

      {state.status === "error" && (
        <View style={styles.error}>
          <Text style={styles.errorText}>読み込みに失敗しました</Text>
          <Pressable onPress={reload}>
            <Text style={styles.retry}>再試行</Text>
          </Pressable>
        </View>
      )}

      {state.status === "ready" && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.listContent}
        >
          {state.data.map((s) => (
            <PopularShrineCard
              key={String(s.id)}
              id={s.id}
              name={s.name}
              address={s.address}
              popularity={s.popularity}
              rating={s.rating}
              photo_url={s.photo_url}
            />
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    paddingHorizontal: spacing.screenX,
    paddingVertical: spacing.lgGap,
    backgroundColor: colors.surfaceMuted,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.smGap,
  },
  title: { fontSize: 18, fontWeight: "700" },
  link: { color: colors.link, fontWeight: "600" },
  skeletonList: {
    gap: spacing.mdGap,
  },
  listContent: {
    paddingRight: spacing.screenX,
    gap: spacing.lgGap,
  },
  error: {
    backgroundColor: colors.errorBackground,
    borderRadius: radius.xs,
    padding: cardSizes.cardPaddingSm,
    alignItems: "center",
    gap: spacing.smGap,
  },
  errorText: { color: colors.error },
  retry: { color: colors.link, fontWeight: "600" },
});
