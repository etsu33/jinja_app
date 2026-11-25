// apps/mobile/app/goshuin/index.tsx
import * as React from "react";
import { View, Text, Image, StyleSheet, ScrollView, Dimensions } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { getStamps } from "../../lib/storage";
import { appColors as theme } from "../../design/theme";
import Button from "../../components/ui/Button";
import { typography } from "../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 空状態の印の大きさ。
const EMPTY_ICON_SIZE = 32;

const GAP = 10;
const COLS = 3;
const W = (Math.min(Dimensions.get("window").width, 430) - 20 * 2 - GAP * (COLS - 1)) / COLS;

export default function GoshuinList() {
  const router = useRouter();
  const [stamps, setStamps] = React.useState<{ id: string; uri: string; createdAt: number }[]>([]);
  const [loading, setLoading] = React.useState(true);

  useFocusEffect(
    React.useCallback(() => {
      let alive = true;
      setLoading(true);

      (async () => {
        try {
          const list = await getStamps();
          if (alive) setStamps(list);
        } catch {
          if (alive) setStamps([]);
        } finally {
          if (alive) setLoading(false);
        }
      })();
      return () => {
        alive = false;
      };
    }, []),
  );

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.headerBar}>
        <Button
          title="＋ 記録する"
          variant="outline"
          size="compact"
          onPress={() => router.push("/goshuin/upload")}
          accessibilityLabel="御朱印の記録を追加する"
        />
      </View>

      <View style={styles.heroBlock}>
        <Text style={styles.heroLead}>参拝の記録</Text>
        <Text style={styles.heroTitle}>結んだご縁を、{`\n`}静かに残す</Text>
        <Text style={styles.heroCount}>{stamps.length} 件の御朱印</Text>
      </View>

      {loading ? (
        <Text style={styles.stateText}>確認中…</Text>
      ) : stamps.length > 0 ? (
        <View style={styles.gridCard}>
          <Text style={styles.sectionLabel}>GOSHUIN</Text>
          <View style={styles.grid}>
            {stamps.map((s, index) => (
              <Image
                key={String(s.id)}
                source={{ uri: s.uri }}
                accessible
                accessibilityRole="image"
                accessibilityLabel={`御朱印の記録 ${index + 1}件目`}
                style={[
                  styles.stampImage,
                  {
                    width: W,
                    height: W,
                    marginRight: (index + 1) % COLS === 0 ? 0 : GAP,
                    marginBottom: GAP,
                  },
                ]}
              />
            ))}
          </View>
        </View>
      ) : (
        <View style={styles.emptyCard}>
          <Ionicons name="images-outline" size={EMPTY_ICON_SIZE} color={theme.muted} />
          <Text style={styles.emptyTitle}>まだ記録はありません</Text>
          <Text style={styles.emptyText}>参拝した神社や御朱印を残すと、あとから自分の流れを振り返れます。</Text>
          <Button
            title="最初の記録を追加する"
            variant="primary"
            onPress={() => router.push("/goshuin/upload")}
            accessibilityLabel="最初の御朱印記録を追加する"
            style={styles.emptyCtaPlacement}
          />
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.outside,
  },
  content: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    minHeight: "100%",
    backgroundColor: theme.background,
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 48,
  },
  headerBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
    marginBottom: 28,
  },
  heroBlock: {
    paddingBottom: 24,
  },
  heroLead: {
    ...typography.body,
    color: theme.mutedSoft,
    marginBottom: 10,
  },
  heroTitle: {
    ...typography.display,
    color: theme.text,
  },
  heroCount: {
    ...typography.subhead,
    color: theme.muted,
    marginTop: 12,
  },
  stateText: {
    ...typography.body,
    color: theme.muted,
    marginTop: 40,
    textAlign: "center",
  },
  gridCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 24,
    padding: 16,
    shadowColor: theme.text,
    shadowOpacity: 0.28,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  sectionLabel: {
    ...typography.eyebrow,
    color: theme.mutedSoft,
    marginBottom: 14,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  stampImage: {
    borderRadius: 14,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderSoft,
  },
  emptyCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 24,
    padding: 22,
    alignItems: "center",
    gap: 10,
  },
  emptyTitle: {
    ...typography.subheading,
    color: theme.text,
  },
  emptyText: {
    ...typography.body,
    color: theme.muted,
    textAlign: "center",
  },
  emptyCtaPlacement: {
    width: "100%",
    marginTop: 8,
  },
});
