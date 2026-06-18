import * as React from "react";
import { useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable } from "react-native";
import { colors } from "./theme";
import RankingCarousel from "../components/home/RankingCarousel";
import { SHRINES } from "../data/shrines";
import MyPageCard from "../components/home/MyPageCard";

export default function Home() {
  const router = useRouter();
  const [consultation, setConsultation] = React.useState("");
  const [selectedTheme, setSelectedTheme] = React.useState<string | null>(null);
  const [showConditions, setShowConditions] = React.useState(false);

  const themes = [
    "💼 仕事・転機",
    "❤️ 恋愛・ご縁",
    "👥 人間関係",
    "💰 金運・商売",
    "🌿 健康・厄除け",
    "🌙 心を整える",
    "✨ その他",
  ];

  const openConcierge = () => {
    const params = new URLSearchParams();
    if (consultation.trim()) params.set("q", consultation.trim());
    if (selectedTheme) params.set("theme", selectedTheme);
    const query = params.toString();
    router.push(query ? `/concierge?${query}` : "/concierge");
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.heroLead}>今の悩みや願いから</Text>
        <Text style={styles.heroTitle}>神社とのご縁を探します</Text>
      </View>

      <View style={styles.consultationCard}>
        <Text style={styles.sectionTitle}>今の気持ちを自由に書いてください</Text>
        <TextInput
          placeholder="最近気になっていること、叶えたい願いごと、整理したい気持ちなど"
          placeholderTextColor={colors.muted}
          style={styles.consultationInput}
          value={consultation}
          onChangeText={setConsultation}
          multiline
          textAlignVertical="top"
        />

        <View style={styles.examples}>
          <Text style={styles.exampleLabel}>例えば</Text>
          <Text style={styles.exampleText}>・最近気になっていること</Text>
          <Text style={styles.exampleText}>・叶えたい願いごと</Text>
          <Text style={styles.exampleText}>・整理したい気持ち</Text>
        </View>

        <View style={styles.themeGrid}>
          {themes.map((theme) => {
            const active = selectedTheme === theme;
            return (
              <Pressable
                key={theme}
                onPress={() => setSelectedTheme(active ? null : theme)}
                style={[styles.themePill, active && styles.themePillActive]}
              >
                <Text style={[styles.themePillText, active && styles.themePillTextActive]}>{theme}</Text>
              </Pressable>
            );
          })}
        </View>

        <Pressable onPress={() => setShowConditions((current) => !current)} style={styles.accordionToggle}>
          <Text style={styles.accordionToggleText}>{showConditions ? "− 条件を閉じる" : "+ 条件を追加"}</Text>
        </Pressable>

        {showConditions ? (
          <View style={styles.conditionList}>
            <Text style={styles.conditionItem}>🎂 誕生日</Text>
            <Text style={styles.conditionItem}>⛩ ご利益</Text>
            <Text style={styles.conditionItem}>📍 エリア</Text>
            <Text style={styles.conditionItem}>🚶 参拝スタイル</Text>
          </View>
        ) : null}

        <Pressable onPress={openConcierge} style={styles.primaryCta}>
          <Text style={styles.primaryCtaText}>神社とのご縁を探す</Text>
        </Pressable>
      </View>

      <View style={styles.exploreCard}>
        <Text style={styles.exploreTitle}>⛩ 神社を探す</Text>
        <Text style={styles.exploreDescription}>神社との出会いを探す</Text>
        <View style={styles.exploreActions}>
          <Pressable onPress={() => router.push("/search")} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>地図から探す</Text>
          </Pressable>
          <Pressable onPress={() => router.push("/search")} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>神社一覧を見る</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.rankingSection}>
        <Text style={styles.rankingTitle}>🔥 よく見られている神社</Text>
        <RankingCarousel items={SHRINES.slice(0, 5)} />
      </View>

      <MyPageCard />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.paper,
  },
  content: {
    paddingBottom: 32,
  },
  hero: {
    paddingHorizontal: 20,
    paddingTop: 28,
    paddingBottom: 16,
  },
  heroLead: {
    color: colors.muted,
    fontSize: 15,
    fontWeight: "500",
    marginBottom: 4,
  },
  heroTitle: {
    color: colors.text,
    fontSize: 28,
    fontWeight: "800",
    lineHeight: 34,
  },
  consultationCard: {
    marginHorizontal: 16,
    padding: 16,
    borderRadius: 24,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#EFE7DA",
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 2,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 10,
  },
  consultationInput: {
    minHeight: 132,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#E3D8C7",
    backgroundColor: "#FFFDF8",
    color: colors.text,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    lineHeight: 22,
  },
  examples: {
    marginTop: 12,
    gap: 3,
  },
  exampleLabel: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
    marginBottom: 2,
  },
  exampleText: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
  themeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 16,
  },
  themePill: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: "#F7F1E8",
    borderWidth: 1,
    borderColor: "#E8DCCB",
  },
  themePillActive: {
    backgroundColor: "#3D2C1E",
    borderColor: "#3D2C1E",
  },
  themePillText: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "700",
  },
  themePillTextActive: {
    color: "white",
  },
  accordionToggle: {
    marginTop: 16,
    paddingVertical: 8,
  },
  accordionToggleText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  conditionList: {
    borderRadius: 16,
    backgroundColor: "#FAF7F1",
    padding: 12,
    gap: 8,
  },
  conditionItem: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "600",
  },
  primaryCta: {
    height: 54,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#8A3B2E",
    marginTop: 18,
  },
  primaryCtaText: {
    color: "white",
    fontSize: 16,
    fontWeight: "800",
  },
  exploreCard: {
    marginHorizontal: 16,
    marginTop: 18,
    padding: 16,
    borderRadius: 22,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#EFE7DA",
  },
  exploreTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  exploreDescription: {
    color: colors.muted,
    fontSize: 13,
    marginTop: 4,
    marginBottom: 12,
  },
  exploreActions: {
    flexDirection: "row",
    gap: 10,
  },
  secondaryButton: {
    flex: 1,
    minHeight: 44,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F2F2F2",
    borderWidth: 1,
    borderColor: "#E6E0D5",
  },
  secondaryButtonText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  rankingSection: {
    marginTop: 20,
  },
  rankingTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "800",
    paddingHorizontal: 16,
    marginBottom: 10,
  },
});
