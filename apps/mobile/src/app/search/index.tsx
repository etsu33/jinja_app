import { useLocalSearchParams, useRouter } from "expo-router";
import { View, Text, ScrollView, Pressable, Image, StyleSheet } from "react-native";
import { SHRINES } from "../../../data/shrines";
import { kamimusubiDark as theme } from "../../../app/theme";

export default function SearchPage() {
  const router = useRouter();
  const { q, filters } = useLocalSearchParams<{ q?: string; filters?: string }>();
  const query = (q ?? "").toLowerCase();
  const selected = (filters ?? "").split(",").filter(Boolean);

  const filtered = SHRINES.filter(s => {
    const textHit =
      !query ||
      s.name.toLowerCase().includes(query) ||
      s.tags.some(t => t.toLowerCase().includes(query)) ||
      (s.prefecture ?? "").toLowerCase().includes(query);

    const tagsHit =
      selected.length === 0 ||
      selected.every(sel => s.tags.includes(sel) || s.prefecture === sel);

    return textHit && tagsHit;
  });

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Pressable
        onPress={() => router.canGoBack() ? router.back() : router.replace("/")}
        style={styles.back}
      >
        <Text style={styles.backText}>← 戻る</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.heroLead}>神社を探す</Text>
        <Text style={styles.heroTitle}>今の気持ちに合う神社を、{`\n`}静かに見つける</Text>
        <Text style={styles.heroSub}>
          地域やご利益、気になる言葉から、参拝先の候補を確認できます。
        </Text>
      </View>

      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>検索条件</Text>
        <Text style={styles.summaryText}>キーワード: {q || "なし"}</Text>
        {selected.length > 0 ? (
          <View style={styles.tagRow}>
            {selected.map((c) => (
              <View key={c} style={styles.tag}>
                <Text style={styles.tagText}>{c}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.summaryHint}>条件なしで、登録神社を一覧表示しています。</Text>
        )}
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>神社一覧</Text>
        <Text style={styles.sectionCount}>{filtered.length}件</Text>
      </View>

      <View style={styles.list}>
        {filtered.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>該当する神社がありませんでした</Text>
            <Text style={styles.emptyText}>条件を変えるか、相談タブから今の気持ちを入力して探してみてください。</Text>
          </View>
        ) : null}

        {filtered.map((s) => (
          <Pressable
            key={s.id}
            onPress={() => router.push(`/shrines/${s.id}`)}
            style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
          >
            <Image source={{ uri: s.imageUrl }} style={styles.cardImage} />
            <View style={styles.cardBody}>
              <Text style={styles.cardName}>{s.name}</Text>
              <Text style={styles.cardArea}>{s.prefecture}</Text>
              <View style={styles.miniTagRow}>
                {s.tags.slice(0, 3).map((t) => (
                  <View key={t} style={styles.miniTag}>
                    <Text style={styles.miniTagText}>{t}</Text>
                  </View>
                ))}
              </View>
            </View>
            <Text accessibilityElementsHidden style={styles.chevron}>›</Text>
          </Pressable>
        ))}
      </View>
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
    paddingBottom: 96,
  },
  back: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingVertical: 8,
    paddingHorizontal: 13,
    borderRadius: 999,
    backgroundColor: "transparent",
    marginBottom: 28,
  },
  backText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  hero: {
    paddingBottom: 22,
    gap: 10,
  },
  heroLead: {
    color: theme.mutedSoft,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 1,
  },
  heroTitle: {
    color: theme.text,
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 38,
    letterSpacing: 0.8,
  },
  heroSub: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 21,
    fontWeight: "600",
  },
  summaryCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 20,
    padding: 16,
    marginBottom: 24,
  },
  summaryLabel: {
    color: theme.mutedSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.8,
    marginBottom: 8,
  },
  summaryText: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "800",
  },
  summaryHint: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
    fontWeight: "600",
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  tag: {
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  tagText: {
    color: theme.gold,
    fontSize: 12,
    fontWeight: "700",
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  sectionTitle: {
    color: theme.text,
    fontSize: 18,
    fontWeight: "900",
  },
  sectionCount: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  list: {
    gap: 12,
  },
  emptyCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 18,
    padding: 18,
    gap: 8,
  },
  emptyTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "900",
  },
  emptyText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderHeader,
    borderRadius: 18,
    padding: 12,
    gap: 12,
  },
  cardPressed: {
    opacity: 0.74,
  },
  cardImage: {
    width: 76,
    height: 64,
    borderRadius: 14,
    backgroundColor: theme.surfaceSoft,
  },
  cardBody: {
    flex: 1,
    gap: 4,
  },
  cardName: {
    color: theme.text,
    fontSize: 16,
    fontWeight: "900",
  },
  cardArea: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  miniTagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 4,
  },
  miniTag: {
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  miniTagText: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "700",
  },
  chevron: {
    color: theme.gold,
    fontSize: 22,
    fontWeight: "800",
  },
});
