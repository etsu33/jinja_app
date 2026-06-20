// apps/mobile/app/goshuin/index.tsx
import * as React from "react";
import { View, Text, Image, Pressable, StyleSheet, ScrollView, Dimensions } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { getStamps } from "../../../lib/storage";
import { kamimusubiDark as theme } from "../../../app/theme";

const GAP = 10;
const COLS = 3;
const W = (Math.min(Dimensions.get("window").width, 430) - 20 * 2 - GAP * (COLS - 1)) / COLS;

export default function GoshuinList() {
  const router = useRouter();
  const [stamps, setStamps] = React.useState<{ id: string; uri: string; createdAt: number }[]>([]);

  useFocusEffect(
    React.useCallback(() => {
      let alive = true;
      (async () => {
        const list = await getStamps();
        if (alive) setStamps(list);
      })();
      return () => {
        alive = false;
      };
    }, []),
  );

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.headerBar}>
        <Pressable
          onPress={() => {
            if (router.canGoBack()) {
              router.back();
            } else {
              router.replace("/records");
            }
          }}
          style={styles.back}
        >
          <Text style={styles.backText}>← 戻る</Text>
        </Pressable>
        <Pressable onPress={() => router.push("/goshuin/upload")} style={styles.addButton}>
          <Text style={styles.addButtonText}>＋ 記録する</Text>
        </Pressable>
      </View>

      <View style={styles.heroBlock}>
        <Text style={styles.heroLead}>参拝の記録</Text>
        <Text style={styles.heroTitle}>結んだご縁を、{`\n`}静かに残す</Text>
        <Text style={styles.heroCount}>{stamps.length} 件の御朱印</Text>
      </View>

      {stamps.length > 0 ? (
        <View style={styles.gridCard}>
          <Text style={styles.sectionLabel}>GOSHUIN</Text>
          <View style={styles.grid}>
            {stamps.map((s, index) => (
              <Image
                key={String(s.id)}
                source={{ uri: s.uri }}
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
          <Text style={styles.emptyIcon}>□</Text>
          <Text style={styles.emptyTitle}>まだ記録はありません</Text>
          <Text style={styles.emptyText}>参拝した神社や御朱印を残すと、あとから自分の流れを振り返れます。</Text>
          <Pressable onPress={() => router.push("/goshuin/upload")} style={styles.emptyCta}>
            <Text style={styles.emptyCtaText}>最初の記録を追加する</Text>
          </Pressable>
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
    justifyContent: "space-between",
    marginBottom: 28,
  },
  back: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingVertical: 8,
    paddingHorizontal: 13,
    borderRadius: 999,
    backgroundColor: "transparent",
  },
  backText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  addButton: {
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingVertical: 8,
    paddingHorizontal: 13,
    borderRadius: 999,
    backgroundColor: theme.borderGoldDark,
  },
  addButtonText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  heroBlock: {
    paddingBottom: 24,
  },
  heroLead: {
    color: theme.mutedSoft,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 1,
    marginBottom: 10,
  },
  heroTitle: {
    color: theme.text,
    fontSize: 30,
    fontWeight: "900",
    lineHeight: 40,
    letterSpacing: 1,
  },
  heroCount: {
    color: theme.muted,
    fontSize: 13,
    fontWeight: "700",
    marginTop: 12,
  },
  gridCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 24,
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.28,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  sectionLabel: {
    color: theme.mutedSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 2,
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
  emptyIcon: {
    color: theme.gold,
    fontSize: 28,
    fontWeight: "900",
    marginBottom: 6,
  },
  emptyTitle: {
    color: theme.text,
    fontSize: 18,
    fontWeight: "900",
  },
  emptyText: {
    color: theme.muted,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
    textAlign: "center",
  },
  emptyCta: {
    width: "100%",
    height: 50,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
    marginTop: 8,
  },
  emptyCtaText: {
    color: theme.background,
    fontSize: 15,
    fontWeight: "900",
  },
});
