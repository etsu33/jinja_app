import * as React from "react";
import { useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable } from "react-native";
import { kamimusubiDark as theme } from "../../app/theme";

const THEMES = [
  "疲れを整えたい",
  "迷いを整理したい",
  "前に進みたい",
  "静かに考えたい",
  "人との縁を見直したい",
  "仕事の流れを整えたい",
] as const;

export default function Home() {
  const router = useRouter();
  const [consultation, setConsultation] = React.useState("");
  const [selectedTheme, setSelectedTheme] = React.useState<string | null>(null);
  const [showConditions, setShowConditions] = React.useState(false);

  const openConcierge = () => {
    const params = new URLSearchParams();
    if (consultation.trim()) params.set("q", consultation.trim());
    if (selectedTheme) params.set("theme", selectedTheme);
    const query = params.toString();
    router.push(query ? `/concierge?${query}` : "/concierge");
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      {/* ブランドヘッダー */}
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <Text style={styles.logoMark}>⛩️</Text>
          <View>
            <Text style={styles.brandName}>神結び</Text>
            <Text style={styles.brandRuby}>kami musubi</Text>
          </View>
        </View>
      </View>

      {/* Hero */}
      <View style={styles.hero}>
        <Text style={styles.heroLead}>今の相談から、向かう神社を見つける</Text>
        <Text style={styles.heroSub}>
          悩みや願いを一言にすると、今の状態に合う神社を探しやすくなります。
        </Text>
      </View>

      {/* 自由入力カード */}
      <View style={styles.chatCard}>
        <TextInput
          placeholder="例: 気持ちを切り替えたい、前に進みたい"
          placeholderTextColor={theme.mutedDark}
          style={styles.chatInput}
          value={consultation}
          onChangeText={setConsultation}
          multiline
          textAlignVertical="top"
        />
        <View style={styles.chatFooter}>
          <Text style={styles.aiHint}>AIがあなたの言葉からご縁を結びます</Text>
          <Pressable onPress={openConcierge} style={styles.sendButton}>
            <Text style={styles.sendButtonText}>↑</Text>
          </Pressable>
        </View>
      </View>

      {/* テーマチップ */}
      <View style={styles.themeSection}>
        <Text style={styles.themeLabel}>ことばが浮かばないときは、ここから</Text>
        <View style={styles.themeGrid}>
          {THEMES.map((t) => {
            const active = selectedTheme === t;
            return (
              <Pressable
                key={t}
                onPress={() => setSelectedTheme(active ? null : t)}
                style={[styles.themePill, active && styles.themePillActive]}
              >
                <Text style={[styles.themePillText, active && styles.themePillTextActive]}>{t}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* 条件追加トグル */}
      <Pressable
        onPress={() => setShowConditions((c) => !c)}
        style={styles.accordionToggle}
      >
        <Text style={styles.accordionToggleText}>
          {showConditions ? "− 条件を閉じる" : "+ 条件を追加"}
        </Text>
      </Pressable>

      {showConditions ? (
        <View style={styles.conditionHint}>
          <Text style={styles.conditionHintText}>
            誕生日・ご利益・参拝スタイルは次のステップで追加できます。
          </Text>
        </View>
      ) : null}

      {/* 主CTA */}
      <Pressable onPress={openConcierge} style={styles.primaryCta}>
        <Text style={styles.primaryCtaText}>この相談ではじめる</Text>
      </Pressable>

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

  // ヘッダー
  header: {
    height: 60,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottomWidth: 1,
    borderBottomColor: theme.borderHeader,
    marginHorizontal: -20,
    paddingHorizontal: 20,
    marginBottom: 28,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  logoMark: {
    fontSize: 22,
  },
  brandName: {
    color: theme.text,
    fontSize: 20,
    fontWeight: "900",
    letterSpacing: 1,
  },
  brandRuby: {
    color: theme.muted,
    fontSize: 12,
    letterSpacing: 4,
    marginTop: 1,
  },

  // Hero
  hero: {
    paddingBottom: 24,
    gap: 10,
  },
  heroLead: {
    color: theme.text,
    fontSize: 20,
    fontWeight: "900",
    lineHeight: 30,
    letterSpacing: 0.4,
  },
  heroSub: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 21,
    fontWeight: "500",
  },

  // 入力カード
  chatCard: {
    minHeight: 154,
    borderRadius: 22,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.25,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 3,
  },
  chatInput: {
    minHeight: 78,
    color: theme.text,
    fontSize: 15,
    lineHeight: 24,
    padding: 0,
  },
  chatFooter: {
    marginTop: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  aiHint: {
    flex: 1,
    color: theme.mutedDark,
    fontSize: 12,
    lineHeight: 18,
  },
  sendButton: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: theme.gold,
    alignItems: "center",
    justifyContent: "center",
  },
  sendButtonText: {
    color: theme.background,
    fontSize: 22,
    fontWeight: "900",
  },

  // テーマチップ
  themeSection: {
    marginTop: 24,
  },
  themeLabel: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  themeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  themePill: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderMuted,
  },
  themePillActive: {
    backgroundColor: theme.gold,
    borderColor: theme.gold,
  },
  themePillText: {
    color: theme.mutedSoft,
    fontSize: 13,
    fontWeight: "700",
  },
  themePillTextActive: {
    color: theme.background,
  },

  // 条件追加
  accordionToggle: {
    marginTop: 18,
    paddingVertical: 8,
  },
  accordionToggleText: {
    color: theme.mutedSoft,
    fontSize: 13,
    fontWeight: "700",
  },
  conditionHint: {
    borderRadius: 14,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  conditionHintText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "500",
  },

  // 主CTA
  primaryCta: {
    height: 54,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
    marginTop: 20,
    shadowColor: theme.gold,
    shadowOpacity: 0.2,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  primaryCtaText: {
    color: theme.background,
    fontSize: 16,
    fontWeight: "900",
    letterSpacing: 0.3,
  },

});
